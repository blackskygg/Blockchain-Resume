import sys
import json
import functools
import traceback

import tornado.web
import tornado.websocket

from tornado import gen

from tornado.web import (
    HTTPError,
    decode_signed_value,
)

import models
from database import db_session
from util import conn_redis, AdvEncoder


redis_cli = conn_redis()


class JSONHTTPError(HTTPError):
    def __init__(self, status_code, log_message=None, *args, **kwargs):
        self.response = kwargs.get('response', {})
        super().__init__(status_code, log_message, *args, **kwargs)


class BaseDBHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.session = db_session()
        self.redis_cli = redis_cli

    def on_finish(self):
        self.session.close()


class JSONHandler(BaseDBHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Origin, Content-Type, X-Auth-Token")

    def prepare(self):
        if self.request.method not in ('GET', 'HEAD'):
            try:
                body = self.request.body.decode('utf8')
                print(body)
                if body:
                    json_args = json.loads(self.request.body.decode('utf8'))
                    self.json_args = dict()
                    for key, value in json_args.items():
                        self.json_args[key] = [value]
                else:
                    self.json_args = None
            except Exception as e:
                raise JSONHTTPError(415) from e

    def write_error(self, status_code, **kwargs):
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            response = kwargs.get('response', None)
            if "exc_info" in kwargs:
                exception = kwargs['exc_info'][1]
                if isinstance(exception, JSONHTTPError) and exception.response:
                    response = exception.response

            if response is None:
                response = [
                    {
                        'error': self._reason
                    }
                ]
            if not (isinstance(response, str) or isinstance(response, bytes)):
                response = json.dumps(response)
            self.set_status(status_code)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.finish(response)


class FormHandlerMixin():
    def validation_error(self, form):
        response = list()
        for name, error in form.errors.items():
            response.append({
                'name': name,
                'error': error,
            })
        raise JSONHTTPError(400, response=response)

    def check_for_same(self, name):
        response = list()
        response.append({
            'name': name,
            'error': "this " + name + " has been used",
        })
        raise JSONHTTPError(400, response=response)


class QueryHandlerMixin():
    def apply_limit(self, query, form):
        if form.offset.data is not None:
            query = query.offset(form.offset.data)
        if form.limit.data is not None:
            query = query.limit(form.limit.data)
        return query

    def apply_order(self, query, form, apply_limit=True):
        query = query.order_by("%s %s" % (form.sortby.data, form.order.data))
        if apply_limit:
            query = self.apply_limit(query, form)
        return query

    def apply_edit(self, target, form, attr_list,
                   permission_check=None):
        if permission_check is not None \
                and not permission_check(target, self.current_user):
            raise JSONHTTPError(404)
        changed = False
        for attr in attr_list:
            new_data = getattr(form, attr).data
            ori_data = getattr(target, attr)
            if new_data and new_data != ori_data:
                changed = True
                setattr(target, attr, new_data)
        return changed

    def get_or_404(self, query, query_string=None, **kwargs):
        try:
            if query_string is not None:
                result = query.get(query_string)
            else:
                result = query.filter_by(**kwargs).first()
            assert result is not None
        except AssertionError as e:
            raise JSONHTTPError(404) from e
        else:
            return result

    def finish_objects(self, Form, Model=None, query=None,
                       permission_check=None,
                       *args, **kwargs):
        form = Form(self.request.arguments,
                    locale_code=self.locale.code)
        if form.validate():
            if Model is not None:
                query = self.session.query(Model)
            objects_query = self.apply_order(query, form)
            objects = objects_query.all()

            response = list()
            for obj in objects:
                if permission_check is not None \
                        and not permission_check(obj, self.current_user):
                    continue

                response.append(
                    obj.format_detail(*args, **kwargs)
                )
            self.finish(json.dumps(response, cls=AdvEncoder))
        else:
            self.validation_error(form)

    def finish_objects_count(self, Model=None, query=None):
        if Model is not None:
            query = self.session.query(Model)
        response = {
            'count': query.count()
        }
        self.finish(json.dumps(response, cls=AdvEncoder))

    def finish_object(self, Model, id=None, permission_check=None,
                      query_kwargs={},
                      format_args=[], format_kwargs={}):
        obj = self.get_or_404(self.session.query(Model),
                              id, **query_kwargs)
        if permission_check is not None \
                and not permission_check(obj, self.current_user):
            raise JSONHTTPError(404)

        self.finish(json.dumps(
            obj.format_detail(*format_args, **format_kwargs),
            cls=AdvEncoder
        ))
        return obj


class APIBaseHandler(JSONHandler, FormHandlerMixin, QueryHandlerMixin):
    def get_current_user(self):
        uid = self.request.headers.get('Authorization', None)
        if uid:
            uid = \
                decode_signed_value(self.application.settings["cookie_secret"],
                                    'uid', uid)
        try:
            current_user = self.session.query(models.User).get(uid.decode('utf8')) or \
                self.session.query(models.Company).get(uid.decode('utf-8'))
        except Exception:
            current_user = None

        return current_user


def authenticated(admin=False):
    def _authenticated(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Auth
            if not self.current_user:
                raise JSONHTTPError(401)
            # Permission
            if admin:
                if not self.current_user.is_admin:
                    raise JSONHTTPError(403)
            return method(self, *args, **kwargs)
        return wrapper
    return _authenticated


def db_success_or_500(db_func):
    @functools.wraps(db_func)
    def wrapper(self, *args, **kwargs):
        try:
            result = db_func(self, *args, **kwargs)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise JSONHTTPError(500) from e
        else:
            return result
    return wrapper


def db_success_or_pass(db_func):
    @functools.wraps(db_func)
    def wrapper(self, *args, **kwargs):
        try:
            result = db_func(self, *args, **kwargs)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
            return None
        else:
            return result
    return wrapper


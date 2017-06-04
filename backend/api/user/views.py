import json
import string
import random
from urllib import request, response, parse
import httplib2
import http.client
import urllib
import rsa

import tornado.httpclient
from tornado import gen
from tornado.httpclient import (
    AsyncHTTPClient,
    HTTPError,
)
from sqlalchemy import func
import util
import models
from .. import base
from . import forms

__all__ = [
    "UserLoginHandler",
    "UserRegisterHandler",
    "UserQueryCertifiedHandler"
]


class UserRegisterHandler(base.APIBaseHandler):
    """
    URL: /user/register
    Allowed methods: POST
    """
    def post(self):
        """
        create a new user
        """
        form = forms.RegisterForm(self.json_args,
                                  locale_code=self.locale.code)
        if form.validate():
            user = self.create_user(form)

            self.set_status(201)
            self.finish(json.dumps({
                'auth': self.create_signed_value('uid', user.uid.hex).decode('utf-8'),
            }))

            chaincodeId = "e0cf3fb8201dbbd10aa493f866acd7616ab091395a75717801e070f8ce06c07e843ae3aa0bd1a3d24b74f57cd70bda7266c325697171a3679f5b439a569573e6"
            text = {
                "Rp": {
                    "ID": form.identityNum.data,
                    "Name": form.realname.data
                },
                "PubKeyPem": user.publicKey
            }
            text = json.dumps(text)
            data = {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "type": 1,
                    "chaincodeID": {
                        "name": chaincodeId
                    },
                    "ctorMsg": {
                        "function": "AddRecipient",

                        "args": [
                            text
                        ]
                    },
                    "secureContext": "admin"
                },
                "id": 0
            }
            headers = {'Content-type': "application/json"}
            conn = http.client.HTTPSConnection("a4f9e701badb4a279c4cb2206f7361c3-vp0.us.blockchain.ibm.com", 5004)

            conn.request("POST", "/chaincode", body=json.dumps(data), headers=headers)
            resp = conn.getresponse()

            if resp.status == 200:
                print(True)
            else:
                print(False)
        else:
            self.validation_error(form)

    @base.db_success_or_pass
    def create_user(self, form):
        public_key, private_key = util.generrate_key()
        user = models.User(realname=form.realname.data,
                           identityNum=form.identityNum.data,
                           privateKey=private_key,
                           publicKey=public_key)
        user.set_password(form.password.data)
        self.session.add(user)

        return user


class UserLoginHandler(base.APIBaseHandler):
    """
    URL: /user/login
    Allowed methods: 'POST'
    """
    def post(self):
        """
        Get auth token
        """
        form = forms.LoginForm(self.json_args,
                               locale_code=self.locale.code)
        if form.validate():
            user = form.kwargs['user']
            self.finish(json.dumps({
                'auth': self.create_signed_value('uid', user.uid.hex).decode('utf-8'),
            }))
        else:
            self.validation_error(form)


class UserQueryCertifiedHandler(base.APIBaseHandler):
    """
    URL: /user/getCertifites
    """
    @base.authenticated()
    def get(self):
        identifyNum = self.current_user.identityNum
        realname = self.current_user.realname
        chaincodeId = "e0cf3fb8201dbbd10aa493f866acd7616ab091395a75717801e070f8ce06c07e843ae3aa0bd1a3d24b74f57cd70bda7266c325697171a3679f5b439a569573e6"
        text = {
            "ID": identifyNum,
            "Name": realname
        }
        text = json.dumps(text)
        data = {
            "jsonrpc": "2.0",
            "method": "query",
            "params": {
                "type": 1,
                "chaincodeID": {
                    "name": chaincodeId
                },
                "ctorMsg": {
                    "function": "GetCertList",

                    "args": [
                        text
                    ]
                },
                "secureContext": "admin"
            },
            "id": 0
        }
        headers = {'Content-type': "application/json"}
        conn = http.client.HTTPSConnection("a4f9e701badb4a279c4cb2206f7361c3-vp0.us.blockchain.ibm.com", 5004)

        conn.request("POST", "/chaincode", body=json.dumps(data), headers=headers)
        resp = conn.getresponse()

        if resp.status == 200:
            print(True)
        else:
            print(False)
        # self.finish(json.dumps(resp))
        print(resp)

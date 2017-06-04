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
    "CompanyLoginHandler",
    "CompanyRegisterHandler",
    "CompanyIssueCertifates"
]


class CompanyRegisterHandler(base.APIBaseHandler):
    """
    URL: /company/register
    Allowed methods: POST
    """
    def post(self):
        """
        create a new user
        """
        form = forms.RegisterForm(self.json_args,
                                  locale_code=self.locale.code)
        if form.validate():
            user = self.create_company(form)

            self.set_status(201)
            self.finish(json.dumps({
                'auth': self.create_signed_value('uid', user.uid.hex).decode('utf-8'),
            }))
            chaincodeId = "e0cf3fb8201dbbd10aa493f866acd7616ab091395a75717801e070f8ce06c07e843ae3aa0bd1a3d24b74f57cd70bda7266c325697171a3679f5b439a569573e6"
            text = {
                "Issuer": form.companyName.data,
                "PubKeyPem": user.public_key
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
                        "function": "AddIssuer",

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
    def create_company(self, form):
        public_key, private_key = util.generrate_key()
        company = models.Company(companyName=form.companyName.data,
                                 privateKey=private_key,
                                 publicKey=public_key)
        company.set_password(form.password.data)
        self.session.add(company)

        return company


class CompanyLoginHandler(base.APIBaseHandler):
    """
    URL: /company/login
    Allowed methods: 'POST'
    """
    def post(self):
        """
        Get auth token
        """
        form = forms.LoginForm(self.json_args,
                               locale_code=self.locale.code)
        if form.validate():
            company = form.kwargs['company']
            self.finish(json.dumps({
                'auth': self.create_signed_value('uid', company.uid.hex).decode('utf-8'),
            }))
        else:
            self.validation_error(form)


class CompanyIssueCertifates(base.APIBaseHandler):
    def post(self):
        form = forms.IssueForm(self.json_args,
                               locale_code=self.locale.code)
        if form.validate():
            realname = form.realname.data
            identifyNum = form.identifyNum.data
            content = form.content.data
            hash = form.hash.data
            certsName = form.certsName.data
            chaincodeId = "e0cf3fb8201dbbd10aa493f866acd7616ab091395a75717801e070f8ce06c07e843ae3aa0bd1a3d24b74f57cd70bda7266c325697171a3679f5b439a569573e6"
            text = {
                "Recipient": {
                    "ID": identifyNum,
                    "Name": realname
                },
                "Link": content,
                "Hash": hash,
                "Issuer": self.current_user.companyName,
                "Description": certsName
            }
            text = json.dumps(text)
            priv_key = rsa.PrivateKey.load_pkcs1(self.current_user.private_key)
            # signed_text = util.generate_data_signature(text.encode("utf-8"), priv_key)
            data = {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "type": 1,
                    "chaincodeID": {
                        "name": chaincodeId
                    },
                    "ctorMsg": {
                        "function": "IssueCert",

                        "args": [
                            text,
                            # str(signed_text)
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

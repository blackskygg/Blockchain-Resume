import random
from datetime import date, datetime
import hashlib
import mimetypes
import uuid
import functools
import json
import base64
import time
import hmac
import redis
import rsa

from dateutil.tz import (
    tzlocal,
    tzutc,
)

from tornado import gen

from settings import (
    site_settings,
    redis_settings,
)


def get_salt(length=12,
             allowed_chars='abcdef0123456789'):
    return ''.join(random.choice(allowed_chars) for i in range(length))


def set_password(pwd):
    salt = get_salt(length=site_settings["salt_length"])
    new_pwd = salt + pwd + salt
    encoded_pwd = hashlib.sha256(new_pwd.encode("utf8")).hexdigest()
    final_pwd = salt + encoded_pwd

    return final_pwd


def check_password(request_pwd, final_pwd):
    salt = final_pwd[:site_settings["salt_length"]]
    encoded_pwd = final_pwd[site_settings["salt_length"]:]
    request_new_pwd = salt + request_pwd + salt
    request_encoded_pwd = hashlib.sha256(request_new_pwd.encode('utf8'))\
        .hexdigest()
    if request_encoded_pwd == encoded_pwd:
        return True
    else:
        return False


def get_utc_time():
    return datetime.now(tzlocal()).astimezone(tzutc())


class AdvEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return super().default(self, obj)


def generate_url(urls, apps=None, name=None):
    if apps is None:
        apps = []
    mapping = []

    mapping.extend(urls)

    for prefix, app_name in apps:
        if name == "__main__":
            app_path = app_name
        else:
            app_path = "%s.%s" % (name, app_name)
        app = __import__(app_path, fromlist=['mapping'])
        for app_url in app.mapping:
            new_url = list(app_url)

            new_url[0] = prefix + new_url[0]

            if isinstance(new_url[1], str):
                new_url[1] = "%s.%s" % (app_name, new_url[1])

            if len(app_url) == 4:
                new_url[3] = '%s.%s' % (app_name, new_url[3])
            mapping.append(tuple(new_url))
    return mapping


def conn_redis():
    return redis.StrictRedis(host=redis_settings["host"],
                             port=redis_settings["port"])


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    boundary = b'------------------------aa502a40917c'
    crlf = b'\r\n'
    l = []
    for (key, value) in fields:
        l.append(b'--' + boundary)
        l.append(b'Content-Disposition: form-data; name="%s"' % key.encode())
        l.append(b'')
        l.append(value.encode())
    for (key, filename, value) in files:
        # filename = filename.encode("utf8")
        l.append(b'--' + boundary)
        l.append(
            b'Content-Disposition: form-data; name="%s"; filename="%s"'
            % (key.encode(), filename.encode())
        )
        l.append(
            b'Content-Type: %s'
            % mimetypes.guess_type(filename)[0].encode() or b'application/octet-stream'
        )
        l.append(b'')
        l.append(value)
    l.append(b'')
    l.append(b'--' + boundary + b'--')
    l.append(b'')
    body = crlf.join(l)
    content_type = b'multipart/form-data; boundary=%s' % boundary
    return content_type, body


def generate_cos_signature(settings):
    cur_time = time.time()
    original = 'a={s[appid]}&b={s[bucket]}&k={s[secretid]}' \
               '&e={e}&t={t}&r={r}&f='\
        .format(s=settings,
                e=cur_time+300,
                t=cur_time,
                r=random.randint(0, 9999999999)
                )
    sign_tmp = hmac.new(settings['secretkey'].encode(),
                        original.encode(),
                        hashlib.sha1).digest()

    return base64.b64encode(sign_tmp + original.encode())


def generate_message_signature(settings):
    cur_time = int(time.time())
    rand_num = random.randint(0, 999999999)
    base = '{appsecret}{random}{time}'.format(appsecret=settings['message_appsercet'],
                                              random=rand_num,
                                              time=cur_time)
    sha1 = hashlib.sha1()
    sha1.update(base.encode())

    return sha1.hexdigest(), cur_time, rand_num


def generate_data_signature(data, priv_key):
    return rsa.sign(data, priv_key, 'SHA-256')


def decrypt_data(data, priv_key):
    pri = rsa.PrivateKey.load_pkcs1(priv_key)
    return rsa.decrypt(data, pri)


def generrate_key():
    pub, priv = rsa.newkeys(1024)
    return pub.save_pkcs1(), priv.save_pkcs1()


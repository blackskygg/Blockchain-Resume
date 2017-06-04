import os

__all__ = [
    "site_settings",
    "database_settings"
]

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates/').replace('\\', '/')
STATIC_DIR = os.path.join(BASE_DIR, 'static/').replace('\\', '/')
LOCALE_DIR = os.path.join(BASE_DIR, 'locale/').replace('\\', '/')
IMAGE_DIR = os.path.join(STATIC_DIR, 'img/').replace('\\', '/')

ACCESS_HOST = "http://yuepai01-1251817761.file.myqcloud.com/"
BUCKET_NAME = "BlockChainResume"


site_settings = {
    "debug": False,
    "cookie_secret": "d13a4dbd47f042ccb47169a2fdd5e789",
    "xsrf_cookies": False,
    "login_url": "/login",
    "autoescape": None,
    "port": 8002,
    "base_path": BASE_DIR,
    "template_path": TEMPLATE_DIR,
    "static_path": STATIC_DIR,
    "locale_path": LOCALE_DIR,
    "image_path": IMAGE_DIR,
    "image_dir": "/static/img/",
    "locale_domain": "wtforms",
    "salt_length": 12,
    "cos_host": "http://gz.file.myqcloud.com/files/v2/1251817761/",
    "access_host": ACCESS_HOST,
    "appid": "1251817761",
    "bucket": BUCKET_NAME,
    "image_host": ACCESS_HOST + r'image/',
    "secretid": "AKIDprkeWDWGTeabcWfxSjkfKn57xXrvZFbh",
    "secretkey": "2oNs77ud7nSsHRPTI0SgfjgTEo8C0lKe",
    "message_appkey": "977231374b138370b68dc3c7a60449fb",
    "message_appsercet": "0df2d5f6edf4",
    "message_templateid": "3051094",
    "message_url": "https://api.netease.im/sms/sendtemplate.action"
}

database_settings = {
    "default": "mysql+pymysql://root:P@ssw0rd@139.198.15.91:3306/BlockChainResume?charset=utf8",
    "sqlite": "sqlite:///database.db",
}

redis_settings = {
    'host': 'localhost',
    'port': 6379,
}

# 139.198.15.91

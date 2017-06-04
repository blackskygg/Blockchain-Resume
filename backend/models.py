import uuid
import json

from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.schema import (
    UniqueConstraint,
    PrimaryKeyConstraint,
    Index,
)

from sqlalchemy import (
    Table,
    Column,
    BigInteger,
    SmallInteger,
    Integer,
    Unicode,
    UnicodeText,
    Boolean,
    DateTime,
    ForeignKey,
    JSON
)

from sqlalchemy.orm import (
    relationship,
    backref,
)

from database import Base
import util

IMAGE_HOST = "http://yuepai01-1251817761.file.myqcloud.com/image/"


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(str(value))


class User(Base):
    __tablename__ = 'user'
    uid = Column(GUID(),
                 default=uuid.uuid4,
                 primary_key=True)
    password = Column(Unicode(100),
                      nullable=True)
    realname = Column(Unicode(100),
                      nullable=False)
    identityNum = Column(Unicode(50),
                         nullable=False)
    publicKey = Column(Unicode(1024),
                       nullable=False)
    privateKey = Column(Unicode(1024),
                        nullable=False)

    def check_password(self, request_pwd):
        return util.check_password(request_pwd, self.password)

    def set_password(self, new_pwd):
        self.password = util.set_password(new_pwd)

    def __init__(self,
                realname=None, identityNum=None,
                 publicKey=None, privateKey=None):
        self.realname = realname
        self.identityNum = identityNum
        self.privateKey = privateKey
        self.publicKey = publicKey

    def format_detail(self):
        detail = {
            'uid': self.uid.hex,
        }
        return detail


class Company(Base):
    __tablename__ = 'company'
    uid = Column(GUID(),
                 default=uuid.uuid4,
                 primary_key=True)
    companyName = Column(Unicode(50),
                      nullable=False)
    password = Column(Unicode(100),
                      nullable=False)
    is_certified = Column(Boolean,
                          default=False)
    public_key = Column(Unicode(1024),
                        nullable=True)
    private_key = Column(Unicode(1024),
                         nullable=True)

    def check_password(self, request_pwd):
        return util.check_password(request_pwd, self.password)

    def set_password(self, new_pwd):
        self.password = util.set_password(new_pwd)

    def __init__(self, companyName=None,
                 publicKey=None, privateKey=None):
        self.companyName = companyName
        self.public_key = publicKey
        self.private_key = privateKey

    def format_detail(self):
        detail = {
            'uid': self.uid.hex,
            'companyName': self.companyName,
            'is_certified': self.is_certified
        }
        return detail

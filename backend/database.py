from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from settings import database_settings

engine = create_engine(database_settings["default"],
                       convert_unicode=True,
                       encoding='utf-8')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)


def drop_db():
    import models
    Base.metadata.drop_all(bind=engine)


def init_models():
    import models
    session = db_session()
    try:
        admin = models.User(identityNum=130132199709102554,
                            realname='李泽康')
        admin.set_password("15927573538")
        session.add(admin)
        session.commit()
    except Exception as e:
        session.rollback()
    session.close()


def init_test_models():
    import models
    session = db_session()
    user = models.User(identityNum=130132199709102554,
                       realname='李泽康')
    user.set_password("123456")
    session.add(user)
    session.commit()

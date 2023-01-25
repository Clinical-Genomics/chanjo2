import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DEMO_DB = "sqlite:///./chanjotest.db"
DEMO_CONNECT_ARGS = {"check_same_thread": False}

root_password = os.getenv("MYSQL_ROOT_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE_NAME")
host_name = os.getenv("MYSQL_HOST_NAME")
port_no = os.getenv("MYSQL_PORT")

if os.getenv("DEMO") or not db_name:
    mysql_url = DEMO_DB
    engine = create_engine(mysql_url, echo=True, connect_args=DEMO_CONNECT_ARGS)

else:
    if port_no is None:
        host = host_name
    else:
        host = ":".join([host_name, port_no])

    mysql_url = f"mysql://root:{root_password}@{host}/{db_name}"
    engine = create_engine(mysql_url, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()

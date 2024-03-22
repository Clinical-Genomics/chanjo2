import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DEMO_DB = "sqlite://"
DEMO_CONNECT_ARGS = {"check_same_thread": False}

db_user = os.getenv("MYSQL_USER")
db_password = os.getenv("MYSQL_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE_NAME")
host_name = os.getenv("MYSQL_HOST_NAME")
port_no = os.getenv("MYSQL_PORT")

if os.getenv("DEMO") or not db_name:
    mysql_url = DEMO_DB
    engine = create_engine(
        mysql_url,
        echo=True,
        connect_args=DEMO_CONNECT_ARGS,
        poolclass=StaticPool,
        future=True,
    )

else:
    if port_no == "":
        host = host_name
    else:
        host = ":".join([host_name, port_no])

    mysql_url = f"mysql://{db_user}:{db_password}@{host}/{db_name}"
    engine = create_engine(mysql_url, echo=True, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

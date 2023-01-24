import os

from sqlmodel import Session, create_engine

DEMO_DB = "sqlite://"

root_password = os.getenv("MYSQL_ROOT_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE_NAME")
host_name = os.getenv("MYSQL_HOST_NAME")
port_no = os.getenv("MYSQL_PORT")

if os.getenv("DEMO") or not db_name:
    mysql_url = DEMO_DB
    engine = create_engine(mysql_url, echo=True, connect_args={"check_same_thread": False})

else:
    if port_no is None:
        host = host_name
    else:
        host = ":".join([host_name, port_no])

    mysql_url = f"mysql://root:{root_password}@{host}/{db_name}"
    engine = create_engine(mysql_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

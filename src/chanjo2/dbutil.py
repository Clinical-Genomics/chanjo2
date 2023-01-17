import os

from sqlmodel import Session, create_engine

engine = None

root_password = os.getenv("MYSQL_ROOT_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE_NAME")
host_name = os.getenv("MYSQL_HOST_NAME")
port_no = os.getenv("MYSQL_PORT")

if os.getenv("DEMO") or not db_name:
    mysql_url = "sqlite:///./chanjotest.db"
else:
    mysql_url = f"mysql://root:{root_password}@{host_name}:{port_no}/{db_name}"

engine = create_engine(mysql_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

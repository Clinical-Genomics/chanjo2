import os
from sqlmodel import Session, create_engine

root_password = os.getenv("MYSQL_ROOT_PASSWORD")
host_name = os.getenv("MYSQL_HOST_NAME")
db_name = os.getenv("MYSQL_DATABASE_NAME")
port_no = os.getenv("MYSQL_PORT")

mysql_url = f"mysql://root:{root_password}@{host_name}:{port_no}/{db_name}"

engine = create_engine(mysql_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

import logging
import os

LOG = logging.getLogger("uvicorn.access")

from sqlmodel import Session, create_engine

root_password = os.getenv("MYSQL_ROOT_PASSWORD") or "test"
db_name = os.getenv("MYSQL_DATABASE_NAME") or "chanjo2_test"

# Set DB host and port inti host variable
host = ""
host_name = os.getenv("MYSQL_HOST_NAME") or "127.0.0.1"
port_no = os.getenv("MYSQL_PORT") or "3307"
if os.getenv("MYSQL_PORT") != "None":
    host = ":".join([host_name, port_no])
else:  # This happens when app is invoked from Docker-compose (no db port needed)
    host = host_name

mysql_url = f"mysql://root:{root_password}@{host}/{db_name}"
LOG.error(f"MYSQL URL IS:{mysql_url}")

engine = create_engine(mysql_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

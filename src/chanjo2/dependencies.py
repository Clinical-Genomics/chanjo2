import os
from sqlmodel import Session, create_engine

root_password = os.getenv("MYSQL_ROOT_PASSWORD")

mysql_url = f"mysql://root:{root_password}@d4database:3306/d4files"

engine = create_engine(mysql_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

from sqlmodel import Session, create_engine

mysql_url = f"mysql://root:my_secret_pw@d4database:3306/d4files"

engine = create_engine(mysql_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session


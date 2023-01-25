from pathlib import Path
from typing import List

from chanjo2 import __version__
from chanjo2.dbutil import Base, engine
from fastapi import FastAPI, status

from .endpoints import intervals, samples


def create_db_and_tables():
    Base.metadata.create_all(engine)


app = FastAPI()

app.include_router(
    intervals.router,
    prefix="/intervals",
    tags=["regions"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

app.include_router(
    samples.router,
    prefix="/samples",
    tags=["samples"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()

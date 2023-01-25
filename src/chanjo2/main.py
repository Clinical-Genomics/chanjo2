import logging
import os

import coloredlogs
from chanjo2 import __version__
from chanjo2.dbutil import engine
from fastapi import FastAPI, status
from pydantic import BaseModel
from sqlmodel import SQLModel

from .endpoints import intervals, samples

LOG = logging.getLogger(__name__)
coloredlogs.install(level="INFO")


app = FastAPI()

app.include_router(
    intervals.router,
    prefix="/intervals",
    tags=["intervals"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

app.include_router(
    samples.router,
    prefix="/samples",
    tags=["samples"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@app.on_event("startup")
async def on_startup():
    SQLModel.metadata.create_all(engine)
    if os.getenv("DEMO") or not os.getenv("MYSQL_DATABASE_NAME"):
        LOG.warning("Running a demo instance of Chanjo2")


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}

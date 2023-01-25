import logging
from pathlib import Path
from typing import List, Literal, Optional

import coloredlogs
from chanjo2 import __version__
from chanjo2.dbutil import engine
from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from .dbutil import DEMO_DB
from .endpoints import individuals, regions

LOG = logging.getLogger(__name__)
coloredlogs.install(level="INFO")


class CoverageInterval(BaseModel):
    chromosome: str
    start: int
    end: int
    individual_id: str
    interval_id: str
    mean_coverage: float


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()

app.include_router(
    regions.router,
    prefix="/regions",
    tags=["regions"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

app.include_router(
    individuals.router,
    prefix="/individuals",
    tags=["individuals"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    if str(engine.url) == DEMO_DB:
        LOG.warning("Running a demo instance of Chanjo2")


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}

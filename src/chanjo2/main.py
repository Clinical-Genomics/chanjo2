from pathlib import Path
from typing import List, Literal, Optional

from chanjo2 import __version__
from chanjo2.dbutil import engine
from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import SQLModel

from .endpoints import individuals, intervals


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()

app.include_router(
    intervals.router,
    prefix="/intervals",
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


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}

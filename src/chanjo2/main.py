from pathlib import Path
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status

from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from src.chanjo2.dependencies import engine, get_session
from .models.individuals import Individual
from .endpoints import regions, individuals


##


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


@app.get("/")
async def root():
    return {"message": "Welcome to Chanjo2: A strangely named app about to be reborn."}

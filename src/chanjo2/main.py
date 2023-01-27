import logging
import os

import uvicorn
from chanjo2 import __version__
from chanjo2.dbutil import engine
from chanjo2.endpoints import intervals, samples
from chanjo2.models.sql_models import Base
from fastapi import FastAPI, status

LOG = logging.getLogger("uvicorn.access")


def create_db_and_tables():
    Base.metadata.create_all(engine)


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
    # Configure logging
    LOG = logging.getLogger("uvicorn.access")
    console_formatter = uvicorn.logging.ColourizedFormatter(
        "{levelprefix} {asctime} : {message}", style="{", use_colors=True
    )
    LOG.handlers[0].setFormatter(console_formatter)

    # Create database tables
    create_db_and_tables()

    if os.getenv("DEMO") or not os.getenv("MYSQL_DATABASE_NAME"):
        LOG.warning("Running a demo instance of Chanjo2")


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}

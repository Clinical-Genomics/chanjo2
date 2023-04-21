import logging
import os

import uvicorn
from chanjo2 import __version__
from chanjo2.dbutil import engine
from chanjo2.endpoints import cases, intervals, samples, coverage
from chanjo2.models.sql_models import Base
from chanjo2.populate_demo import load_demo_data
from fastapi import FastAPI, status

LOG = logging.getLogger("uvicorn.access")


def create_db_and_tables():
    Base.metadata.create_all(engine)


app = FastAPI()

app.include_router(
    intervals.router,
    tags=["intervals"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

app.include_router(
    coverage.router,
    tags=["coverage"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

app.include_router(
    cases.router,
    tags=["cases"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

app.include_router(
    samples.router,
    tags=["samples"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@app.on_event("startup")
async def on_startup():
    # Configure logging
    console_formatter = uvicorn.logging.ColourizedFormatter(
        "{levelprefix} {asctime} : {message}", style="{", use_colors=True
    )
    if LOG.handlers:
        LOG.handlers[0].setFormatter(console_formatter)
    else:
        logging.basicConfig()

    # Create database tables
    create_db_and_tables()

    if os.getenv("DEMO") or not os.getenv("MYSQL_DATABASE_NAME"):
        LOG.warning("Running a demo instance of Chanjo2")
        if await load_demo_data():
            LOG.info("Demo data loaded into database")


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}

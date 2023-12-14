import logging
import os
from contextlib import asynccontextmanager
from typing import List, Tuple

import uvicorn
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles

from chanjo2 import __version__
from chanjo2.dbutil import engine
from chanjo2.endpoints import cases, coverage, intervals, overview, report, samples
from chanjo2.models.sql_models import Base
from chanjo2.populate_demo import load_demo_data

LOG = logging.getLogger("uvicorn.access")
APP_ROUTER_TAGS: List[Tuple] = [
    (intervals.router, "intervals"),
    (coverage.router, "coverage"),
    (cases.router, "cases"),
    (samples.router, "samples"),
    (report.router, "report"),
    (overview.router, "overview"),
]


def create_db_and_tables():
    Base.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app_: FastAPI):
    LOG.info("Starting up...")
    await startup_db()
    yield
    LOG.info("Shutting down...")


app = FastAPI(lifespan=lifespan)


def configure_static(app):
    """Configure static folder."""
    exec_dir: str = os.path.dirname(__file__)
    static_abs_file_path: str = os.path.join(exec_dir, "static/")
    app.mount("/static", StaticFiles(directory=static_abs_file_path), name="static")


# include app router tags
for router, tag in APP_ROUTER_TAGS:
    app.include_router(
        router,
        tags=[tag],
        responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
    )


async def startup_db():
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

    configure_static(app)

    if os.getenv("DEMO") or not os.getenv("MYSQL_DATABASE_NAME"):
        LOG.warning("Running a demo instance of Chanjo2")
        if await load_demo_data():
            LOG.info("Demo data loaded into database")


@app.get("/")
def heartbeat():
    return {"message": f"Chanjo2 v{__version__} is up and running!"}

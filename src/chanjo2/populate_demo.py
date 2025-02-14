from typing import Iterator, List, Tuple

from schug.demo import (
    EXONS_37_FILE_PATH,
    EXONS_38_FILE_PATH,
    GENES_37_FILE_PATH,
    GENES_38_FILE_PATH,
    TRANSCRIPTS_37_FILE_PATH,
    TRANSCRIPTS_38_FILE_PATH,
)
from sqlalchemy.orm import sessionmaker

from chanjo2.dbutil import get_session
from chanjo2.meta.handle_load_intervals import update_interval_table
from chanjo2.models.pydantic_models import Builds, IntervalType

db: sessionmaker = next(get_session())

BUILD_GENES_RESOURCE: List[Tuple[Builds, str]] = [
    (Builds.build_37, GENES_37_FILE_PATH),
    (Builds.build_38, GENES_38_FILE_PATH),
]
BUILD_TRANSCRIPTS_RESOURCE: List[Tuple[Builds, str]] = [
    (Builds.build_37, TRANSCRIPTS_37_FILE_PATH),
    (Builds.build_38, TRANSCRIPTS_38_FILE_PATH),
]
BUILD_EXONS_RESOURCE: List[Tuple[Builds, str]] = [
    (Builds.build_37, EXONS_37_FILE_PATH),
    (Builds.build_38, EXONS_38_FILE_PATH),
]


async def load_demo_data() -> None:
    """Loads demo data into the database of a demo instance of Chanjo2."""
    await load_demo_genes()
    await load_demo_transcripts()
    await load_demo_exons()


async def load_demo_genes() -> None:
    """Load test genes into the database."""

    for build, path in BUILD_GENES_RESOURCE:
        update_interval_table(
            interval_type=IntervalType.GENES, build=build, file_path=path, session=db
        )


async def load_demo_transcripts() -> None:
    """Load test transcripts into the database."""

    for build, path in BUILD_TRANSCRIPTS_RESOURCE:
        update_interval_table(
            interval_type=IntervalType.TRANSCRIPTS,
            build=build,
            file_path=path,
            session=db,
        )


async def load_demo_exons() -> None:
    """Load test exons into the database."""

    for build, path in BUILD_EXONS_RESOURCE:
        update_interval_table(
            interval_type=IntervalType.EXONS, build=build, file_path=path, session=db
        )

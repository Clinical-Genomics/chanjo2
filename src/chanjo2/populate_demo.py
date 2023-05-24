from typing import Dict, List, Tuple, Iterator

from schug.demo import (
    EXONS_37_FILE_PATH,
    EXONS_38_FILE_PATH,
    GENES_37_FILE_PATH,
    GENES_38_FILE_PATH,
    TRANSCRIPTS_37_FILE_PATH,
    TRANSCRIPTS_38_FILE_PATH,
)
from sqlalchemy.orm import sessionmaker

from chanjo2.constants import BUILD_37, BUILD_38
from chanjo2.crud.cases import create_db_case
from chanjo2.crud.samples import create_sample_in_case
from chanjo2.dbutil import get_session
from chanjo2.demo import d4_demo_path
from chanjo2.meta.handle_load_intervals import (
    update_genes,
    update_transcripts,
    update_exons,
)
from chanjo2.models.pydantic_models import CaseCreate, SampleCreate, Builds

db: sessionmaker = next(get_session())

DEMO_CASE: Dict[str, str] = {"name": "internal_id", "display_name": "643594"}
DEMO_SAMPLE: Dict[str, str] = {
    "name": "ADM1059A2",
    "display_name": "NA12882",
    "track_name": "ADM1059A2",
    "case_name": DEMO_CASE["name"],
    "coverage_file_path": d4_demo_path,
}
BUILD_GENES_RESOURCE: List[Tuple[Builds, str]] = [
    (BUILD_37, GENES_37_FILE_PATH),
    (BUILD_38, GENES_38_FILE_PATH),
]
BUILD_TRANSCRIPTS_RESOURCE: List[Tuple[Builds, str]] = [
    (BUILD_37, TRANSCRIPTS_37_FILE_PATH),
    (BUILD_38, TRANSCRIPTS_38_FILE_PATH),
]
BUILD_EXONS_RESOURCE: List[Tuple[Builds, str]] = [
    (BUILD_37, EXONS_37_FILE_PATH),
    (BUILD_38, EXONS_38_FILE_PATH),
]


def resource_lines(file_path: str) -> Iterator[str]:
    resource = open(file_path, "r", encoding="utf-8")
    lines: List = resource.readlines()
    lines: List = [line.rstrip("\n") for line in lines]
    return iter(lines)


async def load_demo_data() -> None:
    """Loads demo data into the database of a demo instance of Chanjo2."""
    load_demo_case()
    load_demo_sample()
    await load_demo_genes()
    await load_demo_transcripts()
    await load_demo_exons()


def load_demo_case() -> None:
    """Load a demo case into the database."""
    case: CaseCreate = CaseCreate(**DEMO_CASE)
    create_db_case(db=db, case=case)


def load_demo_sample() -> None:
    """Add a sample to a demo case."""
    sample: SampleCreate = SampleCreate(**DEMO_SAMPLE)
    create_sample_in_case(db=db, sample=sample)


async def load_demo_genes() -> None:
    """Load test genes into the database."""

    for build, path in BUILD_GENES_RESOURCE:
        gene_lines: Iterator = resource_lines(path)
        await update_genes(build=build, session=db, lines=gene_lines)


async def load_demo_transcripts() -> None:
    """Load test transcripts into the database."""

    for build, path in BUILD_TRANSCRIPTS_RESOURCE:
        transcript_lines: Iterator = resource_lines(path)
        await update_transcripts(build=build, session=db, lines=transcript_lines)


async def load_demo_exons() -> None:
    """Load test exons into the database."""

    for build, path in BUILD_EXONS_RESOURCE:
        exon_lines: Iterator = resource_lines(path)
        await update_exons(build=build, session=db, lines=exon_lines)

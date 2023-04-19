from typing import Dict, List, Tuple, Iterator

from chanjo2.crud.cases import create_db_case
from chanjo2.crud.samples import create_sample_in_case
from chanjo2.dbutil import get_session
from chanjo2.demo import d4_demo_path
from chanjo2.models.pydantic_models import CaseCreate, SampleCreate, Builds
from schug.demo import (
    EXONS_37_FILE_PATH,
    EXONS_38_FILE_PATH,
    GENES_37_FILE_PATH,
    GENES_38_FILE_PATH,
    TRANSCRIPTS_37_FILE_PATH,
    TRANSCRIPTS_38_FILE_PATH,
)
from sqlalchemy.orm import sessionmaker

db: sessionmaker = next(get_session())

DEMO_CASE: Dict[str, str] = {"name": "internal_id", "display_name": "643594"}
DEMO_SAMPLE: Dict[str, str] = {
    "name": "ADM1059A2",
    "display_name": "NA12882",
    "case_name": DEMO_CASE["name"],
    "coverage_file_path": d4_demo_path,
}
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


def resource_lines(file_path: str) -> Iterator[str]:
    resource = open(file_path, "r", encoding="utf-8")
    lines: List = resource.readlines()
    lines: List = [line.rstrip("\n") for line in lines]
    return iter(lines)


def load_demo_data() -> None:
    """Loads demo data into the database of a demo instance of Chanjo2."""
    load_demo_case()
    load_demo_sample()
    load_demo_genes()


def load_demo_case() -> None:
    """Load a demo case into the database."""
    case: CaseCreate = CaseCreate(**DEMO_CASE)
    create_db_case(db=db, case=case)


def load_demo_sample() -> None:
    """Add a sample to a demo case."""
    sample: SampleCreate = SampleCreate(**DEMO_SAMPLE)
    create_sample_in_case(db=db, sample=sample)


def load_demo_genes() -> None:
    """Load 50 test genes into the database"""

    for build, path in BUILD_GENES_RESOURCE:
        gene_lines: Iterator = resource_lines(path)

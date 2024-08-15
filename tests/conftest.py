from pathlib import PosixPath
from typing import Dict, List, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chanjo2.constants import BUILD_37, BUILD_38
from chanjo2.crud.intervals import get_genes
from chanjo2.dbutil import DEMO_CONNECT_ARGS, get_session
from chanjo2.demo import d4_demo_path, gene_panel_path
from chanjo2.main import Base, app, engine
from chanjo2.meta.handle_bed import bed_file_interval_id_coords
from chanjo2.models import sql_models
from chanjo2.models.sql_models import Gene as SQLGene

TEST_DB = "sqlite:///./test.db"
COVERAGE_FILE = "a_file.d4"
BED_FILE = "a_file.bed"
REMOTE_COVERAGE_FILE = "https://a_remote_host/a_file.d4"
CONTENT: str = "content"
GENOMIC_IDS_37: Dict[str, List] = {
    "ensembl_exons_ids": ["ENSE00001799379", "ENSE00001499436", "ENSE00001676225"],
    "ensembl_transcript_ids": ["ENST00000418454", "ENST00000384428", "ENST00000414345"],
    "ensembl_gene_ids": ["ENSG00000233440", "ENSG00000207157", "ENSG00000196593"],
    "hgnc_ids": [19121, 42488, 42737],
    "hgnc_symbols": ["HMGA1P6", "RNY3P4", "ANKRD20A19P"],
}
GENOMIC_IDS_38: Dict[str, List] = {
    "ensembl_exons_ids": ["ENSE00003889014", "ENSE00003689846", "ENSE00003510521"],
    "ensembl_transcript_ids": ["ENST00000673477", "ENST00000378391", "ENST00000270722"],
    "ensembl_gene_ids": ["ENSG00000160072", "ENSG00000142611", "ENSG00000171729"],
    "hgnc_ids": [24007, 14000, 25488],
    "hgnc_symbols": ["ATAD3B", "PRDM16", "TMEM51"],
}

engine = create_engine(TEST_DB, connect_args=DEMO_CONNECT_ARGS)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Endpoints(str):
    """Contains all the app endpoints used in testing."""

    INTERVAL = "/intervals/interval/"
    INTERVALS = "/intervals/"
    LOAD_GENES = "/intervals/load/genes/"
    GENES = "/intervals/genes"
    LOAD_TRANSCRIPTS = "/intervals/load/transcripts/"
    TRANSCRIPTS = "/intervals/transcripts"
    LOAD_EXONS = "/intervals/load/exons/"
    EXONS = "/intervals/exons"
    INTERVAL_COVERAGE = "/coverage/d4/interval/"
    INTERVALS_FILE_COVERAGE = "/coverage/d4/interval_file/"
    GENES_COVERAGE_SUMMARY = "/coverage/d4/genes/summary"
    GET_SAMPLES_PREDICTED_SEX = "/coverage/samples/predicted_sex"
    REPORT_DEMO = "/report/demo/"
    REPORT = "/report"
    GENE_OVERVIEW = "/gene_overview"
    OVERVIEW = "/overview"
    OVERVIEW_DEMO = "/overview/demo/"


@pytest.fixture
def endpoints() -> Endpoints:
    """returns an instance of the class Endpoints"""
    return Endpoints


@pytest.fixture(name="test_db")
def test_db_fixture() -> str:
    """Returns a string representing the path to the test database file."""
    return TEST_DB


@pytest.fixture(name="session")
def session_fixture() -> sessionmaker:
    """Returns an object of type sqlalchemy.orm.session.sessionmaker."""

    # Create the database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal(future=True)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(name="client")
def client_fixture(session) -> TestClient:
    """Returns a fastapi.testclient.TestClient used to test the app endpoints."""

    def _override_get_db():
        try:
            db = session
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override_get_db

    return TestClient(app)


@pytest.fixture(name="demo_session", scope="function")
def demo_session_fixture() -> TestClient:
    """Returns an object of type sqlalchemy.orm.session.sessionmaker containing demo data."""
    return next(get_session())


@pytest.fixture(name="demo_client", scope="function")
def demo_client_fixture(demo_session) -> TestClient:
    """Returns a fastapi.testclient.TestClient used to test the endpoints of an app with a populated demo database."""

    def _override_get_db():
        try:
            db = demo_session
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override_get_db

    return TestClient(app)


@pytest.fixture(name="demo_genes_37")
def demo_genes_37(demo_session) -> List[sql_models.Gene]:
    """Return SQL Gene objects."""

    return get_genes(
        db=demo_session,
        build=BUILD_37,
        ensembl_ids=[],
        hgnc_ids=[],
        hgnc_symbols=GENOMIC_IDS_37["hgnc_symbols"],
        limit=None,
    )


@pytest.fixture(name="demo_sql_genes")
def demo_sql_genes() -> List[SQLGene]:
    """Return the 4 demo genes present in the demo gene panel as SQLGenes."""
    gene_dicts = [
        {
            "ensembl_id": "ENSG00000228716",
            "chromosome": "5",
            "start": 79922047,
            "stop": 79950802,
        },
        {
            "ensembl_id": "ENSG00000110195",
            "chromosome": "11",
            "start": 71900602,
            "stop": 71907345,
        },
        {
            "ensembl_id": "ENSG00000177000",
            "chromosome": "1",
            "start": 11845780,
            "stop": 11866977,
        },
        {
            "ensembl_id": "ENSG00000076351",
            "chromosome": "17",
            "start": 26721661,
            "stop": 26734215,
        },
    ]
    return [SQLGene(**gene) for gene in gene_dicts]


@pytest.fixture(name="mock_coverage_file")
def mock_coverage_file() -> str:
    """Returns the name of a mock coverage file."""
    return COVERAGE_FILE


@pytest.fixture(name="remote_coverage_file")
def remote_coverage_file() -> str:
    """Returns the URL of a mock coverage file."""
    return REMOTE_COVERAGE_FILE


@pytest.fixture(name="coverage_path")
def coverage_path(tmp_path) -> PosixPath:
    """Returns a mock temp coverage file."""

    tmp_coverage_file: PosixPath = tmp_path / COVERAGE_FILE
    tmp_coverage_file.touch()
    tmp_coverage_file.write_text(CONTENT)
    return tmp_coverage_file


@pytest.fixture(name="real_coverage_path")
def real_coverage_path() -> str:
    """Returns the string path to a demo D4 file present on disk."""
    return d4_demo_path


@pytest.fixture(name="bed_interval")
def bed_interval() -> Tuple[str, int, int]:
    """Returns a genomic interval (chr, start, stop) as a tuple."""
    return bed_file_interval_id_coords(file_path=gene_panel_path)[0][1]


@pytest.fixture(name="interval_query")
def interval_query(bed_interval) -> Dict:
    """Returns a query dictionary with genomic coordinates."""

    return {
        "chromosome": bed_interval[0],
        "start": bed_interval[1],
        "end": bed_interval[2],
    }


@pytest.fixture(name="real_d4_query")
def real_d4_query(real_coverage_path) -> Dict[str, str]:
    """Returns a query dictionary with the path to an existing D4 coverage file."""

    return {
        "coverage_file_path": real_coverage_path,
    }


@pytest.fixture(name="genomic_ids_per_build")
def genomic_ids_per_build() -> Dict[str, List]:
    """Return a dict containing lists with test genes in different build specific formats."""
    return {BUILD_37: GENOMIC_IDS_37, BUILD_38: GENOMIC_IDS_38}

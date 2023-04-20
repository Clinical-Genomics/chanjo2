from chanjo2.crud.cases import get_cases
from chanjo2.crud.intervals import get_genes, get_transcripts, get_exons
from chanjo2.crud.samples import get_samples
from chanjo2.dbutil import get_session
from chanjo2.main import app
from chanjo2.models.pydantic_models import Builds
from chanjo2.models.sql_models import Case, Sample, Gene, Transcript, Exon
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

client = TestClient(app)
db: sessionmaker = next(get_session())


def test_load_demo_data():
    """Test loading demo data."""

    # WHEN the app is launched
    with TestClient(app) as client:
        # THEN database should contain a case
        cases: List[Case] = get_cases(db=db)
        assert isinstance(cases[0], Case)

        # THEN database should contain samples
        samples: List[Sample] = get_samples(db=db)
        assert isinstance(samples[0], Sample)

        # THEN for each genome build
        for build in Builds.get_enum_values():
            # database should contain genes
            genes: List[Gene] = get_genes(
                db=db,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                limit=1,
            )
            assert isinstance(genes[0], Gene)

            # database should contain transcripts
            transcripts: List[Transcripts] = get_transcripts(
                db=db, build=build, limit=1
            )
            assert isinstance(transcripts[0], Transcript)

            # database should contain exons
            exons: List[exons] = get_exons(db=db, build=build, limit=1)
            assert isinstance(exons[0], Exon)

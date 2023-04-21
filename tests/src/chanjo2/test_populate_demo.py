from chanjo2.crud.cases import get_cases
from chanjo2.crud.intervals import get_genes, get_gene_intervals
from chanjo2.crud.samples import get_samples
from chanjo2.models.pydantic_models import Builds
from chanjo2.models.sql_models import Case, Sample, Gene, Transcript, Exon
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


def test_load_demo_data(demo_client: TestClient, demo_session: sessionmaker):
    """Test loading demo data."""

    # WHEN the app is launched
    with demo_client:
        # THEN database should contain a case
        cases: List[Case] = get_cases(db=demo_session)
        assert isinstance(cases[0], Case)

        # THEN database should contain samples
        samples: List[Sample] = get_samples(db=demo_session)
        assert isinstance(samples[0], Sample)

        # THEN for each genome build
        for build in Builds.get_enum_values():
            # database should contain genes
            genes: List[Gene] = get_genes(
                db=demo_session,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                limit=1,
            )
            assert isinstance(genes[0], Gene)

            # database should contain transcripts
            transcripts: List[Transcripts] = get_gene_intervals(
                db=demo_session,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=None,
                limit=1,
                interval_type=Transcript,
            )
            assert isinstance(transcripts[0], Transcript)

            # database should contain exons
            exons: List[Transcripts] = get_gene_intervals(
                db=demo_session,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=None,
                limit=1,
                interval_type=Exon,
            )
            assert isinstance(exons[0], Exon)

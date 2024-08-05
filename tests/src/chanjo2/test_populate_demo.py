from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from chanjo2.crud.intervals import get_gene_intervals, get_genes
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import Builds


def test_load_demo_data(demo_client: TestClient, demo_session: sessionmaker):
    """Test loading demo data."""

    # WHEN the app is launched
    with demo_client:

        # THEN for each genome build
        for build in Builds.get_enum_values():
            # database should contain genes
            genes: List[SQLGene] = get_genes(
                db=demo_session,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                limit=1,
            )
            assert isinstance(genes[0], SQLGene)

            # database should contain transcripts
            transcripts: List[SQLTranscripts] = get_gene_intervals(
                db=demo_session,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=None,
                limit=1,
                interval_type=SQLTranscript,
            )
            assert isinstance(transcripts[0], SQLTranscript)

            # database should contain exons
            exons: List[SQLExon] = get_gene_intervals(
                db=demo_session,
                build=build,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=None,
                limit=1,
                interval_type=SQLExon,
            )
            assert isinstance(exons[0], SQLExon)

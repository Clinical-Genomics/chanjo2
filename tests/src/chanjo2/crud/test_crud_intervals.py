from typing import List, Dict

from sqlalchemy.orm import sessionmaker

from chanjo2.constants import BUILD_37
from chanjo2.crud.intervals import get_gene_intervals
from chanjo2.models import SQLTranscript


def test_get_gene_intervals_all_transcripts(
    demo_session: sessionmaker, genomic_ids_per_build: Dict[str, List]
):
    """Retrieve all transcripts from a gene list using the get_gene_intervals function."""

    # WHEN all transcripts get collected
    transcripts: List[SQLTranscript] = get_gene_intervals(
        db=demo_session,
        build=BUILD_37,
        interval_type=SQLTranscript,
        hgnc_ids=genomic_ids_per_build[BUILD_37]["hgnc_ids"],
    )

    # THEN they might or might not have a refseq_mrna ID
    for transcript in transcripts:
        assert transcript.refseq_mrna or transcript.refseq_mrna is None


def test_get_gene_intervals_refseq_mrna_transcripts(
    demo_session: sessionmaker, genomic_ids_per_build: Dict[str, List]
):
    """Retrieve all transcripts with refseq_mrna ID from a gene list using the get_gene_intervals function."""

    # WHEN all transcripts with refseq_mrna get collected
    transcripts: List[SQLTranscript] = get_gene_intervals(
        db=demo_session,
        build=BUILD_37,
        interval_type=SQLTranscript,
        hgnc_ids=genomic_ids_per_build[BUILD_37]["hgnc_ids"],
        transcript_tags=["refseq_mrna"],
    )
    # THEN they should have a refseq_mrna ID
    for transcript in transcripts:
        assert transcript.refseq_mrna

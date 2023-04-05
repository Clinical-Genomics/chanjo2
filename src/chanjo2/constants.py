from typing import Callable, Dict, List

from schug.load.ensembl import (
    fetch_ensembl_exon_lines,
    fetch_ensembl_genes,
    fetch_ensembl_transcripts,
)

WRONG_COVERAGE_FILE_MSG: str = (
    "Coverage_file_path must be either an existing local file path or a URL"
)
WRONG_BED_FILE_MSG: str = "Provided intervals files is not a valid BED file"

ENSEMBL_RESOURCE_CLIENT: Dict[str, Callable] = {
    "genes": fetch_ensembl_genes,
    "transcripts": fetch_ensembl_transcripts,
    "exons": fetch_ensembl_exon_lines,
}

GENES_FILE_HEADER: Dict[str, List[str]] = {
    "GRCh37": [
        "Chromosome Name",
        "Gene Start (bp)",
        "Gene End (bp)",
        "Ensembl Gene ID",
        "HGNC symbol",
        "HGNC ID(s)",
    ],
    "GRCh38": [
        "Chromosome/scaffold name",
        "Gene start (bp)",
        "Gene end (bp)",
        "Gene stable ID",
        "HGNC symbol",
        "HGNC ID",
    ],
}

TRANSCRIPTS_FILE_HEADER: Dict[str, List[str]] = {
    "GRCh37": [
        "Chromosome Name",
        "Ensembl Gene ID",
        "Ensembl Transcript ID",
        "Transcript Start (bp)",
        "Transcript End (bp)",
        "RefSeq mRNA [e.g. NM_001195597]",
        "RefSeq mRNA predicted [e.g. XM_001125684]",
        "RefSeq ncRNA [e.g. NR_002834]",
    ],
    "GRCh38": [
        "Chromosome/scaffold name",
        "Gene stable ID",
        "Transcript stable ID",
        "Transcript start (bp)",
        "Transcript end (bp)",
        "RefSeq mRNA ID",
        "RefSeq mRNA predicted ID",
        "RefSeq ncRNA ID",
        "RefSeq match transcript (MANE Select)",
        "RefSeq match transcript (MANE Plus Clinical)",
    ],
}


EXONS_FILE_HEADER: Dict[str, List[str]] = {
    "GRCh37": [
        "Chromosome Name",
        "Ensembl Gene ID",
        "Ensembl Transcript ID",
        "Ensembl Exon ID",
        "Exon Chr Start (bp)",
        "Exon Chr End (bp)",
        "5' UTR Start",
        "5' UTR End",
        "3' UTR Start",
        "3' UTR End",
        "Strand",
        "Exon Rank in Transcript",
    ],
    "GRCh38": [
        "Chromosome/scaffold name",
        "Gene stable ID",
        "Transcript stable ID",
        "Exon stable ID",
        "Exon region start (bp)",
        "Exon region end (bp)",
        "5' UTR start",
        "5' UTR end",
        "3' UTR start",
        "3' UTR end",
        "Strand",
        "Exon rank in transcript",
    ],
}

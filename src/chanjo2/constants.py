from typing import Callable, Dict, List

from schug.load.ensembl import (
    fetch_ensembl_exons,
    fetch_ensembl_genes,
    fetch_ensembl_transcripts,
)

SAMPLE_NOT_FOUND: str = "One of more requested samples were not present in the database"
WRONG_COVERAGE_FILE_MSG: str = (
    "Coverage_file_path must be either an existing local file path or a URL"
)
WRONG_BED_FILE_MSG: str = "Provided intervals files is not a valid BED file"
MULTIPLE_PARAMS_NOT_SUPPORTED_MSG = "Interval query contains too many filter parameters. Please specify genome build and max one type of filter."
GENE_LISTS_NOT_SUPPORTED_MSG = (
    "Please provide either Ensembl gene IDs, HGNC gene IDS or HGNC gene symbols."
)
AMBIGUOUS_SAMPLES_INPUT = "Please provide either a name of a case or a list of samples."

ENSEMBL_RESOURCE_CLIENT: Dict[str, Callable] = {
    "genes": fetch_ensembl_genes,
    "transcripts": fetch_ensembl_transcripts,
    "exons": fetch_ensembl_exons,
}

BUILD_37 = "GRCh37"
BUILD_38 = "GRCh38"
CHROMOSOME_NAME_37: str = "Chromosome Name"
CHROMOSOME_NAME_38: str = "Chromosome/scaffold name"
ENSEMBL_GENE_ID_37: str = "Ensembl Gene ID"
ENSEMBL_GENE_ID_38: str = "Gene stable ID"

GENES_FILE_HEADER: Dict[str, List[str]] = {
    BUILD_37: [
        CHROMOSOME_NAME_37,
        "Gene Start (bp)",
        "Gene End (bp)",
        ENSEMBL_GENE_ID_37,
        "HGNC symbol",
        "HGNC ID(s)",
    ],
    BUILD_38: [
        CHROMOSOME_NAME_38,
        "Gene start (bp)",
        "Gene end (bp)",
        ENSEMBL_GENE_ID_38,
        "HGNC symbol",
        "HGNC ID",
    ],
}

CHROMOSOMES = [str(i) for i in range(0, 23)] + ["X", "Y", "MT"]

TRANSCRIPTS_FILE_HEADER: Dict[str, List[str]] = {
    BUILD_37: [
        CHROMOSOME_NAME_37,
        ENSEMBL_GENE_ID_37,
        "Ensembl Transcript ID",
        "Transcript Start (bp)",
        "Transcript End (bp)",
        "RefSeq mRNA [e.g. NM_001195597]",
        "RefSeq mRNA predicted [e.g. XM_001125684]",
        "RefSeq ncRNA [e.g. NR_002834]",
    ],
    BUILD_38: [
        CHROMOSOME_NAME_38,
        ENSEMBL_GENE_ID_38,
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
    BUILD_37: [
        CHROMOSOME_NAME_37,
        ENSEMBL_GENE_ID_37,
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
    BUILD_38: [
        CHROMOSOME_NAME_38,
        ENSEMBL_GENE_ID_38,
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

DEFAULT_COMPLETENESS_LEVELS = [10, 15, 20, 50, 100]
DEFAULT_COVERAGE_LEVEL = 10

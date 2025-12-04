from typing import Callable, Dict, List

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
HTTP_D4_COMPLETENESS_ERROR = "Completeness_thresholds must not be provided if any sample.coverage_file_path is a URL"

BUILD_37 = "GRCh37"
BUILD_38 = "GRCh38"
CHROMOSOME_NAME: str = "Chromosome/scaffold name"
ENSEMBL_GENE_ID: str = "Gene stable ID"

GENES_FILE_HEADER: list[str] = [
    CHROMOSOME_NAME,
    "Gene start (bp)",
    "Gene end (bp)",
    ENSEMBL_GENE_ID,
    "HGNC symbol",
    "HGNC ID",
    "Gene type",
]

CHROMOSOMES = [str(i) for i in range(0, 23)] + ["X", "Y", "MT"]

TRANSCRIPTS_FILE_HEADER_37: list[str] = [
    CHROMOSOME_NAME,
    ENSEMBL_GENE_ID,
    "Transcript stable ID",
    "Transcript start (bp)",
    "Transcript end (bp)",
    "RefSeq mRNA ID",
    "RefSeq mRNA predicted ID",
    "RefSeq ncRNA ID",
]

TRANSCRIPTS_FILE_HEADER: list[str] = TRANSCRIPTS_FILE_HEADER_37 + [
    "RefSeq match transcript (MANE Select)",
    "RefSeq match transcript (MANE Plus Clinical)",
]

EXONS_FILE_HEADER: list[str] = [
    CHROMOSOME_NAME,
    ENSEMBL_GENE_ID,
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
]


DEFAULT_COMPLETENESS_LEVELS = [10, 15, 20, 50, 100]
DEFAULT_COVERAGE_LEVEL = 10

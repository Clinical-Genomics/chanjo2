from typing import List

WRONG_COVERAGE_FILE_MSG: str = (
    "Coverage_file_path must be either an existing local file path or a URL"
)
WRONG_BED_FILE_MSG: str = "Provided intervals files is not a valid BED file"

GENES_FILE_HEADER = {
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

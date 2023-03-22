from typing import List

WRONG_COVERAGE_FILE_MSG: str = (
    "Coverage_file_path must be either an existing local file path or a URL"
)
WRONG_BED_FILE_MSG: str = "Provided intervals files is not a valid BED file"

GENES_FILE_HEADER: List = [
    "Chromosome Name",
    "Gene Start (bp)",
    "Gene End (bp)",
    "Ensembl Gene ID",
    "HGNC symbol",
    "HGNC ID(s)",
]

GENE_TAG = "gene"

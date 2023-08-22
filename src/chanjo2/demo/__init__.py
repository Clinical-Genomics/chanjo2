from importlib_resources import files

BASE_PATH: str = "chanjo2.demo"

GENE_PANEL_FILE: str = "109_green.bed"
D4_DEMO_FILE: str = "panelapp_109_example.d4"

# Paths
gene_panel_path = str(files(BASE_PATH).joinpath(GENE_PANEL_FILE))
d4_demo_path = str(files(BASE_PATH).joinpath(D4_DEMO_FILE))

# Data for generating a demo coverage report
DEMO_COVERAGE_QUERY_DATA = {
    "build": BUILD_37,
    "hgnc_gene_symbols": ["ATAD3B", "PRDM16", "TMEM51"],
    "samples": [{
        "name":
    }],
    "case": "internal_id",
    "interval_type": "genes",
    "gene_panel": "Test Panel",
    "ensembl_gene_ids": [],
    "hgnc_gene_ids": [],
    "hgnc_gene_symbols": ["HMGA1P6", "RNY3P4", "ANKRD20A19P"],
}

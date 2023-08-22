from datetime import datetime

from importlib_resources import files

from chanjo2.models.pydantic_models import Sex

BASE_PATH: str = "chanjo2.demo"

GENE_PANEL_FILE: str = "109_green.bed"
D4_DEMO_FILE: str = "panelapp_109_example.d4"

DEMO_CASE: Dict[str, str] = {"name": "internal_id", "display_name": "643594"}

DEMO_SAMPLE: Dict[str, str] = {
    "name": "ADM1059A2",
    "display_name": "NA12882",
    "track_name": "ADM1059A2",
    "case_name": DEMO_CASE["name"],
    "coverage_file_path": d4_demo_path,
}

# Paths
gene_panel_path = str(files(BASE_PATH).joinpath(GENE_PANEL_FILE))
d4_demo_path = str(files(BASE_PATH).joinpath(D4_DEMO_FILE))

# Data for generating a demo coverage report
DEMO_COVERAGE_QUERY_DATA = {
    "build": BUILD_37,
    "samples": [
        {
            "name": DEMO_SAMPLE["name"],
            "case_name": DEMO_CASE["name"],
            "coverage_file_path": d4_demo_path,
            "analysis_date": datetime.now(),
            "sex": Sex.MALE,
        }
    ],
    "gene_panel": "A test Panel 1.0",
    "interval_type": "genes",
    "ensembl_gene_ids": [],
    "hgnc_gene_ids": [],
    "hgnc_gene_symbols": ["HMGA1P6", "RNY3P4", "ANKRD20A19P"],
}

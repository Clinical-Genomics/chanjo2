from typing import Dict

from importlib_resources import files

from chanjo2.constants import BUILD_37

BASE_PATH: str = "chanjo2.demo"

GENE_PANEL_FILE: str = "109_green.bed"
D4_DEMO_FILE: str = "panelapp_109_example.d4"

# Paths
gene_panel_path = str(files(BASE_PATH).joinpath(GENE_PANEL_FILE))
d4_demo_path = str(files(BASE_PATH).joinpath(D4_DEMO_FILE))

DEMO_CASE: Dict[str, str] = {"name": "internal_id", "display_name": "643594"}

DEMO_SAMPLE: Dict[str, str] = {
    "name": "ADM1059A2",
    "display_name": "NA12882",
    "track_name": "ADM1059A2",
    "case_name": DEMO_CASE["name"],
    "coverage_file_path": d4_demo_path,
}

HTTP_SERVER_D4_file = "https://d4-format-testing.s3.us-west-1.amazonaws.com/hg002.d4"

# Data for generating a demo coverage report
DEMO_COVERAGE_QUERY_DATA = {
    "build": BUILD_37,
    "samples": [
        {
            "name": DEMO_SAMPLE["name"],
            "case_name": DEMO_CASE["name"],
            "coverage_file_path": d4_demo_path,
            "analysis_date": "2023-04-23T10:20:30.400+02:30",
        }
    ],
    "gene_panel": "Panelapp panel 109: Cerebral folate deficiency",
    "interval_type": "genes",
    "ensembl_gene_ids": [],
    "hgnc_gene_ids": [7436, 2861, 3791, 30521],
    "hgnc_gene_symbols": [],
}

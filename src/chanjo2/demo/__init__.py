from typing import Dict

from importlib_resources import files

from chanjo2.constants import BUILD_37, DEFAULT_COMPLETENESS_LEVELS

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
DEMO_HGNC_GENE_SYMBOLS = ["MTHFR", "DHFR", "FOLR1", "SLC46A1", "LAMA1", "PIPPI6"]
DEMO_HGNC_IDS = [7436, 2861, 3791, 30521]
ANALYSIS_DATE = "2023-04-23T10:20:30.400+02:30"


# HTTP FORM-like data for generating a demo coverage report
DEMO_COVERAGE_QUERY_FORM = {
    "build": BUILD_37,
    "samples": f"[{{'name': '{DEMO_SAMPLE['name']}', 'coverage_file_path': '{d4_demo_path}', 'case_name': '{DEMO_CASE['name']}', 'analysis_date': '{ANALYSIS_DATE}'}}]",
    "case_display_name": DEMO_CASE["name"],
    "gene_panel": "A test Panel 1.0",
    "interval_type": "transcripts",
    "ensembl_gene_ids": [],
    "hgnc_gene_ids": [],
    "hgnc_gene_symbols": ",".join(DEMO_HGNC_GENE_SYMBOLS),
    "default_level": "20",
    "completeness_thresholds": ",".join(
        [str(threshold) for threshold in DEFAULT_COMPLETENESS_LEVELS]
    ),
}

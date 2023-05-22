from importlib_resources import files

BASE_PATH: str = "chanjo2.demo"

GENE_PANEL_FILE: str = "109_green.bed"
D4_DEMO_FILE: str = "panelapp_109_example.d4"

# Paths
gene_panel_path = str(files(BASE_PATH).joinpath(gene_panel_file))
d4_demo_path = str(files(BASE_PATH).joinpath(d4_demo_file))

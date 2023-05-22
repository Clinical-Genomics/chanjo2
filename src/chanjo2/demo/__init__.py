from importlib_resources import files

BASE_PATH = "chanjo2.demo"

gene_panel_file = "109_green.bed"
d4_demo_file = "panelapp_109_example.d4"

# Paths
gene_panel_path = str(files(BASE_PATH).joinpath(gene_panel_file))
d4_demo_path = str(files(BASE_PATH).joinpath(d4_demo_file))

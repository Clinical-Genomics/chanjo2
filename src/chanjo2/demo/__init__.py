import pkg_resources

# Files
gene_panel_file = "demo/109_green.bed"
d4_demo_file = "demo/panelapp_109_example.d4"

# Paths
gene_panel_path = pkg_resources.resource_filename("chanjo2", gene_panel_file)
d4_demo_path = pkg_resources.resource_filename("chanjo2", d4_demo_file)

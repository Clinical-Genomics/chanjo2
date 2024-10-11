# Creating a coverage report for one or more samples based on a list of genes

An example of this report is shown by the demo report endpoint: http://0.0.0.0:8000/report/demo (requires all genes and gene transcripts in build GRCh37 loaded into the database).

<img width="924" alt="image" src="https://github.com/Clinical-Genomics/chanjo2/assets/28093618/02fcfcc8-94ce-4344-bc02-fae4609810cb">

The statistics from the report above are computed using the transcripts intervals present in the provided genes.

Given an application running in production settings, with **genes, transcripts and exons** loaded into the database, a coverage report like the one above can be created taking into account one of these types of intervals from any gene of choice.

The gene list might be provided as a list of **Ensembl gene IDs, HGNC gene IDs or HGNC gene symbols**.

Here is what the request data of a **POST request to the `/report` endpoint** looks like:

``` shell
{
  "build": "GRCh37",
  "completeness_thresholds": [
    10,
    15,
    20,
    50,
    100
  ],
  "ensembl_gene_ids": [],
  "hgnc_gene_ids": [],
  "hgnc_gene_symbols": [],
  "interval_type": "genes",
  "default_level": 10,
  "panel_name": "Custom panel",
  "case_display_name": "internal_id",
  "samples": [
    {
      "name": "string",
      "coverage_file_path": "string",
      "case_name": "string",
      "analysis_date": "2023-10-04T08:22:06.980106"
    }
  ]
}
```

### Mandatory parameters

- **build** _either "GRCh37" or "GRCh38"_
- **ensembl_gene_ids OR hgnc_gene_ids OR hgnc_gene_symbols** _either a list of strings (for Ensembl IDs or HGNC symbols or a list of integers for HGNC IDs_
- **interval_type** _either "genes", "transcripts" or "exons", depending on the analysis type (WGS, WES, WTS)_
- **default_level** _default coverage threshold level to take into account for displaying the number of fully covered or partially covered intervals_
- **samples** _mandatory parameters are **name** and either **coverage_file_path** or **case_name**_

### Optional parameters

- **completeness_thresholds** _the list of different coverage thresholds that will be used to calculate gene coverage completeness. If not provided, the default threshold values will be: 10, 15, 20, 50, 100_
- **panel_name** _Add a name only if the provided genes are part of a gene panel_
- **case_display_name** _provide this string parameter if the case belong to the same case / group_
- **samples analysis_date** _if not provided with be set to current date_


# Creating a genes coverage overview report to show incompletely covered genomic intervals

This type of report contains stats from incompletely covered genomic intervals at different coverage thresholds and is basically the same as the genes overview report provided by [chanjo-report](https://github.com/Clinical-Genomics/chanjo-report/blob/9ca7a8ad279ab862c148ce4dfe2b2e675fdc4be4/chanjo_report/server/blueprints/report/views.py#L46).

A demo genes overview report based on genes transcripts from the demo PanelApp genes is available at the demo overview endpoint: http://0.0.0.0:8000/overview/demo (requires all genes and gene transcripts in build GRCh37 loaded into the database).

<img width="1014" alt="image" src="https://github.com/Clinical-Genomics/chanjo2/assets/28093618/70bfdfb4-2345-47dd-b6e4-f6ea49d43cbc">

To create a custom genes coverage overview report, send a **POST request to the `/overview` endpoint** containing the same request data described above for the `/report` endpoint.


# Creating coverage overview over MANE transcripts for a list of genes

<img width="1278" alt="image" src="https://github.com/user-attachments/assets/44eaa5c0-3777-42d0-8713-c33a2c5108cc">

This report contains statistics over all MANE Select and Mane Plus Clinical transcripts for a list of genes provided by the user. 

The **`/mane_overview` endpoint** accepts POST request with the same data described for the 2 reports above.

Note that MANE overview reports are available <ins>only for analyses run with genome build GRCh38</ins>.









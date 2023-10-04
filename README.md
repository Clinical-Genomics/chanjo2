# chanjo2

![Build Status - GitHub][actions-build-status]
[![PyPI Version][pypi-img]][pypi-url]
[![Code style: black][black-image]][black-url]
[![Coverage Status][codecov-img]][codecov-url]
![GitHub commits latest][latest-commit]
![GitHub commit rate][commit-rate]

Chanjo2 is <strong>coverage analysis tool for human clinical sequencing data</strong> using the <strong>[d4 (Dense Depth Data Dump) format][d4-article]</strong>. 
It's implemented in Python [FastAPI][fastapi] and provides API endpoints to communicate with a d4tools software in order to 
<strong>return coverage and coverage completeness over genomic intervals (genes, transcripts, exons as well as custom intervals)</strong> over 
single d4 files or samples stored in the database with associated d4 files.


## Run a software demo containing test data

A demo REST server connected with a temporary SQLite database can be launched using Docker:

``` shell
docker run -d --rm  -p 8000:8000 --expose 8000 clinicalgenomics/chanjo2:latest
```

The endpoints of the app will be now reachable and described from any web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs

From a terminal, you can use the API to access the data contained in the demo database of this Chanjo2 instance:

### Examples of endpoints usage:

#### Return available cases (cases are collections of related samples):

``` shell
curl -X 'GET' \
  'http://localhost:8000/cases/' \
  -H 'accept: application/json'
```

This will return a json response describing the demo case and its associated sample:

``` shell
[
  {
    "display_name": "643594",
    "name": "internal_id",
    "id": 1,
    "samples": [
      {
        "coverage_file_path": "/home/worker/app/src/chanjo2/demo/panelapp_109_example.d4",
        "display_name": "NA12882",
        "track_name": "ADM1059A2",
        "name": "ADM1059A2",
        "case_id": 1,
        "created_at": "2023-06-01T08:05:12",
        "id": 1
      }
    ]
  }
]
```

The available demo sample contains a d4 coverage file with a limited amount of genes in genome build GRCh37, those present in [PanelApp gene panel 109 (Cerebral folate deficiency)][panelapp-109]: .

#### Loading genes to the database

In order to perform coverage queries over genes, transcripts and exons, these genomic intervals should be saved into the database first. Genes, transcripts and exons definitions are collected from [Ensembl][ensembl] using a BioMart service.

To load genes in genome build GRCh37 from into the database send the following POST request to the server:


``` shell
curl -X 'POST' \
  'http://localhost:8000/intervals/load/genes/GRCh37' \
  -H 'accept: application/json' \
  -d ''
```

The response will return the number of genes inserted in the database:

``` shell
{
  "detail": "57849 genes loaded into the database"
}
```

#### Return coverage data over genes of database sample

Sequencing coverage and coverage completeness statistics can be returned for genes, transcripts and exons by providing a list of genes.
The provided gene list accepts genes in the following formats:
- Ensembl gene IDs
- HGNC ids
- HGNC symbols

- The user should also **specify a valid genome build - either GRCh37 or GRCh38.**

For instance, to retrieve coverage stats for the demo sample (mean gene coverage and coverage completeness with sequencing depth of for instance 30, 20 and 10) over the genes the Cerebral folate deficiency PanelAPP panel (*DHFR, FOLR1, MTHFR, SLC46A1* genes), send the following POST request:

``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/samples/genes_coverage' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
   "completeness_thresholds": [
    30, 20.10
  ],
  "hgnc_gene_symbols": [
    "FOLR1", "DHFR", "MTHFR", "SLC46A1"
  ],
  "case": "internal_id"
}'
```

That will return this response, containing the requested statistics over the list of 4 genes:

``` shell
{
  "ADM1059A2": [
    {
      "mean_coverage": 22.76,
      "completeness": {
        "10": 0.89,
        "20": 0.74,
        "30": 0.21
      },
      "interval_id": null,
      "interval_type": "genes",
      "inner_intervals": [],
      "hgnc_id": 2861,
      "hgnc_symbol": "DHFR",
      "ensembl_gene_id": "ENSG00000228716"
    },
    {
      "mean_coverage": 22.48,
      "completeness": {
        "10": 1,
        "20": 0.77,
        "30": 0.03
      },
      "interval_id": null,
      "interval_type": "genes",
      "inner_intervals": [],
      "hgnc_id": 3791,
      "hgnc_symbol": "FOLR1",
      "ensembl_gene_id": "ENSG00000110195"
    },
    {
      "mean_coverage": 22.07,
      "completeness": {
        "10": 1,
        "20": 0.69,
        "30": 0.07
      },
      "interval_id": null,
      "interval_type": "genes",
      "inner_intervals": [],
      "hgnc_id": 7436,
      "hgnc_symbol": "MTHFR",
      "ensembl_gene_id": "ENSG00000177000"
    },
    {
      "mean_coverage": 22.2,
      "completeness": {
        "10": 0.99,
        "20": 0.7,
        "30": 0.09
      },
      "interval_id": null,
      "interval_type": "genes",
      "inner_intervals": [],
      "hgnc_id": 30521,
      "hgnc_symbol": "SLC46A1",
      "ensembl_gene_id": "ENSG00000076351"
    }
  ]
}
```

To find more information on how to set up a REST server running chanjo2 please visit the software's [documentation pages][github-docs]. Here you'll find also instructions on how to populate the database with custom cases and different genomic intervals.


#### Coverage report and genes coverage overview

Chanjo2 can be directly used to create the same types of report produced by [chanjo-report][chanjo-report] in conjunction with chanjo[chanjo].

Given a running demo instance of chanjo2, with gene genes and transcripts from genome build GRCh37 loaded in the database, an example of the coverage report based on PanelAPP gene panel described is provided by this demo report endpoint: http://0.0.0.0:8000/report/demo:

<img width="816" alt="image" src="https://github.com/Clinical-Genomics/chanjo2/assets/28093618/dfeb0db8-a5ed-4a2e-9e65-ad2fa34b9816">

Similarly, an example report containing an overview of the genes with partial coverage at the given coverage thresholds is provided by the demo overview endpoint:

<img width="1014" alt="image" src="https://github.com/Clinical-Genomics/chanjo2/assets/28093618/70bfdfb4-2345-47dd-b6e4-f6ea49d43cbc">

Follow the instructions present in the [documentation pages][github-docs] to learn how to use the report and the overview endpoints to create customised gene coverage report using this software.



[actions-build-status]: https://github.com/Clinical-Genomics/chanjo2/actions/workflows/build_and_push_docker_stage.yml/badge.svg
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black
[chanjo2]: https://github.com/Clinical-Genomics/chanjo
[chanjo-report]: https://github.com/Clinical-Genomics/chanjo-report
[codecov-img]: https://codecov.io/gh/Clinical-Genomics/chanjo2/branch/main/graph/badge.svg?token=6U8ILA2SOY
[codecov-url]: https://codecov.io/gh/Clinical-Genomics/chanjo2
[d4-article]: https://www.nature.com/articles/s43588-021-00085-0
[ensembl]: https://useast.ensembl.org/index.html
[fastapi]: https://fastapi.tiangolo.com/
[github-docs]: https://clinical-genomics.github.io/chanjo2/
[latest-commit]: https://img.shields.io/github/commits-since/Clinical-Genomics/chanjo2/latest
[commit-rate]: https://img.shields.io/github/commit-activity/w/Clinical-Genomics/chanjo2
[panelapp-109]: https://panelapp.genomicsengland.co.uk/panels/109/
[pypi-img]: https://img.shields.io/pypi/v/chanjo2.svg?style=flat-square
[pypi-url]: https://pypi.python.org/pypi/chanjo2

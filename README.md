# chanjo2

![Build Status - GitHub][actions-build-status]
[![PyPI Version][pypi-img]][pypi-url]
[![Code style: black][black-image]][black-url]
[![Coverage Status][codecov-img]][codecov-url]
![GitHub commits latest][latest-commit]
![GitHub commit rate][commit-rate]

Chanjo2 is <strong>coverage analysis tool for human clinical sequencing data</strong> using the <strong>[d4 (Dense Depth Data Dump) format][d4-article]</strong>. 
It's implemented in Python [FastAPI][fastapi] and provides API endpoints to communicate with a d4tools software in order to 
<strong>return reports containing coverage and coverage completeness over genomic intervals (genes, transcripts, exons as well as custom intervals)</strong> over d4 files.

## Coverage and coverage overview reports

Chanjo2 can be directly used to create the same types of report produced by [chanjo-report][chanjo-report] in conjunction with chanjo[chanjo].
Follow the instructions present in the [documentation pages][github-docs] to learn how to use the report and the overview endpoints to create customised gene coverage report using this software.

Examples of reports available with chanjo2:

### Coverage report

<img width="924" alt="image" src="https://github.com/Clinical-Genomics/chanjo2/assets/28093618/02fcfcc8-94ce-4344-bc02-fae4609810cb">

### Genes coverage overview

<img width="1014" alt="image" src="https://github.com/Clinical-Genomics/chanjo2/assets/28093618/70bfdfb4-2345-47dd-b6e4-f6ea49d43cbc">

### Mane coverage overview

<img width="1278" alt="image" src="https://github.com/user-attachments/assets/44eaa5c0-3777-42d0-8713-c33a2c5108cc">

### Gene overview

<img width="1313" alt="image" src="https://github.com/user-attachments/assets/47e7d4e4-7404-46a3-981a-2dd94677b225">


## Run a software demo containing test data

A demo REST server connected with a temporary SQLite database can be launched using Docker:

``` shell
docker run -d --rm  -p 8000:8000 --expose 8000 clinicalgenomics/chanjo2:latest
```

The endpoints of the app will be now reachable and described from any web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs


From a terminal, you can use the API to access the data contained in the demo database of this Chanjo2 instance. The available demo sample contains a d4 coverage file with a limited amount of genes in genome build GRCh37, those present in [PanelApp gene panel 109 (Cerebral folate deficiency)][panelapp-109].

### Examples of endpoints usage:

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

To find more information on how to set up a REST server running chanjo2 please visit the software's [documentation pages][github-docs]. Here you'll find also instructions on how to populate the database with custom cases and different genomic intervals.



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

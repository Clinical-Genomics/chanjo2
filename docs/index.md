# Chanjo2 documentation pages

Chanjo2 is <strong>coverage analysis tool for clinical sequencing data</strong> using the <strong>[d4 (Dense Depth Data Dump) format][d4-article]</strong>. 
It's implemented in Python [FastAPI][fastapi] and provides API endpoints to communicate with a d4tools software in order to 
<strong>return coverage and coverage completeness over genomic intervals (genes, transcripts, exons as well as custom intervals)</strong> over 
single d4 files or samples stored in the database with associated d4 files.


The tool is flexible and can be used in different ways. The simplest use case would be calculating sequencing coverage over one or more intervals for a d4 file stored locally or remotely on the internet.

## Chanjo2 image as a proxy to d4tools to compute coverage stats over genomic intervals of a d4 file

Chanjo2 image contains [d4tools][d4tools-tool] and can be used to directly retrieve statistics over d4 files.

* Executing d4tools:
``` bash 
docker run --entrypoint d4tools --rm  clinicalgenomics/chanjo2-stage:latest
```

### Calculating coverage on specific genomic intervals of a d4 file using d4tools

``` shell
docker run --entrypoint d4tools --rm  -v <path-to-local-d4-files-folder>:/home/worker/infiles clinicalgenomics/chanjo2-stage:latest view /home/worker/infiles/<d4file.d4> 1:1234560-1234580 X:1234560-1234580
```

## Chanjo2 as a REST server

When chanjo2 is launched and runs as a REST server, it is offering many additional features, including:

* `The possibility to store samples with associated d4 files in a SQL-based database` so that coverage info can be retrieved for sample and groupd of sample (cases).
* `Support for calculating coverage and coverage completeness over genes, transcripts and exons for different genome builds`
* Chanjo2 server can be either installed on a virtual environment using [poetry][python-poetry] of directly launched using [Docker][docker]

Instructions on how to set up and run Chanjo2 as a REST server as well as the functionalities that it offers are better illustrated in these dedicated pages.


[d4-article]: https://www.nature.com/articles/s43588-021-00085-0
[d4tools-tool]: https://github.com/38/d4-format
[docker]: https://www.docker.com/ 
[fastapi]: https://fastapi.tiangolo.com/
[python-poetry]: https://python-poetry.org/

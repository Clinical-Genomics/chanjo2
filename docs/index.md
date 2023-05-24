# Welcome to the documentation pages of Chanjo2

Chanjo2 is coverage analysis for clinical sequencing data using the [d4 (Dense Depth Data Dump) format][d4-github]. 
It's implemented in Python [FastAPI][fastapi] and provides API endpoints to return coverage stats on genomic intervals (gene, transcripts, exons and custom intervals) over 
single d4 files or samples stored in the database.


## Simple use case: launch a chanjo2 with Docker to return stats over genomic intervals of a d4 file




* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.


[fastapi]: https://fastapi.tiangolo.com/
[d4-github]: https://github.com/38/d4-format
## Loading genetic intervals: genes, transcripts and exons into the database

Genes, transcripts and exons should be loaded and updated at regular intervals of time. Depending on the type of sequencing data analysed using chanjo2, <strong>loading of transcripts and exons might not be required.</strong>
For instance, gene coordinates should be enough for whole genome sequencing (WGS) experiments, while transcripts and exons data are necessary to return statistics from transcripts and exons-based experiments.

Genes, transcripts and exons can pre pre-downloaded from the [Ensembl Biomart][ensembl-biomart] using the [Schug][shug] library and loaded into the database in three distinct tables.

<strong>Genes should be loaded into the database before transcripts and exons intervals.</strong> Depending on the hardware in use and the HTML connection speed, the process of loading these intervals might take some time. For this reason requests sent to these endpoints are asynchronous, so that they don't time out while processing the information.


### Loading/updating database genes

Loading of genes in a given genome build can be achieved by sending a POST request to the `/intervals/load/genes/{<genome-build}` endpoint:


``` shell
curl -X 'POST' \
  'http://localhost:8000/intervals/load/genes/GRCh38?file_path=<path_to_genes_file_downloaded_from_schug_GRCh38.txt>' \
  -H 'accept: application/json' \
  -d ''
```

Please note that the process of <strong>loading genes into the database will erase eventual transcripts and exons with the same genome build</strong> that are already present in the database. This ensures that transcripts and exons intervals will be up-to-date with the latest definitions of the genes loaded into the database.

### Loading/updating transcripts 

Transcripts can be loaded/updated by using the `/intervals/load/transcripts/{<genome-build}` endpoint:

``` shell
curl -X 'POST' \
  'http://localhost:8000/intervals/load/transcripts/GRCh38?file_path=<path_to_transcripts_file_downloaded_from_schug_GRCh38.txt>' \
  -H 'accept: application/json' \
  -d ''
```

### Loading/updating exons:

As for the previous endpoints, exons are loaded by sending a POST request to the `/intervals/load/exons/{<genome-build}` endpoint.

``` shell
curl -X 'POST' \
  'http://localhost:8000/intervals/load/transcripts/GRCh38?file_path=<path_to_exons_file_downloaded_from_schug_GRCh38.txt>' \
  -H 'accept: application/json' \
  -d ''
```

### Genes, transcripts and exons queries

Once the database is populated with genomic intervals data, it is possible to run queries to retrieve its content.

Genomic intervals can be queried using genes definitions. Genes can be provided as a parameter to the query in the following formats
 
- Ensembl gene IDs (use parameter `ensembl_ids`)
- HGNC ids (use parameter `hgnc_ids`)
- HGNC symbols (use parameter `hgnc_symbols`)

Genome build is always a required parameter in these queries.

Examples:

* Send a POST request to Retrieve information on a list of <strong>genes</strong> using HGNC symbols:

``` shell
{
  "build": "GRCh37",
  "hgnc_symbols": ["LAMA1","LAMA2"]
}
```

* Retrieve transcripts available for one of more genes described by Ensembl IDs:

``` shell
curl -X 'POST' \
  'http://localhost:8000/intervals/transcripts' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
  "ensembl_gene_ids": [
    "ENSG00000101680", "ENSG00000196569"
  ]
}'
```

* Retrieve all exons for genes with HGNC IDs: 6481 and 6482:

``` shell
curl -X 'POST' \
  'http://localhost:8000/intervals/exons' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
  "hgnc_ids": [
    6481, 6482
  ]
}'
```

Whenever ensembl_ids, hgnc_ids, hgnc_symbols parameter is not provided, these endpoints will return a list of 100 default genes, transcripts or exons. To increase the number of returned entries you can specify a custom value for the query `limit` parameter.




[ensembl-biomart]: http://useast.ensembl.org/info/data/biomart/index.html
[schug]: https://github.com/Clinical-Genomics/schug






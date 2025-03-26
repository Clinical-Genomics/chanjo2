## Loading genetic intervals: genes, transcripts and exons into the database

Genes, transcripts and exons should be loaded and updated at regular intervals of time. Depending on the type of sequencing data analysed using chanjo2, <strong>loading of transcripts and exons might not be required.</strong>
For instance, gene coordinates should be enough for whole genome sequencing (WGS) experiments, while transcripts and exons data are necessary to return statistics from transcripts and exons-based experiments.

Genes, transcripts and exons should pre pre-downloaded from the [Ensembl Biomart][ensembl-biomart] using the [Schug][shug] library and loaded into the database in three distinct tables.

<strong>Genes should be loaded into the database before transcripts and exons intervals.</strong>

### Downloading resources from the Schug instance at SciLifeLab

#### Downloading of genes

``` shell
curl -X 'GET' 'https://schug.scilifelab.se/genes/ensembl_genes/?build=38' > genes_GRCh38.txt
```

#### Downloading of transcripts

``` shell
curl -X 'GET' 'https://schug.scilifelab.se/transcripts/ensembl_transcripts/?build=38' > transcripts_GRCh38.txt
```

#### Downloading of exons

``` shell
curl -X 'GET' 'https://schug.scilifelab.se/exons/ensembl_exons/?build=38' > exons_GRCh38.txt
```

Just replace "38" with "37" to download genes, transcripts and exons in genome build 37 (GRCh37).

**Note that sometimes Biomart downloads time out and the resulting might be incomplete. For this reason it's always recommended to make sure the last lines of these file contain MT chromosome data (MT chromosome is the last chromosome downloaded from Biomart).**

### Loading/updating database genes

FastAPI comes with an helpful Swagger UI, which allows to simplify several tasks, including loading of genes, transcripts and exons into the database.

Given a running local instance of chanjo2, with a swagger UI available in the browser at `http://localhost:8000/docs, loading of genes in a given genome build can be achieved by using the `/intervals/load/genes/{<genome-build}` endpoint:

<img width="1478" alt="Image" src="https://github.com/user-attachments/assets/7ef17743-6f46-4428-89ca-34e7cf04eab9" />

Genes are loaded in background and would be available some minutes after the update is triggered.

Please note that the process of <strong>loading genes into the database will erase eventual transcripts and exons with the same genome build</strong> that are already present in the database. This ensures that transcripts and exons intervals will be up-to-date with the latest definitions of the genes loaded into the database.

### Loading/updating transcripts

Similarly, transcript data 

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






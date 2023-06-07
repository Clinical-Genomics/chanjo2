## Coverage queries on d4 files or data contained in the database

Chanjo2 can be used to quickly access average coverage depth statistics for an interval from a list of genomic intervals on a custom d4 coverage file.
Additionally, samples stored in the database contain the location of d4 files on disk or on a remote server. For this reason, it is possible to retrieve coverage statistics relative to one or more samples by specifying their name (or the case name).

### Direct coverage query over a single genomic interval

Coverage over a genomic interval can be computed by sending a `GET` request to the `/coverage/d4/interval/` endpoint.

The parameters accepted by this query are:

- <strong>coverage_file_path</strong> (required). Path to a d4 file that is stored on the local drive or on a remote server (slower computation)
- <strong>chromosome</strong> (required). Genomic interval chromosome
- <strong>start</strong>. Genomic interval start position 
- <strong>stop</strong> Genomic interval end position 

Note that start and stop coordinates are not required and whenever they are omitted coverage statistics will be computer over the entire chromosome.

Query example:

``` shell
curl -X 'GET' \
  'http://localhost:8000/coverage/d4/interval/?coverage_file_path=https%3A%2F%2Fd4-format-testing.s3.us-west-1.amazonaws.com%2Fhg002.d4&chromosome=7&start=124822386&end=124929983' \
  -H 'accept: application/json'
```

This query wll return a response like this, where the mean coverage over the single interval is present in the first element of the mean_coverage value:

``` shell
{
  "chromosome": "7",
  "completeness": [],
  "ensembl_gene_id": null,
  "end": 124929983,
  "hgnc_id": null,
  "hgnc_symbol": null,
  "interval_id": null,
  "mean_coverage": [
    [
      "D4File",
      27.19804455514559
    ]
  ],
  "start": 124822386
}
```

### Direct coverage query over the intervals present in a bed file

Mean coverage can be also calculated for a list of intervals. The intervals list should be provided as bed-formatted file in a `POST` request.

If we were to use the [demo bed file](https://github.com/Clinical-Genomics/chanjo2/blob/main/src/chanjo2/demo/109_green.bed) provided in this repository, the query would look like this:

``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/d4/interval_file/?coverage_file_path=https%3A%2F%2Fd4-format-testing.s3.us-west-1.amazonaws.com%2Fhg002.d4' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'bed_file=<path-to-109_green.bed>'
```

And it would return the following result:

``` shell
[
  {
    "chromosome": "1",
    "completeness": [],
    "ensembl_gene_id": null,
    "end": 11866977,
    "hgnc_id": null,
    "hgnc_symbol": null,
    "interval_id": null,
    "mean_coverage": [
      [
        "D4File",
        22.17115629570222
      ]
    ],
    "start": 11845780
  },
  {
    "chromosome": "5",
    "completeness": [],
    "ensembl_gene_id": null,
    "end": 79950802,
    "hgnc_id": null,
    "hgnc_symbol": null,
    "interval_id": null,
    "mean_coverage": [
      [
        "D4File",
        83.1338549817423
      ]
    ],
    "start": 79922047
  },
  {
    "chromosome": "11",
    "completeness": [],
    "ensembl_gene_id": null,
    "end": 71907345,
    "hgnc_id": null,
    "hgnc_symbol": null,
    "interval_id": null,
    "mean_coverage": [
      [
        "D4File",
        252.63072816253893
      ]
    ],
    "start": 71900602
  },
  {
    "chromosome": "17",
    "completeness": [],
    "ensembl_gene_id": null,
    "end": 26734215,
    "hgnc_id": null,
    "hgnc_symbol": null,
    "interval_id": null,
    "mean_coverage": [
      [
        "D4File",
        141.35853114545165
      ]
    ],
    "start": 26721661
  }
]
```

Please note that <strong>direct coverage queries are not yet supporting the computation of coverage completeness</strong> over a custom list of coverage thresholds.


### Coverage completeness

When querying the server for sample coverage statistics, it is also possible to specify a custom list of numbers (example 30, 20, 10) representing the coverage thresholds that should be used to calculate the <strong>coverage completeness</strong> for each genomic interval. 
This number describes the percentage of bases (as a decimal number) meeting the user-defined coverage threshold for each genomic interval.

### Case and samples coverage queries

Genes, transcripts and exons coverage data can be computed by sending POST requests to their relative endpoints:

* `/coverage/samples/genes_coverage` 
* `/coverage/samples/transcripts_coverage` 
* `/coverage/samples/exons_coverage` 

These endpoints are very similar and accept the following parameters:

- <strong>build</strong> (required) # genome build (GRCh37 or GRCh38)
- <strong>completeness_thresholds</strong> # Threshold values for computing coverage completeness. Example [50, 30, 10]
- <strong>ensembl_gene_ids</strong> # List of Ensembl gene IDs. Example: ["ENSG00000101680", "ENSG00000196569"]
- <strong>hgnc_gene_ids</strong> # List of HGNC gene IDs. Example: [6481, 6482]
- <strong>hgnc_gene_symbols</strong> # List of HGNC gene symbols. Example: ["LAMA1", "LAMA2"]
- <strong>samples</strong> # List containing name of samples stored in the database. Example: ["sample1". "sample2", ..]
- <strong>case</strong> # name of a case containing one or more samples stored in the database

While the only required parameter is "build", <strong>it is necessary to specify a list of genes</strong> (either ensembl_gene_ids, hgnc_gene_ids or hgnc_gene_symbols) and either <strong>a case or a list of samples</strong>.

### Coverage and coverage completeness query esamples

- Given all samples from case "internal_id", retrieve mean coverage and coverage completeness with threshold 30, 20 on the genes from the Cerebral folate deficiency PanelAPP panel (*DHFR, FOLR1, MTHFR, SLC46A1*):

``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/samples/genes_coverage' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
  "completeness_thresholds": [
    30, 20
  ],
  "hgnc_gene_symbols": [
    "DH?FR", "FOLR1", "MTHFR", "SLC46A1"
  ],
  "case": "internal_id"
}'
```


- Given two samples named sample1 and sample2. Calculate mean coverage and coverage completeness over the transcripts of the ATM gene (described by its Ensembl ID)

``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/samples/transcripts_coverage' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
  "completeness_thresholds": [
    50, 30
  ],
  "ensembl_gene_ids": [
    "ENSG00000149311"
  ],
  "samples": ["sample1", "sample2"]
}'
```

- Evaluate mean coverage and coverage completeness over the exons of genes *LAMA1* and *LAMA2* (described by HGNC IDs):

``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/samples/exons_coverage' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
  "completeness_thresholds": [
    100, 75, 50
  ],
  "hgnc_gene_ids": [
    6481, 6482
  ],
  "samples": ["sample1", "sample2"]
}'
```




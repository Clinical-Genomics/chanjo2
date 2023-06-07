## Direct Coverage queries on custom d4 files

Chanjo2 can be used to quickly access coverage statistics for an interval of a list of genomic intervals on a custom d4 coverage file.

### Mean coverage over a single genomic interval

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

### Coverage over the intervals present in a bed file

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

Please note that <strong>direct coverage queries are not yet supporting the computation of coverage completeness</string> over a custom list of coverage thresholds.
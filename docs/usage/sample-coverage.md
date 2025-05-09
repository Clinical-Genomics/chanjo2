## Coverage queries on d4 files or data contained in the database

Chanjo2 can be used to quickly access average coverage depth statistics for an interval from a list of genomic intervals on a custom d4 coverage file.

### Coverage completeness

When querying the server for sample coverage statistics, it is also possible to specify a custom list of numbers (example 30, 20, 10) representing the coverage thresholds that should be used to calculate the <strong>coverage completeness</strong> for each genomic interval. 
This number describes the percentage of bases (as a decimal number) meeting the user-defined coverage threshold for each genomic interval. 
**Please note** that computing coverage completeness for non-local files (files provided as URLs) is not supported. This is because the functionality is not present in d4tools.

### Direct coverage query over a single genomic interval

Coverage and coverage completeness over a genomic interval can be computed by sending a `POST` request to the `/coverage/d4/interval/` endpoint.

The entrypoint accepts a json query with the following parameters:

- <strong>coverage_file_path</strong> # (required). Path to a d4 file that is stored on the local drive or on a remote server (slower computation)
- <strong>chromosome</strong> # (required). Genomic interval chromosome
- <strong>completeness_thresholds</strong> # Threshold values for computing coverage completeness. Example [50, 30, 10]
- <strong>start</strong> # Genomic interval start position 
- <strong>stop</strong> # Genomic interval end position 

Note that start and stop coordinates are not required and whenever they are omitted coverage statistics will be computer over the entire chromosome.

Query example:

``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/d4/interval/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "coverage_file_path": "<path-to-d4-file.d4>",
  "chromosome": "7",
  "start": 124822386,
  "end": 124929983,
  "completeness_thresholds": [
    10,20,30
  ]
}'
```

This query wll return a response, where the mean coverage over the single interval is present under the mean_coverage key. 
Coverage completeness values will be additionally returned if the query sent to the server contains values for the completeness_thresholds key. 
A response from the server to the query above will return for instance a mean interval coverage of 27.2 and coverage completeness of 99.6%, 85% and 33.4% using threshold values of respectively 10, 20 and 30.

``` shell
{
  "mean_coverage": 27.19804455514559,
  "completeness": {
    "10": 1,
    "20": 0.85,
    "30": 0.33
  },
  "interval_id": null,
  "interval_type": null
}
```

### Direct coverage query over the intervals present in a bed file

Mean coverage can be also calculated for a list of intervals using the `/coverage/d4/interval_file` endpoint. The intervals list should be provided as the path to a bed-formatted file.

The entrypoint accepts a json query with the following parameters:

- <strong>coverage_file_path</strong> # (required). Path to a d4 file that is stored on the local drive or on a remote server (slower computation)
- <strong>intervals_bed_path</strong> # (required). Path to a .bed file present on the local drive.
- <strong>completeness_thresholds</strong> # Threshold values for computing coverage completeness. Example [50, 30, 10]

If we were to use the [demo bed file](https://github.com/Clinical-Genomics/chanjo2/blob/main/src/chanjo2/demo/109_green.bed) provided in this repository, the query would look like this:


``` shell
curl -X 'POST' \
  'http://localhost:8000/coverage/d4/interval_file/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "coverage_file_path": "<path-to-d4-file.d4>",
  "intervals_bed_path": "<path-to-109_green.bed>",
  "completeness_thresholds": [
    10,20,30
  ]
}'
```

And it would return the following result:

``` shell
[
  {
    "mean_coverage": 22.17115629570222,
    "completeness": {
      "10": 1,
      "20": 0.69,
      "30": 0.08
    },
    "interval_id": null,
    "interval_type": null
  },
  {
    "mean_coverage": 83.1338549817423,
    "completeness": {
      "10": 1,
      "20": 0.84,
      "30": 0.24
    },
    "interval_id": null,
    "interval_type": null
  },
  {
    "mean_coverage": 252.63072816253893,
    "completeness": {
      "10": 1,
      "20": 0.78,
      "30": 0.03
    },
    "interval_id": null,
    "interval_type": null
  },
  {
    "mean_coverage": 141.35853114545165,
    "completeness": {
      "10": 0.99,
      "20": 0.7,
      "30": 0.09
    },
    "interval_id": null,
    "interval_type": null
  }
]
```

### Condensed summary stats for one or more samples over a list of HGNC IDs

To obtain condensed statistics for one or more samples, use the `/coverage/d4/genes/summary` endpoint. 
Send a request with a list of HGNC gene IDs, the path to the d4 files for the samples, and the coverage threshold for computing coverage completeness. 
The endpoint will return the average coverage and coverage completeness for all the genes included in the query.
You need to provide a parameter `interval_type` to specify whether the statistics should be computed over entire genes, gene transcripts, or exons.

#### Request example:

``` shell
curl -X 'POST' \
  'https://chanjo2-stage.scilifelab.se/coverage/d4/genes/summary' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "build": "GRCh37",
  "samples": [
    {
      "name": "TestSample",
      "coverage_file_path": "<path-to-d4-file.d4>"
    }
  ],
  "hgnc_gene_ids": [
    2861, 3791, 6481, 7436, 30521
  ],
  "coverage_threshold": 10,
  "interval_type": "genes"
}'
```

#### Response from chanjo2:

``` shell
{"TestSample":{"mean_coverage":54.38,"coverage_completeness_percent":33.03}}
```




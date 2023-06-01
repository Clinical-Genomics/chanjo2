## Loading cases and samples into the database

When used in connection with a database, Chanjo2 can be used to store information relative to collections of samples (cases).

Cases might include one or more related samples (different individuals of a trio, tumor and normal pairs ect) and samples can be assigned to multiple cases.

### Basic structure of a case:

``` shell
 {
    "display_name": "643594", # Non-unique descriptor of the case
    "name": "internal_id", # Unique ID associated the case
    "id": 1, # Unique database ID for the case
    "samples": [sample1, sample2 ] # List of samples associated to the case
  }
```

### Creating a new case

The only 2 parameters that should be provided when creating a case are `display_name` and `name`.

With a running instance of Chanjo2, a new case can be saved into the database by sending a <strong>POST</strong> request to the `/cases/` endpoint:

``` shell
curl -X 'POST' \
  'http://localhost:8000/cases/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "display_name": "Case 1",
  "name": "case1"
}'
```

If the command was successful, then the newly created case will be returned in the response body:

``` shell
{
  "display_name": "Case 1",
  "name": "case1",
  "id": 2,
  "samples": []
}
``` 
Note that the new case `id` is created automatically and the sample list is empty because there are no associated samples to the case yet.

### Basic structure of a sample

A sample describes a sequencing analysis and has the following structure

``` shell
{
    "coverage_file_path": "/home/worker/app/src/chanjo2/demo/panelapp_109_example.d4", # complete path to a d4 file on a local disk or URL to a d4 file on a remote server
    "display_name": "NA12882", # Non-unique descriptor of the sample
    "track_name": "ADM1059A2", # d4 file track associated to this sample (for multitrack d4 files) *
    "name": "ADM1059A2", # Unique ID associated the sample
    "created_at": "2023-06-01T09:20:02", # Date and time the sample was saved into the database
    "id": 1  # Unique database ID for the sample
}
```
* Please note that chanjo2 is not yet supporting multitrack d4 coverage files, so the track name value is only used to store this value until the functionality is in place.


### Creating a new sample

A new sample can be created by sending a  <strong>POST</strong> request with the relative json information to the `/samples/` endpoint:

``` shell
curl -X 'POST' \
  'http://localhost:8000/samples/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "coverage_file_path": "<path-to-d4-coverage-file.d4>",
  "display_name": "Sample 1",
  "track_name": "sample1",
  "name": "sample1",
  "case_name": "case1"
}'
```

To associate this sample to more than one case, you can send several requests with the same sample data except for `case_name`, which will differ for each case the case has to be associated with.

If sample is created successfully then the created entry will be returned in the server response body:

``` shell
{
  "coverage_file_path": "<path-to-d4-coverage-file.d4>",
  "display_name": "Sample 1",
  "track_name": "sample1",
  "name": "sample1",
  "case_id": 1,
  "created_at": "2023-06-01T12:11:35",
  "id": 2
}
```

### Removing a sample

A sample can be removed from the database by sending a <strong>DELETE</strong> request to the sample ID to the `samples/delete/{<sample-id>}` endpoint:

``` shell
curl -X 'DELETE' \
  'http://localhost:8000/samples/delete/sample1' \
  -H 'accept: application/json'
```

A successful response will return:

``` shell
"Removing sample sample1. Affected rows: 1"
```

### Removing a case

<strong>Removing a case will remove the case itself and all samples associated uniquely to this case</strong>. Samples associated also with other cases will not be removed from the database.

To remove a case from the database, send a <strong>DELETE</strong> request to the `/cases/delete/{<case-id>}` endpoint:

``` shell
curl -X 'DELETE' \
  'http://localhost:8000/cases/delete/internal_id' \
  -H 'accept: application/json'
```

A successful response will return:

``` shell
"Removing case internal_id. Affected rows: 1"
```
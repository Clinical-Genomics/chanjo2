## [unreleased]
### Added
- Load genes, transcripts and exons from pre-downloaded files
- Demo coverage report endpoint in new `report` module
- Coverage completeness lines in HTML coverage report
- Default threshold level coverage lines in HTML coverage report
- Hidden table cell showing incompletely covered genes in coverage report
- Display optional case name on gene coverage report
- Display error in coverage report when query genes are not found in the database
- Export coverage report to PDF
- Metrics explanation section on coverage report
- Non-demo coverage report endpoint
- Fixed coverage report filters to update report using other settings
- Demo genes overview endpoint
- Incomplete intervals at different coverage thresholds on demo genes overview page
### Changed
- Moved helper function from endpoints coverage to crud samples
- Deleted unused `src/chanjo2/meta/handle_query_intervals.py` file
- Non-root user and password for database connections
- Refactor and simplify code in `meta.handle_d4` module
- Fixed documentation according to changed coverage API
### Fixed
- Bump certifi from 2022.12.7 to 2023.7.22
- Datababase connection parameters in documentation files

## [1.1.0]
### Added
- Created a woke-language-check GitHub action
- `/coverage/d4/interval/` and `/coverage/d4/interval_file/` modified to accept POST requests with new `completeness_thresholds` parameter
- A new endpoint `/coverage/samples/predicted_sex` that returns mean coverage over X and Y and predicted sex of the sample
### Changed
- Modified documentation pages to reflect changes in the `/coverage/d4/interval/` and `/coverage/d4/interval_file/` endpoints

## [1.0.1]
### Fixed
- docker_build_on_release GitHub action

## [1.0.0]
### Added
- Instructions on how to install and run the app on a Conda environment
- Test for heartbeat endpoint
- Automated tests GitHub workflow
- Instructions on how to run a demo connected to a database in README
- Add Codecov steps to Tests GitHub action
- Vulture GitHub action to remove unused code
- Colored logs for development and debugging
- Common test fixtures
- Some badges on README page
- Tests for cases and samples endpoints
- Save samples with coverage files stored on a remote HTTP(s) server
- Demo data (D4 file containing coverage data for a panel of 4 genes)
- Endpoint for coverage queries over a single interval of a provided D4 file
- Demo case and demo sample loaded with demo instance startup
- Endpoint for coverage queries over the intervals of a BED file
- Include a default .env file loaded on app startup
- Filter genes, transcripts and exons by Ensemble id, HGNC id, HGNC symbol
- Demo genes, transcripts and exons loaded on demo instance startup
- Return coverage over a list of genes for a sample in the database
- Remove a sample from the database by providing its name
- Return coverage and coverage completeness (custom thresholds) over a list of genes for a case or a list of samples
- Return transcripts coverage and coverage completeness (custom thresholds) over a list of genes for a case or a list of
  samples
- Return exons coverage and coverage completeness (custom thresholds) over a list of genes for a case or a list of
  samples
- Remove a sample and all associated samples from the database by providing its name
- Created the basic structure of the howto using mkdocs
- Created a GitHub action for publishing the documentation on the GitHub pages
- Documentation on how to load cases and samples into the database
- Documentation on how to query the server for coverage stats
- Documentation on how to load genes, transcripts and exons into the database
- Improve documentation on how to customise the .env file to use a production database
### Fixed
- Bugs preventing the gunicorn app to launch
- Code to compose DB url to work when app is invoked from docker-compose
- Dockerfile building error due to missing d4tools lib
- Add VARCHAR length to sample.coverage_file_path SQL field
- Format of Build field in genes, transcripts and exons tables
- Increased size of allowed HGNC symbols in the MySQL gene model
- Remove old exons and transcripts data when updating genes
- Test warnings regarding Case-Sample database relationship
- Error when removing a case that is not found in the database
- Updated and faster GitHub actions
- Format of mean coverage and coverage completeness returned in responses
### Changed
- Renamed root endpoint to heartbeat
- Use a multi-stage build in Dockerfile to reduce its size
- SQLite database launched instead of MySQL as the default demo database
- Simpler docker-compose file and additional docker-compose file to show MySQL connection howto
- Removed broken BumpVersion GitHub action
- Use a temporary file when running the demo app
- Modified the command to run a demo instance in README file
- Renamed table `Individuals` table to the more general `Samples`
- Renamed table `Regions` table to `Intervals`
- Use uvicorn logging and avoid printing logs twice
- Modified samples and cases endpoints to interact with database via CRUD utils
- Use SQLAlchemy 1.4 Declarative which is now integrated into the ORM to avoid deprecation warning
- Start SQL engine and sessions using the future tag to prepare migration to SQLAlchemy 2.0
- Updated a few python dependencies
- Moved validation of sample's coverage file path to sample's pydantic model
- Installing the pyd4 module as a requirement of this repository
- Moved the endpoints constants to a class in test fixtures
- More explicit names for two endpoints
- Load genes, transcripts and exons in batches of 10K records
- Simpler code to load genes and transcripts into the database
- Updated version of several GitHub actions
- Validate sample coverage queries so that only one gene list format can be provided
- Speed up queries by optimizing Genes, Transcripts and Exons tables and indexes
- Custom algorithm to speed up coverage completeness thresholds calculation
- Replaced deprecated `pkg_resources` lib with `importlib_resources` lib
- Modified Python version in Dockerfile from 3.8 to 3.11
- Introduced a "track_name" key in sample database objects to be used in multitrack D4 files analysis
- One sample can belong to more than one case
- Practical howto in README file and moved deployment instructions to the docs
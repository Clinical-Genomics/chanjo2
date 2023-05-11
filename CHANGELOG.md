## [unreleased]

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
- Return coverage and coverage completeness (custom thresholds) over a list of genes for a sample in the database
- Return transcripts coverage and coverage completeness (custom thresholds) over a list of genes for a sample in the
  database
- Return exons coverage and coverage completeness (custom thresholds) over a list of genes for a sample in the database

### Fixed

- Bugs preventing the gunicorn app to launch
- Code to compose DB url to work when app is invoked from docker-compose
- Dockerfile building error due to missing d4tools lib
- Add VARCHAR length to sample.coverage_file_path SQL field
- Format of Build field in genes, transcripts and exons tables
- Increased size of allowed HGNC symbols in the MySQL gene model
- Remove old exons and transcripts data when updating genes

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
- Speed up queries by optimizing Genes, Transcripts and Exons table indexes

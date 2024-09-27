## [unreleased]
### Added
- Improve report explanation to better interpret average coverage and coverage completeness stats shown on the coverage report
- Check that provided d4 files when running queries using `/coverage/d4/genes/summary` endpoint are valid, with test
- General report with coverage over the entire genome when no genes or genes panels are provided
### Changed
- Do not use stored cases/samples any more and run stats exclusively on d4 files paths provided by the user in real time
- How parameters are passed to starlette.templating since it was raising a deprecation warning.
- Replaced deprecated Pydantic `parse_obj` method with `model_validate`
- Report and genes overview endpoints accept only POST requests with form data now (application/x-www-form-urlencoded) - no json
- Sort alphabetically the list genes that are incompletely covered on report page
- `d4_genes_condensed_summary` coverage endpoint will not convert `nan` or `inf` coverage values to None, but to str(value)
- Updated the Dockerfile base image so it contains the latest d4tools (master branch)
- Updated tests workflow to cargo install the latest d4tools from git (master branch)
- Computing coverage completeness stats using d4tools `perc_cov` stat function (much quicker reports)
- Moved functions computing the coverage stats to a separate `meta/handle_coverage_stats.py` module
- Refactored gene code computing stats for gene overview
### Fixed
- Updated dependencies including `certifi` to address dependabot alert
- Update pytest to v.7.4.4 to address a `ReDoS` vulnerability
- Colored logs
- Link for switching between coverage thresholds on overview report
- Gene links in genes overview page open into new tabs

## [1.9]
### Added
- Condensed `/coverage/d4/genes/summary` for condensed stats over a gene list
- Documentation for new coverage summary endpoint
### Changed
- GitHub tests action to use d4tools 0.3.10
### Fixed
- Updated dependencies to address dependabot's security alerts
- Use a base image containing d4tools 0.3.10 in Dockerfile

## [1.8]
### Added
-  `cryptography` lib dependency
### Changed
- Updated PR template
- Generalised issue templates to make them more user-friendly for people outside our organisation
- Moved logging setup out of app lifespan and db initialisation logic
- Switch to __main__ logger and removed unused logger from multiprocessing code
### Fixed
- Updated version of external images used in GitHub actions

## [1.7]
### Added
- An environment.yml with the minimum supported python version (3.8) and the installed libs
### Changed
- pyd4 library no longer available in chanjo2 Docker image
### Fixed
- Position of `Show genes` checkbox on report page
- Updating gene panel name using the web form on report page

## [1.6]
### Added
- Coverage report and genes coverage overview endpoints now accept also requests with application/x-www-form-urlencoded data
- Allow system admin to customise coverage levels to be used in reports' metrics by editing the REPORT_COVERAGE_LEVELS in .env file
- Documentation on how to change app's default coverage level values to be used when creating the reports
### Changed
- Templates form submit data as application/x-www-form-urlencoded without having to transform it into json
- Customize form on report page now accepts genes as Ensembl IDs or HGNC symbols
### Fixed
- Faster genes overview report loading
- Broken GitHub action due to d4tools failing to install using cargo
- Broken Codecov upload step in GitHub action failing due to missing token
- Completeness cutoff select not updating after submitting customize form on report page

## [1.5.1]
### Fixed
- Avoid MySQLdb.OperationalError `Server has gone away` by modifying by setting `pool_pre_ping=True` when creating the engine
- Coverage report screenshot displayed on README page and on the documentation to reflect true statistics from the demo samples
- Coverage report/overview page crashing when transcripts or exons intervals are required only genes are loaded
- Coverage overview over a gene should return transcript statistics if D4 file contains WGS data

## [1.5]
### Added
- `coverage.d4_intervals_coverage` responses contain also interval name as provided in bed file
- `coverage.d4_interval_coverage` responses now returns also the genomic region used to compute the stats on
- Test for modified function collecting coverage report data
### Changed
- Speed up response by `coverage.d4_intervals_coverage` by replacing pyd4 lib with direct calls d4tools and multiprocessing
- Removed 2 redundant functions in `meta.handle.bed.py`
- `coverage.d4_interval_coverage` is using direct calls to d4tools to retrieve stats over an entire chromosome or a genomic interval
- Reformat report sample' sex rows and coverage.get_samples_predicted_sex endpoint to use d4tools and not pyd4 for evaluating sample sex
- Refactored code to create coverage report and genes overview report to be faster by using d4tools calls and multiprocessing
- Renamed `handle_tasks.py` to `handle_completeness_tasks.py`
- Refactored coverage endpoints `samples_genes_coverage`, `samples_transcripts_coverage` and `samples_exons_coverage` to use calls to d4tools instead of the pyd4 library
- Speed up coverage report creation by collecting SQL intervals before looping through samples stats
- Refactored gene overview to use d4tools instead of pyd4 lib to compute gene-level intervals stats
- Removed pyd4 lib and all remaining code which was still using it
### Fixed
-  `coverage.d4_interval_coverage` endpoint crashing trying to computer coverage completeness over an entire chromosome
- Samples mean coverage values a hundredfold higher on coverage reports
- Install software packages using poetry v<1.8 to avoid problems installing pyd4 (pyd4 not supporting PEP 517 builds)
- Typo in report template with unclosed span/div causing cramped genes not found message
- Mariadb container not passing healthcheck when runned from demo docker-compose file
- Fixed an error on gene overview that made the coverage seem 100-folds higher
- Return error when genes are not provided in the request form to create a coverage report

## [1.4]
### Changed
- Upgraded Bootstrap and JQuery versions on genes coverage overview and coverage report pages
- Optimized indexes to speed up retrieval of genes, transcripts and exons intervals from database

## [1.3]
### Changed
- Simplified the import of SQL classes from `scout.models.sql_model`
- Upgraded Pydantic and Fastapi libraries and their dependencies
- Use app lifespan instead of deprecated startup `on_event'.
- Modified code to support upgraded libraries
- Rename a test file from `test_d4.py` to `test_handle_d4.py` and add 2 new tests to it
- Fix return type of `get_intervals_completeness` function
- Isort imports of the entire repo

## [1.2]
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
- Demo and non-demo genes coverage overview endpoint
- Incomplete intervals at different coverage thresholds on genes overview page
- Gene coverage overview endpoint
- Documentation to create custom genes coverage and coverage overview reports
### Changed
- Moved helper function from endpoints coverage to crud samples
- Deleted unused `src/chanjo2/meta/handle_query_intervals.py` file
- Non-root user and password for database connections
- Refactor and simplify code in `meta.handle_d4` module
- Fixed documentation according to changed coverage API
- Removed unused `sqlmodel` and updated some other dependencies
- Show only RefSeq transcripts in coverage report and overview
- Refactored HTML templates to reduce repetitions by inheriting code from base template
- Coverage report form to accept genes as Ensembl IDS, HGNC IDs and HGNC symbols
- Moved coverage report "show genes" outside form and just above custom coverage stats table
- Updated several Python libraries including schug
### Fixed
- Bump certifi from 2022.12.7 to 2023.7.22
- Database connection parameters in documentation files
- Avoid duplications when retrieving transcripts and exons in gene
- Add upgrade-insecure-requests meta to HTML page to be able to use javascript fetch in requests
- Renamed imported function from schug 1.3

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
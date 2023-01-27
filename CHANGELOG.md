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
### Fixed
- Bugs preventing the gunicorn app to launch
- Code to compose DB url to work when app is invoked from docker-compose
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
- Use uvicorn logging and avoid printing database logs twice

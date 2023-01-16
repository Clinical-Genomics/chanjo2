## [unreleased]
### Added
- Instructions on how to install and run the app on a Conda environment
- Test for heartbeat endpoint
- Automated tests GitHub workflow
- Instructions on how to run a demo connected to a database in README
- Add Codecov steps to Tests GitHub action
### Fixed
- Bugs preventing the gunicorn app to launch
- Code to compose DB url to work when app is invoked from docker-compose
### Changed
- Renamed root endpoint to heartbeat
- Use a multi-stage build in Dockerfile to reduce its size

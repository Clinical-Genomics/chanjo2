## Deploying Chanjo2 using Docker

The [Dockerfile][dockerfile-link] provided in the chanjo2 repository can be built and runned to deploy the software. Alternatively an image containing chanjo2 and all its dependencies is hosted on [Docker Hub][docker-hub-chanjo2].


### Launching a demo using Docker

The file named `Dockerfile` is a generic Docker file to run the application. Whenever the app is launched with the ENV param `DEMO` (check the settings present in file `docker-compose.yml`) it will create a test SQLite database to work with.

To start the demo via docker, run:

```
docker run -d --rm  -p 8000:8000 --expose 8000 clinicalgenomics/chanjo2-stage:latest
```

The endpoints of the app will be now reachable from any web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs


## Launching the app connected to a MySQL database via docker-compose

An example of this setup is provided in the `docker-compose-mysql.yml` file.
Here we connect the app to a MySQL (MariaDB) and provide the connection settings to use it.

Note that a file containing enviromnent variables is required to run this setup. The `template.env` file offers an example of the required variables and can be customised according to your local settings.

To check the configuration (env variables passed to the docker-compose file) run:

```
docker-compose -f docker-compose-mysql.yml --env-file template.env config
```

The docker-compose file contains 2 services:
- **MariaDB database**, runned from a Docker file that includes the script to create an empty `testdb` database
- **The chanjo2 web app**, a REST API

To start the demo, run:

```
docker-compose -f docker-compose-mysql.yml --env-file template.env up
```

The endpoints of the app will be now reachable from any web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs



[docker-hub-chanjo2]: https://hub.docker.com/repository/docker/clinicalgenomics/chanjo2-stage/general
[dockerfile-link]: https://github.com/Clinical-Genomics/chanjo2/blob/main/Dockerfile
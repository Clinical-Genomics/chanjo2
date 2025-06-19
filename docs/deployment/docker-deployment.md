## Deploying Chanjo2 using Docker

The [Dockerfile][dockerfile-link] provided in the chanjo2 repository can be built and runned to deploy the software. Alternatively an image containing chanjo2 and all its dependencies is hosted on [Docker Hub][docker-hub-chanjo2].


### Launching a demo using Docker

The file named `Dockerfile` is a generic Docker file to run the application. Whenever the app is launched with the ENV param `DEMO` (check the settings present in file `docker-compose.yml`) it will create a test SQLite database to work with.

To start the demo via docker, run:

```
docker run -d --rm  -p 8000:8000 --expose 8000 clinicalgenomics/chanjo2:latest
```

The endpoints of the app will be now reachable from any web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs


### Launching the app connected to a MySQL database via docker-compose

An example of this setup is provided in the `docker-compose-mysql.yml` file.
Here we connect the app to a MySQL (MariaDB) and provide the connection settings to use it.

Note that a file containing environmnent variables is required to run this setup. The `template.env` file offers an example of the required variables and can be customised according to your local settings.

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


### Production settings and .env file

Keep in mind that Chanjo2 reads the variables necessary for connecting to the database from a default [.env file](https://github.com/Clinical-Genomics/chanjo2/blob/main/.env). 
If you run a dockerized version of Chanjo2 and want to connect to a real database, you'll need to replace the default .env file with a custom environment file containing the correct settings to connect to your MySQL database. 
The last line present on the .env file (`DEMO=Y`) should be removed or commented out.

Given a local database running on localhost and port 3306, a custom .env file like this:

```
MYSQL_USER=dbUser
MYSQL_PASSWORD=dbPassword
MYSQL_DATABASE_NAME=chanjo2_test
MYSQL_HOST_NAME=host.docker.internal
MYSQL_PORT=3306
```

Should suffice to override the parameters present in the default .env file of Chanjo2:

``` shell
docker run -d --rm -v $(pwd)/.env:/home/worker/app/.env  -p 8000:8000 --expose 8000 clinicalgenomics/chanjo2:latest
```

[docker-hub-chanjo2]: https://hub.docker.com/repository/docker/clinicalgenomics/chanjo2/general
[dockerfile-link]: https://github.com/Clinical-Genomics/chanjo2/blob/main/Dockerfile
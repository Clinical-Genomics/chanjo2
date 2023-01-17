# chanjo2

<strong>Please note that this project is still a work in progress!!</strong>

## Launching a demo using Docker-compose

The file named `Dockerfile` is a generic Docker file to run the application. Whenever the app is launched with the ENV param `DEMO` (check the settings present in file `docker-compose.yml`) it will create a test SQLite database to work with.

To start the demo via docker-compose, run:

```
docker-compose up
```

The endpoints of the app will be now reachable from ant web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs


## Lauching the app connected to a MySQL database

An example of this setup is provided in the `docker-compose-mysql.yml` file.
Here we connect the app to a MySQL (MariaDB) and provide the connection settings to use it.

Note that a file containing enviroment variables is required to run this setup. The `template.env` file offers an example of the required variables and can be customised according to your local settings.

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

The endpoints of the app will be now reachable from ant web browser: http://0.0.0.0:8000/docs or http://localhost:8000/docs





## Installing the application on a local Conda environment

Given a conda environment containing python >=3.7 and [poetry](https://github.com/python-poetry/poetry), clone the repository from Github with the following command:

```
git clone https://github.com/Clinical-Genomics/chanjo2.git
```

The command will create a folder named `chanjo2` in your current working directory. Move inside this directory:

```
cd chanjo2
```

And install the software with poetry:

```
poetry install
```

You can run a demo instance of the web server by typing:

```
gunicorn --config gunicorn.conf.py src.chanjo2.main:app
```

The server will run on localhost and default port 8000 (http://0.0.0.0:8000)

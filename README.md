# Please note that this project is still a work in progress!!

## Launching a demo app connected to a database using Docker Compose

## Installing the application on a local Conda environment

Given a local instance of a MySQL database (you can skip the step below if you already have a running instance of MySQL):
```
docker run --name mariadb -e MYSQL_ROOT_PASSWORD=test -e MYSQL_DATABASE=chanjo2_test -d -p 3307:3306 mariadb
```

Make sure that the database can be accessed in a terminal with the command `mysql -h 127.0.0.1 -P 3307 -u root -ptest`


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

You can run an instance of the web server by typing:

```
gunicorn --config gunicorn.conf.py src.chanjo2.main:app
```

The server will run on localhost and default port 8000 (http://0.0.0.0:8000)

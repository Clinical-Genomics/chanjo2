## Installing Chanjo2 in a virtual environment

### Installing the application on a local Conda environment

Given a conda environment containing [Rust][rust], Python >=3.8 with [poetry](https://github.com/python-poetry/poetry) installed, clone the repository from GitHub with the following command:

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

If you encounter any difficulties installing the pyd4 library due to its lack of support for PEP 517 builds, simply retry the aforementioned step using a version of poetry that is less than 1.8.


You can run a demo instance of the web server by typing:

```
uvicorn src.chanjo2.main:app --reload
```

The server will run on localhost and default port 8000 (http://0.0.0.0:8000)

The demo server is connecting to a SQLite database whose temporary tables are destroyed and re-created every time the server is started.
In order to connect to a permanent MYSQL database instance, you'd need to customise the settings present on the [`.env`](https://github.com/Clinical-Genomics/chanjo2/blob/main/.env) file. 
For info about custom settings on the .env file, please visit [this document](env_file.md).


[rust]: https://www.rust-lang.org/

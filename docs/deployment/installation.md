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

You can run a demo instance of the web server by typing:

```
uvicorn src.chanjo2.main:app --reload
```

The server will run on localhost and default port 8000 (http://0.0.0.0:8000)


[rust]: https://www.rust-lang.org/
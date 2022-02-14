FROM clinicalgenomics/pyd4

LABEL base_image="clinicalgenomics/pyd4"
LABEL about.home="https://github.com/Clinical-Genomics/chanjo2"

ENV UVICORN_WORKERS=1
ENV UVICORN_THREADS=1
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT="8000"

EXPOSE 8000

WORKDIR /home/worker/app
COPY . /home/worker/app

# Install poetry
RUN apt-get update 
RUN apt-get install -y default-libmysqlclient-dev
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH="/root/.poetry/bin:${PATH}"

# Install dependencies
RUN poetry install
RUN poetry add mysqlclient
ENV PATH="/root/.poetry/bin:${PATH}"
ENV PYTHONPATH="/usr/local/lib/python3.9/site-packages/pyd4:${PYTHONPATH}"


CMD . /root/.cache/pypoetry/virtualenvs/chanjo2-iv4VKWd0-py3.9/bin/activate && uvicorn\
    --workers=$UVICORN_WORKERS \
    --host=$UVICORN_HOST \
    --port=$UVICORN_PORT \
    --log-level="debug" \
    chanjo2.main:app

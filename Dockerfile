FROM clinicalgenomics/python3.8-venv-pyd4:1.0

LABEL about.home="https://github.com/Clinical-Genomics/chanjo2"
LABEL about.license="MIT License (MIT)"

USER root

# Install base dependencies
RUN apt-get update && \
     apt-get -y upgrade && \
     apt-get -y install -y --no-install-recommends gcc default-libmysqlclient-dev && \
     apt-get clean && \
     rm -rf /var/lib/apt/lists/*

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# Install app
WORKDIR /home/worker/app
COPY --chown=worker:worker . /home/worker/app

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

# Run commands as non-root
USER worker

CMD gunicorn\
    --config gunicorn.conf.py \
    chanjo2.main:app

FROM clinicalgenomics/python3.11-venv-pyd4:2.0 AS builder

LABEL about.home="https://github.com/Clinical-Genomics/chanjo2"
LABEL about.license="MIT License (MIT)"

USER root

# Install base dependencies
RUN apt-get update && \
     apt-get -y upgrade && \
     apt-get -y install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config && \
     apt-get clean && \
     rm -rf /var/lib/apt/lists/*

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/worker/libs/d4tools/bin:${PATH}"
RUN echo export PATH="/venv/bin:\$PATH" > /etc/profile.d/venv.sh

# Install app
WORKDIR /home/worker/app
COPY --chown=worker:worker . /home/worker/app

# Copy pre-installed software from builder
COPY --chown=worker:worker --from=builder /venv /venv
COPY --chown=worker:worker --from=builder /home/worker/libs /home/worker/libs

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

# Run commands as non-root
USER worker

CMD gunicorn\
    --config gunicorn.conf.py \
    chanjo2.main:app

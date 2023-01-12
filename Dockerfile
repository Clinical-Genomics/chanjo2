###########
# BUILDER #
###########
FROM clinicalgenomics/python3.8-venv:1.0 AS python-builder

ENV PATH="/venv/bin:$PATH"

WORKDIR /app

# Install base dependencies
RUN apt-get update && \
     apt-get -y upgrade && \
     apt-get -y install -y --no-install-recommends gcc default-libmysqlclient-dev && \
     apt-get clean && \
     rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#########
# FINAL #
#########
FROM python:3.8-slim

LABEL about.home="https://github.com/Clinical-Genomics/chanjo2"
LABEL about.license="MIT License (MIT)"

# Install base dependencies
RUN apt-get update && \
     apt-get -y upgrade && \
     apt-get -y install -y --no-install-recommends gcc default-libmysqlclient-dev && \
     apt-get clean && \
     rm -rf /var/lib/apt/lists/*

# Do not upgrade to the latest pip version to ensure more reproducible builds
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PATH="/venv/bin:$PATH"
RUN echo export PATH="/venv/bin:\$PATH" > /etc/profile.d/venv.sh

# Create a non-root user to run commands
RUN groupadd --gid 1000 worker && useradd -g worker --uid 1000 --shell /usr/sbin/nologin --create-home worker

# Copy virtual environment from builder
COPY --chown=worker:worker --from=python-builder /venv /venv

WORKDIR /home/worker/app
COPY --chown=worker:worker . /home/worker/app

# Install only the app
RUN pip install --no-cache-dir --editable .

# Run the app as non-root user
USER worker

ENV GUNICORN_WORKERS=1
ENV GUNICORN_THREADS=1
ENV GUNICORN_BIND="0.0.0.0:8000"
ENV GUNICORN_TIMEOUT=400

CMD gunicorn \
    --workers=$GUNICORN_WORKERS \
    --bind=$GUNICORN_BIND  \
    --threads=$GUNICORN_THREADS \
    --timeout=$GUNICORN_TIMEOUT \
    --proxy-protocol \
    --forwarded-allow-ips="10.0.2.100,127.0.0.1" \
    --log-syslog \
    --access-logfile - \
    --error-logfile - \
    --log-level="debug" \
    chanjo2.main:app --log-level debug

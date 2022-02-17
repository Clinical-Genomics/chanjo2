FROM clinicalgenomics/pyd4

LABEL base_image="clinicalgenomics/pyd4"
LABEL about.home="https://github.com/Clinical-Genomics/chanjo2"

ENV GUNICORN_WORKERS=1
ENV GUNICORN_THREADS=1
ENV GUNICORN_BIND="0.0.0.0:8000"
ENV GUNICORN_TIMEOUT=400

WORKDIR /home/worker/app
COPY . /home/worker/app

# Install poetry
RUN apt-get update 
RUN apt-get install -y default-libmysqlclient-dev
RUN pip install -r requirements.txt
RUN pip install .



# switch to gunicorn
CMD gunicorn\
    --workers=$GUNICORN_WORKERS \
    --bind=$GUNICORN_BIND \
    --threads=$GUNICORN_THREADS \
    --timeout=$GUNICORN_TIMEOUT \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level="debug" \
    chanjo2.main:app

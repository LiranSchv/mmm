FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libopenblas-dev gfortran pkg-config \
    r-base r-base-dev \
    libcurl4-openssl-dev libssl-dev libxml2-dev \
    libharfbuzz-dev libfribidi-dev libnlopt-dev libgit2-dev \
    && rm -rf /var/lib/apt/lists/*

# Cache bust — increment to force full rebuild of R + pip layers
ARG CACHE_BUST=7

# Install R packages — Robyn + runtime deps
RUN R -e "install.packages(c('jsonlite','data.table','reticulate','remotes'), repos='https://cran.r-project.org', dependencies=TRUE)" \
    && R -e "tryCatch(install.packages('Robyn', repos='https://cran.r-project.org', dependencies=TRUE), error=function(e) remotes::install_github('facebookexperimental/Robyn', subdir='R', dependencies=TRUE))" \
    && R -e "library(Robyn); cat('Robyn version:', as.character(packageVersion('Robyn')), '\n')"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTENSOR_FLAGS="mode=FAST_COMPILE,floatX=float64"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

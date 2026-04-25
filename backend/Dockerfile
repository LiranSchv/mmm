FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libopenblas-dev gfortran pkg-config \
    r-base r-base-dev \
    libcurl4-openssl-dev libssl-dev libxml2-dev \
    libharfbuzz-dev libfribidi-dev libnlopt-dev libgit2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages — Robyn + runtime deps
# Install dependencies first, then Robyn from CRAN with verbose output to catch errors
RUN R -e "install.packages(c('jsonlite','data.table','reticulate'), repos='https://cran.r-project.org', dependencies=TRUE)" \
    && R -e "install.packages('remotes', repos='https://cran.r-project.org')" \
    && R -e "remotes::install_github('facebookexperimental/Robyn/R', dependencies=TRUE, upgrade='never')"

COPY requirements.txt .
ARG CACHE_BUST=6
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTENSOR_FLAGS="mode=FAST_COMPILE,floatX=float64"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libopenblas-dev gfortran pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
ARG CACHE_BUST=8
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTENSOR_FLAGS="mode=FAST_COMPILE,floatX=float64"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

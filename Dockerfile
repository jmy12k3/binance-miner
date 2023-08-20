FROM python:3.11 as builder

WORKDIR /install

# https://cryptography.io/en/latest/installation/#debian-ubuntu
RUN apt-get update \ 
    && apt-get install -y rustc \
    && apt-get install -y build-essential \
    && apt-get install -y libssl-dev \
    && apt-get install -y libffi-dev \
    && apt-get install -y python3-dev \
    && apt-get install -y cargo \
    && apt-get install -y pkg-config 

COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

CMD ["python", "-m", "crypto_miner"]
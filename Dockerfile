FROM python:3.11 as builder

WORKDIR /install

RUN apt-get update && apt-get install -y rustc && apt-get install -y libssl-dev

COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

CMD ["python", "-m", "crypto_miner"]
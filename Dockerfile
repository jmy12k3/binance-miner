FROM python:3.11 as builder

WORKDIR /install

RUN apt-get update \
    && curl --proto "=https" --tlsv1.2 https://sh.rustup.rs > rustup.sh \
    && sh rustup.sh -y

COPY requirements.txt /requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip . $HOME/.cargo/env \
    && pip install --prefix=/install -r /requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

CMD ["python", "-m", "binance_miner"]
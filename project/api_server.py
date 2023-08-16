# mypy: disable-error-code=annotation-unchecked
from datetime import datetime
from itertools import groupby
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_socketio import SocketManager
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import CONFIG
from .database import Database
from .logger import DummyLogger
from .models import Coin, CoinValue, CurrentCoin, Pair, ScoutHistory, Trade

# Initialize FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sio = SocketManager(app)

# Initialize database
logger = DummyLogger()
db = Database(logger, CONFIG)


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/api/v1/current_coin")
def current_coin():
    coin = db.get_current_coin()
    return coin.info() if coin else None


@app.get("/api/v1/coins")
def coins():
    session: Session
    with db.db_session() as session:
        _current_coin = session.merge(db.get_current_coin())
        _coins: list[Coin] = session.query(Coin).all()
        return [{**coin.info(), "is_current": coin == _current_coin} for coin in _coins]


@app.get("/api/v1/pairs")
def pairs():
    session: Session
    with db.db_session() as session:
        all_pairs: list[Pair] = session.query(Pair).all()
        return [pair.info() for pair in all_pairs]


@app.get("/api/v1/value_history")
def value_history(coin: str | None = None):
    session: Session
    with db.db_session() as session:
        query = session.query(CoinValue).order_by(CoinValue.coin_id.asc(), CoinValue.datetime.asc())
        if coin:
            values: list[CoinValue] = query.filter(CoinValue.coin_id == coin).all()
            return [entry.info() for entry in values]
        coin_values = groupby(query.all(), key=lambda cv: cv.coin)
        return {coin.symbol: [entry.info() for entry in history] for coin, history in coin_values}


@app.get("/api/v1/total_value_history")
def total_value_history():
    session: Session
    with db.db_session() as session:
        query = session.query(
            CoinValue.datetime,
            func.sum(CoinValue.btc_value),
            func.sum(CoinValue.usd_value),
        ).group_by(CoinValue.datetime)
        total_values: list[tuple[datetime, float, float]] = query.all()
        return [{"datetime": tv[0], "btc": tv[1], "usd": tv[2]} for tv in total_values]


@app.get("/api/v1/current_coin_history")
def current_coin_history():
    session: Session
    with db.db_session() as session:
        query = session.query(CurrentCoin)
        current_coins: list[CurrentCoin] = query.all()
        return [cc.info() for cc in current_coins]


@app.get("/api/v1/scouting_history")
def scouting_history():
    _current_coin = db.get_current_coin()
    coin = _current_coin.symbol if _current_coin is not None else None
    session: Session
    with db.db_session() as session:
        query = (
            session.query(ScoutHistory)
            .join(ScoutHistory.pair)
            .filter(Pair.from_coin_id == coin)
            .order_by(ScoutHistory.datetime.asc())
        )
        scouts: list[ScoutHistory] = query.all()
        return [scout.info() for scout in scouts]


@app.get("/api/v1/trade_history")
def trade_history():
    session: Session
    with db.db_session() as session:
        query = session.query(Trade).order_by(Trade.datetime.asc())
        trades: list[Trade] = query.all()
        return [trade.info() for trade in trades]


@sio.on("update", namespace="/backend")
def on_update(msg: dict[str, str | dict[str, Any]]):
    sio.emit("update", msg, namespace="/frontend")

# https://github.com/python/mypy/issues/5570
# mypy: disable-error-code="annotation-unchecked, arg-type"
from datetime import datetime
from enum import Enum
from itertools import groupby
from typing import Any

from dateutil.relativedelta import relativedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_socketio import SocketManager
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

from . import models
from .config import Config
from .database import Database
from .logger import DummyLogger

# Initialize FastAPI server
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
logger = DummyLogger("api_server")
config = Config()
db = Database(logger, config)


class Period(str, Enum):
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "M"


def filter_period(period: Period | None, query: Query, model: type[models.DatetimeModel]) -> Query:
    if Period.SECOND == period:
        query = query.filter(model.datetime > datetime.now() - relativedelta(seconds=1))
    if Period.MINUTE == period:
        query = query.filter(model.datetime > datetime.now() - relativedelta(minutes=1))
    if Period.HOUR == period:
        query = query.filter(model.datetime > datetime.now() - relativedelta(hours=1))
    if Period.DAY == period:
        query = query.filter(model.datetime > datetime.now() - relativedelta(days=1))
    if Period.WEEK == period:
        query = query.filter(model.datetime > datetime.now() - relativedelta(weeks=1))
    if Period.MONTH == period:
        query = query.filter(model.datetime > datetime.now() - relativedelta(months=1))
    return query


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/api/v1/value_history")
def value_history(period: Period | None = None, coin: str | None = None):
    session: Session
    with db.db_session() as session:
        query = session.query(models.CoinValue).order_by(
            models.CoinValue.coin_id.asc(), models.CoinValue.datetime.asc()
        )
        query = filter_period(period, query, models.CoinValue)
        if coin:
            values: list[models.CoinValue] = query.filter(models.CoinValue.coin_id == coin).all()
            return [entry.info() for entry in values]
        coin_values = groupby(query.all(), key=lambda cv: cv.coin)
        return {coin.symbol: [entry.info() for entry in history] for coin, history in coin_values}


@app.get("/api/v1/total_value_history")
def total_value_history(period: Period | None = None):
    session: Session
    with db.db_session() as session:
        query = session.query(
            models.CoinValue.datetime,
            func.sum(models.CoinValue.btc_value),
            func.sum(models.CoinValue.usd_value),
        ).group_by(models.CoinValue.datetime)
        query = filter_period(period, query, models.CoinValue)
        total_values: list[tuple[datetime, float, float]] = query.all()
        return [{"datetime": tv[0], "btc": tv[1], "usd": tv[2]} for tv in total_values]


@app.get("/api/v1/trade_history")
def trade_history(period: Period | None = None):
    session: Session
    with db.db_session() as session:
        query = session.query(models.Trade).order_by(models.Trade.datetime.asc())
        query = filter_period(period, query, models.Trade)
        trades: list[models.Trade] = query.all()
        return [trade.info() for trade in trades]


@app.get("/api/v1/scouting_history")
def scouting_history(period: Period | None = None):
    _current_coin = db.get_current_coin()
    coin = _current_coin.symbol if _current_coin is not None else None
    session: Session
    with db.db_session() as session:
        query = (
            session.query(models.ScoutHistory)
            .join(models.ScoutHistory.pair)
            .filter(models.Pair.from_coin_id == coin)
            .order_by(models.ScoutHistory.datetime.asc())
        )
        query = filter_period(period, query, models.ScoutHistory)
        scouts: list[models.ScoutHistory] = query.all()
        return [scout.info() for scout in scouts]


@app.get("/api/v1/current_coin")
def current_coin():
    coin = db.get_current_coin()
    return coin.info() if coin else None


@app.get("/api/v1/current_coin_history")
def current_coin_history(period: Period | None = None):
    session: Session
    with db.db_session() as session:
        query = session.query(models.CurrentCoin)
        query = filter_period(period, query, models.CurrentCoin)
        current_coins: list[models.CurrentCoin] = query.all()
        return [cc.info() for cc in current_coins]


@app.get("/api/v1/coins")
def coins():
    session: Session
    with db.db_session() as session:
        _current_coin = session.merge(db.get_current_coin())
        _coins: list[models.Coin] = session.query(models.Coin).all()
        return [{**coin.info(), "is_current": coin == _current_coin} for coin in _coins]


@app.get("/api/v1/pairs")
def pairs():
    session: Session
    with db.db_session() as session:
        all_pairs: list[models.Pair] = session.query(models.Pair).all()
        return [pair.info() for pair in all_pairs]


@sio.on("update", namespace="/backend")
def on_update(sid: str, msg: Any):
    sio.emit("update", msg, namespace="/frontend")

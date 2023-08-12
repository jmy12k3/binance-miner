# mypy: disable-error-code=annotation-unchecked
from datetime import datetime
from itertools import groupby
from typing import no_type_check

from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

from .config import CONFIG
from .database import Database
from .logger import Logger
from .models import Coin, CoinValue, CurrentCoin, Pair, ScoutHistory, Trade

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

logger = Logger(None)
db = Database(logger, CONFIG)


@no_type_check
def filter_period(query: Query, model: CoinValue | CurrentCoin | ScoutHistory | Trade) -> Query:
    period = request.args.get("period")
    if not period:
        return query
    if "s" in period:
        return query.filter(model.datetime >= datetime.now() - relativedelta(seconds=1))
    if "h" in period:
        return query.filter(model.datetime >= datetime.now() - relativedelta(hours=1))
    if "d" in period:
        return query.filter(model.datetime >= datetime.now() - relativedelta(days=1))
    if "w" in period:
        return query.filter(model.datetime >= datetime.now() - relativedelta(weeks=1))
    if "m" in period:
        return query.filter(model.datetime >= datetime.now() - relativedelta(months=1))


@app.route("/api/value_history")
@app.route("/api/value_history/<coin>")
def value_history(coin: str | None = None):
    session: Session
    with db.db_session() as session:
        query = session.query(CoinValue).order_by(CoinValue.coin_id.asc(), CoinValue.datetime.asc())
        query = filter_period(query, CoinValue)  # type: ignore
        if coin:
            values: list[CoinValue] = query.filter(CoinValue.coin_id == coin).all()
            return jsonify([entry.info() for entry in values])
        coin_values = groupby(query.all(), key=lambda cv: cv.coin)
        return jsonify(
            {coin.symbol: [entry.info() for entry in history] for coin, history in coin_values}
        )


@app.route("/api/total_value_history")
def total_value_history():
    session: Session
    with db.db_session() as session:
        query = session.query(
            CoinValue.datetime,
            func.sum(CoinValue.btc_value),
            func.sum(CoinValue.usd_value),
        ).group_by(CoinValue.datetime)
        query = filter_period(query, CoinValue)
        total_values: list[tuple[datetime, float, float]] = query.all()
        return jsonify([{"datetime": tv[0], "btc": tv[1], "usd": tv[2]} for tv in total_values])


@app.route("/api/trade_history")
def trade_history():
    session: Session
    with db.db_session() as session:
        query = session.query(Trade).order_by(Trade.datetime.asc())
        query = filter_period(query, Trade)
        trades: list[Trade] = query.all()
        return jsonify([trade.info() for trade in trades])


@app.route("/api/scouting_history")
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
        query = filter_period(query, ScoutHistory)
        scouts: list[ScoutHistory] = query.all()
        return jsonify([scout.info() for scout in scouts])


@app.route("/api/current_coin")
def current_coin():
    coin = db.get_current_coin()
    return coin.info() if coin else None


@app.route("/api/current_coin_history")
def current_coin_history():
    session: Session
    with db.db_session() as session:
        query = session.query(CurrentCoin)
        query = filter_period(query, CurrentCoin)
        current_coins: list[CurrentCoin] = query.all()
        return jsonify([cc.info() for cc in current_coins])


@app.route("/api/coins")
def coins():
    session: Session
    with db.db_session() as session:
        _current_coin = session.merge(db.get_current_coin())
        _coins: list[Coin] = session.query(Coin).all()
        return jsonify([{**coin.info(), "is_current": coin == _current_coin} for coin in _coins])


@app.route("/api/pairs")
def pairs():
    session: Session
    with db.db_session() as session:
        all_pairs: list[Pair] = session.query(Pair).all()
        return jsonify([pair.info() for pair in all_pairs])


@socketio.on("update", namespace="/backend")
def on_update(msg):
    emit("update", msg, namespace="/frontend", broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True)

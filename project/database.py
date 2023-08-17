# mypy: disable-error-code=annotation-unchecked
import time
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from typing import Annotated, no_type_check

from dateutil.relativedelta import relativedelta
from easydict import EasyDict
from socketio import Client, exceptions
from sqlalchemy import bindparam, create_engine, func, insert, select, update
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from . import models
from .config import CONFIG
from .logger import AbstractLogger
from .postpone import heavy_call
from .ratios import CoinStub, RatiosManager

LogScout = namedtuple(
    "LogScout", ["pair_id", "ratio_diff", "target_ratio", "coin_price", "optional_coin_price"]
)


class Database:
    # URL for SQLite database
    URL = "sqlite:///data/crypto_trading.db"

    # URL for API server deployed in Docker
    API = "http://api:5000"

    def __init__(self, logger: AbstractLogger, config: Annotated[EasyDict, CONFIG]):
        self.logger = logger
        self.config = config
        self.engine = create_engine(self.URL, future=True)
        self.session_factory = scoped_session(sessionmaker(self.engine))
        self.socketio_client = Client()
        self.ratios_manager: RatiosManager | None = None

    @contextmanager
    def db_session(self):
        session: Session = self.session_factory()
        yield session
        session.commit()
        session.close()

    def _api_session(self):
        if self.socketio_client.connected and self.socketio_client.namespaces:
            return True
        try:
            if not self.socketio_client.connected:
                self.socketio_client.connect(self.API, namespaces=["/backend"])
            while not self.socketio_client.connected or not self.socketio_client.namespaces:
                time.sleep(0.1)
            return True
        except exceptions.ConnectionError:
            return False

    def create_database(self):
        models.Base.metadata.create_all(self.engine)
        try:
            with self.db_session() as session:
                session.execute("ALTER TABLE scout_history ADD COLUMN ratio_diff float;")
        except Exception:
            pass

    def send_update(self, model):
        if not self._api_session():
            return
        self.socketio_client.emit(
            "update", {"table": model.__tablename__, "data": model.info()}, "/backend"
        )

    @no_type_check
    def set_coins(self, symbols: list[str]):
        session: Session
        with self.db_session() as session:
            coins: list[models.Coin] = session.query(models.Coin).all()
            for coin in coins:
                if coin.symbol not in symbols:
                    coin.enabled = False
            for symbol in symbols:
                coin = next((coin for coin in coins if coin.symbol == symbol), None)
                if coin is None:
                    session.add(models.Coin(symbol))
                else:
                    coin.enabled = True
        CoinStub.reset()
        with self.db_session() as session:
            coins: list[models.Coin] = (
                session.query(models.Coin)
                .filter(models.Coin.enabled)
                .order_by(models.Coin.symbol)
                .all()
            )
            for coin in coins:
                CoinStub.create(coin.symbol)
            for from_coin in coins:
                for to_coin in coins:
                    if from_coin != to_coin:
                        pair = (
                            session.query(models.Pair)
                            .filter(
                                models.Pair.from_coin == from_coin, models.Pair.to_coin == to_coin
                            )
                            .first()
                        )
                        if pair is None:
                            session.add(models.Pair(from_coin, to_coin))
        with self.db_session() as session:
            pairs = session.query(models.Pair).filter(models.Pair.enabled.is_(True)).all()
            self.ratios_manager = RatiosManager(pairs)

    def get_coins(self, only_enabled: bool = True) -> list[models.Coin]:
        session: Session
        with self.db_session() as session:
            if only_enabled:
                coins = session.query(models.Coin).filter(models.Coin.enabled).all()
            else:
                coins = session.query(models.Coin).all()
            session.expunge_all()
            return coins

    def get_coin(self, coin: models.Coin | str):
        if isinstance(coin, models.Coin):
            return coin
        session: Session
        with self.db_session() as session:
            coin = session.get(models.Coin, coin)  # type: ignore
            session.expunge(coin)
            return coin

    def set_current_coin(self, coin: models.Coin | str):
        coin = self.get_coin(coin)
        session: Session
        with self.db_session() as session:
            if isinstance(coin, models.Coin):
                coin = session.merge(coin)
            cc = CurrentCoin(coin)  # type: ignore
            session.add(cc)
            self.send_update(cc)

    def get_current_coin(self) -> models.Coin | None:
        session: Session
        with self.db_session() as session:
            current_coin = (
                session.query(models.CurrentCoin)
                .order_by(models.CurrentCoin.datetime.desc())
                .first()
            )
            if current_coin is None:
                return None
            coin = current_coin.coin
            session.expunge(coin)
            return coin

    def get_pair(self, from_coin: models.Coin | str, to_coin: models.Coin | str):
        from_coin = self.get_coin(from_coin)
        to_coin = self.get_coin(to_coin)
        session: Session
        with self.db_session() as session:
            pair: models.Pair | None = (
                session.query(models.Pair)
                .filter(models.Pair.from_coin == from_coin, models.Pair.to_coin == to_coin)
                .first()
            )
            session.expunge(pair)
            return pair

    def prune_scout_history(self):
        time_diff = datetime.now() - relativedelta(hours=self.config.SCOUT_HISTORY_PRUNE_TIME)
        session: Session
        with self.db_session() as session:
            session.query(models.ScoutHistory).filter(
                models.ScoutHistory.datetime < time_diff
            ).delete()

    def prune_value_history(self):
        def _datetime_id_query(dt_format):
            dt_column = func.strftime(dt_format, models.CoinValue.datetime)
            grouped = select(
                models.CoinValue, func.max(models.CoinValue.datetime), dt_column
            ).group_by(models.CoinValue.coin_id, models.CoinValue, dt_column)
            return select(grouped.c.id.label("id")).select_from(grouped)

        def _update_query(datetime_query, interval):
            return (
                update(models.CoinValue)
                .where(models.CoinValue.id.in_(datetime_query))
                .values(interval=interval)
                .execution_options(synchronize_session="fetch")
            )

        hourly_update_query = _update_query(_datetime_id_query("%H"), models.Interval.HOURLY)
        weekly_update_query = _update_query(_datetime_id_query("%Y-%W"), models.Interval.WEEKLY)
        daily_update_query = _update_query(_datetime_id_query("%Y-%j"), models.Interval.DAILY)
        session: Session
        with self.db_session() as session:
            session.execute(hourly_update_query)
            session.execute(daily_update_query)
            session.execute(weekly_update_query)
            session.commit()
            time_diff = datetime.now() - relativedelta(days=1)
            session.query(models.CoinValue).filter(
                models.CoinValue.interval == models.Interval.MINUTELY,
                models.CoinValue.datetime < time_diff,
            ).delete()
            time_diff = datetime.now() - relativedelta(months=1)
            session.query(models.CoinValue).filter(
                models.CoinValue.interval == models.Interval.HOURLY,
                models.CoinValue.datetime < time_diff,
            ).delete()
            time_diff = datetime.now() - relativedelta(years=1)
            session.query(models.CoinValue).filter(
                models.CoinValue.interval == models.Interval.DAILY,
                models.CoinValue.datetime < time_diff,
            ).delete()

    def batch_update_coin_values(self, cv_batch: list[models.CoinValue]):
        session: Session
        with self.db_session() as session:
            session.execute(
                insert(models.CoinValue),
                [
                    {
                        "coin_id": cv.coin.symbol,
                        "balance": cv.balance,
                        "usd_price": cv.usd_price,
                        "btc_price": cv.btc_price,
                        "interval": cv.interval,
                        "datetime": cv.datetime,
                    }
                    for cv in cv_batch
                ],
            )

    @heavy_call
    def batch_log_scout(self, logs: list[LogScout]):
        session: Session
        with self.db_session() as session:
            dt = datetime.now()
            for ls in logs:
                sh = {
                    "pair_id": ls.pair_id,
                    "ratio_diff": ls.ratio_diff,
                    "target_ratio": ls.target_ratio,
                    "current_coin_price": ls.coin_price,
                    "other_coin_price": ls.optional_coin_price,
                    "datetime": dt,
                }
                session.execute(insert(models.ScoutHistory), sh)
                self.send_update(sh)

    @heavy_call
    def commit_ratios(self):
        dirty_cells = self.ratios_manager.get_dirty()
        if len(dirty_cells) == 0:
            return
        pair_t = models.Pair.__table__
        stmt = (
            pair_t.update()
            .where(pair_t.c.id == bindparam("pair_id"))
            .values(ratio=bindparam("pair_ratio"))
        )
        with self.db_session() as session:
            session.execute(
                stmt,
                [
                    {
                        "pair_id": self.ratios_manager.get_pair_id(from_idx, to_idx),
                        "pair_ratio": self.ratios_manager.get(from_idx, to_idx),
                    }
                    for from_idx, to_idx in dirty_cells
                ],
            )
        self.ratios_manager.commit()

    def start_trade_log(self, from_coin: str, to_coin: str, selling: bool):
        return TradeLog(self, from_coin, to_coin, selling)


class TradeLog:
    def __init__(self, db: Database, from_coin: str, to_coin: str, selling: bool):
        self.db = db
        session: Session
        with self.db.db_session() as session:
            self.trade = models.Trade(from_coin, to_coin, selling)
            session.add(self.trade)
            session.flush()
            self.db.send_update(self.trade)

    @no_type_check
    def set_ordered(
        self, alt_starting_balance: float, crypto_starting_balance: float, alt_trade_amount: float
    ):
        session: Session
        with self.db.db_session() as session:
            trade: models.Trade = session.merge(self.trade)
            trade.alt_starting_balance = alt_starting_balance
            trade.alt_trade_amount = alt_trade_amount
            trade.crypto_starting_balance = crypto_starting_balance
            trade.state = models.TradeState.ORDERED
            self.db.send_update(trade)

    @no_type_check
    def set_complete(self, crypto_trade_amount: float):
        session: Session
        with self.db.db_session() as session:
            trade: models.Trade = session.merge(self.trade)
            trade.crypto_trade_amount = crypto_trade_amount
            trade.state = models.TradeState.COMPLETE
            self.db.send_update(trade)

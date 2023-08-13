# mypy: disable-error-code="operator, union-attr"
from collections import defaultdict
from datetime import datetime, timedelta
from traceback import format_exc
from typing import Annotated

from binance import Client
from binance.exceptions import BinanceAPIException
from easydict import EasyDict
from sqlitedict import SqliteDict

from .binance import BinanceAPIManager, BinanceOrderBalanceManager
from .binance_ws import BinanceCache, BinanceOrder
from .config import CONFIG
from .database import Database, LogScout
from .logger import Logger
from .strategies import get_strategy


class MockBinanceManager(BinanceAPIManager):
    def __init__(
        self,
        client: Client,
        sqlite_cache: SqliteDict,
        binance_cache: BinanceCache,
        config: EasyDict,
        db: Database,
        logger: Logger,
        start_date: datetime,
        start_balances: dict[str, float],
    ):
        super().__init__(
            client,
            binance_cache,
            config,
            db,
            logger,
            BinanceOrderBalanceManager(logger, client, binance_cache),
        )
        self.sqlite_cache = sqlite_cache
        self.config = config
        self.datetime = start_date
        self.balances = start_balances
        self.non_existing_pairs: set = set()
        self.reinit_trader_callback = None

    def set_reinit_trader_callback(self, reinit_trader_callback):
        self.reinit_trader_callback = reinit_trader_callback

    def set_coins(self, coins_list: list[str]):
        self.db.set_coins(coins_list)
        if self.reinit_trader_callback is not None:
            self.reinit_trader_callback()

    def setup_websockets(self):
        pass

    def increment(self, interval: int = 1):
        self.datetime += timedelta(minutes=interval)

    def get_fee(self, origin_coin: str, target_coin: str, selling: bool):
        return 0.001

    def get_ticker_price(self, ticker_symbol: str) -> float | None:
        target_date = self.datetime.strftime("%d %b %Y %H:%M:%S")
        key = f"{ticker_symbol} - {target_date}"
        val = self.sqlite_cache.get(key, None)
        if val is None:
            end_date = self.datetime + timedelta(minutes=1000)
            if end_date > datetime.now():
                end_date = datetime.now()
            end_date_str = end_date.strftime("%d %b %Y %H:%M:%S")
            historical_klines = self.binance_client.get_historical_klines(
                ticker_symbol, "1m", target_date, end_date_str, limit=1000
            )
            no_data_cur_date = self.datetime
            no_data_end_date = (
                end_date
                if len(historical_klines) == 0
                else (
                    datetime.utcfromtimestamp(historical_klines[0][0] / 1000) - timedelta(minutes=1)
                )
            )
            while no_data_cur_date <= no_data_end_date:
                self.sqlite_cache[
                    f"{ticker_symbol} - {no_data_cur_date.strftime('%d %b %Y %H:%M:%S')}"
                ] = 0.0
                no_data_cur_date += timedelta(minutes=1)
            for result in historical_klines:
                date = datetime.utcfromtimestamp(result[0] / 1000).strftime("%d %b %Y %H:%M:%S")
                price = float(result[1])
                self.sqlite_cache[f"{ticker_symbol} - {date}"] = price
            self.sqlite_cache.commit()
            val = self.sqlite_cache.get(key, None)
        return val if val != 0.0 else None

    def get_currency_balance(self, currency_symbol: str, force: bool = False):
        return self.balances.get(currency_symbol, 0)

    def get_market_sell_price(
        self, symbol: str, amount: float
    ) -> tuple[float, float] | tuple[None, None]:
        price = self.get_ticker_price(symbol)
        return (price, amount * price) if price is not None else (None, None)

    def get_market_buy_price(
        self, symbol: str, quote_amount: float
    ) -> tuple[float, float] | tuple[None, None]:
        price = self.get_ticker_price(symbol)
        return (price, quote_amount / price) if price is not None else (None, None)

    def get_market_sell_price_fill_quote(
        self, symbol: str, quote_amount: float
    ) -> tuple[float, float] | tuple[None, None]:
        price = self.get_ticker_price(symbol)
        return (price, quote_amount / price) if price is not None else (None, None)

    def buy_alt(self, origin_coin: str, target_coin: str, buy_price: float):
        origin_symbol = origin_coin
        target_symbol = target_coin
        target_balance = self.get_currency_balance(target_symbol)
        from_coin_price = self.get_ticker_price(origin_symbol + target_symbol)
        assert abs(buy_price - from_coin_price) < 1e-15 or buy_price == 0.0
        order_quantity = self.buy_quantity(
            origin_symbol, target_symbol, target_balance, from_coin_price
        )
        target_quantity = order_quantity * from_coin_price
        self.balances[target_symbol] -= target_quantity
        order_filled_quantity = order_quantity * (1 - self.get_fee(origin_coin, target_coin, False))
        self.balances[origin_symbol] = self.balances.get(origin_symbol, 0) + order_filled_quantity
        return BinanceOrder(
            defaultdict(
                lambda: None,
                price=from_coin_price,
                cummulativeQuoteQty=target_quantity,
                executedQty=order_quantity,
            )
        )

    def sell_alt(self, origin_coin: str, target_coin: str, sell_price: float):
        origin_symbol = origin_coin
        target_symbol = target_coin
        origin_balance = self.get_currency_balance(origin_symbol)
        from_coin_price = self.get_ticker_price(origin_symbol + target_symbol)
        assert abs(sell_price - from_coin_price) < 1e-15
        order_quantity = self.sell_quantity(origin_symbol, target_symbol, origin_balance)
        target_quantity = order_quantity * from_coin_price
        target_filled_quantity = target_quantity * (
            1 - self.get_fee(origin_coin, target_coin, True)
        )
        self.balances[target_symbol] = self.balances.get(target_symbol, 0) + target_filled_quantity
        self.balances[origin_symbol] -= order_quantity
        return BinanceOrder(
            defaultdict(
                lambda: None,
                price=from_coin_price,
                cummulativeQuoteQty=target_quantity,
                executedQty=order_quantity,
            )
        )

    def collate_coins(self, target_symbol: str):
        total = 0.0
        for coin, balance in self.balances.items():
            if coin == target_symbol:
                total += balance
                continue
            if coin == self.config.BRIDGE.symbol:
                price = self.get_ticker_price(target_symbol + coin)
                if price is None:
                    continue
                total += balance / price
            else:
                if coin + target_symbol in self.non_existing_pairs:
                    continue
                price = None
                try:
                    price = self.get_ticker_price(coin + target_symbol)
                except BinanceAPIException:
                    self.non_existing_pairs.add(coin + target_symbol)
                if price is None:
                    continue
                total += price * balance
        return total


class MockDatabase(Database):
    DB = "sqlite:///"

    def __init__(self, logger: Logger, config: Annotated[EasyDict, CONFIG]):
        super().__init__(logger, config)

    def batch_log_scout(self, logs: list[LogScout]):
        pass


def backtest(
    start_date: datetime,
    end_date: datetime | None = None,
    interval: int = 1,
    yield_interval: int = 100,
    start_balances: dict[str, float] | None = None,
    starting_coin: str | None = None,
):
    # Initialize modules
    sqlite_cache = SqliteDict("data/backtest_cache.db")
    logger = Logger("backtesting", False)
    end_date = end_date or datetime.today()
    start_balances = start_balances or {CONFIG.BRIDGE.symbol: CONFIG.PAPER_WALLET_BALANCE}

    # Initialize database
    db = MockDatabase(logger, CONFIG)
    db.create_database()
    db.set_coins(CONFIG.WATCHLIST)

    # Initialize manager and database
    manager = MockBinanceManager(
        Client(CONFIG.BINANCE_API_KEY, CONFIG.BINANCE_API_SECRET_KEY),
        sqlite_cache,
        BinanceCache(),
        CONFIG,
        db,
        logger,
        start_date,
        start_balances,
    )
    starting_coin = db.get_coin(starting_coin or CONFIG.WATCHLIST[0])
    if manager.get_currency_balance(starting_coin.symbol) == 0:
        manager.buy_alt(starting_coin.symbol, CONFIG.BRIDGE.symbol, 0.0)
    db.set_current_coin(starting_coin)  # type: ignore

    # Initialize autotrader
    strategy = get_strategy(CONFIG.STRATEGY)
    if strategy is None:
        logger.error(f"Invalid strategy: {strategy}")
        return manager
    trader = strategy(logger, CONFIG, db, manager)
    logger.info(f"Chosen strategy: {strategy}")
    trader.initialize()

    # Yield manager
    manager.set_reinit_trader_callback(trader.initialize)
    yield manager

    # Initiate backtesting
    n = 1
    try:
        while manager.datetime < end_date:
            try:
                trader.scout()
            except Exception:
                logger.warning(f"An error occured\n\n{format_exc()}")
            manager.increment(interval)
            if n % yield_interval:
                yield manager
            n += 1
    except KeyboardInterrupt:
        pass

    # Initiate clean-up
    sqlite_cache.close()
    return manager

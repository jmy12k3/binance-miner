import atexit
import os
import signal
import time
from threading import Thread
from typing import Any

from .binance import BinanceAPIManager
from .config import CONFIG
from .database import Database
from .logger import Logger
from .scheduler import SafeScheduler
from .strategies import get_strategy

TIMEOUT = 10


def main():
    # Initialize exit_handler flag
    exiting = False

    # Initialize logger and database
    logger = Logger("crypto_trading")
    logger.info("Starting")
    db = Database(logger, CONFIG)

    # Initialize manager
    if CONFIG.ENABLE_PAPER_TRADING:
        manager = BinanceAPIManager.create_manager_paper_trading(
            CONFIG, db, logger, {CONFIG.BRIDGE.symbol: CONFIG.PAPER_WALLET_BALANCE}
        )
        logger.info("Will be running in paper trading mode")
    else:
        manager = BinanceAPIManager.create_manager(CONFIG, db, logger)
        logger.info("Will be running in live trading mode")

    # Initialize exit handler
    def timeout_exit():
        thread = Thread(target=manager.close)
        thread.start()
        thread.join(TIMEOUT)

    def exit_handler(f_code=0, _: Any | None = None):
        nonlocal exiting
        if not exiting:
            exiting = True
            timeout_exit()
            os._exit(f_code)

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    atexit.register(exit_handler)

    # Verify Binance API key
    try:
        _ = manager.get_account()
    except Exception as e:
        logger.error(e)
        return exit_handler(1)

    # Get strategy
    strategy = get_strategy(CONFIG.STRATEGY)
    if not strategy:
        logger.error(f"Invalid strategy '{CONFIG.STRATEGY}'")
        return exit_handler(1)
    trader = strategy(logger, CONFIG, db, manager)
    logger.info(f"Using {CONFIG.STRATEGY} strategy")

    # Warmup database and initialize autotrader
    db.create_database()
    db.set_coins(CONFIG.WATCHLIST)
    logger.info(f"Warming up database for {TIMEOUT} seconds")
    time.sleep(TIMEOUT)
    trader.initialize()

    # Initialize scheduler
    schedule = SafeScheduler(logger)
    schedule.every(CONFIG.SCOUT_SLEEP_TIME).seconds.do(trader.scout)
    schedule.every(1).minutes.do(trader.update_values)
    schedule.every(1).minutes.do(db.prune_scout_history)
    schedule.every(1).hours.do(db.prune_value_history)

    # Running schedules until exit_handler is called
    while not exiting:
        schedule.run_pending()
        time.sleep(1)

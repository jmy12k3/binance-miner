import atexit
import os
import signal
import time
from threading import Thread

from .binance import BinanceAPIManager
from .config import Config
from .database import Database
from .logger import Logger
from .scheduler import SafeScheduler
from .strategies import get_strategy


def main():
    # Initialize exit_handler flag and logger
    exiting = False
    logger = Logger()
    logger.info("Starting")

    # Initialize config and database
    config = Config()
    db = Database(logger, config)

    # Initialize manager
    if config.ENABLE_PAPER_TRADING:
        manager = BinanceAPIManager.create_manager_paper_trading(
            logger, config, db, {config.BRIDGE.symbol: config.PAPER_WALLET_BALANCE}
        )
        logger.info("Will be running in paper trading mode")
    else:
        manager = BinanceAPIManager.create_manager(logger, config, db)
        logger.info("Will be running in live trading mode")

    # Initialize exit_handler
    def timeout_exit(timeout: float | None = None):
        thread = Thread(target=manager.close)
        thread.start()
        thread.join(timeout)

    def exit_handler(signum: signal.Signals, frame: object):
        nonlocal exiting
        if not exiting:
            exiting = True
            timeout_exit(10)
            os._exit(0)

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    atexit.register(exit_handler)

    # Validate Binance API keys
    try:
        _ = manager.get_account()
    except Exception as e:
        logger.error(e)
        return

    # Get autotrader strategy
    strategy = get_strategy(config.STRATEGY)
    if strategy is None:
        logger.info(f"Invalid strategy: {config.STRATEGY}")
        return
    trader = strategy(logger, config, db, manager)
    logger.info(f"Chosen strategy: {config.STRATEGY}")

    # Create database
    logger.info("Creating database schema if it doesn't already exist")
    db.create_database()

    # Set watchlist and initialize autotrader
    db.set_coins(config.WATCHLIST)
    time.sleep(10)
    trader.initialize()

    # Initialize scheduler
    schedule = SafeScheduler(logger)
    schedule.every(config.SCOUT_SLEEP_TIME).seconds.do(trader.scout)
    schedule.every().minutes.do(trader.update_values)
    schedule.every().minutes.do(db.prune_scout_history)
    schedule.every().hours.do(db.prune_value_history)

    # Initiate scheduler loop
    while not exiting:
        schedule.run_pending()
        time.sleep(1)

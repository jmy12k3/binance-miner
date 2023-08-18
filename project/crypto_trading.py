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
    # Instantiate logger, config, and database
    exiting = False
    logger = Logger("crypto_trading")
    logger.info("Starting")
    config = Config()
    db = Database(logger, config)

    # Create manager
    if config.ENABLE_PAPER_TRADING:
        manager = BinanceAPIManager.create_manager_paper_trading(
            logger, config, db, {config.BRIDGE.symbol: config.PAPER_WALLET_BALANCE}
        )
        logger.info("Will be running in paper trading mode")
    else:
        manager = BinanceAPIManager.create_manager(logger, config, db)
        logger.info("Will be running in live trading mode")

    # Create and hook exit handler
    def timeout_exit():
        thread = Thread(target=manager.close)
        thread.start()
        thread.join(10)  # Docker defaults to SIGKILL after 10 seconds

    def exit_handler(*_):
        nonlocal exiting
        if not exiting:
            exiting = True
            timeout_exit()
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

    # Get strategy
    strategy = get_strategy(config.STRATEGY)
    if not strategy:
        logger.info(f"Invalid strategy: {config.STRATEGY}")
        return
    trader = strategy(logger, config, db, manager)
    logger.info(f"Chosen strategy: {config.STRATEGY}")

    # Create database
    logger.info("Creating database schema if it doesn't already exist")
    db.create_database()

    # Warmup database
    db.set_coins(config.WATCHLIST)
    logger.info("Sleeping for 10 seconds to let order book to fill up")
    time.sleep(10)  # 10 seconds is just a arbitrary number
    trader.initialize()

    # Initialize scheduler
    schedule = SafeScheduler(logger)
    schedule.every(config.SCOUT_SLEEP_TIME).seconds.do(trader.scout)
    schedule.every(1).minutes.do(trader.update_values)
    schedule.every(1).minutes.do(db.prune_scout_history)
    schedule.every(1).hours.do(db.prune_value_history)

    # Initiate scheduler loop
    while not exiting:
        schedule.run_pending()
        time.sleep(1)

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
    # Initialize modules
    exiting = False
    logger = Logger()
    logger.info("Starting")
    config = Config()
    db = Database(logger, config)

    # Initialize manager
    if config.ENABLE_PAPER_TRADING:
        manager = BinanceAPIManager.create_manager_paper_trading(
            config, db, logger, {config.BRIDGE.symbol: config.PAPER_BALANCE}
        )
    else:
        manager = BinanceAPIManager.create_manager(config, db, logger)

    # Initialize exit timeout
    def timeout_exit(timeout: int):
        logger.info(f"Waiting for {timeout} seconds at most to clean-up")
        thread = Thread(target=manager.close)
        thread.start()
        thread.join(timeout)

    # Initialize exit handler
    def exit_handler(*_):
        nonlocal exiting
        if exiting:
            return
        exiting = True
        timeout_exit(10)
        os._exit(0)

    # Hook exit handler
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    atexit.register(exit_handler)

    # Check if API keys are valid
    try:
        _ = manager.get_account()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"An error occured: {e}")
        return

    # Initialize strategy
    strategy = get_strategy(config.STRATEGY)
    if strategy is None:
        logger.error(f"Invalid strategy: {config.STRATEGY}")
        return
    trader = strategy(manager, db, logger, config)

    # Log configurations
    logger.info(f"Chosen strategy: {config.STRATEGY}")
    logger.info(f"Paper trading: {config.ENABLE_PAPER_TRADING}")

    # Initialize database
    logger.info("Warming up order books")
    db.create_database()
    db.set_coins(config.WATCHLIST)
    time.sleep(10)
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

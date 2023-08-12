import atexit
import os
import signal
import time
from threading import Thread

from .binance import BinanceAPIManager
from .config import CONFIG
from .database import Database
from .logger import Logger
from .scheduler import SafeScheduler
from .strategies import get_strategy


def main():
    # Initialize exit flag
    exiting = False

    # Initialize modules
    logger = Logger(logging_service="crypto_trading")
    logger.info("Starting")
    db = Database(logger, CONFIG)

    # Initialize manager
    if CONFIG.ENABLE_PAPER_TRADING:
        manager = BinanceAPIManager.create_manager_paper_trading(
            CONFIG, db, logger, {CONFIG.BRIDGE.symbol: CONFIG.PAPER_WALLET_BALANCE}
        )
    else:
        manager = BinanceAPIManager.create_manager(CONFIG, db, logger)

    # Initialize clean-up
    def timeout_exit(timeout: int):
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

    # Hook signals to exit handler
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    atexit.register(exit_handler)

    # Initiate websocket (test if private API keys are valid)
    try:
        _ = manager.get_account()
    except Exception as e:
        logger.error(f"An error occured: {e}")
        return

    # Initialize autotrader
    strategy = get_strategy(CONFIG.STRATEGY)
    if strategy is None:
        logger.error(f"Invalid strategy: {strategy}")
        return
    trader = strategy(logger, CONFIG, db, manager)

    # Log configurations (partially)
    logger.info(f"Chosen strategy: {CONFIG.STRATEGY}")
    logger.info(f"Paper trading: {CONFIG.ENABLE_PAPER_TRADING}")

    # Initialize database
    db.create_database()
    db.set_coins(CONFIG.WATCHLIST)
    time.sleep(10)
    trader.initialize()

    # Initialize scheduler
    schedule = SafeScheduler(logger)
    schedule.every(CONFIG.SCOUT_SLEEP_TIME).seconds.do(trader.scout)
    schedule.every(1).minutes.do(trader.update_values)
    schedule.every(1).minutes.do(db.prune_scout_history)
    schedule.every(1).hours.do(db.prune_value_history)

    # Initiate scheduler loop
    while not exiting:
        schedule.run_pending()
        time.sleep(1)

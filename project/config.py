import os

from pydantic_settings import BaseSettings

from .models import Coin

CONFIG_PATH = "config"
ENV_PATH_NAME = os.path.join(CONFIG_PATH, "process.env")

# XXX: Consider fully remove watchlist.txt and use WATCHLIST env variable only
WATCHLIST_PATH_NAME = os.path.join(CONFIG_PATH, "watchlist.txt")


class Settings(BaseSettings):
    BRIDGE_SYMBOL: str = "USDT"
    SCOUT_HISTORY_PRUNE_TIME: float = 1
    SCOUT_MULTIPLIER: float = 5
    SCOUT_SLEEP_TIME: int = 1
    USE_MARGIN: bool = True
    SCOUT_MARGIN: float = 0.8
    BINANCE_API_KEY: str
    BINANCE_API_SECRET_KEY: str
    TLD: str = "com"
    WATCHLIST: str = ""
    STRATEGY: str = "default"
    ENABLE_PAPER_TRADING: bool
    PAPER_WALLET_BALANCE: float = 10_000


settings = Settings(_env_file=ENV_PATH_NAME, _env_file_encoding="utf-8")  # type: ignore

# XXX: Consider fully remove watchlist.txt and use WATCHLIST env variable only
WATCHLIST = [coin.strip() for coin in settings.WATCHLIST.split() if coin.strip()]
if not WATCHLIST and os.path.exists(WATCHLIST_PATH_NAME):
    with open(WATCHLIST_PATH_NAME) as watchlist:
        for line in watchlist:
            line = line.strip()
            if not line or line in WATCHLIST:
                continue
            WATCHLIST.append(line)


class Config:
    def __init__(self):
        self.BRIDGE = Coin(settings.BRIDGE_SYMBOL, enabled=False)

        # XXX: Consider fully remove watchlist.txt and use WATCHLIST env variable only
        self.WATCHLIST = WATCHLIST

    def __getattr__(self, name: str):
        return getattr(settings, name)

import os
from typing import Annotated, Optional
from warnings import filterwarnings

import pydantic_settings
from easydict import EasyDict

from .models import Coin

filterwarnings("ignore", module=pydantic_settings.__name__)

CONFIG_PATH = "config"

ENV_PATH_NAME = os.path.join(CONFIG_PATH, ".env.production")
WATCHLIST_PATH_NAME = os.path.join(CONFIG_PATH, "watchlist.txt")


class Config(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=ENV_PATH_NAME,
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets",
    )

    BRIDGE_SYMBOL: str
    SCOUT_HISTORY_PRUNE_TIME: Optional[float] = 1
    SCOUT_MULTIPLIER: Optional[float] = 5
    SCOUT_SLEEP_TIME: Optional[int] = 1
    USE_MARGIN: Optional[bool] = True
    SCOUT_MARGIN: Optional[float] = 0.8
    BINANCE_API_KEY: str
    BINANCE_API_SECRET_KEY: str
    WATCHLIST: Optional[str] = ""
    STRATEGY: Optional[str] = "default"
    ENABLE_PAPER_TRADING: bool
    PAPER_WALLET_BALANCE: Optional[float] = 10_000


settings = Config()  # type: ignore

watchlist = [coin.strip() for coin in os.environ.get("WATCHLIST", "").split() if coin.strip()]
if not watchlist and os.path.exists(WATCHLIST_PATH_NAME):
    with open(WATCHLIST_PATH_NAME) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line in watchlist:
                continue
            watchlist.append(line)

CONFIG: Annotated[EasyDict, "CONFIG"] = EasyDict(
    {
        "BRIDGE_SYMBOL": settings.BRIDGE_SYMBOL,
        "BRIDGE": Coin(settings.BRIDGE_SYMBOL, False),
        "SCOUT_HISTORY_PRUNE_TIME": settings.SCOUT_HISTORY_PRUNE_TIME,
        "SCOUT_MULTIPLIER": settings.SCOUT_MULTIPLIER,
        "SCOUT_SLEEP_TIME": settings.SCOUT_SLEEP_TIME,
        "USE_MARGIN": settings.USE_MARGIN,
        "SCOUT_MARGIN": settings.SCOUT_MARGIN,
        "BINANCE_API_KEY": settings.BINANCE_API_KEY,
        "BINANCE_API_SECRET_KEY": settings.BINANCE_API_SECRET_KEY,
        "WATCHLIST": settings.WATCHLIST or watchlist,
        "STRATEGY": settings.STRATEGY,
        "ENABLE_PAPER_TRADING": settings.ENABLE_PAPER_TRADING,
        "PAPER_WALLET_BALANCE": settings.PAPER_WALLET_BALANCE,
    }
)

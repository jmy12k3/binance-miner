import configparser
import os

from .models import Coin

CFG_SECTION = "project"

CFG = "config/user.cfg"
WATCHLIST = "config/watchlist.txt"


# XXX: Simplify the transformation of the config values
class Config:
    def __init__(self):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "bridge": "BUSD",
            "use_margin": "true",
            "scout_multiplier": "5",
            "scout_margin": "0.8",
            "scout_sleep_time": "1",
            "hourToKeepScoutHistory": "1",
            "strategy": "default",
            "enable_paper_trading": "true",
            "paper_wallet_balance": "10000",
        }

        # XXX: Notify user when the config could not be loaded
        if not os.path.exists(CFG):
            config[CFG_SECTION] = {}
        else:
            config.read(CFG)

        self.BRIDGE_SYMBOL = os.environ.get("BRIDGE_SYMBOL") or config.get(CFG_SECTION, "bridge")

        self.BRIDGE = Coin(self.BRIDGE_SYMBOL, False)

        self.SCOUT_HISTORY_PRUNE_TIME = float(
            os.environ.get("HOURS_TO_KEEP_SCOUTING_HISTORY")
            or config.get(CFG_SECTION, "hourToKeepScoutHistory")
        )

        self.SCOUT_MULTIPLIER = float(
            os.environ.get("SCOUT_MULTIPLIER") or config.get(CFG_SECTION, "scout_multiplier")
        )

        self.SCOUT_SLEEP_TIME = int(
            os.environ.get("SCOUT_SLEEP_TIME") or config.get(CFG_SECTION, "scout_sleep_time")
        )

        use_margin = os.environ.get("USE_MARGIN") or config.get(CFG_SECTION, "use_margin")
        self.USE_MARGIN = {"true": True, "false": False}.get(str(use_margin).lower())
        if self.USE_MARGIN is None:
            raise ValueError("use_margin parameter must be either 'true' or 'false'")

        self.SCOUT_MARGIN = os.environ.get("SCOUT_MARGIN") or config.get(
            CFG_SECTION, "scout_margin"
        )

        self.SCOUT_MARGIN = float(self.SCOUT_MARGIN)

        self.BINANCE_API_KEY = os.environ.get("API_KEY") or config.get(CFG_SECTION, "api_key")

        self.BINANCE_API_SECRET_KEY = os.environ.get("API_SECRET_KEY") or config.get(
            CFG_SECTION, "api_secret_key"
        )

        watchlist = [
            coin.strip() for coin in os.environ.get("WATCHLIST", "").split() if coin.strip()
        ]
        if not watchlist and os.path.exists(WATCHLIST):
            with open(WATCHLIST) as rfh:
                for line in rfh:
                    line = line.strip()
                    if not line or line.startswith("#") or line in watchlist:
                        continue
                    watchlist.append(line)
        self.WATCHLIST = watchlist

        self.STRATEGY = os.environ.get("STRATEGY") or config.get(CFG_SECTION, "strategy")

        enable_paper_trading = os.environ.get("ENABLE_PAPER_TRADING") or config.get(
            CFG_SECTION, "enable_paper_trading"
        )
        self.ENABLE_PAPER_TRADING = {"true": True, "false": False}.get(
            str(enable_paper_trading).lower()
        )
        if self.ENABLE_PAPER_TRADING is None:
            raise ValueError("enable_paper_trading parameter must be either 'true' or 'false'")

        self.PAPER_BALANCE = float(
            os.environ.get("PAPER_BALANCE") or config.get(CFG_SECTION, "paper_wallet_balance")
        )

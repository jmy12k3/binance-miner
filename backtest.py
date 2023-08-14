from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from project import backtest
from project.backtesting import show_spinner

if __name__ == "__main__":
    equity = np.array([])
    start_date = datetime.now() - relativedelta(years=1)
    with show_spinner(text="Backtesting") as sp:
        for manager in backtest(sp, datetime(start_date.year, start_date.month, start_date.day)):
            bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
            btc_value = manager.collate_coins("BTC")
            equity = np.append(equity, [manager.datetime, bridge_value, btc_value])
    equity_curve = pd.DataFrame(equity, columns=["datetime", "bridge_value", "btc_value"])
    equity_curve.to_csv("data/equity_curve.csv")

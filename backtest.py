from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

from project import backtest

if __name__ == "__main__":
    history = []
    start_date = datetime.now() - relativedelta(years=1)
    for manager in backtest(datetime(start_date.year, start_date.month, start_date.day)):
        btc_value = manager.collate_coins("BTC")
        bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
        history.append([manager.datetime, bridge_value, btc_value])
    df = pd.DataFrame(history, columns=["datetime", "bridge_value", "btc_value"])
    df.to_csv("data/backtest.csv")

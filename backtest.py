from datetime import datetime

import pandas as pd
import pytz
import quantstats as qs
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from tzlocal import get_localzone

from crypto_miner import Config, backtest


def main():
    # Initialize dataframe placeholder
    df = []

    # Initialize config
    config = Config()

    # Set start and end date
    end_date = datetime.utcnow() - relativedelta(minutes=1)
    start_date = end_date - relativedelta(months=1)
    start_date = datetime(start_date.year, start_date.month, start_date.day)
    total = round((end_date - start_date).total_seconds() / 60 * 0.99)

    # Initiate backtest
    for manager in tqdm(
        backtest(start_date, end_date), desc="Backtesting", total=total, ascii="░▒█", delay=1
    ):
        returns = manager.collate_coins(config.BRIDGE.symbol)
        benchmark = manager.get_ticker_price("BTC" + config.BRIDGE.symbol)
        df.append((manager.datetime, returns, benchmark))

    # Cast placeholder into dataframe
    df = pd.DataFrame(df, columns=["Date", "returns", "benchmark"]).set_index("Date")
    df.index = df.index.tz_localize(utc).tz_convert(get_localzone()).tz_localize(None)

    # Forward-filling missing values
    missing_rows = df.isnull().any(axis=1)
    total = missing_rows.sum()
    if total > 0:
        index = df.index
        df = df.reset_index().drop(columns=["Date"])
        for i, _ in tqdm(
            df[missing_rows].iterrows(), desc="Validating", total=total, ascii="░▒█", leave=True
        ):
            if i == df.index[0]:
                continue
            last_row = df.loc[i - 1]
            if last_row.isnull().any():
                continue
            df.loc[i] = last_row
        df.set_index(index, inplace=True)

    # Aggregate dataframe into daily timeframe and generate report
    returns = df.returns.pct_change().resample("D").sum()
    benchmark = df.benchmark.pct_change().resample("D").sum()
    qs.reports.html(
        returns,
        benchmark,
        periods_per_year=365,
        output="data/reports.html",
    )


if __name__ == "__main__":
    main()

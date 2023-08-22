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
    start_date = end_date - relativedelta(years=1)
    start_date = datetime(start_date.year, start_date.month, start_date.day)
    total = ((end_date - start_date).total_seconds()) // 60

    # Initiate backtest
    for manager in (
        pbar := tqdm(
            backtest(start_date, end_date),
            desc="Backtesting",
            total=total,
            ascii="░▒█",
            miniters=1,
            bar_format="{desc:<10}:{percentage:3.0f}%|{bar:20}{r_bar}",
            delay=1,
        )
    ):
        returns = manager.collate_coins(config.BRIDGE.symbol)
        benchmark = manager.get_ticker_price("BTC" + config.BRIDGE.symbol)
        df.append((manager.datetime, returns, benchmark))

    # Cast placeholder into dataframe
    df = pd.DataFrame(df, columns=["Date", "returns", "benchmark"]).set_index("Date")

    # Convert UTC to local timezone
    index = df.index.tz_localize(pytz.UTC).tz_convert(get_localzone()).tz_localize(None)
    df = df.reset_index().drop(columns=["Date"])

    # Forward-filling missing values
    missing_rows = df.isnull().any(axis=1)
    total = missing_rows.sum()
    if total > 0:
        for i, _ in df[missing_rows].iterrows():
            if i == df.index[0]:
                continue
            last_row = df.loc[i - 1]
            if last_row.isnull().any():
                continue
            df.loc[i] = last_row
    df.set_index(index, inplace=True)

    # Aggregate dataframe into daily timeframe and generate report
    returns = df.returns.pct_change().asfreq("D")
    benchmark = df.benchmark.pct_change().asfreq("D")
    qs.reports.html(
        returns,
        benchmark,
        periods_per_year=365,
        output="data/reports.html",
    )


if __name__ == "__main__":
    main()

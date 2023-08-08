from datetime import datetime

from project import backtest

if __name__ == "__main__":
    history = []
    # XXX: Improve the backtesting UI
    for manager in backtest(datetime(2023, 1, 1)):
        btc_value = manager.collate_coins("BTC")
        bridge_value = manager.collate_coins(manager.config.BRIDGE.symbol)
        history.append((btc_value, bridge_value))
        btc_diff = (btc_value - history[0][0]) / history[0][0] * 100
        bridge_diff = (bridge_value - history[0][1]) / history[0][1] * 100
        print("\u2500" * 100)
        print("TIME:", manager.datetime)
        print("BALANCES:", manager.balances)
        print(f"BTC VALUE: {btc_value:.5f} ({btc_diff:.2f}%)")
        print(f"{manager.config.BRIDGE.symbol} VALUE: {bridge_value:.5f} ({bridge_diff:.2f}%)")
        print("\u2500" * 100)

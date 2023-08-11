from project.autotrader import AutoTrader
from project.ratios import CoinStub


class Strategy(AutoTrader):
    # XXX: Improve logging semantics
    def scout(self):
        for coin in CoinStub.get_all():
            current_coin_balance = self.manager.get_currency_balance(coin.symbol)
            coin_price, quote_amount = self.manager.get_market_sell_price(
                coin.symbol + self.config.BRIDGE.symbol, current_coin_balance
            )
            if coin_price is None:
                self.logger.info(
                    f"Skipping scouting... current coin {coin.symbol + self.config.BRIDGE.symbol} n"
                    "ot found"
                )
                continue
            min_notional = self.manager.get_min_notional(coin.symbol, self.config.BRIDGE.symbol)
            if coin_price * current_coin_balance < min_notional:
                continue
            self._jump_to_best_coin(coin, coin_price, quote_amount, current_coin_balance)
        self.bridge_scout()

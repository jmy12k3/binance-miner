# Strategies

Minimal working example

```python
from binance_miner.autotrader import AutoTrader


class Strategy(AutoTrader):
    def scout(self):
        ...
```
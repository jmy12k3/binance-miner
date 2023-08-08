# Strategies

```python
from project.autotrader import AutoTrader


class Strategy(AutoTrader):
    def initialize(self):
        # Required initialization
        super().initialize()
        
        # Optional initialization
        self.initialize_current_coin()
    
    # Required overridden method
    def scout(self):
        ...

    # Optional initialization
    def initialize_current_coin(self):
        ...
    
    # Optional overridden method
    def my_overridden_method(self):
        ...
    
    # Optional new method
    def my_new_method(self):
        ...
```
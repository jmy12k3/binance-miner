import importlib
import os


def get_strategy(name):
    for dirpath, _, filenames in os.walk(os.path.dirname(__file__)):
        for strategy in filenames:
            if not (strategy.endswith(".py") and strategy.replace(".py", "") == name):
                continue
            location = os.path.join(dirpath, strategy)
            spec = importlib.util.spec_from_file_location(name, location)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.Strategy
    return None

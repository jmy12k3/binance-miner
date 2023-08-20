import importlib.util
import os


def get_strategy(name: str) -> type | None:
    for dirpath, _, filenames in os.walk(os.path.dirname(__file__)):
        for strategy in filenames:
            if not (strategy.replace(name, "") == ".py" and strategy.endswith(".py")):
                continue
            location = os.path.join(dirpath, strategy)
            spec = importlib.util.spec_from_file_location(name, location)
            if spec is not None:
                module = importlib.util.module_from_spec(spec)
                if module is not None and spec.loader is not None:
                    spec.loader.exec_module(module)
                    return module.Strategy
    return None

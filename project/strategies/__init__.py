import importlib.util
import os
from collections.abc import Callable
from typing import TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


def get_strategy(name: str) -> Callable[P, T] | None:
    for dirpath, _, filenames in os.walk(os.path.dirname(__file__)):
        for strategy in filenames:
            if not (strategy.startswith(name) and strategy.endswith(".py")):
                continue
            location = os.path.join(dirpath, strategy)
            spec = importlib.util.spec_from_file_location(name, location)
            module = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(module)  # type: ignore
            return module.Strategy
    return None

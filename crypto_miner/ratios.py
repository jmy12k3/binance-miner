# https://docs.sqlalchemy.org/en/20/orm/extensions/mypy.html
# mypy: disable-error-code=call-overload
from __future__ import annotations

from array import array
from collections.abc import Iterable, KeysView
from math import nan

from .models import Pair


class CoinStub:
    _instances: list[CoinStub] = []
    _instances_by_symbol: dict[str, CoinStub] = {}

    def __init__(self, ratio_idx: int, symbol: str):
        self.idx = ratio_idx
        self.symbol = symbol

    def __repr__(self):
        return f"CoinStub({self.idx}, {self.symbol})"

    @classmethod
    def create(cls: type[CoinStub], symbol: str) -> CoinStub:
        idx = len(cls._instances)
        new_instance = cls(idx, symbol)
        cls._instances.append(new_instance)
        cls._instances_by_symbol[symbol] = new_instance
        return new_instance

    @classmethod
    def get_by_idx(cls: type[CoinStub], idx: int) -> CoinStub:
        return cls._instances[idx]

    @classmethod
    def get_by_symbol(cls: type[CoinStub], symbol: str) -> CoinStub:
        return cls._instances_by_symbol.get(symbol, None)  # type: ignore

    @classmethod
    def reset(cls: type[CoinStub]):
        cls._instances.clear()
        cls._instances_by_symbol.clear()

    @classmethod
    def len_coins(cls: type[CoinStub]) -> int:
        return len(cls._instances)

    @classmethod
    def get_all(cls: type[CoinStub]) -> list[CoinStub]:
        return cls._instances


class RatiosManager:
    def __init__(self, ratios: Iterable[Pair] | None = None):
        self.n = CoinStub.len_coins()
        self._data = array(
            "d", (nan if i != j else 1.0 for i in range(self.n) for j in range(self.n))
        )
        self._dirty: dict[tuple[int, int], float] = {}
        self._ids: array | None = None
        if ratios is not None:
            self._ids = array("Q", (0 for _ in range(self.n * self.n)))
            for pair in ratios:
                i = CoinStub.get_by_symbol(pair.from_coin.symbol).idx
                j = CoinStub.get_by_symbol(pair.to_coin.symbol).idx
                val = pair.ratio if pair.ratio is not None else nan
                pair_id = pair.id if pair.id is not None else 0
                idx = self.n * i + j
                self._data[idx] = val
                self._ids[idx] = pair_id

    def set(self, from_coin_idx: int, to_coin_idx: int, val: float):
        cell = (from_coin_idx, to_coin_idx)
        if cell not in self._dirty:
            self._dirty[cell] = self._data[self.n * cell[0] + cell[1]]
        self._data[self.n * cell[0] + cell[1]] = val

    def get(self, from_coin_idx: int, to_coin_idx: int) -> float:
        return self._data[self.n * from_coin_idx + to_coin_idx]

    def get_from_coin(self, from_coin_idx: int):
        return self._data[self.n * from_coin_idx : self.n * (from_coin_idx + 1)]

    def get_to_coin(self, to_coin_idx: int):
        return self._data[to_coin_idx :: self.n]

    def get_dirty(self) -> KeysView[tuple[int, int]]:
        return self._dirty.keys()

    def get_pair_id(self, from_coin_idx: int, to_coin_idx: int) -> int:
        return self._ids[from_coin_idx * self.n + to_coin_idx]  # type: ignore

    def rollback(self):
        for cell, old_value in self._dirty.items():
            self._data[self.n * cell[0] + cell[1]] = old_value
        self._dirty.clear()

    def commit(self):
        self._dirty.clear()

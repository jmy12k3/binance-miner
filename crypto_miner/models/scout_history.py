# https://docs.sqlalchemy.org/en/20/orm/extensions/mypy.html
# mypy: disable-error-code=assignment
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Base


class ScoutHistory(Base):
    __tablename__ = "scout_history"
    id = Column(Integer, primary_key=True)
    pair_id = Column(String, ForeignKey("pairs.id"))
    pair = relationship("Pair", foreign_keys=[pair_id], lazy="joined")
    ratio_diff = Column(Float)
    target_ratio = Column(Float)
    current_coin_price = Column(Float)
    other_coin_price = Column(Float)
    dt = Column(DateTime)

    def __init__(
        self,
        pair_id: str,
        ratio_diff: float,
        target_ratio: float,
        current_coin_price: float,
        other_coin_price: float,
        dt: datetime | None = None,
    ):
        self.pair_id = pair_id
        self.ratio_diff = ratio_diff
        self.target_ratio = target_ratio
        self.current_coin_price = current_coin_price
        self.other_coin_price = other_coin_price
        self.dt = dt or datetime.utcnow()

    @hybrid_property
    def current_ratio(self):
        return self.current_coin_price / self.other_coin_price

    def info(self):
        return {
            "from_coin": self.pair.from_coin.info(),
            "to_coin": self.pair.to_coin.info(),
            "ratio_diff": self.ratio_diff,
            "current_ratio": self.current_ratio,
            "target_ratio": self.target_ratio,
            "current_coin_price": self.current_coin_price,
            "other_coin_price": self.other_coin_price,
            "datetime": self.dt.isoformat(),
        }

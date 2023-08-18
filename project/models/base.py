from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import declarative_base


class Base:
    __allow_unmapped__ = True


class Model(Protocol):
    def info(self):
        ...


class DatetimeModel(Model):
    datetime: datetime


Base = declarative_base(cls=Base)  # type: ignore

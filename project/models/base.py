from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import declarative_base


class Base:
    __allow_unmapped__ = True


class Model(Protocol):
    __tablename__: str

    def info(self):
        ...


class DTModel(Model):
    datetime: datetime


Base = declarative_base(cls=Base)  # type: ignore

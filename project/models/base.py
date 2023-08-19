from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import declarative_base


class DeclarativeBase:
    __allow_unmapped__ = True


class Model(Protocol):
    __tablename__: str
    datetime: datetime

    def info(self):
        ...


Base = declarative_base(cls=DeclarativeBase)

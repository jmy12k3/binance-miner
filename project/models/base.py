from typing import Protocol

from sqlalchemy.orm import declarative_base


class Base:
    __allow_unmapped__ = True


class Info(Protocol):
    def info(self):
        ...


Base = declarative_base(cls=Base)  # type: ignore

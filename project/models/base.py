from sqlalchemy.orm import declarative_base


class Base:
    __allow_unmapped__ = True


Base = declarative_base(cls=Base)

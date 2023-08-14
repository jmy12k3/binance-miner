from sqlalchemy.orm import declarative_base


class cls:
    __allow_unmapped__ = True


Base = declarative_base(cls=cls)

from sqlalchemy import Column, BigInteger, Text

from database.base import SqlAlchemyBase


class Manufacture(SqlAlchemyBase):
    __tablename__ = "manufacture"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"name={self.name}"
            f")>"
        )
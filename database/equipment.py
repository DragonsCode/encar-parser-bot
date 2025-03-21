from sqlalchemy import Column, BigInteger, Text, ForeignKey

from database.base import SqlAlchemyBase


class Equipment(SqlAlchemyBase):
    __tablename__ = "equipment"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    series_id = Column(BigInteger, ForeignKey("series.id"))
    name = Column(Text, nullable=False)
    translated = Column(Text, nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"series_id={self.series_id}, "
            f"name={self.name}, "
            f"translated={self.translated}"
            f")>"
        )
from sqlalchemy import Column, BigInteger, Text, ForeignKey

from database.base import SqlAlchemyBase


class Series(SqlAlchemyBase):
    __tablename__ = "series"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    models_id = Column(BigInteger, ForeignKey("models.id"))
    name = Column(Text, nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"models_id={self.models_id}, "
            f"name={self.name}"
            f")>"
        )
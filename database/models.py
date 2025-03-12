from sqlalchemy import Column, BigInteger, Text, ForeignKey

from database.base import SqlAlchemyBase


class Models(SqlAlchemyBase):
    __tablename__ = "models"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    manufacture_id = Column(BigInteger, ForeignKey("manufacture.id"))
    name = Column(Text, nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"manufacture_id={self.manufacture_id}, "
            f"name={self.name}"
            f")>"
        )
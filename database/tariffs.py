from sqlalchemy import Column, BigInteger, DateTime, Text, Integer, Float
from datetime import datetime

from database.base import SqlAlchemyBase


class Tariffs(SqlAlchemyBase):
    __tablename__ = "tariffs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, default=None)
    description = Column(Text, default=None)
    days_count = Column(Integer, default=None)
    price = Column(Float, default=None)
    filters_count = Column(Integer, default=None)
    create_dttm = Column(DateTime, default=datetime.now)
    update_dttm = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"name={self.name}, "
            f"description={self.description}, "
            f"days_count={self.days_count}, "
            f"price={self.price}, "
            f"filters_count={self.filters_count}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )

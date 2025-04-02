from sqlalchemy import Column, BigInteger, ForeignKey, DateTime
from datetime import datetime
from database.base import SqlAlchemyBase

class ViewedCars(SqlAlchemyBase):
    __tablename__ = "viewed_cars"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    filter_id = Column(BigInteger, ForeignKey("filters.id"))
    car_id = Column(BigInteger)
    viewed_dttm = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"filter_id={self.filter_id}, "
            f"car_id={self.car_id}, "
            f"viewed_dttm={self.viewed_dttm}"
            f")>"
        )
from sqlalchemy import Column, BigInteger, DateTime, ForeignKey
from datetime import datetime

from database.base import SqlAlchemyBase


class Subscription(SqlAlchemyBase):
    __tablename__ = "subscription"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    tariff_id = Column(BigInteger, ForeignKey("tariffs.id"))
    subscription_end = Column(DateTime, default=None)
    create_dttm = Column(DateTime, default=datetime.now)
    update_dttm = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return f'{self.user_id}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"tariff_id={self.tariff_id}, "
            f"subscription_end={self.subscription_end}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )

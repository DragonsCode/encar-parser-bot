from sqlalchemy import Column, BigInteger, Integer, Text, DateTime
from datetime import datetime

from database.base import SqlAlchemyBase


class Users(SqlAlchemyBase):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(Text, default=None)
    first_name = Column(Text, default=None)
    create_dttm = Column(DateTime, default=datetime.now)
    update_dttm = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"username={self.username}, "
            f"first_name={self.first_name}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )

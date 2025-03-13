from sqlalchemy import Column, BigInteger, DateTime, Integer, Text
from datetime import datetime

from database.base import SqlAlchemyBase


class Contacts(SqlAlchemyBase):
    __tablename__ = "contacts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, default=None)
    url = Column(Text, default=None)
    sequence_number = Column(Integer, default=None)
    create_dttm = Column(DateTime, default=datetime.now)
    update_dttm = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return f'{self.title}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"title={self.title}, "
            f"url={self.url}, "
            f"sequence_number={self.sequence_number}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )

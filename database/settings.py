from sqlalchemy import Column, DateTime, Text, BigInteger, String
from datetime import datetime

from database.base import SqlAlchemyBase


class Settings(SqlAlchemyBase):
    __tablename__ = "settings"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True)
    name = Column(Text, default=None)
    description = Column(Text, default=None)
    value = Column(Text, default=None)
    create_dttm = Column(DateTime, default=datetime.now)
    update_dttm = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __str__(self):
        return f'{self.user_id}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"key={self.key}, "
            f"name={self.name}, "
            f"description={self.description}, "
            f"value={self.value}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )

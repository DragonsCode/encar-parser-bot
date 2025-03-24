from sqlalchemy import Column, BigInteger, Integer, DateTime, ForeignKey
from datetime import datetime

from database.base import SqlAlchemyBase


class Filters(SqlAlchemyBase):
    __tablename__ = "filters"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    manufacture_id = Column(BigInteger, ForeignKey("manufacture.id"), default=None)
    model_id = Column(BigInteger, ForeignKey("models.id"), default=None)
    series_id = Column(BigInteger, ForeignKey("series.id"), default=None)
    equipment_id = Column(BigInteger, ForeignKey("equipment.id"), default=None)
    engine_type_id = Column(BigInteger, ForeignKey("engine_type.id"), default=None)
    # drive_type_id = Column(BigInteger, ForeignKey("drive_type.id"), default=None)
    car_color_id = Column(BigInteger, ForeignKey("car_color.id"), default=None)
    mileage_from = Column(Integer, default=None)
    mileage_defore = Column(Integer, default=None)
    price_from = Column(Integer, default=None)
    price_defore = Column(Integer, default=None)
    date_release_from = Column(DateTime, default=None)
    date_release_defore = Column(DateTime, default=None)
    create_dttm = Column(DateTime, default=datetime.now)
    update_dttm = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"manufacture_id={self.manufacture_id}, "
            f"model_id={self.model_id}, "
            f"series_id={self.series_id}, "
            f"equipment_id={self.equipment_id}, "
            f"engine_type_id={self.engine_type_id}, "
            # f"drive_type_id={self.drive_type_id}, "
            f"car_color_id={self.car_color_id}, "
            f"mileage_from={self.mileage_from}, "
            f"mileage_defore={self.mileage_defore}, "
            f"price_from={self.price_from}, "
            f"price_defore={self.price_defore}, "
            f"date_release_from={self.date_release_from}, "
            f"date_release_defore={self.date_release_defore}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )
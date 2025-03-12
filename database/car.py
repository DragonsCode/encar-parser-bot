from sqlalchemy import Column, BigInteger, Integer, Text, DateTime, ForeignKey, Float
from datetime import datetime

from database.base import SqlAlchemyBase


class Car(SqlAlchemyBase):
    __tablename__ = "car"
    id = Column(BigInteger, primary_key=True)
    manufacture_id = Column(BigInteger, ForeignKey("manufacture.id"))
    model_id = Column(BigInteger, ForeignKey("models.id"))
    series_id = Column(BigInteger, ForeignKey("series.id"))
    equipment_id = Column(BigInteger, ForeignKey("equipment.id"))
    engine_type_id = Column(BigInteger, ForeignKey("engine_type.id"))
    drive_type_id = Column(BigInteger, ForeignKey("drive_type.id"))
    car_color_id = Column(BigInteger, ForeignKey("car_color.id"))
    mileage = Column(Integer, default=None)
    price_won = Column(Integer, default=None)
    price_rub = Column(Integer, default=None)
    date_release = Column(DateTime, default=None)
    publication_dttm = Column(DateTime, default=None)
    check_dttm = Column(DateTime, default=None)
    change_ownership = Column(Integer, default=None)
    all_traffic_accident = Column(Integer, default=None)
    traffic_accident_owner = Column(Integer, default=None)
    traffic_accident_other = Column(Integer, default=None)
    repair_cost_owner = Column(Float, default=None)
    repair_cost_other = Column(Float, default=None)
    theft = Column(Integer, default=None)
    flood = Column(Integer, default=None)
    death = Column(Integer, default=None)
    url = Column(Text, default=None)
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
            f"drive_type_id={self.drive_type_id}, "
            f"car_color_id={self.car_color_id}, "
            f"mileage={self.mileage}, "
            f"price_won={self.price_won}, "
            f"price_rub={self.price_rub}, "
            f"date_release={self.date_release}, "
            f"publication_dttm={self.publication_dttm}, "
            f"check_dttm={self.check_dttm}, "
            f"change_ownership={self.change_ownership}, "
            f"all_traffic_accident={self.all_traffic_accident}, "
            f"traffic_accident_owner={self.traffic_accident_owner}, "
            f"traffic_accident_other={self.traffic_accident_other}, "
            f"repair_cost_owner={self.repair_cost_owner}, "
            f"repair_cost_other={self.repair_cost_other}, "
            f"theft={self.theft}, "
            f"flood={self.flood}, "
            f"death={self.death}, "
            f"url={self.url}, "
            f"create_dttm={self.create_dttm}, "
            f"update_dttm={self.update_dttm}"
            f")>"
        )
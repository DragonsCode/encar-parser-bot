from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy import func

from database.base_db_api import BaseDBApi
from database.car import Car
from database.car_color import CarColor
from database.manufacture import Manufacture
from database.models import Models
from database.series import Series
from database.equipment import Equipment
from database.engine_type import EngineType
from database.drive_type import DriveType
from database.users import Users
from database.filters import Filters
from database.subscription import Subscription
from database.tariffs import Tariffs
from database.payhistory import PayHistory
from database.contacts import Contacts
from database.settings import Settings


class DBApi(BaseDBApi):
    # Методы для таблицы Car
    async def create_car(self, **kwargs) -> Car:
        """Создает новую запись в таблице Car."""
        car = Car(**kwargs)
        self._sess.add(car)
        await self._sess.commit()
        return car
    
    async def get_all_car_ids(self):
        """Получает все ID автомобилей."""
        result = await self._sess.execute(select(Car.id))  # Предполагается, что модель называется Car
        return [row[0] for row in result.fetchall()]

    async def get_car_by_id(self, car_id: int) -> Car:
        """Получает автомобиль по ID."""
        result = await self._sess.execute(select(Car).where(Car.id == car_id))
        return result.scalars().first()

    async def update_car(self, car_id: int, **kwargs) -> Car:
        """Обновляет данные автомобиля по ID."""
        car = await self.get_car_by_id(car_id)
        if car:
            for key, value in kwargs.items():
                if hasattr(car, key):
                    setattr(car, key, value)
            await self._sess.commit()
            return car
        print(f"Автомобиль с id={car_id} не найден")
        return None

    async def delete_car(self, car_id: int) -> bool:
        """Удаляет автомобиль по ID."""
        car = await self.get_car_by_id(car_id)
        if car:
            await self._sess.delete(car)
            await self._sess.commit()
            return True
        print(f"Автомобиль с id={car_id} не найден")
        return False

    # Методы для таблицы CarColor
    async def create_car_color(self, name: str) -> CarColor:
        """Создает новый цвет автомобиля."""
        color = CarColor(name=name)
        self._sess.add(color)
        await self._sess.commit()
        return color

    async def get_car_color_by_name(self, name: str) -> CarColor:
        """Получает цвет автомобиля по названию."""
        result = await self._sess.execute(select(CarColor).where(CarColor.name == name))
        return result.scalars().first()

    async def get_all_car_colors(self) -> list[CarColor]:
        """Получает все цвета автомобилей."""
        result = await self._sess.execute(select(CarColor))
        return result.scalars().all()

    # Методы для таблицы Manufacture
    async def create_manufacture(self, name: str) -> Manufacture:
        """Создает нового производителя."""
        manufacture = Manufacture(name=name)
        self._sess.add(manufacture)
        await self._sess.commit()
        return manufacture

    async def get_manufacture_by_name(self, name: str) -> Manufacture:
        """Получает производителя по названию."""
        result = await self._sess.execute(select(Manufacture).where(Manufacture.name == name))
        return result.scalars().first()

    async def get_all_manufactures(self) -> list[Manufacture]:
        """Получает всех производителей."""
        result = await self._sess.execute(select(Manufacture))
        return result.scalars().all()

    # Методы для таблицы Models
    async def create_model(self, manufacture_id: int, name: str) -> Models:
        """Создает новую модель автомобиля."""
        model = Models(manufacture_id=manufacture_id, name=name)
        self._sess.add(model)
        await self._sess.commit()
        return model

    async def get_model_by_name(self, name: str) -> Models:
        """Получает модель по названию."""
        result = await self._sess.execute(select(Models).where(Models.name == name))
        return result.scalars().first()

    async def get_models_by_manufacture(self, manufacture_id: int) -> list[Models]:
        """Получает все модели по ID производителя."""
        result = await self._sess.execute(select(Models).where(Models.manufacture_id == manufacture_id))
        return result.scalars().all()

    # Методы для таблицы Series
    async def create_series(self, models_id: int, name: str) -> Series:
        """Создает новую серию модели."""
        series = Series(models_id=models_id, name=name)
        self._sess.add(series)
        await self._sess.commit()
        return series

    async def get_series_by_name(self, name: str) -> Series:
        """Получает серию по названию."""
        result = await self._sess.execute(select(Series).where(Series.name == name))
        return result.scalars().first()

    async def get_series_by_model(self, models_id: int) -> list[Series]:
        """Получает все серии по ID модели."""
        result = await self._sess.execute(select(Series).where(Series.models_id == models_id))
        return result.scalars().all()

    # Методы для таблицы Equipment
    async def create_equipment(self, series_id: int, name: str) -> Equipment:
        """Создает новую комплектацию."""
        equipment = Equipment(series_id=series_id, name=name)
        self._sess.add(equipment)
        await self._sess.commit()
        return equipment

    async def get_equipment_by_name(self, name: str) -> Equipment:
        """Получает комплектацию по названию."""
        result = await self._sess.execute(select(Equipment).where(Equipment.name == name))
        return result.scalars().first()

    async def get_equipment_by_series(self, series_id: int) -> list[Equipment]:
        """Получает все комплектации по ID серии."""
        result = await self._sess.execute(select(Equipment).where(Equipment.series_id == series_id))
        return result.scalars().all()

    # Методы для таблицы EngineType
    async def create_engine_type(self, name: str) -> EngineType:
        """Создает новый тип двигателя."""
        engine_type = EngineType(name=name)
        self._sess.add(engine_type)
        await self._sess.commit()
        return engine_type

    async def get_engine_type_by_name(self, name: str) -> EngineType:
        """Получает тип двигателя по названию."""
        result = await self._sess.execute(select(EngineType).where(EngineType.name == name))
        return result.scalars().first()

    async def get_all_engine_types(self) -> list[EngineType]:
        """Получает все типы двигателей."""
        result = await self._sess.execute(select(EngineType))
        return result.scalars().all()

    # Методы для таблицы DriveType (предполагается, что это drive_type)
    async def create_drive_type(self, name: str) -> DriveType:
        """Создает новый тип привода."""
        drive_type = DriveType(name=name)
        self._sess.add(drive_type)
        await self._sess.commit()
        return drive_type

    async def get_drive_type_by_name(self, name: str) -> DriveType:
        """Получает тип привода по названию."""
        result = await self._sess.execute(select(DriveType).where(DriveType.name == name))
        return result.scalars().first()

    async def get_all_drive_types(self) -> list[DriveType]:
        """Получает все типы приводов."""
        result = await self._sess.execute(select(DriveType))
        return result.scalars().all()

    # Методы для таблицы Users
    async def create_user(self, id: int, username: str = None, first_name: str = None) -> Users:
        """Создает нового пользователя."""
        user = await self.get_user_by_id(id)
        if user:
            return user
        user = Users(id=id, username=username, first_name=first_name)
        self._sess.add(user)
        await self._sess.commit()
        return user

    async def get_user_by_id(self, user_id: int) -> Users:
        """Получает пользователя по ID."""
        result = await self._sess.execute(select(Users).where(Users.id == user_id))
        return result.scalars().first()

    async def get_all_users(self) -> list[Users]:
        """Получает всех пользователей."""
        result = await self._sess.execute(select(Users))
        return result.scalars().all()

    # Методы для таблицы Filters
    async def create_filter(self, user_id: int, **kwargs) -> Filters:
        """Создает новый фильтр для пользователя."""
        filter = Filters(user_id=user_id, **kwargs)
        self._sess.add(filter)
        await self._sess.commit()
        return filter
    
    async def get_filter_by_id(self, filter_id: int):
        result = await self._sess.execute(select(Filters).where(Filters.id == filter_id))
        return result.scalars().first()

    async def get_filters_by_user(self, user_id: int) -> list[Filters]:
        """Получает все фильтры пользователя."""
        result = await self._sess.execute(select(Filters).where(Filters.user_id == user_id))
        return result.scalars().all()
    
    async def get_filters_count_by_user(self, user_id: int):
        result = await self._sess.execute(select(func.count(Filters.id)).where(Filters.user_id == user_id))
        return result.scalar()
    
    async def delete_filter(self, filter_id: int):
        filter_obj = await self.get_filter_by_id(filter_id)
        if filter_obj:
            await self._sess.delete(filter_obj)
            await self._sess.commit()
            return True
        return False

    # Методы для таблицы Subscription
    async def create_subscription(self, user_id: int, tariff_id: int, subscription_end: datetime) -> Subscription:
        """Создает новую подписку."""
        subscription = Subscription(user_id=user_id, tariff_id=tariff_id, subscription_end=subscription_end)
        self._sess.add(subscription)
        await self._sess.commit()
        return subscription
    
    async def edit_subscription(self, id: int, tariff_id: int = None, subscription_end: datetime = None):
        sub = await self._sess.execute(select(Subscription).where(Subscription.id == id))
        sub_obj = sub.scalars().first()
        if sub_obj:
            if tariff_id:
                sub_obj.tariff_id = tariff_id
            if subscription_end:
                sub_obj.subscription_end = subscription_end
            await self._sess.commit()
            return sub_obj
        return None

    async def get_subscription_by_user(self, user_id: int) -> Subscription:
        """Получает подписку пользователя."""
        result = await self._sess.execute(select(Subscription).where(Subscription.user_id == user_id))
        return result.scalars().first()
    
    async def get_expiring_subscriptions(self, start_time: datetime, end_time: datetime) -> list[Subscription]:
        """Получает подписки, истекающие в заданном временном интервале."""
        query = select(Subscription).where(
            Subscription.subscription_end.between(start_time, end_time)
        )
        result = await self._sess.execute(query)
        return result.scalars().all()
    
    async def get_subscription_by_id(self, sub_id: int):
        result = await self._sess.execute(select(Subscription).where(Subscription.id == sub_id))
        return result.scalars().first()

    async def delete_subscription(self, sub_id: int):
        sub = await self.get_subscription_by_id(sub_id)
        if sub:
            await self._sess.delete(sub)
            await self._sess.commit()
            return True
        return False

    # Методы для таблицы Tariffs
    async def create_tariff(self, name: str, description: str, days_count: int, price: float, filters_count: int) -> Tariffs:
        """Создает новый тариф."""
        tariff = Tariffs(name=name, description=description, days_count=days_count, price=price, filters_count=filters_count)
        self._sess.add(tariff)
        await self._sess.commit()
        return tariff

    async def get_tariff_by_id(self, tariff_id: int) -> Tariffs:
        """Получает тариф по ID."""
        result = await self._sess.execute(select(Tariffs).where(Tariffs.id == tariff_id))
        return result.scalars().first()

    async def get_all_tariffs(self) -> list[Tariffs]:
        """Получает все тарифы."""
        result = await self._sess.execute(select(Tariffs))
        return result.scalars().all()

    # Методы для таблицы PayHistory
    async def create_pay_history(self, user_id: int, tariff_id: int, price: float, successfully: bool) -> PayHistory:
        """Создает запись в истории платежей."""
        pay_history = PayHistory(user_id=user_id, tariff_id=tariff_id, price=price, successfully=successfully)
        self._sess.add(pay_history)
        await self._sess.commit()
        return pay_history
    
    async def edit_payhistory(self, id: int, successfully: bool = None):
        pay = await self._sess.execute(select(PayHistory).where(PayHistory.id == id))
        pay_obj = pay.scalars().first()
        if pay_obj:
            if successfully is not None:
                pay_obj.successfully = successfully
            await self._sess.commit()
            return pay_obj
        return None

    async def get_pay_history_by_user(self, user_id: int) -> list[PayHistory]:
        """Получает историю платежей пользователя."""
        result = await self._sess.execute(select(PayHistory).where(PayHistory.user_id == user_id))
        return result.scalars().all()

    # Методы для таблицы Contacts
    async def create_contact(self, title: str, url: str, sequence_number: int) -> Contacts:
        """Создает новый контакт."""
        contact = Contacts(title=title, url=url, sequence_number=sequence_number)
        self._sess.add(contact)
        await self._sess.commit()
        return contact

    async def get_all_contacts(self) -> list[Contacts]:
        """Получает все контакты, отсортированные по sequence_number."""
        result = await self._sess.execute(select(Contacts).order_by(Contacts.sequence_number))
        return result.scalars().all()

    # Методы для таблицы Settings
    async def set_setting(self, key: str, value: str, name: str = None, description: str = None) -> Settings:
        """Создает или обновляет настройку по ключу."""
        setting = await self.get_setting_by_key(key)
        if setting:
            setting.value = value
            if name:
                setting.name = name
            if description:
                setting.description = description
        else:
            setting = Settings(key=key, value=value, name=name, description=description)
            self._sess.add(setting)
        await self._sess.commit()
        return setting

    async def get_setting_by_key(self, key: str) -> Settings:
        """Получает настройку по ключу."""
        result = await self._sess.execute(select(Settings).where(Settings.key == key))
        return result.scalars().first()

    async def get_all_settings(self) -> list[Settings]:
        """Получает все настройки."""
        result = await self._sess.execute(select(Settings))
        return result.scalars().all()
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
from database.viewed_cars import ViewedCars


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
    
    async def get_all_cars_query(self):
        # Возвращаем SQLAlchemy-запрос вместо списка
        return select(Car)
    
    async def get_all_cars(self):
        """Получает все автомобили."""
        result = await self._sess.execute(select(Car))
        return result.scalars().all()

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
    async def create_car_color(self, name: str, translated: str) -> CarColor:
        """Создает новый цвет автомобиля."""
        color = CarColor(name=name, translated=translated)
        self._sess.add(color)
        await self._sess.commit()
        return color
    
    async def get_car_color_by_id(self, color_id: int) -> CarColor:
        """Получает цвет автомобиля по ID."""
        result = await self._sess.execute(select(CarColor).where(CarColor.id == color_id))
        return result.scalars().first()

    async def get_car_color_by_name(self, name: str) -> CarColor:
        """Получает цвет автомобиля по названию."""
        result = await self._sess.execute(select(CarColor).where(CarColor.name == name))
        return result.scalars().first()
    
    async def get_car_color_by_translated(self, translated: str) -> CarColor:
        """Получает цвет автомобиля по переводу."""
        result = await self._sess.execute(select(CarColor).where(CarColor.translated == translated))
        return result.scalars().first()

    async def get_all_car_colors(self) -> list[CarColor]:
        """Получает все цвета автомобилей."""
        result = await self._sess.execute(select(CarColor))
        return result.scalars().all()

    # Методы для таблицы Manufacture
    async def create_manufacture(self, name: str, translated: str) -> Manufacture:
        """Создает нового производителя."""
        manufacture = Manufacture(name=name, translated=translated)
        self._sess.add(manufacture)
        await self._sess.commit()
        return manufacture
    
    async def get_manufacture_by_id(self, manufacture_id: int) -> Manufacture:
        """Получает производителя по ID."""
        result = await self._sess.execute(select(Manufacture).where(Manufacture.id == manufacture_id))
        return result.scalars().first()

    async def get_manufacture_by_name(self, name: str) -> Manufacture:
        """Получает производителя по названию."""
        result = await self._sess.execute(select(Manufacture).where(Manufacture.name == name))
        return result.scalars().first()
    
    async def get_manufacture_by_translated(self, translated: str) -> Manufacture:
        """Получает производителя по переводу."""
        result = await self._sess.execute(select(Manufacture).where(Manufacture.translated == translated))
        return result.scalars().first()

    async def get_all_manufactures(self) -> list[Manufacture]:
        """Получает всех производителей."""
        result = await self._sess.execute(select(Manufacture))
        return result.scalars().all()

    # Методы для таблицы Models
    async def create_model(self, manufacture_id: int, name: str, translated: str) -> Models:
        """Создает новую модель автомобиля."""
        model = Models(manufacture_id=manufacture_id, name=name, translated=translated)
        self._sess.add(model)
        await self._sess.commit()
        return model
    
    async def get_model_by_id(self, model_id: int) -> Models:
        """Получает модель по ID."""
        result = await self._sess.execute(select(Models).where(Models.id == model_id))
        return result.scalars().first()

    async def get_model_by_name(self, name: str) -> Models:
        """Получает модель по названию."""
        result = await self._sess.execute(select(Models).where(Models.name == name))
        return result.scalars().first()
    
    async def get_model_by_translated(self, translated: str) -> Models:
        """Получает модель по переводу."""
        result = await self._sess.execute(select(Models).where(Models.translated == translated))
        return result.scalars().first()

    async def get_models_by_manufacture(self, manufacture_id: int) -> list[Models]:
        """Получает все модели по ID производителя."""
        result = await self._sess.execute(select(Models).where(Models.manufacture_id == manufacture_id))
        return result.scalars().all()

    # Методы для таблицы Series
    async def create_series(self, models_id: int, name: str, translated: str) -> Series:
        """Создает новую серию модели."""
        series = Series(models_id=models_id, name=name, translated=translated)
        self._sess.add(series)
        await self._sess.commit()
        return series
    
    async def get_series_by_id(self, series_id: int) -> Series:
        """Получает серию по ID."""
        result = await self._sess.execute(select(Series).where(Series.id == series_id))
        return result.scalars().first()

    async def get_series_by_name(self, name: str) -> Series:
        """Получает серию по названию."""
        result = await self._sess.execute(select(Series).where(Series.name == name))
        return result.scalars().first()
    
    async def get_series_by_translated(self, translated: str) -> Series:
        """Получает серию по переводу."""
        result = await self._sess.execute(select(Series).where(Series.translated == translated))
        return result.scalars().first()

    async def get_series_by_model(self, models_id: int) -> list[Series]:
        """Получает все серии по ID модели."""
        result = await self._sess.execute(select(Series).where(Series.models_id == models_id))
        return result.scalars().all()

    # Методы для таблицы Equipment
    async def create_equipment(self, series_id: int, name: str, translated: str) -> Equipment:
        """Создает новую комплектацию."""
        equipment = Equipment(series_id=series_id, name=name, translated=translated)
        self._sess.add(equipment)
        await self._sess.commit()
        return equipment
    
    async def get_equipment_by_id(self, equipment_id: int) -> Equipment:
        """Получает комплектацию по ID."""
        result = await self._sess.execute(select(Equipment).where(Equipment.id == equipment_id))
        return result.scalars().first()

    async def get_equipment_by_name(self, name: str) -> Equipment:
        """Получает комплектацию по названию."""
        result = await self._sess.execute(select(Equipment).where(Equipment.name == name))
        return result.scalars().first()
    
    async def get_equipment_by_translated(self, translated: str) -> Equipment:
        """Получает комплектацию по переводу."""
        result = await self._sess.execute(select(Equipment).where(Equipment.translated == translated))
        return result.scalars().first()

    async def get_equipment_by_series(self, series_id: int) -> list[Equipment]:
        """Получает все комплектации по ID серии."""
        result = await self._sess.execute(select(Equipment).where(Equipment.series_id == series_id))
        return result.scalars().all()

    # Методы для таблицы EngineType
    async def create_engine_type(self, name: str, translated: str) -> EngineType:
        """Создает новый тип двигателя."""
        engine_type = EngineType(name=name, translated=translated)
        self._sess.add(engine_type)
        await self._sess.commit()
        return engine_type
    
    async def get_engine_type_by_id(self, engine_type_id: int) -> EngineType:
        """Получает тип двигателя по ID."""
        result = await self._sess.execute(select(EngineType).where(EngineType.id == engine_type_id))
        return result.scalars().first()

    async def get_engine_type_by_name(self, name: str) -> EngineType:
        """Получает тип двигателя по названию."""
        result = await self._sess.execute(select(EngineType).where(EngineType.name == name))
        return result.scalars().first()
    
    async def get_engine_type_by_translated(self, translated: str) -> EngineType:
        """Получает тип двигателя по переводу."""
        result = await self._sess.execute(select(EngineType).where(EngineType.translated == translated))
        return result.scalars().first()

    async def get_all_engine_types(self) -> list[EngineType]:
        """Получает все типы двигателей."""
        result = await self._sess.execute(select(EngineType))
        return result.scalars().all()

    # Методы для таблицы DriveType (предполагается, что это drive_type)
    async def create_drive_type(self, name: str, translated: str) -> DriveType:
        """Создает новый тип привода."""
        drive_type = DriveType(name=name, translated=translated)
        self._sess.add(drive_type)
        await self._sess.commit()
        return drive_type
    
    async def get_drive_type_by_id(self, drive_type_id: int) -> DriveType:
        """Получает тип привода по ID."""
        result = await self._sess.execute(select(DriveType).where(DriveType.id == drive_type_id))
        return result.scalars().first()

    async def get_drive_type_by_name(self, name: str) -> DriveType:
        """Получает тип привода по названию."""
        result = await self._sess.execute(select(DriveType).where(DriveType.name == name))
        return result.scalars().first()
    
    async def get_drive_type_by_translated(self, translated: str) -> DriveType:
        """Получает тип привода по переводу."""
        result = await self._sess.execute(select(DriveType).where(DriveType.translated == translated))
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
    
    async def get_all_users_query(self):
        return select(Users)

    async def update_user(self, user_id: int, **kwargs) -> Users:
        """Обновляет данные пользователя по ID."""
        user = await self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self._sess.commit()
            return user
        print(f"Пользователь с id={user_id} не найден")
        return None

    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя по ID."""
        user = await self.get_user_by_id(user_id)
        if user:
            await self._sess.delete(user)
            await self._sess.commit()
            return True
        print(f"Пользователь с id={user_id} не найден")
        return False

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
        result = await self._sess.execute(
            select(func.count(Filters.id))
            .where(Filters.user_id == user_id)
        )
        return result.scalar()
    
    async def get_filters_by_user_query(self, user_id: int):
        return select(Filters).where(Filters.user_id == user_id).order_by(Filters.create_dttm.asc())
    
    async def delete_filter(self, filter_id: int):
        filter_obj = await self.get_filter_by_id(filter_id)
        if filter_obj:
            await self._sess.delete(filter_obj)
            await self._sess.commit()
            return True
        return False
    
    async def get_all_filters(self) -> list[Filters]:
        """Получает все фильтры."""
        result = await self._sess.execute(select(Filters))
        return result.scalars().all()
    
    async def get_all_filters_query(self):
        return select(Filters)

    async def update_filter(self, filter_id: int, **kwargs) -> Filters:
        """Обновляет данные фильтра по ID."""
        filter_obj = await self.get_filter_by_id(filter_id)
        if filter_obj:
            for key, value in kwargs.items():
                if hasattr(filter_obj, key):
                    setattr(filter_obj, key, value)
            await self._sess.commit()
            return filter_obj
        print(f"Фильтр с id={filter_id} не найден")
        return None

    # Методы для таблицы Subscription
    async def create_subscription(self, user_id: int, tariff_id: int, subscription_end: datetime) -> Subscription:
        """Создает новую подписку."""
        subscription = Subscription(user_id=user_id, tariff_id=tariff_id, subscription_end=subscription_end)
        self._sess.add(subscription)
        await self._sess.commit()
        return subscription

    async def get_all_subscriptions(self) -> list[Subscription]:
        """Получает все подписки."""
        result = await self._sess.execute(select(Subscription))
        return result.scalars().all()
    
    async def get_all_subscriptions_query(self):
        return select(Subscription)

    async def get_subscription_by_user(self, user_id: int) -> Subscription:
        """Получает подписки пользователя."""
        result = await self._sess.execute(select(Subscription).where(Subscription.user_id == user_id))
        return result.scalars().all()
    
    async def get_subscription_by_user_query(self, user_id: int) -> Subscription:
        """Получает подписки пользователя."""
        return select(Subscription).where(Subscription.user_id == user_id)

    async def get_expiring_subscriptions(self, start_time: datetime, end_time: datetime) -> list[Subscription]:
        """Получает подписки, истекающие в заданном временном интервале."""
        query = select(Subscription).where(
            Subscription.subscription_end.between(start_time, end_time)
        )
        result = await self._sess.execute(query)
        return result.scalars().all()
    
    async def get_expiring_subscriptions_query(self, start_time: datetime, end_time: datetime):
        return select(Subscription).where(
            Subscription.subscription_end.between(start_time, end_time)
        )

    async def get_subscription_by_id(self, sub_id: int) -> Subscription:
        """Получает подписку по ID."""
        result = await self._sess.execute(select(Subscription).where(Subscription.id == sub_id))
        return result.scalars().first()
    
    async def get_active_subscription_by_user(self, user_id: int) -> Subscription | None:
        """Получает последнюю активную подписку пользователя."""
        now = datetime.now()
        result = await self._sess.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.subscription_end > now)
            .order_by(Subscription.id.desc())  # Последняя по id (предполагаем, что id растёт с временем)
            .limit(1)
        )
        return result.scalars().first()

    async def update_subscription(self, subscription_id: int, **kwargs) -> Subscription:
        """Обновляет данные подписки по ID."""
        subscription = await self.get_subscription_by_id(subscription_id)
        if subscription:
            for key, value in kwargs.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            await self._sess.commit()
            return subscription
        print(f"Подписка с id={subscription_id} не найдена")
        return None

    async def delete_subscription(self, sub_id: int) -> bool:
        """Удаляет подписку по ID."""
        sub = await self.get_subscription_by_id(sub_id)
        if sub:
            await self._sess.delete(sub)
            await self._sess.commit()
            return True
        return False
    
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
    
    async def get_all_tariffs_query(self):
        return select(Tariffs)

    async def update_tariff(self, tariff_id: int, **kwargs) -> Tariffs:
        """Обновляет данные тарифа по ID."""
        tariff = await self.get_tariff_by_id(tariff_id)
        if tariff:
            for key, value in kwargs.items():
                if hasattr(tariff, key):
                    setattr(tariff, key, value)
            await self._sess.commit()
            return tariff
        print(f"Тариф с id={tariff_id} не найден")
        return None

    async def delete_tariff(self, tariff_id: int) -> bool:
        """Удаляет тариф по ID."""
        tariff = await self.get_tariff_by_id(tariff_id)
        if tariff:
            await self._sess.delete(tariff)
            await self._sess.commit()
            return True
        print(f"Тариф с id={tariff_id} не найден")
        return False

    # Методы для таблицы PayHistory
    async def create_pay_history(self, user_id: int, tariff_id: int, price: float, successfully: bool, **kwargs) -> PayHistory:
        """Создает запись в истории платежей."""
        pay_history = PayHistory(user_id=user_id, tariff_id=tariff_id, price=price, successfully=successfully, **kwargs)
        self._sess.add(pay_history)
        await self._sess.commit()
        return pay_history

    async def get_all_pay_histories(self) -> list[PayHistory]:
        """Получает все записи в истории платежей."""
        result = await self._sess.execute(select(PayHistory))
        return result.scalars().all()
    
    async def get_all_pay_histories_query(self):
        return select(PayHistory)

    async def get_pay_history_by_id(self, pay_history_id: int) -> PayHistory:
        """Получает запись в истории платежей по ID."""
        result = await self._sess.execute(select(PayHistory).where(PayHistory.id == pay_history_id))
        return result.scalars().first()

    async def get_pay_history_by_user(self, user_id: int) -> list[PayHistory]:
        """Получает историю платежей пользователя."""
        result = await self._sess.execute(select(PayHistory).where(PayHistory.user_id == user_id))
        return result.scalars().all()
    
    async def get_pay_history_by_user_query(self, user_id: int):
        return select(PayHistory).where(PayHistory.user_id == user_id)

    async def get_last_payhistory_by_user(self, user_id: int) -> PayHistory:
        """Получает последнюю запись в истории платежей пользователя."""
        result = await self._sess.execute(select(PayHistory).where(PayHistory.user_id == user_id).order_by(PayHistory.id.desc()))
        return result.scalars().first()

    async def get_payhistory_by_invoice(self, invoice_id: str) -> PayHistory:
        """Получает запись в истории платежей по invoice_id."""
        result = await self._sess.execute(select(PayHistory).where(PayHistory.invoice_id == invoice_id))
        return result.scalars().first()

    async def update_pay_history(self, pay_history_id: int, **kwargs) -> PayHistory:
        """Обновляет данные записи в истории платежей по ID."""
        pay_history = await self.get_pay_history_by_id(pay_history_id)
        if pay_history:
            for key, value in kwargs.items():
                if hasattr(pay_history, key):
                    setattr(pay_history, key, value)
            await self._sess.commit()
            return pay_history
        print(f"Запись в истории платежей с id={pay_history_id} не найдена")
        return None

    async def update_payhistory_by_invoice(self, invoice_id: str, successfully: bool = None):
        """Обновляет запись в истории платежей по invoice_id."""
        pay = await self._sess.execute(select(PayHistory).where(PayHistory.invoice_id == invoice_id))
        pay_obj = pay.scalars().first()
        if pay_obj:
            if successfully is not None:
                pay_obj.successfully = successfully
            await self._sess.commit()
            return pay_obj
        return None

    async def delete_pay_history(self, pay_history_id: int) -> bool:
        """Удаляет запись в истории платежей по ID."""
        pay_history = await self.get_pay_history_by_id(pay_history_id)
        if pay_history:
            await self._sess.delete(pay_history)
            await self._sess.commit()
            return True
        print(f"Запись в истории платежей с id={pay_history_id} не найдена")
        return False
    
    async def edit_payhistory(self, id: int, invoice_id: str = None, successfully: bool = None):
        pay = await self._sess.execute(select(PayHistory).where(PayHistory.id == id))
        pay_obj = pay.scalars().first()
        if pay_obj:
            if successfully is not None:
                pay_obj.successfully = successfully
            if invoice_id is not None:
                pay_obj.invoice_id = invoice_id
            await self._sess.commit()
            return pay_obj
        return None

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
    
    async def get_all_contacts_query(self):
        return select(Contacts)

    async def get_contact_by_id(self, contact_id: int) -> Contacts:
        """Получает контакт по ID."""
        result = await self._sess.execute(select(Contacts).where(Contacts.id == contact_id))
        return result.scalars().first()

    async def update_contact(self, contact_id: int, **kwargs) -> Contacts:
        """Обновляет данные контакта по ID."""
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            for key, value in kwargs.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            await self._sess.commit()
            return contact
        print(f"Контакт с id={contact_id} не найден")
        return None

    async def delete_contact(self, contact_id: int) -> bool:
        """Удаляет контакт по ID."""
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            await self._sess.delete(contact)
            await self._sess.commit()
            return True
        print(f"Контакт с id={contact_id} не найден")
        return False

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

    async def get_setting_by_id(self, setting_id: int) -> Settings:
        """Получает настройку по ID."""
        result = await self._sess.execute(select(Settings).where(Settings.id == setting_id))
        return result.scalars().first()

    async def get_all_settings(self) -> list[Settings]:
        """Получает все настройки."""
        result = await self._sess.execute(select(Settings))
        return result.scalars().all()
    
    async def get_all_settings_query(self):
        return select(Settings)

    async def update_setting(self, setting_id: int, **kwargs) -> Settings:
        """Обновляет данные настройки по ID."""
        setting = await self.get_setting_by_id(setting_id)
        if setting:
            for key, value in kwargs.items():
                if hasattr(setting, key):
                    setattr(setting, key, value)
            await self._sess.commit()
            return setting
        print(f"Настройка с id={setting_id} не найдена")
        return None

    async def delete_setting(self, setting_id: int) -> bool:
        """Удаляет настройку по ID."""
        setting = await self.get_setting_by_id(setting_id)
        if setting:
            await self._sess.delete(setting)
            await self._sess.commit()
            return True
        print(f"Настройка с id={setting_id} не найдена")
        return False
    
    async def create_viewed_car(self, user_id: int, filter_id: int, car_id: int) -> ViewedCars:
        """Создаёт запись о просмотренном автомобиле."""
        viewed_car = ViewedCars(user_id=user_id, filter_id=filter_id, car_id=car_id)
        self._sess.add(viewed_car)
        await self._sess.commit()
        return viewed_car

    async def get_viewed_cars_by_filter(self, user_id: int, filter_id: int) -> list[int]:
        """Получает список ID просмотренных автомобилей для фильтра."""
        result = await self._sess.execute(
            select(ViewedCars.car_id).where(
                ViewedCars.user_id == user_id,
                ViewedCars.filter_id == filter_id
            )
        )
        return [row[0] for row in result.fetchall()]

    async def get_unviewed_cars_by_filter(self, filter_id: int, user_id: int, limit: int = 1):
        """Получает непросмотренные автомобили, соответствующие фильтру."""
        filter_obj = await self.get_filter_by_id(filter_id)
        if not filter_obj:
            return []

        query = select(Car).where(
            (Car.manufacture_id == filter_obj.manufacture_id) if filter_obj.manufacture_id else True,
            (Car.model_id == filter_obj.model_id) if filter_obj.model_id else True,
            (Car.series_id == filter_obj.series_id) if filter_obj.series_id else True,
            (Car.equipment_id == filter_obj.equipment_id) if filter_obj.equipment_id else True,
            (Car.engine_type_id == filter_obj.engine_type_id) if filter_obj.engine_type_id else True,
            (Car.car_color_id == filter_obj.car_color_id) if filter_obj.car_color_id else True,
            (Car.mileage >= filter_obj.mileage_from) if filter_obj.mileage_from else True,
            (Car.mileage <= filter_obj.mileage_defore) if filter_obj.mileage_defore else True,
            (Car.price_rub >= filter_obj.price_from) if filter_obj.price_from else True,
            (Car.price_rub <= filter_obj.price_defore) if filter_obj.price_defore else True,
            (Car.date_release >= filter_obj.date_release_from) if filter_obj.date_release_from else True,
            (Car.date_release <= filter_obj.date_release_defore) if filter_obj.date_release_defore else True,
        )

        viewed_cars = await self.get_viewed_cars_by_filter(user_id, filter_id)
        if viewed_cars:
            query = query.where(Car.id.notin_(viewed_cars))

        query = query.limit(limit)
        result = await self._sess.execute(query)
        return result.scalars().all()

    async def get_new_cars_by_filter(self, filter_id: int, user_id: int, limit: int = 1):
        """Получает новые автомобили, добавленные после создания фильтра."""
        filter_obj = await self.get_filter_by_id(filter_id)
        if not filter_obj:
            return []

        query = select(Car).where(
            Car.create_dttm > filter_obj.create_dttm,
            (Car.manufacture_id == filter_obj.manufacture_id) if filter_obj.manufacture_id else True,
            (Car.model_id == filter_obj.model_id) if filter_obj.model_id else True,
            (Car.series_id == filter_obj.series_id) if filter_obj.series_id else True,
            (Car.equipment_id == filter_obj.equipment_id) if filter_obj.equipment_id else True,
            (Car.engine_type_id == filter_obj.engine_type_id) if filter_obj.engine_type_id else True,
            (Car.car_color_id == filter_obj.car_color_id) if filter_obj.car_color_id else True,
            (Car.mileage >= filter_obj.mileage_from) if filter_obj.mileage_from else True,
            (Car.mileage <= filter_obj.mileage_defore) if filter_obj.mileage_defore else True,
            (Car.price_rub >= filter_obj.price_from) if filter_obj.price_from else True,
            (Car.price_rub <= filter_obj.price_defore) if filter_obj.price_defore else True,
            (Car.date_release >= filter_obj.date_release_from) if filter_obj.date_release_from else True,
            (Car.date_release <= filter_obj.date_release_defore) if filter_obj.date_release_defore else True,
        )

        viewed_cars = await self.get_viewed_cars_by_filter(user_id, filter_id)
        if viewed_cars:
            query = query.where(Car.id.notin_(viewed_cars))

        query = query.limit(limit)
        result = await self._sess.execute(query)
        return result.scalars().all()
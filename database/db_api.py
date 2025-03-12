from datetime import datetime
import random
from sqlalchemy.future import select
from sqlalchemy import or_, exists

from models.base_db_api import BaseDBApi
from models.user_profiles import UserProfiles
from models.chats import Chats
from models.queue import Queue
from models.referrals import Referrals
from models.user_answers import UserAnswers
from models.user_settings import UserSettings
from models.questions import Questions
from models.blocked_users import BlockedUsers
from models.feedbacks import Feedbacks
from models.interests import Interests
from models.moderators import Moderators
from models.user_interests import UserInterests
from models.warnings import Warnings

class DBApi(BaseDBApi):
    
    async def create_user_profile(self, user_id: int)  -> UserProfiles:
        user = UserProfiles(id=user_id)
        self._sess.add(user)
        await self._sess.commit()
        await self.create_user_settings(user_id)
        return user

    async def edit_user_profile(self, user_id: int, level: str = None, empathy_level: str = None, last_test_date: datetime = None, donate_level: int = None) -> UserProfiles:
        user = await self.get_user_profile_by_user_id(user_id) 
        if user:
            if level:
                user.level = level
            if empathy_level:
                user.empathy_level = empathy_level
            if last_test_date:
                user.last_test_date = last_test_date
            if donate_level:
                user.donate_level = donate_level
            await self._sess.commit()
            return user
        else:
            print(f"Такая запись не найдена в таблице {UserProfiles.__tablename__}: {user_id}")
            return None

    async def get_user_profile_by_user_id(self, user_id: int) -> UserProfiles:
        result = await self._sess.execute(select(UserProfiles).where(UserProfiles.id == user_id))
        return result.scalars().first()
    
    async def get_all_users(self) -> list[UserProfiles]:
        result = await self._sess.execute(select(UserProfiles))
        return result.scalars().all()
    
    async def create_chat(self, user_id: int, interlocutor: int) -> Chats:
        chat = Chats(user_id=user_id, interlocutor=interlocutor)
        self._sess.add(chat)
        await self._sess.commit()
        return chat
    
    async def delete_chat(self, user_id: int) -> Chats:
        chat = await self.get_chat_by_user_id(user_id)
        if chat:
            await self._sess.delete(chat)
            await self._sess.commit()
            return chat
        else:
            print(f"Такая запись не найдена в таблице {Chats.__tablename__}: {user_id}")
            return None
    
    async def end_chat(self, user_id: int) -> Chats:
        chat = await self.get_chat_by_user_id(user_id)
        if chat:
            chat.is_ended = True
            chat.datetime_ended = datetime.now()
            await self._sess.commit()
            return chat
        else:
            print(f"Такая запись не найдена в таблице {Chats.__tablename__}: {user_id}")
            return None
    
    async def get_chat_by_user_id(self, user_id: int) -> Chats:
        result = await self._sess.execute(select(Chats).where(Chats.user_id == user_id).where(Chats.is_ended == False))
        return result.scalars().first()
    
    async def get_chat_by_id(self, chat_id: int) -> Chats:
        result = await self._sess.execute(select(Chats).where(Chats.id == chat_id))
        return result.scalars().first()
    
    async def create_queue(self, user_id: int, age: int, gender: str, age_from: int = 16, age_to: int = 100, search_gender: str = "Не важно") -> Queue:
        queue = Queue(user_id=user_id, age=age, gender=gender, age_from=age_from, age_to=age_to, search_gender=search_gender)
        self._sess.add(queue)
        await self._sess.commit()
        return queue
    
    async def delete_queue(self, user_id: int) -> Queue:
        queue = await self.get_queue_by_user_id(user_id)
        if queue:
            await self._sess.delete(queue)
            await self._sess.commit()
            return queue
        else:
            print(f"Такая запись не найдена в таблице {Queue.__tablename__}: {user_id}")
            return None
    
    async def get_queue_by_user_id(self, user_id: int) -> Queue:
        result = await self._sess.execute(select(Queue).where(Queue.user_id == user_id))
        return result.scalars().first()
    
    async def get_queue_first(self) -> Queue:
        result = await self._sess.execute(select(Queue).order_by(Queue.datetime_created.asc()).limit(1))
        return result.scalars().first()
    
    async def get_queue_first_with_filters(
        self,
        user_gender: str,           # Пол пользователя, ищущего собеседника
        search_gender: str,         # Настройка поиска по полу
        search_age_from: int,
        search_age_to: int,
        current_level: str,         # Ваш спиральный уровень (UserProfiles.level)
        current_empathy: str,       # Ваш уровень эмпатии (UserProfiles.empathy_level)
        search_level: str,          # Настройка поиска по уровню: "Собеседник моего уровня", "Собеседник соседних уровней", "Собеседник любого уровня"
        search_empathy_level: str,  # Настройка поиска по эмпатии: "Собеседник моего уровня", "Собеседник соседних уровней", "Собеседник любого уровня"
        current_interests: list = []# Список ID интересов текущего пользователя
    ) -> Queue:
        # Базовый запрос – отбираем записи из очереди по возрасту
        query = select(Queue).join(UserProfiles, UserProfiles.id == Queue.user_id).where(
            Queue.age >= search_age_from,
            Queue.age <= search_age_to
        )
        
        # Фильтрация по полу: если выбран конкретный пол для поиска
        if search_gender != "Не важно":
            query = query.where(Queue.gender == search_gender)
        
        # Проверяем, что собеседнику подходит ваш пол (либо у него предпочтение "Не важно")
        query = query.where(
            or_(Queue.search_gender == "Не важно", Queue.search_gender == user_gender)
        )
        
        # Фильтрация по спиральному уровню
        spiral_order = ["Бежевый", "Фиолетовый", "Синий", "Красный", "Оранжевый", "Жёлтый", "Зелёный", "Бирюзовый"]
        if search_level == "Собеседник моего уровня":
            query = query.where(UserProfiles.level == current_level)
        elif search_level == "Собеседник соседних уровней":
            if current_level in spiral_order:
                idx = spiral_order.index(current_level)
                valid_levels = [current_level]
                if idx > 0:
                    valid_levels.append(spiral_order[idx - 1])
                if idx < len(spiral_order) - 1:
                    valid_levels.append(spiral_order[idx + 1])
                query = query.where(UserProfiles.level.in_(valid_levels))
        # Если выбрано "Собеседник любого уровня" — фильтрация по уровню не применяется
        
        # Фильтрация по уровню эмпатии
        empathy_order = ["низкий", "средний", "высокий"]
        if search_empathy_level == "Собеседник моего уровня":
            query = query.where(UserProfiles.empathy_level == current_empathy)
        elif search_empathy_level == "Собеседник соседних уровней":
            if current_empathy in empathy_order:
                idx = empathy_order.index(current_empathy)
                valid_empathy = [current_empathy]
                if idx > 0:
                    valid_empathy.append(empathy_order[idx - 1])
                if idx < len(empathy_order) - 1:
                    valid_empathy.append(empathy_order[idx + 1])
                query = query.where(UserProfiles.empathy_level.in_(valid_empathy))
        # При выборе "Собеседник любого уровня" фильтрация по эмпатии не применяется
        
        # Фильтрация по интересам: хотя бы одно совпадение
        if current_interests:
            query = query.where(
                exists(
                    select(UserInterests.id).where(
                        UserInterests.user_id == Queue.user_id,
                        UserInterests.interest_id.in_(current_interests)
                    )
                )
            )
        
        # Сортировка по времени добавления в очередь (старейшая запись) и выбор одного собеседника
        query = query.order_by(Queue.datetime_created.asc()).limit(1)
        
        result = await self._sess.execute(query)
        return result.scalars().first()
    
    async def get_all_queue(self) -> list[Queue]:
        result = await self._sess.execute(select(Queue))
        return result.scalars().all()
    
    async def get_count_queue(self) -> int:
        result = await self._sess.execute(select(Queue))
        return len(result.scalars().all())
    
    async def create_referral(self, user_id: int, invitied: int) -> Referrals:
        referral = Referrals(user_id=user_id, invitied=invitied)
        self._sess.add(referral)
        await self._sess.commit()
        return referral
    
    async def get_count_referrals_by_user_id(self, user_id: int) -> int:
        result = await self._sess.execute(select(Referrals).where(Referrals.user_id == user_id))
        return len(result.scalars().all())
    
    async def create_user_answer(self, user_id: int, question_id: int, selected_option: str, level: str, empathy_score: int) -> UserAnswers:
        answer = UserAnswers(user_id=user_id, question_id=question_id, selected_option=selected_option, level=level, empathy_score=empathy_score)
        self._sess.add(answer)
        await self._sess.commit()
        return answer
    
    async def edit_user_answer(self, user_id: int, question_id: int, selected_option: str = None, level: str = None, empathy_score: int = None) -> UserAnswers:
        answer = await self.get_user_answer_by_user_id_and_question_id(user_id, question_id)
        if answer:
            if selected_option:
                answer.selected_option = selected_option
            if level:
                answer.level = level
            if empathy_score:
                answer.empathy_score = empathy_score
            await self._sess.commit()
            return answer
        else:
            print(f"Такая запись не найдена в таблице {UserAnswers.__tablename__}: {user_id} - {question_id}")
            return None
    
    async def get_user_answer_by_user_id_and_question_id(self, user_id: int, question_id: int) -> UserAnswers:
        result = await self._sess.execute(select(UserAnswers).where(UserAnswers.user_id == user_id).where(UserAnswers.question_id == question_id))
        return result.scalars().first()
    
    async def create_user_settings(self, user_id: int) -> UserSettings:
        settings = UserSettings(user_id=user_id)
        self._sess.add(settings)
        await self._sess.commit()
        return settings
    
    async def edit_user_settings(self, user_id: int, age: int = None, gender: str = None, search_level: str = None, search_empathy_level: str = None, search_gender: str = None, search_age_from: int = None, search_age_to: int = None) -> UserSettings:
        settings = await self.get_user_settings_by_user_id(user_id) 
        if settings:
            if age:
                settings.age = age
            if gender:
                settings.gender = gender
            if search_level:
                settings.search_level = search_level
            if search_empathy_level:
                settings.search_empathy_level = search_empathy_level
            if search_gender:
                settings.search_gender = search_gender
            if search_age_from:
                settings.search_age_from = search_age_from
            if search_age_to:
                settings.search_age_to = search_age_to
            await self._sess.commit()
            return settings
        else:
            print(f"Такая запись не найдена в таблице {UserSettings.__tablename__}: {user_id}")
            return None
    
    async def get_user_settings_by_user_id(self, user_id: int) -> UserSettings:
        result = await self._sess.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        return result.scalars().first()
    
    async def get_questions(self) -> list[Questions]:
        result = await self._sess.execute(select(Questions))
        return result.scalars().all()
    
    async def get_question_by_id(self, question_id: int) -> Questions:
        result = await self._sess.execute(select(Questions).where(Questions.id == question_id))
        return result.scalars().first()
    
    async def create_blocked_user(self, user_id: int, reason: str = "Не уточнено", blocked_until: datetime = None) -> BlockedUsers:
        if blocked_until is None:
            blocked_user = BlockedUsers(user_id=user_id, reason=reason)
        else:
            blocked_user = BlockedUsers(user_id=user_id, reason=reason, blocked_until=blocked_until)
        self._sess.add(blocked_user)
        await self._sess.commit()
        return blocked_user
    
    async def get_blocked_users_by_user_id(self, user_id: int) -> list[BlockedUsers]:
        result = await self._sess.execute(select(BlockedUsers).where(BlockedUsers.user_id == user_id))
        return result.scalars().all()
    
    async def get_blocked_user_latest_by_user_id(self, user_id: int) -> BlockedUsers:
        """
        Returns the latest time user was blocked
        """
        result = await self._sess.execute(select(BlockedUsers).where(BlockedUsers.user_id == user_id).order_by(BlockedUsers.datetime_created.desc()).limit(1))
        return result.scalars().first()
    
    async def get_blocked_user_until_by_user_id(self, user_id: int) -> BlockedUsers:
        """
        Returns blocked user if the user is blocked now
        """
        result = await self._sess.execute(select(BlockedUsers).where(BlockedUsers.user_id == user_id).where(BlockedUsers.blocked_until > datetime.now()).limit(1))
        return result.scalars().first()
    
    async def get_blocked_user_by_id(self, id: int) -> BlockedUsers:
        result = await self._sess.execute(select(BlockedUsers).where(BlockedUsers.id == id))
        return result.scalars().first()
    
    async def delete_blocked_user_by_id(self, id: int) -> None:
        blocked_user = await self.get_blocked_user_by_id(id)
        if not blocked_user:
            print(f"Такая запись не найдена в таблице {BlockedUsers.__tablename__}: {id}")
            return
        await self._sess.delete(blocked_user)
        await self._sess.commit()
        return
    
    async def edit_blocked_user_by_id(self, id: int, reason: str = None, blocked_until: datetime = None) -> None:
        blocked_user = await self.get_blocked_user_by_id(id)
        if blocked_user:
            if reason:
                blocked_user.reason = reason
            if blocked_until:
                blocked_user.blocked_until = blocked_until
            await self._sess.commit()
            return
        else:
            print(f"Такая запись не найдена в таблице {BlockedUsers.__tablename__}: {id}")
            return
    
    async def create_feedback(self, from_user_id: int, to_user_id: int, chat_id: int, feedback_type: str = "Не уточнено", reason: str = "Не уточнено") -> Feedbacks:
        feedback = Feedbacks(from_user_id=from_user_id, to_user_id=to_user_id, chat_id=chat_id, feedback_type=feedback_type, reason=reason)
        self._sess.add(feedback)
        await self._sess.commit()
        return feedback
    
    async def get_feedback_by_id(self, id: int) -> Feedbacks:
        result = await self._sess.execute(select(Feedbacks).where(Feedbacks.id == id))
        return result.scalars().first()
    
    async def get_feedbacks_by_from_user_id(self, from_user_id: int) -> list[Feedbacks]:
        result = await self._sess.execute(select(Feedbacks).where(Feedbacks.from_user_id == from_user_id))
        return result.scalars().all()
    
    async def get_feedbacks_by_reviewed(self, reviewed: bool) -> list[Feedbacks]:
        result = await self._sess.execute(select(Feedbacks).where(Feedbacks.reviewed == reviewed))
        return result.scalars().all()
    
    async def get_bad_not_reviewed_feedbacks_by_to_user_id(self, to_user_id: int) -> list[Feedbacks]:
        result = await self._sess.execute(select(Feedbacks).where(Feedbacks.to_user_id == to_user_id).where(Feedbacks.feedback_type == "👎 Отрицательно").where(Feedbacks.reviewed == False))
        return result.scalars().all()
    
    async def get_good_not_reviewed_feedbacks_by_to_user_id(self, to_user_id: int) -> list[Feedbacks]:
        result = await self._sess.execute(select(Feedbacks).where(Feedbacks.to_user_id == to_user_id).where(Feedbacks.feedback_type == "👍 Положительно").where(Feedbacks.reviewed == False))
        return result.scalars().all()
    
    async def edit_feedback_by_id(self, id: int, reviewed: bool = None) -> None:
        feedback = await self.get_feedback_by_id(id)
        if feedback:
            if reviewed is not None:
                feedback.reviewed = reviewed
            await self._sess.commit()
            return
        else:
            print(f"Такая запись не найдена в таблице {Feedbacks.__tablename__}: {id}")
            return
    
    async def delete_feedback_by_id(self, id: int) -> None:
        await self._sess.delete(Feedbacks(id=id))
        await self._sess.commit()
        return
    
    async def get_all_interests(self) -> list[Interests]:
        result = await self._sess.execute(select(Interests))
        return result.scalars().all()
    
    async def get_interest_by_name(self, name: str) -> Interests:
        result = await self._sess.execute(select(Interests).where(Interests.name == name))
        return result.scalars().first()
    
    async def create_moderator(self, user_id: int, permissions: str = "r") -> Moderators:
        moderator = Moderators(user_id=user_id, permissions=permissions)
        self._sess.add(moderator)
        await self._sess.commit()
        return moderator
    
    async def edit_moderator_by_user_id(self, user_id: int, permissions: str = None) -> None:
        moderator = await self.get_moderator_by_user_id(user_id)
        if moderator:
            if permissions:
                moderator.permissions = permissions
            await self._sess.commit()
            return
        else:
            print(f"Такая запись не найдена в таблице {Moderators.__tablename__}: {user_id}")
            return
    
    async def get_moderator_by_user_id(self, user_id: int) -> Moderators:
        result = await self._sess.execute(select(Moderators).where(Moderators.user_id == user_id))
        return result.scalars().first()
    
    async def delete_moderator_by_user_id(self, user_id: int) -> None:
        await self._sess.delete(Moderators(user_id=user_id))
        await self._sess.commit()
        return
    
    async def get_all_moderators(self) -> list[Moderators]:
        result = await self._sess.execute(select(Moderators))
        return result.scalars().all()
    
    async def create_user_interest(self, user_id: int, interest_id: int) -> UserInterests:
        user_interest = UserInterests(user_id=user_id, interest_id=interest_id)
        self._sess.add(user_interest)
        await self._sess.commit()
        return user_interest
    
    async def create_or_delete_user_interest(self, user_id: int, interest_id: int) -> None:
        user_interest = await self.get_user_interest_by_user_id_and_interest_id(user_id, interest_id)
        if user_interest:
            await self.delete_user_interest_by_user_id_and_interest_id(user_id, interest_id)
        else:
            await self.create_user_interest(user_id, interest_id)
        return
    
    async def get_user_interests_by_user_id(self, user_id: int) -> list[UserInterests]:
        result = await self._sess.execute(select(UserInterests).where(UserInterests.user_id == user_id))
        return result.scalars().all()
    
    async def get_user_interest_by_user_id_and_interest_id(self, user_id: int, interest_id: int) -> UserInterests:
        result = await self._sess.execute(select(UserInterests).where(UserInterests.user_id == user_id).where(UserInterests.interest_id == interest_id))
        return result.scalars().first()
    
    async def delete_user_interest_by_user_id_and_interest_id(self, user_id: int, interest_id: int) -> None:
        user_interest = await self.get_user_interest_by_user_id_and_interest_id(user_id, interest_id)
        if user_interest:
            await self._sess.delete(user_interest)
            await self._sess.commit()
        else:
            print(f"Такая запись не Kurdена в таблице {UserInterests.__tablename__}: {user_id} - {interest_id}")
        return
    
    async def create_warning(self, user_id: int, moderator_id: int, reason: str = "Не уточнено") -> Warnings:
        warning = Warnings(user_id=user_id, moderator_id=moderator_id, reason=reason)
        self._sess.add(warning)
        await self._sess.commit()
        return warning
    
    async def get_warnings_by_user_id(self, user_id: int) -> list[Warnings]:
        result = await self._sess.execute(select(Warnings).where(Warnings.user_id == user_id))
        return result.scalars().all()
    
    async def get_warning_by_id(self, id: int) -> Warnings:
        result = await self._sess.execute(select(Warnings).where(Warnings.id == id))
        return result.scalars().first()
    
    async def get_warnings_by_moderator_id(self, moderator_id: int) -> list[Warnings]:
        result = await self._sess.execute(select(Warnings).where(Warnings.moderator_id == moderator_id))
        return result.scalars().all()
    
    async def edit_warning_by_id(self, id: int, reason: str = None) -> None:
        warning = await self.get_warning_by_id(id)
        if warning:
            if reason:
                warning.reason = reason
            await self._sess.commit()
            return
        else:
            print(f"Такая запись не Kurdена в таблице {Warnings.__tablename__}: {id}")
            return
    
    async def delete_warining_by_id(self, id: int) -> None:
        await self._sess.delete(Warnings(id=id))
        await self._sess.commit()
        return
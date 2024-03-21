import os
from datetime import datetime, timedelta

from database.models.models import Database
from database.models.payment_model import PaymentSchemaWithoutId
from database.models.user_model import UserStatusValues

from subscription import config
from subscription.scheduler import Scheduler


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


class UserHasAlreadyStartedTrial(Exception):
    """Error when user tries start a trial again"""
    pass


@singleton
class Subscription:
    """Модуль системы подписки"""

    def __init__(self, database: Database, scheduler: Scheduler) -> None:
        self.user_db = database.get_user_dao()
        self.payment_db = database.get_payment_dao()

        self.scheduler = scheduler

    async def start_trial(self, user_id: int) -> datetime:
        """Starts trial subscription of the user"""
        user = await self.user_db.get_user(user_id)
        if user.status != UserStatusValues.NEW:
            raise UserHasAlreadyStartedTrial(f"user with user_id {user_id} has already stated a trial")

        user.subscribed_until = datetime.now() + timedelta(
            days=config.TRIAL_DURATION_IN_DAYS)  # TODO change it to 7 days
        user.status = UserStatusValues.TRIAL

        await self.user_db.update_user(user)
        return user.subscribed_until

    async def approve_payment(self, user_id: int) -> datetime:
        """Approves user's payment"""
        user = await self.user_db.get_user(user_id)
        await self.create_payment(user_id)

        subscription_delta = timedelta(days=config.SUBSCRIPTION_DURATION_IN_DAYS)
        if user.status == UserStatusValues.SUBSCRIPTION_ENDED or user.subscribed_until is None:
            user.subscribed_until = datetime.now() + subscription_delta  # TODO change it to 31 days
        else:
            user.subscribed_until = user.subscribed_until + subscription_delta  # TODO change it to 31 days
        user.status = UserStatusValues.SUBSCRIBED

        await self.user_db.update_user(user)
        return user.subscribed_until

    async def create_payment(self, user_id: int) -> None:
        """Creates a new payment"""
        current_datetime = datetime.now()
        payment = PaymentSchemaWithoutId(from_user=user_id,
                                         amount=config.SUBSCRIPTION_PRICE,
                                         status="success",
                                         created_at=current_datetime,
                                         last_update=current_datetime)
        await self.payment_db.add_payment(payment)

    async def add_notifications(self, user_id, on_expiring_notification, on_end_notification,
                                subscribed_until: datetime) -> list[str]:
        """Create notifications about states of subscription"""
        user = await self.user_db.get_user(user_id)

        job_ids = []
        for notification_before_days in config.NOTIFICATIONS_BEFORE_DAYS:
            job_ids.append(await self.scheduler.add_scheduled_job(
                func=on_expiring_notification,
                run_date=subscribed_until - timedelta(days=notification_before_days),
                args=[user]
            ))
        job_ids.append(await self.scheduler.add_scheduled_job(
            func=on_end_notification,
            run_date=subscribed_until,
            args=[user]
        ))

        return job_ids

    async def get_user_status(self, user_id: int) -> UserStatusValues:
        """Returns the status of user's subscription"""
        return (await self.user_db.get_user(user_id)).status

    async def is_user_subscribed(self, user_id: int) -> bool:
        """Check if user status is subscribed or trial"""
        user = await self.user_db.get_user(user_id)
        return user.status in (UserStatusValues.TRIAL, UserStatusValues.SUBSCRIBED)

    @staticmethod
    def get_subscription_price() -> int:
        """Returns the price of subscription"""
        return config.SUBSCRIPTION_PRICE

    @staticmethod
    def get_destination_phone_number() -> str:
        """Returns the phone number to pay to"""
        return config.DESTINATION_PHONE_NUMBER

    async def start_scheduler(self) -> None:
        """Starts the scheduler"""
        await self.scheduler.start()

    async def get_when_expires_text(self, user_id: int, is_trial: bool) -> str:
        user = await self.user_db.get_user(user_id)
        subscription_type = " бесплатная " if is_trial else " "
        return f"Твоя{subscription_type}подписка истекает " \
               f"<b>{user.subscribed_until.strftime('%d.%m.%Y %H:%M')}</b> " \
               f"(через <b>{(user.subscribed_until - datetime.now()).days}</b> дней)." \
               f"\nХочешь продлить прямо сейчас?"

    @staticmethod
    def get_subscribe_instructions() -> tuple[str, str]:
        """Returns file name of QR CODE image and text of instructions"""
        return "sbp_qr.png", \
               f"• Стоимость подписки: <b>{config.SUBSCRIPTION_PRICE}₽</b>\n\n" \
               f"• Оплачивайте подписку удобным способом, " \
               f"через qr код. Либо на карту сбербанка по номеру телефона: " \
               f"<code>{config.DESTINATION_PHONE_NUMBER}</code>\n\n" \
               f"• После оплаты пришлите боту чек (скрин или пдфку) с подтверждением оплаты.\n\n" \
               f"• В подписи к фото <b>напишите Ваши контакты для связи</b> с " \
               f"Вами в случае возникновения вопросов по оплате.",


if __name__ == '__main__':
    from bot import config

    from database.models.models import Database

    scheduler = Scheduler('postgres', config.TIMEZONE)

    subscription = Subscription(
        database=Database(sqlalchemy_url=os.getenv("DB_FOR_TESTS")),
        scheduler=scheduler
    )

from datetime import datetime, timedelta


from database.models.models import Database
from database.models.user_model import UserStatusValues, UserSchema
from database.models.payment_model import PaymentSchemaWithoutId

from common_utils.env_config import DESTINATION_PHONE_NUMBER, TIMEZONE, DB_FOR_TESTS, SCHEDULER_URL
from common_utils.subscription import config
from common_utils.scheduler.scheduler import Scheduler

from logs.config import logger, extra_params


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

    def __init__(self, database: Database, custom_scheduler: Scheduler) -> None:
        self.user_db = database.get_user_dao()
        self.payment_db = database.get_payment_dao()

        self.scheduler = custom_scheduler

    async def start_trial(self, user_id: int) -> UserSchema:
        """Starts trial subscription of the user"""
        user = await self.user_db.get_user(user_id)
        if user.status != UserStatusValues.NEW:
            raise UserHasAlreadyStartedTrial(f"user with user_id {user_id} has already stated a trial")

        user.subscribed_until = datetime.now() + timedelta(
            days=config.TRIAL_DURATION_IN_DAYS)
        user.status = UserStatusValues.TRIAL

        logger.info(
            f"user_id={user_id}: the user started trial for {config.TRIAL_DURATION_IN_DAYS} days and he is subscribed"
            f"until {user.subscribed_until}",
            extra=extra_params(user_id=user_id)
        )

        return user

    async def approve_payment(self, user_id: int) -> datetime:
        """Approves user's payment"""
        user = await self.user_db.get_user(user_id)
        payment_id = await self.create_payment(user_id)

        subscription_delta = timedelta(days=config.SUBSCRIPTION_DURATION_IN_DAYS)
        if user.status == UserStatusValues.SUBSCRIPTION_ENDED or user.subscribed_until is None:
            user.subscribed_until = datetime.now() + subscription_delta
        else:
            user.subscribed_until = user.subscribed_until + subscription_delta
        user.status = UserStatusValues.SUBSCRIBED

        await self.user_db.update_user(user)

        logger.info(
            f"user_id={user_id}: the user's payment has been approved so the user is subscribed "
            f"until {user.subscribed_until} (+{subscription_delta} days)",
            extra=extra_params(user_id=user_id, payment_id=payment_id)
        )

        return user.subscribed_until

    async def create_payment(self, user_id: int) -> int:
        """Creates a new payment"""
        current_datetime = datetime.now()
        payment = PaymentSchemaWithoutId(from_user=user_id,
                                         amount=config.SUBSCRIPTION_PRICE,
                                         status="success",
                                         created_at=current_datetime,
                                         last_update=current_datetime)
        payment_id = await self.payment_db.add_payment(payment)

        logger.info(
            f"user_id={user_id}: the user's payment created: {payment}",
            extra=extra_params(user_id=user_id, payment_id=payment_id)
        )

        return payment_id

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

        logger.debug(
            f"user_id={user_id}: user's notifications about payment are created: job_ids={job_ids}",
            extra=extra_params(user_id=user_id)
        )

        return job_ids

    async def get_user_status(self, user_id: int) -> UserStatusValues:
        """Returns the status of user's subscription"""
        user_status = (await self.user_db.get_user(user_id)).status

        logger.debug(
            f"user_id={user_id}: user's subscription status is {user_status}",
            extra=extra_params(user_id=user_id)
        )

        return user_status

    async def is_user_subscribed(self, user_id: int) -> bool:
        """Check if user status is subscribed or trial"""
        user = await self.user_db.get_user(user_id)
        is_subscribed = user.status in (UserStatusValues.TRIAL, UserStatusValues.SUBSCRIBED)

        logger.debug(
            f"user_id={user_id}: user is subscribed with {user.status}",
            extra=extra_params(user_id=user_id)
        )

        return is_subscribed

    @staticmethod
    def get_subscription_price() -> int:
        """Returns the price of subscription"""
        price = config.SUBSCRIPTION_PRICE
        logger.debug(
            f"returned subscription_price={price}"
        )
        return price

    @staticmethod
    def get_destination_phone_number() -> str:
        """Returns the phone number to pay to"""
        logger.debug(
            f"returned phone_number={DESTINATION_PHONE_NUMBER}"
        )
        return DESTINATION_PHONE_NUMBER

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
               f"<code>{DESTINATION_PHONE_NUMBER}</code>\n\n" \
               f"• После оплаты пришлите боту чек (скрин или пдфку) с подтверждением оплаты.\n\n" \
               f"• В подписи к фото <b>напишите Ваши контакты для связи</b> с " \
               f"Вами в случае возникновения вопросов по оплате.",


if __name__ == '__main__':
    from database.models.models import Database

    scheduler = Scheduler(SCHEDULER_URL, 'postgres', TIMEZONE)

    subscription = Subscription(
        database=Database(sqlalchemy_url=DB_FOR_TESTS, logger=logger),
        custom_scheduler=scheduler,
    )

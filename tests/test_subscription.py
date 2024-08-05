import asyncio
import os
from datetime import datetime, timedelta

import pytest

from common_utils.subscription.subscription import Subscription, UserHasAlreadyStartedTrial
from common_utils.env_config import PROJECT_ROOT
from database.models.payment_model import PaymentDao
from database.models.user_model import UserDao, UserStatusValues

from tests.schemas import user_schema_2, user_schema_1


class TestSubscription:
    async def test_start_trial(self, subscription: Subscription, user_db: UserDao, before_add_two_users) -> None:
        """Subscription.start_trial"""
        with pytest.raises(UserHasAlreadyStartedTrial):
            await subscription.start_trial(user_schema_2.id)

        subscribed_until = await subscription.start_trial(user_schema_1.id)
        expired_in_seconds = int((subscribed_until - datetime.now()).total_seconds())
        assert expired_in_seconds in range(7 * 24 * 3600 - 5, 7 * 24 * 3600)

        user = await user_db.get_user(user_schema_1.id)
        assert user.status == UserStatusValues.TRIAL and user.subscribed_until == subscribed_until

    async def test_approve_payment(
            self, subscription: Subscription, user_db: UserDao, payment_db: PaymentDao, before_add_user
    ) -> None:
        """Subscription.approve_payment"""
        user = await user_db.get_user(1)
        user.status = UserStatusValues.SUBSCRIPTION_ENDED
        await user_db.update_user(user)

        await subscription.approve_payment(user_id=1)
        approved_user = await user_db.get_user(1)
        payment = await payment_db.get_payment(1)

        user_schema_1.status, backup_status = UserStatusValues.SUBSCRIBED, user_schema_1.status
        expired_in_seconds = int((approved_user.subscribed_until - datetime.now()).total_seconds())

        assert approved_user.model_dump(exclude={"subscribed_until"}) == \
               user_schema_1.model_dump(exclude={"subscribed_until"})
        assert expired_in_seconds in range(31 * 24 * 3600 - 5, 31 * 24 * 3600)
        assert payment.status == "success" and payment.from_user == user_schema_1.id

        user_schema_1.status = backup_status

    async def test_create_payment(self, subscription: Subscription, payment_db: PaymentDao, before_add_user) -> None:
        """Subscription.create_payment"""
        await subscription.create_payment(user_id=1)
        payment = await payment_db.get_payment(payment_id=1)
        assert payment.from_user == 1 and payment.amount == 1990 and payment.status == "success" and \
               payment.created_at == payment.last_update and int(
            (datetime.now() - payment.created_at).total_seconds()) < 5

    async def test_add_notifications(self, subscription: Subscription, before_add_user) -> None:
        """Subscription.add_notifications"""
        subscribed_until = datetime.now() + timedelta(days=31)

        job_ids = await subscription.add_notifications(
            user_id=1,
            on_expiring_notification=TestSubscription._func,
            on_end_notification=TestSubscription._func,
            subscribed_until=subscribed_until
        )
        assert len(job_ids) == 3

        for job_id, notification_before_days in zip(job_ids, [1, 3]):
            job = await subscription.scheduler.get_job(job_id)
            assert job.next_run_time.replace(tzinfo=None) == subscribed_until - timedelta(days=notification_before_days)

        assert (await subscription.scheduler.get_job(job_ids[-1])).next_run_time.replace(tzinfo=None) == \
               subscribed_until

    async def test_get_user_status(self, subscription: Subscription, before_add_two_users) -> None:
        """Subscription.get_user_status"""
        assert await subscription.get_user_status(user_schema_1.id) == UserStatusValues.NEW
        assert await subscription.get_user_status(user_schema_2.id) == UserStatusValues.SUBSCRIBED

    async def test_is_user_subscribed(self, subscription: Subscription, user_db: UserDao, before_add_user) -> None:
        """Subscription.is_user_subscribed"""
        user_id = 1
        user = await user_db.get_user(user_id)
        for user_status in UserStatusValues:
            user.status = user_status
            await user_db.update_user(user)
            assert await subscription.is_user_subscribed(user_id) == (True
                                                                      if user_status in (
                UserStatusValues.SUBSCRIBED, UserStatusValues.TRIAL) else False)

    def test_get_subscription_price(self, subscription: Subscription) -> None:
        """Subscription.get_subscription_price"""
        assert subscription.get_subscription_price() == 1990

    def test_get_destination_phone_number(self, subscription: Subscription) -> None:
        """Subscription.get_destination_phone_number"""
        assert subscription.get_destination_phone_number() == "+79778506494"

    async def test_start_scheduler(self, subscription: Subscription) -> None:
        """Subscription.start_scheduler"""
        await subscription.scheduler.stop_scheduler()
        await asyncio.sleep(1)
        assert subscription.scheduler.scheduler.running == False
        await subscription.start_scheduler()
        await asyncio.sleep(1)
        assert subscription.scheduler.scheduler.running == True

    async def test_get_when_expires_text(self, subscription: Subscription, before_add_two_users) -> None:
        """Subscription.get_when_expires_text"""
        expired_days = (user_schema_2.subscribed_until - datetime.now()).days
        trial_text = await subscription.get_when_expires_text(user_id=2, is_trial=True)
        assert trial_text == f"""Твоя бесплатная подписка истекает <b>03.03.2056 08:05</b> (через <b>{expired_days}</b> дней).
Хочешь продлить прямо сейчас?"""

    def test_get_subscribe_instructions(self, subscription: Subscription) -> None:
        """Subscription.get_subscribe_instructions"""
        excepted_qr_code_filename = "sbp_qr.png"
        subscribe_instructions = subscription.get_subscribe_instructions()
        assert os.path.exists(PROJECT_ROOT + "resources/" + excepted_qr_code_filename)
        assert subscribe_instructions[0] == excepted_qr_code_filename and \
               subscribe_instructions[1] == """• Стоимость подписки: <b>1990₽</b>

• Оплачивайте подписку удобным способом, через qr код. Либо на карту сбербанка по номеру телефона: <code>+79778506494</code>

• После оплаты пришлите боту чек (скрин или пдфку) с подтверждением оплаты.

• В подписи к фото <b>напишите Ваши контакты для связи</b> с Вами в случае возникновения вопросов по оплате."""

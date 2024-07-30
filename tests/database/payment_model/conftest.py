import datetime

import pytest
import datetime

from database.models.models import Database
from database.models.user_model import UserSchema, UserStatusValues
from database.models.payment_model import PaymentSchema, PaymentDao


@pytest.fixture
def payment_db(database: Database):
    return database.get_payment_dao()


@pytest.fixture
def user():
    return UserSchema(
        user_id=1,
        username="admin",
        status=UserStatusValues.SUBSCRIBED,
        subscribed_until=datetime.datetime.now(),
        registered_at=datetime.datetime.now(),
        settings=None,
        locale="ru",
        balance=0,
        subscription_job_ids=None
    )


@pytest.fixture
def payments(user: UserSchema):
    return [
        PaymentSchema(
            payment_id=1,
            from_user=user.id,
            amount=1990,
            status="success",
            created_at=datetime.datetime.now(),
            last_update=datetime.datetime.now()
        )
    ]


@pytest.fixture
async def add_payments(payments: list[PaymentSchema], payment_db: PaymentDao):
    for payment in payments:
        print(2)
        await payment_db.add_payment(payment)

import datetime

import pytest
from aiogram.types import User

from database.models.option_model import OptionSchema
from database.models.payment_model import PaymentSchema
from database.models.user_model import UserSchema, UserStatusValues


@pytest.fixture
def user_schema(tg_user: User) -> UserSchema:
    return UserSchema(
        user_id=tg_user.id,
        username=tg_user.username,
        status=UserStatusValues.NEW,
        subscribed_until=None,
        registered_at=datetime.date(1960, 12, 12),
    )


@pytest.fixture
def option_schema() -> OptionSchema:
    return OptionSchema(id=1, web_app_button="default")


@pytest.fixture
def payment_schemas(user_schema: UserSchema):
    return [
        PaymentSchema(
            payment_id=1,
            from_user=user_schema.id,
            amount=1990,
            status="success",
            created_at=datetime.datetime.now(),
            last_update=datetime.datetime.now(),
        )
    ]

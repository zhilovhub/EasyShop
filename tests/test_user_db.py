from datetime import datetime, timedelta

import pytest

from bot.exceptions import InvalidParameterFormat, UserNotFound, InstanceAlreadyExists
from database.models.user_model import UserDao, UserSchema, NotInUserStatusesList

from pydantic import ValidationError

user_schema_1 = UserSchema(
    user_id=1,
    status="new",
    subscribed_until=None,
    registered_at=datetime.utcnow()
)
user_schema_2 = UserSchema(
    user_id=2,
    status="new",
    subscribed_until=datetime.now() + timedelta(days=7),
    registered_at=datetime.utcnow()
)


@pytest.fixture
async def before_add_user(user_db: UserDao) -> None:
    await user_db.add_user(user_schema_1)


@pytest.fixture
async def before_add_two_users(user_db: UserDao) -> None:
    await user_db.add_user(user_schema_1)
    await user_db.add_user(user_schema_2)


class TestUserDb:
    async def test_get_user(self, user_db: UserDao, before_add_user) -> None:
        """UserDao.get_user"""
        with pytest.raises(InvalidParameterFormat):
            await user_db.get_user(str(user_schema_1.id))

        with pytest.raises(UserNotFound):
            await user_db.get_user(user_schema_1.id + 1)

        user = await user_db.get_user(user_schema_1.id)
        assert user == user_schema_1

    async def test_get_users(self, user_db: UserDao, before_add_two_users) -> None:
        """UserDao.get_users"""
        users = await user_db.get_users()
        assert users[0] == user_schema_1
        assert users[1] == user_schema_2

    async def test_add_user(self, user_db: UserDao, before_add_user) -> None:
        """UserDao.add_user"""
        with pytest.raises(InvalidParameterFormat):
            await user_db.add_user(1)

        with pytest.raises(InstanceAlreadyExists):
            await user_db.add_user(user_schema_1)

        await user_db.add_user(user_schema_2)
        user = await user_db.get_user(user_schema_2.id)
        assert user == user_schema_2

    async def test_update_user(self, user_db: UserDao, before_add_user) -> None:
        """UserDao.update_user"""
        with pytest.raises(InvalidParameterFormat):
            await user_db.update_user(1)

        with pytest.raises(ValidationError):
            user_schema_1.status = "random_string"
            await user_db.update_user(user_schema_1)
            user = await user_db.get_user(user_schema_1.id)

        user_schema_1.status = "trial"
        await user_db.update_user(user_schema_1)
        user = await user_db.get_user(user_schema_1.id)
        assert user.status == "trial"

    async def test_del_user(self, user_db: UserDao, before_add_user) -> None:
        """UserDao.del_user"""
        with pytest.raises(InvalidParameterFormat):
            await user_db.del_user(user_schema_1)

        await user_db.get_user(user_schema_1.id)
        await user_db.del_user(user_schema_1.id)

        with pytest.raises(UserNotFound):
            await user_db.get_user(user_schema_1.id)

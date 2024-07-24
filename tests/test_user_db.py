# import pytest
#
# from database.exceptions import InvalidParameterFormat, UserNotFound, InstanceAlreadyExists
# from database.models.user_model import UserDao, UserStatusValues
# from database.models.order_model import OrderStatusValues
#
# from pydantic import ValidationError
#
# from tests.schemas import user_schema_1, user_schema_2
#
#
# class TestUserDb:
#     async def test_get_user(self, user_db: UserDao, before_add_user) -> None:
#         """UserDao.get_user"""
#         with pytest.raises(InvalidParameterFormat):
#             await user_db.get_user(str(user_schema_1.id))
#
#         with pytest.raises(UserNotFound):
#             await user_db.get_user(user_schema_1.id + 1)
#
#         user = await user_db.get_user(user_schema_1.id)
#         assert user == user_schema_1
#
#     async def test_get_users(self, user_db: UserDao, before_add_two_users) -> None:
#         """UserDao.get_users"""
#         users = await user_db.get_users()
#         assert users[0] == user_schema_1
#         assert users[1] == user_schema_2
#
#     async def test_add_user(self, user_db: UserDao, before_add_user) -> None:
#         """UserDao.add_user"""
#         with pytest.raises(InvalidParameterFormat):
#             await user_db.add_user(1)
#
#         with pytest.raises(InstanceAlreadyExists):
#             await user_db.add_user(user_schema_1)
#
#         await user_db.add_user(user_schema_2)
#         user = await user_db.get_user(user_schema_2.id)
#         assert user == user_schema_2
#
#     async def test_update_user(self, user_db: UserDao, before_add_user) -> None:
#         """UserDao.update_user"""
#         with pytest.raises(InvalidParameterFormat):
#             await user_db.update_user(1)
#
#         with pytest.raises(ValidationError):
#             user_schema_1.status = OrderStatusValues.BACKLOG
#             await user_db.update_user(user_schema_1)
#             await user_db.get_user(user_schema_1.id)
#
#         user_schema_1.status = UserStatusValues.TRIAL
#         await user_db.update_user(user_schema_1)
#         user = await user_db.get_user(user_schema_1.id)
#         assert user.status == UserStatusValues.TRIAL
#
#     async def test_del_user(self, user_db: UserDao, before_add_user) -> None:
#         """UserDao.del_user"""
#         with pytest.raises(InvalidParameterFormat):
#             await user_db.del_user(user_schema_1)
#
#         await user_db.get_user(user_schema_1.id)
#         await user_db.del_user(user_schema_1.id)
#
#         with pytest.raises(UserNotFound):
#             await user_db.get_user(user_schema_1.id)

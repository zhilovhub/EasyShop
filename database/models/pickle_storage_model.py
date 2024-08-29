import string
from random import choice

import cloudpickle
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, select, insert, delete, LargeBinary, BigInteger, String
from sqlalchemy.ext.asyncio import AsyncEngine

from database.exceptions.exceptions import KwargsException

from database.models import Base
from database.models.dao import Dao


class PickledDataNotFound(KwargsException):
    """Raised when provided uuid for pickled data not found in database"""


class PickledData(Base):
    __tablename__ = "pickle_storage"

    id = Column(String(length=15), primary_key=True)
    unique_for_user = Column(BigInteger, nullable=True)
    pickled = Column(LargeBinary, nullable=False)
    pickled_args = Column(LargeBinary, nullable=True)
    bot_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=True)


class PickledObjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(frozen=True, max_length=15, min_length=15)
    unique_for_user: int | None = None
    pickled: bytes
    pickled_args: bytes | None = None
    bot_id: int | None = None
    user_id: int | None = None

    def unpickle_callable(self) -> Any:
        return cloudpickle.loads(self.pickled)

    def unpickle_args(self) -> Any:
        return cloudpickle.loads(self.pickled_args)


def create_pickled_object(
    object_to_store: Any, args: dict[str, Any] | None = None, unique_for_user: int | None = None
) -> PickledObjectSchema:
    letters = string.ascii_letters + string.digits
    rand_id = "".join(choice(letters) for _ in range(15))
    return PickledObjectSchema(
        id=rand_id,
        pickled=cloudpickle.dumps(object_to_store),
        pickled_args=cloudpickle.dumps(args),
        unique_for_user=unique_for_user,
    )


class PickleStorageDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_pickled_object(self, object_id: str) -> PickledObjectSchema:
        """
        :param object_id: object_id to search
        :return: list of CategorySchema

        :raise PickledDataNotFound
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(PickledData).where(PickledData.id == object_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if raw_res is None:
            raise PickledDataNotFound(uuid=object_id)
        res = PickledObjectSchema.model_validate(raw_res)

        self.logger.debug(f"returning pickled data with uuid: {res.id}")

        return res

    @validate_call(validate_return=True)
    async def add_pickled_object(self, new_object: PickledObjectSchema):
        """
        :param new_object: pydantic model PickledObjectSchema with new object data
        """
        if new_object.unique_for_user:
            self.logger.info(
                f"unique data is adding, deleting all old data " f"with provided user id {new_object.unique_for_user}"
            )
            async with self.engine.begin() as conn:
                await conn.execute(
                    delete(PickledData).where(
                        PickledData.unique_for_user == new_object.unique_for_user  # noqa
                    )
                )

        async with self.engine.begin() as conn:
            await conn.execute(insert(PickledData).values(new_object.model_dump()))

        self.logger.debug(f"add pickled data with uuid: {new_object.id}")

    @validate_call
    async def delete_pickled_object(self, object_id: str) -> None:
        """
        Deletes the pickled object from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(PickledData).where(PickledData.id == object_id))

        self.logger.debug(f"delete pickled data with uuid: {object_id}")

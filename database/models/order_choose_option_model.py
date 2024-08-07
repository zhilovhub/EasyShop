from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, BigInteger, String, ForeignKey, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.exceptions.exceptions import KwargsException
from database.models.order_option_model import OrderOption
from logs.config import extra_params


class OrderChooseOptionNotFoundError(KwargsException):
    """Raised when provided choose order option not found in database"""


class OrderChooseOption(Base):
    __tablename__ = "order_choose_options"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_option_id = Column(ForeignKey(OrderOption.id, ondelete="CASCADE"), nullable=False)
    choose_option_name = Column(String, nullable=False)


class OrderChooseOptionSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_option_id: int = Field(frozen=True)
    choose_option_name: str


class OrderChooseOptionSchema(OrderChooseOptionSchemaWithoutId):
    id: int = Field(frozen=True)


class OrderChooseOptionDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_choose_options(self, order_option_id: int) -> list[OrderChooseOptionSchema]:
        """
        :param order_option_id: order_option_id from search
        :return: list of OrderChooseOptionSchema
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(OrderChooseOption).where(OrderChooseOption.order_option_id == order_option_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for choose_option in raw_res:
            res.append(OrderChooseOptionSchema.model_validate(choose_option))

        self.logger.debug(
            f"order_option_id={order_option_id}: has {len(res)} choose options",
            extra=extra_params(order_option_id=order_option_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_choose_option(self, choose_option_id: int) -> OrderChooseOptionSchema:
        """
        :param choose_option_id: choose_option_id
        :return: OrderChooseOptionSchema

        :raises OrderOptionNotFoundError: no choose option in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(OrderChooseOption).where(OrderChooseOption.id == choose_option_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise OrderChooseOptionNotFoundError(order_option_id=choose_option_id)

        res = OrderChooseOptionSchema.model_validate(res)
        self.logger.debug(
            f"choose_option_id={choose_option_id}: found choose option {res}",
            extra=extra_params(choose_option_id=choose_option_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_choose_option(self, new_choose_option: OrderChooseOptionSchemaWithoutId) -> int:
        """
        Adds new choose option

        :return: new choose_option_id
        """
        async with self.engine.begin() as conn:
            choose_option_id = (
                await conn.execute(insert(OrderChooseOption).values(new_choose_option.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"choose_option_id={choose_option_id}: new added choose option {new_choose_option}",
            extra=extra_params(order_option_id=new_choose_option.order_option_id, choose_option_id=choose_option_id)
        )

        return choose_option_id

    @validate_call(validate_return=True)
    async def update_choose_option(self, updated_choose_option: OrderChooseOptionSchema) -> None:
        """
        Updates choose option
        """
        order_option_id, choose_option_id = updated_choose_option.order_option_id, updated_choose_option.id
        await self.get_choose_option(choose_option_id)

        async with self.engine.begin() as conn:
            await conn.execute(
                update(OrderChooseOption).where(OrderChooseOption.id ==
                                                choose_option_id).values(updated_choose_option.model_dump())
            )

        self.logger.debug(
            f"choose_option_id={choose_option_id}: updated choose option {updated_choose_option}",
            extra=extra_params(order_option_id=order_option_id, choose_option_id=choose_option_id)
        )

    @validate_call
    async def delete_choose_option(self, choose_option_id: int) -> None:
        """
        Deletes the choose option from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(OrderChooseOption).where(OrderChooseOption.id == choose_option_id))

        self.logger.debug(
            f"choose_option_id={choose_option_id}: deleted choose option {choose_option_id}",
            extra=extra_params(choose_option_id=choose_option_id)
        )

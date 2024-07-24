from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import Column, BigInteger, String, Boolean, Integer, select, ForeignKey, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.exceptions.exceptions import KwargsException

from database.models import Base
from database.models.dao import Dao

# from bot.utils.message_texts import MessageTexts

from logs.config import extra_params

# TODO Create handle_exception_func
class OptionNotFoundError(KwargsException):
    """Raised when provided option not found in database"""


class Option(Base):
    __tablename__ = "options"

    id = Column(BigInteger, primary_key=True)
    start_msg = Column(String, nullable=False)
    default_msg = Column(String, nullable=False)
    post_order_msg = Column(String, nullable=True)
    auto_reduce = Column(Boolean, nullable=False, default=False)
    bg_color = Column(String, nullable=True)
    web_app_button = Column(String, nullable=False)


class OptionSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_msg: str
    default_msg: str
    post_order_msg: str | None = None
    auto_reduce: bool = False
    bg_color: str | None = None
    web_app_button: str


class OptionSchema(OptionSchemaWithoutId):
    id: int = Field(frozen=True)


class OptionDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_options(self) -> list[OptionSchema]:
        """
        :return: list of OptionSchema
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Option))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for option in raw_res:
            res.append(OptionSchema.model_validate(option))

        self.logger.debug(
            f"Found {len(res)} options",
            extra=extra_params()
        )

        return res

    @validate_call(validate_return=True)
    async def get_option(self, option_id: int) -> OptionSchema:
        """
        :param option_id: option_id
        :return: OptionSchema

        :raises OptionNotFoundError: no option in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Option).where(Option.id == option_id)
            )
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise OptionNotFoundError(option_id=option_id)

        res = OptionSchema.model_validate(res)
        self.logger.debug(
            f"option_id={option_id}: found option {res}",
            extra=extra_params(option_id=option_id)
        )

        return res

    @validate_call(validate_return=True)
    async def add_option(self, new_option: OptionSchemaWithoutId) -> int:
        """
        Adds new option to database
        """
        async with self.engine.begin() as conn:
            opt_id = (await conn.execute(insert(Option).values(new_option.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"option_id={opt_id}: new added option {new_option}",
            extra=extra_params(option_id=opt_id)
        )

        return opt_id

    @validate_call(validate_return=True)
    async def update_option(self, updated_option: OptionSchema) -> None:
        """
        Updates the option in database
        """
        option_id = updated_option.id
        await self.get_option(option_id)

        async with self.engine.begin() as conn:
            await conn.execute(
                update(Option).where(Option.id == option_id).values(updated_option.model_dump())
            )

        self.logger.debug(
            f"option_id={option_id}: updated option {updated_option}",
            extra=extra_params(option_id=option_id)
        )

    @validate_call
    async def delete_option(self, option_id: int) -> None:
        """
        Deletes the option from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(Option).where(Option.id == option_id))

        self.logger.debug(
            f"option_id={option_id}: deleted option {option_id}",
            extra=extra_params(option_id=option_id)
        )

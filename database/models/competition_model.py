import datetime
from typing import Optional

from pydantic import BaseModel, Field, validate_call, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, select, insert, delete, BOOLEAN, ForeignKeyConstraint, String, \
    DateTime, update
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.exceptions import InvalidParameterFormat
from database.models import Base
from database.models.bot_model import Bot
from database.models.channel_model import Channel
from database.models.dao import Dao
from logs.config import extra_params


class CompetitionNotFound(Exception):
    """Raised when provided Competition not found in database"""
    pass


class Competition(Base):
    __tablename__ = "competitions"

    competition_id = Column(BigInteger, autoincrement=True, primary_key=True)

    channel_id = Column(BigInteger, nullable=False)
    bot_id = Column(BigInteger, nullable=False)

    name = Column(String, default="-")
    description = Column(String)

    duration = Column(DateTime)
    end_date = Column(DateTime)

    button_url = Column(String)

    # If False - send messages to private chats
    to_channel = Column(BOOLEAN, default=True)

    # Media Files will be as another table
    # Conditionals will be as another table
    # Analytic will be as another table

    # Randomizer will be as another table
    has_randomizer = Column(BOOLEAN, default=False)


    __table_args__ = (
        ForeignKeyConstraint(
            ["channel_id", "bot_id"],
            [f"{Channel.__tablename__}.channel_id", f"{Channel.__tablename__}.bot_id"],
            ondelete="CASCADE"
        ),
    )


class CompetitionSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: int = Field(frozen=True)
    bot_id: int = Field(frozen=True)

    name: str = "-"
    description: Optional[str | None] = None

    duration: Optional[datetime.datetime | None] = None
    end_date: Optional[datetime.datetime | None] = None

    button_url: Optional[str | None] = None

    to_channel: bool = True

    has_randomizer: bool = False


class CompetitionSchema(CompetitionSchemaWithoutId):
    competition_id: int = Field(frozen=True)


class CompetitionDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_competitions(self, channel_id: int, bot_id: int) -> list[CompetitionSchema]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(Competition).where(Competition.channel_id == channel_id, Competition.bot_id == bot_id)
            )
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for competition in raw_res:
            res.append(CompetitionSchema.model_validate(competition))

        self.logger.debug(
            f"channel_id={channel_id}: has {res} channels",
            extra=extra_params(channel_id=channel_id, bot_id=bot_id)
        )

        return res

    @validate_call(validate_return=True)
    async def get_competition(self, competition_id: int) -> CompetitionSchema:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Competition).where(Competition.competition_id == competition_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if not raw_res:
            raise CompetitionNotFound

        self.logger.debug(
            f"competition_id={competition_id}: is found",
            extra=extra_params(competition_id=competition_id)
        )

        return CompetitionSchema.model_validate(raw_res)

    @validate_call
    async def add_competition(self, new_competition: CompetitionSchemaWithoutId) -> int:
        if type(new_competition) != CompetitionSchemaWithoutId:
            raise InvalidParameterFormat("new_competition must be type of CompetitionSchema")

        async with self.engine.begin() as conn:
            competition_id = (await conn.execute(insert(Competition).values(new_competition.model_dump()))).inserted_primary_key[0]

        self.logger.debug(
            f"channel_id={new_competition.channel_id}: {competition_id} is added",
            extra=extra_params(competition_id=competition_id, channel_id=new_competition.channel_id, bot_id=new_competition.bot_id)
        )

        return competition_id

    @validate_call
    async def update_competition(self, updated_competition: CompetitionSchema):
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Competition).where(
                    Competition.competition_id == updated_competition.competition_id
                ).values(updated_competition.model_dump())
            )

        self.logger.debug(
            f"channel_id={updated_competition.channel_id}: {updated_competition.competition_id} is updated",
            extra=extra_params(competition_id=updated_competition.competition_id, channel_id=updated_competition.channel_id,
                               bot_id=updated_competition.bot_id)
        )

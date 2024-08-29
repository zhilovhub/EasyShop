from pydantic import BaseModel, ConfigDict, Field, validate_call

from sqlalchemy import BOOLEAN, Column, BigInteger, String, ForeignKey, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from database.models import Base
from database.models.dao import Dao
from database.models.user_model import User
from database.exceptions.exceptions import KwargsException
from logs.config import extra_params


class ReferralInviteNotFoundError(KwargsException):
    """Raised when provided referral invite not found in database"""


class ReferralInviteModel(Base):
    __tablename__ = "referral_invites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    referral_deep_link = Column(String, nullable=True)
    came_from = Column(ForeignKey(User.user_id), nullable=True)
    paid = Column(BOOLEAN, nullable=False)


class ReferralInviteSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(frozen=True)
    referral_deep_link: str | None = None
    came_from: int | None = None
    paid: bool = False


class ReferralInviteSchema(ReferralInviteSchemaWithoutId):
    id: int = Field(frozen=True)


class ReferralInviteDao(Dao):
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_invites(self) -> list[ReferralInviteSchema]:
        """
        :return: All invitations
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ReferralInviteModel))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for referral_invite in raw_res:
            res.append(ReferralInviteSchema.model_validate(referral_invite))

        self.logger.debug(f"There are {len(res)} referral invitations")

        return res

    @validate_call(validate_return=True)
    async def get_invite_by_user_id(self, user_id: int) -> ReferralInviteSchema:
        """
        :param user_id: user_id from search
        :return: ReferralInviteSchema

        :raises ReferralInviteNotFoundError: no referral invite in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ReferralInviteModel).where(ReferralInviteModel.user_id == user_id))
        await self.engine.dispose()

        raw_res = raw_res.fetchone()
        if raw_res is None:
            raise ReferralInviteNotFoundError(user_id=user_id)

        return ReferralInviteSchema.model_validate(raw_res)

    @validate_call(validate_return=True)
    async def get_invite(self, invite_id: int) -> ReferralInviteSchema:
        """
        :param invite_id: invite_id
        :return: ReferralInviteSchema

        :raises ReferralInviteNotFoundError: no referral invite in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(ReferralInviteModel).where(ReferralInviteModel.id == invite_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise ReferralInviteNotFoundError(invite_id=invite_id)

        res = ReferralInviteSchema.model_validate(res)
        self.logger.debug(
            f"invite_id={invite_id}: found referral invite {res}",
            extra=extra_params(invite_id=invite_id),
        )

        return res

    @validate_call(validate_return=True)
    async def add_invite(self, new_invite: ReferralInviteSchemaWithoutId) -> int:
        """
        Adds a new referral invite to the database.

        :param new_invite: A ReferralInviteSchemaWithoutId object representing the new invite.
        :return: The ID of the newly added invite.

        :raises IntegrityError: If the invite cannot be added due to a database integrity error.
        """
        async with self.engine.begin() as conn:
            invite_id = (
                await conn.execute(insert(ReferralInviteModel).values(new_invite.model_dump()))
            ).inserted_primary_key[0]

        self.logger.debug(
            f"invite_id={invite_id}: new added referral invite {new_invite}",
            extra=extra_params(user_id=new_invite.user_id, invite_id=invite_id),
        )

        return invite_id

    @validate_call(validate_return=True)
    async def update_invite(self, updated_invite: ReferralInviteSchema) -> None:
        """
        Updates an existing referral invite in the database.

        :param updated_invite: A ReferralInviteSchema object representing the updated invite.
        :return: None

        :raises ReferralInviteNotFoundError: no referral invite in db
        """
        user_id, invite_id = updated_invite.user_id, updated_invite.id
        await self.get_invite(invite_id)

        async with self.engine.begin() as conn:
            await conn.execute(
                update(ReferralInviteModel)
                .where(ReferralInviteModel.id == invite_id)
                .values(updated_invite.model_dump())
            )

        self.logger.debug(
            f"invite_id={invite_id}: updated referral invite {updated_invite}",
            extra=extra_params(user_id=user_id, invite_id=invite_id),
        )

    @validate_call
    async def delete_invite(self, invite_id: int) -> None:
        """
        Deletes the referral invite from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(ReferralInviteModel).where(ReferralInviteModel.id == invite_id))

        self.logger.debug(
            f"invite_id={invite_id}: deleted referral invite {invite_id}",
            extra=extra_params(invite_id=invite_id),
        )

from datetime import datetime

import pytest

from bot.exceptions import InvalidParameterFormat, BotNotFound, InstanceAlreadyExists
from database.models.bot_model import BotDao, BotSchema, BotSchemaWithoutId

bot_schema_without_id_1 = BotSchemaWithoutId(
    token="1000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=1,
    locale=""
)
bot_schema_without_id_2 = BotSchemaWithoutId(
    token="2000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=2,
    locale=""
)
bot_schema_1 = BotSchema(
    bot_id=1,
    token="1000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=1,
    locale=""
)
bot_schema_2 = BotSchema(
    bot_id=2,
    token="2000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=2,
    locale=""
)


@pytest.fixture
async def before_add_bot(bot_db: BotDao) -> None:
    await bot_db.add_bot(bot_schema_without_id_1)


@pytest.fixture
async def before_add_two_bots(bot_db: BotDao) -> None:
    await bot_db.add_bot(bot_schema_without_id_1)
    await bot_db.add_bot(bot_schema_without_id_2)


class TestBotDb:
    async def test_get_bot(self, bot_db: BotDao, before_add_bot) -> None:
        """BotDao.get_bot"""
        with pytest.raises(InvalidParameterFormat):
            await bot_db.get_bot(str(bot_schema_1.bot_id))

        with pytest.raises(BotNotFound):
            await bot_db.get_bot(bot_schema_1.bot_id + 1)

        bot = await bot_db.get_bot(1)
        assert bot == bot_schema_1

    async def test_get_bot_by_token(self, bot_db: BotDao, before_add_bot) -> None:
        """BotDao.get_bot"""
        with pytest.raises(InvalidParameterFormat):
            await bot_db.get_bot_by_token("100000A000:AaA5AaAaAaAaAaAaAaAaAaAaAaAaAaAaA")

        with pytest.raises(BotNotFound):
            await bot_db.get_bot_by_token("3000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA")

        bot = await bot_db.get_bot_by_token(bot_schema_1.token)
        assert bot == bot_schema_1

    async def test_get_bots(self, bot_db: BotDao, before_add_two_bots) -> None:
        """BotDao.get_bots"""
        bots = await bot_db.get_bots()
        assert bots[0] == bot_schema_1
        assert bots[1] == bot_schema_2

    async def test_add_bot(self, bot_db: BotDao, before_add_bot) -> None:
        """BotDao.add_bot"""
        with pytest.raises(InvalidParameterFormat):
            await bot_db.add_bot(bot_schema_1)

        with pytest.raises(InstanceAlreadyExists):
            await bot_db.add_bot(bot_schema_without_id_1)

        bot_id = await bot_db.add_bot(bot_schema_without_id_2)
        bot = await bot_db.get_bot(bot_id)
        assert bot.created_at == bot_schema_2.created_at and \
               bot.token == bot_schema_2.token and bot.bot_id == 3 and \
               bot_schema_2.bot_id == bot.bot_id - 1

    async def test_update_bot(self, bot_db: BotDao, before_add_bot) -> None:
        """BotDao.update_bot"""
        with pytest.raises(InvalidParameterFormat):
            await bot_db.update_bot(1)

        bot_schema_1.status = "new_status"
        await bot_db.update_bot(bot_schema_1)
        bot = await bot_db.get_bot(bot_schema_1.bot_id)
        assert bot.status == "new_status"

    async def test_del_bot(self, bot_db: BotDao, before_add_bot) -> None:
        """BotDao.del_bot"""
        with pytest.raises(InvalidParameterFormat):
            await bot_db.del_bot(bot_schema_1)

        await bot_db.get_bot(bot_schema_1.bot_id)
        await bot_db.del_bot(bot_schema_1.bot_id)

        with pytest.raises(BotNotFound):
            await bot_db.get_bot(bot_schema_1.bot_id)

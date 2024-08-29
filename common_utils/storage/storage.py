from abc import ABC
from typing import Optional, Dict, Any

from sqlalchemy import MetaData
from sqlalchemy import Table, Column, String, JSON
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import create_async_engine

from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

from logs.config import logger


class AlchemyStorageAsync(BaseStorage, ABC):
    def __init__(self, db_url: str, table_name: str):
        self.table_name = table_name
        self.db_url = db_url
        self.metadata = MetaData()
        self.storage_table = Table(
            self.table_name,
            self.metadata,
            Column("id", String(70), primary_key=True),  # user_id#chat_id  example: 11111111#22222222
            Column("state", String(55)),
            Column("data", JSON),
        )
        self.engine = create_async_engine(f"{db_url}")

    async def connect(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)
        await self.engine.dispose()
        logger.info("storage db connected.")

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        if state is None:
            await self.clear_state(key)
            return None
        if await self.get_state(key):
            async with self.engine.begin() as conn:
                await conn.execute(
                    update(self.storage_table)
                    .where(self.storage_table.c.id == f"{key.user_id}#{abs(key.chat_id)}")
                    .values(state=state.state, data={})
                )
            await self.engine.dispose()
            logger.debug(f"updated state for user {key.user_id} in chat {key.chat_id} to state {state.state}.")
            return None
        async with self.engine.begin() as conn:
            await conn.execute(
                insert(self.storage_table).values(id=f"{key.user_id}#{abs(key.chat_id)}", state=state.state, data={})
            )
        await self.engine.dispose()
        logger.debug(f"set state for user {key.user_id} in chat {key.chat_id} to state {state.state}.")

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(self.storage_table).where(self.storage_table.c.id == f"{key.user_id}#{abs(key.chat_id)}")
            )
        await self.engine.dispose()
        res = raw_res.fetchone()
        if res is None or res.state in ("None", None):
            await self.clear_state(key)
            return None
        return res.state

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                update(self.storage_table)
                .where(self.storage_table.c.id == f"{key.user_id}#{abs(key.chat_id)}")
                .values(data=data)
            )
        await self.engine.dispose()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(
                select(self.storage_table).where(self.storage_table.c.id == f"{key.user_id}#{abs(key.chat_id)}")
            )
        await self.engine.dispose()
        res = raw_res.fetchone()
        if res is None or res.state == "None":
            return {}
        return res.data

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        _data = await self.get_data(key)
        _data.update(data)
        async with self.engine.begin() as conn:
            await conn.execute(
                update(self.storage_table)
                .where(self.storage_table.c.id == f"{key.user_id}#{abs(key.chat_id)}")
                .values(data=_data)
            )
        await self.engine.dispose()
        return _data

    async def clear_state(self, key: StorageKey) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                delete(self.storage_table).where(self.storage_table.c.id == f"{key.user_id}#{abs(key.chat_id)}")
            )
        await self.engine.dispose()
        logger.debug(f"cleared state for user {key.user_id} in chat {key.chat_id}.")
        return None

    async def clear_table(self) -> None:
        """
        Often used in tests
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(self.storage_table))
        await self.engine.dispose()

        logger.debug(f"Table {self.storage_table.name} has been cleared")

    async def close(self) -> None:
        pass

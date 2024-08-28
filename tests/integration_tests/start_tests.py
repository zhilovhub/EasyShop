import datetime
from typing import Optional

from aiogram import Dispatcher, Bot
from aiogram.types import User, Chat, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard
from bot.states import States
from bot.keyboards.start_keyboards import ShortDescriptionKeyboard
from bot.utils import MessageTexts

from database.models.user_model import UserDao, UserStatusValues, UserSchema

from common_utils.storage.storage import AlchemyStorageAsync

from tests.mock_objects.updates import MockMessage


class TestStartCommand:
    async def test_start_command_as_new_user(
        self,
        user_db: UserDao,
        tg_main_bot: Bot,
        dispatcher: Dispatcher,
        main_storage: AlchemyStorageAsync,
        tg_user: User,
        tg_chat: Chat,
    ):
        messages = await _propagate_message_event(
            tg_main_bot, dispatcher, main_storage, tg_user, tg_chat, text="/start", raw_state=None
        )

        assert len(messages) == 3

        self._check_start_default_message(messages)

        user_from_database = await user_db.get_user(tg_user.id)
        assert user_from_database.status == UserStatusValues.TRIAL
        assert 2 < (user_from_database.subscribed_until - datetime.datetime.now()).days < 32
        assert len(user_from_database.subscription_job_ids) == 3

        user_raw_state = await main_storage.get_state(_get_storage_key(tg_user))
        assert user_raw_state == States.WAITING_FOR_TOKEN.state

    async def test_start_command_without_subscription(
        self,
        add_subscribe_ended_user: UserSchema,
        user_db: UserDao,
        tg_main_bot: Bot,
        dispatcher: Dispatcher,
        main_storage: AlchemyStorageAsync,
        tg_user: User,
        tg_chat: Chat,
    ):
        messages = await _propagate_message_event(
            tg_main_bot, dispatcher, main_storage, tg_user, tg_chat, text="/start", raw_state=States.SUBSCRIBE_ENDED.state
        )

        assert len(messages) == 4

        self._check_start_default_message(messages)

        assert messages[3].html_text == MessageTexts.SUBSCRIBE_END_NOTIFY.value
        assert messages[3].reply_markup.model_dump() == InlineSubscriptionContinueKeyboard.get_keyboard(None).model_dump()

        user_from_database = await user_db.get_user(tg_user.id)
        assert user_from_database.status == UserStatusValues.SUBSCRIPTION_ENDED
        assert user_from_database.subscribed_until < datetime.datetime.now()
        assert not user_from_database.subscription_job_ids

        user_raw_state = await main_storage.get_state(_get_storage_key(tg_user))
        assert user_raw_state == States.SUBSCRIBE_ENDED.state

    @staticmethod
    def _check_start_default_message(messages: list[Message]) -> None:
        assert messages[0].forward_from_message_id == 4
        assert messages[0].reply_markup is None

        assert messages[1].forward_from_message_id == 6
        assert messages[1].reply_markup is None

        assert messages[2].forward_from_message_id is None
        assert messages[2].reply_markup.model_dump() == ShortDescriptionKeyboard.get_keyboard().model_dump()


def _get_storage_key(tg_user: User) -> StorageKey:
    """Returns Storage Key to get states from the storage"""
    return StorageKey(bot_id=0, chat_id=tg_user.id, user_id=tg_user.id)


async def _propagate_message_event(
    tg_main_bot: Bot,
    dispatcher: Dispatcher,
    main_storage: AlchemyStorageAsync,
    tg_user: User,
    tg_chat: Chat,
    text: str,
    raw_state: Optional[str],
) -> list[Message]:
    """
    Method to propagate message event ot the bot

    :return: sorted (by message_id) list of Message object
    """
    result: list[Message] = await dispatcher.propagate_event(
        update_type="message",
        event=MockMessage(bot=tg_main_bot, chat=tg_chat, from_user=tg_user, text=text),
        bot=tg_main_bot,
        event_from_user=tg_user,
        state=FSMContext(
            storage=main_storage, key=StorageKey(bot_id=tg_main_bot.id, chat_id=tg_chat.id, user_id=tg_chat.id)
        ),
        raw_state=raw_state,
    )

    return sorted(result, key=lambda x: x.message_id)

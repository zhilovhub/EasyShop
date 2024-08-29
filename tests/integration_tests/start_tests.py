import datetime
from typing import Optional, Any

from aiogram import Dispatcher, Bot
from aiogram.types import User, Chat, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from bot.utils import MessageTexts
from bot.states import States
from bot.keyboards.start_keyboards import ShortDescriptionKeyboard
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard
from bot.keyboards.subscription_keyboards import InlineSubscriptionContinueKeyboard

from common_utils.storage.storage import AlchemyStorageAsync
from common_utils.keyboards.keyboards import InlineBotMenuKeyboard
from common_utils.keyboards.remove_keyboard import OurReplyKeyboardRemove

from database.models.bot_model import BotSchema
from database.models.user_model import UserDao, UserStatusValues, UserSchema
from database.models.option_model import OptionSchema

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

        assert ReplyBotMenuKeyboard.has_been_triggered
        assert not OurReplyKeyboardRemove.has_been_triggered

        user_from_database = await user_db.get_user(tg_user.id)
        assert user_from_database.status == UserStatusValues.TRIAL
        assert 2 < (user_from_database.subscribed_until - datetime.datetime.now()).days < 32
        assert len(user_from_database.subscription_job_ids) == 3

        storage_key = _get_storage_key(tg_user)
        user_raw_state = await main_storage.get_state(storage_key)
        assert user_raw_state == States.WAITING_FOR_TOKEN.state

        user_state_data = await main_storage.get_data(storage_key)
        assert user_state_data == {"bot_id": -1}

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
            tg_main_bot,
            dispatcher,
            main_storage,
            tg_user,
            tg_chat,
            text="/start",
            raw_state=States.SUBSCRIBE_ENDED.state,
        )

        assert len(messages) == 5

        self._check_start_default_message(messages)

        assert messages[3].html_text == MessageTexts.SUBSCRIBE_END_NOTIFY.value
        assert (
            messages[3].reply_markup.model_dump() == InlineSubscriptionContinueKeyboard.get_keyboard(None).model_dump()
        )

        assert messages[4].html_text == MessageTexts.SUBSCRIBE_END_NOTIFY_PART_2.value

        assert not ReplyBotMenuKeyboard.has_been_triggered
        assert OurReplyKeyboardRemove.has_been_triggered

        user_from_database = await user_db.get_user(tg_user.id)
        assert user_from_database.status == UserStatusValues.SUBSCRIPTION_ENDED
        assert user_from_database.subscribed_until < datetime.datetime.now()
        assert not user_from_database.subscription_job_ids

        storage_key = _get_storage_key(tg_user)
        user_raw_state = await main_storage.get_state(storage_key)
        assert user_raw_state == States.SUBSCRIBE_ENDED.state

        user_state_data = await main_storage.get_data(storage_key)
        assert user_state_data == {"bot_id": -1}

    async def test_start_command_with_bot(
        self,
        add_subscribed_user: UserSchema,
        add_option: OptionSchema,
        add_bot: BotSchema,
        user_db: UserDao,
        tg_main_bot: Bot,
        tg_custom_bot: Bot,
        dispatcher: Dispatcher,
        main_storage: AlchemyStorageAsync,
        tg_user: User,
        tg_chat: Chat,
    ):
        messages = await _propagate_message_event(
            tg_main_bot,
            dispatcher,
            main_storage,
            tg_user,
            tg_chat,
            text="/start",
            raw_state=States.EDITING_CUSTOM_COLOR.state,
        )

        assert len(messages) == 5

        self._check_start_default_message(messages)

        assert messages[3].html_text == MessageTexts.ALREADY_HAS_BOT.value

        custom_bot_username = (await tg_custom_bot.get_me()).username
        assert messages[4].html_text == MessageTexts.BOT_MENU_MESSAGE.value.format(custom_bot_username)
        assert (
            messages[4].reply_markup.model_dump()
            == (await InlineBotMenuKeyboard.get_keyboard(add_bot.bot_id, tg_user.id)).model_dump()
        )

        assert ReplyBotMenuKeyboard.has_been_triggered
        assert not OurReplyKeyboardRemove.has_been_triggered

        user_from_database = await user_db.get_user(tg_user.id)
        assert user_from_database == add_subscribed_user

        storage_key = _get_storage_key(tg_user)
        user_raw_state = await main_storage.get_state(storage_key)
        assert user_raw_state == States.BOT_MENU.state

        user_state_data = await main_storage.get_data(storage_key)
        assert user_state_data == {"bot_id": add_bot.bot_id}

    async def test_start_command_without_bot(
        self,
        add_subscribed_user: UserSchema,
        user_db: UserDao,
        tg_main_bot: Bot,
        dispatcher: Dispatcher,
        main_storage: AlchemyStorageAsync,
        tg_user: User,
        tg_chat: Chat,
    ):
        messages = await _propagate_message_event(
            tg_main_bot,
            dispatcher,
            main_storage,
            tg_user,
            tg_chat,
            text="/start",
            raw_state=None,
        )

        assert len(messages) == 4

        self._check_start_default_message(messages)

        assert messages[3].html_text == MessageTexts.HAS_NO_BOT_YET.value

        assert not ReplyBotMenuKeyboard.has_been_triggered
        assert OurReplyKeyboardRemove.has_been_triggered

        user_from_database = await user_db.get_user(tg_user.id)
        assert user_from_database == add_subscribed_user

        storage_key = _get_storage_key(tg_user)
        user_raw_state = await main_storage.get_state(storage_key)
        assert user_raw_state == States.WAITING_FOR_TOKEN.state

        user_state_data = await main_storage.get_data(storage_key)
        assert user_state_data == {"bot_id": -1}

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
    result: tuple[Any, list[Message]] = await dispatcher.propagate_event(
        update_type="message",
        event=MockMessage(bot=tg_main_bot, chat=tg_chat, from_user=tg_user, text=text),
        bot=tg_main_bot,
        event_from_user=tg_user,
        state=FSMContext(
            storage=main_storage, key=StorageKey(bot_id=tg_main_bot.id, chat_id=tg_chat.id, user_id=tg_chat.id)
        ),
        raw_state=raw_state,
    )

    return sorted(result[1], key=lambda x: x.message_id)

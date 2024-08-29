from typing import Callable, Dict, Any, Awaitable

import cloudpickle
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, InlineQuery

from common_utils.keyboards.keyboards import FirstTimeInlineSelectLanguageKb

from database.enums.language import AVAILABLE_LANGUAGES, UserLanguageValues
from database.models.custom_bot_user_model import CustomBotUserNotFoundError
from database.config import bot_db, option_db, custom_bot_user_db, pickle_store_db, user_db

from common_utils.message_texts import MessageTexts as CommonMessageTexts
from database.models.pickle_storage_model import create_pickled_object
from database.models.user_model import UserNotFoundError

from logs.config import logger


class LangCheckMiddleware(BaseMiddleware):
    def __init__(self, from_main_bot: bool = True) -> None:
        self.from_main_bot = from_main_bot

    async def __call__(
        self,
        handler: Callable[[CallbackQuery | Message, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message | InlineQuery,
        data: Dict[str, Any],
    ) -> Any:
        try:
            if not self.from_main_bot:
                bot = await bot_db.get_bot_by_token(event.bot.token)
                bot_options = await option_db.get_option(bot.options_id)
                langs = bot_options.languages

                try:
                    custom_bot_user = await custom_bot_user_db.get_custom_bot_user(bot.bot_id, event.from_user.id)
                    user_lang = custom_bot_user.user_language
                except CustomBotUserNotFoundError:
                    user_lang = None
            else:
                langs = AVAILABLE_LANGUAGES
                try:
                    user = await user_db.get_user(event.from_user.id)
                    user_lang = user.locale
                except UserNotFoundError:
                    user_lang = None

            # if only one language is added to bot options return handler with that language
            # ignoring user selected lang in custom bot user schema
            if len(langs) == 1:
                data["lang"] = langs[0]
                if user_lang:
                    if not self.from_main_bot:
                        custom_bot_user.user_language = langs[0]  # noqa
                        await custom_bot_user_db.update_custom_bot_user(custom_bot_user)
                    else:
                        user.locale = langs[0]  # noqa
                        await user_db.update_user(user)
                return await handler(event, data)

            # if user is not created or user don't have selected lang, choosing lang by telegram app default
            if not user_lang:
                tg_user_lang = event.from_user.language_code
                match tg_user_lang:
                    case "ru":
                        user_lang = UserLanguageValues.RUSSIAN
                    case "he":
                        user_lang = UserLanguageValues.HEBREW
                    case "en":
                        user_lang = UserLanguageValues.ENGLISH
                    case _:
                        user_lang = "unsupported"

            # if selected user language not in bots language available list or unsupported, ask a language to choose
            if user_lang not in langs:
                data_to_pickle = data.copy()
                # добавятся актуальные после нажатия на инлайн кнопку
                del data_to_pickle["event_from_user"]
                del data_to_pickle["event_chat"]
                del data_to_pickle["session"]
                del data_to_pickle["bot"]
                del data_to_pickle["fsm_storage"]
                del data_to_pickle["state"]
                del data_to_pickle["event_router"]

                to_validate = {}

                for k in data_to_pickle:
                    try:
                        cloudpickle.dumps(data[k])
                    except Exception as ex:
                        logger.debug(f"error while pickling {k} dumping... err reason: {ex}")
                        to_validate[k] = type(data_to_pickle[k])
                        data_to_pickle[k] = data_to_pickle[k].model_dump()

                data_to_pickle["to_validate"] = to_validate
                data_to_pickle["event_type_to_validate"] = type(event)

                pickled_handler = create_pickled_object(
                    handler,
                    {"event": event.model_dump(), "data": data_to_pickle},
                    unique_for_user=event.from_user.id,
                )
                await pickle_store_db.add_pickled_object(pickled_handler)
                await data["bot"].send_message(
                    chat_id=event.from_user.id,
                    **CommonMessageTexts.get_first_select_language_message(
                        user_lang if user_lang != "unsupported" else UserLanguageValues.ENGLISH
                    ).as_kwargs(),
                    reply_markup=FirstTimeInlineSelectLanguageKb.get_keyboard(
                        pickled_uuid=pickled_handler.id,
                        languages=langs,
                    ),
                )
                # handler will execute after user select language on keyboard
                return

            data["lang"] = user_lang

            return await handler(event, data)
        except Exception as e:
            logger.error("error while getting user language")
            # if error return english as default language to handler
            data["lang"] = UserLanguageValues.ENGLISH
            await handler(event, data)
            raise e

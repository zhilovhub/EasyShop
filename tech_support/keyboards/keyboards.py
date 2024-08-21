from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from common_utils.keyboards.keyboard_utils import callback_json_validator


class ReplyCancelKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            CANCEL = "🚫 Отменить отправку"
            CANCEL_ENG = "🚫 Cancel sending"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cancel", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard(lang: str) -> ReplyKeyboardMarkup:
        # TODO replace lang to lang enum from db (translate_shop branch)
        actions = ReplyCancelKeyboard.Callback.ActionEnum

        def _get_button_text():
            match lang:
                case "eng":
                    return actions.CANCEL_ENG.value
                case "ru" | _:
                    return actions.CANCEL.value

        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=_get_button_text())]], resize_keyboard=True)


class MainUserKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ASK_QUESTION = "ask"
            FAQ = "faq"
            SUGGEST = "suggest"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="main", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return MainUserKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            MainUserKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(lang: str) -> InlineKeyboardMarkup:
        # TODO replace lang to lang enum from db (translate_shop branch)
        actions = MainUserKeyboard.Callback.ActionEnum

        def _get_button_text(button: actions, language: str):
            match language:
                case "eng":
                    match button:
                        case actions.ASK_QUESTION:
                            return "📝 Ask a question"
                        case actions.FAQ:
                            return "📋 FAQ"
                        case actions.SUGGEST:
                            return "🆕 Suggest feature"
                case "ru" | _:
                    match button:
                        case actions.ASK_QUESTION:
                            return "📝 Задать вопрос"
                        case actions.FAQ:
                            return "📋 Часто задаваемые вопросы"
                        case actions.SUGGEST:
                            return "🆕 Предложить обновление"

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.ASK_QUESTION, lang),
                        callback_data=MainUserKeyboard.callback_json(actions.ASK_QUESTION),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.FAQ, lang),
                        callback_data=MainUserKeyboard.callback_json(actions.FAQ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.SUGGEST, lang),
                        callback_data=MainUserKeyboard.callback_json(actions.SUGGEST),
                    )
                ],
            ],
        )


class FAQKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            PAYMENT = "payment"
            ADMINS = "admins"
            EXPORT_PRODUCT = "export"
            CUSTOMIZATION = "customization"
            RESTRICTIONS = "restrictions"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="faq", frozen=True)
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum) -> str:
        return FAQKeyboard.Callback(a=action).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            FAQKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(lang: str) -> InlineKeyboardMarkup:
        # TODO replace lang to lang enum from db (translate_shop branch)
        actions = FAQKeyboard.Callback.ActionEnum

        def _get_button_text(button: actions, language: str):
            match language:
                case "eng":
                    match button:
                        case actions.PAYMENT:
                            return "💳 About Payments"
                        case actions.ADMINS:
                            return "👥 Add admins"
                        case actions.RESTRICTIONS:
                            return "🚫 Service restrictions"
                        case actions.CUSTOMIZATION:
                            return "🎨 Customization"
                        case actions.EXPORT_PRODUCT:
                            return "🔽 Export products"
                case "ru" | _:
                    match button:
                        case actions.PAYMENT:
                            return "💳 Платежи"
                        case actions.ADMINS:
                            return "👥 Добавить админов"
                        case actions.RESTRICTIONS:
                            return "🚫 Ограничения"
                        case actions.CUSTOMIZATION:
                            return "🎨 Кастомизация"
                        case actions.EXPORT_PRODUCT:
                            return "🔽 Экспорт товаров"

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.PAYMENT, lang),
                        callback_data=FAQKeyboard.callback_json(actions.PAYMENT),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.ADMINS, lang),
                        callback_data=FAQKeyboard.callback_json(actions.ADMINS),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.CUSTOMIZATION, lang),
                        callback_data=FAQKeyboard.callback_json(actions.CUSTOMIZATION),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.RESTRICTIONS, lang),
                        callback_data=FAQKeyboard.callback_json(actions.RESTRICTIONS),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_get_button_text(actions.EXPORT_PRODUCT, lang),
                        callback_data=FAQKeyboard.callback_json(actions.EXPORT_PRODUCT),
                    )
                ],
            ],
        )


class AnswerKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            ANSWER = "ans"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="ans", frozen=True)
        user_id: int
        msg_id: int
        a: ActionEnum

    @staticmethod
    @callback_json_validator
    def callback_json(action: Callback.ActionEnum, user_id: int, msg_id: int) -> str:
        return AnswerKeyboard.Callback(a=action, user_id=user_id, msg_id=msg_id).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            AnswerKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(user_id: int, msg_id: int) -> InlineKeyboardMarkup:
        actions = AnswerKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Ответить", callback_data=AnswerKeyboard.callback_json(actions.ANSWER, user_id, msg_id)
                    )
                ]
            ]
        )


class AnswerUserButton:
    @staticmethod
    def get_keyboard(lang: str) -> InlineKeyboardMarkup:
        actions = MainUserKeyboard.Callback.ActionEnum

        def _get_button_text():
            match lang:
                case "eng":
                    return "Answer"
                case "ru" | _:
                    return "Ответить"

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_get_button_text(), callback_data=MainUserKeyboard.callback_json(actions.ASK_QUESTION)
                    )
                ],
            ]
        )

from enum import Enum

from pydantic import ValidationError, Field, ConfigDict, BaseModel

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from common_utils.keyboards.keyboard_utils import callback_json_validator, get_bot_channels, get_bot_username, \
    get_bot_channel_post, get_bot_post_message, get_bot_contest

from database.models.post_message_model import PostMessageType


class ReplyBackChannelMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            BACK_TO_CHANNEL_MENU = "🔙 Назад"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="back_to_channel_menu", frozen=True)
        a: ActionEnum

        bot_id: int

    @staticmethod
    def get_keyboard() -> ReplyKeyboardMarkup:
        actions = ReplyBackChannelMenuKeyboard.Callback.ActionEnum

        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=actions.BACK_TO_CHANNEL_MENU.value
                    )
                ]
            ], resize_keyboard=True
        )


class InlineChannelPublishAcceptKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            SEND = "sen"
            BACK_TO_CHANNEL_PICK = "bb"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cla", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="bi")
        mid: int = Field(alias="m")
        pid: int = Field(alias="p")
        chid: int | None = Field(alias="ci")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            msg_id,
            product_id: int,
            channel_id: int | None
    ) -> str:
        return InlineChannelPublishAcceptKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            chid=channel_id,
            pid=product_id,
            mid=msg_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineChannelPublishAcceptKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    def get_keyboard(
            bot_id: int,
            msg_id: int,
            product_id: int,
            channel_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlineChannelPublishAcceptKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Отправить",
                        callback_data=InlineChannelPublishAcceptKeyboard.callback_json(
                            actions.SEND, bot_id=bot_id, msg_id=msg_id, product_id=product_id, channel_id=channel_id
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineChannelPublishAcceptKeyboard.callback_json(
                            actions.BACK_TO_CHANNEL_PICK,
                            bot_id=bot_id,
                            product_id=product_id,
                            msg_id=msg_id,
                            channel_id=channel_id
                        )
                    )
                ]
            ]
        )


class InlineChannelsListPublishKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            PICK_CHANNEL = "p"
            CANCEL = "c"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cl", frozen=True)
        a: ActionEnum

        bot_id: int = Field(alias="bi")
        mid: int = Field(alias="m")
        chid: int | None = Field(alias="ci")
        pid: int = Field(alias="p")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            msg_id,
            product_id: int,
            channel_id: int | None,
    ) -> str:
        return InlineChannelsListPublishKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            chid=channel_id,
            mid=msg_id,
            pid=product_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineChannelsListPublishKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int,
            msg_id: int,
            product_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlineChannelsListPublishKeyboard.Callback.ActionEnum

        resized_channels_buttons = await _get_resized_channels_button(
            keyboard=InlineChannelsListPublishKeyboard,
            action=actions.PICK_CHANNEL,
            bot_id=bot_id,
            msg_id=msg_id,
            product_id=product_id
        )

        return InlineKeyboardMarkup(inline_keyboard=[
            *resized_channels_buttons,
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=InlineChannelsListPublishKeyboard.callback_json(
                        actions.CANCEL, bot_id, msg_id, product_id, None
                    )
                )
            ],
        ])


class InlineChannelsListKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            OPEN_CHANNEL = "channel"
            BACK_TO_MAIN_MENU = "back_main_menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cl", frozen=True)
        a: ActionEnum

        bot_id: int
        channel_id: int | None = Field(alias="ci")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            channel_id: int | None
    ) -> str:
        return InlineChannelsListKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            channel_id=channel_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineChannelsListKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlineChannelsListKeyboard.Callback.ActionEnum

        resized_channels_buttons = await _get_resized_channels_button(
            keyboard=InlineChannelsListKeyboard,
            action=actions.OPEN_CHANNEL,
            bot_id=bot_id
        )

        return InlineKeyboardMarkup(inline_keyboard=[
            *resized_channels_buttons,
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlineChannelsListKeyboard.callback_json(
                        actions.BACK_TO_MAIN_MENU, bot_id, None
                    )
                ),
                InlineKeyboardButton(
                    text="📢 Добавить в канал",
                    url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
                )
            ],
        ])


class InlineChannelMenuKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            EDIT_POST_MESSAGE = "epm"
            CREATE_POST_MESSAGE = "cpm"

            EDIT_CONTEST = "ec"
            CREATE_CONTEST = "cc"

            ANALYTICS = "an"
            LEAVE_CHANNEL = "lc"

            BACK_CHANNELS_LIST = "back_cc"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cm", frozen=True)
        a: ActionEnum

        bot_id: int
        channel_id: int = Field(alias="ci")
        post_message_id: int | None = Field(alias="pmi", default=None)

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            channel_id: int,
            post_message_id: int | None = None
    ) -> str:
        to_exclude = set()
        if post_message_id is None:
            to_exclude.add("post_message_id")

        return InlineChannelMenuKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            channel_id=channel_id,
            post_message_id=post_message_id
        ).model_dump_json(by_alias=True, exclude=to_exclude)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineChannelMenuKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int,
            channel_id: int
    ) -> InlineKeyboardMarkup:
        actions = InlineChannelMenuKeyboard.Callback.ActionEnum

        channel_post = await get_bot_channel_post(bot_id=bot_id)
        if channel_post:
            channel_post_button = InlineKeyboardButton(
                text="Редактировать запись",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.EDIT_POST_MESSAGE, bot_id, channel_id, channel_post.post_message_id
                )
            )
        else:
            channel_post_button = InlineKeyboardButton(
                text="Создать запись",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.CREATE_POST_MESSAGE, bot_id, channel_id
                )
            )

        channel_contest = await get_bot_contest(bot_id)
        post_message = await get_bot_post_message(bot_id, PostMessageType.CONTEST)
        if channel_contest and post_message:
            channel_contest_button = InlineKeyboardButton(
                text="Текущий конкурс",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.EDIT_CONTEST, bot_id, channel_id
                )
            )
        else:
            channel_contest_button = InlineKeyboardButton(
                text="Создать конкурс",
                callback_data=InlineChannelMenuKeyboard.callback_json(
                    actions.CREATE_CONTEST, bot_id, channel_id
                )
            )

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    channel_post_button,
                    InlineKeyboardButton(
                        text="Аналитика",
                        callback_data=InlineChannelMenuKeyboard.callback_json(
                            actions.ANALYTICS, bot_id, channel_id
                        )
                    )
                ],
                [
                    channel_contest_button
                ],
                [
                    InlineKeyboardButton(
                        text="Права бота",
                        url=f"https://t.me/{await get_bot_username(bot_id)}?startchannel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=InlineChannelMenuKeyboard.callback_json(
                            actions.BACK_CHANNELS_LIST, bot_id, channel_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="🛑 Выйти из канала",
                        callback_data=InlineChannelMenuKeyboard.callback_json(
                            actions.LEAVE_CHANNEL, bot_id, channel_id
                        )
                    )
                ]
            ],
        )


class InlineContestTypeKeyboard:
    class Callback(BaseModel):
        class ActionEnum(Enum):
            RANDOMIZER = "random"
            BACK_TO_CHANNEL_MENU = "bk_ch_menu"

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)

        n: str = Field(default="cts", frozen=True)
        a: ActionEnum

        bot_id: int
        channel_id: int = Field(alias="ci")

    @staticmethod
    @callback_json_validator
    def callback_json(
            action: Callback.ActionEnum,
            bot_id: int,
            channel_id: int
    ) -> str:
        return InlineContestTypeKeyboard.Callback(
            a=action,
            bot_id=bot_id,
            channel_id=channel_id
        ).model_dump_json(by_alias=True)

    @staticmethod
    def callback_validator(json_string: str) -> bool:
        try:
            InlineContestTypeKeyboard.Callback.model_validate_json(json_string)
            return True
        except ValidationError:
            return False

    @staticmethod
    async def get_keyboard(
            bot_id: int,
            channel_id: int,
    ) -> InlineKeyboardMarkup:
        actions = InlineContestTypeKeyboard.Callback.ActionEnum

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎲 Рандомайзер",
                    callback_data=InlineContestTypeKeyboard.callback_json(
                        actions.RANDOMIZER, bot_id, channel_id
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=InlineContestTypeKeyboard.callback_json(
                        actions.BACK_TO_CHANNEL_MENU, bot_id, channel_id
                    )
                ),
            ],
        ])


async def _get_resized_channels_button(
        keyboard: InlineChannelsListPublishKeyboard.__class__ | InlineChannelsListKeyboard.__class__,
        action,
        bot_id: int,
        msg_id: int | None = None,
        product_id: int | None = None

) -> list[list[InlineKeyboardButton]]:
    """Returns resized inline keyboard with channels as buttons"""
    all_channels = await get_bot_channels(bot_id=bot_id)

    if keyboard == InlineChannelsListKeyboard:
        channels_buttons = [
            InlineKeyboardButton(
                text='@' + channel[1],
                callback_data=keyboard.callback_json(
                    action, bot_id=bot_id, channel_id=channel[0].channel_id
                )
            ) for channel in all_channels
        ]
    else:
        channels_buttons = [
            InlineKeyboardButton(
                text='@' + channel[1],
                callback_data=keyboard.callback_json(
                    action, bot_id=bot_id, msg_id=msg_id, product_id=product_id, channel_id=channel[0].channel_id
                )
            ) for channel in all_channels
        ]

    return [channels_buttons[i:i + 4] for i in range(0, len(channels_buttons), 4)]

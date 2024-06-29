from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import States
from bot.handlers import post_message_router
from bot.enums.post_message_type import PostMessageType
from bot.post_message.post_message_editors import edit_delay_date, edit_message, edit_button_text, edit_button_url, \
    edit_media_files


@post_message_router.message(StateFilter(
    States.EDITING_POST_TEXT,
    States.EDITING_POST_BUTTON_TEXT,
    States.EDITING_POST_BUTTON_URL,
    States.EDITING_POST_MEDIA_FILES,
    States.EDITING_POST_DELAY_DATE,
))
async def editing_post_message_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    current_state = await state.get_state()
    
    match state_data["post_message_type"]:
        case PostMessageType.MAILING.value:
            post_message_type = PostMessageType.MAILING
        case PostMessageType.CHANNEL_POST.value:
            post_message_type = PostMessageType.CHANNEL_POST
        case _:
            raise Exception("UnknownMessageType")

    match current_state:
        case States.EDITING_POST_DELAY_DATE:
            await edit_delay_date(message, state, post_message_type)
        case States.EDITING_POST_TEXT:
            await edit_message(message, state, post_message_type)
        case States.EDITING_POST_BUTTON_TEXT:
            await edit_button_text(message, state, post_message_type)
        case States.EDITING_POST_BUTTON_URL:
            await edit_button_url(message, state, post_message_type)
        case States.EDITING_POST_MEDIA_FILES:
            await edit_media_files(message, state, post_message_type)

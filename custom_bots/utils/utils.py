from aiogram.utils.token import TokenValidationError, validate_token

from aiogram.types import Chat, User

from typing import Any, Union, Dict


def format_locales(text: str, user: User, chat: Chat, reply_to_user: User = None, bot_data: User = None) -> str:
    if text is None:
        return "Empty message"
    data_dict = {
        "name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": f"@{user.username}",
        "user_id": user.id,
        "chat": chat.full_name,
    }
    if bot_data:
        data_dict.update({"bot_username": bot_data.username})
    if reply_to_user:
        data_dict.update(
            {
                "reply_name": reply_to_user.full_name,
                "reply_first_name": reply_to_user.first_name,
                "reply_last_name": reply_to_user.last_name,
                "reply_username": f"@{reply_to_user.username}",
                "reply_user_id": reply_to_user.id,
            }
        )
    text = text.replace("{{", "START_FLAG").replace("}}", "END_FLAG")
    for param in data_dict:
        text = text.replace("{" + str(param) + "}", str(data_dict[param]))
    text = text.replace("START_FLAG", "{{").replace("END_FLAG", "}}")
    return text


def is_bot_token(value: str) -> Union[bool, Dict[str, Any]]:
    try:
        validate_token(value)
    except TokenValidationError:
        return False
    return True

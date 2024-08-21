from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, create_model

from bot.keyboards.start_keyboards import CALLBACK_TO_STRING_NAME


class UserStartMessageActionSchema(BaseModel):
    """User Action in Start Message"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(frozen=True)
    username: Optional[str] = None
    action: str  # bot/keyboards/start_keyboards.py/CALLBACK_TO_STRING_NAME

    date: str


# Class for couting referal system actions
StartMessageAnalyticSchema = create_model(
    "StartMessageAnalyticSchema",
    __config__=ConfigDict(from_attributes=True),
    **{
        (value if isinstance(value, str) else " ".join(value)): (int, Field(default=0))
        for value in CALLBACK_TO_STRING_NAME.values()
    },
    actions=(list[UserStartMessageActionSchema], Field(default=[])),
)

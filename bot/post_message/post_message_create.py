from datetime import datetime

from bot.enums.post_message_type import PostMessageType
from bot.main import post_message_db, mailing_db, channel_post_db
from database.models.channel_post_model import ChannelPostSchemaWithoutId
from database.models.mailing_model import MailingSchemaWithoutId
from database.models.post_message_model import PostMessageSchemaWithoutId


async def post_message_create(bot_id: int, post_message_type: PostMessageType) -> None:
    post_message_id = await post_message_db.add_post_message(PostMessageSchemaWithoutId.model_validate(
        {"bot_id": bot_id, "created_at": datetime.now().replace(tzinfo=None), "post_message_type": post_message_type}
    ))

    data = {"bot_id": bot_id, "post_message_id": post_message_id}

    match post_message_type:
        case PostMessageType.MAILING:
            await mailing_db.add_mailing(MailingSchemaWithoutId.model_validate(data))
        case PostMessageType.CHANNEL_POST:
            await channel_post_db.add_channel_post(ChannelPostSchemaWithoutId.model_validate(data))

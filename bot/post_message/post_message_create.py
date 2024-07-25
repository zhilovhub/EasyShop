from datetime import datetime

from database.config import post_message_db, mailing_db, channel_post_db, contest_db, partnership_db
from database.models.contest_model import ContestSchemaWithoutId
from database.models.mailing_model import MailingSchemaWithoutId
from database.models.partnership_model import PartnershipSchemaWithoutId
from database.models.channel_post_model import ChannelPostSchemaWithoutId
from database.models.post_message_model import PostMessageSchemaWithoutId, PostMessageType, UnknownPostMessageTypeError


async def post_message_create(bot_id: int,
                              post_message_type: PostMessageType,
                              contest_winners_count: int = None) -> None:
    """
    Creates post message

    :raises  UnknownPostMessageTypeError:
    """
    post_message_id = await post_message_db.add_post_message(PostMessageSchemaWithoutId.model_validate(
        {"bot_id": bot_id, "created_at": datetime.now().replace(tzinfo=None), "post_message_type": post_message_type}
    ))

    data = {"bot_id": bot_id, "post_message_id": post_message_id}
    if contest_winners_count is not None:
        data["winners_count"] = contest_winners_count

    match post_message_type:
        case PostMessageType.MAILING:
            await mailing_db.add_mailing(MailingSchemaWithoutId.model_validate(data))
        case PostMessageType.CHANNEL_POST:
            await channel_post_db.add_channel_post(ChannelPostSchemaWithoutId.model_validate(data))
        case PostMessageType.CONTEST:
            await contest_db.add_contest(ContestSchemaWithoutId.model_validate(data))
        case PostMessageType.PARTNERSHIP_POST:
            await partnership_db.add_partnership(PartnershipSchemaWithoutId.model_validate(data))
        case _:
            raise UnknownPostMessageTypeError

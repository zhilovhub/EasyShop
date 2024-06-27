from database.models.models import Database
from database.models.contest_channel_model import ContestChannelDao, ContestChannelSchema, ContestChannelSchemaWithoutId
from database.models.post_message_media_files import PostMessageMediaFileDao, PostMessageMediaFileSchema


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class CompetitionModule:  # TODO write tests
    """Модуль конкурсов в каналах"""

    def __init__(self, database: Database) -> None:
        self.channel_db = database.get_channel_dao()
        self.contest_channel_db: ContestChannelDao = database.get_contest_channel_dao()
        self.post_message_media_file_db: PostMessageMediaFileDao = database.get_post_message_media_file_dao()

    async def get_all_competitions(self, channel_id: int, bot_id: int) -> list[ContestChannelSchema]:
        return await self.competition_db.get_all_competitions(channel_id, bot_id)

    async def get_competition(self, competition_id: int) -> ContestChannelSchema:
        competition = await self.competition_db.get_competition(competition_id)
        return competition

    async def get_competition_media_files(self, competition_id: int) -> list[PostMessageMediaFileSchema]:
        return await self.competition_media_file_db.get_all_competition_media_files(competition_id)

    async def create_competition(self, channel_id: int, bot_id: int) -> int:
        competition_id = await self.competition_db.add_competition(
            ContestChannelSchemaWithoutId.model_validate({
                "channel_id": channel_id,
                "bot_id": bot_id
            })
        )

        return competition_id

    async def update_competition(self, competition: ContestChannelSchema) -> None:
        await self.competition_db.update_competition(competition)

    async def add_competition_media_file(self, competition_id: int, file_name: str, media_type: str) -> None:
        await self.competition_media_file_db.add_competition_media_file(
            PostMessageMediaFileSchema.model_validate({
                "competition_id": competition_id,
                "file_name": file_name,
                "media_type": media_type,
            })
        )

    async def delete_competition_media_files(self, competition_id: int) -> None:
        await self.competition_media_file_db.delete_competition_media_files(competition_id)

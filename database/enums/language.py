from enum import Enum
from typing import Optional

from sqlalchemy import Unicode, Dialect, String, TypeDecorator


class UserLanguageValues(Enum):
    RUSSIAN = "ru"
    ENGLISH = "eng"
    HEBREW = "heb"


AVAILABLE_LANGUAGES = [
    UserLanguageValues.ENGLISH,
    UserLanguageValues.RUSSIAN,
    UserLanguageValues.HEBREW,
]


class UserLanguageEmoji(Enum):
    RUSSIAN = "🇷🇺"
    ENGLISH = "🇬🇧"
    HEBREW = "🇮🇱"
    UNKNOWN = "🌐"


def get_lang_emoji(lang: UserLanguageValues) -> str:
    match lang:
        case UserLanguageValues.RUSSIAN:
            return UserLanguageEmoji.RUSSIAN.value
        case UserLanguageValues.HEBREW:
            return UserLanguageEmoji.HEBREW.value
        case UserLanguageValues.ENGLISH:
            return UserLanguageEmoji.ENGLISH.value
        case _:
            return UserLanguageEmoji.UNKNOWN.value


class UserLanguage(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""

    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[UserLanguageValues], dialect: Dialect) -> String:  # noqa
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[UserLanguageValues]:  # noqa
        match value:
            case UserLanguageValues.RUSSIAN.value:
                return UserLanguageValues.RUSSIAN
            case UserLanguageValues.ENGLISH.value:
                return UserLanguageValues.ENGLISH
            case UserLanguageValues.HEBREW.value:
                return UserLanguageValues.HEBREW

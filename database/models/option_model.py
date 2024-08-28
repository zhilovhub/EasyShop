import json

from pydantic import BaseModel, ConfigDict, Field, validate_call

from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    select,
    insert,
    update,
    delete,
    TypeDecorator,
    Unicode,
    Dialect,
    ARRAY,
    JSON,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from common_utils.themes import ThemeParamsSchema

from database.models import Base
from database.models.dao import Dao
from database.exceptions.exceptions import KwargsException

from database.enums import UserLanguage, UserLanguageValues

from logs.config import extra_params


# TODO Create handle_exception_func
class OptionNotFoundError(KwargsException):
    """Raised when provided option not found in database"""


DEFAULT_START_MESSAGES = {
    UserLanguageValues.RUSSIAN.value: "Здравствуйте, <b>{name}</b>! Для открытия магазина нажмите на кнопку магазин",
    UserLanguageValues.ENGLISH.value: "Hello, <b>{name}</b>! To open a store, click on the store button",
    UserLanguageValues.HEBREW.value: "שלום, <b>{name}</b>! כדי לפתוח את החנות, לחץ על כפתור החנות",
}

DEFAULT_DEF_MESSAGES = {
    UserLanguageValues.RUSSIAN.value: "Приветствую, этот бот создан с помощью @{bot_username}",
    UserLanguageValues.ENGLISH.value: "Greetings, this bot was created using @{bot_username}",
    UserLanguageValues.HEBREW.value: "ברכות, הבוט הזה נוצר עם @{bot_username}",
}


class CurrencyCodesValues(Enum):
    RUSSIAN_RUBLE = "RUB"
    US_DOLLAR = "USD"
    EURO = "EUR"
    ISRAELI_SHEQEL = "ILS"

    TELEGRAM_STARS = "XTR"


class CurrencySymbolsValues(Enum):
    RUSSIAN_RUBLE = "₽"
    US_DOLLAR = "$"
    EURO = "€"
    ISRAELI_SHEQEL = "₪"

    TELEGRAM_STARS = "⭐️"


class CurrencyCodes(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""

    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[CurrencyCodesValues], dialect: Dialect) -> String:  # noqa
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[CurrencyCodesValues]:  # noqa
        match value:
            case CurrencyCodesValues.RUSSIAN_RUBLE.value:
                return CurrencyCodesValues.RUSSIAN_RUBLE
            case CurrencyCodesValues.US_DOLLAR.value:
                return CurrencyCodesValues.US_DOLLAR
            case CurrencyCodesValues.EURO.value:
                return CurrencyCodesValues.EURO
            case CurrencyCodesValues.ISRAELI_SHEQEL.value:
                return CurrencyCodesValues.ISRAELI_SHEQEL
            case CurrencyCodesValues.TELEGRAM_STARS.value:
                return CurrencyCodesValues.TELEGRAM_STARS


class CurrencySymbols(TypeDecorator):  # noqa
    """Class to convert Enum values to db values (and reverse)"""

    impl = Unicode
    cache_ok = True

    def process_bind_param(self, value: Optional[CurrencySymbolsValues], dialect: Dialect) -> String:  # noqa
        return value.value

    def process_result_value(self, value: Optional[String], dialect: Dialect) -> Optional[CurrencySymbolsValues]:  # noqa
        match value:
            case CurrencySymbolsValues.RUSSIAN_RUBLE.value:
                return CurrencySymbolsValues.RUSSIAN_RUBLE
            case CurrencySymbolsValues.US_DOLLAR.value:
                return CurrencySymbolsValues.US_DOLLAR
            case CurrencySymbolsValues.EURO.value:
                return CurrencySymbolsValues.EURO
            case CurrencySymbolsValues.ISRAELI_SHEQEL.value:
                return CurrencySymbolsValues.ISRAELI_SHEQEL
            case CurrencySymbolsValues.TELEGRAM_STARS.value:
                return CurrencySymbolsValues.TELEGRAM_STARS


class Option(Base):
    __tablename__ = "options"

    id = Column(BigInteger, primary_key=True)
    start_msg = Column(JSON, nullable=False, default=json.dumps(DEFAULT_START_MESSAGES))
    default_msg = Column(JSON, nullable=False, default=json.dumps(DEFAULT_DEF_MESSAGES))
    post_order_msg = Column(String, nullable=True)
    auto_reduce = Column(Boolean, nullable=False, default=False)

    theme_params = Column(JSON)
    web_app_button = Column(String, nullable=False)
    languages = Column(ARRAY(UserLanguage), nullable=False, default=[UserLanguageValues.RUSSIAN])

    currency_code = Column(CurrencyCodes, nullable=False)
    currency_symbol = Column(CurrencySymbols, nullable=False)
    request_name_in_payment = Column(Boolean, nullable=False, default=False)
    request_email_in_payment = Column(Boolean, nullable=False, default=False)
    request_phone_in_payment = Column(Boolean, nullable=False, default=False)
    request_address_in_payment = Column(Boolean, nullable=False, default=False)
    show_photo_in_payment = Column(Boolean, nullable=False, default=True)
    show_payment_in_webview = Column(Boolean, nullable=False, default=True)


class OptionSchemaWithoutId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_msg: dict = DEFAULT_START_MESSAGES
    default_msg: dict = DEFAULT_DEF_MESSAGES
    post_order_msg: str | None = None
    auto_reduce: bool = False

    theme_params: ThemeParamsSchema = ThemeParamsSchema()
    web_app_button: str

    languages: list[UserLanguageValues] = [UserLanguageValues.RUSSIAN]

    currency_code: CurrencyCodesValues = CurrencyCodesValues.RUSSIAN_RUBLE
    currency_symbol: CurrencySymbolsValues = CurrencySymbolsValues.RUSSIAN_RUBLE
    request_name_in_payment: bool = False
    request_email_in_payment: bool = False
    request_phone_in_payment: bool = False
    request_address_in_payment: bool = False
    show_photo_in_payment: bool = True
    show_payment_in_webview: bool = True


class OptionSchema(OptionSchemaWithoutId):
    id: int = Field(frozen=True)


class OptionDao(Dao):  # TODO write tests
    def __init__(self, engine: AsyncEngine, logger) -> None:
        super().__init__(engine, logger)

    @validate_call(validate_return=True)
    async def get_all_options(self) -> list[OptionSchema]:
        """
        :return: list of OptionSchema
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Option))
        await self.engine.dispose()

        raw_res = raw_res.fetchall()
        res = []
        for option in raw_res:
            res.append(OptionSchema.model_validate(option))

        self.logger.debug(f"Found {len(res)} options", extra=extra_params())

        return res

    @validate_call(validate_return=True)
    async def get_option(self, option_id: int) -> OptionSchema:
        """
        :param option_id: option_id
        :return: OptionSchema

        :raises OptionNotFoundError: no option in db
        """
        async with self.engine.begin() as conn:
            raw_res = await conn.execute(select(Option).where(Option.id == option_id))
        await self.engine.dispose()

        res = raw_res.fetchone()
        if res is None:
            raise OptionNotFoundError(option_id=option_id)

        res = OptionSchema.model_validate(res)
        if isinstance(res.theme_params, dict):
            res.theme_params = ThemeParamsSchema(**res.theme_params)
        self.logger.debug(f"option_id={option_id}: found option {res}", extra=extra_params(option_id=option_id))

        return res

    @validate_call(validate_return=True)
    async def add_option(self, new_option: OptionSchemaWithoutId) -> int:
        """
        Adds new option to database
        """
        async with self.engine.begin() as conn:
            opt_id = (await conn.execute(insert(Option).values(new_option.model_dump()))).inserted_primary_key[0]

        self.logger.debug(f"option_id={opt_id}: new added option {new_option}", extra=extra_params(option_id=opt_id))

        return opt_id

    @validate_call(validate_return=True)
    async def update_option(self, updated_option: OptionSchema) -> None:
        """
        Updates the option in database
        """
        option_id = updated_option.id
        await self.get_option(option_id)

        async with self.engine.begin() as conn:
            await conn.execute(update(Option).where(Option.id == option_id).values(updated_option.model_dump()))

        self.logger.debug(
            f"option_id={option_id}: updated option {updated_option}", extra=extra_params(option_id=option_id)
        )

    @validate_call(validate_return=True)
    async def delete_option(self, option_id: int) -> None:
        """
        Deletes the option from database
        """
        async with self.engine.begin() as conn:
            await conn.execute(delete(Option).where(Option.id == option_id))

        self.logger.debug(f"option_id={option_id}: deleted option {option_id}", extra=extra_params(option_id=option_id))

    @validate_call(validate_return=True)
    async def clear_table(self) -> None:
        """
        Often used in tests
        """
        await super().clear_table(Option)

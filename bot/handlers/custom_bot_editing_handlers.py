import re

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.main import bot, cache_resources_file_id_store
from bot.utils import MessageTexts
from bot.states.states import States
from bot.handlers.routers import custom_bot_editing_router
from bot.utils.send_instructions import send_instructions
from bot.keyboards.main_menu_keyboards import ReplyBotMenuKeyboard, ReplyBackBotMenuKeyboard

from common_utils.bot_utils import create_bot_options
from common_utils.keyboards.keyboards import InlineBotEditOrderOptionKeyboard, InlineBotEditOrderOptionsKeyboard, \
    InlineBotMenuKeyboard, InlineBotSettingsMenuKeyboard

from database.config import bot_db, option_db, order_option_db
from database.models.option_model import OptionNotFoundError
from database.models.order_option_model import OrderOptionNotFoundError, OrderOptionSchemaWithoutId

from logs.config import logger


def _is_valid_hex_code(string: str) -> bool:
    """Проверяет, валидный ли цвет передал пользователь"""

    regex = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"

    p = re.compile(regex)

    if string is None:
        return False

    if re.search(p, string):
        return True
    else:
        return False


@custom_bot_editing_router.callback_query(
    lambda query: InlineBotEditOrderOptionsKeyboard.callback_validator(query.data)
)
async def manage_order_options(query: CallbackQuery, state: FSMContext):
    callback_data = InlineBotEditOrderOptionsKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)
    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_BOT_MENU:
            await query.message.edit_text(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(callback_data.bot_id)
            )
        case callback_data.ActionEnum.ADD_ORDER_OPTION:
            await query.message.answer(
                "Введите название новой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_NEW_ORDER_OPTION_TEXT)
            await state.set_data({"bot_id": callback_data.bot_id})
        case callback_data.ActionEnum.EDIT_ORDER_OPTION:
            try:
                oo = await order_option_db.get_order_option(callback_data.order_option_id)
            except OrderOptionNotFoundError:
                await query.answer("Вы уже удалили эту опцию", show_alert=True)
                await query.message.delete()
                return
            await query.message.edit_text(
                **MessageTexts.generate_order_option_info(oo),
                reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                    custom_bot.bot_id, callback_data.order_option_id
                )
            )
            await query.answer()


@custom_bot_editing_router.callback_query(lambda query: InlineBotEditOrderOptionKeyboard.callback_validator(query.data))
async def manage_order_option(query: CallbackQuery, state: FSMContext):
    callback_data = InlineBotEditOrderOptionKeyboard.Callback.model_validate_json(query.data)

    custom_bot = await bot_db.get_bot(callback_data.bot_id)

    order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)

    sorted_oo = sorted(order_options, key=lambda x: x.position_index)

    try:
        order_option = await order_option_db.get_order_option(callback_data.order_option_id)
    except OrderOptionNotFoundError:
        await query.answer("Эта опция уже удалена", show_alert=True)
        await query.message.delete()
        return

    match callback_data.a:
        case callback_data.ActionEnum.BACK_TO_ORDER_OPTIONS:
            await query.message.edit_text(
                **MessageTexts.generate_order_options_info(order_options),
                reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
            )

        case callback_data.ActionEnum.EDIT_REQUIRED_STATUS:
            order_option.required = not order_option.required
            await order_option_db.update_order_option(order_option)
            await query.message.edit_reply_markup(
                reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                    custom_bot.bot_id, callback_data.order_option_id
                )
            )

        case callback_data.ActionEnum.EDIT_EMOJI:
            await query.message.answer(
                "Введите новый эмодзи к этой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_ORDER_OPTION_EMOJI)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.order_option_id})

        case callback_data.ActionEnum.EDIT_OPTION_NAME:
            await query.message.answer(
                "Введите новый текст к этой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_ORDER_OPTION_TEXT)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.order_option_id})
        case callback_data.ActionEnum.EDIT_POSITION_INDEX:
            await query.message.answer(
                "Введите номер позиции к этой опции: ",
                reply_markup=ReplyBackBotMenuKeyboard.get_keyboard()
            )
            await query.answer()
            await state.set_state(States.WAITING_FOR_ORDER_OPTION_POSITION)
            await state.set_data({"bot_id": callback_data.bot_id, "order_option_id": callback_data.order_option_id})
        case callback_data.ActionEnum.DELETE_ORDER_OPTION:

            await order_option_db.delete_order_option(order_option.id)
            sorted_oo.remove(order_option)
            for index, option in enumerate(sorted_oo):
                option.position_index = index + 1
                await order_option_db.update_order_option(option)
            await query.answer("Опция удалена", show_alert=True)
            await query.message.edit_text(
                **MessageTexts.generate_order_options_info(sorted_oo),
                reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
            )


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_OPTION_POSITION)
async def edit_order_option_position(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)
        sorted_oo = sorted(order_options, key=lambda x: x.position_index)
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    index = int(message.text)
                except ValueError:
                    return await message.answer("В сообщении должно  быть только число")
                if index <= 0:
                    return await message.answer("Номер позиции должен быть больше 0")
                if index > sorted_oo[-1].position_index:
                    return await message.answer("У вас нет столько опций")
                sorted_oo.remove(order_option)
                sorted_oo.insert(index-1, order_option)
                for i, option in enumerate(sorted_oo):
                    option.position_index = i + 1
                    await order_option_db.update_order_option(option)
                await message.answer(
                    "Новая позиция опции добавлена",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot.bot_id)
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_OPTION_TEXT)
async def edit_order_option_name(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                order_option.option_name = message.text
                await order_option_db.update_order_option(order_option)
                await message.answer(
                    "Новое название опции добавлено",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot.bot_id)
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_ORDER_OPTION_EMOJI)
async def edit_order_option_emoji(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_option = await order_option_db.get_order_option(state_data["order_option_id"])
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_option_info(order_option),
                    reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(custom_bot.bot_id, order_option.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                emoji_pattern = re.compile(
                    r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-'
                    r'\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-'
                    r'\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-'
                    r'\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]$'
                )
                if emoji_pattern.match(message.text):
                    order_option.emoji = message.text
                    await order_option_db.update_order_option(order_option)
                    await message.answer(
                        "Новый эмодзи добавлен",
                        reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=custom_bot.bot_id)
                    )
                    await message.answer(
                        **MessageTexts.generate_order_option_info(order_option),
                        reply_markup=await InlineBotEditOrderOptionKeyboard.get_keyboard(
                            custom_bot.bot_id, order_option.id
                        )
                    )
                    await state.set_state(States.BOT_MENU)
                    await state.set_data(state_data)
                else:
                    await message.answer("Сообщение должно содержать эмодзи")

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.WAITING_FOR_NEW_ORDER_OPTION_TEXT)
async def create_new_order_option(message: Message, state: FSMContext):
    if message.text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])
        order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)
        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    **MessageTexts.generate_order_options_info(order_options),
                    reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
                )

                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                sorted_oo = sorted(order_options, key=lambda x: x.position_index)
                await order_option_db.add_order_option(
                    OrderOptionSchemaWithoutId(
                        bot_id=custom_bot.bot_id,
                        option_name=message.text,
                        position_index=(sorted_oo[-1].position_index + 1))
                )
                await message.answer("Новая опция успешно добавлена!")
                order_options = await order_option_db.get_all_order_options(custom_bot.bot_id)
                await message.answer(
                    **MessageTexts.generate_order_options_info(order_options),
                    reply_markup=await InlineBotEditOrderOptionsKeyboard.get_keyboard(custom_bot.bot_id)
                )

    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.EDITING_START_MESSAGE)
async def editing_start_message_handler(message: Message, state: FSMContext):
    """Настраивает стартовое сообщение кастомного бота"""

    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message.text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.start_msg = message_text
                await option_db.update_option(options)

                await message.answer(
                    "Стартовое сообщение изменено!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )

                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Стартовое сообщение должно содержать текст")


@custom_bot_editing_router.message(States.EDITING_DEFAULT_MESSAGE)
async def editing_default_message_handler(message: Message, state: FSMContext):
    """Настраивает дефолтное сообщение кастомного бота"""

    message_text = message.text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.default_msg = message_text
                await option_db.update_option(options)

                await message.answer(
                    "Сообщение-затычка изменена!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение-затычка должна содержать текст")


@custom_bot_editing_router.message(States.EDITING_BG_COLOR)
async def editing_bg_color_handler(message: Message, state: FSMContext):
    """Настраивает bg_color веб приложения магазина"""

    message_text = message.text.strip()
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в меню настроек...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                if not _is_valid_hex_code(message_text) and message_text != "telegram":
                    return await message.answer("Не получилось распознать ввод. Введите еще раз цвет в формате "
                                                "<i>#FFFFFF</i> или напишите <i>telegram</i> для дефолтных цветов.")

                bg_color = None if message_text == "telegram" else message_text

                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.bg_color = bg_color
                await option_db.update_option(options)

                await message.answer(
                    "Цвет фона изменен!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotSettingsMenuKeyboard.get_keyboard(custom_bot.bot_id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Цвет должен быть указан в тексте сообщения.")


@custom_bot_editing_router.message(States.EDITING_POST_ORDER_MESSAGE)
async def editing_post_order_message_handler(message: Message, state: FSMContext):
    """Настраивает сообщение, которое будет отправляться клиентам после оформления заказа"""

    message_text = message.html_text
    if message_text:
        state_data = await state.get_data()
        custom_bot = await bot_db.get_bot(state_data['bot_id'])

        match message_text:
            case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
                await message.answer(
                    "Возвращаемся в главное меню...",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
            case _:
                try:
                    options = await option_db.get_option(custom_bot.options_id)
                except OptionNotFoundError:
                    new_options_id = await create_bot_options()
                    custom_bot.options_id = new_options_id
                    await bot_db.update_bot(custom_bot)
                    options = await option_db.get_option(new_options_id)
                options.post_order_msg = message_text
                await option_db.update_option(options)

                await message.answer(
                    "Сообщение после заказа изменено!",
                    reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
                )
                await message.answer(
                    MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                    reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
                )
                await state.set_state(States.BOT_MENU)
                await state.set_data(state_data)
    else:
        await message.answer("Сообщение должно содержать текст")


@custom_bot_editing_router.message(States.DELETE_BOT)
async def delete_bot_handler(message: Message, state: FSMContext):
    """Обрабатывает подтверждение удаления бота"""

    message_text = message.text
    state_data = await state.get_data()
    custom_bot = await bot_db.get_bot(state_data['bot_id'])

    match message_text:
        case ReplyBackBotMenuKeyboard.Callback.ActionEnum.BACK_TO_BOT_MENU.value:
            await message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=ReplyBotMenuKeyboard.get_keyboard(bot_id=state_data["bot_id"])
            )
            await message.answer(
                MessageTexts.BOT_MENU_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineBotMenuKeyboard.get_keyboard(custom_bot.bot_id, message.from_user.id)
            )
            await state.set_state(States.BOT_MENU)
            await state.set_data(state_data)

        case "ПОДТВЕРДИТЬ":
            logger.info(f"Disabling bot {state_data['bot_id']}, setting deleted status to db...")
            custom_bot.status = "Deleted"
            await bot_db.del_bot(custom_bot.bot_id)

            await message.answer(
                "Бот удален",
                reply_markup=ReplyKeyboardRemove()
            )
            await send_instructions(bot, None, message.from_user.id, cache_resources_file_id_store)
            await state.set_state(States.WAITING_FOR_TOKEN)
            await state.set_data({"bot_id": -1})

        case _:
            await message.answer("Напишите ПОДТВЕРДИТЬ для подтверждения удаления или вернитесь назад")

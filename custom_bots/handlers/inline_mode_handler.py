from custom_bots.handlers.routers import inline_mode_router

from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from custom_bots.multibot import API_URL, custom_bot_logger
from custom_bots.utils.custom_message_texts import CustomMessageTexts

from database.config import product_db, bot_db
from database.enums import UserLanguageValues
from database.models.product_model import ProductFilter

from common_utils.keyboards.keyboards import InlineModeProductKeyboardButton


@inline_mode_router.inline_query()
async def handle_inline_query(query: InlineQuery, lang: UserLanguageValues):
    if not query.offset:
        prev_offset = 0
    else:
        prev_offset = int(query.offset)

    custom_bot_object = await bot_db.get_bot_by_token(query.bot.token)
    custom_bot_data = await query.bot.get_me()

    if query.query.strip():
        filters = [
            ProductFilter(
                bot_id=custom_bot_object.bot_id,
                filter_name="search",
                is_category_filter=False,
                reverse_order=False,
                category_id=None,
                search_word=query.query.strip(),
            )
        ]
    else:
        filters = None

    found_products = await product_db.get_all_products(custom_bot_object.bot_id, filters=filters)
    custom_bot_logger.debug(f"found {len(found_products)} products with inline query: '{query.query}'")
    inline_not_found_texts = CustomMessageTexts.get_inline_not_found_texts(lang)
    if not found_products:
        return await query.answer(
            results=[
                InlineQueryResultArticle(
                    id="not found",
                    **inline_not_found_texts,
                    input_message_content=InputTextMessageContent(message_text=inline_not_found_texts["title"]),
                )
            ],
            is_personal=True,
            cache_time=10,
        )
    else:
        try:
            results = []
            offset = False
            for product in found_products[prev_offset::]:
                if len(results) == 50:
                    offset = True
                    break
                thumb = None
                url = None
                if product.picture:
                    thumb = f"{API_URL}/files/get_product_thumbnail/{product.id}"
                custom_bot_logger.debug(f"thumb for product {product.id} : {thumb}")

                text, entities = product.convert_to_product_page_text(lang=lang).render()

                results.append(
                    InlineQueryResultArticle(
                        id=f"found product {product.id}",
                        title=f"{product.name}",
                        description=f"{product.description}",
                        thumbnail_url=thumb,
                        url=url,
                        input_message_content=InputTextMessageContent(
                            message_text=text,
                            parse_mode=None,
                            entities=entities,
                        ),
                        reply_markup=InlineModeProductKeyboardButton.get_keyboard(
                            product.id, custom_bot_data.username, lang=lang
                        ),
                    )
                )
            if offset:
                return await query.answer(
                    results=results, is_personal=True, next_offset=str(prev_offset + 50), cache_time=10
                )
            else:
                return await query.answer(results=results, is_personal=True, cache_time=10)
        except Exception as ex:
            custom_bot_logger.error("error while making inline query results", exc_info=ex)

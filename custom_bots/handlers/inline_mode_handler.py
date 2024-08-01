from custom_bots.handlers.routers import inline_mode_router

from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from custom_bots.multibot import API_URL, custom_bot_logger

from database.config import product_db, bot_db
from database.models.product_model import ProductFilter

from common_utils.keyboards.keyboards import InlineModeProductKeyboardButton


@inline_mode_router.inline_query()
async def handle_inline_query(query: InlineQuery):
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
                search_word=query.query.strip()
            )
        ]
    else:
        filters = None

    found_products = await product_db.get_all_products(custom_bot_object.bot_id, filters=filters)
    custom_bot_logger.debug(f"found {len(found_products)} products with inline query: '{query.query}'")
    if not found_products:
        return await query.answer(results=[InlineQueryResultArticle(
            id="not found",
            title="Товары не найдены.",
            description="По указанному запросу не было найдено ни одного товара в базе бота.",
            input_message_content=InputTextMessageContent(
                message_text="Товары не найдены.")
        )], is_personal=True, cache_time=10)
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
                    # thumb = "https://ezbots.ru:8888/r.png"
                    # thumb = f"https://koshka.top/uploads/posts/2021-11/1638103603_50-koshka-top-p
                    # -samie-malenkie-koshechki-54.jpg"
                    thumb = f"{API_URL}/files/get_product_thumbnail/{product.id}"
                    # thumb = "https://ezbots.ru:2024/static/A.png"
                    # thumb = f"https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftoppng.com
                    # %2Fuploads%2Fpreview%2Flinux-logo-png-linux-tux-black-white-115628885292kgc8ongco.png&f=1&nofb=1&ipt=822eeb3705d3e8d05ea0f00b7a07832aeaada0ff876978a2f7a805f707f312d8&ipo=images"
                custom_bot_logger.debug(f"thumb for product {product.id} : {thumb}")

                text, entities = product.convert_to_product_page_text().render()

                results.append(InlineQueryResultArticle(
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
                    reply_markup=InlineModeProductKeyboardButton.get_keyboard(product.id, custom_bot_data.username)
                ))
            if offset:
                return await query.answer(results=results, is_personal=True, next_offset=str(prev_offset + 50),
                                          cache_time=10)
            else:
                return await query.answer(results=results, is_personal=True, cache_time=10)
        except Exception as ex:
            custom_bot_logger.error("error while making inline query results", exc_info=ex)

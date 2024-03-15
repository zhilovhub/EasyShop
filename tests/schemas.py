from datetime import datetime, timedelta

from database.models.bot_model import BotSchemaWithoutId, BotSchema
from database.models.order_model import OrderSchema, OrderStatusValues
from database.models.product_model import ProductWithoutId, ProductSchema
from database.models.user_model import UserSchema

BOT_ID = 1

user_schema_1 = UserSchema(
    user_id=1,
    status="new",
    subscribed_until=None,
    registered_at=datetime.utcnow()
)
user_schema_2 = UserSchema(
    user_id=2,
    status="new",
    subscribed_until=datetime.now() + timedelta(days=7),
    registered_at=datetime.utcnow()
)

bot_schema_without_id_1 = BotSchemaWithoutId(
        token="1000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
        status="a",
        created_at=datetime.utcnow(),
        created_by=1,
        locale=""
    )
bot_schema_without_id_2 = BotSchemaWithoutId(
    token="2000000000:AaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaAaA",
    status="a",
    created_at=datetime.utcnow(),
    created_by=2,
    locale=""
)
bot_schema_1 = BotSchema(
    bot_id=1,
    **bot_schema_without_id_1.model_dump()
)
bot_schema_2 = BotSchema(
    bot_id=2,
    **bot_schema_without_id_2.model_dump()
)

order_schema_1 = OrderSchema(
    id="asdF5",
    bot_id=BOT_ID,
    products={1: 2, 2: 1},
    from_user=1,
    payment_method="Картой онлайн",
    ordered_at=datetime.utcnow(),
    address="Москва",
    status=OrderStatusValues.BACKLOG,
    comment="Позвонтить за 10 минут"
)
order_schema_2 = OrderSchema(
    order_id="qw3D2",
    bot_id=BOT_ID,
    products={1: 1},
    from_user=1,
    payment_method="Картой онлайн",
    ordered_at=datetime.utcnow(),
    address="Москва",
    status=OrderStatusValues.BACKLOG,
    comment="Позвонтить за 20 минут"
)

product_schema_without_id_1 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox",
    description="",
    price=21000,
    count=5,
    picture="asd4F.jpg"
)
product_schema_without_id_2 = ProductWithoutId(
    bot_id=BOT_ID,
    name="Xbox Series X",
    description="",
    price=31000,
    count=6,
    picture="sa123.jpg"
)
product_schema_1 = ProductSchema(
    id=1,
    **product_schema_without_id_1.model_dump()
)
product_schema_2 = ProductSchema(
    id=2,
    **product_schema_without_id_2.model_dump()
)

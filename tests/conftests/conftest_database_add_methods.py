import pytest

from database.models.payment_model import PaymentSchema, PaymentDao


@pytest.fixture
async def add_payments(payment_schemas: list[PaymentSchema], payment_db: PaymentDao) -> list[PaymentSchema]:
    for payment_schema in payment_schemas:
        await payment_db.add_payment(payment_schema)
    return payment_schemas

from database.models.payment_model import PaymentSchema, PaymentDao


class TestPaymentModel:
    """Tests for PaymentDao"""
    async def test_get_all_payments(self, payments: list[PaymentSchema], payment_db: PaymentDao, add_payments):
        schemas = await payment_db.get_all_payments()

        assert schemas
        for schema in schemas:
            assert schema in payments

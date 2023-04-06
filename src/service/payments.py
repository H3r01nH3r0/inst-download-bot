from src import tables
from src.database import Session
from src.models.payments import CreatePayment, UpdatePayment


class PaymentService:
    def __init__(self):
        self.session = Session()

    async def create(self, payment_data: CreatePayment) -> tables.Payments:
        payment = tables.Payments(
            **payment_data.dict()
        )
        self.session.add(payment)
        self.session.commit()
        return payment

    async def get(self, user_id: int, payment_id: str) -> tables.Payments:
        payment = (
            self.session
            .query(tables.Payments)
            .filter_by(
                user_id=user_id,
                payment_id=payment_id
            )
            .first()
        )
        return payment

    async def get_saved(self, user_id: int) -> tables.Payments:
        payment = (
            self.session
            .query(tables.Payments)
            .filter_by(
                user_id=user_id,
                payment_saved=True
            )
            .first()
        )
        return payment

    async def update(self, user_id: int, payment_id: str, payment_data: UpdatePayment) -> tables.Payments:
        payment = await self.get(user_id, payment_id)

        for field, value in payment_data:
            setattr(payment, field, value)

        self.session.commit()
        return payment

    async def delete(self, user_id: int, payment_id: str) -> None:
        payment = await self.get(user_id, payment_id)
        self.session.delete(payment)
        self.session.commit()
        return
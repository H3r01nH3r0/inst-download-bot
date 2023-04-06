from src import tables
from src.database import Session
from src.models.discount import CreateDiscount


class DiscountService:
    def __init__(self):
        self.session = Session()

    async def create(self, discount_data: CreateDiscount) -> tables.Discount:
        discount = tables.Discount(
            **discount_data.dict()
        )
        self.session.add(discount)
        self.session.commit()
        return discount

    async def get(self, discount_id: int) -> tables.Discount:
        discount = (
            self.session
            .query(tables.Discount)
            .filter_by(discount_id=discount_id)
            .first()
        )
        return discount

    async def delete(self, discount_id: int) -> None:
        discount = await self.get(discount_id)
        self.session.delete(discount)
        self.session.commit()
        return
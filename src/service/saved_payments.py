from src import tables
from src.database import Session
from src.models.saved_payments import CreateSavePay


class SavePayService:
    def __init__(self):
        self.session = Session()

    async def create(self, pay_data: CreateSavePay) -> tables.SavedPayments:
        result = tables.SavedPayments(
            **pay_data.dict()
        )
        self.session.add(result)
        self.session.commit()

    async def get(self, user_id: int) -> tables.SavedPayments:
        result = (
            self.session
            .query(tables.SavedPayments)
            .filter_by(user_id=user_id)
            .first()
        )
        return result

    async def delete(self, user_id: int) -> None:
        result = await self.get(user_id)
        self.session.delete(result)
        self.session.commit()
        return

from src import tables
from src.database import Session
from src.models.subscribers import CreateSubscriber, UpdateSubscriber


class SubsService:
    def __init__(self):
        self.session = Session()

    async def create(self, sub_data: CreateSubscriber) -> tables.Subscribers:
        sub = tables.Subscribers(
            **sub_data.dict()
        )
        self.session.add(sub)
        self.session.commit()
        return sub

    async def get(self, user_id: int) -> tables.Subscribers:
        sub = (
            self.session
            .query(tables.Subscribers)
            .filter_by(user_id=user_id)
            .first()
        )
        return sub

    async def update(self, user_id: int, sub_data: UpdateSubscriber) -> tables.Subscribers:
        sub = await self.get(user_id)
        for field, value in sub_data:
            setattr(sub, field, value)
        self.session.commit()
        return sub

    async def delete(self, user_id: int) -> None:
        sub = await self.get(user_id)
        self.session.delete(sub)
        self.session.commit()

    async def end_of_time(self, now: int) -> None:
        subs = (
            self.session
            .query(tables.Subscribers)
            .filter(tables.Subscribers.end_time <= now)
            .all()
        )
        return subs

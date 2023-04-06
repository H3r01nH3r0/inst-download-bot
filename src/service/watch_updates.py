from typing import List

from src import tables
from src.database import Session
from src.models.watch_updates import CreateWatch, UpdateWatch


class WatchService:
    def __init__(self):
        self.session = Session()

    async def create(self, watch_data: CreateWatch) -> tables.WatchUpdates:
        new_watch = tables.WatchUpdates(
            **watch_data.dict()
        )
        self.session.add(new_watch)
        self.session.commit()
        return new_watch

    async def get(self, user_id: int, target_id: str) -> tables.WatchUpdates:
        result = (
            self.session
            .query(tables.WatchUpdates)
            .filter_by(
                user_id=user_id,
                target_id=target_id
            )
            .first()
        )
        return result

    async def get_by_username(self, user_id: int, username: str) -> tables.WatchUpdates:
        result = (
            self.session
            .query(tables.WatchUpdates)
            .filter_by(
                user_id=user_id,
                target_username=username
            )
            .first()
        )
        return result

    async def get_all(self) -> List[tables.WatchUpdates]:
        result = (
            self.session
            .query(tables.WatchUpdates)
            .all()
        )
        return result

    async def get_users_subs(self, user_id: int) -> List[tables.WatchUpdates]:
        subs = (
            self.session
            .query(tables.WatchUpdates)
            .filter_by(user_id=user_id)
            .all()
        )
        return subs

    async def update(self, watch_data: UpdateWatch) -> tables.WatchUpdates:
        watch = await self.get(watch_data.user_id, watch_data.target_id)
        for field, value in watch_data:
            setattr(watch, field, value)
        self.session.commit()
        return watch

    async def delete(self, user_id: int, target_username: str) -> None:
        watch = (
            self.session
            .query(tables.WatchUpdates)
            .filter_by(
                user_id=user_id,
                target_username=target_username
            )
            .first()
        )
        self.session.delete(watch)
        self.session.commit()
        return

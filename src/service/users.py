from typing import List

from src import tables
from src.database import Session
from src.models.users import CreateUser, UpdateUser


class UsersService:
    def __init__(self):
        self.session = Session()

    async def create(self, user_data: CreateUser) -> tables.Users:
        user = tables.Users(
            **user_data.dict()
        )
        self.session.add(user)
        self.session.commit()
        return user

    async def get(self, user_id: int) -> tables.Users:
        user = (
            self.session
            .query(tables.Users)
            .filter_by(user_id=user_id)
            .first()
        )
        return user

    async def get_users(self) -> List[tables.Users]:
        users = (
            self.session
            .query(tables.Users)
            .all()
        )
        result = [user for user in users if not user.tariff]
        return result

    async def get_all(self) -> int:
        users = (
            self.session
            .query(tables.Users)
            .all()
        )
        return len(users)

    async def update(self, user_id: int, user_data: UpdateUser) -> tables.Users:
        user = await self.get(user_id)
        for field, value in user_data:
            setattr(user, field, value)
        self.session.commit()
        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get(user_id)
        self.session.delete(user)
        self.session.commit()

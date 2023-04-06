from typing import List

from src import tables
from src.database import Session
from src.models.user_requests import CreateRequest


class RequestService:
    def __init__(self):
        self.session = Session()

    async def create(self, request_data: CreateRequest) -> tables.UsersRequests:
        request = tables.UsersRequests(
            **request_data.dict()
        )
        self.session.add(request)
        self.session.commit()
        return request

    async def get_all(self, user_id: int) -> List[tables.UsersRequests]:
        requests = (
            self.session
            .query(tables.UsersRequests)
            .filter_by(user_id=user_id)
            .all()
        )
        return requests

    async def get(self, user_id: int, request_id: int) -> tables.UsersRequests:
        request = (
            self.session
            .query(tables.UsersRequests)
            .filter_by(
                id=request_id,
                user_id=user_id
            )
            .first()
        )
        return request

    async def request_exists(self, user_id: int, request_name: str) -> tables.UsersRequests:
        request = (
            self.session
            .query(tables.UsersRequests)
            .filter_by(
                user_id=user_id,
                request_name=request_name
            )
            .first()
        )
        return request

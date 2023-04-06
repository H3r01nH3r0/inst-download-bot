from typing import List

from src import tables
from src.database import Session


class AdminRefService:
    def __init__(self):
        self.session = Session()

    async def create(self, channel_name: str, link: str):
        admin_ref = tables.AdminRefs(
            channel_name=channel_name,
            link=link
        )
        self.session.add(admin_ref)
        self.session.commit()
        return

    async def get(self, link: str) -> tables.AdminRefs:
        res = (
            self.session
            .query(tables.AdminRefs)
            .filter_by(link=link)
            .first()
        )
        return res

    async def get_all(self) -> List[tables.AdminRefs]:
        res = (
            self.session
            .query(tables.AdminRefs)
            .all()
        )
        return res

    async def update(self, link: str, count: int):
        admin_ref = await self.get(link)
        setattr(admin_ref, "count", count)
        self.session.commit()
        return admin_ref

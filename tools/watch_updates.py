import asyncio
import aioschedule as schedule

from src.service.watch_updates import WatchService


class UserUpdates:
    def __init__(self):
        self.watch_db = WatchService()

    def send_updates(self):
        users_to_check = self.watch_db.get_all()

from datetime import datetime

from pydantic import BaseModel


class BaseSubscriber(BaseModel):
    user_id: int
    start_time: datetime
    end_time: datetime


class CreateSubscriber(BaseSubscriber):
    pass


class UpdateSubscriber(BaseSubscriber):
    pass


class Subscriber(BaseSubscriber):
    id: int

    class Config:
        orm_mode = True

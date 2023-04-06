from datetime import datetime

from pydantic import BaseModel


class BaseWatch(BaseModel):
    user_id: int
    target_username: str
    target_id: str
    last_watch: datetime


class CreateWatch(BaseWatch):
    pass


class UpdateWatch(BaseWatch):
    pass


class Watch(BaseWatch):
    id: int

    class Config:
        orm_mode = True

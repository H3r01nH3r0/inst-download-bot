from typing import List, Tuple

from pydantic import BaseModel


class BaseMedia(BaseModel):
    username: str
    user_id: str
    media_pk: int
    media_type: int
    caption: str


class CreateMedia(BaseMedia):
    url_list: List[Tuple[int, str]]


class Media(BaseMedia):
    id: int

    class Config:
        orm_mode = True

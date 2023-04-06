from pydantic import BaseModel


class BaseRequest(BaseModel):
    user_id: int
    request_name: str
    request_link: str


class CreateRequest(BaseRequest):
    pass


class Request(BaseRequest):
    id: int

    class Config:
        orm_mode = True

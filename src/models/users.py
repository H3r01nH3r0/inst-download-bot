from pydantic import BaseModel


class BaseUser(BaseModel):
    user_id: int
    username: str


class CreateUser(BaseUser):
    pass


class UpdateBalance(BaseUser):
    balance: int


class UpdateUser(BaseUser):
    tariff: str


class User(BaseUser):
    id: int
    tariff: str
    balance: int

    class Config:
        orm_mode = True

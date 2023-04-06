from datetime import datetime

from pydantic import BaseModel


class BaseDiscount(BaseModel):
    discount_value: int
    discount_id: int
    expire_date: datetime


class CreateDiscount(BaseDiscount):
    pass


class Discount(BaseDiscount):
    id: int

    class Config:
        orm_mode = True

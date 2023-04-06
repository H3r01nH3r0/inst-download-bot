from pydantic import BaseModel


class BasePayment(BaseModel):
    payment_id: str
    user_id: int
    user_email: str
    payment_url: str
    payment_description: str


class CreatePayment(BasePayment):
    pass


class UpdatePayment(BasePayment):
    pass


class Payments(BasePayment):
    id: int

    class Config:
        orm_mode = True

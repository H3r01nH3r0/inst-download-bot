from pydantic import BaseModel


class BaseSavePay(BaseModel):
    user_id: int
    email: str
    card: str
    method_id: str


class CreateSavePay(BaseSavePay):
    pass


class SavePay(BaseSavePay):
    id: int

    class Config:
        orm_mode = True

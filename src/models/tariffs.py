from pydantic import BaseModel


class BaseTariff(BaseModel):
    tariff_price: int
    tariff_days: int


class CreateTariff(BaseTariff):
    pass


class UpdateTariff(BaseTariff):
    pass


class Tariff(BaseTariff):
    id: int

    class Config:
        orm_mode = True

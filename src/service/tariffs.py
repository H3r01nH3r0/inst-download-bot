from typing import List

from src import tables
from src.database import Session
from src.models.tariffs import CreateTariff, UpdateTariff


class TariffService:
    def __init__(self):
        self.session = Session()

    async def create(self, tariff_data: CreateTariff) -> tables.Tariffs:
        tariff = tables.Tariffs(
            **tariff_data.dict()
        )
        self.session.add(tariff)
        self.session.commit()

    async def get(self, tariff_id: int) -> tables.Tariffs:
        tariff = (
            self.session
            .query(tables.Tariffs)
            .filter_by(id=tariff_id)
            .first()
        )
        return tariff

    async def get_all(self) -> List[tables.Tariffs]:
        tariffs = (
            self.session
            .query(tables.Tariffs)
            .all()
        )
        return tariffs

    async def get_cheep(self):
        tariffs = await self.get_all()
        cheep = tariffs[0]
        for tariff in tariffs[1:]:
            if tariff.tariff_price < cheep.tariff_price:
                cheep = tariff
                continue
            else:
                continue
        return cheep

    async def update(self, tariff_id: int, tariff_data: UpdateTariff) -> tables.Tariffs:
        tariff = await self.get(tariff_id)
        for field, value in tariff_data:
            setattr(tariff, field, value)
        self.session.commit()
        return tariff

    async def delete(self, tariff_id: int) -> None:
        tariff = await self.get(tariff_id)
        self.session.delete(tariff)
        self.session.commit()

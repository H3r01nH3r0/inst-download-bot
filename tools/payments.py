from time import sleep

from yookassa import Configuration, Payment

from src.models.discount import Discount
from src.models.payments import CreatePayment, Payments
from src.models.tariffs import Tariff

Configuration.account_id = 978631
Configuration.secret_key = "live_LbfRHn9eUaIzWc3stX708nmpXAVMX9LCENGtwlDk010"


def create_balance_payment(balance_value: int, user_email: str, user_id: int) -> CreatePayment:
    payment = Payment.create({
        "amount": {
            "value": f"{balance_value}",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/anonsavebot"
        },
        "receipt": {
            "email": user_email,
            "items": [
                {
                    "description": "Пополнение внутреннего баланса",
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{balance_value}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        },
        # "save_payment_method": True,
        "capture": True,
        "description": f"Пополнение баланса на {balance_value}₽"
    })
    user_payment = CreatePayment(
        payment_id=payment.id,
        user_id=user_id,
        user_email=user_email,
        payment_description="add_balance",
        payment_url=payment.confirmation.confirmation_url
    )
    return user_payment


def create_subs_payment(tariff: Tariff, user_email: str, user_id: int, discount_value: float = 1.0) -> CreatePayment:
    payment = Payment.create({
        "amount": {
            "value": f"{int(tariff.tariff_price * discount_value)}",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/anonsavebot"
        },
        "receipt": {
            "email": user_email,
            "items": [
                {
                    "description": "Оплата подписки",
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{int(tariff.tariff_price * discount_value)}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        },
        # "save_payment_method": True,
        "capture": True,
        "description": f"Опата подписки на {tariff.tariff_days} дней"
    })
    user_payment = CreatePayment(
        payment_id=payment.id,
        user_id=user_id,
        user_email=user_email,
        payment_description=f"tariff_id={tariff.id}",
        payment_url=payment.confirmation.confirmation_url
    )
    return user_payment


def auto_payment(method_id: str, tariff: Tariff, user_email: str) -> bool:
    payment = Payment.create({
        "amount": {
            "value": tariff.tariff_price,
            "currency": "RUB"
        },
        "receipt": {
            "email": user_email,
            "items": [
                {
                    "description": "Оплата подписки",
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{tariff.tariff_price}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        },
        "capture": True,
        "payment_method_id": method_id,
        "description": f"Опата подписки на {tariff.tariff_days} дней"
    })
    sleep(10)
    return payment.paid


def check_payment(payment_id: str):
    payment = Payment.find_one(payment_id)
    return payment


def save_payment_method(payment_id: str) -> str:
    payment = Payment.find_one(payment_id)
    if payment.payment_method.saved:
        return payment.payment_method.id, payment.payment_method.title
    else:
        return False

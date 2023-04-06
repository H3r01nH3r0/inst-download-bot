from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.models.discount import Discount
from src.models.payments import Payments
from src.models.tariffs import Tariff
from src.models.user_requests import Request
from src.models.watch_updates import Watch


class Keyboards:
    def __init__(self, config):
        self.config = config

    def main_keyboard(self, price: int, days: int, tariff_id: int) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["stock"].format(price, days),
                callback_data=f"tariffs_{tariff_id}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["tariff-unlimited"],
                callback_data="tariff-unlimited"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["watch-stories"],
                callback_data="watch-stories"
            ),
            InlineKeyboardButton(
                text=self.config["download-post"],
                callback_data="download-post"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["highlights"],
                callback_data="highlights"
            ),
            InlineKeyboardButton(
                text=self.config["balance"],
                callback_data="balance"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["requests"],
                callback_data="requests"
            ),
            InlineKeyboardButton(
                text=self.config["my_subs"],
                callback_data="my_subs"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["subs"],
                callback_data="subs"
            ),
            InlineKeyboardButton(
                text=self.config["support"],
                url=self.config["support_url"]
            )
        )
        return markup

    def payments(self, add_balance: int = None, tariff_id: int = None) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if add_balance:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["card"],
                    callback_data=f"create_payment_link=add_balance_{add_balance}"
                )
            )
        if tariff_id:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["card"],
                    callback_data=f"create_payment_link=tariff_id_{tariff_id}"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def unlimited_vars(self, tariffs: List[Tariff], discount: Discount = None) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if discount:
            value = 1 - discount.discount_value / 100
        else:
            value = 1
        for item in tariffs:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["default_tariff"].format(item.tariff_days, int(item.tariff_price * value)),
                    callback_data=f"tariffs_{item.id}"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def add_balance(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        row = list()
        for key, value in self.config["add_balance"].items():
            button = InlineKeyboardButton(
                text=value,
                callback_data=key
            )
            row.append(button)
        markup.row(*row)
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def back_home(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def my_subscriptions(self, is_subscribed: bool = False) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if not is_subscribed:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["stock"],
                    callback_data="stock"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def download_post(self, tariff_id: int) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["unlimited"],
                callback_data=f"tariffs_{tariff_id}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["download_once"],
                callback_data="download_once"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def get_content(self, tariff: Tariff) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["stock"].format(tariff.tariff_price, tariff.tariff_days),
                callback_data=f"tariffs_{tariff.id}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def user_request(self, requests: List[Request]) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if requests:
            for request in requests:
                markup.add(
                    InlineKeyboardButton(
                        text=request.request_name,
                        callback_data=f"request={request.request_name}"
                    )
                )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def watch_updates(self, target_name: str, more: bool = False, more_posts: bool = False) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if more:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["all_stories"],
                    callback_data="all_stories"
                )
            )
        elif more_posts:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["all_posts"],
                    callback_data="all_posts"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["watch-updates"],
                callback_data=f"watch-updates={target_name}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def cancel_sub(self, is_save_pay: bool = False) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if is_save_pay:
            markup.add(
                InlineKeyboardButton(
                    text=self.config["cancel_auto_pay"],
                    callback_data="cancel_auto_pay"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def carousel(self, user_poss: Tuple[int, int], target_name: str, story: bool = False) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        content_type = "post" if not story else "story"
        markup.add(
            InlineKeyboardButton(
                text=self.config["watch-updates"],
                callback_data=f"watch-updates={target_name}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["prev"],
                callback_data=f"prev_{content_type}"
            ),
            InlineKeyboardButton(
                text=self.config["user_poss"].format(*user_poss),
                callback_data="Empty"
            ),
            InlineKeyboardButton(
                text=self.config["next"],
                callback_data=f"next_{content_type}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def check_payment(self, payment: Payments) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["payment_link"],
                url=payment.payment_url
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["check_payment"],
                callback_data=f"check_payment={payment.payment_id}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def list_subscriptions(self, subs: List[Watch]) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        for sub in subs:
            markup.add(
                InlineKeyboardButton(
                    text=sub.target_username,
                    callback_data=f"unwatch={sub.target_username}"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["home"],
                callback_data="home"
            )
        )
        return markup

    def admin_panel(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["give_subscription"],
                callback_data="give_subscription"
            ),
            InlineKeyboardButton(
                text=self.config["create_ref_link"],
                callback_data="create_ref_link"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["adv_mailing"],
                callback_data="adv_mailing"
            ),
            InlineKeyboardButton(
                text=self.config["discount_mailing"],
                callback_data="discount_mailing"
            )
        )
        # markup.add(
        #     InlineKeyboardButton(
        #         text=self.config["add_proxy"],
        #         callback_data="proxy"
        #     )
        # )
        markup.add(
            InlineKeyboardButton(
                text=self.config["show_referals"],
                callback_data="show_referals"
            )
        )
        markup.add(
            InlineKeyboardButton(
                text=self.config["admin_home"],
                callback_data="admin_home"
            )
        )
        return markup

    def back_admin(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text=self.config["admin_home"],
                callback_data="admin_home"
            )
        )
        return markup

    @staticmethod
    def from_str(text: str) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        for line in text.split("\n"):
            sign, url = line.split(" - ")
            markup.add(InlineKeyboardButton(text=sign, url=url))
        markup.to_python()
        return markup

    def admin_give_subscription(self, tariffs: List[Tariff]) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        for tariff in tariffs:
            markup.add(
                InlineKeyboardButton(
                    text=f"Выдать подписку на {tariff.tariff_days}",
                    callback_data=f"admin_give_tariff={tariff.id}"
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=self.config["admin_home"],
                callback_data="admin_home"
            )
        )
        return markup

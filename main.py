import asyncio
import datetime
import random
import string
import time
import urllib
from urllib import request
from asyncio import sleep
from typing import Tuple, List

import aioschedule
from aiogram import Bot, Dispatcher, types, executor, filters
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hlink
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.models.discount import CreateDiscount
from src.models.saved_payments import CreateSavePay
from src.models.subscribers import CreateSubscriber, UpdateSubscriber, Subscriber
from src.models.tariffs import Tariff
from src.models.user_requests import CreateRequest
from src.models.users import CreateUser, User, UpdateBalance, UpdateUser
from src.models.watch_updates import UpdateWatch, CreateWatch
from src.service.admin_refs import AdminRefService
from src.service.discount import DiscountService
from src.service.payments import PaymentService
from src.service.requests import RequestService
from src.service.saved_payments import SavePayService
from src.service.subscribers import SubsService
from src.service.tariffs import TariffService
from src.service.users import UsersService
from src.service.watch_updates import WatchService

from tools.download import DownloadService
from tools.keyboards import Keyboards
from tools.payments import create_balance_payment, create_subs_payment, check_payment, auto_payment, save_payment_method
from tools.utils import get_config, save_config, username_from_link, is_link, str2file

config_filename = 'config.json'
config = get_config(config_filename)

bot = Bot(token=config["bot_token"], parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
owners_filter = filters.IDFilter(user_id=config['owners'])

log_file = open("logs.txt", "a")

user_db = UsersService()
tariff_db = TariffService()
sub_db = SubsService()
request_db = RequestService()
payments_db = PaymentService()
save_pay_db = SavePayService()
watch_db = WatchService()
discount_db = DiscountService()
ref_db = AdminRefService()
download_service = DownloadService(config["instagram_accounts"])

keyboards = Keyboards(config["keyboards"])

user_data = dict()

user_poss = dict()

user_payment = dict()

user_discount = dict()


class Form(StatesGroup):
    mailing = State()
    mailing_markup = State()
    user_id = State()
    discount_mailing = State()
    discount_value = State()
    channel_name = State()


class UserLink(StatesGroup):
    user_link = State()


class CreatePayment(StatesGroup):
    user_email = State()


class CancelSubscription(StatesGroup):
    user_email = State()


class UploadProxy(StatesGroup):
    file = State()


async def process(users: list, kwargs: dict):
    total = 0
    sent = 0
    unsent = 0
    for user in users:
        kwargs['chat_id'] = user
        try:
            await bot.copy_message(**kwargs)
            sent += 1
        except:
            unsent += 1
        await sleep(config["sleep_time"])
        total += 1
    return total, sent, unsent


async def sub_proc(users: list, kwargs: dict):
    number = len(users) // 5
    t = 0
    s = 0
    u = 0
    for total, sent, unsent in await asyncio.gather(
        process(users[:number], kwargs),
        process(users[number:2 * number], kwargs),
        process(users[2 * number:3 * number], kwargs),
        process(users[3 * number:4 * number], kwargs),
        process(users[4 * number:], kwargs)
    ):
        t += total
        s += sent
        u += unsent
    return t, s, u


async def check_subs_balance(subscribers: List[Subscriber]) -> None:
    for subscriber in subscribers:
        saved_payment = await save_pay_db.get(subscriber.user_id)
        user = await user_db.get(subscriber.user_id)
        tariff = await tariff_db.get(user.tariff)
        balance = user.balance
        if balance >= tariff.tariff_price:
            new_balance = balance - tariff.tariff_price
            new_time = subscriber.end_time + datetime.timedelta(days=tariff.tariff_days)
            update_user = UpdateBalance(
                user_id=user.user_id,
                username=user.username,
                balance=new_balance
            )
            await user_db.update(user.user_id, update_user)
            update_subscriber = UpdateSubscriber(
                user_id=user.user_id,
                start_time=subscriber.start_time,
                end_time=new_time
            )
            await sub_db.update(user.user_id, update_subscriber)
        elif saved_payment:
            if auto_payment(saved_payment.method_id, tariff, saved_payment.email):
                new_time = subscriber.end_time + datetime.timedelta(days=tariff.tariff_days)
                update_subscriber = UpdateSubscriber(
                    user_id=user.user_id,
                    start_time=subscriber.start_time,
                    end_time=new_time
                )
                await sub_db.update(user.user_id, update_subscriber)
        else:
            await sub_db.delete(user.user_id)
            update_user = UpdateUser(
                user_id=user.user_id,
                username=user.username,
                tariff=0
            )
            await user_db.update(user.user_id, update_user)


async def timeout_checker() -> List[Subscriber]:
    while True:
        now = datetime.datetime.utcnow()
        timeout_subs = await sub_db.end_of_time(now)
        await check_subs_balance(timeout_subs)
        await sleep(3600)


async def download_media(user_id: int):
    user_content = user_data[user_id]
    link = user_content["link"]
    if user_content["content_type"] == "download-post":
        return download_service.download_post(link)
    elif user_content["content_type"] == "highlights":
        return download_service.download_highlights(link)
    return


async def send_story(user_id, story_info):
    try:
        media_type, value = download_service.download_story(story_info)[0]
        media = types.MediaGroup()
        if media_type == 1:
            media.attach_photo(value)
        elif media_type == 2:
            media.attach_video(value)
        await bot.send_media_group(
            user_id,
            media=media
        )
    except Exception as a:
        log_file.write(str(a))


async def get_posts(user_id: int):
    try:
        now_poss, end_poss = user_poss[user_id]
        post_info = user_data[user_id]["request"]["content"][now_poss - 1]
        target_name = user_data[user_id]["request"]["username"]
        await send_user_media(post_info, user_id)
        await bot.send_message(
            user_id,
            text=config["text"]["request_info_1"].format(
                target_name,
                f"https://www.instagram.com/{target_name}"
            ),
            reply_markup=keyboards.carousel(
                user_poss[user_id],
                target_name,
                story=False
            ),
            disable_web_page_preview=True
        )
    except Exception as a:
        log_file.write(str(a))


async def get_all_stories(user_id: int):
    try:
        now_poss, end_poss = user_poss[user_id]
        story_info = user_data[user_id]["request"][now_poss - 1]
        target_name = user_data[user_id]["target_name"]
        await send_story(user_id, story_info)
        await bot.send_message(
            user_id,
            text=config["text"]["request_info_1"].format(
                target_name,
                f"https://www.instagram.com/{target_name}"
            ),
            reply_markup=keyboards.carousel(
                user_poss[user_id],
                target_name,
                story=True
            ),
            disable_web_page_preview=True
        )
    except Exception as a:
        log_file.write(str(a))


async def send_user_media(media_info: Tuple[int, str], user_id):
    try:
        media_type, media_link = media_info
        media = types.MediaGroup()
        if media_type == 1:
            media.attach_photo(media_link)
        elif media_type == 2:
            media.attach_video(media_link)
        await bot.send_media_group(
            user_id,
            media=media
        )
    except Exception as a:
        log_file.write(a)


async def send_media(user_id: int):
    try:
        user_content = user_data[user_id]
        if user_content["content_type"] == "watch-stories":
            target_name = username_from_link(user_content["link"])
            user_content["target_name"] = target_name
            user_request = await request_db.request_exists(user_id, target_name)
            if not user_request:
                new_request = CreateRequest(
                    user_id=user_id,
                    request_name=target_name,
                    request_link=f"https://www.instagram.com/{target_name}"
                )
                await request_db.create(new_request)
            target_stories = download_service.get_stories(target_name)
            user_content["request"] = target_stories
            if not target_stories:
                await bot.send_message(
                    user_id,
                    text=config["text"]["no_stories"],
                    reply_markup=keyboards.back_home()
                )
                return
            if len(target_stories) > 1:
                user_poss[user_id] = (1, len(target_stories))
                await send_story(user_id, target_stories[0])
                await bot.send_message(
                    user_id,
                    text=config["text"]["request_info_3"].format(
                        target_name,
                        f"https://www.instagram.com/{target_name}",
                        len(target_stories)
                    ),
                    reply_markup=keyboards.watch_updates(target_name, more=True),
                    disable_web_page_preview=True
                )
            else:
                await send_story(user_id, target_stories[0])
                await bot.send_message(
                    user_id,
                    text=config["text"]["request_info_1"].format(
                        target_name,
                        f"https://www.instagram.com/{target_name}"
                    ),
                    reply_markup=keyboards.watch_updates(target_name),
                    disable_web_page_preview=True
                )
            return
        else:
            if not is_link(user_content["link"]):
                await bot.send_message(
                    user_id,
                    text=config["text"]["link_error"],
                    reply_markup=keyboards.back_home()
                )
                return
            output = await download_media(user_id)
            user_request = await request_db.request_exists(user_id, output["username"])
            if not user_request:
                new_request = CreateRequest(
                    user_id=user_id,
                    request_name=output["username"],
                    request_link=output["link"]
                )
                await request_db.create(new_request)

            await send_user_media(output["content"][0], user_id)
            if len(output["content"]) > 1:
                user_content["request"] = output
                user_poss[user_id] = (1, len(output["content"]))
                await bot.send_message(
                    user_id,
                    text=config["text"]["request_info_4"].format(
                        output["username"],
                        output["caption"],
                        output["link"],
                        len(output["content"]) - 1
                    ),
                    reply_markup=keyboards.watch_updates(output["username"], more_posts=True)
                )
            else:
                await bot.send_message(
                    user_id,
                    text=config["text"]["request_info_2"].format(
                        output["username"],
                        output["caption"],
                        output["link"]
                    ),
                    reply_markup=keyboards.watch_updates(output["username"])
                )
    except KeyError:
        await bot.send_message(
            user_id,
            text=config["text"]["error"],
            reply_markup=keyboards.back_home()
        )


async def send_updates():
    while True:
        await sleep(43200)
        users_to_check = await watch_db.get_all()
        for checking in users_to_check:
            is_sub = await sub_db.get(checking.user_id)
            if not is_sub:
                continue
            user_stories = await download_service.check_stories(checking.target_username, checking.last_watch)
            user_posts = await download_service.check_posts(checking.target_id, checking.last_watch)
            user_content = user_stories + user_posts
            if user_content:
                for media_info in user_content:
                    await send_user_media(media_info, checking.user_id)
                await bot.send_message(
                    checking.user_id,
                    text=f"Новые публикации пользователя {checking.target_username}!\n"
                         f"Ссылка: https://www.instagram.com/{checking.target_username}"
                )
            now_time = datetime.datetime.utcnow()
            new_watch = UpdateWatch(
                user_id=checking.user_id,
                target_username=checking.target_username,
                target_id=checking.target_id,
                last_watch=now_time
            )
            await watch_db.update(new_watch)


async def check_discount(user_id):
    if user_id in user_discount.keys():
        discount = await discount_db.get(user_discount[user_id])
        if discount.expire_date < datetime.datetime.utcnow():
            await discount_db.delete(user_discount[user_id])
            res_discount = None
        else:
            res_discount = discount
    else:
        res_discount = None
    return res_discount


async def home_page(user: User, tariff: Tariff) -> None:
    try:
        if not user.tariff:
            if user.user_id in user_discount.keys():
                discount = await discount_db.get(user_discount[user.user_id])
                if discount.expire_date < datetime.datetime.utcnow():
                    await discount_db.delete(user_discount[user.user_id])
                    tariff_price = tariff.tariff_price
                else:
                    tariff_price = int(tariff.tariff_price * (1 - discount.discount_value/100))
            else:
                tariff_price = tariff.tariff_price
            await bot.send_message(
                user.user_id,
                text=config["text"]["home_page_1"].format(
                    user.username,
                    user.user_id,
                    tariff_price,
                    tariff.tariff_days
                ),
                reply_markup=keyboards.main_keyboard(tariff_price, tariff.tariff_days, tariff.id)
            )
        else:
            sub = await sub_db.get(user.user_id)
            await bot.send_message(
                user.user_id,
                text=config["text"]["home_page_2"].format(
                    user.username,
                    sub.end_time.strftime("%H:%M %d-%m-%Y"),
                    user.user_id,
                    tariff.tariff_price,
                    tariff.tariff_days
                ),
                reply_markup=keyboards.main_keyboard(tariff.tariff_price, tariff.tariff_days, tariff.id)
            )
        return
    except Exception as a:
        log_file.write(str(a))


async def admin_home(admin_id: int):
    await bot.send_message(
        admin_id,
        text=config["text"]["admin_home"],
        reply_markup=keyboards.admin_panel()
    )


@dp.message_handler(owners_filter, commands=["admin"])
async def admin_handler(message: types.Message):
    await admin_home(message.from_user.id)


@dp.message_handler(commands=["count"])
async def count_handler(message: types.Message):
    users_count = await user_db.get_all()
    await bot.send_message(
        message.from_user.id,
        text=f"Пользователей в БД: {users_count}"
    )


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    try:
        base_tariff = await tariff_db.get_cheep()
        user = await user_db.get(message.from_user.id)
        if not user:
            args = message.text.split(' ')
            args = args[-1]
            if args.startswith('__'):
                link = f'https://t.me/{config["bot_user_name"]}?start={args}'
                ref_count = await ref_db.get(link)
                new_count = ref_count.count + 1
                await ref_db.update(link, new_count)
            user = CreateUser(
                user_id=message.from_user.id,
                username=message.from_user.username
            )
            user = await user_db.create(user)
        await home_page(user, base_tariff)
    except Exception as a:
        log_file.write(str(a))


@dp.callback_query_handler(state="*")
async def callback_query_handler(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        if callback_query.data == "home":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await state.finish()
            base_tariff = await tariff_db.get_cheep()
            user = await user_db.get(callback_query.from_user.id)
            await home_page(user, base_tariff)

        elif callback_query.data in ["watch-stories", "download-post", "highlights"]:
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            user_content = user_data[callback_query.from_user.id] = dict()
            user_content["content_type"] = callback_query.data
            await UserLink.user_link.set()
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"][callback_query.data],
                reply_markup=keyboards.back_home()
            )

        elif callback_query.data == "tariff-unlimited":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            tariff_list = await tariff_db.get_all()

            res_discount = await check_discount(callback_query.from_user.id)

            link = hlink(config["text"]["term_of_use"], config["text"]["term_of_use_link"])
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"][callback_query.data].format(link),
                reply_markup=keyboards.unlimited_vars(tariff_list, discount=res_discount),
                disable_web_page_preview=True
            )

        elif callback_query.data == "balance":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            user = await user_db.get(callback_query.from_user.id)
            await bot.send_message(
                user.user_id,
                text=config["text"][callback_query.data].format(user.balance),
                reply_markup=keyboards.add_balance()
            )

        elif callback_query.data.startswith("tariffs_"):
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            res_discount = await check_discount(callback_query.from_user.id)
            if res_discount:
                discount = res_discount.discount_value
            else:
                discount = 0
            item_id = int(callback_query.data.split("_")[-1])
            tariff = await tariff_db.get(item_id)
            link = hlink(config["text"]["term_of_use"], config["text"]["term_of_use_link"])
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["buy_tariff"].format(
                    int(tariff.tariff_price * (1 - discount/100)),
                    tariff.tariff_days, link
                ),
                reply_markup=keyboards.payments(tariff_id=tariff.id),
                disable_web_page_preview=True
            )

        elif callback_query.data.startswith("add_"):
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            value = int(callback_query.data.split("_")[-1])
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["add_balance"].format(value),
                reply_markup=keyboards.payments(add_balance=value)
            )

        elif callback_query.data == "requests":
            resent = await request_db.get_all(callback_query.from_user.id)
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["request_history"],
                reply_markup=keyboards.user_request(resent)
            )

        elif callback_query.data.startswith("request="):
            try:
                user_content = user_data[callback_query.from_user.id]
            except KeyError:
                user_content = user_data[callback_query.from_user.id] = dict()
            user_content["link"] = callback_query.data.split("=")[-1]
            user_content["content_type"] = "watch-stories"
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["start_search"]
            )
            await send_media(callback_query.from_user.id)

        elif callback_query.data == "download_once":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            user = await user_db.get(callback_query.from_user.id)
            price = config["download_post_price"]
            if user.balance >= price:
                new_balance = user.balance - price
                update_user = UpdateBalance(
                    user_id=callback_query.from_user.id,
                    username=callback_query.from_user.username,
                    balance=new_balance
                )
                await user_db.update(callback_query.from_user.id, update_user)
                if user_data[callback_query.from_user.id]["content_type"] != "watch-stories":
                    await send_media(callback_query.from_user.id)
                else:
                    await get_all_stories(callback_query.from_user.id)

            else:
                text = "Недостаточно средств\n"
                await bot.send_message(
                    user.user_id,
                    text=text+config["text"]["balance"].format(user.balance),
                    reply_markup=keyboards.add_balance()
                )
        elif callback_query.data == "all_stories":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            sub = await sub_db.get(callback_query.from_user.id)
            cheep = await tariff_db.get_cheep()
            if not sub:
                await bot.send_message(
                    callback_query.from_user.id,
                    text=config["text"]["info_message"].format(config["download_post_price"]),
                    reply_markup=keyboards.download_post(cheep.id)
                )
            else:
                await get_all_stories(callback_query.from_user.id)

        elif callback_query.data == "all_posts":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await get_posts(callback_query.from_user.id)

        elif callback_query.data == "subs":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            is_sub = await user_db.get(callback_query.from_user.id)
            save_pay = await save_pay_db.get(callback_query.from_user.id)
            cancel_button = True if save_pay else False
            auto_pay_status = save_pay.card if save_pay else "No cards"
            if is_sub.tariff:
                sub = await sub_db.get(callback_query.from_user.id)
                end_time = sub.end_time
                await bot.send_message(
                    callback_query.from_user.id,
                    text=config["text"]["sub_status"].format(
                        "ACTIVE 🟢",
                        end_time.strftime("%H:%M %d-%m-%Y")
                    ),
                    reply_markup=keyboards.cancel_sub(is_save_pay=cancel_button)
                )
            else:
                await bot.send_message(
                    callback_query.from_user.id,
                    text=config["text"]["sub_status"].format("INACTIVE 🔴", "..."),
                    reply_markup=keyboards.cancel_sub(is_save_pay=cancel_button)
                )

        elif callback_query.data == "cancel_auto_pay":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await save_pay_db.delete(callback_query.from_user.id)
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["auto_pay_canceled"],
                reply_markup=keyboards.back_home()
            )

        elif callback_query.data.startswith("check_payment"):
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            payment_id = callback_query.data.split("=")[-1]
            payment_status = check_payment(payment_id)
            payment_data = await payments_db.get(
                callback_query.from_user.id,
                payment_id
            )
            if payment_status.paid:
                saved = await save_pay_db.get(callback_query.from_user.id)
                if not saved:
                    auto_pay = save_payment_method(payment_id)
                    if auto_pay:
                        method_id, user_card = auto_pay
                        save_user_method = CreateSavePay(
                            user_id=callback_query.from_user.id,
                            email=payment_data.user_email,
                            card=user_card,
                            method_id=method_id
                        )
                        await save_pay_db.create(save_user_method)
                await payments_db.delete(
                    callback_query.from_user.id,
                    payment_id
                )
                if payment_data.payment_description.startswith("tariff_id"):
                    tariff_id = payment_data.payment_description.split("=")[-1]
                    tariff = await tariff_db.get(int(tariff_id))
                    sub = await sub_db.get(callback_query.from_user.id)
                    if not sub:
                        now = datetime.datetime.utcnow()
                        end = now + datetime.timedelta(days=tariff.tariff_days)
                        update_user = UpdateUser(
                            user_id=callback_query.from_user.id,
                            username=callback_query.from_user.username,
                            tariff=int(tariff_id)
                        )
                        new_sub = CreateSubscriber(
                            user_id=callback_query.from_user.id,
                            start_time=now,
                            end_time=end
                        )
                        await user_db.update(
                            callback_query.from_user.id,
                            update_user
                        )
                        await sub_db.create(
                            new_sub
                        )
                    else:
                        start_time = sub.start_time
                        end_time = sub.end_time + datetime.timedelta(days=tariff.tariff_days)
                        update_sub = UpdateSubscriber(
                            user_id=callback_query.from_user.id,
                            start_time=start_time,
                            end_time=end_time
                        )
                        await sub_db.update(callback_query.from_user.id, update_sub)

                elif payment_data.payment_description == "add_balance":
                    balance = payment_status.amount.value
                    user = await user_db.get(callback_query.from_user.id)
                    new_balance = user.balance + int(balance)
                    update_balance = UpdateBalance(
                        user_id=callback_query.from_user.id,
                        username=callback_query.from_user.username,
                        balance=new_balance
                    )
                    await user_db.update(callback_query.from_user.id, update_balance)
                await bot.send_message(
                    callback_query.from_user.id,
                    text=config["text"]["payment_ok"],
                    reply_markup=keyboards.back_home()
                )
            else:
                await bot.send_message(
                    callback_query.from_user.id,
                    text=config["text"]["payment_bad"],
                    reply_markup=keyboards.check_payment(payment_data)
                )

        elif callback_query.data in ["prev_post", "next_post", "prev_story", "next_story"]:
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            now_poss, end_poss = user_poss[callback_query.from_user.id]
            if callback_query.data.startswith("prev"):
                if now_poss > 1:
                    now_poss -= 1
            elif callback_query.data.startswith("next"):
                if now_poss < end_poss:
                    now_poss += 1
            user_poss[callback_query.from_user.id] = (now_poss, end_poss)
            if callback_query.data.endswith("post"):
                await get_posts(callback_query.from_user.id)
            elif callback_query.data.endswith("story"):
                await get_all_stories(callback_query.from_user.id)

        elif callback_query.data.startswith("create_payment_link"):
            operation = callback_query.data.split("=")[-1]
            user_payment[callback_query.from_user.id] = operation
            await CreatePayment.user_email.set()
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["enter_email"],
                reply_markup=keyboards.back_home()
            )

        elif callback_query.data.startswith("watch-updates="):
            sub = await sub_db.get(callback_query.from_user.id)
            cheep = await tariff_db.get_cheep()
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            if not sub:
                await bot.send_message(
                    callback_query.from_user.id,
                    text=config["text"]["subscriptions"].format(cheep.tariff_price, cheep.tariff_days),
                    reply_markup=keyboards.payments(cheep.id)
                )
            else:
                print("start")
                target_name = callback_query.data.split("=")[-1]
                already_sub = await watch_db.get_by_username(callback_query.from_user.id, target_name)
                if not already_sub:
                    target_id = download_service.user_exists(target_name)
                    last_watch = datetime.datetime.utcnow()
                    watch = CreateWatch(
                        user_id=callback_query.from_user.id,
                        target_username=target_name,
                        target_id=target_id,
                        last_watch=last_watch
                    )
                    print("hello")
                    await watch_db.create(watch)
                    await bot.send_message(
                        callback_query.from_user.id,
                        text=config["text"]["watch_ok"],
                        reply_markup=keyboards.back_home()
                    )
                else:
                    await bot.send_message(
                        callback_query.from_user.id,
                        text=config["text"]["already_sub"],
                        reply_markup=keyboards.back_home()
                    )
        elif callback_query.data == "my_subs":
            my_subs = await watch_db.get_users_subs(callback_query.from_user.id)
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["subs_list"],
                reply_markup=keyboards.list_subscriptions(my_subs)
            )

        elif callback_query.data.startswith("unwatch"):
            target_name = callback_query.data.split("=")[-1]
            await watch_db.delete(callback_query.from_user.id, target_name)
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["unsub_ok"].format(target_name),
                reply_markup=keyboards.back_home()
            )

        elif callback_query.data == "admin_home":
            await state.finish()
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await admin_home(callback_query.from_user.id)

        elif callback_query.data == "proxy":
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await UploadProxy.file.set()
            await bot.send_message(
                callback_query.from_user.id,
                text="Отправьте файл с данными",
                reply_markup=keyboards.back_admin()
            )

        elif callback_query.data == "adv_mailing":
            await Form.mailing.set()
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["enter_mailing"],
                reply_markup=keyboards.back_admin()
            )

        elif callback_query.data == "give_subscription":
            await Form.user_id.set()
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["enter_user_id"],
                reply_markup=keyboards.back_admin()
            )

        elif callback_query.data.startswith("admin_give_tariff="):
            tariff_id = int(callback_query.data.split("=")[-1])
            tariff = await tariff_db.get(tariff_id)
            async with state.proxy() as data:
                user_id = data["user_id"]
                username = data["username"]
            await state.finish()
            sub = await sub_db.get(user_id)
            if not sub:
                now = datetime.datetime.utcnow()
                end = now + datetime.timedelta(days=tariff.tariff_days)
                update_user = UpdateUser(
                    user_id=user_id,
                    username=username,
                    tariff=int(tariff_id)
                )
                new_sub = CreateSubscriber(
                    user_id=user_id,
                    start_time=now,
                    end_time=end
                )
                await user_db.update(
                    user_id,
                    update_user
                )
                await sub_db.create(
                    new_sub
                )
            else:
                start_time = sub.start_time
                end_time = sub.end_time + datetime.timedelta(days=tariff.tariff_days)
                update_sub = UpdateSubscriber(
                    user_id=user_id,
                    start_time=start_time,
                    end_time=end_time
                )
                await sub_db.update(user_id, update_sub)

            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["saved"]
            )

        elif callback_query.data == "discount_mailing":
            await Form.discount_mailing.set()
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await bot.send_message(
                callback_query.from_user.id,
                text=config["text"]["enter_mailing"],
                reply_markup=keyboards.back_admin()
            )

        elif callback_query.data.startswith("discount_id="):
            discount_id = int(callback_query.data.split("=")[-1])
            discount = await discount_db.get(discount_id)
            if discount.expire_date < datetime.datetime.utcnow():
                await discount_db.delete(discount_id)
            else:
                user_discount[callback_query.from_user.id] = discount_id
                base_tariff = await tariff_db.get_cheep()
                user = await user_db.get(callback_query.from_user.id)
                await home_page(user, base_tariff)

        elif callback_query.data == 'create_ref_link':
            await Form.channel_name.set()
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            await bot.send_message(
                callback_query.from_user.id,
                text=config['text']['insert_channel_name'],
                reply_markup=keyboards.back_admin()
            )

        elif callback_query.data == 'show_referals':
            await bot.delete_message(
                callback_query.from_user.id,
                callback_query.message.message_id
            )
            channels = await ref_db.get_all()
            ref = "КАНАЛЫ\n\n"
            ref += '=' * 100 + '\n\n'
            ref += 'channel\t\t\t\tactivates\n'
            for channel in channels:
                ref += f'{str(channel.channel_name)}\t\t\t{str(channel.count)}\n'
            ref = ref + '=' * 100 + '\n\n'
            file = str2file(ref, 'refs.txt')
            try:
                await bot.send_document(callback_query.from_user.id, file)
            except:
                await bot.send_message(callback_query.from_user.id, text=config["texts"]["no_users"])
    except Exception as a:
        log_file.write(str(a))


@dp.message_handler(content_types=types.ContentType.all(), state=CreatePayment.user_email)
async def get_user_email(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        user_email = message.text
        payment_request = user_payment[message.from_user.id]
        if payment_request.startswith("add_balance"):
            balance_value = payment_request.split("_")[-1]
            payment = create_balance_payment(balance_value, user_email, message.from_user.id)
        else:
            res_discount = await check_discount(message.from_user.id)
            if res_discount:
                discount = 1 - res_discount.discount_value / 100
            else:
                discount = 1
            tariff_id = int(payment_request.split("_")[-1])
            tariff = await tariff_db.get(tariff_id)
            if message.from_user.id in user_discount.keys():
                del user_discount[message.from_user.id]
            payment = create_subs_payment(tariff, user_email, message.from_user.id, discount_value=discount)
        payment_data = await payments_db.create(payment)
        await bot.send_message(
            message.from_user.id,
            text=config["text"]["payment_created"],
            reply_markup=keyboards.check_payment(payment_data)
        )
    except ValueError:
        await CreatePayment.user_email.set()
        await bot.send_message(
            message.from_user.id,
            text=config["text"]["enter_email"],
            reply_markup=keyboards.back_home()
        )


@dp.message_handler(content_types=types.ContentType.all(), state=UserLink.user_link)
async def get_user_link(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        user_content = user_data[message.from_user.id]
        user_content["link"] = message.text
        await bot.send_message(
            message.from_user.id,
            text=config["text"]["start_search"]
        )
        sub = await sub_db.get(message.from_user.id)
        cheep = await tariff_db.get_cheep()

        if user_content["content_type"] == "watch-stories":
            await send_media(message.from_user.id)

        elif user_content["content_type"] == "download-post":
            if not sub:
                await bot.send_message(
                    message.from_user.id,
                    text=config["text"]["info_message"].format(config["download_post_price"]),
                    reply_markup=keyboards.download_post(cheep.id)
                )
            else:
                await send_media(message.from_user.id)

        elif user_content["content_type"] == "highlights":
            if not sub:
                await bot.send_message(
                    message.from_user.id,
                    text=config["text"]["info_message_2"],
                    reply_markup=keyboards.get_content(cheep)
                )
            else:
                await send_media(message.from_user.id)
    except Exception as a:
        log_file.write(str(a))


@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=UploadProxy.file)
async def change_proxy_from_file(message: types.Message, state: FSMContext):
    await state.finish()
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    file = file_info.file_path
    file_name = message.document.file_name
    urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{config["bot_token"]}/{file}', file_name)
    with open(file_name, "r") as file:
        new_proxy = [line for line in file]
    for item in new_proxy:
        inst_username, inst_password, ip, port, username, password = item.strip().split(":")
        value = (inst_username, inst_password, f"https://{username}:{password}@{ip}:{port}")
        if value not in config["instagram_accounts"]:
            config["instagram_accounts"].append(value)
        else:
            continue
    save_config(config_filename, config)
    await bot.send_message(
        message.from_user.id,
        text=config["text"]["saved"]
    )


@dp.message_handler(content_types=types.ContentType.all(), state=Form.user_id)
async def get_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_in_db = await user_db.get(user_id)
        async with state.proxy() as data:
            data["user_id"] = user_id
            data["username"] = user_in_db.username
        if user_in_db:
            tariffs = await tariff_db.get_all()
            await bot.send_message(
                message.from_user.id,
                text=config["text"]["choose_days"],
                reply_markup=keyboards.admin_give_subscription(tariffs)
            )
        else:
            await state.finish()
            await Form.user_id.set()
            await bot.send_message(
                message.from_user.id,
                text=config["text"]["incorrect_user_id"],
                reply_markup=keyboards.back_admin()
            )
    except ValueError:
        await state.finish()
        await Form.user_id.set()
        await bot.send_message(
            message.from_user.id,
            text=config["text"]["incorrect_user_id"],
            reply_markup=keyboards.back_admin()
        )


@dp.message_handler(content_types=types.ContentType.all(), state=Form.mailing)
async def owners_process_mailing_handler(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data["message"] = message.to_python()
        await Form.mailing_markup.set()
        await message.answer(
            config["text"]["enter_mailing_markup"],
            reply_markup=keyboards.back_admin()
        )
    except Exception as a:
        print(a)


@dp.message_handler(content_types=types.ContentType.all(), state=Form.discount_mailing)
async def owners_process_mailing_handler(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data["discount_message"] = message.to_python()
        await Form.discount_value.set()
        await message.answer(
            config["text"]["enter_discount_percent"],
            reply_markup=keyboards.back_admin()
        )
    except Exception as a:
        print(a)


@dp.message_handler(content_types=types.ContentType.all(), state=Form.discount_value)
async def owners_process_mailing_handler(message: types.Message, state: FSMContext):
    try:
        try:
            discount_value = int(message.text)
            unique_id = random.randint(10000000, 99999999)
            expire_date = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            discount = CreateDiscount(
                discount_value=discount_value,
                discount_id=unique_id,
                expire_date=expire_date
            )
            await discount_db.create(discount)

            async with state.proxy() as data:
                _message = data["discount_message"]
            await state.finish()

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    text=f"Безлимит подписка за {100 - discount_value}%",
                    callback_data=f"discount_id={unique_id}"
                )
            )

            await message.answer(config["text"]["start_mailing"])
            started = time.time()
            kwargs = {
                "from_chat_id": _message["chat"]["id"],
                "message_id": _message["message_id"],
                "reply_markup": markup
            }
            user_list = [user.user_id for user in await user_db.get_users()]

            total, sent, unsent = await sub_proc(user_list, kwargs)

            await message.answer(
                config["text"]["mailing_stats"].format(
                    total=total,
                    sent=sent,
                    unsent=unsent,
                    time=round(time.time() - started, 3)
                )
            )
        except ValueError:
            await Form.discount_value.set()
            await bot.send_message(
                message.from_user.id,
                text=config["text"]["incorrect_value"],
                reply_markup=keyboards.back_admin()
            )
    except Exception as a:
        print(a)


@dp.message_handler(state=Form.mailing_markup)
async def owners_process_mailing_markup_handler(message: types.Message, state: FSMContext) -> None:

    try:
        if message.text not in ["-", "."]:
            try:
                markup = keyboards.from_str(message.text)
            except:
                await message.answer(
                    text=config["text"]["incorrect_mailing_markup"],
                    reply_markup=keyboards.back_admin()
                )
                return
        else:
            markup = types.InlineKeyboardMarkup()
        markup = markup.to_python()
        async with state.proxy() as data:
            _message = data["message"]

        await state.finish()
        await message.answer(config["text"]["start_mailing"])
        started = time.time()
        kwargs = {
            "from_chat_id": _message["chat"]["id"],
            "message_id": _message["message_id"],
            "reply_markup": markup
        }
        user_list = [user.user_id for user in await user_db.get_users()]

        total, sent, unsent = await sub_proc(user_list, kwargs)

        await message.answer(
            config["text"]["mailing_stats"].format(
                total=total,
                sent=sent,
                unsent=unsent,
                time=round(time.time() - started, 3)
            )
        )
    except Exception as a:
        print(a)


@dp.message_handler(content_types=types.ContentType.all(), state=Form.channel_name)
async def owners_process_channel_name(message: types.Message, state: FSMContext):
    try:
        channel_name = message.text
        chars = string.ascii_letters + string.digits
        password = '__'
        for i in range(10):
            password += random.choice(chars)
        link = f'https://t.me/{config["bot_user_name"]}?start={password}'
        await ref_db.create(channel_name, link)
        await bot.send_message(
            message.from_user.id,
            text=config['text']['link_generated'].format(config['bot_user_name'], password),
            reply_markup=keyboards.back_admin()
        )
        await state.finish()
    except Exception as a:
        print(a)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(timeout_checker())
    loop.create_task(send_updates())
    executor.start_polling(dispatcher=dp, skip_updates=False)

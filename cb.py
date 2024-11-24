import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from cryptopay import CryptoPay
from cryptopay.exceptions import APIError

bot = Bot(token="TOKEN")
dp = Dispatcher()


class States(StatesGroup):
    """Состояния бота пон."""

    token = State()
    amount = State()


@dp.message(CommandStart())
async def start_command(message: Message) -> None:
    """Ну тут мы короче втираем челику функцию нашего ботика."""
    await message.answer(
        "Даров, чувак, хочешь короче я тебе "
        "выставлю счёт на пополнение твоей"
        "приложухи в @CryptoBot ?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Ну го")]],
            resize_keyboard=True,
        ),
    )


@dp.message(States.token)
async def token_handler(message: Message, state: FSMContext) -> None:
    """Короче мы типа развели чела на токен КБ."""
    cp = CryptoPay(token=message.text)
    try:
        await cp.get_me()
    except APIError:
        await message.answer(
            "Ты мне какое-то говно скинул, кинь норм токен",
        )
        return
    await message.answer(
        "Кайф, токен работает, сколько тебе там юсдтшек надо пополнить?"
    )
    await state.update_data(cp=cp)
    await state.set_state(States.amount)


@dp.message(F.text.regexp(r"^\d+$|^\d+\.\d+$"), States.amount)
async def amount_handler(message: Message, state: FSMContext) -> None:
    """Челик сказал скок ему надо пополнить и мы выставляем счёт."""
    data = await state.get_data()
    cp: CryptoPay = data["cp"]
    amount = float(message.text)
    invoice = await cp.create_invoice(asset="USDT", amount=amount)
    await message.answer(
        "Счёт на пополнение твоей приложухи выставлен, оплачивай",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Оплатить",
                        url=invoice.mini_app_invoice_url,
                    ),
                ]
            ],
        ),
    )
    await state.clear()


@dp.message(F.text == "Ну го")
async def go_handler(message: Message, state: FSMContext) -> None:
    """Челик согласился и мы просим у него токен пон."""
    await message.answer(
        "Кайф чел, ток мне нужен твой токен, можешь кинуть по фасту?",
    )
    await state.set_state(States.token)


@dp.message(States.token)
async def token_handler(message: Message, state: FSMContext) -> None:
    """Короче мы типа развели чела на токен КБ."""
    cp = CryptoPay(token=message.text)
    try:
        await cp.get_me()
    except APIError:
        await message.answer(
            "Ты мне какое-то говно скинул, кинь норм токен",
        )
        return
    await message.answer(
        "Кайф, токен работает, сколько тебе там юсдтшек надо пополнить?"
    )
    await state.update_data(cp=cp)
    await state.set_state(States.amount)


@dp.message(F.text.regexp(r"^\d+$|^\d+\.\d+$"), States.amount)
async def amount_handler(message: Message, state: FSMContext) -> None:
    """Челик сказал скок ему надо пополнить и мы выставляем счёт."""
    data = await state.get_data()
    cp: CryptoPay = data["cp"]
    amount = float(message.text)
    invoice = await cp.create_invoice(asset="USDT", amount=amount)
    await message.answer(
        "Счёт на пополнение твоей приложухи выставлен, оплачивай",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Оплатить",
                        url=invoice.mini_app_invoice_url,
                    ),
                ]
            ],
        ),
    )
    await state.clear()


async def main() -> None:
    """Погнали ёпта."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


async def create_check(amount: float, asset: str, user_id=None, username=None):
    try:
        check = CryptoPay.create_check(amount, asset, pin_to_user_id=user_id, pin_to_username=username)
        return check
    except APIError as e:
        return f"Error creating check: {e}"


async def transfer_funds(user_id: int, asset: str, amount: float, comment=None, disable_notification=False):
    try:
        transfer = CryptoPay.transfer(
            user_id=user_id,
            asset=asset,
            amount=amount,
            comment=comment,
            disable_send_notification=disable_notification,
        )
        return transfer
    except APIError as e:
        return f"Error during transfer: {e}"


async def get_all_checks(asset=None, status=None, offset=0, count=100):
    try:
        checks = CryptoPay.get_checks(asset=asset, status=status, offset=offset, count=count)
        return checks
    except APIError as e:
        return f"Error retrieving checks: {e}"


async def get_all_transfers(asset=None, offset=0, count=100):
    try:
        transfers = CryptoPay.get_transfers(asset=asset, offset=offset, count=count)
        return transfers
    except APIError as e:
        return f"Error retrieving transfers: {e}"


async def get_balance():
    try:
        balance = CryptoPay.get_balance()
        return balance
    except APIError as e:
        return f"Error retrieving balance: {e}"


@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать чек", callback_data="create_check")],
        [InlineKeyboardButton(text="Трансфер", callback_data="transfer_funds")],
        [InlineKeyboardButton(text="Получить все чеки", callback_data="get_all_checks")],
        [InlineKeyboardButton(text="Получить все трансферы", callback_data="get_all_transfers")],
        [InlineKeyboardButton(text="Получить баланс", callback_data="get_balance")],
    ])
    await message.answer("Привет! Что ты хочешь сделать?", reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data == "create_check")
async def handle_create_check(callback_query):
    await callback_query.message.answer("Введите сумму и валюту через пробел (например: 10 BTC):")
    await States.waiting_for_check_details.set()


@dp.message(States.waiting_for_check_details)
async def process_check_details(message: Message, state: FSMContext):
    details = message.text.split()
    if len(details) == 2:
        try:
            amount = float(details[0])
            asset = details[1]
            check = await create_check(amount, asset)
            if isinstance(check, str):
                await message.answer(check)
            else:
                await message.answer(f"Чек создан! Вот ссылка: {check.link}")
            await state.clear()
        except ValueError:
            await message.answer("Ошибка: Неверный формат суммы.")
    else:
        await message.answer("Ошибка: Неверный ввод. Попробуйте снова.")


# Similar handlers for transfer, get_all_checks, get_all_transfers, and get_balance would be implemented.

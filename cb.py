from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from cryptopay import CryptoPay, APIError

TOKEN = "5869182045:AAErBtQQZ-r2au6czX45iJFJKboBjYlPG9A"  # Замените на токен вашего бота
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class States(StatesGroup):
    waiting_for_token = State()
    waiting_for_check_amount = State()
    waiting_for_transfer_details = State()

crypto_pay = None  # Для хранения CryptoPay объекта


@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    """Начальный экран с выбором действия."""
    await message.answer("Привет! Что ты хочешь сделать?", reply_markup=main_keyboard())


def main_keyboard():
    """Инлайн-кнопки для выбора действия."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать чек", callback_data="create_check")],
        [InlineKeyboardButton(text="Трансфер", callback_data="transfer_funds")],
        [InlineKeyboardButton(text="Получить баланс", callback_data="get_balance")],
    ])


@dp.callback_query_handler(lambda call: call.data in ["create_check", "transfer_funds", "get_balance"])
async def handle_action_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора действия."""
    action = callback_query.data
    await state.update_data(action=action)
    await callback_query.message.answer("Кайф чел, ток мне нужен твой токен, можешь кинуть по фасту?")
    await States.waiting_for_token.set()


@dp.message(States.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    """Обработка токена."""
    global crypto_pay
    token = message.text.strip()
    if len(token) >= 20:  # Простая проверка токена
        try:
            crypto_pay = CryptoPay(token=token)
            await message.answer("Кайф, токен работает!")
            user_data = await state.get_data()
            action = user_data.get("action")

            if action == "create_check":
                await message.answer("Сколько тебе там USDT-шек надо?")
                await States.waiting_for_check_amount.set()
            elif action == "transfer_funds":
                await message.answer("Введи ID пользователя, сумму и валюту через пробел (например: 123456789 10 USDT):")
                await States.waiting_for_transfer_details.set()
            elif action == "get_balance":
                balance = await get_balance()
                if isinstance(balance, str):
                    await message.answer(balance)
                else:
                    balance_details = "\n".join([f"{b.currency}: {b.amount}" for b in balance])
                    await message.answer(f"Ваш баланс:\n{balance_details}")
                await state.clear()
        except APIError as e:
            await message.answer(f"Ошибка с токеном: {e}. Попробуй снова.")
    else:
        await message.answer("Это точно токен? Похоже, что-то не так. Попробуй снова.")


@dp.message(States.waiting_for_check_amount)
async def process_check_amount(message: types.Message, state: FSMContext):
    """Обработка суммы для создания чека."""
    try:
        amount = float(message.text)
        check = await create_check(amount, "USDT")
        if isinstance(check, str):
            await message.answer(check)
        else:
            await message.answer(f"Счёт на пополнение выставлен! Вот ссылка: {check.link}")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка: Неверный формат суммы. Введите сумму числом.")


@dp.message(States.waiting_for_transfer_details)
async def process_transfer_details(message: types.Message, state: FSMContext):
    """Обработка данных для трансфера."""
    details = message.text.split()
    if len(details) == 3:
        try:
            user_id = int(details[0])
            amount = float(details[1])
            asset = details[2]
            transfer = await transfer_funds(user_id, asset, amount)
            if isinstance(transfer, str):
                await message.answer(transfer)
            else:
                await message.answer(f"Трансфер выполнен: {transfer.amount} {transfer.currency} отправлено.")
            await state.clear()
        except ValueError:
            await message.answer("Ошибка: Неверный формат данных. Попробуй снова.")
    else:
        await message.answer("Ошибка: Введи ID, сумму и валюту через пробел.")


async def create_check(amount, asset):
    """Создание чека."""
    try:
        check = crypto_pay.create_check(amount=amount, asset=asset)
        return check
    except APIError as e:
        return f"Ошибка при создании чека: {e}"


async def transfer_funds(user_id, asset, amount):
    """Трансфер средств."""
    try:
        transfer = crypto_pay.transfer(user_id=user_id, asset=asset, amount=amount)
        return transfer
    except APIError as e:
        return f"Ошибка при трансфере: {e}"


async def get_balance():
    """Получение баланса."""
    try:
        balances = crypto_pay.get_balance()
        return balances
    except APIError as e:
        return f"Ошибка при получении баланса: {e}"


if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

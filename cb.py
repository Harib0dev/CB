from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from cryptopay import CryptoPay
from cryptopay.exceptions import APIException  # Исправленный импорт

# Создание объекта CryptoPay (пример токена и TESTNET)
cp = CryptoPay("282701:AAcVcUZD3A2dRin4UaxYy0NI0cv3QEbT32Y")

# Инициализация бота
BOT_TOKEN = "5869182045:AAErBtQQZ-r2au6czX45iJFJKboBjYlPG9A"  # Заменить на токен Telegram-бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для FSM
class States(StatesGroup):
    waiting_for_token = State()
    waiting_for_check_amount = State()
    waiting_for_transfer_details = State()


@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    """Приветствие и выбор действия."""
    await message.answer("Привет! Что ты хочешь сделать?", reply_markup=main_keyboard())


def main_keyboard():
    """Инлайн-клавиатура для выбора действия."""
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
    """Обработка токена и выполнение действия."""
    token = message.text.strip()
    try:
        # Здесь можешь проверить токен на валидность, если нужно
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
            await message.answer(balance)
            await state.clear()
    except APIException as e:
        await message.answer(f"Ошибка с токеном: {e}. Попробуй снова.")


@dp.message(States.waiting_for_check_amount)
async def process_check_amount(message: types.Message, state: FSMContext):
    """Создание чека."""
    try:
        amount = float(message.text)
        check = cp.create_check(amount=amount, asset="USDT")
        await message.answer(f"Счёт на пополнение выставлен! Вот ссылка: {check.link}")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка: Неверный формат суммы. Введите сумму числом.")
    except APIException as e:
        await message.answer(f"Ошибка при создании чека: {e}")


@dp.message(States.waiting_for_transfer_details)
async def process_transfer_details(message: types.Message, state: FSMContext):
    """Обработка данных для трансфера."""
    details = message.text.split()
    if len(details) == 3:
        try:
            user_id = int(details[0])
            amount = float(details[1])
            asset = details[2]
            transfer = cp.transfer(user_id=user_id, asset=asset, amount=amount)
            await message.answer(f"Трансфер выполнен: {transfer.amount} {transfer.currency} отправлено.")
            await state.clear()
        except ValueError:
            await message.answer("Ошибка: Неверный формат данных. Попробуй снова.")
        except APIException as e:
            await message.answer(f"Ошибка при трансфере: {e}")
    else:
        await message.answer("Ошибка: Введи ID, сумму и валюту через пробел.")


async def get_balance():
    """Получение баланса."""
    try:
        balances = cp.get_balance()
        balance_details = "\n".join([f"{b.currency}: {b.amount}" for b in balances])
        return f"Ваш баланс:\n{balance_details}"
    except APIException as e:
        return f"Ошибка при получении баланса: {e}"


if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

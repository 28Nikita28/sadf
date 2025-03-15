import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, MenuButtonWebApp, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

from generator import generate

# Инициализация окружения
load_dotenv()

# Создаем экземпляр диспетчера
dp = Dispatcher()

# Определяем состояния FSM
class Reg(StatesGroup):
    wait = State()

# ========================
# 🏗️ ИНИЦИАЛИЗАЦИЯ БОТА
# ========================
async def startup():
    """Настройка веб-приложения в меню бота"""
    bot = Bot(os.getenv("TG_TOKEN"))
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🌐 App",
            web_app=WebAppInfo(url="https://w5model.netlify.app/")
        )
    )
    await bot.session.close()

# ========================
# 🎯 ОБРАБОТЧИКИ СООБЩЕНИЙ
# ========================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer('Добро пожаловать! Нажмите иконку "🌐 App" справа внизу.')

@dp.message(Reg.wait)
async def waiting(message: Message):
    """Промежуточный обработчик состояния ожидания"""
    await message.answer('Секундочку!')

@dp.message()
async def gpt_work(message: Message, state: FSMContext):
    """Основной обработчик сообщений"""
    await state.set_state(Reg.wait)
    result = await generate(message.text)
    await message.answer(result)
    await state.clear()

# ========================
# 🚀 ЗАПУСК ПРИЛОЖЕНИЯ
# ========================
async def main():
    """Основная функция запуска бота"""
    await startup()  # Инициализация меню
    bot = Bot(os.getenv("TG_TOKEN"))
    # Get the port from the environment variables, default to 10000
    port = int(os.environ.get("PORT", 10000))
    await dp.start_polling(bot, listen_address="0.0.0.0", port=port)

if __name__ == '__main__':
    asyncio.run(main())
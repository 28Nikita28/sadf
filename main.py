import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, MenuButtonWebApp, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from aiohttp import web

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
async def startup(bot: Bot):
    """Настройка веб-приложения в меню бота"""
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🌐 App",
            web_app=WebAppInfo(url="https://w5model.netlify.app/")
        )
    )

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
# 🌐 WEB SERVER SETUP
# ========================
async def web_server():
    """Запуск простого веб-сервера для Render"""
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    print(f"Web server started on port {port}")

# ========================
# 🚀 ЗАПУСК ПРИЛОЖЕНИЯ
# ========================
async def main():
    """Основная функция запуска бота"""
    bot = Bot(os.getenv("TG_TOKEN"))
    await startup(bot)
    
    # Запускаем бота и веб-сервер параллельно
    await asyncio.gather(
        dp.start_polling(bot),
        web_server()
    )

if __name__ == '__main__':
    asyncio.run(main())

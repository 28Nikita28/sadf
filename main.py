import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

from generator import generate

load_dotenv()

# Конфигурация
TOKEN = os.getenv("TG_TOKEN")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = "/webhook"
BASE_WEBHOOK_URL = os.getenv("https://sadf-pufq.onrender.com")

# Инициализация
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(TOKEN)

# Обработчики
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('Добро пожаловать! Нажмите иконку "🌐 App" справа внизу.')

@dp.message()
async def handle_message(message: types.Message):
    result = await generate(message.text)
    await message.answer(result)

# Настройка вебхука
async def on_startup(app: web.Application):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
    await bot.set_chat_menu_button(
        menu_button=types.MenuButtonWebApp(
            text="🌐 App",
            web_app=types.WebAppInfo(url="https://w5model.netlify.app/")
        )
    )

# Запуск приложения
def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    
    web.run_app(
        app,
        host=WEB_SERVER_HOST,
        port=WEB_SERVER_PORT
    )

if __name__ == '__main__':
    main()
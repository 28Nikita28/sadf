import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
import logging
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from generator import generate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("TG_TOKEN")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = "/webhook"
BASE_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://sadf-pufq.onrender.com")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "https://hdghs.onrender.com/chat")

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(TOKEN)

class UserState(StatesGroup):
    selected_model = State()

MODELS = {
    "deepseek": "DeepSeek Chat",
    "deepseek-r1": "DeepSeek R1",
    "gemini": "Gemini Pro",
    "llama-4-maverick": "Llama 4 Maverick",
    "qwen": "Qwen 32B"
}

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    try:
        await message.answer('Добро пожаловать! Нажмите иконку "🌐 App" справа внизу или используйте команду /model для выбора модели ИИ.')
    except Exception as e:
        logger.error(f"Error in cmd_start: {str(e)}")

@dp.message(Command("model"))
async def select_model(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=name, callback_data=key)]
        for key, name in MODELS.items()
    ])
    await message.answer("Выберите модель ИИ:", reply_markup=keyboard)

@dp.callback_query()
async def model_selected(callback: types.CallbackQuery, state: FSMContext):
    model_key = callback.data
    if model_key not in MODELS:
        await callback.answer("Неизвестная модель")
        return
    
    await state.update_data(selected_model=model_key)
    await callback.message.edit_text(f"Выбрана модель: {MODELS[model_key]}")
    await callback.answer()

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        selected_model = user_data.get('selected_model', 'deepseek')
        
        logger.info(f"Received message with model [{selected_model}]: {message.text}")
        result = await generate(message.text, AI_SERVICE_URL, selected_model)
        await message.answer(result)
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await message.answer("Произошла ошибка при обработке запроса")

async def on_startup(app: web.Application):
    try:
        await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
        await bot.set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(
                text="🌐 App",
                web_app=types.WebAppInfo(url="https://w5model.netlify.app/")
            )
        )
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

def main():
    try:
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
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == '__main__':
    main()
# main.py
import asyncio
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
from aiogram.utils.markdown import hcode, hbold
from aiogram.client.default import DefaultBotProperties

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
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

class UserState(StatesGroup):
    selected_model = State()

MODELS = {
    "deepseek": "🧠 DeepSeek 0324",
    "deepseek-r1": "🚀 DeepSeek R1",
    "deepseek-v3": "💎 DeepSeek v3",
    "gemini": "🔮 Gemini Pro",
    "gemma": "💎 Gemma 27B",
    "qwen": "🎲 Qwen 32B",
    "qwen 2.5": "🎲 Qwen 2.5",
    "llama-4-maverick": "🦙 Llama Maverick",
    "llama-4-scout": "🦙 Llama Scout"
}

def get_model_keyboard(selected: str = None) -> types.InlineKeyboardMarkup:
    buttons = []
    for key, name in MODELS.items():
        status_icon = "🔵" if key == selected else "⚪"
        buttons.append([
            types.InlineKeyboardButton(
                text=f"{status_icon} {name}", 
                callback_data=key
            )
        ])
    buttons.append([
        types.InlineKeyboardButton(
            text="🌍 Web App", 
            web_app=types.WebAppInfo(url="https://w5model.netlify.app/")
        )
    ])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    try:
        await state.set_data({"selected_model": "deepseek"})
        await message.answer(
            f"{hbold('🤖 AI Assistant Bot')}\n\n"
            "Выберите модель ИИ или используйте веб-приложение:\n"
            "По умолчанию: 🧠 DeepSeek Chat",
            reply_markup=get_model_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")

@dp.message(Command("model"))
async def select_model(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer(
        "🔧 Выберите модель ИИ:",
        reply_markup=get_model_keyboard(user_data.get('selected_model'))
    )

@dp.callback_query()
async def model_selected(callback: types.CallbackQuery, state: FSMContext):
    model_key = callback.data
    if model_key not in MODELS:
        await callback.answer("❌ Неизвестная модель", show_alert=True)
        return
    
    try:
        await state.update_data(selected_model=model_key)
        await callback.message.edit_reply_markup(
            reply_markup=get_model_keyboard(model_key)
        )
        await callback.answer(f"✅ Выбрано: {MODELS[model_key]}", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка выбора модели: {e}")
        await callback.answer("⚠️ Ошибка выбора модели", show_alert=True)

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
        user_data = await state.get_data()
        model = user_data.get('selected_model', 'deepseek')
        
        logger.info(f"Обработка сообщения с моделью [{model}]: {message.text}")
        
        processing_msg = await message.answer("⏳ Запрос принят...")
        
        response = await generate(message.text, AI_SERVICE_URL, model)
        
        await processing_msg.delete()
        
        if not response:
            raise ValueError("Пустой ответ от модели")
            
        formatted = response.replace("```", "'''")
        response_text = f"📝 {MODELS[model]}:\n{hcode(formatted)}"
        
        await message.answer(response_text)
        
    except asyncio.TimeoutError:
        await message.answer("⌛ Превышено время ожидания ответа")
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        await message.answer("⚠️ Ошибка при обработке запроса. Попробуйте снова.")

async def on_startup(app: web.Application):
    try:
        await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
        logger.info("Бот успешно запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
        raise

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == '__main__':
    main()
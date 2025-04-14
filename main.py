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

# Проверка обязательных переменных
TOKEN = os.getenv("TG_TOKEN")
BASE_WEBHOOK_URL = os.getenv("WEBHOOK_URL")
AI_SERVICE_URL = f"http://localhost:{os.environ.get('PORT', 10000)}/chat"  # Локальный адрес FastAPI

if not TOKEN:
    logger.critical("❌ Отсутствует TG_TOKEN")
    exit(1)
if not BASE_WEBHOOK_URL:
    logger.critical("❌ Отсутствует WEBHOOK_URL")
    exit(1)

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = "/webhook"

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
        status_icon = "🟢" if key == selected else "⚪"
        buttons.append([
            types.InlineKeyboardButton(
                text=f"{status_icon} {name}", 
                callback_data=f"model_{key}"
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

@dp.callback_query(lambda c: c.data.startswith('model_'))
async def model_selected(callback: types.CallbackQuery, state: FSMContext):
    model_key = callback.data.replace('model_', '')
    if model_key not in MODELS:
        await callback.answer("❌ Неизвестная модель", show_alert=True)
        return
    
    try:
        await state.update_data(selected_model=model_key)
        await callback.message.edit_text(
            text=f"🎛️ <b>Текущая модель:</b>\n{MODELS[model_key]}",
            reply_markup=get_model_keyboard(model_key)
        )
        await callback.answer(f"✅ Выбрано: {MODELS[model_key]}", show_alert=False)
        logger.info(f"User {callback.from_user.id} selected: {model_key}")
    except Exception as e:
        logger.error(f"Model select error: {str(e)}")
        await callback.answer("⚠️ Ошибка выбора модели", show_alert=True)

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
        user_data = await state.get_data()
        model = user_data.get('selected_model', 'deepseek')
        
        logger.info(f"Model: {model} | Query: {message.text}")
        
        processing_msg = await message.answer("⏳ Обработка запроса...")
        
        response = await generate(message.text, AI_SERVICE_URL, model)
        
        await processing_msg.delete()
        
        if not response:
            raise ValueError("Пустой ответ от модели")
            
        formatted = response.replace("```", "'''")
        response_text = f"📝 {MODELS[model]}:\n{hcode(formatted)}"
        
        await message.answer(response_text)
        
    except asyncio.TimeoutError:
        await message.answer("⌛ Превышено время ожидания")
    except Exception as e:
        logger.error(f"Ошибка: {str(e)[:200]}")
        await message.answer("⚠️ Ошибка обработки запроса")

@dp.get("/")
async def health_check(request: web.Request):
    return web.Response(text="Bot is running", status=200)

async def on_startup(app: web.Application):
    try:
        # Проверяем корректность URL вебхука
        webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
        if not webhook_url.startswith("https://"):
            logger.error("❌ WEBHOOK_URL должен использовать HTTPS")
            exit(1)
            
        logger.info(f"🔄 Устанавливаю вебхук: {webhook_url}")
        await bot.set_webhook(webhook_url)
        logger.info("🤖 Бот запущен. Доступные модели: " + ", ".join(MODELS.keys()))
        
    except Exception as e:
        logger.critical(f"🚨 Ошибка вебхука: {str(e)}")
        exit(1)

def main():
    app = web.Application()
    app.add_routes([web.get("/", health_check)])
    app.on_startup.append(on_startup)
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    try:
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    except Exception as e:
        logger.critical(f"🚨 Серверная ошибка: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main()
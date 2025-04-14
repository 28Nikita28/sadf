# main.py
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

# Инициализация FastAPI приложения
from app import app as fastapi_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Проверка переменных окружения
TOKEN = os.getenv("TG_TOKEN")
BASE_WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    logger.critical("❌ Отсутствует TG_TOKEN")
    exit(1)
if not BASE_WEBHOOK_URL:
    logger.critical("❌ Отсутствует WEBHOOK_URL")
    exit(1)

# Конфигурация сервера
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = "/webhook"
AI_SERVICE_URL = f"{BASE_WEBHOOK_URL}/chat"

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
    await state.set_data({"selected_model": "deepseek"})
    await message.answer(
        f"{hbold('🤖 AI Assistant Bot')}\n\n"
        "Выберите модель ИИ или используйте веб-приложение:\n"
        "По умолчанию: 🧠 DeepSeek Chat",
        reply_markup=get_model_keyboard()
    )

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
    
    await state.update_data(selected_model=model_key)
    await callback.message.edit_text(
        text=f"🎛️ <b>Текущая модель:</b>\n{MODELS[model_key]}",
        reply_markup=get_model_keyboard(model_key)
    )
    await callback.answer(f"✅ Выбрано: {MODELS[model_key]}", show_alert=False)

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
        user_data = await state.get_data()
        model = user_data.get('selected_model', 'deepseek')
        
        processing_msg = await message.answer("⏳ Обработка запроса...")
        response = await generate(message.text, AI_SERVICE_URL, model)
        await processing_msg.delete()
        
        formatted = response.replace("```", "'''")
        await message.answer(f"📝 {MODELS[model]}:\n{hcode(formatted)}")
        
    except Exception as e:
        logger.error(f"Ошибка: {str(e)[:200]}")
        await message.answer("⚠️ Ошибка обработки запроса")

async def on_startup(app: web.Application):
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    logger.info(f"Вебхук установлен: {webhook_url}")

def main():
    # Создаем aiohttp приложение
    aioapp = web.Application()
    
    # Регистрируем обработчики бота
    SimpleRequestHandler(dp, bot).register(aioapp, path=WEBHOOK_PATH)
    
    # Монтируем FastAPI приложение
    aioapp.add_subapp("/api", fastapi_app)
    
    # Настройка вебхука
    setup_application(aioapp, dp, bot=bot)
    
    # Запуск сервера
    web.run_app(aioapp, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == '__main__':
    main()
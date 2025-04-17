from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import logging
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.markdown import hcode, hbold
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from generator import generate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Проверка обязательных переменных
TOKEN = os.getenv("TG_TOKEN")
if not TOKEN:
    logger.critical("❌ Отсутствует TG_TOKEN")
    exit(1)

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
            "По умолчанию: � DeepSeek Chat",
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
    try:
        model_key = callback.data.split('_')[1]
        if model_key not in MODELS:
            await callback.answer("❌ Неизвестная модель")
            return

        await state.update_data(selected_model=model_key)
        await callback.message.edit_reply_markup(
            reply_markup=get_model_keyboard(model_key)
        )
        await callback.answer(f"✅ {MODELS[model_key]}")
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        await callback.answer("⚠️ Ошибка обновления")

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
        user_data = await state.get_data()
        model = user_data.get('selected_model', 'deepseek')
        
        logger.info(f"Model: {model} | Query: {message.text}")
        
        processing_msg = await message.answer("⏳ Обработка запроса...")
        
        # Для примера используем локальный URL
        response = await generate(message.text, "https://hdghs.onrender.com", model)
        
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

async def main():
    logger.info("🤖 Бот запущен в режиме поллинга")
    logger.info("Доступные модели: " + ", ".join(MODELS.keys()))
    await dp.start_polling(bot)

async def on_startup(dp: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)

async def start_bot(app):
    await dp.start_polling(bot)

async def dummy_handler(request):
    return web.Response(text="OK")

async def main():
    # Инициализация веб-сервера для Render
    app = web.Application()
    app.router.add_get("/", dummy_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Порт для Render
    PORT = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Запуск бота с обработкой shutdown
    try:
        logger.info("🤖 Бот запущен в режиме поллинга")
        await dp.start_polling(bot, handle_as_tasks=True)
    finally:
        await runner.cleanup()  # Корректное завершение

if __name__ == '__main__':
    asyncio.run(main())
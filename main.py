# main.py

import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from pymongo import MongoClient
import os

from texts import get_text, TEXTS
from buttons import format_buttons
from utils import detect_platform, download_media

# Bot Token and Mongo
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot, storage=MemoryStorage())

# Mongo setup
client = MongoClient(MONGO_URI)
db = client["tg_downloader"]
users_col = db["users"]

# FSM
class DownloadState(StatesGroup):
    waiting_for_link = State()
    waiting_for_format = State()

# Start
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    users_col.update_one({"_id": user_id}, {"$setOnInsert": {"lang": "en"}}, upsert=True)
    await state.finish()

    with open("assets/welcome.jpg", "rb") as photo:
        await bot.send_photo(message.chat.id, photo, caption=get_text("en", "start"))
    
    lang_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code in TEXTS:
        lang_keyboard.add(types.KeyboardButton(code.upper()))
    
    await message.answer(get_text("en", "choose_language"), reply_markup=lang_keyboard)
    await DownloadState.waiting_for_link.set()

# Language selection
@dp.message_handler(lambda m: m.text.lower() in TEXTS.keys(), state=DownloadState.waiting_for_link)
async def set_lang(message: types.Message, state: FSMContext):
    lang = message.text.lower()
    user_id = message.from_user.id
    users_col.update_one({"_id": user_id}, {"$set": {"lang": lang}})
    await message.reply(get_text(lang, "language_selected"), reply_markup=types.ReplyKeyboardRemove())
    await message.answer(get_text(lang, "guide"))

# Handle link input
@dp.message_handler(state=DownloadState.waiting_for_link)
async def get_link(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = users_col.find_one({"_id": user_id}).get("lang", "en")
    url = message.text.strip()
    platform = detect_platform(url)

    if platform == "unknown":
        await message.reply(get_text(lang, "unsupported"))
        return

    await state.update_data(link=url)
    await message.reply(get_text(lang, "choose_format"), reply_markup=format_buttons())
    await DownloadState.waiting_for_format.set()

# Callback query for format
@dp.callback_query_handler(state=DownloadState.waiting_for_format)
async def process_format(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    lang = users_col.find_one({"_id": user_id}).get("lang", "en")
    data = await state.get_data()
    url = data.get("link")

    audio_only = "audio" in call.data
    await bot.send_message(call.message.chat.id, get_text(lang, "downloading"))

    result = download_media(url, audio_only=audio_only)
    if os.path.exists(result):
        with open(result, "rb") as f:
            if audio_only:
                await bot.send_audio(call.message.chat.id, f)
            else:
                await bot.send_video(call.message.chat.id, f)
        os.remove(result)
    else:
        await bot.send_message(call.message.chat.id, f"{get_text(lang, 'error')}{result}")

    await state.finish()

# Handle unknown
@dp.message_handler()
async def unknown_cmd(message: types.Message):
    user_id = message.from_user.id
    lang = users_col.find_one({"_id": user_id}).get("lang", "en")
    await message.reply(get_text(lang, "unknown_command"))

# Run
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"status": "bot running"}

    import nest_asyncio
    from aiogram import executor
    nest_asyncio.apply()

    import threading

    def start_bot():
        executor.start_polling(dp, skip_updates=True)

    thread = threading.Thread(target=start_bot)
    thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)

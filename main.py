import logging
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified
from pymongo import MongoClient
import os
import asyncio
import subprocess

from texts import get_text, TEXTS
from buttons import format_buttons
from utils import detect_platform, download_media

def quality_buttons():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for q in ["Best", "144p", "360p", "480p", "720p", "1080p"]:
        keyboard.insert(InlineKeyboardButton(text=q, callback_data=f"quality:{q}"))
    return keyboard

def create_progress_hook(bot, chat_id, message_id, loop):
    def hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            speed = d.get('_speed_str', '').strip()
            eta = d.get('eta', '?')
            text = f"📥 Downloading: {percent} at {speed} | ETA: {eta}s"
            async def update():
                try:
                    await bot.edit_message_text(text, chat_id, message_id)
                except MessageNotModified:
                    pass
            asyncio.run_coroutine_threadsafe(update(), loop)
    return hook

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

client = MongoClient(MONGO_URI)
db = client["tg_downloader"]
users_col = db["users"]

class DownloadState(StatesGroup):
    waiting_for_link = State()
    waiting_for_format = State()
    waiting_for_quality = State()

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

@dp.message_handler(lambda m: m.text.lower() in TEXTS.keys(), state=DownloadState.waiting_for_link)
async def set_lang(message: types.Message, state: FSMContext):
    lang = message.text.lower()
    users_col.update_one({"_id": message.from_user.id}, {"$set": {"lang": lang}})
    await message.reply(get_text(lang, "language_selected"), reply_markup=types.ReplyKeyboardRemove())
    await message.answer(get_text(lang, "guide"))

@dp.message_handler(state=DownloadState.waiting_for_link)
async def get_link(message: types.Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id
    lang = users_col.find_one({"_id": user_id}).get("lang", "en")

    platform = detect_platform(url)
    if platform == "unknown":
        await message.reply(get_text(lang, "unsupported"))
        return

    await state.update_data(link=url)
    await message.reply(get_text(lang, "choose_format"), reply_markup=format_buttons())
    await DownloadState.waiting_for_format.set()

@dp.callback_query_handler(state=DownloadState.waiting_for_format)
async def process_format(call: types.CallbackQuery, state: FSMContext):
    audio_only = "audio" in call.data
    await state.update_data(audio_only=audio_only)
    await call.message.edit_reply_markup()
    await call.message.answer("🔽 Choose quality:", reply_markup=quality_buttons())
    await DownloadState.waiting_for_quality.set()

@dp.callback_query_handler(lambda c: c.data.startswith("quality:"), state=DownloadState.waiting_for_quality)
async def process_quality(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    quality = callback_query.data.split(":")[1]
    if quality == "Best":
        quality = None

    data = await state.get_data()
    url = data.get("link")
    audio_only = data.get("audio_only", False)

    msg = await callback_query.message.answer("⏳ Starting download...")
    loop = asyncio.get_event_loop()
    hook = create_progress_hook(bot, callback_query.message.chat.id, msg.message_id, loop)

    file_path = await asyncio.to_thread(
        download_media, url, audio_only=audio_only, quality=quality, progress_hook=hook
    )

    if file_path == "ERROR_FILE_TOO_LARGE":
        await callback_query.message.answer("❌ File is too large to send via Telegram (limit: 2GB).")
        return

    if file_path.startswith("ERROR"):
        await callback_query.message.answer(f"❌ Error during download:\n{file_path}")
        return

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        await callback_query.message.answer(f"✅ File downloaded: {size_mb:.2f} MB")

        # Try compression if video is too large
        if file_size > 2 * 1024 * 1024 * 1024 and not audio_only:
            await callback_query.message.answer("⚠ File too large! Trying to compress with FFmpeg...")
            compressed_path = file_path.replace(".mp4", "_compressed.mp4")
            cmd = [
                "ffmpeg", "-i", file_path, "-vcodec", "libx264", "-crf", "32",
                "-preset", "fast", compressed_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(compressed_path):
                compressed_size = os.path.getsize(compressed_path)
                if compressed_size <= 2 * 1024 * 1024 * 1024:
                    with open(compressed_path, 'rb') as f:
                        await callback_query.message.answer_video(f)
                    os.remove(compressed_path)
                    os.remove(file_path)
                    await state.finish()
                    return
                else:
                    await callback_query.message.answer("❌ Even after compression, file is too large.")
                    os.remove(compressed_path)
            os.remove(file_path)
            return

        if file_size > 2 * 1024 * 1024 * 1024:
            await callback_query.message.answer("❌ File is too large to send. (Limit: 2GB)")
            os.remove(file_path)
            return

        with open(file_path, 'rb') as f:
            if audio_only:
                await callback_query.message.answer_audio(f)
            else:
                await callback_query.message.answer_video(f)
        os.remove(file_path)
    else:
        await callback_query.message.answer("❌ Failed to download.")
    await state.finish()

@dp.message_handler()
async def unknown_cmd(message: types.Message):
    user_id = message.from_user.id
    lang = users_col.find_one({"_id": user_id}).get("lang", "en")
    await message.reply(get_text(lang, "unknown_command"))

# FastAPI setup
app = FastAPI()

@app.get("/")
def home():
    return {"status": "bot running"}

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_polling())

async def start_polling():
    await dp.start_polling()

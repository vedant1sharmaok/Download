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

# ---------- Force Join + Start Command ----------
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    users_col.update_one({"_id": user_id}, {"$setOnInsert": {"lang": "en"}}, upsert=True)
    await state.finish()

    required_channels = ["@Botsassociations", "@heroxstoreofficial"]

    not_joined = []
    for ch in required_channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(ch)
        except:
            not_joined.append(ch)

    # Always send welcome image regardless of join status
    markup = InlineKeyboardMarkup().add(
        *[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.lstrip('@')}") for ch in required_channels],
        InlineKeyboardButton("✅ I've Joined", callback_data="joined_channels")
    )
    with open("assets/welcome.jpg", "rb") as photo:
        await bot.send_photo(
            message.chat.id,
            photo,
            caption="👋 Welcome!\n\nPlease join the required channels to continue using the bot.",
            reply_markup=markup
        )
    return


    await show_main_menu(message)

@dp.callback_query_handler(lambda c: c.data == "joined_channels")
async def joined_channels(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    required_channels = ["@Botsassociations", "@heroxstoreofficial"]

    not_joined = []
    for ch in required_channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(ch)
        except:
            not_joined.append(ch)

    if not_joined:
        await callback_query.answer("❌ You must join all required channels!", show_alert=True)
        return

    await callback_query.message.delete()
    await show_main_menu(callback_query.message)

# ---------- UI: Menus ----------
async def show_main_menu(message: types.Message):
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🌐 Available Websites", callback_data="category_websites"),
        InlineKeyboardButton("📩 Contact Developer", callback_data="contact_dev"),
        InlineKeyboardButton("⬇ Start Download", callback_data="start_download"),
    )
    await message.answer("🏠 *Main Menu*", parse_mode="Markdown", reply_markup=markup)

async def show_website_categories(message: types.Message):
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("📺 Streaming", callback_data="streaming_sites"),
        InlineKeyboardButton("🎓 Educational", callback_data="edu_sites"),
        InlineKeyboardButton("📱 Social Media", callback_data="social_sites"),
        InlineKeyboardButton("🔞 Adult", callback_data="adult_sites"),
        InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
    )
    await message.answer("🌐 *Available Platforms*", parse_mode="Markdown", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "category_websites")
async def show_websites_handler(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await show_website_categories(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main_handler(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await show_main_menu(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == "contact_dev")
async def contact_dev_handler(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer(
        "👨‍💻 *Developer Info:*\n"
        "• Name: Vedant\n"
        "• Telegram: [@Herox_Gfx](https://t.me/Herox_gfx)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

@dp.callback_query_handler(lambda c: c.data in ["streaming_sites", "edu_sites", "social_sites", "adult_sites"])
async def category_handler(callback_query: types.CallbackQuery):
    categories = {
        "streaming_sites": "📺 Streaming Platforms:\nExamples: YouTube, Twitch, etc.",
        "edu_sites": "🎓 Educational Platforms:\nExamples: Coursera, edX, Udemy",
        "social_sites": "📱 Social Media:\nExamples: Facebook, Instagram, TikTok",
        "adult_sites": "🔞 Adult Sites:\nExamples: Pornhub, Xvideos (allowed only if permitted)"
    }
    text = categories.get(callback_query.data, "Coming Soon...")
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Back to Categories", callback_data="category_websites")
    )
    await callback_query.message.delete()
    await callback_query.message.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "start_download")
async def start_download_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("🔗 Please send the video link you'd like to download.")
    await DownloadState.waiting_for_link.set()

# ---------- Language + Download FSM ----------
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

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        await callback_query.message.answer(f"✅ Downloaded file size: {size_mb:.2f} MB")

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

# ---------- FastAPI Bootstrapping ----------
app = FastAPI()

@app.get("/")
def home():
    return {"status": "bot running"}

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_polling())

async def start_polling():
    await dp.start_polling()
              

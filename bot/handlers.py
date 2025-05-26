from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.downloader import download_media, download_spotify
from bot.utils import detect_platform
from bot.texts import get_text
from bot.config import ADMIN_IDS
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

mongo = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo["downloader_bot"]
get_user_collection = lambda: db["users"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_user_collection()
    user_id = update.effective_user.id
    await users.update_one({"user_id": user_id}, {"$setOnInsert": {"lang": "en"}}, upsert=True)

    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang|en")],
        [InlineKeyboardButton("हिन्दी", callback_data="lang|hi")]
    ]
    await update.message.reply_photo(
        photo="https://via.placeholder.com/800x300.png?text=Welcome+to+Downloader+Bot",
        caption=get_text("en", "welcome"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_user_collection()
    user_data = await users.find_one({"user_id": update.effective_user.id})
    lang = user_data.get("lang", "en")
    await update.message.reply_text(get_text(lang, "guide"))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    users = get_user_collection()
    await query.answer()

    if query.data == "lang_menu":
        keyboard = [
            [InlineKeyboardButton("English", callback_data="lang|en")],
            [InlineKeyboardButton("हिन्दी", callback_data="lang|hi")]
        ]
        await query.edit_message_text(get_text("en", "choose_language"), reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("lang|"):
        lang_code = query.data.split("|")[1]
        await users.update_one({"user_id": user_id}, {"$set": {"lang": lang_code}})
        await query.edit_message_text(get_text(lang_code, "language_selected"))
    else:
        await handle_download(update, context)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    users = get_user_collection()
    user_data = await users.find_one({"user_id": update.effective_user.id})
    lang = user_data.get("lang", "en")
    platform = detect_platform(url)

    if platform == "youtube":
        keyboard = [
            [InlineKeyboardButton("720p", callback_data=f"video720|{url}")],
            [InlineKeyboardButton("360p", callback_data=f"video360|{url}")],
            [InlineKeyboardButton(get_text(lang, "btn_audio"), callback_data=f"audio|{url}")]
        ]
        await update.message.reply_text(get_text(lang, "choose_format"), reply_markup=InlineKeyboardMarkup(keyboard))
    elif platform == "spotify":
        keyboard = [[InlineKeyboardButton(get_text(lang, "btn_audio"), callback_data=f"spotify|{url}")]]
        await update.message.reply_text("Spotify audio available:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif platform == "reso":
        await update.message.reply_text("Reso support is under development.")
    else:
        await update.message.reply_text("Unsupported or unknown link.")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = get_user_collection()
    user_data = await users.find_one({"user_id": query.from_user.id})
    lang = user_data.get("lang", "en")
    format_type, url = query.data.split("|")
    msg = await query.message.reply_text("Please wait...")

    try:
        if format_type == "video720":
            file_path = download_media(url, "best[height<=720]")
        elif format_type == "video360":
            file_path = download_media(url, "best[height<=360]")
        elif format_type == "audio":
            file_path = download_media(url, "bestaudio")
        elif format_type == "spotify":
            file_path = download_spotify(url)
        else:
            await msg.edit_text("Unsupported format.")
            return

        await msg.delete()
        await query.message.reply_document(document=open(file_path, "rb"))
        await asyncio.sleep(5)
        os.remove(file_path)
    except Exception as e:
        await msg.edit_text(get_text(lang, "error") + str(e))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Access denied.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast Your message here")
        return

    msg = " ".join(context.args)
    users = get_user_collection()
    all_users = users.find()

    sent = failed = 0
    async for user in all_users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 *Broadcast:*

{escape_markdown(msg)}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"Broadcast complete. Sent: {sent}, Failed: {failed}")

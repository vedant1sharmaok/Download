# handlers.py

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from buttons import format_buttons
from utils import detect_platform, download_media, escape_markdown
from texts import get_text
from database import get_user_collection
from config import ADMIN_IDS
import os

# Handle download link input
async def handle_link(message: types.Message, lang: str, state: FSMContext):
    url = message.text.strip()
    platform = detect_platform(url)

    if platform == "unknown":
        await message.reply(get_text(lang, "unsupported"))
        return

    await state.update_data(link=url)
    await message.reply(get_text(lang, "choose_format"), reply_markup=format_buttons())

# Handle format selection from inline buttons
async def process_format_selection(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    url = data.get("link")

    users = get_user_collection()
    lang = users.find_one({"_id": user_id}).get("lang", "en")

    audio_only = "audio" in call.data
    await call.message.answer(get_text(lang, "downloading"))

    result = download_media(url, audio_only=audio_only)
    if os.path.exists(result):
        with open(result, "rb") as f:
            if audio_only:
                await call.message.answer_audio(f)
            else:
                await call.message.answer_video(f)
        os.remove(result)
    else:
        await call.message.answer(f"{get_text(lang, 'error')}{result}")

    await state.finish()

# Admin broadcast handler
async def broadcast_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("Access denied.")
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply("Usage: /broadcast Your message here")
        return

    msg = args[1]
    users = get_user_collection()
    all_users = users.find()

    sent = failed = 0
    for user in all_users:
        try:
            await message.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 *Broadcast:*\n\n{escape_markdown(msg)}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except Exception:
            failed += 1

    await message.reply(f"Broadcast complete.\n✅ Sent: {sent}\n❌ Failed: {failed}")
    

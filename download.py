import os
import yt_dlp
import asyncio
from aiogram.types import Message

DOWNLOAD_DIR = "./downloads"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ✅ Original hook (not thread-safe inside yt_dlp)
def build_telegram_progress_hook(message: Message):
    async def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            speed = d.get('_speed_str', '')
            eta = d.get('_eta_str', '')
            text = f"⬇ Downloading... `{percent}` at `{speed}` | ETA: `{eta}`"
            try:
                await message.edit_text(text, parse_mode="Markdown")
            except:
                pass
        elif d['status'] == 'finished':
            try:
                await message.edit_text("✅ Download finished. Preparing file...", parse_mode="Markdown")
            except:
                pass

    return progress_hook


# ✅ Thread-safe wrapper for use inside yt_dlp hooks
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
                except:
                    pass

            loop.call_soon_threadsafe(asyncio.create_task, update())

        elif d['status'] == 'finished':
            async def done():
                try:
                    await bot.edit_message_text("✅ Download finished. Preparing file...", chat_id, message_id)
                except:
                    pass

            loop.call_soon_threadsafe(asyncio.create_task, done())

    return hook


# ✅ Download using Telegram message context
async def download_media(url: str, tg_msg: Message, format_code: str = "best") -> str:
    # Audio-only conversion
    postprocessors = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }] if 'audio' in format_code else []

    # Progress Hook (runs async updates safely)
    hook = create_progress_hook(tg_msg.bot, tg_msg.chat.id, tg_msg.message_id, asyncio.ge
            

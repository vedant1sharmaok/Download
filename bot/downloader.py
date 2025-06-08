import os
import yt_dlp
from aiogram.types import Message

DOWNLOAD_DIR = "./downloads"


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
            await message.edit_text("✅ Download finished. Preparing file...")

    return progress_hook


async def download_media(url: str, tg_msg: Message, format_code: str = "best") -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Optional audio-only conversion
    postprocessors = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }] if 'audio' in format_code else []

    ydl_opts = {
        'format': format_code,
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [lambda d: tg_msg.bot.loop.create_task(build_telegram_progress_hook(tg_msg)(d))],
        'quiet': True,
        'postprocessors': postprocessors,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


async def download_spotify(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_dir = os.path.abspath(DOWNLOAD_DIR)
    os.system(f"spotdl download '{url}' --output {output_dir}")

    files = sorted(
        os.listdir(output_dir),
        key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
        reverse=True
    )
    return os.path.join(output_dir, files[0]) if files else None
    

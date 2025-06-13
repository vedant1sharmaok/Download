import os
import re
import yt_dlp
from yt_dlp.utils import sanitize_filename

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes

def escape_md(text):
    return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

def detect_platform(url: str) -> str:
    patterns = {
        "youtube": r"(youtube\.com|youtu\.be)",
        "spotify": r"(spotify\.com)",
        "reso": r"(reso\.app|reso\.com)",
        "facebook": r"(facebook\.com)",
        "instagram": r"(instagram\.com)",
        "tiktok": r"(tiktok\.com)",
        "twitter": r"(twitter\.com|x\.com)",
        "dailymotion": r"(dai\.ly|dailymotion\.com)",
        "pornhub": r"(pornhub\.com)",
        "xhamster": r"(xhamster\.com)",
    }
    for platform, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return "unknown"

def download_media(url: str, audio_only=False, quality=None, progress_hook=None):
    try:
        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            'format': quality or ('bestaudio/best' if audio_only else 'best'),
            'outtmpl': 'downloads/%(title).70s.%(ext)s',
            'noplaylist': True,
            'quiet': False,
            'progress_hooks': [progress_hook] if progress_hook else [],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if audio_only else [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Ensure filename is safe
            filename = sanitize_filename(filename)

            # Use mp3 extension if audio-only
            if audio_only:
                filename = os.path.splitext(filename)[0] + '.mp3'

            # Check file size
            file_size = os.path.getsize(filename)
            if file_size > MAX_FILE_SIZE:
                os.remove(filename)
                return "ERROR_FILE_TOO_LARGE"

            return filename

    except Exception as e:
        return f"ERROR: {str(e)}"
        

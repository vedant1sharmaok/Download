# utils.py

import re
import yt_dlp

# Common platform detection using regex (can expand as needed)
def detect_platform(url: str) -> str:
    patterns = {
        "youtube": r"(youtube\.com|youtu\.be)",
        "spotify": r"(spotify\.com)",
        "reso": r"(reso\.app|reso\.com)",
        "facebook": r"(facebook\.com)",
        "instagram": r"(instagram\.com)",
        "tiktok": r"(tiktok\.com)",
        "twitter": r"(twitter\.com|x\.com)",
        "dailymotion": r"(dailymotion\.com)",
    }

    for platform, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return "unknown"

# Download function using yt-dlp
def download_media(url: str, audio_only=False):
    try:
        ydl_opts = {
            'format': 'bestaudio/best' if audio_only else 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if audio_only else [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only and 'ext' in info:
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            return filename
    except Exception as e:
        return str(e)

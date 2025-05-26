import os
import yt_dlp

DOWNLOAD_DIR = "./downloads"

def download_media(url: str, format_code: str = "best") -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ydl_opts = {
        'format': format_code,
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if 'audio' in format_code else []
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def download_spotify(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_dir = os.path.abspath(DOWNLOAD_DIR)
    os.system(f"spotdl download '{url}' --output {output_dir}")
    files = sorted(os.listdir(output_dir), key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
    return os.path.join(output_dir, files[0]) if files else None

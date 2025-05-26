def detect_platform(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "spotify.com" in url:
        return "spotify"
    elif "reso.com" in url:
        return "reso"
    else:
        return "unknown"

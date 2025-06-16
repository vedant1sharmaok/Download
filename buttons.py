# buttons.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Full language names in native scripts
LANGUAGES = [
    "English",
    "हिन्दी",
    "Español",
    "العربية",
    "Français",
    "Русский",
    "中文",
    "বাংলা",
    "Português",
    "Bahasa Indonesia"
]

def format_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Audio Only", callback_data="format_audio")],
        [InlineKeyboardButton(text="🎞️ Video", callback_data="format_video")],
    ])

def language_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=lang, callback_data=f"setlang:{lang}") for lang in LANGUAGES]
    keyboard.add(*buttons)
    return keyboard

def force_join_keyboard(channel_username):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{channel_username}"),
        InlineKeyboardButton("✅ I've Joined", callback_data="joined")
        )
    

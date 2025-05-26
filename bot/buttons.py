# buttons.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Audio Only", callback_data="format_audio")],
        [InlineKeyboardButton(text="🎞️ Video", callback_data="format_video")],
    ])
  

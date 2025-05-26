texts = {
    "en": {
        "welcome": "Welcome to the Downloader Bot!",
        "guide": "Send me a video or audio link (YouTube, Spotify, etc.), and choose the format you want to download.",
        "choose_format": "Choose the quality/format:",
        "error": "An error occurred: ",
        "btn_audio": "Audio Only",
        "language_selected": "Language selected!",
        "choose_language": "Choose your language:"
    },
    "hi": {
        "welcome": "डाउनलोडर बॉट में आपका स्वागत है!",
        "guide": "मुझे एक वीडियो या ऑडियो लिंक भेजें (YouTube, Spotify आदि), और वह फॉर्मेट चुनें जिसमें आप डाउनलोड करना चाहते हैं।",
        "choose_format": "गुणवत्ता/फॉर्मेट चुनें:",
        "error": "एक त्रुटि हुई: ",
        "btn_audio": "सिर्फ ऑडियो",
        "language_selected": "भाषा चयनित!",
        "choose_language": "अपनी भाषा चुनें:"
    }
}

def get_text(lang, key):
    return texts.get(lang, texts["en"]).get(key, key)

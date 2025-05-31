import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("BOT_TOKEN and WEBHOOK_URL must be set as environment variables")

url = f"https://api.telegram.org/bot7084577439:AAFvktRSNri6cPCwt9TFGVrLbDWrLuXdEtg/setWebhook"
payload = {"url": f"https://puzzled-felicia-heroxgfxmovie-4a7dac59.koyeb.app/webhook"}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())

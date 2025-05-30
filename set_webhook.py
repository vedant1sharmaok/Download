import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("BOT_TOKEN and WEBHOOK_URL must be set as environment variables")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
payload = {"url": f"{WEBHOOK_URL}/webhook"}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())

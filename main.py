from fastapi import FastAPI, Request
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext.webhook import ApplicationRequestHandler
from bot.handlers import start, help_command, handle_link, handle_callback, broadcast
import os
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()
tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("help", help_command))
tg_app.add_handler(CommandHandler("broadcast", broadcast))
tg_app.add_handler(CallbackQueryHandler(handle_callback))
tg_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))

handler = ApplicationRequestHandler(application=tg_app)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    return await handler.handle(request)

@app.get("/")
def root():
    return {"status": "Bot is running."}

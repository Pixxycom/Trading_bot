 #!/usr/bin/env python3
import os
import logging
import ccxt
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify
from threading import Thread
import requests
import time

# ===== Initialization ===== #
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Telegram bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ===== UPTIME MONITORING SETUP ===== #
PING_URL = os.getenv('UPTIME_ROBOT_URL')
PING_INTERVAL = 300  # 5 minutes

def ping_server():
    """Periodically ping the server to keep it awake"""
    while True:
        try:
            if PING_URL:
                requests.get(PING_URL)
                logger.info("Uptime Robot ping sent")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
        time.sleep(PING_INTERVAL)

# ===== MODIFIED INITIALIZATION FOR RENDER ===== #
async def run_bot():
    """Run Telegram bot in webhook mode for Render"""
    WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL')
    
    await application.bot.set_webhook(
        url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
        drop_pending_updates=True
    )
    logger.info(f"Bot running in webhook mode at {WEBHOOK_URL}")

# ===== FLASK ENDPOINTS ===== #
@app.route('/')
def home():
    return "Trading Bot Active - Deployed on Render"

@app.route('/ping')
def ping():
    return jsonify({"status": "alive", "bot": "running"}), 200

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        Thread(target=lambda: application.update_queue.put(update)).start()
    return jsonify(success=True)

# ===== BOT COMMAND HANDLERS ===== #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome to the Trading Bot!')

application.add_handler(CommandHandler("start", start))

# ===== RENDER-SPECIFIC LAUNCH ===== #
if __name__ == '__main__':
    # Start uptime monitoring thread
    Thread(target=ping_server, daemon=True).start()
    
    # Start the bot
    application.run_polling()

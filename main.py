 #!/usr/bin/env python3.9
import os
import logging
import ccxt
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from flask import Flask, request, jsonify
from threading import Thread
import requests
import time

# ===== Setup Logging =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Flask App Setup =====
app = Flask(__name__)

# ===== Uptime Monitoring =====
PING_URL = os.getenv('UPTIME_ROBOT_URL')  # Put this in Replit Secrets
PING_INTERVAL = 300  # 5 minutes

def ping_server():
    """Periodically ping the server to keep Replit awake."""
    while True:
        try:
            if PING_URL:
                requests.get(PING_URL)
                logger.info("Uptime Robot ping sent")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
        time.sleep(PING_INTERVAL)

# ===== Telegram Bot Setup =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# ===== Telegram Command Handlers =====
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Hello! The trading bot is active.")

dispatcher.add_handler(CommandHandler("start", start))

# ===== Run Bot in Webhook Mode =====
def run_bot():
    PORT = int(os.environ.get('PORT', 8080))
    WEBHOOK_URL = f"https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co"

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )
    logger.info(f"🚀 Bot running in webhook mode at {WEBHOOK_URL}")

# ===== Flask Endpoints =====
@app.route('/')
def home():
    return "✅ Trading Bot is Live - Flask is running."

@app.route('/ping')
def ping():
    return jsonify({"status": "alive", "bot": "running"}), 200

@app.route(f'/{os.getenv("TELEGRAM_BOT_TOKEN")}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(), updater.bot)
        dispatcher.process_update(update)
    return jsonify(success=True)

# ===== Launch App =====
if __name__ == '__main__':
    # Start background ping thread
    Thread(target=ping_server, daemon=True).start()

    # Check if running on Replit
    if 'REPLIT' in os.environ:
        run_bot()
        app.run(host='0.0.0.0', port=8080)
    else:
        # Fallback to polling for local testing
        updater.start_polling()
        updater.idle()

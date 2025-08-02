#!/usr/bin/env python3.9
import os
import logging
import ccxt
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask, request, jsonify
from threading import Thread
import requests
import time

# ===== Logging Setup =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Flask App Setup =====
app = Flask(__name__)

# ===== Uptime Monitoring =====
PING_URL = os.getenv('UPTIME_ROBOT_URL')  # Set this in Render or Replit Secrets
PING_INTERVAL = 300  # 5 minutes

def ping_server():
    """Ping to keep the app awake (used by UptimeRobot)."""
    while True:
        try:
            if PING_URL:
                requests.get(PING_URL)
                logger.info("✅ UptimeRobot ping sent")
        except Exception as e:
            logger.error(f"❌ Ping failed: {e}")
        time.sleep(PING_INTERVAL)

# ===== Telegram Bot Setup =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Fail early if token is missing
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN in environment variables")

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# ===== Command Handlers =====
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

# ===== Flask Routes =====
@app.route('/')
def home():
    return "✅ Trading Bot is Live - Flask running."

@app.route('/ping')
def ping():
    return jsonify({"status": "alive", "bot": "running"}), 200

@app.route(f'/{os.getenv("TELEGRAM_BOT_TOKEN")}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), updater.bot)
    dispatcher.process_update(update)
    return jsonify(success=True)

# ===== App Launcher =====
if __name__ == '__main__':
    Thread(target=ping_server, daemon=True).start()

    # Run on Replit or Render using webhook
    if 'REPLIT' in os.environ or 'RENDER' in os.environ:
        run_bot()
        app.run(host='0.0.0.0', port=8080)
    else:
        # Fallback to polling when run locally (for dev/test)
        updater.start_polling()
        updater.idle()

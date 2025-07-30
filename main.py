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
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# ===== UPTIME MONITORING SETUP ===== #
PING_URL = os.getenv('UPTIME_ROBOT_URL')  # Set this in Render environment variables
PING_INTERVAL = 300  # 5 minutes (matches Uptime Robot's minimum)

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
def run_bot():
    """Run Telegram bot in webhook mode for Render"""
    WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL')  # Set your Render external URL in environment variables
    
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.getenv('PORT', 10000)),
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
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
        update = Update.de_json(request.get_json(), updater.bot)
        dispatcher.process_update(update)
    return jsonify(success=True)

# ===== BOT COMMAND HANDLERS ===== #
# Add your command handlers here (start, help, etc.)
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome to the Trading Bot!')

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# ===== RENDER-SPECIFIC LAUNCH ===== #
if __name__ == '__main__':
    # Start uptime monitoring thread
    Thread(target=ping_server, daemon=True).start()
    
    # Start the bot
    run_bot()

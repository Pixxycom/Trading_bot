#!/usr/bin/env python3
import os
import logging
import ccxt
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
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

# PROPER INITIALIZATION (FIX FOR THE ERROR)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
application = Application.builder().token(TELEGRAM_TOKEN).build()  # Correct modern initialization

# ===== UPTIME MONITORING SETUP ===== #
PING_URL = os.getenv('UPTIME_ROBOT_URL')
PING_INTERVAL = 300  # 5 minutes

def ping_server():
    while True:
        try:
            if PING_URL:
                requests.get(PING_URL)
                logger.info("Uptime Robot ping sent")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
        time.sleep(PING_INTERVAL)

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

# ===== LAUNCH ===== #
if __name__ == '__main__':
    # Start uptime monitoring
    Thread(target=ping_server, daemon=True).start()
    
    # Check if running on Render
    if os.getenv('RENDER'):
        # Webhook configuration for Render
        PORT = int(os.getenv('PORT', 5000))
        WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL')
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
            secret_token=os.getenv('WEBHOOK_SECRET', '')
        )
    else:
        # Local development with polling
        application.run_polling()

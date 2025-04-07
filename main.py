import random
import logging
import time

from flask import Flask, request, jsonify
from newspaper import Article, Config
import requests

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# ----------------------
# Configuration Settings
# ----------------------

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.88 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/118.0"
]

USE_PROXY = False
proxies = {
    'http': 'http://your-proxy-url:port',
    'https': 'http://your-proxy-url:port',
}

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def create_config(user_agent):
    config = Config()
    config.browser_user_agent = user_agent
    config.request_headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "DNT": "1",
    }
    config.request_timeout = 10  # seconds
    return config

# ----------------------
# Flask Route
# ----------------------

@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400


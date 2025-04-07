import random
import logging
import time
from flask import Flask, request, jsonify
from newspaper import Article, Config

# -----------------------
# Flask + Logging Setup
# -----------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# -----------------------
# Settings
# -----------------------

MAX_RETRIES = 3
BATCH_DELAY = 3  # delay between articles in seconds

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
]

USE_PROXY = False  # Flip to True if using proxy
proxies = {
    'http': 'http://your-proxy-url:port',
    'https': 'http://your-proxy-url:port',
}

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def create_config():
    ua = get_random_user_agent()
    config = Config()
    config.browser_user_agent = ua
    config.request_headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate"
    }
    return config

# -----------------------
# Article Extraction
# -----------------------

def extract_article(url):
    config = create_config()
    article = Article(url, config=config)

    for attempt in range(MAX_RETRIES):
        try:
            if USE_PROXY:
                article.download(proxies=proxies)
            else:
                article.download()

            article.parse()

            return {
                "title": article.title,
                "authors": article.authors,
                "publish_date": str(article.publish_date) if article.publish_date else None,
                "text": article.text
            }

        except Exception as e:
            wait = 2 ** attempt + random.uniform(0.5, 1.5)
            logging.warning(f"[Attempt {attempt + 1}] Failed to fetch {url}: {e}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

    logging.error(f"❌ All retry attempts failed for {url}")
    return {"error": "Failed after retries"}

# -----------------------
# Flask Route
# -----------------------

@app.route("/batch-extract", methods=["POST"])
def batch_extract():
    data = request.json
    urls = data.get("urls")

    if not urls or not isinstance(urls, list):
        return jsonify({"error": "Please provide a list of URLs under 'urls' key"}), 400

    results = []
    for idx, url in enumerate(urls):
        logging.info(f"🔍 Processing [{idx + 1}/{len(urls)}]: {url}")
        result = extract_article(url)
        results.append({
            "url": url,
            **result
        })

        time.sleep(BATCH_DELAY)

    return jsonify(results), 200


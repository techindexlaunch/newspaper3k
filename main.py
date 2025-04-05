import random
import logging
import time

from flask import Flask, request, jsonify
from newspaper import Article, Config

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# ----------------------
# Configuration Settings
# ----------------------

# List of user agents to rotate for each request.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Optionally use a proxy if needed. Set USE_PROXY to True and update the proxies dictionary.
USE_PROXY = False  # Change to True if you have a proxy service.
proxies = {
    'http': 'http://your-proxy-address:port',
    'https': 'http://your-proxy-address:port',
}

def create_config(user_agent):
    """
    Create a Newspaper3k Config with robust headers to mimic a real browser.
    """
    config = Config()
    config.browser_user_agent = user_agent
    config.request_headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.svpg.com/"
    }
    return config

@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    logging.debug(f"Received data: {data}")
    
    url = data.get("url")
    if not url:
        logging.error("No URL provided in request")
        return jsonify({"error": "No URL provided"}), 400

    # Optional: Introduce a slight delay to prevent rapid-fire requests.
    time.sleep(1)

    try:
        # Set up Newspaper3k with a rotated user agent and robust headers.
        ua = get_random_user_agent()
        config = create_config(ua)
        article = Article(url, config=config)
        
        # If proxy usage is enabled, try downloading with proxies.
        if USE_PROXY:
            try:
                article.download(proxies=proxies)
            except Exception as proxy_exception:
                logging.warning("Proxy download failed, retrying without proxy", exc_info=True)
                article.download()
        else:
            article.download()
        
        article.parse()

        response_data = {
            "title": article.title,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "text": article.text
        }
        logging.debug(f"Extraction successful for URL: {url}")
        return jsonify(response_data), 200

    except Exception as e:
        logging.error("Error processing URL", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

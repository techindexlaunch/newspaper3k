import random
import logging
logging.basicConfig(level=logging.DEBUG)

from flask import Flask, request, jsonify
from newspaper import Article, Config

app = Flask(__name__)

# List of user agents to rotate for each request
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Optionally, set USE_PROXY to True if you want to enable proxy retries.
USE_PROXY = False  # Set to True if you have proxy details
proxies = {
    'http': 'http://your-proxy-address:port',
    'https': 'http://your-proxy-address:port',
}
# If you are not using a proxy, leave USE_PROXY as False.

def create_config(user_agent):
    config = Config()
    config.browser_user_agent = user_agent
    config.request_headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
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

    try:
        # First attempt without proxy
        ua = get_random_user_agent()
        config = create_config(ua)
        article = Article(url, config=config)
        article.download()
        article.parse()
        logging.debug(f"Extraction successful for URL: {url} (without proxy)")
    
    except Exception as e:
        error_str = str(e)
        logging.error("Error processing URL on first attempt", exc_info=True)
        # If a 403 error occurred and proxy usage is enabled, try with proxy
        if "403" in error_str and USE_PROXY:
            try:
                logging.info("403 detected, retrying with proxy...")
                ua = get_random_user_agent()
                config = create_config(ua)
                article = Article(url, config=config)
                article.download(proxies=proxies)
                article.parse()
                logging.debug(f"Extraction successful for URL: {url} (with proxy)")
            except Exception as proxy_e:
                logging.error("Error processing URL with proxy", exc_info=True)
                return jsonify({"error": str(proxy_e)}), 500
        else:
            return jsonify({"error": error_str}), 500

    response_data = {
        "title": article.title,
        "authors": article.authors,
        "publish_date": str(article.publish_date) if article.publish_date else None,
        "text": article.text
    }
    return jsonify(response_data), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

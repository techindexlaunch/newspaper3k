import random
import logging
import time
import requests
from flask import Flask, request, jsonify
from newspaper import Article

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# -----------------------
# Settings
# -----------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
]

def get_random_user_agent():
    """Return a random user agent string."""
    return random.choice(USER_AGENTS)

def fetch_article_html(url):
    """
    Fetch HTML content from the given URL using enhanced headers that mimic a real browser.
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/"
    }
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    return response.text

def extract_article(url):
    """
    Extract article data by manually fetching the HTML and letting Newspaper3k parse it.
    """
    try:
        html = fetch_article_html(url)
        article = Article(url)
        article.set_html(html)
        article.parse()
        return {
            "title": article.title,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "text": article.text
        }
    except Exception as e:
        logging.error(f"Error extracting article from {url}: {e}", exc_info=True)
        return {"error": str(e)}

@app.route("/extract", methods=["POST"])
def extract_route():
    """
    Flask route to handle POST requests for article extraction.
    """
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    result = extract_article(url)
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(debug=True)


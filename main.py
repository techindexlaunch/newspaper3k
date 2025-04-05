import asyncio
import random
import logging
import time

from flask import Flask, request, jsonify
from newspaper import Article, Config
from playwright.async_api import async_playwright

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

# Enable proxy usage if needed. Set USE_PROXY to True and configure your proxy pool.
USE_PROXY = False  # Change to True if you have proxy servers available.
PROXIES = [
    "http://proxy1.example.com:port",
    "http://proxy2.example.com:port",
    "http://proxy3.example.com:port"
]

def get_random_proxy():
    return random.choice(PROXIES)

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

async def get_rendered_html(url: str) -> str:
    """
    Use Playwright to launch a headless browser, navigate to the URL,
    wait for the article to load, and return the fully rendered HTML.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=get_random_user_agent()
        )
        page = await context.new_page()
        logging.debug(f"Navigating to URL: {url}")
        try:
            await page.goto(url, timeout=60000)
        except Exception as nav_error:
            logging.error(f"Error navigating to {url}", exc_info=True)
            raise nav_error
        try:
            await page.wait_for_selector("article", timeout=60000)
        except Exception as wait_error:
            logging.warning(f"Article selector not found for {url}. Proceeding anyway.", exc_info=True)
        html = await page.content()
        await browser.close()
        return html

@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    logging.debug(f"Received data: {data}")
    
    url = data.get("url")
    if not url:
        logging.error("No URL provided in request")
        return jsonify({"error": "No URL provided"}), 400

    # Optional: add a slight delay to prevent rapid-fire requests.
    time.sleep(1)

    try:
        # First, use Playwright to retrieve the fully rendered HTML.
        html_content = asyncio.run(get_rendered_html(url))
        logging.debug("Rendered HTML successfully retrieved.")

        # Now, create a Newspaper3k config with a random user agent.
        ua = get_random_user_agent()
        config = create_config(ua)
        article = Article(url, config=config)
        # Inject the rendered HTML instead of performing a fresh download.
        article.set_html(html_content)
        article.parse()
        logging.debug(f"Extraction successful for URL: {url} without proxy.")
    
    except Exception as e:
        error_str = str(e)
        logging.error("Error on first extraction attempt", exc_info=True)
        # If a 403 error is encountered and proxy usage is enabled, attempt retry.
        if "403" in error_str and USE_PROXY:
            try:
                logging.info("403 detected, retrying with proxy...")
                ua = get_random_user_agent()
                config = create_config(ua)
                article = Article(url, config=config)
                # Retrieve HTML again, now using a proxy
                proxy = {"http": get_random_proxy(), "https": get_random_proxy()}
                html_content_proxy = asyncio.run(get_rendered_html(url))
                article.set_html(html_content_proxy)
                article.parse()
                logging.debug(f"Extraction successful for URL: {url} with proxy.")
            except Exception as proxy_exception:
                logging.error("Error processing URL with proxy", exc_info=True)
                return jsonify({"error": str(proxy_exception)}), 500
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



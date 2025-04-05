import logging
logging.basicConfig(level=logging.DEBUG)

from flask import Flask, request, jsonify
from newspaper import Article, Config

app = Flask(__name__)

# Set up a custom config for Newspaper3k with additional headers
config = Config()
ua = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/83.0.4103.61 Safari/537.36"
)
config.browser_user_agent = ua
config.request_headers = {
    "User-Agent": ua,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.svpg.com/"
}

# Optional: If you want to use a proxy to bypass further blocking,
# define your proxy settings here and use them when downloading the article.
# Uncomment the following lines and update with your proxy details:
#
# proxies = {
#     'http': 'http://your-proxy-address:port',
#     'https': 'http://your-proxy-address:port',
# }

@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    logging.debug(f"Received data: {data}")
    
    url = data.get("url")
    if not url:
        logging.error("No URL provided in request")
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Use the custom config when creating the Article.
        # If using a proxy, uncomment the line below and comment out the next article.download() call.
        # article = Article(url, config=config)
        # article.download(proxies=proxies)
        article = Article(url, config=config)
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


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

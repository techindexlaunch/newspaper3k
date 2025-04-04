from flask import Flask, request, jsonify
from newspaper import Article

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        article = Article(url)
        article.download()
        article.parse()

        response_data = {
            "title": article.title,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "text": article.text
        }
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

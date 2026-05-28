from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import ssl
import random

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "Server is running."


# 4. 발화 내용을 네이버 뉴스에서 검색해서 제목 크롤링
@app.route("/naver-news", methods=["POST"])
def naver_news_skill():
    data = request.get_json(silent=True) or {}
    user_input = data.get("userRequest", {}).get("utterance", "").strip()

    if not user_input:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {
                        "text": "검색어가 없습니다."
                    }
                }]
            }
        })

    query = urllib.parse.quote(user_input)
    url = f"https://search.naver.com/search.naver?where=news&query={query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select(".news_tit")

        titles = []
        for item in items[:5]:
            titles.append(item.get("title", item.get_text(strip=True)))

        if titles:
            result_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
        else:
            result_text = "검색 결과를 찾지 못했습니다."

    except Exception as e:
        result_text = f"크롤링 중 오류가 발생했습니다: {str(e)}"

    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": result_text[:1000]
                }
            }]
        }
    }
    return jsonify(response)


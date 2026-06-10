import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Render 환경변수(Environment Variables)에 OPENAI_API_KEY를 등록해야 합니다.
# OpenAI SDK 최신 버전 초기화 방식입니다.
OPENAI_API_KEY = os.environ.get("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")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# 네이버 뉴스 크롤링 함수 (미래 모빌리티 키워드)
def get_mobility_trends():
    try:
        url = "https://search.naver.com/search.naver?where=news&query=미래+모빌리티+트렌드&sm=tab_opt&sort=1" # 최신순 정렬
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=3)
        
        if res.status_code != 200:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.news_wrap')
        
        trends = []
        for item in news_items[:3]: # 최신 뉴스 3개만 추출
            title_el = item.select_one('.news_tit')
            desc_el = item.select_one('.api_txt_lines.dsc_txt_wrap')
            img_el = item.select_one('.thumb')
            
            if title_el:
                title = title_el.text
                link = title_el['href']
                desc = desc_el.text[:50] + "..." if desc_el else "클릭하여 자세한 내용을 확인하세요."
                img_url = img_el['src'] if img_el else "https://images.unsplash.com/photo-1517976487492-5750f3195933?q=80&w=150"
                
                trends.append({
                    "title": title,
                    "description": desc,
                    "imageUrl": img_url,
                    "link": link
                })
        return trends
    except Exception as e:
        print(f"크롤링 에러: {e}")
        return []

# GPT에게 질문하는 함수
def ask_gpt(prompt):
    if not client:
        return "죄송합니다. AI 서비스 점검 중입니다. (API 키 미등록)"
        
    try:
        # 카카오톡 가독성을 위해 글자 수 제한 및 모빌리티 전문가 페르소나 부여
        system_instruction = "당신은 미래 모빌리티(UAM, 자율주행, PBV 등) 전문가입니다. 사용자의 질문에 대해 핵심만 요약하여 150자 이내의 친절한 한글 문장으로 설명해 주세요."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 빠르고 효율적인 OpenAI 모델
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API 에러: {e}")
        return "AI 답변을 생성하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

@app.route('/', methods=['GET'])
def index():
    return "GPT 기반 미래 모빌리티 챗봇 서버 작동 중", 200

@app.route('/api/mobility', methods=['POST'])
def mobility_skill():
    req = request.get_json()
    user_utterance = req.get('userRequest', {}).get('utterance', '').strip()
    
    # 기본 공통 응답 구조
    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [],
            "quickReplies": [
                {"label": "UAM이 뭐야?", "action": "message", "messageText": "UAM이 뭐야?"},
                {"label": "PBV에 대해 알려줘", "action": "message", "messageText": "PBV에 대해 알려줘"},
                {"label": "최신 트렌드 뉴스", "action": "message", "messageText": "트렌드"}
            ]
        }
    }

    # 1. 사용자가 '트렌드' 또는 '뉴스'를 요구했을 때 -> 크롤링 데이터 반환
    if '트렌드' in user_utterance or '뉴스' in user_utterance:
        trends = get_mobility_trends()
        
        if trends:
            # 카카오톡 ListCard 구조 생성
            list_card_items = []
            for t in trends:
                list_card_items.append({
                    "title": t["title"],
                    "description": t["description"],
                    "imageUrl": t["imageUrl"],
                    "link": {"web": t["link"]}
                })
                
            list_card = {
                "listCard": {
                    "header": {"title": "실시간 미래 모빌리티 트렌드"},
                    "items": list_card_items
                }
            }
            response_body["template"]["outputs"].append(list_card)
        else:
            # 크롤링 실패 시 예외 처리
            response_body["template"]["outputs"].append({
                "simpleText": {"text": "현재 최신 뉴스를 가져올 수 없습니다. 잠시 후 다시 시도해 주세요."}
            })
        return jsonify(response_body)

    # 2. 그 외 모든 질문 -> GPT API가 실시간 답변 생성
    ai_answer = ask_gpt(user_utterance)
    
    # GPT 답변을 담은 텍스트 카드와 웹 검색 버튼 추가
    text_card = {
        "thumbnailCard": {
            "title": "모빌리티 AI 답변",
            "description": ai_answer,
            "thumbnail": {
                "imageUrl": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?q=80&w=600"
            },
            "buttons": [
                {
                    "action": "webLink",
                    "label": "네이버 검색 결과 보기",
                    "webLinkUrl": f"https://search.naver.com/search.naver?query={user_utterance}"
                }
            ]
        }
    }
    response_body["template"]["outputs"].append(text_card)
    return jsonify(response_body)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

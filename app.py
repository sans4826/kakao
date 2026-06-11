import os
import urllib.parse
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def ask_gpt(prompt):
    if not client:
        return "죄송합니다. AI 서비스 점검 중입니다. (API 키 미등록)"
        
    try:
        system_instruction = "당신은 미래 모빌리티(UAM, 자율주행, PBV 등) 전문가입니다. 사용자의 질문에 대해 핵심만 요약하여 친절한 한글 문장으로 설명해 주세요."
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
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
    
    # 1. 키워드에 따라 GPT에게 보낼 프롬프트 조정
    gpt_prompt = user_utterance
    if '트렌드' in user_utterance or '뉴스' in user_utterance:
        gpt_prompt = "최신 미래 모빌리티(UAM, 자율주행, 전기차 등) 관련 주요 트렌드나 동향 3가지를 카카오톡 메시지처럼 보기 좋게 요약해서 알려줘."

    # 2. GPT 답변 생성
    ai_answer = ask_gpt(gpt_prompt)
    
    # 3. 네이버 검색용 한글 URL 인코딩 (이 부분이 추가되었습니다!)
    encoded_query = urllib.parse.quote(user_utterance)
    search_url = f"https://search.naver.com/search.naver?query={encoded_query}"
    
    # 4. 카카오톡 응답 구조 생성
    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": "모빌리티 AI 답변",
                        "description": ai_answer,
                        "thumbnail": {
                            "imageUrl": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?q=80&w=600"
                        },
                        "buttons": [
                            {
                                "action": "webLink",
                                "label": "네이버 검색 결과 보기",
                                "webLinkUrl": search_url
                            }
                        ]
                    }
                }
            ],
            "quickReplies": [
                {"label": "UAM이 뭐야?", "action": "message", "messageText": "UAM이 뭐야?"},
                {"label": "PBV에 대해 알려줘", "action": "message", "messageText": "PBV에 대해 알려줘"},
                {"label": "최신 트렌드 뉴스", "action": "message", "messageText": "트렌드"}
            ]
        }
    }
    return jsonify(response_body)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


# --- (기존 코드 유지) ---
# @app.route('/api/mobility', ...) 끝나는 부분 아래에 추가하세요!

@app.route('/api/recommend', methods=['POST'])
def recommend_skill():
    req = request.get_json()
    user_utterance = req.get('userRequest', {}).get('utterance', '').strip()
    
    # 1. 라이프스타일 분석 및 추천용 맞춤 프롬프트 구성
    gpt_prompt = f"사용자가 자신의 이동 스타일이나 취향을 다음과 같이 말했습니다: '{user_utterance}'\n이 라이프스타일을 분석해서 가장 잘 어울리는 미래 모빌리티(예: 1인용 PBV, UAM, 자율주행 캠핑카, e-VTOL 등)를 하나만 추천해주고, 그 이유를 카카오톡 메시지처럼 친절하고 흥미롭게 3~4문장으로 설명해줘."

    # 2. GPT 답변 생성
    ai_answer = ask_gpt(gpt_prompt)
    
    # 3. 카카오톡 응답 구조 (basicCard)
    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": "🔮 내게 딱 맞는 미래 모빌리티는?",
                        "description": ai_answer,
                        "thumbnail": {
                            # 미래지향적인 자동차/이동수단 느낌의 썸네일 이미지
                            "imageUrl": "https://images.unsplash.com/photo-1519335345719-5d20b666a2cb?q=80&w=600" 
                        },
                        "buttons": [
                            {
                                "action": "share",
                                "label": "추천 결과 공유하기"
                            }
                        ]
                    }
                }
            ],
            # 사용자가 쉽게 테스트해볼 수 있도록 예시 버튼 제공
            "quickReplies": [
                {"label": "왕복 2시간 출퇴근", "action": "message", "messageText": "매일 왕복 2시간 출퇴근해"},
                {"label": "주말마다 캠핑", "action": "message", "messageText": "주말마다 차박 캠핑을 즐겨"},
                {"label": "운전이 너무 싫어", "action": "message", "messageText": "운전하는 걸 너무 귀찮아해"}
            ]
        }
    }
    return jsonify(response_body)

# --- 아래는 원래 있던 실행 코드 ---
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host='0.0.0.0', port=port)

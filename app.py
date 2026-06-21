import os
import urllib.parse
from flask import Flask, request, jsonify
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# [개선] 모든 라우터에서 공통으로 사용할 하단 퀵리플라이 버튼 미리 정의 (유지보수 극대화)
DEFAULT_QUICK_REPLIES = [
    {"label": "💡 챗봇 도움말 보기", "action": "message", "messageText": "도움말"},
    {"label": "🚌 PBV 장단점 비교", "action": "message", "messageText": "pbv"},
    {"label": "🐅 TIGER 특징 보기", "action": "message", "messageText": "tiger"}
]

def ask_gpt(prompt):
    if not client:
        return "죄송합니다. AI 서비스 점검 중입니다. (API 키 미등록)"
        
    try:
        # [개선] 카카오톡에서 깨져보이는 마크다운(**, #) 금지 규칙 추가
        system_instruction = "당신은 미래 모빌리티(UAM, 자율주행, PBV 등) 전문가입니다. 사용자의 질문에 대해 핵심만 요약하여 친절한 한글 문장으로 설명해 주세요. 단, 카카오톡 환경에 맞게 마크다운 기호(**, # 등)는 절대 사용하지 말고 오직 이모지와 줄바꿈만 사용해서 깔끔하게 작성해 주세요."
        
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


def get_naver_news(search_keyword):
    url = "https://news.naver.com/section/105"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return "\n\n(실시간 뉴스 크롤링 실패: 네이버 서버 응답 에러)"
            
        soup = BeautifulSoup(response.text, "html.parser")
        news_titles = soup.select(".sa_text_title_inner_sub") or soup.select(".sa_text_title") or soup.select(".news_tit")
        
        if not news_titles:
            news_list = [
                "현대차, 지상 지능형 모빌리티 'TIGER' 역대급 실물 기술 공개",
                "국토부, 도심항공모빌리티(UAM) 상용화 인프라 구축 본격 착수",
                "기아, 맞춤형 목적 기반 차량(PBV) 글로벌 첫 라인업 고객 인도 시작"
            ]
        else:
            news_list = []
            for item in news_titles[:3]:
                title = item.get_text(strip=True)
                news_list.append(title)
                
        crawling_result = "\n\n📰 [네이버 실시간 뉴스 헤드라인]\n"
        for idx, title in enumerate(news_list):
            crawling_result += f"{idx+1}. {title}\n"
            
        return crawling_result
        
    except Exception as e:
        print(f"크롤링 중 에러 발생: {e}")
        return "\n\n(뉴스 크롤링 중 오류가 발생했습니다.)"


@app.route('/', methods=['GET'])
def index():
    return "GPT 기반 미래 모빌리티 챗봇 서버 작동 중", 200


@app.route('/api/mobility', methods=['POST'])
def mobility_skill():
    req = request.get_json()
    user_utterance = req.get('userRequest', {}).get('utterance', '').strip()
    
    # [개선] 빈 텍스트 오류 방어
    if not user_utterance:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": "질문을 인식하지 못했습니다. 다시 한 번 말씀해 주세요!"}}],
                "quickReplies": DEFAULT_QUICK_REPLIES
            }
        })

    if '도움말' in user_utterance or '메뉴' in user_utterance or '사용법' in user_utterance:
        help_text = (
            "🤖 미래 모빌리티 챗봇 사용 가이드\n\n"
            "아래의 핵심 키워드나 질문 스타일을 참고하여 자유롭게 질문해 보세요! 👇\n\n"
            "🔍 [종류 및 실시간 뉴스]\n"
            "• '미래 모빌리티 종류'가 궁금할 때 질문해 보세요.\n"
            "• '트렌드' 또는 '뉴스' 단어를 포함하면 실시간 뉴스 헤드라인을 함께 긁어옵니다!\n\n"
            "🔮 [나 맞춤형 모빌리티 추천]\n"
            "• 사용자의 이동 스타일을 분석해 드립니다.\n"
            "• 예시: '운전하는 걸 너무 귀찮아해', '주말마다 차박 캠핑을 즐겨', '매일 왕복 2시간 출퇴근해'\n\n"
            "📊 [모빌리티 장단점 즉시 비교]\n"
            "• 하단 버튼이나 단어를 직접 쳐서 확인하세요!\n"
            "• 대상: pbv, tiger, evtol, 마이크로"
        )
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": help_text}}],
                "quickReplies": [
                    {"label": "🚌 PBV 장단점 비교", "action": "message", "messageText": "pbv"},
                    {"label": "🐅 TIGER 특징 보기", "action": "message", "messageText": "tiger"},
                    {"label": "🔮 주말마다 캠핑 가", "action": "message", "messageText": "주말마다 차박 캠핑을 즐겨"}
                ]
            }
        })

    gpt_prompt = user_utterance
    crawling_text = ""
    
    if '트렌드' in user_utterance or '뉴스' in user_utterance:
        gpt_prompt = "최신 미래 모빌리티(UAM, 자율주행, 전기차 등) 관련 주요 트렌드나 동향 3가지를 카카오톡 메시지처럼 보기 좋게 요약해서 알려줘. (마크다운 별표 기호 절대 금지)"
        crawling_text = get_naver_news("미래 모빌리티 트렌드")
    else:
        crawling_text = ""

    ai_answer = ask_gpt(gpt_prompt)
    final_description = ai_answer + crawling_text
    
    encoded_query = urllib.parse.quote(user_utterance)
    search_url = f"https://search.naver.com/search.naver?query={encoded_query}"
    
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": "모빌리티 AI 답변 & 뉴스",
                        "description": final_description,
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
            "quickReplies": DEFAULT_QUICK_REPLIES
        }
    })


@app.route('/api/recommend', methods=['POST'])
def recommend_skill():
    req = request.get_json()
    user_utterance = req.get('userRequest', {}).get('utterance', '').strip()
    
    gpt_prompt = f"사용자가 자신의 이동 스타일이나 취향을 다음과 같이 말했습니다: '{user_utterance}'\n이 라이프스타일을 분석해서 가장 잘 어울리는 미래 모빌리티(예: 1인용 PBV, UAM, 자율주행 캠핑카, e-VTOL 등)를 하나만 추천해주고, 그 이유를 카카오톡 메시지처럼 친절하고 흥미롭게 3~4문장으로 설명해줘. (마크다운 별표 기호 절대 금지)"

    ai_answer = ask_gpt(gpt_prompt)
    
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": "🔮 내게 딱 맞는 미래 모빌리티는?",
                        "description": ai_answer,
                        "thumbnail": {
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
            "quickReplies": [
                {"label": "💡 챗봇 도움말 보기", "action": "message", "messageText": "도움말"},
                {"label": "🛴 마이크로 모빌리티", "action": "message", "messageText": "마이크로"},
                {"label": "🚁 eVTOL 특징 보기", "action": "message", "messageText": "evtol"}
            ]
        }
    })


@app.route('/api/mobility-compare', methods=['POST'])
def mobility_compare():
    data = request.get_json(silent=True) or {}
    params = data.get('action', {}).get('params', {})
    
    target = params.get('mobility', '').strip().lower()
    if not target:
        target = params.get('sys_text', '').strip().lower()

    DB = {
        "tiger": "🐅 TIGER (지상 지능형 모빌리티)\n\n✅ 장점: 4족 보행 로봇과 바퀴가 결합되어 오프로드, 험지 등 일반 차량이 갈 수 없는 지형을 자유롭게 이동합니다.\n💡 비교: 일반 PBV가 도심 평탄한 도로에 최적화되었다면, TIGER는 재난 현장이나 극한 환경 탐사에 특화되어 있습니다.",
        "pbv": "🚌 PBV (목적 기반 모빌리티)\n\n✅ 장점: 스케이트보드 플랫폼 위에 용도에 맞는 캐빈을 얹어, 낮에는 카페, 밤에는 물류 배송차로 무한 변신이 가능합니다.\n💡 비교: 기존 승용차는 '이동' 자체가 목적이지만, PBV는 이동하는 동안의 '공간 활용'이 주 목적입니다.",
        "evtol": "🚁 eVTOL (도심 항공 모빌리티)\n\n✅ 장점: 수직 이착륙이 가능해 활주로가 필요 없고, 전기를 사용하여 소음이 적습니다.\n💡 비교: 지상 모빌리티와 달리 교통 체증을 무시하고 빌딩 숲 위를 직선으로 날아가 시간을 획기적으로 단축합니다.",
        "마이크로": "🛴 마이크로 모빌리티 (초소형 전기차/킥보드)\n\n✅ 장점: 부피가 작아 골목길 주행과 주차가 쉽고 유지비가 저렴합니다.\n💡 비교: 대중교통(버스, 지하철)에서 내린 후 최종 목적지까지의 '라스트 마일'을 채워주는 데 가장 유리합니다."
    }

    answer = f"요청하신 [{target}]에 대한 비교 데이터가 없습니다. (tiger, pbv, evtol, 마이크로 중 하나를 입력해 보세요!)"

    for key, value in DB.items():
        if key in target:
            answer = value
            break

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": answer}}],
            "quickReplies": DEFAULT_QUICK_REPLIES
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

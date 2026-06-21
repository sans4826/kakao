from flask import Flask, request, jsonify
import random
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
from google import genai

app = Flask(__name__)


def kakao_text(text):
    return {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": text[:1000]
                }
            }]
        }
    }


@app.route("/", methods=["GET"])
def home():
    return "Server is running."


# 기존 테스트용
@app.route("/text", methods=["GET", "POST"])
def text_skill():
    return jsonify(kakao_text(str(random.randint(1, 10))))


@app.route("/image", methods=["GET", "POST"])
def image_skill():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleImage": {
                    "imageUrl": "https://t1.daumcdn.net/friends/prod/category/M001_friends_ryan2.jpg",
                    "altText": "hello I'm Ryan"
                }
            }]
        }
    }
    return jsonify(response)


# 1. 데이터 그대로 주고받기
@app.route("/echo", methods=["POST"])
def echo_skill():
    data = request.get_json(silent=True) or {}
    user_input = data.get("userRequest", {}).get("utterance", "입력값이 없습니다.")
    return jsonify(kakao_text(user_input))


# 3. 시간/발화/파라미터 확인
@app.route("/params-check", methods=["POST"])
def params_check():
    data = request.get_json(silent=True) or {}

    user_request = data.get("userRequest", {})
    action = data.get("action", {})
    params = action.get("params", {})

    a = user_request.get("timezone", "timezone 없음")
    b = user_request.get("utterance", "utterance 없음")
    c = params.get("파라미터", "파라미터 없음")
    d = params.get("파라미터2", "파라미터2 없음")

    text = f"{a} / {b} / {c} / {d}"
    return jsonify(kakao_text(text))


# 4. 파라미터 활용 구글 기사 데이터 가져오기
@app.route("/google-news", methods=["POST"])
def google_news():
    data = request.get_json(silent=True) or {}
    y = data.get("action", {}).get("params", {}).get("파라미터", "").strip()

    if not y:
        return jsonify(kakao_text("파라미터 값이 없습니다."))

    query = urllib.parse.quote(y)
    url = f"https://www.google.com/search?q={query}&tbm=nws"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # Google 뉴스 검색 결과에서 자주 보이는 제목 선택자들 시도
        items = soup.select(".n0jPhd") or soup.select(".mCBkyc") or soup.select(".DKV0Md")

        titles = []
        for item in items[:5]:
            title = item.get_text(strip=True)
            if title:
                titles.append(title)

        if titles:
            result = y + " 검색 결과:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
        else:
            result = f"{y} 검색 결과를 찾지 못했습니다."

    except Exception as e:
        result = f"구글 뉴스 조회 중 오류: {str(e)}"

    return jsonify(kakao_text(result))


# 5. 파라미터로 Gemini 연동하기
@app.route("/gemini-param", methods=["POST"])
def gemini_param():
    data = request.get_json(silent=True) or {}
    tt = data.get("action", {}).get("params", {}).get("파라미터", "").strip()

    if not tt:
        return jsonify(kakao_text("파라미터 값이 없습니다."))

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify(kakao_text("GEMINI_API_KEY 환경변수가 설정되지 않았습니다."))

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=tt
        )
        result_text = response.text if response.text else "응답이 비어 있습니다."
    except Exception as e:
        result_text = f"Gemini 호출 중 오류: {str(e)}"

    return jsonify(kakao_text(result_text))


# =====================================================================
# 6. 파라미터 활용: 모빌리티 장단점 및 특징 비교 스킬 (새로 추가된 기능)
# =====================================================================
@app.route('/api/mobility-compare', methods=['POST'])
def mobility_compare():
    data = request.get_json(silent=True) or {}
    
    # 1. 카카오 빌더에서 뽑아낸 '파라미터' 가져오기
    params = data.get('action', {}).get('params', {})
    
    # 파라미터 이름표를 'mobility_name'으로 설정했다고 가정
    target = params.get('mobility_name', '').strip().lower() 

    # 2. 모빌리티 장단점/비교 DB
    DB = {
        "tiger": "🐅 TIGER (지상 지능형 모빌리티)\n\n✅ 장점: 4족 보행 로봇과 바퀴가 결합되어 오프로드, 험지, 계단 등 일반 차량이 갈 수 없는 지형을 자유롭게 이동합니다.\n💡 비교 포인트: 일반 PBV가 평탄한 도로(도심)에 최적화되었다면, TIGER는 재난 현장이나 달 표면 같은 극한 환경 탐사에 특화되어 있습니다.",
        
        "pbv": "🚌 PBV (목적 기반 모빌리티)\n\n✅ 장점: 스케이트보드 플랫폼 위에 용도에 맞는 캐빈(껍데기)을 레고처럼 얹어, 낮에는 카페, 밤에는 물류 배송차로 무한 변신이 가능합니다.\n💡 비교 포인트: 기존 승용차는 '이동' 자체가 목적이지만, PBV는 이동하는 동안의 '공간 활용(휴식, 업무, 상업)'이 주 목적입니다.",
        
        "evtol": "🚁 eVTOL (도심 항공 모빌리티)\n\n✅ 장점: 수직 이착륙이 가능해 활주로가 필요 없고, 전기를 사용하여 헬리콥터보다 소음이 적고 친환경적입니다.\n💡 비교 포인트: 지상의 교통 체증을 완전히 무시하고 빌딩 숲 위를 직선으로 날아가기 때문에, 다른 지상 모빌리티에 비해 도심 이동 시간을 획기적으로 단축합니다.",
        
        "마이크로": "🛴 마이크로 모빌리티 (초소형 전기차/킥보드)\n\n✅ 장점: 부피가 작아 골목길 주행과 주차가 매우 쉽고 유지비가 저렴합니다.\n💡 비교 포인트: 대중교통(버스, 지하철)에서 내린 후 최종 목적지까지의 짧은 거리인 '라스트 마일(Last Mile)'을 채워주는 데 가장 유리한 수단입니다."
    }

    # 3. 파라미터와 DB 매칭
    answer = f"요청하신 [{target}]에 대한 비교 데이터가 아직 입력되지 않았습니다. (tiger, pbv, evtol, 마이크로 중 하나를 입력해 보세요!)"

    for key, value in DB.items():
        if key in target:
            answer = value
            break

    # 기존에 정의된 kakao_text 함수를 활용하여 깔끔하게 응답 반환
    return jsonify(kakao_text(answer))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

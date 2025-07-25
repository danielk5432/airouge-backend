import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# API 키를 설정합니다.
try:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    # .env 파일에 키가 없을 경우를 대비한 에러 처리
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")


def get_ai_explanation():
    """
    Gemini API를 호출하여 간단한 설명을 받아오는 함수.
    """
    try:
        # model.generate_content()를 사용하여 콘텐츠를 생성합니다.
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents="Explain how AI works in a few words"
        )
        return response.text
    except Exception as e:
        # API 호출 중 어떤 종류의 오류든 발생하면 로그를 남기고 None을 반환합니다.
        # 실제 서비스에서는 print 대신 logging 라이브러리를 사용하는 것이 좋습니다.
        print(f"Gemini API 호출 중 오류 발생: {e}")
        return None
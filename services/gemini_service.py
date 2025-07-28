import os
import uuid
import json
from google import genai
from dotenv import load_dotenv
from google.genai import types
from PIL import Image
from io import BytesIO
import base64


# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

try:
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    
    # 공식 문서의 genai.Client 방식을 사용합니다.
    # 변수 이름을 model_client로 하여 역할을 명확히 합니다.
    client = genai.Client(api_key=API_KEY)
    print("Gemini API 클라이언트가 성공적으로 초기화되었습니다.")

except Exception as e:
    print(f"Gemini API 클라이언트 초기화 실패: {e}")
    client = None
    

def get_llm_response(input_text: str):
    """
    미리 생성된 API 클라이언트를 사용하여 Gemini API를 호출합니다.
    """
    # 클라이언트가 성공적으로 초기화되었는지 확인합니다.
    if client is None:
        print("API 클라이언트가 초기화되지 않아 요청을 처리할 수 없습니다.")
        return None

    try:
        # 요청마다 클라이언트를 새로 만드는 대신, 이미 만들어진 객체를 재사용합니다.
        response = client.models.generate_content(
            model="models/gemini-1.5-flash", 
            contents=input_text
        )
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return cleaned_text
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        return None

def create_character(user_description: str):
    """
    사용자 설명을 기반으로 캐릭터 생성 프롬프트를 만들고 LLM을 호출하는 메인 서비스 함수.
    """
    # 이전에 작성한 시스템 프롬프트를 여기에 붙여넣습니다.
    # 이 프롬프트는 LLM에게 역할을 부여하고 JSON 구조를 지시합니다.
    # prompt.txt 파일 생성
    with open('prompt.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()
        

    # 최종적으로 LLM에 보낼 전체 프롬프트
    full_prompt = f"{system_prompt}\n\n### [사용자 입력]\n{user_description}"

    # LLM 호출
    llm_response_str = get_llm_response(full_prompt)

    if llm_response_str is None:
        return None

    # LLM이 반환한 문자열(JSON 형식)을 실제 Python 딕셔너리로 변환
    try:
        character_data = json.loads(llm_response_str)
        
        # 캐릭터 설명이나 이름을 바탕으로 이미지 생성 프롬프트를 만듭니다.
        image_base_prompt = f"{character_data['character_name']}, {character_data['description']}"
        
        # 이미지 '세트' 생성 서비스를 호출합니다.
        image_url = generate_character_image(image_base_prompt)
        
        # 생성된 이미지 URL 딕셔너리를 캐릭터 데이터에 추가합니다.
        # 'image_url' 대신 'image_urls' 라는 새로운 필드를 사용합니다.
        character_data['image_url'] = image_url

        return character_data
    except Exception as e:
        print(f"JSON 파싱 또는 이미지 생성 중 오류: {e}")
        return None

def generate_character_image(base_prompt: str) -> str | None:
    """
    Gemini API를 사용하여 캐릭터 이미지를 생성하고,
    로컬에 저장한 뒤 웹 경로를 반환합니다.
    """
    try:
        print(f"Gemini API에 이미지 생성 요청: '{base_prompt}'")

        # 이미지 생성을 위한 상세 프롬프트 구성
        full_prompt = f"A full body character portrait of a {base_prompt}, fantasy art style, vibrant colors, detailed, simple background, 1:1 aspect ratio"

        # Gemini 이미지 생성 모델 호출
        response = client.models.generate_content(
            model='gemini-2.0-flash-preview-image-generation',
            contents=(full_prompt),
            config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
            )
        )

        # 응답에서 이미지 데이터만 추출하여 저장
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # 1. 고유한 파일 이름 생성 (예: image_abc-123.png)
                filename = f"image_{uuid.uuid4()}.png"
                
                # 2. 이미지를 저장할 폴더 경로 설정 (폴더가 없으면 생성)
                save_dir = "static/images"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, filename)

                # 3. 이미지 데이터를 파일로 저장
                image = Image.open(BytesIO(part.inline_data.data))
                image.save(save_path)
                
                print(f"이미지 생성 성공, 저장 경로: {save_path}")
                
                # 4. 웹에서 접근 가능한 URL 경로를 반환합니다.
                # 예: "/static/images/image_abc-123.png"
                return f"/{save_path}"

        # 루프가 끝날 때까지 이미지를 찾지 못했다면
        print("API 응답에서 이미지를 찾지 못했습니다.")
        return None

    except Exception as e:
        print(f"Gemini 이미지 생성/저장 중 오류 발생: {e}")
        return None
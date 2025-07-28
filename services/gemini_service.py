# gemini_service

import os
import uuid
import json
from google import genai
from dotenv import load_dotenv
from google.genai import types
from PIL import Image, ImageDraw
from io import BytesIO


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
            model="models/gemini-2.5-flash-lite", 
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

        character_data['id'] = str(uuid.uuid4())
        
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
        full_prompt = f"A full body character portrait of a {base_prompt}, fantasy art style, detailed, vibrant colors, white background, 1:1 aspect ratio"

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
                original_image = Image.open(BytesIO(part.inline_data.data))

                # --- 1. Flood Fill을 이용한 배경 제거 (가장 먼저 실행) ---
                # 처음부터 RGBA 모드로 변환하여 투명도(Alpha) 채널을 다룹니다.
                img_bg_removed = original_image.convert("RGBA")
                # 이미지의 네 모서리에서 Flood Fill을 실행하여 배경을 확실히 제거합니다.
                ImageDraw.floodfill(img_bg_removed, xy=(0, 0), value=(0, 0, 0, 0), thresh=10)
                ImageDraw.floodfill(img_bg_removed, xy=(img_bg_removed.width - 1, 0), value=(0, 0, 0, 0), thresh=10)
                ImageDraw.floodfill(img_bg_removed, xy=(0, img_bg_removed.height - 1), value=(0, 0, 0, 0), thresh=10)
                ImageDraw.floodfill(img_bg_removed, xy=(img_bg_removed.width - 1, img_bg_removed.height - 1), value=(0, 0, 0, 0), thresh=10)
                # thresh=40 : 완전한 흰색이 아니더라도 비슷한 밝은 색은 함께 제거합니다.
                # ----------------------------------------------------

                # --- 2. 투명 여백을 추가하여 1:1 비율의 정사각형으로 만들기 ---
                width, height = img_bg_removed.size
                longer_side = max(width, height)
                # 배경을 (0,0,0,0) 즉, '투명'으로 설정한 새 캔버스를 만듭니다.
                squared_image = Image.new("RGBA", (longer_side, longer_side), (0, 0, 0, 0))
                paste_position = (int((longer_side - width) / 2), int((longer_side - height) / 2))
                # 배경이 제거된 이미지를 투명 캔버스 중앙에 붙여넣습니다.
                # 세 번째 인자로 자기 자신(mask)을 주면 투명도가 올바르게 유지됩니다.
                squared_image.paste(img_bg_removed, paste_position, img_bg_removed)
                # ----------------------------------------------------

                # --- 3. 64x64 해상도로 작게 픽셀화 ---
                small_pixelated_image = squared_image.resize((64, 64), Image.Resampling.NEAREST)
                # ----------------------------------------------------

                # --- 4. 최종 결과물로 256x256 크기 확대 ---
                # NEAREST 필터를 사용해야 픽셀 느낌이 깨지지 않고 선명하게 확대됩니다.
                final_image = small_pixelated_image.resize((256, 256), Image.Resampling.NEAREST)
                # ----------------------------------------------------

                # 고유한 파일 이름 생성
                filename = f"image_{uuid.uuid4()}.png"
                save_dir = "static/images"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, filename)

                # 최종적으로 처리된 이미지를 저장합니다.
                final_image.save(save_path)
                
                print(f"이미지 처리 및 저장 완료: {save_path}")
                
                # 웹에서 접근 가능한 URL 경로를 반환합니다.
                return f"/{save_path}"

        # 루프가 끝날 때까지 이미지를 찾지 못했다면
        print("API 응답에서 이미지를 찾지 못했습니다.")
        return None

    except Exception as e:
        print(f"Gemini 이미지 생성/저장 중 오류 발생: {e}")
        return None
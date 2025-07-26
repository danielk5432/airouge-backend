import os
import json
from google import genai
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# API 키를 환경 변수에서 가져옵니다.
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")

def get_llm_response(input_text: str):
    """
    Gemini API를 호출하여 텍스트 응답을 받아오는 함수.
    공식 문서의 genai.Client 방식을 사용합니다.
    """
    try:
        # 제공해주신 문서의 예시에 따라 Client 객체를 생성합니다.
        client = genai.Client(api_key=API_KEY)
        
        # client.generate_content를 사용하여 콘텐츠를 생성합니다.
        # 이 방식을 사용할 때는 모델 이름에 'models/' 접두사가 필요할 수 있습니다.
        response = client.models.generate_content(
            model="models/gemini-1.5-flash", 
            contents=input_text
        )
        
        # LLM 응답에서 불필요한 마크다운 문법(```json ... ```)을 제거합니다.
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
    system_prompt = """
    당신은 게임 캐릭터 데이터를 생성하는 전문 AI입니다. 사용자가 입력한 설명을 바탕으로, 아래의 [규칙]과 [JSON 출력 형식]을 반드시 준수하여 캐릭터의 데이터를 JSON 객체로만 생성해야 합니다. 다른 부가적인 설명이나 마크다운 문법(```json)은 절대 덧붙이지 마십시오.

    [규칙]
    1. 능력치 (Stats):

    기본 총합 400에 50~150 사이의 랜덤 보너스 값을 더하여 최종 총합을 결정하십시오.

    결정된 최종 총합을 6가지 스탯(hp, atk, def, sp_atk, sp_def, speed)에 분배하십시오.

    캐릭터 설명에 '빠르다'가 있으면 speed를, '단단하다'가 있으면 def와 sp_def를, '강력한 마법'이 있으면 sp_atk를, '근육질'이나 '육탄전'이 있으면 atk를 높게 책정하여 분배하십시오.

    2. 타입 (Types):

    캐릭터의 핵심 컨셉을 나타내는 character_type을 창의적으로 1개 만드십시오.

    각 스킬의 컨셉을 나타내는 skill_type을 스킬마다 창의적으로 1개씩 만드십시오.

    3. 스킬 (Skills):

    캐릭터 설명에 맞춰 독창적인 스킬 4개를 생성합니다.

    각 스킬은 아래의 '모듈형 스킬 시스템' 규칙을 따라야 합니다.

    모듈형 스킬 시스템 규칙:
    visual_effect_type: 이 스킬의 시각적 연출을 아래 [시각 타입 목록] 중에서 반드시 하나만 선택해야 합니다.

    parameters: 선택한 visual_effect_type에 맞는 파라미터들을 아래 **[파라미터 옵션]**에 명시된 범위와 목록 내에서만 설정해야 합니다.

    color: 모든 color 필드는 반드시 유효한 헥스 코드(Hex Code) 문자열 (예: "#FF5733")이어야 합니다.

    [시각 타입 목록]

    Shake

    Projectile

    Laser

    [파라미터 옵션]

    visual_effect_type이 "Shake"일 경우:

    shake_effect 객체를 생성하고, 그 안에 particle_color 필드를 설정하십시오.

    visual_effect_type이 "Projectile"일 경우:

    projectile_effect 객체를 생성하고, 그 안의 필드를 아래 규칙에 따라 설정하십시오.

    shape: 반드시 ["구체", "막대기"] 중에서 하나를 선택하십시오.

    count: 반드시 1에서 5 사이의 정수를 선택하십시오.

    color: 헥스 코드로 설정하십시오.

    visual_effect_type이 "Laser"일 경우:

    laser_effect 객체를 생성하고, 그 안의 필드를 아래 규칙에 따라 설정하십시오.

    origin: 반드시 ["Player", "TopToBottom", "BottomToTop"] 중에서 하나를 선택하십시오.

    thickness: 반드시 1에서 3 사이의 정수를 선택하십시오.

    color: 헥스 코드로 설정하십시오.

    [JSON 출력 형식]
    아래는 반드시 지켜야 할 최종 JSON 구조의 예시입니다.

    {
    "character_name": "캐릭터 이름",
    "description": "LLM이 생성한 한 줄짜리 캐릭터 컨셉 요약",
    "image_url": "이미지 URL은 비워두거나 null로 설정",
    "stats": {
        "hp": 120,
        "atk": 70,
        "def": 90,
        "sp_atk": 110,
        "sp_def": 80,
        "speed": 60
    },
    "character_type": "창조된 캐릭터 타입",
    "skills": [
        {
        "skill_name": "독창적인 스킬 이름 1",
        "description": "LLM이 생성한 스킬 설명",
        "base_power": 85,
        "damage_type": "특수",
        "skill_type": "창조된 스킬 타입 1",
        "visual_effect_type": "Projectile",
        "shake_effect": null,
        "projectile_effect": {
            "shape": "구체",
            "count": 3,
            "color": "#FFD700"
        },
        "laser_effect": null
        },
        {
        "skill_name": "독창적인 스킬 이름 2",
        "description": "LLM이 생성한 스킬 설명",
        "base_power": 110,
        "damage_type": "특수",
        "skill_type": "창조된 스킬 타입 2",
        "visual_effect_type": "Laser",
        "shake_effect": null,
        "projectile_effect": null,
        "laser_effect": {
            "origin": "TopToBottom",
            "thickness": 3,
            "color": "#8A2BE2"
        }
        }
    ]
    }

    ```
    """

    # 최종적으로 LLM에 보낼 전체 프롬프트
    full_prompt = f"{system_prompt}\n\n### [사용자 입력]\n{user_description}"

    # LLM 호출
    llm_response_str = get_llm_response(full_prompt)

    if llm_response_str is None:
        return None

    # LLM이 반환한 문자열(JSON 형식)을 실제 Python 딕셔너리로 변환
    try:
        character_data = json.loads(llm_response_str)
        return character_data
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"파싱 실패한 문자열: {llm_response_str}")
        return None

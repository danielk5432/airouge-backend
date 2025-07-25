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
    당신은 게임 캐릭터 데이터를 생성하는 전문 AI입니다. 사용자가 입력한 설명을 바탕으로, 아래의 [규칙]과 [JSON 출력 형식]을 반드시 준수하여 캐릭터의 데이터를 JSON 객체로만 생성해야 합니다. 다른 부가적인 설명은 절대 덧붙이지 마십시오.

    ### [규칙]
    1. 능력치 (Stats):
       - `hp`, `atk`, `def`, `sp_atk`, `sp_def`, `speed` 6가지 능력치를 배분합니다.
       - 각 능력치는 최소 30, 최대 150 사이의 값을 가집니다.
       - 6가지 능력치의 총합은 반드시 500을 넘을 수 없습니다.
       - 캐릭터 설명에 '빠르다'가 있으면 `speed`를, '단단하다'가 있으면 `def`와 `sp_def`를, '강력한 마법'이 있으면 `sp_atk`를, '근육질'이나 '육탄전'이 있으면 `atk`를 높게 책정하십시오.
    2. 타입 (Types):
       - 캐릭터의 핵심 컨셉을 나타내는 타입을 1~2개 창의적으로 만드십시오.
    3. 스킬 (Skills):
       - 캐릭터 설명에 맞춰 독창적인 스킬 4개를 생성합니다.
       - 각 스킬은 아래의 '모듈형 스킬 시스템' 규칙을 따라야 합니다.

    #### 모듈형 스킬 시스템 규칙:
    - `damage_type`: 물리 공격 기반이면 "물리", 마법 공격 기반이면 "특수"로 지정하십시오.
    - `visual_type`: ["Projectile", "Laser", "SelfAura", "TargetImpact"] 중에서 선택하십시오.
    - `parameters`: 선택한 `visual_type`에 맞는 파라미터들을 조합하십시오.
      - Projectile: shape(["구체", "화살", "파편"]), count(1-5), speed(["느림", "보통", "빠름"])
      - Laser: origin(["눈", "손"]), thickness(["얇음", "두꺼움"])
      - SelfAura: duration(["짧게", "길게"]), pattern(["파동", "소용돌이"])
      - TargetImpact: effect_shape(["폭발", "베기", "낙뢰"])

    ### [JSON 출력 형식]
    ```json
    {
      "character_name": "캐릭터 이름",
      "description": "LLM이 생성한 한 줄짜리 캐릭터 컨셉 요약",
      "stats": { "hp": 100, "atk": 50, "def": 80, "sp_atk": 120, "sp_def": 80, "speed": 70 },
      "types": ["창조된 타입 1", "창조된 타입 2"],
      "skills": [
        { "skill_name": "스킬1", "description": "...", "base_power": 85, "damage_type": "특수", "visual_type": "Projectile", "parameters": { "shape": "에너지탄", "count": 3, "speed": "빠름", "color": "#FFD700" } }
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

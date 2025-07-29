# main.py

from math import floor
from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles # StaticFiles 임포트
import uvicorn
from pydantic import BaseModel
from services.gemini_service import *
from services.admin_service import *
import json
import os
from services.gemini_service import create_character
from security.admin_auth import get_current_admin_user
from models import *
import secrets

app = FastAPI()

# CORS 미들웨어 설정
# 웹 브라우저에서 실행되는 test.html이 API 서버에 요청을 보낼 수 있도록 허용합니다.
origins = [
    "*", # 개발 및 테스트를 위해 모든 출처를 허용합니다.
         # 실제 서비스에서는 프론트엔드 도메인 주소만 허용해야 합니다.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메소드 허용
    allow_headers=["*"], # 모든 HTTP 헤더 허용
)

CHARACTER_FILE = os.getenv("CHARACTER_FILE")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/api/v1/characters")
def handle_create_character(request: CharacterCreateRequest):
    character_data = create_character(request.user_prompt)
    if character_data is None:
        raise HTTPException(status_code=500, detail="AI 캐릭터 생성에 실패했습니다. 서버 로그를 확인해주세요.")
    return character_data

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/admin")
def get_admin_page(username: str = Depends(get_current_admin_user)):
    return FileResponse("admin.html")
    
@app.get("/test")
def get_test_html(username: str = Depends(get_current_admin_user)):
    return FileResponse("test.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


# --- admin API endpoint ---

@app.get("/api/admin/characters")
def get_characters_list(username: str = Depends(get_current_admin_user)):
    """저장된 모든 캐릭터 목록을 반환합니다."""
    return get_all_characters_from_file()

@app.post("/api/admin/characters")
def handle_create_character_and_save(request: CharacterCreateRequest, username: str = Depends(get_current_admin_user)):
    """캐릭터를 생성하고 파일에 저장합니다."""
    # 사용자님의 기존 AI 로직 호출 (수정하지 않음)
    character_data = create_character(request.user_prompt)
    if character_data is None:
        raise HTTPException(status_code=500, detail="AI 캐릭터 생성에 실패했습니다.")
    
    # 생성된 데이터에 ID를 부여하고 저장
    saved_character = save_character_to_file(character_data)
    return saved_character

@app.delete("/api/admin/characters/{character_id}")
def handle_delete_character(character_id: str, username: str = Depends(get_current_admin_user)):
    """ID로 특정 캐릭터를 삭제합니다."""
    success = delete_character_from_file(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="해당 ID의 캐릭터를 찾을 수 없습니다.")
    return {"message": "캐릭터가 성공적으로 삭제되었습니다."}


@app.get("/run-test")
def get_run_test_page():
    return FileResponse("run_test.html")

# --- 인메모리 DB: 진행 중인 게임 저장 ---
runs_db = {} # { "run_id": { "status": "calculating" | "completed", "data": {...} } }
# --- 신규 게임 API 엔드포인트 ---

@app.post("/api/runs")
def handle_create_run(request: RunCreateRequest, background_tasks: BackgroundTasks):
    """
    새로운 게임(Run)을 시작합니다. 적 목록을 즉시 반환하고,
    상성표 계산은 백그라운드에서 순차적으로 처리합니다.
    """
    run_id = f"run_{uuid.uuid4()}"
    
    all_enemies_pool = get_all_characters_from_file()
    if not all_enemies_pool or len(all_enemies_pool) < 9:
        raise HTTPException(status_code=500, detail="적이 9명 미만이라 게임을 시작할 수 없습니다. admin 페이지에서 캐릭터를 생성해주세요.")
    
    import random
    enemies = random.sample(all_enemies_pool, 9)
    player_characters_dict = [char.dict(by_alias=True) for char in request.player_characters]

    # Run 데이터 초기 상태로 저장
    runs_db[run_id] = {
        "data": {
            "player_characters": player_characters_dict,
            "enemies": enemies,
            "type_charts": {} # 비어있는 딕셔너리로 시작
        }
    }

    # 백그라운드에서 전체 상성표 계산 작업 시작
    background_tasks.add_task(calculate_all_floor_charts_task, run_id, player_characters_dict, enemies)
    
    # 적 목록과 run_id를 즉시 반환
    print(f"[{run_id}] 게임 시작. 적 목록 즉시 반환. 상성표는 백그라운드에서 계산 중.")
    return {"run_id": run_id, "enemies": enemies}

@app.get("/api/runs/{run_id}/floors/{floor_number}")
def get_floor_data(run_id: str, floor_number: int):
    """
    특정 층의 정보와 상성표를 반환합니다.
    해당 층의 상성표가 아직 계산 중이면 'calculating' 상태를 반환합니다.
    """
    run_session = runs_db.get(run_id)
    if not run_session:
        raise HTTPException(status_code=404, detail="해당 Run을 찾을 수 없습니다.")
    
    # --- (수정된 핵심 로직) ---
    # 1. 층 번호를 문자열 키로 변환합니다.
    floor_key = str(floor_number)
    
    # 2. 해당 층의 상성표가 'type_charts' 딕셔너리 안에 있는지 직접 확인합니다.
    if floor_key not in run_session["data"]["type_charts"]:
        return {"status": "calculating"} # 아직 계산 중
    # --------------------------------

    run_data = run_session["data"]
    if not (1 <= floor_number <= 9):
        raise HTTPException(status_code=400, detail="층 번호는 1에서 9 사이여야 합니다.")
        
    enemy_data = run_data["enemies"][floor_number - 1]
    # 해당 층의 상성표만 정확히 가져옵니다.
    type_chart = run_data["type_charts"][floor_key]

    return {"status": "completed", "enemy": enemy_data, "type_chart": type_chart}

@app.post("/api/runs/{run_id}/complete")
def handle_game_complete(run_id: str, request: GameCompleteRequest):
    """
    게임 클리어를 처리하고, 우승한 캐릭터 3명을 '적 풀'에 저장한 뒤,
    진행 중인 Run 데이터를 삭제합니다.
    """
    # 1. 우승 캐릭터들을 characters.json 파일에 저장합니다.
    winning_characters_dict = [char.dict() for char in request.winning_characters]
    save_characters_to_file(winning_characters_dict)

    # 2. 진행이 끝난 Run 데이터를 메모리에서 삭제합니다.
    if run_id in runs_db:
        del runs_db[run_id]
        print(f"[{run_id}] Run completed and removed from memory.")
        return {"message": "Congratulations! Run complete and characters saved to Hall of Fame."}
    else:
        # Run 데이터가 이미 없더라도 캐릭터는 저장되었으므로 성공으로 간주합니다.
        print(f"[{run_id}] Run not found in memory, but characters were saved.")
        return {"message": "Run not found, but characters were saved to Hall of Fame."}
    

# --- 여러 캐릭터를 파일에 저장하는 함수 ---
def save_characters_to_file(characters_data: List[dict]):
    """우승한 캐릭터 리스트에 '새로운 ID'를 부여하여 JSON 파일에 추가합니다."""
    all_chars = get_all_characters_from_file()
    
    # 새로 저장할 캐릭터들의 ID를 모두 새로 부여합니다.
    for char in characters_data:
        char['id'] = str(uuid.uuid4())
        
    all_chars.extend(characters_data)
    
    with open(CHARACTER_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chars, f, ensure_ascii=False, indent=2)
    return True

# --- 백그라운드 작업 함수 ---
def calculate_and_save_type_chart_task(run_id: str, player_characters: List[dict], enemies: List[dict]):
    """
    (백그라운드에서 실행됨) LLM으로 상성표를 계산하고,
    빠른 조회를 위해 딕셔너리 형태로 변환하여 DB에 저장합니다.
    """
    print(f"[{run_id}] 백그라운드 상성표 계산 시작...")
    # 1. 상성 계산을 위한 모든 고유 타입 수집
    player_skill_types = {skill['skill_type'] for char in player_characters for skill in char['skills']}
    enemy_character_types = {enemy['character_type'] for enemy in enemies}
    enemy_skill_types = {skill['skill_type'] for enemy in enemies for skill in enemy['skills']}
    player_character_types = {char['character_type'] for char in player_characters}

    # 2. LLM으로 상성표 계산 (결과는 플랫 리스트 형태)
    flat_type_chart = calculate_type_chart(
        list(player_skill_types), list(enemy_character_types),
        list(enemy_skill_types), list(player_character_types)
    )

    # 3. 계산 완료 후 Run 데이터 업데이트
    if run_id in runs_db:
        if flat_type_chart:
            # --- (수정) 플랫 리스트를 중첩 딕셔너리로 변환하는 로직 ---
            nested_chart = { "player_vs_enemy": {}, "enemy_vs_player": {} }
            for item in flat_type_chart.get('player_vs_enemy', []):
                attacker = item['attacker']
                defender = item['defender']
                if attacker not in nested_chart['player_vs_enemy']:
                    nested_chart['player_vs_enemy'][attacker] = {}
                nested_chart['player_vs_enemy'][attacker][defender] = item['multiplier']
            
            for item in flat_type_chart.get('enemy_vs_player', []):
                attacker = item['attacker']
                defender = item['defender']
                if attacker not in nested_chart['enemy_vs_player']:
                    nested_chart['enemy_vs_player'][attacker] = {}
                nested_chart['enemy_vs_player'][attacker][defender] = item['multiplier']
            # ----------------------------------------------------
            
            runs_db[run_id]["data"]["type_chart"] = nested_chart
            runs_db[run_id]["status"] = "completed"
            print(f"[{run_id}] 상성표 계산 완료 및 딕셔너리 변환 성공.")
        else:
            runs_db[run_id]["status"] = "failed"
            print(f"[{run_id}] 상성표 계산 실패.")

def calculate_all_floor_charts_task(run_id: str, player_characters: List[dict], enemies: List[dict]):
    """
    (백그라운드에서 실행됨) 1층부터 9층까지의 상성표를 순차적으로 계산합니다.
    """
    print(f"[{run_id}] 백그라운드 작업 시작: 1-9층 상성표 순차 계산")
    for i in range(9): # 1층부터 9층까지 (인덱스 0~8)
        floor_number = i + 1
        enemy = enemies[i]
        
        # 이 층에 필요한 타입만 수집
        player_skill_types = {skill['skill_type'] for char in player_characters for skill in char['skills']}
        enemy_character_types = {enemy['character_type']}
        enemy_skill_types = {skill['skill_type'] for skill in enemy['skills']}
        player_character_types = {char['character_type'] for char in player_characters}

        # LLM으로 상성표 계산
        type_chart = calculate_type_chart(
            list(player_skill_types), list(enemy_character_types),
            list(enemy_skill_types), list(player_character_types)
        )

        # 계산 완료 후 Run 데이터에 해당 층의 상성표 추가
        if run_id in runs_db and type_chart:
            # 딕셔너리로 변환하여 저장
            nested_chart = { "player_vs_enemy": {}, "enemy_vs_player": {} }
            for item in type_chart.get('player_vs_enemy', []):
                attacker, defender, multiplier = item['attacker'], item['defender'], item['multiplier']
                if attacker not in nested_chart['player_vs_enemy']: nested_chart['player_vs_enemy'][attacker] = {}
                nested_chart['player_vs_enemy'][attacker][defender] = multiplier
            
            for item in type_chart.get('enemy_vs_player', []):
                attacker, defender, multiplier = item['attacker'], item['defender'], item['multiplier']
                if attacker not in nested_chart['enemy_vs_player']: nested_chart['enemy_vs_player'][attacker] = {}
                nested_chart['enemy_vs_player'][attacker][defender] = multiplier

            runs_db[run_id]["data"]["type_charts"][str(floor_number)] = nested_chart
            print(f"[{run_id}] {floor_number}층 상성표 계산 완료 및 저장 성공.")
        else:
            print(f"[{run_id}] {floor_number}층 상성표 계산 실패. 백그라운드 작업을 중단합니다.")
            break # 실패 시 중단
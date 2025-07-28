# main.py

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles # StaticFiles 임포트
import uvicorn
from pydantic import BaseModel
from services.gemini_service import create_character
import json
import os
from services.gemini_service import create_character
from security.admin_auth import get_current_admin_user
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

app.mount("/static", StaticFiles(directory="static"), name="static")

class CharacterCreateRequest(BaseModel):
    user_prompt: str

@app.post("/api/v1/characters")
def handle_create_character(request: CharacterCreateRequest):
    character_data = create_character(request.user_prompt)
    if character_data is None:
        raise HTTPException(status_code=500, detail="AI 캐릭터 생성에 실패했습니다. 서버 로그를 확인해주세요.")
    return character_data

@app.get("/")
def read_root():
    return {"message": "AI-Rouge Backend is running!"}

@app.get("/admin")
def get_admin_page(username: str = Depends(get_current_admin_user)):
    """관리자 페이지를 반환합니다. (관리자만 접근 가능)"""
    return FileResponse("admin.html")
    
@app.get("/test")
def get_test_html(username: str = Depends(get_current_admin_user)):
    return FileResponse("test.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


# --- 디버그용 API 엔드포인트 ---

@app.get("/api/characters")
def get_characters_list(username: str = Depends(get_current_admin_user)):
    """저장된 모든 캐릭터 목록을 반환합니다."""
    return get_all_characters_from_file()

@app.post("/api/characters")
def handle_create_character_and_save(request: CharacterCreateRequest, username: str = Depends(get_current_admin_user)):
    """캐릭터를 생성하고 파일에 저장합니다."""
    # 사용자님의 기존 AI 로직 호출 (수정하지 않음)
    character_data = create_character(request.user_prompt)
    if character_data is None:
        raise HTTPException(status_code=500, detail="AI 캐릭터 생성에 실패했습니다.")
    
    # 생성된 데이터에 ID를 부여하고 저장
    saved_character = save_character_to_file(character_data)
    return saved_character

@app.delete("/api/characters/{character_id}")
def handle_delete_character(character_id: str, username: str = Depends(get_current_admin_user)):
    """ID로 특정 캐릭터를 삭제합니다."""
    success = delete_character_from_file(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="해당 ID의 캐릭터를 찾을 수 없습니다.")
    return {"message": "캐릭터가 성공적으로 삭제되었습니다."}


# --- 파일 DB 로직 (main.py에 직접 추가) ---
CHARACTER_FILE = "static/characters.json"

def get_all_characters_from_file():
    """characters.json 파일에서 모든 캐릭터 목록을 불러옵니다."""
    try:
        with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] # 파일이 없거나 비어있으면 빈 리스트 반환

def save_character_to_file(character_data: dict):
    """새로운 캐릭터 하나를 파일에 추가합니다."""
    characters = get_all_characters_from_file()
    characters.append(character_data)
    with open(CHARACTER_FILE, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    return character_data

def delete_character_from_file(character_id: str):
    """ID를 기준으로 캐릭터를 삭제하고, 연관된 이미지 파일도 삭제합니다."""
    characters = get_all_characters_from_file()
    
    char_to_delete = None
    # 삭제할 캐릭터를 찾습니다.
    for char in characters:
        if char.get('id') == character_id:
            char_to_delete = char
            break
    
    # 캐릭터를 찾지 못했다면, False를 반환합니다.
    if not char_to_delete:
        return False

    # --- 이미지 파일 삭제 로직 추가 ---
    image_url = char_to_delete.get('image_url')
    if image_url:
        # URL 경로 (예: /static/images/...)를 실제 파일 시스템 경로 (예: static/images/...)로 변환합니다.
        # lstrip('/')은 맨 앞의 '/'만 안전하게 제거합니다.
        image_path = image_url.lstrip('/')
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                print(f"이미지 파일 삭제 성공: {image_path}")
            except OSError as e:
                print(f"이미지 파일 삭제 실패: {e}")
        else:
            print(f"삭제할 이미지 파일을 찾을 수 없음: {image_path}")
    # --------------------------------

    # 캐릭터 데이터 리스트에서 해당 캐릭터를 제외합니다.
    updated_characters = [char for char in characters if char.get('id') != character_id]
    
    # 업데이트된 리스트를 다시 JSON 파일에 씁니다.
    with open(CHARACTER_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_characters, f, ensure_ascii=False, indent=2)
        
    return True
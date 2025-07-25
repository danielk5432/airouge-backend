from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from pydantic import BaseModel
from services.gemini_service import create_character

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

    
@app.get("/test.html")
def get_test_html():
    return FileResponse("test.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


# main.py

from fastapi import FastAPI
import uvicorn

# FastAPI 앱 인스턴스 생성
app = FastAPI()

# 서버가 살아있는지 확인하는 기본 API (GET /)
@app.get("/")
def read_root():
    return {"Hello": "Rouge!"}

# 로컬에서 개발할 때 터미널에서 `python main.py`로 실행하기 위한 부분
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
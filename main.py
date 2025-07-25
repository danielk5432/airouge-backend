from fastapi import FastAPI, HTTPException
import uvicorn
from services.gemini_service import get_ai_explanation

app = FastAPI()

@app.get("/")
def read_root():
    """
    기본 경로 API. Gemini 서비스 함수를 호출하고 결과를 반환합니다.
    """
    # 분리된 서비스 함수를 호출합니다.
    explanation = get_ai_explanation()

    # 서비스 함수가 오류로 인해 None을 반환했을 경우,
    # 클라이언트에게 500 에러와 함께 명확한 메시지를 전달합니다.
    if explanation is None:
        raise HTTPException(status_code=500, detail="AI 응답을 생성하는 데 실패했습니다.")

    # 성공 시, JSON 형식으로 응답합니다.
    return {"ai_explanation": explanation}

if __name__ == "__main__":
    # uvicorn.run의 reload=True 옵션은 개발 중에만 사용하는 것이 좋습니다.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

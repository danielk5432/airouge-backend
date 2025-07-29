# 🐍 security/admin_auth.py (수정된 파일)

import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBasic()

def get_current_admin_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    HTTP 기본 인증을 통해 관리자 자격 증명을 확인하는 의존성 함수.
    """
    # --- (신규) 디버깅을 위해 브라우저가 보낸 값을 직접 출력합니다. ---
    print(f"브라우저가 보낸 Username: '{credentials.username}', Password: '{credentials.password}'")
    # -----------------------------------------------------------

    # .env 파일에서 올바른 값을 가져옵니다.
    env_username = os.getenv("ADMIN_USERNAME")
    env_password = os.getenv("ADMIN_PASSWORD")

    print(f"username: '{env_username}' password: '{env_password}'")

    # secrets.compare_digest는 두 인자가 모두 문자열일 때만 작동합니다.
    # 환경 변수가 없을 경우를 대비해 빈 문자열로 처리합니다.
    correct_username = secrets.compare_digest(credentials.username, env_username or "")
    correct_password = secrets.compare_digest(credentials.password, env_password or "")
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

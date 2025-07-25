# Dockerfile

# 1. 베이스 이미지 선택 (가벼운 slim 버전 추천)
FROM python:3.12-slim

# 2. 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 파일을 먼저 복사하여 라이브러리 설치 (도커 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 프로젝트 파일들을 컨테이너에 복사
COPY . .

# 5. 컨테이너가 시작될 때 실행할 명령어
# 0.0.0.0으로 호스트를 열어야 외부(Cloudflare Tunnel)에서 접근 가능
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
# airouge-backend
fastapi backend for airouge

## How to use?
```bash
# 'my-game-backend' 라는 이름으로 이미지를 빌드합니다. 맨 뒤의 .은 현재 폴더를 의미합니다.
docker build -t my-game-backend .
# 기존에 실행 중인 컨테이너가 있다면 중지 및 삭제
docker stop my-game-container
docker rm my-game-container

# 새 컨테이너 실행
# -d: 백그라운드에서 실행
# -p 8000:80 : 내 서버의 8000번 포트와 컨테이너의 80번 포트를 연결
# --name: 컨테이너에 이름 부여
# --env-file .env: .env 파일의 환경변수를 컨테이너에 주입
docker run -d -p 8000:80 --name my-game-container --env-file .env my-game-backend
```

pip freeze > requirements.txt
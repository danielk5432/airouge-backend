# airouge-backend
fastapi backend for airouge

## How to use?
```bash
# 'my-game-backend' 라는 이름으로 이미지를 빌드합니다. 맨 뒤의 .은 현재 폴더를 의미합니다.
docker build -t my-game-backend .
# 기존에 실행 중인 컨테이너가 있다면 중지 및 삭제
docker stop my-game-container
docker rm my-game-container

# run docker container
sudo docker run \
    -d \
    --name airouge-backend-container \
    -p 8000:8000 \
    --env-file .env \
    -v $(pwd):/app \
    -w /app \
    --restart always \
    python:3.12-slim \
    bash -c "pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# make requirments
pip freeze > requirements.txt

# download requirments
pip install -r requirements.txt

```
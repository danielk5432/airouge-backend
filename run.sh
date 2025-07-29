sudo docker stop airouge-backend-container
sudo docker rm airouge-backend-container
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
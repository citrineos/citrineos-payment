# Stage 1: Build the Frontend
FROM node:20 AS frontend-builder

WORKDIR /app/frontend

COPY frontend ./
RUN npm install
RUN npm run build

# Stage 2: Create the Python Application
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN if [ ! -f ./.env ]; then echo "Error: .env File not found"; exit 1; fi
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN rm -rf ./frontend
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

ENV WEBSERVER_HOST="0.0.0.0"
ENV WEBSERVER_PORT=9010
EXPOSE $WEBSERVER_PORT

CMD uvicorn main:app --host "$WEBSERVER_HOST" --port "$WEBSERVER_PORT"

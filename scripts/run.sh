#!/bin/bash

# 기본값 설정
ENV_FILE=${1:-./envs/.env}

# 환경 변수 파일 로드
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

# 기본 디렉토리 설정
POSTGRES_DATA_DIR=${POSTGRES_DATA_DIR:-/mnt/nas/storage/webchat/dev/pg_db}
LOG_DIR=${LOG_DIR:-./logs}

# 디렉토리 생성 및 권한 설정
echo "Creating and setting up directories..."

# PostgreSQL 데이터 디렉토리 설정
sudo mkdir -p "$POSTGRES_DATA_DIR"
sudo chown -R 999:999 "$POSTGRES_DATA_DIR"
sudo chmod -R 755 "$POSTGRES_DATA_DIR"

# 로그 디렉토리 설정
sudo mkdir -p "$LOG_DIR"
sudo chmod -R 755 "$LOG_DIR"

echo "Postgres data directory: $POSTGRES_DATA_DIR"
echo "Log directory: $LOG_DIR"

# Docker 컨테이너 재시작
echo "Restarting Docker containers..."
POSTGRES_USER="$POSTGRES_USER" \
POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
POSTGRES_DB="$POSTGRES_DB" \
POSTGRES_DATA_DIR="$POSTGRES_DATA_DIR" \
LOG_DIR="$LOG_DIR" \
APP_PORT="$APP_PORT" \
docker compose up --build -d

echo "Setup completed successfully!"
#!/bin/bash

# 기본값 설정
ENV_FILE=./envs/.env  # 항상 .env 파일만 사용

K8S_IP=${1:-"127.0.0.1"}
SERVICE_PORT=${2:-9012}
POSTGRES_PORT=${3:-5432}
NODE_PORT=${4:-30800}

# 스크립트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 환경 변수 파일 로드
if [ -f "$SCRIPT_DIR/../$ENV_FILE" ]; then
    source "$SCRIPT_DIR/../$ENV_FILE"
    # ENV_FILE을 절대경로로 변환
    ENV_FILE="$(realpath "$SCRIPT_DIR/../$ENV_FILE")"
else
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

# 로그/DB 경로가 상대경로이면 절대경로로 변환
if [[ "$LOG_DIR" != /* ]]; then
    LOG_DIR="$(realpath "$SCRIPT_DIR/../$LOG_DIR")"
fi
if [[ "$POSTGRES_DATA_DIR" != /* ]]; then
    POSTGRES_DATA_DIR="$(realpath "$SCRIPT_DIR/../$POSTGRES_DATA_DIR")"
fi

# K8S 디렉토리 설정
K8S_DIR="$SCRIPT_DIR/../k8s"

# 임시 파일 삭제
echo "Cleaning up temporary files..."
rm -f "$K8S_DIR/app_configured.yaml"
rm -f "$K8S_DIR/db_configured.yaml"

# k8s 디렉토리로 이동
cd "$K8S_DIR"

# 1. 기존 리소스 정리
echo "Cleaning up existing Kubernetes resources..."
kubectl delete deployment tapestry-app --ignore-not-found=true
kubectl delete service tapestry-service tapestry-postgres --ignore-not-found=true
kubectl delete statefulset tapestry-postgres --ignore-not-found=true
kubectl delete secret tapestry-secrets --ignore-not-found=true
kubectl delete pvc --all --ignore-not-found=true
kubectl delete pv tapestry-logs-pv tapestry-postgres-pv --ignore-not-found=true
echo "Waiting for resources to be terminated..."
sleep 10 # Give a moment for termination

# 2. Docker 이미지 빌드 및 로드
echo "Building and loading Docker image..."
cd "$SCRIPT_DIR/.."
docker build -t tapestry:latest .
docker save tapestry:latest | sudo ctr -n k8s.io images import -
cd "$K8S_DIR" # 다시 k8s 디렉토리로

# 3. 호스트 경로 및 권한 설정
echo "Creating required directories on host..."
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$POSTGRES_DATA_DIR"
sudo chown -R 999:999 "$POSTGRES_DATA_DIR"
sudo chmod -R 700 "$POSTGRES_DATA_DIR"
sudo chmod -R 777 "$LOG_DIR"

# 4. Kubernetes 시크릿 생성
echo "Creating Kubernetes secrets from .env file..."
kubectl create secret generic tapestry-secrets \
  --from-env-file="$ENV_FILE" \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. 환경 변수 치환 및 리소스 배포
echo "Configuring and deploying resources..."
export SERVICE_PORT POSTGRES_PORT NODE_PORT LOG_DIR POSTGRES_DATA_DIR

# DB 및 스토리지 리소스 배포
envsubst < db.yaml > db_configured.yaml
kubectl apply -f db_configured.yaml

# PVC가 PV에 바인딩 될 시간을 줌
echo "Waiting 5 seconds for PVC to bind..."
sleep 5

# 앱 리소스 배포
envsubst < app.yaml > app_configured.yaml
kubectl apply -f app_configured.yaml

# 6. 배포 상태 확인
echo "Checking deployment status..."
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=tapestry-postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=tapestry --timeout=300s

echo -e "\n=== Deployment Status ==="
kubectl get pods -o wide
kubectl get services -o wide
kubectl get pv
kubectl get pvc

# 7. 서비스 접근 정보 출력
echo -e "\n=== Service Access Information ==="
echo "You can access the service at: http://${K8S_IP}:${NODE_PORT}"

# 임시 파일 정리
echo "Cleaning up temporary files..."
rm -f app_configured.yaml db_configured.yaml 
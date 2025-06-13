#!/bin/bash

# 기본값 설정
K8S_IP=${1:-"127.0.0.1"}
ENV_FILE=${2:-./envs/k8s.env}
SERVICE_PORT=${3:-9012}
POSTGRES_PORT=${4:-5432}
NODE_PORT=${5:-30800}

# 환경 변수 파일 로드
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    # ENV_FILE을 절대경로로 변환
    ENV_FILE="$(realpath "$ENV_FILE")"
else
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

# 스크립트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="$SCRIPT_DIR/../k8s"

# 불필요한 파일 삭제
echo "Cleaning up unnecessary files..."
rm -f "$K8S_DIR/deploy.sh"
rm -f "$K8S_DIR/deployment_configured.yaml"

# k8s 디렉토리로 이동
cd "$K8S_DIR"

# 스크립트 실행 권한 부여
chmod +x create-secrets.sh

# Docker 이미지 빌드 및 로드
echo "Building and loading Docker image..."
cd "$SCRIPT_DIR/.."
docker build -t tapestry:latest .
docker save tapestry:latest | sudo ctr -n k8s.io images import -

# k8s 디렉토리로 이동
cd "$K8S_DIR"

# 기존 리소스 정리
echo "Cleaning up existing resources..."
kubectl delete service tapestry-external --ignore-not-found=true
kubectl delete secret tapestry-secrets --ignore-not-found=true
kubectl delete -f postgres.yaml --ignore-not-found=true
kubectl delete -f deployment.yaml --ignore-not-found=true
kubectl delete pvc --all --ignore-not-found=true
kubectl delete pv tapestry-logs-pv tapestry-postgres-pv --ignore-not-found=true

# 필요한 디렉토리 생성 및 권한 설정
echo "Creating required directories..."
sudo mkdir -p /mnt/data/tapestry/logs
sudo mkdir -p /mnt/data/tapestry/postgres
sudo chmod -R 777 /mnt/data/tapestry

# PersistentVolume 생성
echo "Creating PersistentVolumes..."
kubectl apply -f pv.yaml

# 기존 시크릿 삭제 후 재생성
echo "Updating Kubernetes secrets..."
ENV_FILE="$ENV_FILE" ./create-secrets.sh

# 환경 변수 치환
echo "Configuring deployment..."
export SERVICE_PORT=$SERVICE_PORT
export POSTGRES_PORT=$POSTGRES_PORT
envsubst < deployment.yaml > deployment_configured.yaml
envsubst < postgres.yaml > postgres_configured.yaml

# Kubernetes 리소스 배포/업데이트
echo "Deploying/Updating Kubernetes resources..."
kubectl apply -f postgres_configured.yaml
kubectl apply -f deployment_configured.yaml

# 배포 상태 확인
echo "Checking deployment status..."
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=tapestry --timeout=300s
kubectl wait --for=condition=ready pod -l app=tapestry-postgres --timeout=300s

echo -e "\n=== Deployment Status ==="
kubectl get pods
kubectl get services
kubectl get pv
kubectl get pvc

# 서비스 접근 정보 출력
echo -e "\n=== Service Access Information ==="
echo "Service port mapping information:"
kubectl get service tapestry-service -o jsonpath='{.spec.ports[0]}' | jq .
echo -e "\nYou can access the service at:"
echo "http://${K8S_IP}:${NODE_PORT}"

# 시크릿 확인 메시지
echo -e "\nNote: Sensitive information in .env file is stored as Kubernetes secrets and is not exposed externally."

# 임시 파일 정리
rm -f deployment_configured.yaml postgres_configured.yaml 
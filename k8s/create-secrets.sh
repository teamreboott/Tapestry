#!/bin/bash

echo "Using ENV_FILE: $ENV_FILE"

# ENV_FILE이 이미 설정되어 있으면 그 값을 사용, 아니면 기본값 사용
ENV_FILE="${ENV_FILE:-../envs/k8s.env}"

# 환경 변수 파일이 존재하는지 확인
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

# 기존 시크릿 삭제
kubectl delete secret tapestry-secrets --ignore-not-found=true

# Kubernetes 시크릿 생성
echo "Creating Kubernetes secrets from .env file..."
kubectl create secret generic tapestry-secrets \
  --from-env-file="$ENV_FILE" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Kubernetes secrets have been created successfully."
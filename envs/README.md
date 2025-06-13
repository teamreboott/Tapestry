# ENV 예시

# Environment Variable Guide

이 프로젝트는 환경 변수 파일(.env)로 모든 설정을 관리합니다.

**중요:**
- 반드시 `example.env` 파일을 복사해 `.env`로 만들어 사용하세요.

## 사용 방법

1. 템플릿 복사
   ```bash
   cp envs/example.env envs/.env
   ```
2. `.env` 파일을 열어 본인 환경에 맞게 수정하세요.
   - API 키, DB 정보 등 필수 값 입력
   - Docker/Kubernetes 환경에 따라 `POSTGRES_HOST` 등 일부 값만 다르게 설정

3. 서비스 실행 시 `.env` 파일만 사용하면 됩니다.
   - Docker Compose, Kubernetes, 로컬 모두 동일하게 `.env` 사용

## Docker/Kubernetes 환경 차이
- `POSTGRES_HOST` 값만 다르게 설정하세요.
  - Docker: `POSTGRES_HOST=postgres`
  - Kubernetes: `POSTGRES_HOST=tapestry-postgres`
- 기타 변수는 동일하게 사용 가능합니다.

## 예시 템플릿
- 모든 변수와 설명은 `example.env` 파일을 참고하세요.

MODEL_NAME=gpt-4.1-2025-04-14
SUB_MODEL_NAME=claude-3-7-sonnet-latest
MAX_TOKENS=1000
APP_HOST=0.0.0.0
APP_PORT=9004
VENDOR=openai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
SERPER_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
SLACK_WEBHOOK_URL=
```

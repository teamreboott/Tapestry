# Tapestry Gradio Web UI

[English](README.md) | 한국어

## 소개
이 프로젝트는 Gradio 기반의 Web Search 챗봇 UI입니다.

## 빠른 시작 (Quick Start)

### 1. 로컬 실행 (Docker 없이)

```bash
bash run_demo.sh
```

환경변수로 포트와 API 주소를 지정할 수 있습니다:

```bash
GRADIO_PORT=8888 API_URL=http://my-api:9000/websearch bash run_demo.sh
```

---

### 2. 도커 실행

```bash
bash run_docker_demo.sh
```

포트와 API 주소도 환경변수로 지정할 수 있습니다:

```bash
GRADIO_PORT=8888 API_URL=http://my-api:9000/websearch bash run_docker_demo.sh
```

---

## 파일 구조

- app.py : Gradio UI 메인 코드
- requirements.txt : Python 패키지 목록
- run_demo.sh : 로컬 실행 스크립트
- run_docker_demo.sh : 도커 실행 스크립트
- Dockerfile : 도커 빌드 파일
- logo.png : 챗봇 아바타 이미지

---

## 참고사항

- 백엔드 API 서버가 먼저 실행되어 있어야 합니다. 
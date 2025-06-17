#!/bin/bash

# 환경변수 기본값 설정 (이미 지정되어 있으면 그대로 사용)
export GRADIO_PORT="${GRADIO_PORT:-80}"
export API_URL="${API_URL:-http://127.0.0.1:9012/websearch}"

exec python app.py 
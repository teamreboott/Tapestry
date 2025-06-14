# Tapestry API 가이드

[English](README.md) | 한국어

이 가이드는 Tapestry API 엔드포인트와 사용 방법에 대한 정보를 제공합니다.

---

## API 엔드포인트

### 웹 검색 API
`POST /websearch`

웹 검색 기반 QA를 위한 메인 엔드포인트입니다.

#### 요청 파라미터

| 이름 | 타입 | 설명 | 기본값 | 필수 |
|------|------|-------------|---------|----------|
| `query` | String | 검색 쿼리 | - | 예 |
| `language` | String | 검색 언어 (`ko`, `en`, `zh`, `ja`) | `ko` | 아니오 |
| `persona_prompt` | String | 페르소나 프롬프트 (필요없으면 `None`) | - | 아니오 |
| `custom_prompt` | String | 커스텀 프롬프트 (필요없으면 `None`) | - | 아니오 |
| `target_nuance` | String | 뉘앙스 (필요없으면 `None`) | - | 아니오 |
| `return_process` | Boolean | 프로세스 메시지 반환 여부 | `true` | 아니오 |
| `stream` | Boolean | 스트리밍 응답 반환 여부 | `true` | 아니오 |
| `use_youtube_transcript` | Boolean | 유튜브 전사 포함 여부 | `true` | 아니오 |
| `top_k` | Integer | 사용할 웹 컨텐츠 수 | `"auto"` | 아니오 |
| `messages` | Array | 메시지 히스토리 (필요없으면 `[]`) | - | 아니오 |
| └ `role` | String | 역할 (`user`, `assistant`) | - | 예* |
| └ `content` | String | 메시지 내용 | - | 예* |

\* `messages` 배열이 제공된 경우 필수

#### 응답 형식

API는 다음과 같은 상태 타입의 스트리밍 응답을 반환합니다:

- `processing`: 처리 상태 업데이트
- `streaming`: 스트리밍 컨텐츠 청크
- `complete`: 최종 완성된 응답
- `failure`: 오류 메시지

#### 사용 예시

```python
import asyncio
import aiohttp
import json

async def request_web_search(query: str):
    payload = {
        "language": "ko",
        "query": query,
        "persona_prompt": "N/A",
        "custom_prompt": "N/A",
        "target_nuance": "Natural",
        "messages": [],
        "stream": True,
        "use_youtube_transcript": False,
        "top_k": None
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:9012/websearch", json=payload) as response:
            async for line in response.content:
                data = json.loads(line.decode("utf-8").strip())
                if data["status"] == "streaming":
                    print(data["delta"]["content"], end="")
                elif data["status"] == "complete":
                    print("\n응답 완료")
                    break
```

### 헬스 체크 API
`GET /health`

서비스 상태를 확인하기 위한 간단한 헬스 체크 엔드포인트입니다.

---

## 클라이언트 예제

`service` 디렉토리에는 다음과 같은 예제 클라이언트가 포함되어 있습니다:

- `client_stream.py`: 스트리밍 API 사용 예제
- `client_sync.py`: 동기식 API 사용 예제

스트리밍 클라이언트를 실행하려면:

```bash
python client_stream.py
```

클라이언트 파일의 `SERVER_URL`을 배포 환경에 맞게 설정해야 합니다:
- Docker: `http://127.0.0.1:9012/websearch`
- Kubernetes: `http://127.0.0.1:30800/websearch` 
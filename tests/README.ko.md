# Tapestry 테스트 클라이언트 & API 가이드

[English](README.md) | 한국어

이 문서는 Tapestry API 엔드포인트와 제공되는 테스트 클라이언트 사용법을 안내합니다.

---

## 📚 API 레퍼런스

### `POST /websearch`

웹 검색 기반 QA를 위한 메인 엔드포인트입니다.

#### 요청 바디

| 이름                    | 타입    | 설명                                                        | 기본값    | 필수    |
|------------------------|---------|-------------------------------------------------------------|-----------|---------|
| `query`                | String  | 검색 쿼리                                                   | -         | 예      |
| `language`             | String  | 검색 언어 (`ko`, `en`, `zh`, `ja`)                          | `ko`      | 아니오  |
| `search_type`          | String  | 검색 타입 (`auto`, `general`, `scholar`, `news`, `youtube`) | `auto`    | 아니오  |
| `persona_prompt`       | String  | 페르소나 프롬프트 (`N/A` 사용 시 미적용)                    | `N/A`     | 아니오  |
| `custom_prompt`        | String  | 커스텀 프롬프트 (`N/A` 사용 시 미적용)                      | `N/A`     | 아니오  |
| `target_nuance`        | String  | 목표 뉘앙스 (`Natural` 사용 시 기본)                        | `Natural` | 아니오  |
| `return_process`       | Boolean | 프로세스 메시지 반환 여부                                   | `true`    | 아니오  |
| `stream`               | Boolean | 스트리밍 응답 반환 여부                                     | `true`    | 아니오  |
| `use_youtube_transcript`| Boolean| 유튜브 트랜스크립트 포함 여부                               | `false`   | 아니오  |
| `top_k`                | Integer | 사용할 웹 컨텐츠 수 (`auto`는 자동)                         | `auto`    | 아니오  |
| `messages`             | Array   | 메시지 히스토리 (필요 없으면 `[]`)                          | `[]`      | 아니오  |
| └ `role`               | String  | 역할 (`user`, `assistant`)                                  | -         | 예*     |
| └ `content`            | String  | 메시지 내용                                                 | -         | 예*     |

\* `messages` 배열이 제공된 경우 필수

#### 응답

아래와 같은 status 타입의 JSON 라인 스트리밍:

- `processing`: 처리 상태
- `streaming`: 스트리밍 응답
- `complete`: 최종 응답
- `failure`: 오류 메시지

---

## 🧪 테스트 클라이언트 사용법

API 테스트용 샘플 클라이언트가 제공됩니다.

### 클라이언트 실행

```bash
python client.py --query "AI 검색 엔진이란?" --language ko
```

#### 주요 옵션

- `--query`: (필수) 검색 쿼리
- `--language`: 검색 언어 (`en`, `ko` 등)
- 기타 옵션은 `python client.py --help` 참고

#### 엔드포인트 설정

`client.py`의 `SERVER_URL`을 환경에 맞게 수정하세요.

- Docker/로컬: `http://127.0.0.1:9012/websearch`
- Kubernetes: `http://127.0.0.1:30800/websearch`

---

## 🩺 헬스 체크

`GET /health`

```bash
curl http://127.0.0.1:9012/health
```

---

## 📁 파일

- `client.py` : API 테스트용 비동기 클라이언트 예제
- `README.md` : (영문)
- `README.ko.md` : (이 파일)

--- 
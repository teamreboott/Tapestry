# Tapestry

[English](README.md) | [한국어](README.ko.md)

웹 검색 기반 LLM QA 시스템으로, CIKM 2025 데모 트랙을 위해 설계되었습니다.

---

## 🚀 빠른 시작

이 가이드는 Docker 또는 Kubernetes를 사용하여 Tapestry 서비스를 실행하는 방법을 설명합니다.

### 1. 사전 요구사항: 환경 설정

서비스를 시작하기 전에 환경 변수를 구성해야 합니다. 모든 설정은 프로젝트 루트의 `.env` 파일을 통해 관리됩니다.

1.  **예제 설정 복사:**  
    제공된 템플릿을 복사하여 환경 파일을 생성합니다.

    ```bash
    cp envs/example.env .env
    ```

2.  **`.env` 파일 편집:**  
    새로 생성된 `.env` 파일을 열고 API 키와 데이터베이스 자격 증명과 같은 필수 값을 입력합니다.

    -   각 변수에 대한 자세한 설명은 [`envs/README.md`](envs/README.md) 가이드를 참조하세요.
    -   **중요**: `POSTGRES_HOST` 변수는 배포 환경에 맞게 올바르게 설정되어야 합니다:
        -   **Docker**: `POSTGRES_HOST=postgres`
        -   **Kubernetes**: `POSTGRES_HOST=tapestry-postgres`

### 2. Docker로 실행하기

로컬 개발 및 테스트에 권장되는 방법입니다.

1.  **`.env` 파일이 위에서 설명한 대로 구성되어 있는지 확인**하세요. `POSTGRES_HOST=postgres`로 설정되어 있어야 합니다.

2.  **실행 스크립트 실행:**  
    스크립트는 디렉토리 설정을 처리하고 Docker Compose를 사용하여 모든 서비스를 시작합니다.

    ```bash
    bash scripts/run.sh
    ```
    > 스크립트는 기본적으로 프로젝트 루트의 `.env` 파일을 사용합니다.

3.  **서비스 접근:**
    API는 `http://localhost:9012`에서 사용할 수 있습니다. `.env` 파일의 `APP_PORT` 변수를 통해 포트를 변경할 수 있습니다.

### 3. Kubernetes로 실행하기

Kubernetes 클러스터에 배포하기 위한 방법입니다.

1.  **`.env` 파일이 위에서 설명한 대로 구성되어 있는지 확인**하세요. `POSTGRES_HOST=tapestry-postgres`로 설정되어 있어야 합니다. 또한 `LOG_DIR`과 `POSTGRES_DATA_DIR`이 Kubernetes 노드에 존재하는 절대 경로인지 확인하세요.

2.  **배포 스크립트 실행:**  
    이 스크립트는 전체 배포 프로세스를 자동화합니다.

    ```bash
    bash scripts/run_k8s.sh [K8S_IP] [SERVICE_PORT] [POSTGRES_PORT] [NODE_PORT]
    ```

    **스크립트 인자:**
    -   `K8S_IP`: Kubernetes 클러스터의 IP 주소 (기본값: `127.0.0.1`)
    -   `SERVICE_PORT`: 애플리케이션 서비스의 내부 포트 (기본값: `9012`)
    -   `POSTGRES_PORT`: PostgreSQL 서비스의 포트 (기본값: `5432`)
    -   `NODE_PORT`: 서비스에 접근하기 위한 외부 포트 (기본값: `30800`)

    **예시:**
    ```bash
    bash scripts/run_k8s.sh 127.0.0.1 9012 5432 30800
    ```

3.  **서비스 접근:**
    API는 `http://[K8S_IP]:[NODE_PORT]`에서 사용할 수 있습니다 (예: `http://127.0.0.1:30800`).

---

## 🧪 서비스 테스트

제공된 클라이언트 스크립트를 사용하여 스트리밍 API를 테스트할 수 있습니다.

1.  **서비스 디렉토리로 이동:**
    ```bash
    cd service/
    ```

2.  **클라이언트 실행:**
    ```bash
    python client_stream.py
    ```

3.  **엔드포인트 구성:**  
    실행하기 전에 `service/client_stream.py`를 열고 `SERVER_URL` 변수가 환경에 맞는 올바른 엔드포인트를 가리키는지 확인하세요:
    -   **Docker:** `http://127.0.0.1:9012/websearch`
    -   **Kubernetes:** `http://127.0.0.1:30800/websearch` (또는 `K8S_IP`와 `NODE_PORT`)

---

## API 엔드포인트

- `GET /health`: 헬스 체크 엔드포인트
- `POST /websearch`: 스트리밍 응답이 있는 메인 QA 엔드포인트

---

## 프로젝트 구조

```
.
├── main.py                # 메인 FastAPI 서버
├── src/                   # 핵심 소스 코드 (모델, 검색, DB, 유틸리티 등)
├── service/               # 서비스 레이어
├── configs/               # 설정 파일
├── scripts/               # 자동화 스크립트 (run.sh, run_k8s.sh)
├── envs/                  # 환경 변수 예제 및 문서
├── k8s/                   # Kubernetes 매니페스트
├── requirements.txt       # Python 의존성
├── Dockerfile             # Docker 빌드 파일
├── docker-compose.yaml    # Docker Compose 파일
└── README.md
``` 
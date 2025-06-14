# 환경 변수 가이드

[English](README.md) | 한국어

이 프로젝트의 모든 설정은 환경 변수 파일(`.env`)을 통해 관리됩니다. 이 방식은 다양한 환경(로컬, Docker, Kubernetes)에서 유연하고 안전한 설정을 가능하게 합니다.

---

## 사용 방법

1.  **`.env` 파일 생성:**  
    제공된 템플릿 `example.env`를 복사하여 `envs` 디렉토리에 `.env` 파일을 생성합니다.

    ```bash
    cp envs/example.env envs/.env
    ```

    > **중요**: `.env` 파일은 `envs` 디렉토리에 위치해야 합니다. 실행 스크립트들은 이 위치에서 설정 파일을 찾습니다.

2.  **`.env` 파일 편집:**  
    `.env` 파일을 열고 API 키, 데이터베이스 자격 증명, 호스트 경로 등과 같은 특정 설정을 입력합니다.

    > **참고:** 각 변수에 대한 자세한 설명은 `envs/example.env` 파일 내의 주석을 참조하세요.

---

## 환경별 설정

대부분의 변수는 보편적이지만, 일부 변수는 Docker 또는 Kubernetes로 서비스를 실행하는지에 따라 특정 값이 필요합니다.

### `POSTGRES_HOST`
이 변수는 PostgreSQL 데이터베이스 서비스의 네트워크 호스트명을 정의합니다.
-   **Docker의 경우:** `docker-compose.yaml`에 정의된 서비스 이름으로 설정합니다.
    ```
    POSTGRES_HOST=postgres
    ```
-   **Kubernetes의 경우:** PostgreSQL의 Kubernetes 서비스 이름으로 설정합니다.
    ```
    POSTGRES_HOST=tapestry-postgres
    ```

### `LOG_DIR` 및 `POSTGRES_DATA_DIR`
이 변수들은 로그와 데이터베이스 데이터를 저장하기 위한 호스트 경로를 정의합니다.
-   **Docker의 경우:** 호스트 머신의 상대 경로 또는 절대 경로를 사용할 수 있습니다.
-   **Kubernetes의 경우:** `hostPath` PersistentVolumes에 사용되므로 Kubernetes 노드에 존재하는 **절대 경로**여야 합니다.
    -   예시: `/mnt/nas/storage/tapestry/logs`
FROM python:3.12-slim

# 기본 패키지 설치
RUN set -eux && \
    echo 'deb https://deb.debian.org/debian bookworm main' > /etc/apt/sources.list && \
    echo 'deb https://deb.debian.org/debian-security bookworm-security main' >> /etc/apt/sources.list && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        # 기본 도구
        wget unzip curl ca-certificates git \
        python3 python3-pip \
        # Chrome/Selenium 의존성
        libnss3 libatk1.0-0 libatk-bridge2.0-0 \
        libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
        libgbm1 libgtk-3-0 libasound2 libxshmfence1 \
        libxss1 libxtst6 fonts-liberation \
        # 폰트 및 빌드 도구
        fonts-nanum \
        build-essential g++ gcc && \
    rm -rf /var/lib/apt/lists/* && \
    fc-cache -fv

# Python 실행을 위한 심볼릭 링크 생성
RUN ln -s /usr/bin/python3 /usr/bin/python

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 파일을 먼저 복사하여 Docker 캐시 효율성 향상
COPY requirements.txt /app/

# Python 패키지 설치
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 나머지 소스 코드 복사
COPY . /app

# 컨테이너 실행 시 애플리케이션 실행
CMD ["python", "main.py"]
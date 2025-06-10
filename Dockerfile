FROM python:3.11-slim


# 기본 패키지 설치
RUN set -eux; \
    echo 'deb https://deb.debian.org/debian bookworm main' >  /etc/apt/sources.list ; \
    echo 'deb https://deb.debian.org/debian-security bookworm-security main' >> /etc/apt/sources.list ; \
    apt-get update ; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    wget unzip curl \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libgtk-3-0 libasound2 libxshmfence1 \
    libxss1 libxtst6 fonts-liberation \
    ca-certificates \
    git \
    python3 \
    python3-pip \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Python 실행을 위한 심볼릭 링크 생성
RUN ln -s /usr/bin/python3 /usr/bin/python


WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    aiohttp==3.11.11 \
    aiofiles==23.2.1 \
    beautifulsoup4==4.12.3 \
    fastapi==0.111.1 \
    gunicorn==22.0.0 \
    numpy==1.26.4 \
    openai==1.59.3 \
    python-dotenv==1.0.1 \
    uvicorn==0.22.0 \
    youtube-transcript-api==0.6.3 \ 
    structlog==24.4.0 \
    trafilatura==2.0.0 \
    markdownify==1.1.0 \ 
    pdfminer \
    pdfminer.six \
    pydantic-settings \ 
    anthropic \ 
    PyMuPDF==1.25.5 \
    concurrent-log-handler \
    rich==14.0.0 \
    httpx[http2] \
    html2text \
    pandas==2.2.3 \
    cloudscraper==1.2.71 \ 
    uvloop \ 
    certifi \
    simhash==2.1.2 \
    fake-useragent==2.2.0 \
    litellm \ 
    selenium \
    psycopg2-binary \
    asyncpg \
    elasticsearch[async]==8.0.0 \
    sqlalchemy \
    pyyaml

# 컨테이너 실행 시 gunicorn 서버 실행
CMD ["python", "main.py"]
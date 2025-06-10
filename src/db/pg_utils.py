import asyncio
import logging
from sqlalchemy import create_engine, text, Column, String, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.exc import SQLAlchemyError
from elasticsearch import AsyncElasticsearch, exceptions as es_exceptions
from datetime import datetime
from typing import Dict, Any, Optional, List
from configs.config import Settings
import structlog
logger = structlog.get_logger(__name__) 

db_settings = Settings()

# --------------------------------------------------------------------------------
# PostgreSQL 설정
# --------------------------------------------------------------------------------
Base = declarative_base()

class CrawledData(Base):
    __tablename__ = "crawled_data"

    url = Column(String, primary_key=True, index=True) # URL을 기본 키 및 인덱스로 사용
    title = Column(String)
    snippet = Column(TEXT, nullable=True)
    image_url = Column(String, nullable=True)
    date = Column(String, nullable=True) # 날짜 형식이 다양하므로 문자열로 저장
    language = Column(String, nullable=True)
    type = Column(String, nullable=True) # Serper 결과의 type 등
    pdf_url = Column(String, nullable=True)
    content = Column(TEXT, nullable=True) # 크롤링된 본문 내용
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 추가: Serper 결과의 다른 필드들을 저장하고 싶다면 JSON 타입 컬럼 활용 가능
    # serper_source_info = Column(JSON, nullable=True)

# 동기 엔진 (테이블 생성용)
sync_engine = create_engine(db_settings.SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def create_pg_tables():
    try:
        Base.metadata.create_all(bind=sync_engine)
        logger.info("PostgreSQL tables created successfully (if they didn't exist).")
    except SQLAlchemyError as e:
        logger.error(f"Error creating PostgreSQL tables: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during table creation: {e}")


# 비동기 PostgreSQL 연결 (asyncpg 사용)
# 실제 애플리케이션에서는 FastAPI의 lifespan 이벤트를 사용하여 연결 풀을 관리하는 것이 좋음
# 여기서는 단순화된 형태로 제공
async def get_pg_connection():
    # import asyncpg # asyncpg 직접 사용 시
    # conn = await asyncpg.connect(db_settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
    # return conn
    # SQLAlchemy async session 사용 시 (더 복잡할 수 있음)
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    engine = create_async_engine(db_settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session # FastAPI dependency injection 스타일


async def get_document_from_pg(url: str) -> Optional[Dict[str, Any]]:
    import asyncpg
    conn = None
    try:
        conn = await asyncpg.connect(db_settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
        row = await conn.fetchrow("SELECT url, title, snippet, image_url, date, language, type, pdf_url, content FROM crawled_data WHERE url = $1", url)
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching document from PostgreSQL for url {url}: {e}")
        return None
    finally:
        if conn:
            await conn.close()

async def save_document_to_pg(data: Dict[str, Any]):
    # Add URL filtering logic
    url = data.get('url', '')
    if not url:
        logger.warning("URL is empty. Skipping...")
        return
    
    # Check if the URL contains specific keywords
    allowed_keywords = ["news", "article", "youtube", "pdf", "arxiv"]
    if not any(keyword in url.lower() for keyword in allowed_keywords):
        return

    import asyncpg
    conn = None
    # Prepare data for CrawledData model fields
    # Except for 'content', other fields are fetched from source, and content is filled with the result of crawling.
    # 'type' and 'language' are fetched from source, so we need to modify the crawl function.
    query = """
    INSERT INTO crawled_data (url, title, snippet, image_url, date, language, type, pdf_url, content, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    ON CONFLICT (url) DO UPDATE SET
        title = EXCLUDED.title,
        snippet = EXCLUDED.snippet,
        image_url = EXCLUDED.image_url,
        date = EXCLUDED.date,
        language = EXCLUDED.language,
        type = EXCLUDED.type,
        pdf_url = EXCLUDED.pdf_url,
        content = EXCLUDED.content,
        updated_at = EXCLUDED.updated_at;
    """
    now = datetime.utcnow()
    try:
        conn = await asyncpg.connect(db_settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
        await conn.execute(query,
                           data.get('url'), data.get('title'), data.get('snippet'),
                           data.get('image_url'), data.get('date'), data.get('language'),
                           data.get('type'), data.get('pdf_url'), data.get('content'),
                           now, now)
    except Exception as e:
        logger.error(f"Error saving document to PostgreSQL for url {data.get('url')}: {e}")
    finally:
        if conn:
            await conn.close()

async def save_documents_to_pg_bulk(data_list: List[Dict[str, Any]]):
    # URL 필터링
    filtered_data = []
    allowed_keywords = ["news", "article", "youtube", "pdf", "arxiv"]
    
    for data in data_list:
        url = data.get('url', '')
        if not url:
            logger.warning("URL이 없어서 저장하지 않습니다.")
            continue
        
        if not any(keyword in url.lower() for keyword in allowed_keywords):
            # logger.info(f"URL {url}이 허용된 키워드를 포함하지 않아 저장하지 않습니다.")
            continue
            
        filtered_data.append(data)
    
    if not filtered_data:
        return
        
    import asyncpg
    conn = None
    query = """
    INSERT INTO crawled_data (url, title, snippet, image_url, date, language, type, pdf_url, content, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    ON CONFLICT (url) DO UPDATE SET
        title = EXCLUDED.title,
        snippet = EXCLUDED.snippet,
        image_url = EXCLUDED.image_url,
        date = EXCLUDED.date,
        language = EXCLUDED.language,
        type = EXCLUDED.type,
        pdf_url = EXCLUDED.pdf_url,
        content = EXCLUDED.content,
        updated_at = EXCLUDED.updated_at;
    """
    now = datetime.utcnow()
    try:
        conn = await asyncpg.connect(db_settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
        # 트랜잭션 시작
        async with conn.transaction():
            await asyncio.gather(*[
                conn.execute(query,
                    data.get('url'), data.get('title'), data.get('snippet'),
                    data.get('image_url'), data.get('date'), data.get('language'),
                    data.get('type'), data.get('pdf_url'), data.get('content'),
                    now, now)
                for data in filtered_data
            ])
        logger.info(f"{len(filtered_data)}개의 문서가 PostgreSQL에 저장되었습니다.")
    except Exception as e:
        logger.error(f"Error saving documents to PostgreSQL in bulk: {e}")
    finally:
        if conn:
            await conn.close()
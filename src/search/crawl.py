import httpx
import fitz
import asyncio
import uvloop
import time
from urllib.parse import urlparse
from src.converter import ExtractorRegistry
from src.converter.news_extractors import NEWS_EXTRACTORS
from src.converter.blog_extractors import BLOG_EXTRACTORS
from src.converter.media_extractors import MEDIA_EXTRACTORS
from src.converter.html_converter import HtmlConverter
from src.db.pg_utils import get_document_from_pg
from structlog import get_logger
from rich.console import Console

console = Console()
logger = get_logger(__name__)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class Crawler:
    '''
    return: title, url, snippet, image_url, date, content
    '''
    def __init__(self, news_list, blog_list, media_list, use_db_content=False, max_content_length=20000):
        self.news_list = news_list
        self.blog_list = blog_list
        self.media_list = media_list
        self.max_content_length = max_content_length
        self.num_contents = 0
        self.use_db_content = use_db_content
        self.html_converter = HtmlConverter()

        self._setup_extractors()

    def _setup_extractors(self):
        self.extractor_registry = ExtractorRegistry()
        
        # news extractors
        for news_domain in self.news_list:
            console.log(f"[green]Crawler-Extract: {news_domain} registered")
            self.extractor_registry.register(NEWS_EXTRACTORS[news_domain]())

        # blog extractors
        for blog_domain in self.blog_list:
            console.log(f"[green]Crawler-Extract: {blog_domain} registered")
            self.extractor_registry.register(BLOG_EXTRACTORS[blog_domain]())

        # media extractors
        for media_domain in self.media_list:
            console.log(f"[green]Crawler-Extract: {media_domain} registered")
            self.extractor_registry.register(MEDIA_EXTRACTORS[media_domain]())

    def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        text = ""
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                # 최대 20페이지까지만 추출
                max_pages = min(10, len(doc))
                text = "".join(doc[i].get_text() for i in range(max_pages))
            return text
        except Exception as e:
            return ""

    def extract_html_text(self, html_str: str, url: str) -> str:
        try:
            result = self.html_converter.convert_string(html_str, url=url)
            return result.markdown.strip()
        except Exception as e:
            return ""

    def remove_surrogates(self, text: str) -> str:
        """유니코드 서러게이트 문자를 효율적으로 제거"""
        if not text:
            return ""
        
        # encode/decode 방식으로 서러게이트 문자 처리 (for 루프보다 훨씬 빠름)
        return text.encode('utf-8', 'ignore').decode('utf-8')

    async def _fetch_text(self, url: str, browser_client) -> str:
        """Download *url* and return decoded body text."""
        
        try:
            # 1. 더 세밀한 타임아웃 설정 (연결 타임아웃과 읽기 타임아웃 분리)
            timeout = httpx.Timeout(connect=0.5, read=0.8, write=0.3, pool=0.2)
            
            # 2. 스트리밍 방식으로 데이터 받기 (메모리 효율성)
            async with browser_client.stream('GET', url, timeout=timeout) as response:
                if response.status_code != 200:
                    return ""
                
                content_type = response.headers.get('content-type', '').lower()
                content_length = response.headers.get('content-length')

                if "arxiv.org/abs" in url:
                    url = url.replace("/abs/", "/pdf/")
                    content_type = "application/pdf"
                
                # 3. 콘텐츠 크기 사전 체크 (너무 큰 파일 차단)
                if content_length and int(content_length) > 25 * 1024 * 1024:  # 25MB 제한
                    return ""
                
                # 4. 청크 단위로 읽으면서 크기 제한
                chunks = []
                total_size = 0
                max_size = 10 * 1024 * 1024  # 10MB 제한
                
                async for chunk in response.aiter_bytes(chunk_size=8192):  # 8KB 청크
                    total_size += len(chunk)
                    if total_size > max_size:
                        break
                    chunks.append(chunk)
                
                content_bytes = b''.join(chunks)
                
                # 5. 콘텐츠 타입별 최적화된 처리
                if "application/pdf" in content_type:
                    # PDF 처리를 별도 스레드에서 타임아웃으로 실행
                    return await asyncio.wait_for(
                        asyncio.to_thread(self.extract_pdf_text, content_bytes), 
                        timeout=1.5
                    )
                elif "text/html" in content_type or "text/" in content_type:
                    # HTML/텍스트 처리
                    try:
                        # 6. 인코딩 자동 감지 및 처리
                        text_content = content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # UTF-8 실패시 다른 인코딩 시도
                        import chardet
                        detected = chardet.detect(content_bytes[:10000])  # 처음 10KB만 검사
                        encoding = detected.get('encoding', 'utf-8')
                        try:
                            text_content = content_bytes.decode(encoding, errors='ignore')
                        except:
                            text_content = content_bytes.decode('utf-8', errors='ignore')
                    
                    if "text/html" in content_type:
                        return await asyncio.wait_for(
                            asyncio.to_thread(self.extract_html_text, text_content, url), 
                            timeout=0.5
                        )
                    else:
                        # 일반 텍스트는 바로 반환 (크기 제한 적용)
                        return text_content[:self.max_content_length]
                else:
                    return ""
                    
        except asyncio.TimeoutError:
            return ""
        except httpx.HTTPStatusError:
            return ""
        except httpx.RequestError:
            return ""
        except Exception:
            return ""

    async def crawl(self, browser_client, source):

        url = source['url']
        
        content = ""
        if self.use_db_content:
            pg_doc = await get_document_from_pg(url)
            if pg_doc and pg_doc.get('content'):
                content = pg_doc.get('content')
        
        if not content:
            try:
                extractor = self.extractor_registry.get_extractor(url)
                if extractor:
                    content = await extractor.extract(url, browser_client)
                else:
                    content = await self._fetch_text(url, browser_client)
            except httpx.HTTPStatusError as e:
                console.log(f"[red]HTTP error {e.response.status_code} for {url}: {e}")
                content = f"Failed to fetch with status {e.response.status_code}"
            except httpx.RequestError as e:
                console.log(f"[red]Request error for {url}: {e}")
                content = f"Request failed: {type(e).__name__}"
            except asyncio.TimeoutError:
                console.log(f"[red]Timeout while processing {url}")
                content = "Processing timed out"
            except Exception as e:
                console.log(f"[red]An unexpected error occurred while crawling {url} ({source['title']}): {e}")
                console.log("[red]****************")
                content = f"Error: {type(e).__name__}" # 예외 유형도 포함

        source['content'] = content[:self.max_content_length]
        console.log(f"[green]Crawler-Extract: {source['title']}")
        console.log(f"[green]Crawler-Extract: {source['content'][:100]}")
        console.log(f"[green]Crawler-Extract: {source['url']}")
        console.log(f"[green]--------------------------------")
        if len(source['content']) > 0:
            self.num_contents += 1
        del source['type']
        del source['language']
        return source

    async def multiple_crawl(self, browser_client, sources):
        start_time = time.time()
        scraped_results = await asyncio.gather(*[self.crawl(browser_client, source) for source in sources])
        console.log(f"[pink bold]Crawler-Extract: {time.time() - start_time:.2f} seconds")
        console.print("[green]****************")
        console.print(f"[green]Extracted contents: {self.num_contents}/{len(sources)}")
        console.print("[green]****************")
        self.num_contents = 0
        return scraped_results
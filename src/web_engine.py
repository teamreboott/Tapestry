import asyncio, io
import httpx
import re
import os
import fitz
import time
import json
import requests
import structlog
import cloudscraper
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import List, Dict, Union, Tuple, Any, Callable, Sequence, Optional
from collections import OrderedDict
from trafilatura import extract
from urllib.parse import urlparse
from src.utils.youtube import get_transcript, get_video_id
from src.converter.html_converter import HtmlConverter
from pdfminer.high_level import extract_text
from src.types.language import Language
from src.cookies import build_cookie_jar, COOKIES
from src.types.search import SearchResult, ScrapedResult
from src.converter.wiki.url2md_async import async_convert_wiki_to_markdown, remove_markdown_links
from httpx import AsyncClient
from rich.console import Console

# ----------------------------- #
# Logging                       #
# ----------------------------- #

logger = structlog.get_logger(__name__)
console = Console()

MAX_CONTENT_LENGTH = 20000

# 인증서 검증 실패가 발생한 도메인을 캐싱하기 위한 세트
CERTIFICATE_FAILED_DOMAINS = set('https://weather.kweather.co.kr/')

# =============================
# 전역 설정 및 상수
# =============================
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_VIDEOS_URL = "https://google.serper.dev/videos"
SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_NEWS_URL = "https://google.serper.dev/news"
SERPER_SHOPPING_URL = "https://google.serper.dev/shopping"

SEARCH_CATEGORY = {
    "Search": SERPER_SEARCH_URL,
    "Images": SERPER_IMAGES_URL,
    "Videos": SERPER_VIDEOS_URL,
    "Places": SERPER_PLACES_URL,
    "News": SERPER_NEWS_URL,
    "Shopping": SERPER_SHOPPING_URL,
}

EXCLUDE_URLS = ["twitter", "tiktok"]

# 일부 웹사이트는 브라우저가 아닌(예: Python 스크립트) 접근을 기본적으로 차단
# 따라서 브라우저 헤더를 추가해야 함
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}
cookie_jar = build_cookie_jar() 
# =============================
# 전역 비동기 클라이언트 (재사용)
# =============================
# shared_async_client = httpx.AsyncClient(verify=False, headers=HEADERS, timeout=8.0)

shared_async_client = httpx.AsyncClient(
    http2=True,                                # HTTP/2 멀티플렉싱
    limits=httpx.Limits(                       # ← 새 이름
        max_connections=200,
        max_keepalive_connections=40,
        keepalive_expiry=90,                   # 초 단위
    ),
    transport=httpx.AsyncHTTPTransport(        # 필요하면 별도 옵션만 지정
        retries=1,
        local_address=None,
        uds=None,
    ),
    headers=HEADERS,
    cookies=COOKIES,
    timeout=httpx.Timeout(
        connect=3.0,       # 연결 타임아웃 감소
        read=5.0,          # 읽기 타임아웃 감소
        write=3.0,         # 쓰기 타임아웃 추가
        pool=2.0           # 풀 타임아웃 추가
    ),
    follow_redirects=True,                    
    max_redirects=10,                         # 15에서 10으로 조정
)

# =============================
# SerperClient (Async)
# =============================
class SerperClientAsync:
    """Async wrapper around Serper search & scrape endpoints.

    Parameters
    ----------
    base_url : str
        The Serper `search` endpoint (e.g. ``"https://google.serper.dev/search"``).
    api_key : str
        Your Serper API key.
    """

    _SCRAPE_ENDPOINT = "https://scrape.serper.dev/"

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        self.client = shared_async_client

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def search(self, query: str, language: str = "ko") -> Dict[str, Any]:
        """Perform a Serper "search" request and return the raw JSON."""
        lang = Language.from_code(language)
        payload = {"q": query, "hl": lang.query_params["hl"]}
        resp = await self.client.post(self.base_url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def scrape_webpage(self, url: str) -> str:
        """Retrieve raw HTML text via Serper's webpage scraper endpoint."""
        resp = await self.client.post(
            self._SCRAPE_ENDPOINT, headers=self.headers, json={"url": url}
        )
        resp.raise_for_status()
        return resp.text

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def extract_components(language: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten Serper response items into a uniform dictionary.

        The method is generic across all Serper response types (search, places,
        images, videos, shopping, news). It minimises field‑specific boilerplate
        by using handler mappings.
        """

        # Determine result type → list‑key mapping
        result_type: str = data.get("searchParameters", {}).get("type", "search")
        list_key_map: Dict[str, str] = {
            "search": "organic",
            "places": "places",
            "images": "images",
            "videos": "videos",
            "shopping": "shopping",
            "news": "news",
        }
        items: List[Dict[str, Any]] = data.get(list_key_map[result_type], [])

        # Per‑type snippet builders
        def _default(item: Dict[str, Any]) -> str:
            return item.get("snippet", "")

        snippet_builders: Dict[str, Callable[[Dict[str, Any]], str]] = {
            "places": lambda i: (
                f"주소: {i.get('address', '')}, "
                f"카테고리: {i.get('category', '')}, "
                f"평점: {i.get('rating', '')}, "
                f"웹사이트: {i.get('website', '')}"
            ),
            "shopping": lambda i: (
                f"가격: {i.get('price', '')}, 배송비: {i.get('delivery', '')}"
            ),
        }
        snippet_for: Callable[[Dict[str, Any]], str] = snippet_builders.get(
            result_type, _default
        )

        # Extract shared fields with minimal duplication
        titles, links, snippets, image_urls, dates = [], [], [], [], []
        for item in items:
            titles.append(item.get("title", ""))
            links.append(item.get("link", item.get("website", "")))
            snippets.append(snippet_for(item))
            image_urls.append(item.get("imageUrl", ""))
            dates.append(item.get("date", ""))

        return {
            "query": data.get("searchParameters", {}).get("q", ""),
            "language": language,
            "count": len(items),
            "titles": titles,
            "links": links,
            "snippets": snippets,
            "image_urls": image_urls,
            "dates": dates,
            "type": result_type,
        }



# =============================
# NaverClient (Async)
# =============================
class NaverClientAsync:
    def __init__(self, endpoint: str, client_id: str, client_secret: str):
        """
        endpoint: 'News' -> 'news', 'Search' -> 'webkr'
        """
        if endpoint == "News":
            endpoint = "news"
        elif endpoint == "Search":
            endpoint = "webkr"

        self.endpoint = endpoint
        self.client_id = client_id
        self.client_secret = client_secret

    async def search(self, query: str) -> dict:
        url = f"https://openapi.naver.com/v1/search/{self.endpoint}?query={query}"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        # 전역 client 사용
        response = await shared_async_client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {}


# =============================
# 웹 스크래퍼 (Async)
# =============================
class WebScraperAsync:
    def __init__(self, category: str="Search"):
        self.category = category
        self.serper_async = SerperClientAsync(
            base_url=SEARCH_CATEGORY.get(self.category, SERPER_SEARCH_URL),
            api_key=SERPER_API_KEY
        )
        self.html_converter = HtmlConverter()

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            # 최대 20페이지까지만 추출
            max_pages = min(20, len(doc))
            text = "".join(doc[i].get_text() for i in range(max_pages))  # MuPDF 코어(C) ↑
        return text

    async def get_webpage_async_cloudscraper(self, url):
        """
        비동기적으로 웹페이지를 스크래핑하는 함수
        """
        # CloudScraper 함수를 별도 스레드에서 실행
        scraper = cloudscraper.create_scraper()
        
        # 동기 함수를 비동기적으로 실행
        response = await asyncio.to_thread(scraper.get, url)
        
        return response

    async def should_skip(self, url: str) -> bool:
        # 이미 인증서 검증에 실패한 도메인인지 확인
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain in CERTIFICATE_FAILED_DOMAINS:
            logger.info("certificate_failed_domain", url=url, message="이전에 인증서 검증에 실패한 도메인")
            return True, "certificate_failed_domain"

        try:
            # HEAD로 먼저 시도
            head = await shared_async_client.head(url, follow_redirects=True)
        except httpx.HTTPStatusError:
            # 일부 서버는 HEAD 미지원 → Range 0-0 GET으로 헤더만
            head = await shared_async_client.get(
                url,
                follow_redirects=True,
                headers={"Range": "bytes=0-0"},
            )
        except Exception as e:
            # SSL 인증서 오류 문자열 검사
            error_str = str(e).lower()
            if "ssl" in error_str or "certificate" in error_str:
                CERTIFICATE_FAILED_DOMAINS.add(domain)
                logger.info("ssl_error", url=url, message=f"SSL 인증서 검증 실패: {e}")
                return True, "ssl_error"
            return True, str(e)

        ct = head.headers.get("content-type", "").lower()

        # ① 이미지·영상·오디오 + zip + octet-stream → 즉시 스킵
        if ct.startswith((
            "image/",            # image/png, image/jpeg …
            "video/",            # video/mp4 …
            "audio/",            # audio/mpeg …
            "application/zip",   # application/zip; charset=binary …
            "application/octet-stream",
        )):
            return True, ct

        # ② 대용량 PDF(50 MB↑)도 스킵
        if ct.startswith("application/pdf"):
            size = int(head.headers.get("content-length", 0))
            if size > 50 * 1024 * 1024:
                return True, ct

        return False, ct

    def _remove_surrogates(self, text: str) -> str:
        """유니코드 서러게이트 문자를 효율적으로 제거"""
        if not text:
            return ""
        
        # encode/decode 방식으로 서러게이트 문자 처리 (for 루프보다 훨씬 빠름)
        return text.encode('utf-8', 'ignore').decode('utf-8')

    async def _fetch_html(self, url: str) -> Union[Tuple[bytes, BeautifulSoup], Tuple[None, None]]:
        # EXCLUDE_URLS 확인
        for ex_str in EXCLUDE_URLS:
            if ex_str in url:
                logger.info("excluded_url", url=url, message="static excluded url found.")
                return None, True

        try:
            is_skip, content_type = await self.should_skip(url)
            if is_skip:
                return None, True

            resp = await shared_async_client.get(url)
            # resp = await self.get_webpage_async_cloudscraper(url)
            
            console.print(f"[blue bold]--------------------------------")
            console.print(f"[blue bold]URL: {url}")
            if resp.status_code == 200:
                console.print(f"[blue bold]Content-Type: {content_type}")

                content_length = int(resp.headers.get('content-length', 0))
                content_length_mb = content_length / (1024 * 1024)
                console.print(f"[blue bold]Content-Length: {content_length_mb:.2f} MB")

                if content_type.startswith("application/pdf"):
                    # text = await asyncio.to_thread(self._extract_pdf_text, resp.content)
                    # text = self._remove_surrogates(text[:MAX_CONTENT_LENGTH])
                    text = 'test'
                elif content_type.startswith("text/html"):
                    
                    # if content_length_mb > 4:
                    #     html_str = resp.text[:500000]  # Maximum 500KB
                    # else:
                    #     html_str = resp.text
                    
                    # try:
                    #     markdownify_result = await asyncio.wait_for(
                    #         asyncio.to_thread(self.html_converter.convert_string, html_str, url=url),
                    #         timeout=3.0
                    #     )
                    #     text = markdownify_result.markdown.strip()
                    #     text = text[:MAX_CONTENT_LENGTH]
                    #     text = remove_markdown_links(text)
                    # except Exception as e:
                    #     logger.warning("html_converter_error", messages=f"HTML 변환 오류: {e}", url=url, content_length_mb=content_length_mb, content_type=content_type)
                    #     text = ""
                    text = 'test'
                else:
                    text = ""

                if len(text) > 0:
                    console.print(f"[green bold]Content: {text[:100]}...\nNumber of characters: {len(text)}")
                    console.print(f"[red bold]--------------------------------")
                    return text, False
                else:
                    console.print(f"[red bold]페이지 내용이 없습니다.")
                    console.print(f"[red bold]--------------------------------")
                    return None, True
            else:
                console.print(f"[red bold]HTTP 상태 코드: {resp.status_code}")
                console.print(f"[red bold]--------------------------------")
                return None, True
        except Exception as e:
            console.print(f"[red bold]오류: {e}")
            console.print(f"[red bold]--------------------------------")
            logger.warning("fetch_html_error", messages=f"HTML 페이지 가져오기 오류: {e}", url=url)
            return None, True

    async def scrape_url_async(self, url: str, rule: int = 0) -> str:
        is_excluded = False
        if rule == 0:
            content, is_excluded = await self._fetch_html(url)
            if not content:
                return "", is_excluded
        else:
            console.print(f"[red bold]--------------------------------")
            console.print(f"[red bold]URL: {url} 재시도 시작 (serper-webpage api)")
            try:
                content = await self.serper_async.scrape_webpage(url)
                content = json.loads(content)['text']
                content = content[:MAX_CONTENT_LENGTH]
                console.print(f"[blue bold]Content: {content[:100]}...\nNumber of characters: {len(content)}")
                console.print(f"[red bold]--------------------------------")
            except Exception as e:
                content = ""
                console.print("[red bold]재시도 실패-------------------------")
                console.print(f"[red bold]--------------------------------")
        return content, is_excluded

# =============================
# WebContentFetcher (Async) - 검색 + 스크래핑 종합
# =============================
class WebContentFetcherAsync:
    """Perform a Google + Naver search **and** scrape the resulting pages.

    The class delegates low-level work to the following collaborators which
    **must** be supplied from the caller. This keeps the class free from
    concrete HTTP frameworks or environment specifics and therefore easy to
    unit-test.

    Parameters
    ----------
    language : str
        Two-letter language code; e.g. ``"ko"`` or ``"en"``.
    query : str
        User search query.
    category : str
        One of ``"Search"``, ``"News"``, ``"Images"``, etc.
    max_results : int, default=6
        Upper bound on the number of search hits returned to the caller.
    """
    def __init__(
        self,
        query: str,
        category: str="Search",
        language: str="en",
        max_results: int=30
    ):
        self.language = language
        self.query = query
        self.category = category
        self.max_results = max_results

        # 비동기 검색 클라이언트
        self.serper = SerperClientAsync(
            base_url=SEARCH_CATEGORY.get(self.category, SERPER_SEARCH_URL),
            api_key=SERPER_API_KEY
        )
        self.naver = NaverClientAsync(
            endpoint=self.category,
            client_id=NAVER_CLIENT_ID,
            client_secret=NAVER_CLIENT_SECRET
        )
        self.scraper = WebScraperAsync(category=self.category)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    async def search(self) -> List[SearchResult]:
        """Return *deduplicated* Google+Naver results (no scraping)."""
        serper_raw, naver_raw = await self._perform_parallel_searches()
        serper_hits = self._flatten_serper_payload(serper_raw)

        hits: List[SearchResult]
        if naver_raw:
            naver_hits = self._parse_naver_payload(naver_raw)
            hits = self._merge_results(serper_hits, naver_hits)
        else:
            hits = serper_hits

        deduped = self._deduplicate_by_domain(hits)[: self.max_results]
        # logger.info("Search completed - %d unique results", len(deduped))
        return deduped

    async def search_and_scrape(self) -> List[ScrapedResult]:
        """High-level convenience wrapper: ``search`` → ``scrape`` each URL."""
        hits = await self.search()
        scraped = await self._scrape_results(hits)
        return scraped

    # ------------------------------------------------------------------ #
    # Step 1 – Search                                                    #
    # ------------------------------------------------------------------ #

    async def _perform_parallel_searches(self) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Fire Google+Naver searches concurrently."""
        google_task = asyncio.create_task(
            self.serper.search(self.query, language=self.language)
        )

        # # Run Naver only if pre‑conditions match
        # naver_task = None
        # if self._should_use_naver():
        #     naver_task = asyncio.create_task(
        #         self.naver.search(self.query)  # type: ignore[attr-defined]
        #     )
        naver_task = False

        google_result = await google_task
        naver_result = await naver_task if naver_task else None
        return google_result, naver_result

    # ---------------------- Helpers ----------------------------------- #

    def _should_use_naver(self) -> bool:
        return (
            self.naver is not None
            and "ko" in self.language
            and self.category in {"News", "Search"}
        )

    # ------------------------------------------------------------------ #
    # Step 2 – Post‑process search payloads                              #
    # ------------------------------------------------------------------ #

    def _flatten_serper_payload(self, payload: Dict[str, Any]) -> List[SearchResult]:
        components = self.serper.extract_components(self.language, payload)
        return [
            SearchResult(t, l, s, img or "", d or "")
            for t, l, s, img, d in zip(
                components["titles"],
                components["links"],
                components["snippets"],
                components["image_urls"],
                components["dates"],
            )
            if l  # Filter empty links early
        ]

    @staticmethod
    def _parse_naver_payload(payload: Dict[str, Any]) -> List[SearchResult]:
        hits: List[SearchResult] = []
        for item in payload.get("items", []):
            hits.append(
                SearchResult(
                    title=re.sub(r"<[^>]*>", "", item.get("title", "")).strip(),
                    link=item.get("link", ""),
                    snippet=item.get("description", ""),
                    date=item.get("pubDate", ""),
                )
            )
        return hits

    # ---------------- Merge & Deduplicate ----------------------------- #

    def _merge_results(
        self,
        google: Sequence[SearchResult],
        naver: Sequence[SearchResult],
        google_prefix: int = 7,
    ) -> List[SearchResult]:
        """Interleave Google & Naver hits (Ggg NNN GGG…)."""
        return list(google[:google_prefix]) + list(naver) + list(google[google_prefix:])

    def _deduplicate_by_domain(self, hits: Sequence[SearchResult]) -> List[SearchResult]:
        seen: set[str] = set()
        unique: List[SearchResult] = []

        for hit in hits:
            base = self._extract_domain(hit.link)
            if base and base not in seen:
                seen.add(base)
                unique.append(hit)
        return unique

    # ------------------------------------------------------------------ #
    # Step 3 – Scrape                                                    #
    # ------------------------------------------------------------------ #

    async def _scrape_results(self, hits: Sequence[SearchResult]) -> List[ScrapedResult]:
        """Launch concurrent scraping tasks for every search result."""
        tasks = [asyncio.create_task(self._scrape_single(hit)) for hit in hits]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        scraped: List[ScrapedResult] = []
        for item in raw_results:
            if isinstance(item, ScrapedResult) and item.content:
                scraped.append(item)
        # logger.info("Scraping finished – %d pages extracted", len(scraped))
        return scraped

    async def _scrape_single(self, hit: SearchResult) -> ScrapedResult:
        if "namu.wiki" in hit.link:
            content = ""
            return ScrapedResult(**hit.__dict__, content=content)
        # Short‑circuit for YouTube (transcript only)
        if "youtube.com" in hit.link:
            video_id = get_video_id(hit.link)
            content = await get_transcript(video_id)
            content = self.scraper._remove_surrogates(content[:MAX_CONTENT_LENGTH])
            return ScrapedResult(**hit.__dict__, content=content or hit.snippet)

        if "wikipedia.org" in hit.link:
            content = await async_convert_wiki_to_markdown(hit.link)
            content = self.scraper._remove_surrogates(content[:MAX_CONTENT_LENGTH])
            console.print(f"[orange bold]Wikipedia: {content[:100]}...\nNumber of characters: {len(content)}")
            return ScrapedResult(**hit.__dict__, content=content or hit.snippet)

        content, excluded = await self.scraper.scrape_url_async(hit.link, rule=0)

        # Retry with Serper scraper if necessary
        #if not content and not excluded:
        #    content, _ = await self.scraper.scrape_url_async(hit.link, rule=1)

        # Fall back to snippet if everything fails
        if not content:
            content = hit.snippet

        return ScrapedResult(**hit.__dict__, content=content)

    # ------------------------------------------------------------------ #
    # Utility                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Return scheme‑less domain part (e.g. '://example.com')."""
        parsed = urlparse(url)
        base = "://" + parsed.netloc + parsed.path
        return (
            base.replace("://www.", "://")
            .replace("://m.", "://")
            .rstrip("/")
            .lower()
        )


# =============================
# 실제 호출 함수
# =============================

async def get_page_sources_from_query(user_message: str, category: str="Search", target_language: str="en"):
    """
    language_str: "Korean" / "English" 등
    user_message: 사용자 메시지
    category: "Search" / "News" / "Images" / "Videos" / "Shopping"
    """
    fetcher = WebContentFetcherAsync(user_message, category, target_language, max_results=14)
    results = await fetcher.search()
    return {"count": len(results), "results": results}

async def get_web_contents_from_source(user_message: str, category: str="Search", target_language: str="en", search_response: dict=None):
    """
    메인 비동기 검색/스크래핑 함수
    """

    fetcher = WebContentFetcherAsync(user_message, category, target_language, max_results=14)

    # 딕셔너리 리스트를 SearchResult 객체 리스트로 변환
    search_results = [SearchResult(
        title=item.get('title', ''),
        link=item.get('link', ''),
        snippet=item.get('snippet', ''),
        image_url=item.get('image_url', ''),
        date=item.get('date', '')
    ) for item in search_response['results']]
    
    scraped_contents = await fetcher._scrape_results(search_results)
    # link 키를 url로 변환
    converted_contents = []
    for item in scraped_contents:
        item_dict = item.__dict__.copy()
        if 'link' in item_dict:
           item_dict['url'] = item_dict.pop('link')
        converted_contents.append(item_dict)
    return converted_contents
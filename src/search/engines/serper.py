import time
import asyncio
from typing import Any, Dict, List, Callable
from src.types.language import Language
from simhash import Simhash
from rich.console import Console

console = Console()

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_VIDEOS_URL = "https://google.serper.dev/videos"
SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_NEWS_URL = "https://google.serper.dev/news"
SERPER_SHOPPING_URL = "https://google.serper.dev/shopping"
SERPER_SCHOLAR_URL = "https://google.serper.dev/scholar"
SEARCH_CATEGORY = {
    "Search": SERPER_SEARCH_URL,
    "Images": SERPER_IMAGES_URL,
    "Videos": SERPER_VIDEOS_URL,
    "Places": SERPER_PLACES_URL,
    "News": SERPER_NEWS_URL,
    "Shopping": SERPER_SHOPPING_URL,
    "Scholar": SERPER_SCHOLAR_URL,
}
# =============================
# SerperClient (Async)
# =============================
class SerperClientAsync:
    """Async wrapper around Serper search & scrape endpoints.

    Parameters
    ----------
    api_key : str
        Your Serper API key.
    """

    _SCRAPE_ENDPOINT = "https://scrape.serper.dev/"

    def __init__(self, 
                 browser_client, 
                 api_key: str, 
                 num_output_per_query: int = 20, 
                 content_type_timeout: float = 0.25,
                 use_youtube_transcript: bool = True,
                 top_k = None,
                 exclude_domain: List[str] = []):
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        self.client = browser_client
        self.num_output_per_query = num_output_per_query
        self.content_type_timeout = content_type_timeout
        self.use_youtube_transcript = use_youtube_transcript
        self.top_k = top_k
        self.exclude_domain = exclude_domain

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def single_search(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform a Serper "search" request and return the raw JSON."""
        lang = Language.from_code(payload['language'])
        period = payload['period']
        serper_payload = {"q": payload['query'], "num": self.num_output_per_query, "hl": lang.query_params["hl"]}

        if period == "Past hour":
            serper_payload["tbs"] = "qdr:h"
        elif period == "Past 24 hours":
            serper_payload["tbs"] = "qdr:d"
        elif period == "Past week":
            serper_payload["tbs"] = "qdr:w"
        elif period == "Past month":
            serper_payload["tbs"] = "qdr:m"
        elif period == "Past year":
            serper_payload["tbs"] = "qdr:y"

        url = SEARCH_CATEGORY[payload['type']]

        resp = await self.client.get(url, headers=self.headers, params=serper_payload)
        if resp.status_code != 200:
            return []
        else:
            return self.extract_components(payload['language'], resp.json())

    async def multiple_search(self, payloads: List[Dict[str, Any]], simhash_threshold: int = 20) -> List[Dict[str, Any]]:
        """
        Perform multiple Serper "search" requests, merge, and deduplicate results.
        Deduplication is done first by URL, then by SimHash of the snippet.
        """
        start_time = time.time()
        results_from_searches = await asyncio.gather(
            *[self.single_search(payload) for payload in payloads]
        )

        if self.top_k is not None:
            num_iters = len(results_from_searches)
            split_val = self.top_k // num_iters
        
        raw_merged_results = []
        for i, result_list in enumerate(results_from_searches):
            if self.top_k is not None:
                raw_merged_results.extend(result_list[:split_val])
            else:
                raw_merged_results.extend(result_list)

        console.log(f"[pink bold]WebSearch-Search: {time.time() - start_time:.2f} seconds")

        start_time = time.time()
        url_deduplicated_results_dict = {}
        for result in raw_merged_results:
            url = result.get('url')
            if url: 
                 if url not in url_deduplicated_results_dict:
                    url_deduplicated_results_dict[url] = result
            else:
                unique_key_for_no_url_item = f"no_url_{len(url_deduplicated_results_dict)}_{id(result)}" # Add id for more uniqueness
                url_deduplicated_results_dict[unique_key_for_no_url_item] = result

        url_deduplicated_results = list(url_deduplicated_results_dict.values())

        if not url_deduplicated_results:
            return []

        final_results = []
        hashes = []
        num_duplicate = 0

        for item in url_deduplicated_results:
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            content = (title + " " + snippet).strip()
            if not content: 
                final_results.append(item)
                continue

            current_hash = Simhash(content.split()) 

            is_duplicate = False
            for existing_hash in hashes:
                dist = current_hash.distance(existing_hash)
                if dist <= simhash_threshold:
                    is_duplicate = True
                    num_duplicate += 1
                    break
            
            if not is_duplicate:
                final_results.append(item)
                hashes.append(current_hash)
        
        console.log(f"[pink bold]WebSearch-Deduplication: {time.time() - start_time:.2f} seconds")
        return final_results
    
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
    def extract_components(self, language: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten Serper response items into a uniform dictionary.

        The method is generic across all Serper response types (search, places,
        images, videos, shopping, news). It minimises field‑specific boilerplate
        by using handler mappings.
        """

        if self.use_youtube_transcript:
            self.exclude_domain.append("youtube.com")

        # Determine result type → list‑key mapping
        result_type: str = data.get("searchParameters", {}).get("type", "search")
        list_key_map: Dict[str, str] = {
            "search": "organic",
            "places": "places",
            "images": "images",
            "videos": "videos",
            "shopping": "shopping",
            "news": "news",
            "scholar": "organic",
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
            "scholar": lambda i: (
                f"스니펫: {i.get('snippet', '')}, "
                f"출판정보: {i.get('publicationInfo', '')}, "
                f"인용횟수: {i.get('citedBy', '')}, "
                f"출판일: {i.get('year', '')}"
            ),
        }
        snippet_for: Callable[[Dict[str, Any]], str] = snippet_builders.get(
            result_type, _default
        )

        # Extract shared fields with minimal duplication
        results = []
        for item in items:
            url = item.get("link", item.get("website", ""))
            if any(domain in url for domain in self.exclude_domain):
                continue
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", item.get("website", "")),
                "snippet": snippet_for(item),
                "image_url": item.get("imageUrl", ""),
                "date": item.get("date", ""),
                'language': language,
                'type': result_type,
                'pdf_url': item.get('pdfUrl', ''),
            })

        return results
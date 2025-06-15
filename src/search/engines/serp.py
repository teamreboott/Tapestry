import time
import asyncio
from typing import Any, Dict, List, Callable
from src.types.language import Language
from simhash import Simhash
from rich.console import Console

console = Console()

EXCLUDE_DOMAIN = [
    "namu.wiki", "cio.com", "FileDown", "Download", "down", "lilys.ai",
    "facebook.com", "instagram.com", "twitter.com", "tiktok.com",
]

SERP_URL = "https://serpapi.com/search"
# =============================
# SerpClient (Async)
# =============================
class SerpClientAsync:
    """Async wrapper around Serp search & scrape endpoints.

    Parameters
    ----------
    api_key : str
        Your Serp API key.
    """
    def __init__(self, 
                 browser_client, 
                 api_key: str, 
                 num_output_per_query: int = 20, 
                 content_type_timeout: float = 0.25,
                 use_youtube_transcript: bool = True,
                 top_k = None,
                 exclude_domain: List[str] = []):
        self.client = browser_client
        self.api_key = api_key
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
        serp_payload = {"q": payload['query'], "num": self.num_output_per_query, "hl": lang.query_params["hl"], "api_key": self.api_key}

        if payload['type'] == "News":
            serp_payload['engine'] = 'google_news'
        elif payload['type'] == 'Videos':
            serp_payload['engine'] = 'google_videos'
        elif payload['type'] == 'Scholar':
            serp_payload['engine'] = 'google_scholar'
        elif payload['type'] == 'Shopping':
            serp_payload['engine'] = 'google_shopping'
        elif payload['type'] == 'Places':
            serp_payload['engine'] = 'google_maps'
        elif payload['type'] == 'Images':
            serp_payload['engine'] = 'google_images'

        if period == "Past hour":
            serp_payload["tbs"] = "qdr:h"
        elif period == "Past 24 hours":
            serp_payload["tbs"] = "qdr:d"
        elif period == "Past week":
            serp_payload["tbs"] = "qdr:w"
        elif period == "Past month":
            serp_payload["tbs"] = "qdr:m"
        elif period == "Past year":
            serp_payload["tbs"] = "qdr:y"

        url = SERP_URL

        resp = await self.client.get(url, params=serp_payload)
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def extract_components(self, language: str, data: Dict[str, Any]) -> Dict[str, Any]:

        if self.use_youtube_transcript:
            self.exclude_domain.append("youtube.com")

        # Determine result type → list‑key mapping
        result_type: str = data.get("searchParameters", {}).get("type", "search")
        list_key_map: Dict[str, str] = {
            "search": "organic_results",
            "places": "local_results",
            "images": "images_results",
            "videos": "video_results",
            "shopping": "shopping_results",
            "news": "news_results",
            "scholar": "organic_results",
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
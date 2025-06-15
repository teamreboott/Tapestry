import time
import asyncio
from typing import Any, Dict, List, Callable
from src.types.language import Language
from simhash import Simhash
from rich.console import Console

console = Console()

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_IMAGES_URL = "https://api.search.brave.com/res/v1/images/search"
BRAVE_VIDEOS_URL = "https://api.search.brave.com/res/v1/videos/search"
BRAVE_NEWS_URL = "https://api.search.brave.com/res/v1/news/search"
SEARCH_CATEGORY = {
    "Search": BRAVE_SEARCH_URL,
    "Images": BRAVE_IMAGES_URL,
    "Videos": BRAVE_VIDEOS_URL,
    "News": BRAVE_NEWS_URL,
    "Scholar": BRAVE_SEARCH_URL,
    "Shopping": BRAVE_SEARCH_URL,
    "Places": BRAVE_SEARCH_URL,
}

# =============================
# BraveClient (Async)
# =============================
class BraveClientAsync:
    """Async wrapper around Brave search endpoints.

    Parameters
    ----------
    api_key : str
        Your Brave API key.
    """

    def __init__(self, 
                 browser_client, 
                 api_key: str, 
                 num_output_per_query: int = 20, 
                 content_type_timeout: float = 0.25,
                 use_youtube_transcript: bool = True,
                 top_k = None,
                 exclude_domain: List[str] = []):

        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "x-subscription-token": api_key
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
        brave_payload = {"q": payload['query'], "count": self.num_output_per_query, "search_lang": lang.query_params["hl"]}

        url = SEARCH_CATEGORY[payload['type']]

        resp = await self.client.get(url, headers=self.headers, params=brave_payload)
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
        search_type = data.get("type", "search")

        if self.use_youtube_transcript:
            self.exclude_domain.append("youtube.com")

        results = []

        if search_type == "search":
            web_items = data.get("web", {}).get("results", [])
            video_items = data.get("videos", {}).get("results", [])

            for web_item in web_items:
                title = web_item.get("title", "")
                url = web_item.get("url", "")
                snippet = web_item.get("description", "")
                web_language = web_item.get("language", "")
                date = web_item.get("age", "")

                if any(domain in url for domain in self.exclude_domain):
                    continue

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "image_url": "",
                    "language": web_language,
                    "date": date,
                    "type": search_type,
                    "pdf_url": "",
                })

            if self.use_youtube_transcript:
                for video_item in video_items:
                    title = video_item.get("title", "")
                    url = video_item.get("url", "")
                    snippet = video_item.get("description", "")
                    snippet += f"\n\n{video_item.get('video', '')}"
                    video_language = language
                    date = video_item.get("age", "")

                    if any(domain in url for domain in self.exclude_domain):
                        continue

                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "image_url": "",
                        "language": video_language,
                        "date": date,
                        "type": search_type,
                        "pdf_url": "",
                    })



        elif search_type == "images":
            items = data.get("results", [])

            for item in items:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("description", "")
                image_url = item.get("thumbnail", "")
                if image_url != "":
                    image_url = image_url.get("src", "")
                date = item.get("age", "")

                if any(domain in url for domain in self.exclude_domain):
                    continue

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "image_url": image_url,
                    "language": language,
                    "date": date,
                    "type": search_type,
                    "pdf_url": "",
                })
        elif search_type == "videos":
            items = data.get("results", [])

            for item in items:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("description", "")
                snippet += f"\n\n{item.get('video', '')}"
                video_language = language
                date = item.get("age", "")

                if any(domain in url for domain in self.exclude_domain):
                    continue

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "image_url": "",
                    "language": video_language,
                    "date": date,
                    "type": search_type,
                    "pdf_url": "",
                })
        elif search_type == "news":
            items = data.get("results", [])

            for item in items:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("description", "")
                web_language = item.get("language", "")
                date = item.get("age", "")

                if any(domain in url for domain in self.exclude_domain):
                    continue

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "image_url": "",
                    "language": web_language,
                    "date": date,
                    "type": search_type,
                    "pdf_url": "",
                })

        return results
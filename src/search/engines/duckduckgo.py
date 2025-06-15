import asyncio
import time
from src.types.language import Language
from typing import Any, Dict, List, Callable
from duckduckgo_search import DDGS
from simhash import Simhash
from rich.console import Console

console = Console()


class DuckDuckGoClientAsync:
    """Async wrapper around DuckDuckGo search & scrape endpoints.

    Parameters
    ----------
    api_key : str
        Your DuckDuckGo API key.
    """

    def __init__(self,
                 num_output_per_query: int = 20, 
                 content_type_timeout: float = 0.25,
                 use_youtube_transcript: bool = True,
                 top_k = None,
                 exclude_domain: List[str] = []):
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

        if payload['period'] == 'Past 24 hours':
            period = 'd'
        elif payload['period'] == 'Past week':
            period = 'w'
        elif payload['period'] == 'Past month':
            period = 'm'
        elif payload['period'] == 'Past year':
            period = 'y'
        else:
            period = None

        # gl-hl
        region = f"{lang.query_params['gl']}-{lang.query_params['hl']}"
        ddgs = DDGS()
        if payload['type'] == 'Search':
            results = ddgs.text(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        elif payload['type'] == 'Images':
            results = ddgs.images(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        elif payload['type'] == 'Videos':
            results = ddgs.videos(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        elif payload['type'] == 'News':
            results = ddgs.news(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        elif payload['type'] == 'Scholar':
            results = ddgs.text(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        elif payload['type'] == 'Shopping':
            results = ddgs.text(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        elif payload['type'] == 'Places':
            results = ddgs.text(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)
        else:
            results = ddgs.text(payload['query'], max_results=self.num_output_per_query, region=region, timelimit=period)     
        return self.extract_components(payload['language'], payload['type'], results)

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
    def extract_components(self, language: str, search_type: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.use_youtube_transcript:
            self.exclude_domain.append("youtube.com")

        results = []
        if search_type == 'Videos':
            for item in data:
                url = item.get('content', '')
                if any(domain in url for domain in self.exclude_domain):
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get('description', ''),
                    "image_url": item.get("embed_url", ""),
                    "date": item.get("published", ""),
                    'language': language,
                    'type': search_type,
                    'pdf_url': item.get('pdfUrl', ''),
                })
        elif search_type == 'Images':
            for item in data:
                url = item.get('url', '')
                if any(domain in url for domain in self.exclude_domain):
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get('body', ''),
                    "image_url": item.get('image', ''),
                    "date": item.get('date', ''),
                    'language': language,
                    'type': search_type,
                    'pdf_url': item.get('pdfUrl', ''),
                })

        elif search_type == 'News':
            for item in data:
                url = item.get('url', '')
                if any(domain in url for domain in self.exclude_domain):
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get('body', ''),
                    "image_url": item.get('image', ''),
                    "date": item.get('date', ''),
                    'language': language,
                    'type': search_type,
                    'pdf_url': item.get('pdfUrl', ''),
                })
        else:
            for item in data:
                url = item.get('href', '')
                if any(domain in url for domain in self.exclude_domain):
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "url": url, 
                    "snippet": item.get('body', ''),
                    "image_url": item.get('image', ''),
                    "date": item.get('date', ''),
                    'language': language,
                    'type': search_type,
                    'pdf_url': item.get('pdfUrl', ''),
                })

        return results
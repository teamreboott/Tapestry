import os
from typing import List
from .brave import BraveClientAsync
from .serp import SerpClientAsync
from .serper import SerperClientAsync
from .duckduckgo import DuckDuckGoClientAsync


def load_search_engine(engine_name: str,
                       browser_client,
                       num_output_per_query: int = 20,
                       content_type_timeout: float = 0.25,
                       use_youtube_transcript: bool = True,
                       top_k = None,
                       exclude_domain: List[str] = []):
    if engine_name == "serper":
        api_key = os.getenv("SERPER_API_KEY")
        return SerperClientAsync(browser_client=browser_client, api_key=api_key, num_output_per_query=num_output_per_query, content_type_timeout=content_type_timeout, use_youtube_transcript=use_youtube_transcript, top_k=top_k, exclude_domain=exclude_domain)
    elif engine_name == "serp":
        api_key = os.getenv("SERP_API_KEY")
        return SerpClientAsync(browser_client=browser_client, api_key=api_key, num_output_per_query=num_output_per_query, content_type_timeout=content_type_timeout, use_youtube_transcript=use_youtube_transcript, top_k=top_k, exclude_domain=exclude_domain)
    elif engine_name == "duckduckgo":
        return DuckDuckGoClientAsync(num_output_per_query=num_output_per_query, content_type_timeout=content_type_timeout, use_youtube_transcript=use_youtube_transcript, top_k=top_k, exclude_domain=exclude_domain)
    elif engine_name == "brave":
        api_key = os.getenv("BRAVE_API_KEY")
        return BraveClientAsync(browser_client=browser_client, api_key=api_key, num_output_per_query=num_output_per_query, content_type_timeout=content_type_timeout, use_youtube_transcript=use_youtube_transcript, top_k=top_k, exclude_domain=exclude_domain)
    else:
        raise ValueError(f"Invalid engine name: {engine_name}")
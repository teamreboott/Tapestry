from . import ContentExtractor
from .medias.youtube.base import get_transcript, get_video_id
from .medias.wiki.url2md_async import async_extract_wiki_content


class YoutubeExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "youtube.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        video_id = get_video_id(url)
        content = await get_transcript(video_id)
        return content


class WikipediaExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "wikipedia.org" in url
    
    async def extract(self, url: str, browser_client) -> str:
        content = await async_extract_wiki_content(url, browser_client)
        return content


MEDIA_EXTRACTORS = {
    "youtube.com": YoutubeExtractor,
    "wikipedia.org": WikipediaExtractor,
}
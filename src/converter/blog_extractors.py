from . import ContentExtractor
from .blogs.naver_blog.url2md_async import async_extract_naver_blog_content
from .blogs.goover_blog.url2md_async import async_extract_goover_blog_content
from .blogs.tistory_blog.url2md_async import async_extract_tistory_blog_content
from .blogs.brunch_blog.url2md_async import async_extract_brunch_blog_content

class NaverBlogExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "blog.naver.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        # URL 변환 로직
        url = url.replace("blog.naver.com", "m.blog.naver.com")
        return await async_extract_naver_blog_content(url, browser_client)
    
class GooverBlogExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "seo.goover.ai" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_goover_blog_content(url, browser_client)
    
class TistoryBlogExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "tistory.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_tistory_blog_content(url, browser_client)
    
class BrunchBlogExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "brunch.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_brunch_blog_content(url, browser_client)
    

BLOG_EXTRACTORS = {
    "blog.naver.com": NaverBlogExtractor,
    "seo.goover.ai": GooverBlogExtractor,
    "tistory.com": TistoryBlogExtractor,
    "brunch.co.kr": BrunchBlogExtractor,
}
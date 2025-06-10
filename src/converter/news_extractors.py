from . import ContentExtractor
from .chosun_news.url2md_async import async_extract_chosun_news_content
from .donga_news.url2md_async import async_extract_donga_news_content
from .nate_news.url2md_async import async_extract_nate_news_content
from .sedaily_news.url2md_async import async_extract_sedaily_news_content
from .kmib_news.url2md_async import async_extract_kmib_news_content
from .aitimes_news.url2md_async import async_extract_aitimes_news_content
from .dongascience_news.url2md_async import async_extract_dongascience_news_content
from .joongang_news.url2md_async import async_extract_joongang_news_content
from .yna_news.url2md_async import async_extract_yna_news_content
from .dt_news.url2md_asnyc import async_extract_dt_news_content
from .mt_news.url2md_async import async_extract_mt_news_content
from .sbs_news.url2md_async import async_extract_sbs_news_content
from .ohmynews_news.url2md_async import async_extract_ohmynews_content

class ChosunExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "chosun.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_chosun_news_content(url, browser_client)

class DongaExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "donga.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_donga_news_content(url, browser_client)

class NateNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "news.nate.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_nate_news_content(url, browser_client)
    

class SedailyNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "sedaily.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_sedaily_news_content(url, browser_client)
    

class KmibNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "kmib.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_kmib_news_content(url, browser_client)

class AitimesNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "aitimes.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_aitimes_news_content(url, browser_client)
    

class DongascienceNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "dongascience.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        url = url.replace("m.dongascience.com", "www.dongascience.com")
        return await async_extract_dongascience_news_content(url, browser_client)

class JoongangNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "joongang.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_joongang_news_content(url, browser_client)


class YnaNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "yna.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_yna_news_content(url, browser_client)


class DtNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "dt.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_dt_news_content(url, browser_client)

class MtNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "mt.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_mt_news_content(url, browser_client)

class SbsNewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "news.sbs.co.kr" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_sbs_news_content(url, browser_client)

class OhmynewsExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return "ohmynews.com" in url
    
    async def extract(self, url: str, browser_client) -> str:
        return await async_extract_ohmynews_content(url, browser_client)

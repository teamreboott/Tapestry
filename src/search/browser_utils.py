from fake_useragent import UserAgent
import httpx
import ssl
import certifi

HEADTER_TEMPLATE = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.google.com/",
}
ctx = ssl.create_default_context(cafile=certifi.where())
ua = UserAgent(platforms='desktop')

def load_browser_client():
    HEADTER_TEMPLATE["User-Agent"] = ua.random
    
    browser_client = httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(
            max_connections=200,
            max_keepalive_connections=40,
            keepalive_expiry=90,
        ),
        transport=httpx.AsyncHTTPTransport(
            retries=1,
            local_address=None,
            uds=None,
        ),
        headers=HEADTER_TEMPLATE,
        follow_redirects=True,                    
        max_redirects=5,
        verify=ctx,
    )
    return browser_client
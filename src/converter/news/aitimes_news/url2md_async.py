from bs4 import BeautifulSoup
import re

async def async_extract_aitimes_news_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        content_elm = html.find(attrs={'id': 'article-view-content-div'})
        result = re.sub(r'\n\n+', '\n', content_elm.text)
        result = result.strip()
    except Exception as e:
        result = ""
    finally:
        return result
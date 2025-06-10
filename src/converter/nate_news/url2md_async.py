from bs4 import BeautifulSoup
import re

async def async_extract_nate_news_content(url, browser_client):
    url = url.replace("m.news.nate.com", "news.nate.com")
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        content_elm = html.find(attrs={"class": lambda x: x and any(
                    keyword in str(x).lower() for keyword in [
                        "content_view",
                    ]
                )})
        result = re.sub(r'\n\n+', '\n', content_elm.text)
        result = result.strip()
    except Exception as e:
        result = ""
    finally:
        # await client.aclose()
        return result
from bs4 import BeautifulSoup
import re

async def async_extract_dongascience_news_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        content_elm = html.find(attrs={"id": lambda x: x and any(
                    keyword in str(x).lower() for keyword in [
                        "contents",
                    ]
                )})
        result = re.sub(r'\n\n+', '\n', content_elm.text)
        end_index = result.find("Copyright")
        result = result[:end_index]
        result = result.strip()
    except Exception as e:
        result = ""
    finally:
        return result
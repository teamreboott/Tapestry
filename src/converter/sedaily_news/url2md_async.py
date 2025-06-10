from bs4 import BeautifulSoup
import re

async def async_extract_sedaily_news_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        content_elm = html.find(attrs={"class": lambda x: x and any(
                    keyword in str(x).lower() for keyword in [
                        "article_con",
                    ]
                )})
        result = re.sub(r'\n\n+', '\n', content_elm.text)
        result = result.strip()
        end_index = result.find("< 저작권자 ⓒ 서울경제, 무단 전재 및 재배포 금지 >")
        result = result[:end_index]
    except Exception as e:
        result = ""
    finally:
        return result
from bs4 import BeautifulSoup
import re

async def async_extract_mt_news_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        content_elm = html.find(attrs={"class": lambda x: x and any(
                    keyword in str(x).lower() for keyword in [
                        "article_view",
                    ]
                )})
        result = re.sub(r'\n\n+', '\n', content_elm.text)
        end_idx = result.find("<저작권자 © ‘돈이 보이는 리얼타임 뉴스’ 머니투데이. 무단전재 및 재배포, AI학습 이용 금지>")
        result = result[:end_idx].strip()
    except Exception as e:
        result = ""
    finally:
        return result
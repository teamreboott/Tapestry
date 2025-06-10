from bs4 import BeautifulSoup
import re

async def async_extract_naver_blog_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        # \n 2개 이상 있는 것들 제거
        result = re.sub(r'\n\n+', '\n', html.text)
        try:
            title = result.split("\n")[0]
        except Exception as e:
            title = ""
        start_idx = result.find("신고하기") if result.find("신고하기") != -1 else 0
        end_idx = result.find("공감한 사람 보러가기") if result.find("공감한 사람 보러가기") != -1 else len(result)
        result = title + "\n" + result[start_idx:end_idx].replace("신고하기", "").strip()
    except Exception as e:
        result = ""
    finally:
        # await client.aclose()
        return result
from bs4 import BeautifulSoup
import re

async def async_extract_bbc_news_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        # BBC는 data-component="text-block" 사용
        content_elements = html.find_all(attrs={"data-component": "text-block"})
        
        # 모든 텍스트 블록의 내용을 합치기
        full_text = ""
        for element in content_elements:
            full_text += element.get_text() + "\n"
        
        # 연속된 줄바꿈 정리
        result = re.sub(r'\n\n+', '\n\n', full_text)
        result = result.strip()
        
    except Exception as e:
        result = ""
    finally:
        return result

if __name__ == "__main__":
    import asyncio
    import httpx

    client = httpx.AsyncClient()
    result = asyncio.run(async_extract_bbc_news_content("https://www.bbc.com/news/articles/c3w463pyj90o", client))
    print(result)
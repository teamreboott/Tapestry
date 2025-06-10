from bs4 import BeautifulSoup
import re

async def async_extract_tistory_blog_content(url, browser_client):
    ARTICLE_DIV_CLASS = "tt_article_useless_p_margin"
    result = ""
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")

        # 0️⃣  글 제목 (본문보다 먼저 뽑아 둔다)
        title = soup.select_one("h1")
        title_txt = title.get_text(strip=True) if title else ""

        # 1️⃣  articleTemplate <template> 블록 안쪽까지 재파싱
        template = soup.select_one('template[x-ref="articleTemplate"]')
        article_dom = (
            BeautifulSoup(template.decode_contents(), "html.parser")
            if template else soup
        )

        # 2️⃣  본문 컨테이너 찾기 (class membership 테스트 이용)
        content_div = (
            article_dom.select_one(f"div.{ARTICLE_DIV_CLASS}") or
            article_dom.find("div", class_=ARTICLE_DIV_CLASS) or
            article_dom.find(attrs={"class": re.compile(r"\b(article|content|post)\b")})
        )
        if not content_div:
            return ""

        # 3️⃣  텍스트 정리 – 단락 간 \n 하나만 남기고 모두 삭제
        raw = content_div.get_text("\n", strip=True)
        cleaned = re.sub(r"\n{2,}", "\n", raw)

        # 4️⃣  제목이 없으면 본문 첫 줄을 대신 사용
        if not title_txt:
            title_txt = cleaned.split("\n", 1)[0]

        result = title_txt + "\n" + cleaned
        result = result.strip()
    except Exception as e:
        result = ""
    finally:
        return result
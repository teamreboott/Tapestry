import httpx
from bs4 import BeautifulSoup
import pandas as pd
import re
import html2text
import asyncio
from urllib.parse import urljoin
from io import StringIO

async def async_extract_wikipedia_content(url, browser_client):
    """
    위키피디아 URL에서 제목, 목차, 텍스트, 표 등을 비동기식으로 추출합니다.
    
    Args:
        url (str): 위키피디아 URL
        session (aiohttp.ClientSession, optional): 재사용할 세션
        
    Returns:
        dict: 제목, 목차, 텍스트, 표 등을 포함한 사전
    """
    
    try:
        # 페이지 요청
        response = await browser_client.get(url)
        if response.status != 200:
            return ""
        # BeautifulSoup 객체 생성
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 결과를 저장할 사전
        result = {}
        
        # 1. 제목 추출
        title = soup.find('h1', {'id': 'firstHeading'})
        result['title'] = title.text if title else "제목을 찾을 수 없습니다."
        
        # 2. 목차 추출
        toc = soup.find('div', {'id': 'toc'})
        if toc:
            toc_items = toc.find_all('li', {'class': 'toclevel-1'})
            result['table_of_contents'] = [item.get_text(strip=True) for item in toc_items]
        else:
            # 목차가 없는 경우 헤딩을 추출
            headings = soup.find_all(['h2', 'h3', 'h4'])
            result['table_of_contents'] = [h.get_text(strip=True) for h in headings if 'id' in h.attrs and not h.get_text(strip=True).startswith('참고')]
        
        # 3. 본문 텍스트 추출
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if content_div:
            # 참고 문헌 및 외부 링크 섹션 제외
            paragraphs = []
            current_element = content_div.find('p')
            
            while current_element:
                if current_element.name == 'p':
                    text = current_element.get_text(strip=True)
                    if text:  # 빈 단락 건너뛰기
                        paragraphs.append(text)
                elif current_element.name in ['h2', 'h3', 'h4']:
                    heading_text = current_element.get_text(strip=True)
                    if heading_text in ['각주', '참고 문헌', '외부 링크', '같이 보기']:
                        break
                
                current_element = current_element.find_next()
            
            result['text'] = paragraphs
        else:
            result['text'] = "본문을 찾을 수 없습니다."
        
        # 4. 표 추출
        tables = content_div.find_all('table', {'class': 'wikitable'})
        result['tables'] = []
        
        for idx, table in enumerate(tables):
            try:
                # pandas로 표 변환
                df = pd.read_html(str(table))[0]
                result['tables'].append({
                    'table_number': idx + 1,
                    'data': df.to_dict(orient='records')
                })
            except Exception as e:
                result['tables'].append({
                    'table_number': idx + 1,
                    'error': f"표 변환 오류: {str(e)}"
                })
        
        # 5. 인포박스 추출 (있는 경우)
        infobox = soup.find('table', {'class': re.compile(r'infobox')})
        if infobox:
            info_rows = []
            for row in infobox.find_all('tr'):
                header = row.find('th')
                value = row.find('td')
                if header and value:
                    info_rows.append({
                        'field': header.get_text(strip=True),
                        'value': value.get_text(strip=True)
                    })
            result['infobox'] = info_rows
        
        return result
    
    except Exception as e:
        return ""


async def async_convert_to_markdown(url, browser_client=None):
    try:
        # 페이지 요청
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""   
        # BeautifulSoup 객체 생성
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 메타데이터를 저장할 사전
        metadata = {
            'title': '',
            'images': [],
            'language': url.split('/')[2].split('.')[0]  # URL에서 언어 코드 추출 (ko, en 등)
        }
        
        # 제목 추출
        title_elem = soup.find('h1', {'id': 'firstHeading'})
        if title_elem:
            metadata['title'] = title_elem.text.strip()
        
        # 필요없는 요소 제거
        for element in soup.select('.mw-editsection, .mw-empty-elt, .noprint, #mw-navigation, #mw-panel, #footer, #catlinks, .mw-jump-link, #mw-head'):
            if element:
                element.decompose()
        
        # 본문 콘텐츠만 추출
        content = soup.find('div', {'id': 'mw-content-text'})
        if not content:
            return ""
        
        # 테이블 처리
        for table in content.find_all('table', {'class': 'wikitable'}):
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                
                # 마크다운 테이블 형식으로 변환
                md_table = df.to_markdown(index=False)
                
                # 원본 테이블을 마크다운 테이블로 대체
                table.replace_with(BeautifulSoup(f"<pre>{md_table}</pre>", 'html.parser'))
            except Exception as e:
                # 테이블 변환 실패 시 메시지 추가
                table.replace_with(BeautifulSoup(f"<p>*테이블 변환 실패: {str(e)}*</p>", 'html.parser'))
        
        # HTML을 마크다운으로 변환
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # 줄 바꿈 방지
        h.unicode_snob = True  # 유니코드 문자 유지
        h.skip_internal_links = False
        h.inline_links = True
        h.protect_links = True
        
        # 제목 추가
        markdown_content = f"# {metadata['title']}\n\n"
        
        # 본문 변환
        markdown_content += h.handle(str(content))
        
        # 마크다운 후처리
        # 1. 과도한 빈 줄 제거
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        # 2. 참조 마크 정리 ([1], [2] 등)
        markdown_content = re.sub(r'\[\d+\]', '', markdown_content)
        
        # 3. 편집 링크 제거
        markdown_content = re.sub(r'\[편집\]\(.*?\)', '', markdown_content)
        markdown_content = re.sub('\n\n+', '\n', markdown_content)
        return markdown_content
        
    except Exception as e:
        return ""

def remove_markdown_links(markdown_text):
    """
    마크다운 텍스트에서 링크 구문을 제거하고 텍스트만 추출합니다.
    [텍스트](링크) --> 텍스트 형식으로 변환합니다.
    ![대체텍스트](이미지링크) --> 대체텍스트 형식으로 변환합니다.
    ![](이미지링크) --> 빈 문자열로 변환합니다.
    
    Args:
        markdown_text (str): 마크다운 형식 텍스트
        
    Returns:
        str: 링크가 제거된 텍스트
    """
    # 1. 이미지 링크 처리 (![alt](url) 형식)
    # 대체 텍스트가 있는 이미지 패턴
    img_pattern_with_alt = r'!\[([^\]]+)\]\([^)]+\)'
    markdown_text = re.sub(img_pattern_with_alt, r'\1', markdown_text)
    
    # 대체 텍스트가 없는 이미지 패턴 (![](url) 형식)
    img_pattern_no_alt = r'!\[\]\([^)]+\)'
    markdown_text = re.sub(img_pattern_no_alt, '', markdown_text)
    
    # 2. 일반 링크 처리 ([text](url) 형식)
    link_pattern = r'\[([^\]]+)\]\([^)]+\)'
    text_only = re.sub(link_pattern, r'\1', markdown_text)
    
    return text_only

async def async_extract_wiki_content(url, browser_client=None):
    """
    위키피디아 페이지를 마크다운 형식으로 비동기식으로 변환하고 링크를 제거합니다.
    
    Args:
        url (str): 위키피디아 URL
        session (aiohttp.ClientSession, optional): 재사용할 세션
        
    Returns:
        str: 마크다운 형식의 텍스트 (링크 제거됨)
    """
    try:
        markdown_content = await async_convert_to_markdown(url, browser_client)
        return remove_markdown_links(markdown_content)
    except Exception as e:
        return ""


if __name__ == "__main__":
    import ssl
    import certifi
    import httpx
    import asyncio
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.google.com/",
    }
    ctx = ssl.create_default_context(cafile=certifi.where())
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
        headers=HEADERS,
        follow_redirects=True,                    
        max_redirects=5,
        verify=ctx,
    )
    # 비동기 함수 실행
    result = asyncio.run(async_extract_wiki_content("https://ko.wikipedia.org/wiki/%EC%9D%B4%EC%A4%80%EC%84%9D", browser_client))
    print(result)
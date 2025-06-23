import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor

class AsyncBrunchScraper:
    def __init__(self, use_selenium=True):
        self.use_selenium = use_selenium
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.session = None  # 항상 초기화
        
        if use_selenium:
            self.setup_selenium()
        else:
            self.session = None
    
    def setup_selenium(self):
        """Selenium 설정 - JavaScript 보호 기능 우회"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 브라우저 창 숨기기
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # 복사 방지 기능 무력화
        chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2
        })
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # JavaScript로 보호 기능 무력화
        disable_protection_script = """
        // 우클릭 방지 해제
        document.addEventListener = function(){};
        window.addEventListener = function(){};
        document.oncontextmenu = null;
        document.onselectstart = null;
        document.ondragstart = null;
        
        // CSS로 인한 선택 방지 해제
        var style = document.createElement('style');
        style.innerHTML = `
            * {
                -webkit-user-select: text !important;
                -moz-user-select: text !important;
                -ms-user-select: text !important;
                user-select: text !important;
                -webkit-touch-callout: default !important;
                -webkit-tap-highlight-color: rgba(0,0,0,0) !important;
            }
        `;
        document.head.appendChild(style);
        
        // 이벤트 리스너 제거
        var events = ['contextmenu', 'selectstart', 'dragstart', 'mousedown', 'mouseup'];
        events.forEach(function(event) {
            window[event] = null;
            document[event] = null;
        });
        
        return true;
        """
        
        self.disable_script = disable_protection_script
    
    async def setup_aiohttp_session(self):
        """aiohttp 세션 설정"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
    
    async def scrape_article(self, url):
        """브런치 블로그 글 스크래핑 (보호 기능 우회 포함)"""
        try:
            if self.use_selenium:
                return await self._scrape_with_selenium(url)
            else:
                return await self._scrape_with_aiohttp(url)
                
        except Exception as e:
            print(f"스크래핑 오류: {e}")
            return None
    
    async def _scrape_with_selenium(self, url):
        """Selenium을 사용한 스크래핑 (JavaScript 보호 기능 우회)"""
        try:
            # Selenium 작업을 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            html = await loop.run_in_executor(self.executor, self._selenium_get_html, url)
            
            if html:
                soup = BeautifulSoup(html, "html.parser")
                return await self._extract_article_data_async(soup, url)
            
            return None
            
        except Exception as e:
            print(f"Selenium 스크래핑 오류: {e}")
            return None
    
    def _selenium_get_html(self, url):
        """Selenium으로 HTML 가져오기 (동기 함수)"""
        try:
            self.driver.get(url)
            
            # 페이지 로드 대기
            WebDriverWait(self.driver, 0.5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 보호 기능 무력화 스크립트 실행
            self.driver.execute_script(self.disable_script)
            
            # 추가 대기 (동적 콘텐츠 로딩)
            time.sleep(0.5)
            
            return self.driver.page_source
            
        except TimeoutException:
            print("페이지 로딩 시간 초과")
            return None
        except Exception as e:
            print(f"Selenium HTML 가져오기 오류: {e}")
            return None
    
    async def _scrape_with_aiohttp(self, url):
        """aiohttp를 사용한 스크래핑"""
        try:
            await self.setup_aiohttp_session()
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                return await self._extract_article_data_async(soup, url)
                
        except aiohttp.ClientError as e:
            print(f"요청 오류: {e}")
            return None
    
    async def _extract_article_data_async(self, soup, url):
        """HTML에서 게시글 데이터 추출 (비동기 병렬 처리)"""
        loop = asyncio.get_event_loop()
        
        # 각 추출 작업을 병렬로 실행
        tasks = [
            loop.run_in_executor(self.executor, self._extract_title, soup),
            loop.run_in_executor(self.executor, self._extract_subtitle, soup),
            loop.run_in_executor(self.executor, self._extract_date, soup),
            loop.run_in_executor(self.executor, self._extract_content, soup),
        ]
        
        # 모든 작업이 완료될 때까지 대기
        title, subtitle, publish_date, content = await asyncio.gather(*tasks)
        
        article_data = {
            'url': url,
            'title': title,
            'subtitle': subtitle,
            'publish_date': publish_date,
            'content': content,
        }
        
        return article_data
    
    def _extract_title(self, soup):
        """제목 추출"""
        selectors = [
            'h1.cover_title',
            '.wrap_cover h1',
            '.article_header h1',
            'h1[class*="title"]',
            'meta[property="og:title"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        return ''
    
    def _extract_subtitle(self, soup):
        """부제목 추출"""
        selectors = [
            '.cover_sub_title',
            '.wrap_cover .sub_title',
            '.article_header .sub_title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ''
    
    def _extract_author(self, soup):
        """작성자 이름 추출"""
        selectors = [
            '.by_info .by_name a',
            '.by_info .by_name',
            '.author_info .name',
            '.wrap_author .name',
            'meta[name="author"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        return ''
    
    def _extract_author_id(self, soup):
        """작성자 ID 추출"""
        author_link = soup.select_one('.by_info .by_name a, .author_info a')
        if author_link and author_link.get('href'):
            href = author_link.get('href')
            # brunch.co.kr/@author_id 형태에서 author_id 추출
            match = re.search(r'/@([^/]+)', href)
            if match:
                return match.group(1)
        return ''
    
    def _extract_date(self, soup):
        """작성일 추출"""
        selectors = [
            '.by_info .date',
            '.publish_date',
            '.article_info .date',
            'time[datetime]',
            'meta[property="article:published_time"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                elif element.name == 'time' and element.get('datetime'):
                    return element.get('datetime').strip()
                return element.get_text(strip=True)
        return ''
    
    def _extract_content(self, soup):
        """본문 텍스트 추출"""
        selectors = [
            '.wrap_body',
            '.article_body',
            '#article_body',
            '.post_body'
        ]
        
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # 불필요한 요소들 제거
                for unwanted in content_div.select('.ad, .advertisement, .social_share, .related_articles, .wrap_btn_utility'):
                    unwanted.decompose()
                
                # 텍스트 추출
                paragraphs = []
                for element in content_div.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 5:  # 너무 짧은 텍스트 제외
                        paragraphs.append(text)
                
                return '\n\n'.join(paragraphs)
        
        return ''
    
    def _extract_content_html(self, soup):
        """본문 HTML 추출"""
        selectors = [
            '.wrap_body',
            '.article_body',
            '#article_body',
            '.post_body'
        ]
        
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # 불필요한 요소들 제거
                for unwanted in content_div.select('.ad, .advertisement, .social_share, .related_articles, .wrap_btn_utility'):
                    unwanted.decompose()
                
                return str(content_div)
        
        return ''
    
    def _extract_tags(self, soup):
        """태그 추출"""
        tags = []
        selectors = [
            '.tag_list .tag',
            '.keywords .keyword',
            '.wrap_tag .tag'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text(strip=True).replace('#', '')
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
        
        return tags
    
    def _extract_category(self, soup):
        """카테고리 추출"""
        category_element = soup.select_one('.category, .breadcrumb .category')
        return category_element.get_text(strip=True) if category_element else ''
    
    def _extract_likes(self, soup):
        """좋아요 수 추출"""
        selectors = [
            '.like_count',
            '.sympathy_count',
            '.btn_like .count'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                numbers = re.findall(r'\d+', text)
                return int(numbers[0]) if numbers else 0
        return 0
    
    def _extract_comments_count(self, soup):
        """댓글 수 추출"""
        comment_element = soup.select_one('.comment_count, .btn_comment .count')
        if comment_element:
            text = comment_element.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            return int(numbers[0]) if numbers else 0
        return 0
    
    def _extract_read_time(self, soup):
        """읽기 시간 추출"""
        read_time_element = soup.select_one('.read_time, .reading_time')
        return read_time_element.get_text(strip=True) if read_time_element else ''
    
    def _extract_images(self, soup):
        """본문 이미지 URL 추출"""
        images = []
        content_div = soup.select_one('.wrap_body, .article_body, #article_body')
        
        if content_div:
            img_elements = content_div.select('img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    if not src.startswith('http'):
                        src = 'https:' + src if src.startswith('//') else 'https://brunch.co.kr' + src
                    images.append(src)
        
        return images
    
    async def save_to_file_async(self, article_data, filename=None):
        """결과를 파일로 저장 (비동기)"""
        if not filename:
            # 제목을 파일명으로 사용 (특수문자 제거)
            title = re.sub(r'[^\w\s-]', '', article_data['title'])
            title = re.sub(r'[-\s]+', '-', title)[:50]  # 50자로 제한
            filename = f"brunch_{title}.json"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor, 
            self._write_json_file, 
            article_data, 
            filename
        )
        
        print(f"결과가 {filename}에 저장되었습니다.")
    
    def _write_json_file(self, article_data, filename):
        """JSON 파일 쓰기 (동기 함수)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
    
    async def close(self):
        """리소스 정리"""
        if self.use_selenium and hasattr(self, 'driver'):
            try:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, 
                    self.driver.quit
                )
            except Exception as e:
                print(f"Selenium 드라이버 종료 오류: {e}")
        
        if hasattr(self, 'session') and self.session:
            try:
                await self.session.close()
            except Exception as e:
                print(f"세션 종료 오류: {e}")
        
        if hasattr(self, 'executor'):
            try:
                self.executor.shutdown(wait=True)
            except Exception as e:
                print(f"Executor 종료 오류: {e}")

# 사용 예시
async def async_extract_brunch_blog_content(url, browser_client):
    # Selenium 사용 (JavaScript 보호 기능 우회)
    scraper = AsyncBrunchScraper(use_selenium=True)
    
    try:
        # 비동기로 스크래핑 실행
        article_data = await scraper.scrape_article(url)

        result = ""
        if article_data:
            result += f"# {article_data['title']}\n"
            result += f"## {article_data['subtitle']}\n"
            result += f"### 작성일: {article_data['publish_date']}\n"
            result += f"{article_data['content']}\n"
        else:
            result = ""
    
    finally:
        await scraper.close()
        return result
    
if __name__ == "__main__":
    result = asyncio.run(async_extract_brunch_blog_content("https://brunch.co.kr/@markinnoforest/399", None))
    print(result)
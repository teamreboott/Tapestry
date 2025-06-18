import io
import re
from typing import Any, BinaryIO, Optional, Union
from bs4 import BeautifulSoup
from .stream_info import StreamInfo
from .base_converter import DocumentConverterResult
from .markdownify import _CustomMarkdownify

ACCEPTED_MIME_TYPE_PREFIXES = [
    "text/html",
    "application/xhtml",
]

ACCEPTED_FILE_EXTENSIONS = [
    ".html",
    ".htm",
]


class HtmlConverter:
    """Anything with content type text/html"""

    # def convert(
    #     self,
    #     file_stream: Union[BinaryIO, str],  # <-- str도 받을 수 있도록 타입 변경
    #     stream_info: StreamInfo,
    #     **kwargs: Any,
    # ) -> DocumentConverterResult:
    #     # str 타입인 경우 바로 BeautifulSoup에 넘기기
    #     if isinstance(file_stream, str):
    #         soup = BeautifulSoup(file_stream, "html.parser")
    #     else:
    #         return ""

    #     # Remove javascript and style blocks
    #     for script in soup(["script", "style"]):
    #         script.extract()

    #     # 본문과 관련없는 추가 요소들 제거
    #     for element in soup(["nav", "header", "footer", "aside", "noscript"]):
    #         element.extract()
        
    #     # 광고, 댓글, 소셜미디어 관련 요소들 제거
    #     for element in soup.find_all(attrs={"class": lambda x: x and any(
    #         keyword in str(x).lower() for keyword in [
    #             "ad", "ads", "advertisement", "banner", "sponsor",
    #             "comment", "disqus", "social", "share", "follow",
    #             "newsletter", "popup", "modal", "sidebar"
    #         ]
    #     )}):
    #         element.extract()
        
    #     # ID로 식별되는 불필요한 요소들
    #     for element in soup.find_all(attrs={"id": lambda x: x and any(
    #         keyword in str(x).lower() for keyword in [
    #             "ad", "ads", "sidebar", "footer", "header", "nav",
    #             "comment", "social", "share", "newsletter"
    #         ]
    #     )}):
    #         element.extract()

    #     # # 주요 콘텐츠 요소를 찾는 로직
    #     # content_elm = (
    #     #     soup.find("main") or 
    #     #     soup.find("article") or 
    #     #     soup.find(attrs={"id": "content"}) or
    #     #     soup.find(attrs={"class": "content"}) or
    #     #     soup.find(attrs={"role": "main"}) or
    #     #     soup.find("body") or
    #     #     soup
    #     # )
    #     origin_content = soup.text

    #     # 주요 콘텐츠 요소를 찾는 로직
    #     content_elm = (
    #         soup.find("main") or 
    #         soup.find("article") or 
    #         soup.find(attrs={"id": "content"}) or
    #         soup.find(attrs={"class": "content"}) or
    #         soup.find(attrs={"role": "main"}) or
    #         # 추가적인 본문 패턴들
    #         soup.find(attrs={"class": lambda x: x and any(
    #             keyword in str(x).lower() for keyword in [
    #                 "post", "entry", "article", "story", "text",
    #                 "main", "primary", "body-content", "page-content"
    #             ]
    #         )}) or
    #         soup.find(attrs={"id": lambda x: x and any(
    #             keyword in str(x).lower() for keyword in [
    #                 "post", "entry", "article", "story", "text",
    #                 "main", "primary", "container", "wrapper"
    #             ]
    #         )}) or
    #         # div 태그들 중에서 가장 텍스트가 많은 것
    #         max((div for div in soup.find_all("div") if div.get_text().strip()), 
    #             key=lambda x: len(x.get_text()), default=None) or
    #         soup.find("body") or
    #         soup
    #     )

    #     webpage_text = _CustomMarkdownify(**kwargs).convert_soup(content_elm)
    #     if webpage_text == "":
    #         webpage_text = origin_content

    #     webpage_text = webpage_text.strip()
    #     webpage_text = re.sub(r'\n\n+', '\n\n', webpage_text).strip()

    #     return DocumentConverterResult(
    #         markdown=webpage_text,
    #         title=None if soup.title is None else soup.title.string,
    #     )
    
    def convert(
        self,
        file_stream: Union[BinaryIO, str],  # <-- str도 받을 수 있도록 타입 변경
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        # str 타입인 경우 바로 BeautifulSoup에 넘기기
        if isinstance(file_stream, str):
            soup = BeautifulSoup(file_stream, "html.parser")
        else:
            return ""

        # 스크립트와 스타일 태그 제거
        for script in soup(["script", "style", 'nav', 'navbar', 'navigation', 'menu', 'sidebar', 'side-bar', 
            'aside', 'header', 'footer']):
            script.decompose()
        
        # 숨겨진 요소들도 제거 (선택사항)
        for hidden in soup.find_all(attrs={"style": re.compile(r"display:\s*none", re.I)}):
            hidden.decompose()
        
        # 모든 텍스트 추출 (간단한 방법)
        text = soup.get_text()
        # 여러 공백과 줄바꿈 정리
        text = re.sub(r'\n+', '\n', text)
        webpage_text = re.sub(r' +', ' ', text)
        webpage_text = webpage_text.strip()

        return DocumentConverterResult(
            markdown=webpage_text,
            title=None if soup.title is None else soup.title.string,
        )

    def convert_string(
        self, html_content: str, *, url: Optional[str] = None, **kwargs
    ) -> DocumentConverterResult:
        """
        Non-standard convenience method to convert a string to markdown.
        Given that many converters produce HTML as intermediate output, this
        allows for easy conversion of HTML to markdown.
        """
        return self.convert(
            file_stream=html_content,
            stream_info=StreamInfo(
                mimetype="text/html",
                extension=".html",
                charset="utf-8",
                url=url,
            ),
            **kwargs,
        )
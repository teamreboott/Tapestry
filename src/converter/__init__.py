from abc import ABC, abstractmethod
from typing import Optional
import re

class ContentExtractor(ABC):
    """콘텐츠 추출기 기본 클래스"""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """해당 URL을 처리할 수 있는지 확인"""
        pass
    
    @abstractmethod
    async def extract(self, url: str, browser_client) -> str:
        """콘텐츠 추출"""
        pass

class ExtractorRegistry:
    """추출기 레지스트리"""
    
    def __init__(self):
        self._extractors = []
    
    def register(self, extractor: ContentExtractor):
        """추출기 등록"""
        self._extractors.append(extractor)
    
    def get_extractor(self, url: str) -> Optional[ContentExtractor]:
        """URL에 맞는 추출기 반환"""
        for extractor in self._extractors:
            if extractor.can_handle(url):
                return extractor
        return None
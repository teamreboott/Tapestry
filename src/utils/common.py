import re
import yaml
import uuid
from typing import Any
import json


def json_line(obj: dict[str, Any]) -> str:
    """Serialize object as JSON + newline (SSE friendly)."""
    return json.dumps(obj, ensure_ascii=False) + "\n"


def generate_uuid():
    new_uuid = uuid.uuid4()
    hex_uuid = new_uuid.hex
    return hex_uuid


def build_model_type(model_name: str) -> str:
    if "gpt-4o" in model_name:
        return "gpt-4o"
    if "o1" in model_name:
        return "o1"
    if "claude-3-7-sonnet" in model_name:
        return "claude-3-7-sonnet"
    if "claude-3-5-sonnet" in model_name:
        return "claude-3-5-sonnet"
    if "gpt-4.1" in model_name:
        return "gpt-4.1"
    if "gpt-4.1-nano" in model_name:
        return "gpt-4.1-nano"
    if "gpt-4.1-mini" in model_name:
        return "gpt-4.1-mini"
    return "unknown"


def load_yaml(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def is_url(url: str) -> bool:
    """
    주어진 문자열이 URL인지 확인합니다.
    :param url: 확인할 문자열
    :return: URL이면 True, 아니면 False
    """

    url = url.strip()
    if " " in url or "\n" in url:
        return False
    # URL 패턴 정의 (인코딩된 문자를 포함한 URL 형식)
    url_pattern = re.compile(
        r'(https?:\/\/'                   # http:// 또는 https://
        r'('
        r'([\w\-]+\.)+[\w\-]+|'           # 도메인 (예: www.example.com)
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP 주소 (예: 192.168.0.1)
        r')'
        r'(:\d+)?'                        # 포트 번호 (예: :8080)
        r'(\/[^\s]*)?)'                   # 경로, 쿼리 문자열 등 (공백 아닌 모든 문자 허용)
    )

    return bool(re.match(url_pattern, url))


def extract_urls(text: str, max_num_urls: int = 3) -> list[str]:
    """
    텍스트 내에서 URL을 추출하여 리스트로 반환합니다.
    :param text: URL을 추출할 텍스트
    :param max_num_urls: 최대 반환할 URL 개수
    :return: 추출된 URL 리스트
    """
    # URL 패턴 정의 (인코딩된 문자를 포함한 URL 형식)
    url_pattern = re.compile(
        r'(https?:\/\/'                   # http:// 또는 https://
        r'('
        r'([\w\-]+\.)+[\w\-]+|'           # 도메인 (예: www.example.com)
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP 주소 (예: 192.168.0.1)
        r')'
        r'(:\d+)?'                        # 포트 번호 (예: :8080)
        r'(\/[^\s]*)?)'                   # 경로, 쿼리 문자열 등 (공백 아닌 모든 문자 허용)
    )
    # 전체 URL 찾기
    urls = url_pattern.findall(text)
    
    # findall은 각 그룹을 튜플로 반환하므로 첫 번째 그룹(전체 URL)만 사용
    result = [url[0] for url in urls]
    
    # 중복 제거 및 최대 개수 제한
    unique_result = list(dict.fromkeys(result))  # 순서 유지하며 중복 제거
    return unique_result[:max_num_urls]


if __name__ == "__main__":
    test = "http://192.168.0.10:8000/portal/"
    test = "https://arxiv.org/pdf/2409.01140  https://docs.llamaindex.ai/en/stable/examples/vector_stores/qdrant_hybrid/"
    print(is_url(test))
    print(extract_urls(test))
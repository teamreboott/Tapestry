from bs4 import BeautifulSoup
import re
import json

async def async_extract_chosun_news_content(url, browser_client):
    try:
        response = await browser_client.get(url)
        if response.status_code != 200:
            return ""
        html = BeautifulSoup(response.text, "html.parser")

        # 방법 1: fusion-metadata에서 JSON 데이터 추출
        fusion_script = html.find("script", {"id": "fusion-metadata"})
        if fusion_script:
            script_content = fusion_script.string
            # window.Fusion.globalContent에서 데이터 추출
            start_idx = script_content.find('Fusion.globalContent=') + len('Fusion.globalContent=')
            end_idx = script_content.find(';', start_idx)
            json_str = script_content[start_idx:end_idx]

            try:
                content_data = json.loads(json_str)
            except json.JSONDecodeError:
                try:
                    content_data = {}
                    # 마지막 완전한 객체까지만 추출
                    last_complete_brace = json_str.rfind('}')
                    print(last_complete_brace)
                    if last_complete_brace != -1:
                        # 마지막 }부터 끝까지 확인해서 완전한 JSON 구조 찾기
                        for i in range(last_complete_brace, -1, -1):
                            if json_str[i] == '}':
                                try:
                                    # 해당 위치까지의 문자열이 유효한 JSON인지 확인
                                    truncated_json = json_str[:i+1] + "]}"
                                    # content_elements 배열이 제대로 닫혀있는지 확인
                                    if truncated_json.count('[') == truncated_json.count(']'):
                                        content_data = json.loads(truncated_json)
                                        break
                                except:
                                    continue
                except Exception as e:
                    result = ""
            
            try:
                # content_elements에서 텍스트 추출
                content_parts = []
                for element in content_data.get('content_elements', []):
                    if element.get('type') == 'text':
                        content_parts.append(element.get('content', ''))
                
                result = '\n\n'.join(content_parts)
                result = result.strip()
            except json.JSONDecodeError:
                result = ""
    except Exception as e:
        result = ""
    finally:
        return result
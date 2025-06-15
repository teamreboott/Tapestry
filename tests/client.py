import asyncio
import aiohttp
import json
import time
from typing import List
from rich.console import Console
import argparse

console = Console()

# --- Server URL Configuration ---
# Select the appropriate URL based on your environment.

# 1. For Docker deployment (or local development)
#    - The service runs directly on the host machine or in a Docker container.
#    - The port is mapped directly. Default is 9012.
SERVER_URL = "http://127.0.0.1:9012/websearch"

# 2. For Kubernetes deployment
#    - The service is accessed via a NodePort.
#    - The default NodePort is 30800.
# SERVER_URL = "http://127.0.0.1:30800/websearch"

TIMEOUT = 180

def parse_args():
    parser = argparse.ArgumentParser(description="Web search client stream")
    parser.add_argument('--language', type=str, default='en', help='검색 언어')
    parser.add_argument('--query', type=str, required=True, help='검색 쿼리')
    parser.add_argument('--search_type', type=str, default='auto', help='검색 타입')
    parser.add_argument('--persona_prompt', type=str, default='N/A', help='페르소나 프롬프트')
    parser.add_argument('--custom_prompt', type=str, default='N/A', help='커스텀 프롬프트')
    parser.add_argument('--target_nuance', type=str, default='Natural', help='목표 뉘앙스')
    parser.add_argument('--stream', action='store_true', help='스트리밍 사용 여부')
    parser.add_argument('--no-stream', dest='stream', action='store_false', help='스트리밍 미사용')
    parser.set_defaults(stream=True)
    parser.add_argument('--use_youtube_transcript', action='store_true', help='유튜브 트랜스크립트 사용 여부')
    parser.add_argument('--no-youtube', dest='use_youtube_transcript', action='store_false', help='유튜브 트랜스크립트 미사용')
    parser.set_defaults(use_youtube_transcript=False)
    parser.add_argument('--top_k', type=int, default=None, help='top_k 값')
    parser.add_argument('--num_requests', type=int, default=1, help='동시 요청 개수')
    return parser.parse_args()

async def request_web_search(
        q: str, 
        session_id: str, 
        search_type: str = 'auto',
        previous_messages: List[dict] = [], 
        language: str = 'en', 
        persona_prompt: str = 'N/A', 
        custom_prompt: str = 'N/A', 
        target_nuance: str = 'Natural', 
        stream: bool = True, 
        use_youtube_transcript: bool = False, 
        top_k: int = None):
    
    previous_messages = [{"role": "user", "content": "what is an ai search engine?"}, {"role": "assistant", "content": "An AI search engine is a search engine that uses artificial intelligence to improve its search results. It can understand the user's query and provide relevant results."}]
    payload = {
        "language": language,
        "query": q,
        "search_type": search_type,
        "persona_prompt": persona_prompt,
        "custom_prompt": custom_prompt,
        "target_nuance": target_nuance,
        "messages": previous_messages,
        "stream": stream,
        "use_youtube_transcript": use_youtube_transcript,
        "top_k": top_k
    }
    url = SERVER_URL
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=TIMEOUT) as response:
            response.raise_for_status()
            async for line in response.content:
                data_str = line.decode("utf-8").strip()
                if data_str:
                    data_json = json.loads(data_str)
                    if data_json["status"] in "processing":
                        console.print(f"[blue]Session {session_id}: {data_json}")
                    elif data_json["status"] == "failure":
                        console.print(f"[red]Session {session_id}: {data_json}")
                        break
                    elif data_json["status"] == "streaming":
                        delta = data_json['delta']['content']
                        console.print(f"[green]{delta}")
                    elif data_json["status"] == "complete":
                        console.print(f"[yellow bold]Session {session_id}: {data_json}")
                        break

async def run_concurrent_requests(query: str, num_requests: int = 10, language: str = 'en', search_type: str = 'auto', persona_prompt: str = 'N/A', custom_prompt: str = 'N/A', target_nuance: str = 'Natural', stream: bool = True, use_youtube_transcript: bool = False, top_k: int = None):
    tasks = []
    for i in range(num_requests):
        session_id = f"session_{i:03d}"
        task = request_web_search(query, session_id, search_type, [], language, persona_prompt, custom_prompt, target_nuance, stream, use_youtube_transcript, top_k)
        tasks.append(task)
    await asyncio.gather(*tasks)

def main(args):
    asyncio.run(run_concurrent_requests(
        args.query,
        args.num_requests,
        args.language,
        args.search_type,
        args.persona_prompt,
        args.custom_prompt,
        args.target_nuance,
        args.stream,
        args.use_youtube_transcript,
        args.top_k
    ))

if __name__ == "__main__":
    start_time = time.time()
    args = parse_args()
    main(args)
    end_time = time.time()
    print(f"Duration: {end_time - start_time}초")

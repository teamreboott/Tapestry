import asyncio
import aiohttp
import json
import time
from typing import List
from rich.console import Console

console = Console()
# SERVER_URL = "http://127.0.0.1:9012/websearch"
SERVER_URL = "http://127.0.0.1:32178/websearch"
TIMEOUT = 180

async def request_web_search(q: str, session_id: str, previous_messages: List[dict] = []):
    payload = {
        "language": "en",
        "query": q,
        "persona_prompt": "N/A",
        "custom_prompt": "N/A",
        "target_nuance": "Natural",
        "messages": previous_messages,
        "stream": True,
        "use_youtube_transcript": False,
        "top_k": None
    }
    url = SERVER_URL
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=TIMEOUT) as response:
            response.raise_for_status()
            async for line in response.content:
                data_str = line.decode("utf-8").strip()
                if data_str:
                    data_json = json.loads(data_str)
                    if data_json["status"] == "success":
                        console.print(f"[green]Session {session_id}: Success")
                        console.print_json(f"{json.dumps(data_json)}")
                        break
                    elif data_json["status"] in "processing":
                        console.print(f"[blue]Session {session_id}: {data_json}")
                    elif data_json["status"] == "failure":
                        console.print(f"[red]Session {session_id}: {data_json}")
                        break
                    elif data_json["status"] == "streaming":
                        console.print(f"[green]Session {session_id}: {data_json}")
                    elif data_json["status"] == "complete":
                        console.print(f"[green]Session {session_id}: {data_json}")
                        break

async def run_concurrent_requests(query: str, num_requests: int = 10):
    tasks = []
    for i in range(num_requests):
        session_id = f"session_{i:03d}"
        task = request_web_search(query, session_id, [])
        tasks.append(task)
    
    await asyncio.gather(*tasks)

def main(q: str, num_requests: int = 10):
    asyncio.run(run_concurrent_requests(q, num_requests))

if __name__ == "__main__":
    start_time = time.time()
    query = "서울 날씨 알려줘"
    main(query, 1)  # 10개의 동시 요청 실행
    end_time = time.time()
    print(f"실행 시간: {end_time - start_time}초")

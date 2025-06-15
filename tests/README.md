# Tapestry API Guide

English | [한국어](README.ko.md)

This guide provides information about the Tapestry API endpoints and how to use them.

---

## API Endpoints

### Web Search API
`POST /websearch`

The main endpoint for web search-based QA.

#### Request Parameters

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|----------|
| `query` | String | Search query | - | Yes |
| `language` | String | Search language (`ko`, `en`, `zh`, `ja`) | `ko` | No |
| `persona_prompt` | String | Persona prompt (use `None` if not needed) | - | No |
| `custom_prompt` | String | Custom prompt (use `None` if not needed) | - | No |
| `target_nuance` | String | Target nuance (use `None` if not needed) | - | No |
| `return_process` | Boolean | Whether to return process messages | `true` | No |
| `stream` | Boolean | Whether to return streaming response | `true` | No |
| `use_youtube_transcript` | Boolean | Whether to include YouTube transcripts | `true` | No |
| `top_k` | Integer | Number of web contents to use | `"auto"` | No |
| `messages` | Array | Message history (use `[]` if not needed) | - | No |
| └ `role` | String | Role (`user`, `assistant`) | - | Yes* |
| └ `content` | String | Message content | - | Yes* |

\* Required if `messages` array is provided

#### Response Format

The API returns a streaming response with the following status types:

- `processing`: Processing status updates
- `streaming`: Streaming content chunks
- `complete`: Final complete response
- `failure`: Error messages

#### Example Usage

```python
import asyncio
import aiohttp
import json

async def request_web_search(query: str):
    payload = {
        "language": "ko",
        "query": query,
        "persona_prompt": "N/A",
        "custom_prompt": "N/A",
        "target_nuance": "Natural",
        "messages": [],
        "stream": True,
        "use_youtube_transcript": False,
        "top_k": None
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:9012/websearch", json=payload) as response:
            async for line in response.content:
                data = json.loads(line.decode("utf-8").strip())
                if data["status"] == "streaming":
                    print(data["delta"]["content"], end="")
                elif data["status"] == "complete":
                    print("\nComplete response received")
                    break
```

### Health Check API
`GET /health`

Simple health check endpoint to verify service status.

---

## Client Examples

The `service` directory includes example clients:

- `client_stream.py`: Example of using the streaming API
- `client_sync.py`: Example of using the synchronous API

To run the streaming client:

```bash
python client_stream.py
```

Make sure to configure the `SERVER_URL` in the client file according to your deployment:
- Docker: `http://127.0.0.1:9012/websearch`
- Kubernetes: `http://127.0.0.1:30800/websearch` 
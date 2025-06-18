# Tapestry API Guide

English | [한국어](README.ko.md)

This guide provides up-to-date information about the Tapestry API endpoints, request/response formats, and usage examples.

---

## API Endpoints

### Web Search API

`POST /websearch`

Main endpoint for web search-based QA.

#### Request Parameters

| Name                   | Type    | Description                                                      | Default   | Required |
|------------------------|---------|------------------------------------------------------------------|-----------|----------|
| `query`                | String  | Search query                                                     | -         | Yes      |
| `language`             | String  | Search language (`ko`, `en`, `zh`, `ja`)                         | `ko`      | No       |
| `search_type`          | String  | Search type (`auto`, `general`, `scholar`, `news`, `youtube`)    | `auto`    | No       |
| `persona_prompt`       | String  | Persona prompt (`N/A` if not needed)                             | `N/A`     | No       |
| `custom_prompt`        | String  | Custom prompt (`N/A` if not needed)                              | `N/A`     | No       |
| `target_nuance`        | String  | Target nuance (`Natural` if not needed)                          | `Natural` | No       |
| `return_process`       | Boolean | Whether to return process messages                               | `true`    | No       |
| `stream`               | Boolean | Whether to return streaming response                             | `true`    | No       |
| `use_youtube_transcript`| Boolean| Whether to include YouTube transcripts                           | `false`   | No       |
| `top_k`                | Integer | Number of web contents to use (`auto` for automatic)             | `auto`    | No       |
| `messages`             | Array   | Message history (use `[]` if not needed)                         | `[]`      | No       |
| └ `role`               | String  | Role (`user`, `assistant`)                                       | -         | Yes*     |
| └ `content`            | String  | Message content                                                  | -         | Yes*     |

\* Required if `messages` array is provided

#### Response Format

The API returns a streaming response with the following status types:

- `processing`: Processing status updates
- `streaming`: Streaming content chunks
- `complete`: Final complete response
- `failure`: Error messages

Each line is a JSON object.

#### Example Usage (Python, Async)

```python
import asyncio
import aiohttp
import json

async def request_web_search(query: str):
    payload = {
        "language": "ko",
        "query": query,
        "search_type": "auto",
        "persona_prompt": "N/A",
        "custom_prompt": "N/A",
        "target_nuance": "Natural",
        "messages": [],
        "stream": True,
        "use_youtube_transcript": False,
        "top_k": None
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("http://127.0.0.1:9012/websearch", json=payload) as response:
            async for line in response.content:
                data = json.loads(line.decode("utf-8").strip())
                if data["status"] == "streaming":
                    print(data["delta"]["content"], end="")
                elif data["status"] == "complete":
                    print("\nComplete response received")
                    break

asyncio.run(request_web_search("What is an AI search engine?"))
```

---

## Health Check API

`GET /health`

Simple health check endpoint to verify service status.

#### Example

```bash
curl http://127.0.0.1:9012/health
```

---

## Client Examples

Example clients are provided in the `service` directory:

- `client_stream.py`: Example for using the streaming API
- `client_sync.py`: Example for synchronous API usage

To run the streaming client:

```bash
python client_stream.py --query "What is an AI search engine?" --language en
```

You can set the `SERVER_URL` in the client file according to your deployment:

- Docker/local: `http://127.0.0.1:9012/websearch`
- Kubernetes: `http://127.0.0.1:30800/websearch`

For more options, run:

```bash
python client_stream.py --help
```

---

## Notes

- The API supports both streaming and non-streaming responses.
- For best results, use the streaming mode for interactive applications.
- The `messages` parameter allows you to provide conversation history for context. 
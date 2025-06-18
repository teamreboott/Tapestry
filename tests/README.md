# Tapestry Test Clients & API Guide

This document provides up-to-date information on the Tapestry API endpoints and how to use the provided test clients.

---

## 📚 API Reference

### `POST /websearch`

Main endpoint for web search-based QA.

#### Request Body

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

* Required if `messages` array is provided

#### Response

Streaming JSON lines with the following status types:

- `processing`: Processing status updates
- `streaming`: Streaming content chunks
- `complete`: Final complete response
- `failure`: Error messages

---

## 🧪 Test Client Usage

A sample client is provided for testing the API.

### Run the client

```bash
python client.py --query "What is an AI search engine?" --language en
```

#### Options

- `--query`: (Required) Search query string
- `--language`: Search language (`en`, `ko`, etc.)
- `--search_type`: Search type (`auto`, `general`, `news`, `scholar`, `youtube`)
- `--persona_prompt`, `--custom_prompt`, `--target_nuance`, `--stream`, `--use_youtube_transcript`, `--top_k`, `--num_requests`: See `python client.py --help`

#### Configure Endpoint

Edit `SERVER_URL` in `client.py` to match your environment:

- Docker/local: `http://127.0.0.1:9012/websearch`
- Kubernetes: `http://127.0.0.1:30800/websearch`

---

## 🩺 Health Check

`GET /health`

```bash
curl http://127.0.0.1:9012/health
```

---

## 📁 Files

- `client.py` : Example async client for API testing
- `README.md` : (this file) 
   <p align="center">
     <img src="misc/logo.png" alt="logo" width="72"><br>
     <strong style="font-size:2.5em; font-weight:bold;">Tapestry</strong>
   </p>

<p align="center">
  English | <a href="README.ko.md">한국어</a>
</p>

<p align="center">
🌐 Open-Source Web Search Backend Framework via Plug-and-Play Knowledge Reconstruction
</p>

---

## Table of Contents

- [Overview](#-overview)
- [Support](#-support)
- [Quick Start](#-quick-start)
    - [Setup](#1-prerequisites-environment-configuration)
    - [Running with Docker](#2-running-with-docker)
    - [Running with Kubernetes](#3-running-with-kubernetes)
- [API Reference](#-api-reference)
- [Client Tests](#-testing-the-service)
- [Demo](#-demo)
    - [Gradio](#gradio)
- [How do Tapestry work?](#framework)
- [Project Structures](#-project-structure)

---

## 📖 Overview

`Tapestry` is an open-source backend framework designed to build customizable AI web search pipelines. Tapestry allows developers to flexibly combine **plug-and-play modules**, including search engines, domain-specific crawling, LLMs, and algorithms for improving search performance (e.g., deduplication, query rewriting).

![데모](misc/preview.gif)

---

## 🛠️ Support

### Search Engines

| Engine | API Key | Search | Youtube Search | News Search | Scholar Search | Shopping |
|:-------------:|:----:|:----:|:----:|:----:|:----:|:----:|
| Serper | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Serp | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Brave | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| DuckDuckGo | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |

### LLMs

* **OpenAI, Anthropic, Gemini**

---

## 🚀 Quick Start

This guide provides instructions for running the Tapestry service using Docker or Kubernetes.

### 1. Setup: Environment Configuration

Before launching the service, you must configure your environment variables. All settings are managed through a `.env` file in the `envs` directory.

1.  **Copy the Example Configuration:**  
    Create your environment file by copying the provided template.

    ```bash
    cp envs/example.env envs/.env
    ```

2.  **Edit the `.env` File:**  
    Open the newly created `.env` file and fill in the required values, such as your API keys and database credentials.

    -   For a detailed explanation of each variable, refer to the guide at [`envs/README.md`](envs/README.md).
    -   **Important**: The `POSTGRES_HOST` variable must be set correctly for your deployment environment:
        -   For **Docker**: `POSTGRES_HOST=postgres`
        -   For **Kubernetes**: `POSTGRES_HOST=tapestry-postgres`

### 2. Running with Docker

This is the recommended method for local development and testing.

1.  **Ensure your `.env` file is configured** as described above, with `POSTGRES_HOST=postgres`.

2.  **Run the launch script:**  
    The script handles directory setup and starts all services using Docker Compose.

    ```bash
    bash scripts/run.sh
    ```
    > The script uses the `.env` file in the project root by default.

3.  **Accessing the Service:**
    The API will be available at `http://localhost:9012`. You can change the port via the `APP_PORT` variable in your `.env` file.

### 3. Running with Kubernetes

For deployment in a Kubernetes cluster.

1.  **Ensure your `.env` file is configured** as described above, with `POSTGRES_HOST=tapestry-postgres`. Also, ensure `LOG_DIR` and `POSTGRES_DATA_DIR` are absolute paths that exist on your Kubernetes nodes.

2.  **Run the deployment script:**  
    This script automates the entire deployment process.

    ```bash
    bash scripts/run_k8s.sh [K8S_IP] [SERVICE_PORT] [POSTGRES_PORT] [NODE_PORT]
    ```

    **Script Arguments:**
    -   `K8S_IP`: The IP address of your Kubernetes cluster (defaults to `127.0.0.1`).
    -   `SERVICE_PORT`: The internal port for the application service (defaults to `9012`).
    -   `POSTGRES_PORT`: The port for the PostgreSQL service (defaults to `5432`).
    -   `NODE_PORT`: The external port (NodePort) to access the service (defaults to `30800`).

    **Example:**
    ```bash
    bash scripts/run_k8s.sh 127.0.0.1 9012 5432 30800
    ```

3.  **Accessing the Service:**
    The API will be available at `http://[K8S_IP]:[NODE_PORT]` (e.g., `http://127.0.0.1:30800`).

---

## 📚 API Reference

`POST /websearch`

#### Request body (variable | type | required)

* `query` | `string` | **Required**: The search query string.

* `language` | `string` | Optional, defaults to `"en"`: ISO 639-1 two-letter language code (e.g., en, ko, ja).

* `search_type` | `string` | Optional, defaults to `"auto"`: 
    - `auto`: The LLM automatically infers the search type from the query and selects the appropriate search engine.
    - `general`: Uses only indexed content from general search results for answering.
    - `news`: Uses only indexed content from news search results for answering.
    - `scholar`: Uses only indexed content from scholarly search results for answering. If the search engine does not support this, it falls back to `general` search.
    - `youtube`: Extracts and uses only YouTube video links from video search results for answering. If the search engine does not support this, it falls back to `general` search.

* `persona_prompt` | `string` | Optional, defaults to `None`: Persona instructions for the LLM.

* `custom_prompt` | `string` | Optional, defaults to `None`: Additional custom instructions to inject into the LLM.

* `messages` | `array` | Optional, defaults to `None`: Previous conversation history. Must follow the format: `[{"role": "user", "content": ""}, {"role": "assistant", "content": ""}, ...]`.

* `target_nuance` | `string` | Optional, defaults to `"Natural"`: Desired response nuance.

* `use_youtube_transcript` | `bool` | Optional, defaults to `False`: If YouTube results are included, use transcript information.

* `top_k` | `int` | Optional, defaults to `None`: Use the top `k` search results.

* `stream` | `bool` | Optional, defaults to `True`: Return the response as a streaming output.


---

## 🧪 Client Tests

You can test the streaming API using the provided client script.

1.  **Run the client:**
    ```bash
    python tests/client.py
    ```

2.  **Configure the Endpoint:**  
    Before running, open `tests/client.py` and ensure the `SERVER_URL` variable points to the correct endpoint for your environment:
    -   **Docker:** `http://127.0.0.1:9012/websearch`
    -   **Kubernetes:** `http://127.0.0.1:30800/websearch` (or your `K8S_IP` and `NODE_PORT`).

---

## 🎬 Demo

TDB

### Gradio

---

## Framework

- `GET /health`: Health check endpoint.
- `POST /websearch`: Main QA endpoint with a streaming response.

---

## 🧩 Project Structure

```
.
├── main.py                # Main FastAPI server
├── src/                   # Core source code (models, search, db, utils, etc.)
├── service/               # Service layer
├── configs/               # Configuration files
├── scripts/               # Automation scripts (run.sh, run_k8s.sh)
├── envs/                  # Environment variable examples and docs
├── k8s/                   # Kubernetes manifests
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build file
├── docker-compose.yaml    # Docker Compose file
└── README.md
```

# <img src="misc/logo.png" alt="logo" width="32" style="vertical-align: middle;"> Tapestry

English | [한국어](README.ko.md)

Tapestry : Open-Source Web Search Backend Framework via Plug-and-Play Knowledge Reconstruction

---

## Table of Contents <!-- omit in toc -->

- [Overview](#overview)
- [Preview](#preview)
- [Quick Start](#-quick-start)
    - [Prerequisite Step](#1-prerequisites-environment-configuration)
    - [Running with Docker](#2-running-with-docker)
    - [Running with Kubernetes](#3-running-with-kubernetes)
- [API Reference](#api-reference)
- [Client Tests](#-testing-the-service)
- [Demo](#demo)
    - [Gradio](#gradio)
- [API Endpoints](#api-endpoints)
- [Project Structures](#project-structure)

---

## 🚀 Quick Start

This guide provides instructions for running the Tapestry service using Docker or Kubernetes.

### 1. Prerequisites: Environment Configuration

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

## API Reference

TDB

---

## 🧪 Client Tests

You can test the streaming API using the provided client script.

1.  **Navigate to the service directory:**
    ```bash
    cd service/
    ```

2.  **Run the client:**
    ```bash
    python client_stream.py
    ```

3.  **Configure the Endpoint:**  
    Before running, open `service/client_stream.py` and ensure the `SERVER_URL` variable points to the correct endpoint for your environment:
    -   **Docker:** `http://127.0.0.1:9012/websearch`
    -   **Kubernetes:** `http://127.0.0.1:30800/websearch` (or your `K8S_IP` and `NODE_PORT`).

---

## Demo

TDB

### Gradio

---

## API Endpoints

- `GET /health`: Health check endpoint.
- `POST /websearch`: Main QA endpoint with a streaming response.

---

## Project Structure

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

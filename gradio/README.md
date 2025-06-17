# Tapestry Gradio Web UI

English | [한국어](README.ko.md)

## Introduction
This project is a Gradio-based Web Search chatbot UI.

## Quick Start

### 1. Local Run (No Docker)

```bash
bash run_demo.sh
```

You can specify the port and API address via environment variables:

```bash
GRADIO_PORT=8888 API_URL=http://my-api:9000/websearch bash run_demo.sh
```

---

### 2. Docker Run

```bash
bash run_docker_demo.sh
```

You can also specify the port and API address:

```bash
GRADIO_PORT=8888 API_URL=http://my-api:9000/websearch bash run_docker_demo.sh
```

---

## File Structure

- app.py : Main Gradio UI code
- requirements.txt : Python package list
- run_demo.sh : Local run script
- run_docker_demo.sh : Docker run script
- Dockerfile : Docker build file
- logo.png : Chatbot avatar image

---

## Notes

- The backend API server must be running before starting this UI.
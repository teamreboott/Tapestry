# Tapestry

Web Search-based LLM QA System for CIKM 2025

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
├── logs/                  # Log files
├── k8s/                   # Kubernetes manifests
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build file
├── docker-compose.yaml    # Docker Compose file
└── README.md
```

---

## Environment Variables

- All environment variable examples and documentation are provided in [`envs/README.md`](envs/README.md).
- Please copy and edit `example_docker.env` or `example_k8s.env` as needed.

---

## How to Run

### 1. Local (Bare Metal)

```bash
pip install -r requirements.txt
cp envs/example_docker.env envs/docker.env  # Edit as needed
python main.py
```
- The server will run on the port specified in your `.env` (default: 9004).

---

### 2. Docker

```bash
cp envs/example_docker.env envs/docker.env  # Edit as needed
bash scripts/run.sh ./envs/docker.env
```
- This script will:
  - Load environment variables
  - Set up PostgreSQL and log directories
  - Launch all services via Docker Compose

---

### 3. Kubernetes

```bash
cp envs/example_k8s.env envs/k8s.env  # Edit as needed
bash scripts/run_k8s.sh [K8S_IP] ./envs/k8s.env [SERVICE_PORT] [POSTGRES_PORT] [NODE_PORT]
```
- Example:
  ```bash
  bash scripts/run_k8s.sh 127.0.0.1 ./envs/k8s.env 9012 5432 30800
  ```
- This script will:
  - Build and load the Docker image
  - Create secrets, persistent volumes, and deploy all resources
  - Print service access information

---

## Service Access

### 1. Local (Bare Metal)
- Access the API at:  
  `http://localhost:9004`

### 2. Docker
- Access the API at:  
  `http://localhost:[APP_PORT]`  
  (default: 9004, or as set in your `docker.env`)

### 3. Kubernetes
- **Inside the cluster:**  
  Use the service name and port, e.g. `http://tapestry-service:[SERVICE_PORT]`
- **From the server (host):**  
  Use `http://localhost:[NODE_PORT]` (e.g. `http://localhost:30800`)
- **From outside the server:**  
  Use `http://[K8S_IP]:[NODE_PORT]`  
  (e.g. `http://your.server.ip:30800`)

---

## API Endpoints

- `GET /health`  
  Health check endpoint

- `POST /websearch`  
  Main QA endpoint (streaming response)

---

## Notes

- For environment variable details, see [`envs/README.md`](envs/README.md).
- For advanced configuration, see the `configs/` and `k8s/` folders.
- Logs are stored in the `logs/` directory (or mounted volume).

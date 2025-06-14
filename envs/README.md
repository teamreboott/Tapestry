# Environment Variable Guide

English | [한국어](README.ko.md)

All configuration for this project is managed via an environment variable file (`.env`). This approach allows for flexible and secure setup across different environments (local, Docker, Kubernetes).

---

## How to Use

1.  **Create a `.env` file:**  
    Copy the provided template `example.env` to create your own configuration file named `.env` in the `envs` directory.

    ```bash
    cp envs/example.env envs/.env
    ```

    > **Important**: The `.env` file must be located in the `envs` directory. The run scripts look for the configuration file in this location.

2.  **Edit Your `.env` File:**  
    Open the `.env` file and populate it with your specific settings, such as API keys, database credentials, and host paths.

    > **Note:** For a detailed description of each variable, please refer to the comments inside the `envs/example.env` file.

---

## Environment-Specific Configuration

While most variables are universal, a few require specific values depending on whether you are running the service with Docker or Kubernetes.

### `POSTGRES_HOST`
This variable defines the network hostname for the PostgreSQL database service.
-   **For Docker:** Set it to the name of the service defined in `docker-compose.yaml`.
    ```
    POSTGRES_HOST=postgres
    ```
-   **For Kubernetes:** Set it to the name of the Kubernetes service for PostgreSQL.
    ```
    POSTGRES_HOST=tapestry-postgres
    ```

### `LOG_DIR` and `POSTGRES_DATA_DIR`
These variables define the host paths for storing logs and database data.
-   **For Docker:** These can be relative or absolute paths on the host machine.
-   **For Kubernetes:** These **must be absolute paths** that exist on the Kubernetes nodes, as they are used for `hostPath` PersistentVolumes.
    -   Example: `/mnt/nas/storage/tapestry/logs`
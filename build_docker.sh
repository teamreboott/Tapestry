#!/bin/bash

# 이미지 이름과 태그
IMAGE_NAME="auw-web"
IMAGE_TAG="latest"
CONTAINER_NAME="web-agent"

DEPLOY_MODE=$1

if [ "$DEPLOY_MODE" == "prod" ]; then
    DB_DIR="/mnt/nas/storage/webchat/prod"
    cp -r envs/.prod.env .env
    if [ -d "$DB_DIR" ]; then
        echo "Directory $DB_DIR exists."
    else
        echo "Creating directory $DB_DIR..."
        mkdir -p $DB_DIR
    fi
elif [ "$DEPLOY_MODE" == "research" ]; then
    DB_DIR="mnt/nas/storage/webchat/research"
    cp -r envs/.research.env .env
    if [ -d "$DB_DIR" ]; then
        echo "Directory $DB_DIR exists."
    else
        echo "Creating directory $DB_DIR..."
        mkdir -p $DB_DIR
    fi
elif [ "$DEPLOY_MODE" == "dev" ]; then
    DB_DIR="/mnt/nas/storage/webchat/dev"
    cp -r envs/.dev.env .env
    if [ -d "$DB_DIR" ]; then
        echo "Directory $DB_DIR exists."
    else
        echo "Creating directory $DB_DIR..."
        mkdir -p $DB_DIR
    fi
else
    echo "Invalid deploy mode. Please specify 'prod', 'research', or 'dev'."
    exit 1
fi

# 컨테이너가 이미 실행 중인지 확인하고, 있다면 삭제
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "Removing existing container $CONTAINER_NAME..."
    docker rm -f $CONTAINER_NAME
fi

# 이미지가 존재하는지 확인
if docker images $IMAGE_NAME:$IMAGE_TAG | grep -q $IMAGE_NAME; then
    echo "Image $IMAGE_NAME:$IMAGE_TAG exists, removing..."
    # 이미지 삭제
    docker rmi -f $IMAGE_NAME:$IMAGE_TAG
fi

echo "Building image $IMAGE_NAME:$IMAGE_TAG..."
# 현재 디렉토리에서 Docker 이미지 빌드 (Dockerfile 위치를 기준으로 경로 수정 가능)
docker build -t $IMAGE_NAME:$IMAGE_TAG .

# 컨테이너 실행 (백그라운드 모드)
echo "Running container $CONTAINER_NAME from image $IMAGE_NAME:$IMAGE_TAG in background..."
# docker run --gpus all -d --network="host" --name $CONTAINER_NAME $IMAGE_NAME:$IMAGE_TAG

if [ "$DEPLOY_MODE" == "research" ]; then
    docker run -d --network="host" --name $CONTAINER_NAME -v $(pwd)/logs:/app/logs -v $$DB_DIR/:/app/mnt/nas/storage/research $IMAGE_NAME:$IMAGE_TAG
else
    docker run -d --network="host" --name $CONTAINER_NAME -v $(pwd)/logs:/app/logs -v $DB_DIR:$DB_DIR $IMAGE_NAME:$IMAGE_TAG
fi
echo "Success to Build Docker Contrainer!!"

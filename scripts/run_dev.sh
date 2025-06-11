sudo mkdir -p /mnt/nas/storage/webchat/dev

# PostgreSQL 데이터 디렉터리 권한 설정 (Ubuntu 22.04 호환성)
sudo mkdir -p /mnt/nas/storage/webchat/dev/pg_db
sudo chown -R 999:999 /mnt/nas/storage/webchat/dev/pg_db
sudo chmod -R 700 /mnt/nas/storage/webchat/dev/pg_db

# 로그 디렉터리 권한 설정
sudo mkdir -p $(pwd)/logs
sudo chmod -R 755 $(pwd)/logs

# # Elasticsearch 데이터 디렉터리 권한 설정 (예시)
# sudo mkdir -p /mnt/nas/storage/webchat/dev/es_db
# sudo chmod -R 755 /mnt/nas/storage/webchat/dev/es_db # Elasticsearch는 경우에 따라 700보다 넓은 권한이 필요할 수 있음

docker compose down # 기존 컨테이너 및 명명된 볼륨(사용 중지된 경우) 정리 (주의: 데이터 유실 가능성)
docker compose up --build -d
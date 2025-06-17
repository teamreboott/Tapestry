FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
COPY app.py ./
COPY logo.png ./

RUN pip install --no-cache-dir -r requirements.txt

COPY run_demo.sh ./
RUN chmod +x run_demo.sh

CMD ["./run_demo.sh"] 
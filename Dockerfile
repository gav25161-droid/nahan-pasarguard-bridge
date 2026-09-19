FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY proto ./proto
COPY bridge ./bridge
COPY app.py .
COPY start.sh .

RUN chmod +x start.sh

RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./bridge \
    --grpc_python_out=./bridge \
    ./proto/service.proto

RUN touch bridge/__init__.py

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/bridge

CMD ["./start.sh"]

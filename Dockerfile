FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

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

# Create a self-signed TLS certificate for the Railway TCP Proxy hostname.
RUN mkdir -p /app/certs \
    && openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout /app/certs/server.key \
    -out /app/certs/server.crt \
    -days 3650 \
    -subj "/CN=altaria.proxy.rlwy.net" \
    -addext "subjectAltName=DNS:altaria.proxy.rlwy.net"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/bridge

ENV SSL_CERT_FILE=/app/certs/server.crt
ENV SSL_KEY_FILE=/app/certs/server.key

CMD ["./start.sh"]

FROM python:3.12-slim

WORKDIR /app

# Install OpenSSL and system CA certificates
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssl \
        ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY proto ./proto
COPY bridge ./bridge
COPY app.py .
COPY start.sh .

RUN chmod +x start.sh

# Generate PasarGuard gRPC Python files
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./bridge \
    --grpc_python_out=./bridge \
    ./proto/service.proto

RUN touch bridge/__init__.py

# Create TLS certificate for Railway Private Network
# and Railway TCP Proxy hostname
RUN mkdir -p /app/certs \
    && openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout /app/certs/server.key \
    -out /app/certs/server.crt \
    -days 3650 \
    -subj "/CN=nahan-pasarguard-bridge.railway.internal" \
    -addext "subjectAltName=DNS:nahan-pasarguard-bridge.railway.internal,DNS:altaria.proxy.rlwy.net"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/bridge

CMD ["./start.sh"]

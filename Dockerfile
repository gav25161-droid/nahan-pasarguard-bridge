FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/certs && \
    openssl req -x509 -nodes -days 3650 \
    -newkey rsa:2048 \
    -keyout /app/certs/server.key \
    -out /app/certs/server.crt \
    -subj "/CN=nahan-pasarguard-bridge.railway.internal" \
    -addext "subjectAltName=DNS:nahan-pasarguard-bridge.railway.internal,DNS:altaria.proxy.rlwy.net"

EXPOSE 8080

CMD ["python", "app.py"]

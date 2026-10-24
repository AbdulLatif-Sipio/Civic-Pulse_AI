#!/bin/bash
# ==============================================================================
# CivicPulse AI - Automated Let's Encrypt SSL Setup for Custom Domains
# ==============================================================================

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: sudo ./deploy/enable_ssl.sh <DOMAIN_NAME> <CONTACT_EMAIL>"
    echo "Example: sudo ./deploy/enable_ssl.sh cleancity.example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "[*] Setting up Let's Encrypt SSL for domain: $DOMAIN ($EMAIL)"

# 1. Install Certbot
if command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y certbot
elif command -v yum >/dev/null 2>&1; then
    yum install -y epel-release && yum install -y certbot
fi

# 2. Temporarily stop Nginx container on port 80 to obtain certificate
docker compose stop nginx || true

# 3. Request Certificate
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

# 4. Generate SSL Nginx Configuration
mkdir -p deploy/ssl
cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem deploy/ssl/cert.pem
cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem deploy/ssl/key.pem

cat <<EOF > deploy/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout 65;
    client_max_body_size 25M;

    upstream backend_app {
        server backend:8000;
    }

    upstream frontend_app {
        server frontend:8501;
    }

    # Redirect all HTTP to HTTPS
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$host\$request_uri;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Strict Transport Security
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            proxy_pass http://backend_app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }

        location ^~ /admin-ui/ {
            proxy_pass http://frontend_app/;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }

        location ^~ /_stcore/ {
            proxy_pass http://frontend_app/_stcore/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }
    }
}
EOF

# Restart Nginx with SSL enabled
docker compose restart nginx
echo "[✓] SSL successfully activated! Visit: https://$DOMAIN"

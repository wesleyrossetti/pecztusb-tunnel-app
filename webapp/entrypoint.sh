#!/bin/sh

CERT_PATH="/etc/nginx/certs/painel-admin.laetonline.org_ecc/fullchain.cer"
KEY_PATH="/etc/nginx/certs/painel-admin.laetonline.org_ecc/painel-admin.laetonline.org.key"

echo "⏳ Aguardando certificados SSL..."

while [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; do
  sleep 2
done

echo "✅ Certificados encontrados. Iniciando NGINX..."
exec nginx -g "daemon off;"

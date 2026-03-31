#!/bin/bash
# Development entrypoint — generates RSA keys if they don't exist.
# Production uses keys from Secrets Manager via env vars (JWT_PRIVATE_KEY, JWT_PUBLIC_KEY).
set -e

if [ ! -f keys/private.pem ]; then
    echo "Generating RSA key pair for development..."
    mkdir -p keys
    openssl genrsa -out keys/private.pem 2048 2>/dev/null
    openssl rsa -in keys/private.pem -pubout -out keys/public.pem 2>/dev/null
    echo "RSA keys generated at keys/private.pem and keys/public.pem"
fi

exec "$@"

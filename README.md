# Real Estate App

A small FastAPI + React application for demonstrating real estate price estimations.
The project runs in Docker and supports HTTPS via Let's Encrypt certificates.

## Quick start

1. Copy `.env.example` to `.env` and adjust the variables if needed:
   ```
   GOOGLE_API_KEY=AIzaSyDwN8UV2bfiMz9afTicKRh6ynHgMGK3YwU
   LETSENCRYPT_HOST=real-estate-app.pro
   LETSENCRYPT_EMAIL=shumerrr@yandex.ru
   VIRTUAL_HOST=real-estate-app.pro
   ```
2. Build and start the stack:
   ```
   docker-compose up --build
   ```
   For production use:
   ```
   docker-compose -f docker-compose.prod.yml up -d
   ```

The nginx-proxy and companion containers will automatically obtain and renew HTTPS certificates for the domain specified in `LETSENCRYPT_HOST`.

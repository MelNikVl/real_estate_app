# Real Estate App

A small FastAPI + React application for demonstrating real estate price estimations.
The project runs in Docker and supports HTTPS via Certbot-managed certificates.

## Quick start

1. Copy `.env.example` to `.env` and adjust the variables if needed:
   ```
   GOOGLE_API_KEY=AIzaSyDwN8UV2bfiMz9afTicKRh6ynHgMGK3YwU
   CERTBOT_EMAIL=shumerrr@yandex.ru
   VIRTUAL_HOST=real-estate-app.pro
   REACT_APP_API_BASE_URL=http://backend:8000
   ```
2. Build and start the stack:
   ```
   docker-compose up --build
   ```
   For production use:
   ```
   docker-compose -f docker-compose.prod.yml up -d
   # Obtain certificates
   docker-compose -f docker-compose.prod.yml run --rm certbot
   # Reload nginx to use them
   docker-compose -f docker-compose.prod.yml restart nginx-proxy
   ```

The `certbot` service requests certificates for the domain specified in `VIRTUAL_HOST` and stores them in `certs/`. The `nginx-proxy` container serves these certificates.

The frontend uses `REACT_APP_API_BASE_URL` to contact the backend. With Docker Compose the correct value is `http://backend:8000`.

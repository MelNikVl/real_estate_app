# Real Estate App

A small FastAPI + React application for demonstrating real estate price estimations.
The project runs in Docker and supports HTTPS via Let's Encrypt certificates.

## Quick start

1. Create a `.env` file in the project root and set required variables:
   ```
   GOOGLE_API_KEY=your-google-api-key
   LETSENCRYPT_HOST=your.domain.com
   LETSENCRYPT_EMAIL=you@example.com
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

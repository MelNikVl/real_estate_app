FROM python:3.10-slim-buster
# frontend/Dockerfile
# Этап сборки (build stage)
# FROM python:3.10-slim-buster>>>>>>> 8db00ae (ssl_certificate:)
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build # или yarn build, если используешь yarn   


FROM nginx:stable-alpine
COPY --from=build-stage /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

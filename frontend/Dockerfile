# frontend/Dockerfile
# Этап сборки (build stage)
FROM python:3.10-slim-buster
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build # или yarn build, если используешь yarn   

# Этап продакшена (production stage)
FROM nginx:stable-alpine
COPY --from=build-stage /app/build /usr/share/nginx/html
# COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
FROM node:20 AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install

COPY . .
ARG VITE_API_BASE_URL
ARG VITE_OPENAPI_URL
RUN npm run build

# ---------- nginx ----------
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginxのデフォルトポート80

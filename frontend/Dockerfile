FROM node:20

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

# ---------- nginx ----------
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginxのデフォルトポート80
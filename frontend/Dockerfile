FROM node:22-alpine AS build

WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
RUN addgroup -S nginxuser && adduser -S nginxuser -G nginxuser
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chown -R nginxuser:nginxuser /var/cache/nginx /usr/share/nginx/html /etc/nginx \
    && touch /var/run/nginx.pid && chown nginxuser:nginxuser /var/run/nginx.pid
USER nginxuser
EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]

FROM node:22-alpine AS build

WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# OpenShift's "restricted" SCC runs this as an arbitrary UID in group 0 and
# never binds privileged port 80 (no CAP_NET_BIND_SERVICE), so nginx listens
# on 8080 (see nginx.conf) and every path it writes to at runtime —
# cache/temp dirs, the pid file — must be group-writable, not just
# owner-writable, since that arbitrary UID isn't the "nginxuser" below.
RUN addgroup -S nginxuser && adduser -S nginxuser -G nginxuser \
    && touch /var/run/nginx.pid \
    && chgrp -R 0 /var/cache/nginx /usr/share/nginx/html /etc/nginx /var/run/nginx.pid \
    && chmod -R g=u /var/cache/nginx /usr/share/nginx/html /etc/nginx /var/run/nginx.pid

USER 1001:0
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1:8080 || exit 1

CMD ["nginx", "-g", "daemon off;"]

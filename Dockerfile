FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
COPY test-data/requirements.json ./requirements.json

# Override the production .env value so the packaged frontend calls nginx proxy.
ARG VITE_BASE_URL=/api/v1
ENV VITE_BASE_URL=${VITE_BASE_URL}
RUN npm run build


FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN echo 'Types: deb\nURIs: https://mirrors.aliyun.com/debian\nSuites: trixie trixie-updates trixie-backports\nComponents: main contrib non-free non-free-firmware\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg' > /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

COPY backend/app ./app
COPY backend/app.py backend/excel_exporter.py backend/testcase_generator.py ./
COPY backend/template ./template

RUN mkdir -p data /usr/share/nginx/html /run/nginx \
    && rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
RUN sed -i 's|http://test-case-generate-backend:5000/v1/|http://127.0.0.1:5000/v1/|' /etc/nginx/conf.d/default.conf

COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["sh", "-c", "python app.py & exec nginx -g 'daemon off;'"]

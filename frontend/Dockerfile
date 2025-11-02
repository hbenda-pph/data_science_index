# Dockerfile para Frontend estático con Nginx
FROM nginx:alpine

# Copiar archivo HTML
COPY frontend/index.html /usr/share/nginx/html/index.html

# La URL de la API se detecta automáticamente en el JavaScript
# El script getApiUrl() en index.html maneja la detección

# Configuración de Nginx
RUN echo 'server { \
    listen 8080; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 8080

# Nginx se inicia automáticamente

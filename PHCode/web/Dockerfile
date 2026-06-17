FROM php:8.3-cli

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    --no-install-recommends && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
        | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && apt-get install -y caddy && \
    rm -rf /var/lib/apt/lists/*

COPY index.php /var/www/html/index.php
COPY Caddyfile /etc/caddy/Caddyfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3000
CMD ["/entrypoint.sh"]

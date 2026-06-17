#!/bin/sh

for port in 8001 8002 8003 8004; do
    php -S 0.0.0.0:$port -t /var/www/html \
        -d display_errors=On \
        -d error_reporting=32767 \
        -d max_input_vars=1000000 &
done

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile

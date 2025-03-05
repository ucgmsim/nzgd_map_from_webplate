#!/usr/bin/env sh

echo "Starting nginx"

uwsgi --ini /nzgd.ini &
nginx -g "daemon off;"

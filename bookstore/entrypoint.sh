#!/bin/sh
if [ -z "$FLAG" ]; then FLAG='GCUP{placeholder}'; fi
printf '%s\n' "$FLAG" > /flag
chmod 444 /flag
unset FLAG
exec python app.py

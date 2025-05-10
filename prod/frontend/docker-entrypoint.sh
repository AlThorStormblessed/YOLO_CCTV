#!/bin/sh
sed -i "s/backend:5003/localhost:5003/g" /app/.next/static/chunks/*.js
echo "Fixed backend references in JavaScript files"
exec "$@" 
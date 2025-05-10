#!/bin/sh
sed -i "s/backend:5003/model.viewer.in/g" /app/.next/static/chunks/*.js
sed -i "s/localhost:5003/model.viewer.in/g" /app/.next/static/chunks/*.js
echo "Fixed backend references in JavaScript files to use model.viewer.in"
exec "$@" 
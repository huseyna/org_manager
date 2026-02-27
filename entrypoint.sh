#!/bin/sh
echo "Checking database connection..."

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  echo "Database not ready, sleeping..."
  sleep 1
done

echo "Database is up!"
exec "$@"

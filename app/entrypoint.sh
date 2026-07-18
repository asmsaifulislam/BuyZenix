#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import socket; socket.create_connection(('${DB_HOST:-db}', ${DB_PORT:-5432}), timeout=2)" 2>/dev/null; do
  echo "  DB not ready, sleeping..."
  sleep 2
done
echo "PostgreSQL is up."

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true
python manage.py seed || true

# Create a default superuser if none exists (idempotent)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@buyzenix.com', 'admin12345')
    print('Created superuser: admin / admin12345')
" 2>/dev/null || true

exec gunicorn buyzenix.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

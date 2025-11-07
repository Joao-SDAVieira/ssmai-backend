#!/bin/sh

echo "🔄 Executando migrações..."
poetry run alembic upgrade head

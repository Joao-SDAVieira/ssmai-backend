#!/bin/sh

echo "🚀 Iniciando SSMai Backend..."

# Wait for database to be ready
echo "⏳ Aguardando banco de dados..."
until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB; do
  echo "⏳ Banco ainda não está pronto. Aguardando 2s..."
  sleep 2
done

echo "✅ Banco de dados pronto!"

# Run migrations
echo "🔄 Executando migrações..."
poetry run alembic upgrade head

# Test MCP connection (optional)
echo "🧪 Testando conexão MCP..."
python3 -c "
import os
import sys
sys.path.append('/app/src')
try:
    from ssmai_backend.mcp.postgres_server import PostgreSQLMCPServer
    server = PostgreSQLMCPServer()
    server.connect_database()
    print('✅ MCP connection test successful')
except Exception as e:
    print(f'⚠️  MCP connection test failed: {e}')
    print('🔄 Continuando mesmo assim...')
"

# Start the application
echo "🚀 Iniciando aplicação..."
poetry run uvicorn --host 0.0.0.0 src.ssmai_backend.app:app
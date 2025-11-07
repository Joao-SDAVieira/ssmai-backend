#!/bin/sh

echo "🔄 Executando migrações..."
poetry run alembic upgrade head

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

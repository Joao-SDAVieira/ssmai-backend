#!/usr/bin/env python3
"""
PostgreSQL MCP Server for SSMai
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional, Union
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG_VERSION = 2
except ImportError:
    import psycopg
    from psycopg.rows import dict_row
    PSYCOPG_VERSION = 3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLMCPServer:
    def __init__(self):
        self.connection = None
        self.tools = [
            {
                "name": "query_database",
                "description": "Execute a SQL query on the PostgreSQL database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all tables in the database",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "describe_table",
                "description": "Get the schema of a specific table",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to describe"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "count_records",
                "description": "Count the number of records in a table",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to count records"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        ]

    def connect_database(self):
        """Connect to PostgreSQL database"""
        import time
        
        # Try 'db' first (for Docker), then fallback to 'localhost' (for development)
        hosts_to_try = [os.getenv('POSTGRES_HOST', 'db'), 'localhost']
        
        # Retry logic for Docker startup
        max_retries = 30
        retry_delay = 2
        
        for host in hosts_to_try:
            for attempt in range(max_retries):
                try:
                    port = os.getenv('POSTGRES_PORT', '5432')
                    user = os.getenv('POSTGRES_USER', 'user')
                    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
                    database = os.getenv('POSTGRES_DB', 'ssmai_db')
                    
                    if attempt == 0:
                        logger.info(f"🔗 Tentando conectar ao PostgreSQL em {host}:{port}...")
                    else:
                        logger.info(f"🔗 Tentativa {attempt + 1}/{max_retries} para {host}:{port}...")
                    
                    if PSYCOPG_VERSION == 2:
                        self.connection = psycopg2.connect(
                            host=host,
                            port=port,
                            user=user,
                            password=password,
                            database=database,
                            cursor_factory=RealDictCursor,
                            connect_timeout=10
                        )
                    else:
                        self.connection = psycopg.connect(
                            host=host,
                            port=port,
                            user=user,
                            password=password,
                            dbname=database,
                            row_factory=dict_row,
                            connect_timeout=10
                        )
                    
                    # Test the connection
                    with self.connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    
                    logger.info(f"✅ Conectado ao PostgreSQL com sucesso em {host}:{port}!")
                    return True
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️  Tentativa {attempt + 1} falhou em {host}:{port} - {e}")
                        logger.info(f"🔄 Aguardando {retry_delay}s antes da próxima tentativa...")
                        time.sleep(retry_delay)
                    else:
                        logger.warning(f"⚠️  Todas as tentativas falharam em {host}:{port} - {e}")
                    
                    if self.connection:
                        try:
                            self.connection.close()
                        except:
                            pass
                        self.connection = None
        
        # Se chegou aqui, todas as tentativas falharam
        raise Exception("Não foi possível conectar ao PostgreSQL em nenhum dos hosts após várias tentativas")

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query"""
        try:
            logger.info(f"🔧 DEBUG: Executando query: {query[:100]}...")
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    # Convert RealDictRow to regular dict
                    results = [dict(row) for row in results]
                    logger.info(f"🔧 DEBUG: Query executada com sucesso. Rows: {len(results)}")
                    return {
                        "content": f"Results:\n{json.dumps(results, indent=2, default=str)}"
                    }
                else:
                    self.connection.commit()
                    return {
                        "content": f"Query executed successfully. Rows affected: {cursor.rowcount}"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erro na query: {e}")
            return {
                "content": f"Error executing query: {str(e)}"
            }

    def list_tables(self) -> Dict[str, Any]:
        """List all tables"""
        try:
            logger.info("🔧 DEBUG: Executando query list_tables...")
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                tables = [row['table_name'] for row in results]
                logger.info(f"🔧 DEBUG: Query list_tables executada com sucesso. Rows: {len(tables)}")
                
                return {
                    "content": f"Tables found: {len(tables)}\n" + "\n".join(f"- {table}" for table in tables)
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao listar tabelas: {e}")
            return {
                "content": f"Error listing tables: {str(e)}"
            }

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Describe table schema"""
        try:
            logger.info(f"🔧 DEBUG: Descrevendo tabela '{table_name}'...")
            query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (table_name,))
                results = cursor.fetchall()
                
                if not results:
                    return {
                        "content": f"Table '{table_name}' not found"
                    }
                
                # Convert to list of dicts
                columns = [dict(row) for row in results]
                logger.info(f"🔧 DEBUG: Tabela descrita com sucesso. Colunas: {len(columns)}")
                
                return {
                    "content": f"Schema for table '{table_name}':\n{json.dumps(columns, indent=2, default=str)}"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao descrever tabela: {e}")
            return {
                "content": f"Error describing table: {str(e)}"
            }

    def count_records(self, table_name: str) -> Dict[str, Any]:
        """Count records in table"""
        try:
            logger.info(f"🔧 DEBUG: Contando registros da tabela '{table_name}'...")
            query = f"SELECT COUNT(*) as total FROM {table_name}"
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                total = result['total']
                
                logger.info(f"🔧 DEBUG: Count executado com sucesso. Total: {total}")
                
                return {
                    "content": f"Total records: {total}"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao contar registros: {e}")
            return {
                "content": f"Error counting records: {str(e)}"
            }

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        logger.info(f"🔧 DEBUG: Executando tool '{name}' com args: {arguments}")
        
        try:
            if name == "query_database":
                return self.execute_query(arguments.get("query", ""))
            elif name == "list_tables":
                return self.list_tables()
            elif name == "describe_table":
                return self.describe_table(arguments.get("table_name", ""))
            elif name == "count_records":
                return self.count_records(arguments.get("table_name", ""))
            else:
                return {
                    "content": f"Unknown tool: {name}"
                }
        except Exception as e:
            logger.error(f"❌ Erro ao executar tool '{name}': {e}")
            return {
                "content": f"Error executing tool {name}: {str(e)}"
            }

    async def handle_stdio(self):
        """Handle MCP communication via stdio"""
        logger.info("PostgreSQL MCP Server running on stdio")
        
        # Connect to database
        try:
            self.connect_database()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            # Send error response and exit
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32000,
                    "message": f"Database connection failed: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            sys.exit(1)
        
        try:
            while True:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                try:
                    message = json.loads(line.strip())
                    response = None
                    
                    if message.get("method") == "tools/list":
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "result": {
                                "tools": self.tools
                            }
                        }
                    elif message.get("method") == "tools/call":
                        params = message.get("params", {})
                        tool_name = params.get("name")
                        tool_args = params.get("arguments", {})
                        
                        result = self.call_tool(tool_name, tool_args)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "result": result
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "error": {
                                "code": -32601,
                                "message": "Method not found"
                            }
                        }
                    
                    # Send response to stdout
                    if response:
                        print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    # Send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id") if 'message' in locals() else None,
                        "error": {
                            "code": -32000,
                            "message": str(e)
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            if self.connection:
                try:
                    self.connection.close()
                    logger.info("Database connection closed")
                except:
                    pass

def main():
    """Main entry point"""
    server = PostgreSQLMCPServer()
    
    try:
        asyncio.run(server.handle_stdio())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

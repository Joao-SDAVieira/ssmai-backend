"""
MCP Client for SSMai - Handles communication with Claude 3.5 Haiku via AWS Bedrock
"""

import asyncio
import json
import logging
import subprocess
import re
from typing import Dict, List, Any, Optional
import boto3
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TableSchema(BaseModel):
    tableName: str
    columns: List[Dict[str, Any]]
    recordCount: int
    sampleData: List[Dict[str, Any]]

class DatabaseContext(BaseModel):
    tables: List[TableSchema]
    relationships: List[str]
    summary: str

class MCPClient:
    def __init__(self, inference_profile_id: Optional[str] = None):
        self.model_id = inference_profile_id or "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('BEDROCK_AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
        )
        self.mcp_process = None
        self.tools = []
        self.database_context = ""
        
        # SSMai Context
        self.ssmai_context = """Você é o assistente do SSMai (Smart Stock Management AI).

        Assistente SSMai (Smart Stock Management AI)

        Função:
        Você é o assistente inteligente de gestão de estoque SSMai (Smart Stock Management AI).

        Regra Fundamental:
        Jamais invente, assuma ou imagine dados.
        Responda somente com base nas informações fornecidas no contexto.
        Se algo não estiver disponível, informe explicitamente.

        Suas Capacidades:
        - Consultar produtos, categorias e estoques reais
        - Visualizar históricos e movimentações existentes
        - Responder apenas com dados factuais e verificáveis

        Quando Não Houver Dados:
        Se o contexto não contiver informações suficientes, responda de forma clara:
        "Não há dados disponíveis."
        ou
        "Não foram encontrados [produtos/movimentações/etc] para este período."

        Jamais crie:
        - Nomes de produtos
        - Quantidades
        - Transações ou movimentações fictícias

        Estilo de Resposta:
        - Seja conciso e direto (máximo de 4–5 linhas)
        - Utilize apenas dados reais do contexto
        - Evite explicações longas ou especulações
        - Priorize clareza e objetividade

        Exemplo de Resposta Correta:
        Com dados: "Foram registradas 15 unidades vendidas do produto X no período informado."
        Sem dados: "Não foram encontradas movimentações para este período.\""""

    async def connect_to_server(self, server_path: str):
        """Connect to MCP server"""
        try:
            logger.info(f"🔌 Connecting to MCP server: {server_path}")
            
            # Start the MCP server process
            self.mcp_process = await asyncio.create_subprocess_exec(
                'python3', server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait a bit for the server to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if self.mcp_process.returncode is not None:
                stderr_output = await self.mcp_process.stderr.read()
                raise Exception(f"MCP server process failed to start: {stderr_output.decode()}")
            
            # Get available tools
            await self._initialize_tools()
            
            # Map database structure
            logger.info("🔍 Mapeando estrutura do banco de dados...")
            self.database_context = await self._map_database_structure()
            
            logger.info("✅ Connected to MCP server successfully")
            
        except Exception as e:
            logger.error(f"❌ Error connecting to MCP server: {e}")
            if self.mcp_process:
                try:
                    stderr_output = await self.mcp_process.stderr.read()
                    if stderr_output:
                        logger.error(f"Server stderr: {stderr_output.decode()}")
                except:
                    pass
            raise

    async def _send_mcp_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send request to MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.mcp_process.stdin.write(request_json.encode())
            await self.mcp_process.stdin.drain()
            
            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    self.mcp_process.stdout.readline(), 
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                raise Exception("MCP server timeout - no response received")
            
            if not response_line:
                raise Exception("MCP server closed connection")
            
            response_text = response_line.decode().strip()
            if not response_text:
                raise Exception("Empty response from MCP server")
            
            try:
                response = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from MCP server: {response_text}")
                raise Exception(f"Invalid JSON response: {e}")
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")
            
            return response.get("result", {})
            
        except Exception as e:
            logger.error(f"MCP communication error: {e}")
            raise

    async def _initialize_tools(self):
        """Initialize available tools from MCP server"""
        try:
            result = await self._send_mcp_request("tools/list")
            self.tools = result.get("tools", [])
            
            logger.info(f"Connected to server with tools: {[tool['name'] for tool in self.tools]}")
            
        except Exception as e:
            logger.error(f"Error initializing tools: {e}")
            raise

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        try:
            result = await self._send_mcp_request("tools/call", {
                "name": name,
                "arguments": arguments
            })
            return result
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return {"content": f"Error: {str(e)}"}

    async def _map_database_structure(self) -> str:
        """Map the complete database structure"""
        try:
            db_context = DatabaseContext(tables=[], relationships=[], summary="")
            
            # Get all tables
            tables_result = await self.call_tool("list_tables", {})
            tables_content = tables_result.get("content", "")
            
            # Extract table names
            table_names = []
            for line in tables_content.split('\n'):
                if line.startswith('- '):
                    table_names.append(line[2:].strip())
            
            # Analyze each table
            for table_name in table_names:
                logger.info(f"📋 Analisando tabela: {table_name}")
                
                # Get table schema
                try:
                    schema_result = await self.call_tool("describe_table", {"table_name": table_name})
                    schema_content = schema_result.get("content", "")
                    
                    # Parse schema JSON
                    schema_data = []
                    if "Schema for table" in schema_content:
                        json_match = re.search(r':\n(.*)', schema_content, re.DOTALL)
                        if json_match:
                            schema_data = json.loads(json_match.group(1))
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao obter schema para {table_name}: {e}")
                    schema_data = []
                
                # Get record count
                count_result = await self.call_tool("count_records", {"table_name": table_name})
                count_content = count_result.get("content", "")
                count_match = re.search(r'Total records: (\d+)', count_content)
                record_count = int(count_match.group(1)) if count_match else 0
                
                # Get sample data
                sample_data = []
                if record_count > 0:
                    try:
                        sample_result = await self.call_tool("query_database", {
                            "query": f"SELECT * FROM {table_name} LIMIT 3"
                        })
                        sample_content = sample_result.get("content", "")
                        
                        json_match = re.search(r'Results:\n(.*)', sample_content, re.DOTALL)
                        if json_match:
                            sample_data = json.loads(json_match.group(1))
                    except Exception as e:
                        logger.warning(f"⚠️  Erro ao obter dados de exemplo para {table_name}")
                
                db_context.tables.append(TableSchema(
                    tableName=table_name,
                    columns=schema_data,
                    recordCount=record_count,
                    sampleData=sample_data
                ))
            
            # Generate relationships
            db_context.relationships = self._find_relationships(db_context.tables)
            
            # Generate summary
            db_context.summary = self._generate_summary(db_context)
            
            logger.info("✅ Mapeamento do banco concluído!")
            
            return self._format_database_context(db_context)
            
        except Exception as e:
            logger.error(f"❌ Erro ao mapear banco: {e}")
            return "Erro ao mapear estrutura do banco de dados."

    def _find_relationships(self, tables: List[TableSchema]) -> List[str]:
        """Find relationships between tables"""
        relationships = []
        
        for table in tables:
            for column in table.columns:
                column_name = column.get('column_name', '')
                # Look for foreign key patterns
                if column_name.startswith('id_') or column_name.endswith('_id'):
                    referenced_table = column_name.replace('id_', '').replace('_id', '')
                    plural_table = referenced_table + 's'
                    
                    # Check if referenced table exists
                    target_table = None
                    for t in tables:
                        if (t.tableName == referenced_table or 
                            t.tableName == plural_table or
                            t.tableName == referenced_table.rstrip('s')):
                            target_table = t
                            break
                    
                    if target_table:
                        relationships.append(f"{table.tableName}.{column_name} → {target_table.tableName}.id")
        
        return relationships

    def _generate_summary(self, db_context: DatabaseContext) -> str:
        """Generate database summary"""
        total_tables = len(db_context.tables)
        total_records = sum(table.recordCount for table in db_context.tables)
        main_tables = sorted(
            [table for table in db_context.tables if table.recordCount > 0],
            key=lambda x: x.recordCount,
            reverse=True
        )[:5]
        
        main_tables_str = ', '.join(f"{table.tableName} ({table.recordCount} registros)" 
                                   for table in main_tables)
        
        return f"""Sistema possui {total_tables} tabelas com {total_records} registros totais.
Principais tabelas: {main_tables_str}"""

    def _format_database_context(self, db_context: DatabaseContext) -> str:
        """Format database context for AI"""
        context = f"\n=== CONTEXTO DO BANCO DE DADOS SSMai ===\n\n"
        context += f"RESUMO: {db_context.summary}\n\n"
        
        context += "ESTRUTURA DAS TABELAS:\n"
        for table in db_context.tables:
            context += f"\n• {table.tableName} ({table.recordCount} registros)\n"
            
            if table.columns:
                context += "  Colunas:\n"
                for col in table.columns[:5]:  # Limit columns shown
                    context += f"    - {col.get('column_name')}: {col.get('data_type')}\n"
            
            if table.sampleData:
                context += "  Dados de exemplo:\n"
                for i, row in enumerate(table.sampleData[:2]):  # Show 2 sample rows
                    context += f"    Registro {i+1}: {dict(list(row.items())[:3])}\n"
        
        if db_context.relationships:
            context += f"\nRELACIONAMENTOS:\n"
            for rel in db_context.relationships[:10]:  # Show first 10
                context += f"  - {rel}\n"
        
        context += "\n=== FIM DO CONTEXTO ===\n"
        return context

    def _clean_response(self, response: str) -> str:
        """Remove technical messages from AI response"""
        logger.info(f"🧹 Cleaning response with {len(response.split())} lines")
        lines = response.split('\n')
        filtered_lines = []
        removed_lines = []
        
        tech_patterns = [
            re.compile(r'^\[Calling tool .* with args .*\]$'),
            re.compile(r'^\[Tool call:.*\]$'),
            re.compile(r'^\[Using tool:.*\]$'),
            re.compile(r'^\[Executing:.*\]$'),
            re.compile(r'^Tool result:', re.IGNORECASE),
            re.compile(r'^Calling function:', re.IGNORECASE),
            re.compile(r'^Function call:', re.IGNORECASE)
        ]
        
        for line in lines:
            line_stripped = line.strip()
            if not any(pattern.match(line_stripped) for pattern in tech_patterns):
                filtered_lines.append(line)
            else:
                removed_lines.append(line_stripped)
        
        if removed_lines:
            logger.info(f"🗑️  Removed {len(removed_lines)} technical lines")
        
        cleaned = '\n'.join(filtered_lines).strip()
        logger.info(f"🧹 Cleaning complete: {len(cleaned)} characters final")
        return cleaned

    async def process_query(self, query: str) -> str:
        """Process user query using Claude 3.5 Haiku"""
        try:
            # Create message with context
            full_context = f"{self.ssmai_context}\n{self.database_context}"
            
            messages = [{
                "role": "user",
                "content": f"{full_context}\n\nUsuário: {query}"
            }]
            
            # Prepare tools for Bedrock
            tools_for_bedrock = []
            if self.tools:
                for tool in self.tools:
                    tools_for_bedrock.append({
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "input_schema": tool["input_schema"]
                    })
            
            # Create request payload
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,  # Increased token limit
                "top_k": 250,
                "stop_sequences": [],
                "temperature": 0.7,
                "top_p": 0.999,
                "messages": messages
            }
            
            if tools_for_bedrock:
                payload["tools"] = tools_for_bedrock
            
            # Invoke Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            final_text = []
            
            # Process response content
            for content in response_body.get("content", []):
                if content["type"] == "text":
                    final_text.append(content["text"])
                elif content["type"] == "tool_use":
                    tool_name = content["name"]
                    tool_args = content["input"]
                    
                    # Call the MCP tool
                    result = await self.call_tool(tool_name, tool_args)
                    
                    # Add technical message (will be filtered later)
                    final_text.append(f"[Calling tool {tool_name} with args {json.dumps(tool_args)}]")
                    
                    # Handle follow-up with tool result
                    messages.append({
                        "role": "assistant",
                        "content": [{
                            "type": "tool_use",
                            "id": content["id"],
                            "name": tool_name,
                            "input": tool_args
                        }]
                    })
                    
                    tool_result_content = result.get("content", "")
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content["id"],
                            "content": tool_result_content
                        }]
                    })
                    
                    # Follow-up request
                    follow_up_payload = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 4096,  # Increased token limit for follow-up
                        "top_k": 250,
                        "stop_sequences": [],
                        "temperature": 0.7,
                        "top_p": 0.999,
                        "messages": messages
                    }
                    
                    if tools_for_bedrock:
                        follow_up_payload["tools"] = tools_for_bedrock
                    
                    follow_up_response = self.bedrock_client.invoke_model(
                        modelId=self.model_id,
                        contentType="application/json",
                        accept="application/json",
                        body=json.dumps(follow_up_payload)
                    )
                    
                    follow_up_body = json.loads(follow_up_response['body'].read())
                    
                    if (follow_up_body.get("content") and 
                        follow_up_body["content"][0]["type"] == "text"):
                        final_text.append(follow_up_body["content"][0]["text"])
            
            raw_response = "\n".join(final_text)
            logger.info(f"🔍 Raw response length: {len(raw_response)} characters")
            logger.info(f"🔍 Raw response preview: {raw_response[:200]}...")
            cleaned_response = self._clean_response(raw_response)
            logger.info(f"🔍 Cleaned response length: {len(cleaned_response)} characters")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error: {str(e)}"

    async def cleanup(self):
        """Cleanup MCP connection"""
        if self.mcp_process and self.mcp_process.returncode is None:
            try:
                self.mcp_process.terminate()
                await asyncio.wait_for(self.mcp_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.mcp_process.kill()
                await self.mcp_process.wait()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    def is_connected(self) -> bool:
        """Check if MCP server is connected and running"""
        return (
            self.mcp_process is not None and 
            self.mcp_process.returncode is None and
            len(self.tools) > 0
        )
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool['name'] for tool in self.tools]
    
    def get_database_context(self) -> str:
        """Get the current database context"""
        return self.database_context

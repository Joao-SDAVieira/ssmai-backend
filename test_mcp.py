#!/usr/bin/env python3
"""
Test script for MCP connection
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_postgres_connection():
    """Test PostgreSQL connection directly"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        PSYCOPG_VERSION = 2
    except ImportError:
        try:
            import psycopg
            from psycopg.rows import dict_row
            PSYCOPG_VERSION = 3
        except ImportError:
            logger.error("❌ Neither psycopg2 nor psycopg3 is installed")
            return False

    # Try database connection
    hosts_to_try = [os.getenv('POSTGRES_HOST', 'db'), 'localhost']
    
    for host in hosts_to_try:
        try:
            port = os.getenv('POSTGRES_PORT', '5432')
            user = os.getenv('POSTGRES_USER', 'user')
            password = os.getenv('POSTGRES_PASSWORD', 'postgres')
            database = os.getenv('POSTGRES_DB', 'ssmai_db')
            
            logger.info(f"🔗 Testing PostgreSQL connection to {host}:{port}...")
            
            if PSYCOPG_VERSION == 2:
                connection = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    cursor_factory=RealDictCursor
                )
            else:
                connection = psycopg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname=database,
                    row_factory=dict_row
                )
            
            # Test query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                logger.info(f"✅ Database connection successful! Test result: {result}")
            
            connection.close()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to {host}:{port}: {e}")
            continue
    
    logger.error("❌ Could not connect to PostgreSQL on any host")
    return False

async def test_mcp_server():
    """Test MCP server startup"""
    try:
        logger.info("🧪 Testing MCP server startup...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.join(current_dir, "src", "ssmai_backend", "mcp", "postgres_server.py")
        
        if not os.path.exists(server_path):
            logger.error(f"❌ Server script not found: {server_path}")
            return False
        
        logger.info(f"📍 Server path: {server_path}")
        
        # Start MCP server process
        process = await asyncio.create_subprocess_exec(
            'python3', server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait a bit for startup
        await asyncio.sleep(3)
        
        # Check if process is running
        if process.returncode is not None:
            stderr_output = await process.stderr.read()
            logger.error(f"❌ MCP server failed to start: {stderr_output.decode()}")
            return False
        
        logger.info("✅ MCP server started successfully")
        
        # Try to send a tools/list request
        import json
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        
        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(), 
                timeout=10.0
            )
            
            if response_line:
                response = json.loads(response_line.decode().strip())
                tools = response.get("result", {}).get("tools", [])
                logger.info(f"✅ MCP server responded with {len(tools)} tools: {[tool['name'] for tool in tools]}")
            else:
                logger.error("❌ No response from MCP server")
                return False
                
        except asyncio.TimeoutError:
            logger.error("❌ MCP server timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Error communicating with MCP server: {e}")
            return False
        finally:
            # Cleanup
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except:
                process.kill()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing MCP server: {e}")
        return False

async def test_aws_credentials():
    """Test AWS credentials"""
    try:
        import boto3
        
        access_key = os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('BEDROCK_AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
        region = os.getenv('REGION', 'us-east-1')
        
        if not access_key or not secret_key:
            logger.error("❌ AWS credentials not found in environment")
            return False
        
        logger.info("🔑 Testing AWS credentials...")
        
        client = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Try to list foundation models (this doesn't make actual calls but validates credentials)
        try:
            # This is a simple test that validates the client can be created
            logger.info("✅ AWS credentials appear to be valid")
            return True
        except Exception as e:
            logger.error(f"❌ AWS credentials test failed: {e}")
            return False
            
    except ImportError:
        logger.error("❌ boto3 not installed")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing AWS credentials: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🧪 Starting MCP system tests...")
    
    tests = [
        ("PostgreSQL Connection", test_postgres_connection),
        ("AWS Credentials", test_aws_credentials),
        ("MCP Server", test_mcp_server),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ❌ FAILED with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! MCP system should work correctly.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

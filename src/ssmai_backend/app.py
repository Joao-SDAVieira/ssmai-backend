import asyncio
from http import HTTPStatus
from sys import platform

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ssmai_backend.routers import ai_analysis, enterprises, products, stock
from ssmai_backend.routers.users import fastapi_users, inject_creator, router
from ssmai_backend.schemas.root_schemas import Message
from ssmai_backend.schemas.users_schemas import (
    BaseUserSchema,
    UserPublic,
    UserSchema,
)
from ssmai_backend.security.user_settings import auth_backend
from ssmai_backend.mcp.client import MCPClient
from pydantic import BaseModel, Field
from typing import Optional
import logging
import time
from datetime import datetime

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for MCP
class ChatRequest(BaseModel):
    message: str = Field(..., example="Quantos produtos temos no estoque?")

class SuccessResponse(BaseModel):
    status: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ChatResponse(SuccessResponse):
    query: str
    response: str
    processing_time: str

app = FastAPI(title="SSMai API")

# Import global MCP container
from ssmai_backend.globals import mcp_container

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "SSMai API"
    }

# API Routes for MCP Chat (uses default MCP connection)
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ssmai(request: ChatRequest):
    """
    Chat with SSMai Assistant

    The assistant can answer questions about:
    - Product inventory and counts
    - Stock movements and transactions
    - Company information
    - Database structure and relationships
    - System summaries and reports
    """
    if not mcp_container.client:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                error="MCP service unavailable",
                message="MCP server is not connected. Please check server logs and try again later."
            ).dict()
        )

    user_query = request.message

    try:
        logger.info(f"💬 Processing query: {user_query}")

        start_time = time.time()
        response = await mcp_container.client.process_query(user_query)
        processing_time = time.time() - start_time

        return ChatResponse(
            query=user_query,
            response=response,
            processing_time=f"{processing_time*1000:.0f}ms"
        )

    except Exception as e:
        logger.error(f"Query processing error: {e}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Query processing failed",
                message=str(e)
            ).dict()
        )

@app.on_event("startup")
async def startup_event():
    """Auto-connect to MCP server on startup with default settings"""
    try:
        logger.info("🚀 Auto-connecting to MCP server...")
        mcp_container.client = MCPClient("us.anthropic.claude-3-5-haiku-20241022-v1:0")

        # Use absolute path to avoid path issues
        import os

        # Try different possible paths for the MCP server
        possible_paths = [
            # Docker environment path
            "/app/src/ssmai_backend/mcp/postgres_server.py",
            # Development environment path
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp", "postgres_server.py"),
            # Alternative Docker path
            "./src/ssmai_backend/mcp/postgres_server.py"
        ]

        server_path = None
        for path in possible_paths:
            if os.path.exists(path):
                server_path = path
                break

        if not server_path:
            raise Exception(f"MCP server script not found in any of: {possible_paths}")

        logger.info(f"🔧 Server path: {server_path}")
        await mcp_container.client.connect_to_server(server_path)
        logger.info("✅ MCP server connected successfully on startup")
    except Exception as e:
        logger.error(f"⚠️  Failed to auto-connect MCP server: {e}")
        # Não falhar a aplicação se o MCP não conectar
        logger.info("🔄 Application will continue without MCP connection")
        mcp_container.client = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if mcp_container.client:
        await mcp_container.client.cleanup()

app.include_router(products.router)
app.include_router(router)
app.include_router(stock.router)
app.include_router(enterprises.router)
app.include_router(ai_analysis.router)
app.include_router(chatbot.router)

origins = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=False),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserPublic, BaseUserSchema),
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(inject_creator)]
)
app.include_router(
    fastapi_users.get_users_router(
        UserPublic, UserSchema, requires_verification=False
    ),
    prefix="/users",
    tags=["users"],
)


@app.get("/", status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {
        "message": "Smart Stock management AI, "
        "Gerencie seu estoque de forma eficaz"
    }

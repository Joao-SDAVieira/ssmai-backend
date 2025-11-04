"""
SSMai API - Chatbot Router for Smart Stock Management AI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
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

# Router for chatbot endpoints
router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ssmai(request: ChatRequest):
    """
    Chat with SSMai Assistant - Uses global MCP connection from main app
    
    The assistant can answer questions about:
    - Product inventory and counts
    - Stock movements and transactions  
    - Company information
    - Database structure and relationships
    - System summaries and reports
    """
    # Import here to avoid circular imports
    from ssmai_backend.globals import mcp_container
    
    logger.info(f"🔍 DEBUG: mcp_client status: {mcp_container.client is not None}")
    logger.info(f"🔍 DEBUG: mcp_client type: {type(mcp_container.client)}")
    
    if not mcp_container.client:
        logger.error("❌ MCP client is None - service unavailable")
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                error="MCP service unavailable",
                message="MCP server is not connected. The service starts automatically."
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
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Query processing failed",
                message=str(e)
            ).dict()
        )

@router.get("/database/info")
async def get_database_info():
    """Get database information"""
    from ssmai_backend.globals import mcp_container
    
    if not mcp_container.client:
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                error="MCP service unavailable",
                message="MCP server is not connected. The service starts automatically."
            ).dict()
        )
    
    try:
        db_context = mcp_container.client.get_database_context()
        
        return {
            "status": "success",
            "database_info": {
                "has_context": bool(db_context),
                "context_length": len(db_context) if db_context else 0,
                "summary": db_context[:500] + "..." if db_context else None
            },
            "tools": mcp_container.client.get_available_tools(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database info error: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get database info",
                message=str(e)
            ).dict()
        )

@router.get("/products/count")
async def get_products_count():
    """Get product count - Quick endpoint to get the total number of products"""
    from ssmai_backend.globals import mcp_container
    
    if not mcp_container.client:
        raise HTTPException(status_code=503, detail={"error": "MCP service unavailable"})
    
    try:
        response = await mcp_container.client.process_query('Quantos produtos temos no total?')
        return {
            "count": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/stock/summary")
async def get_stock_summary():
    """Get system summary - Quick endpoint to get a comprehensive summary"""
    from ssmai_backend.globals import mcp_container
    
    if not mcp_container.client:
        raise HTTPException(status_code=503, detail={"error": "MCP service unavailable"})
    
    try:
        response = await mcp_container.client.process_query('Mostre um resumo do sistema: produtos, empresas e movimentações')
        return {
            "summary": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/status")
async def get_mcp_status():
    """Get MCP service status"""
    from ssmai_backend.globals import mcp_container
    
    status = {
        "mcp_client_exists": mcp_container.client is not None,
        "connected": mcp_container.client is not None,
        "tools_available": [],
        "database_context_loaded": False,
        "timestamp": datetime.now().isoformat()
    }
    
    if mcp_container.client:
        status["tools_available"] = mcp_container.client.get_available_tools()
        status["database_context_loaded"] = bool(mcp_container.client.get_database_context())
    
    return status


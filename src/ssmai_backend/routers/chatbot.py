"""
SSMai API - Chatbot Router for Smart Stock Management AI
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import logging
import time
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import get_session
from ssmai_backend.models.user import User
from ssmai_backend.routers.users import fastapi_users
from ssmai_backend.services.chat_history_service import ChatHistoryService
from ssmai_backend.schemas.chat_schemas import (
    ChatHistoryResponse,
    ChatSessionsResponse,
    ChatConversationResponse,
    ClearHistoryResponse
)

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
    session_id: str
    conversation_id: int

# Router for chatbot endpoints
router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)

# Type aliases for dependencies
T_CurrentUser = Annotated[User, Depends(fastapi_users.current_user())]
T_Session = Annotated[AsyncSession, Depends(get_session)]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ssmai(request: ChatRequest, current_user: T_CurrentUser, session: T_Session):
    """
    Chat with SSMai Assistant - Uses global MCP connection from main app
    
    The assistant can answer questions about:
    - Product inventory and counts (filtered by user's company)
    - Stock movements and transactions (filtered by user's company)
    - Company information (user's company only)
    - Database structure and relationships
    - System summaries and reports (filtered by user's company)
    
    Requires authentication. Only returns data from the user's company.
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
        logger.info(f"💬 Processing query for user {current_user.id} from company {current_user.id_empresas}: {user_query}")
        
        start_time = time.time()
        response = await mcp_container.client.process_query_with_company_filter(user_query, current_user.id_empresas)
        processing_time = time.time() - start_time
        processing_time_ms = int(processing_time * 1000)
        
        # Save conversation to history (session_id will be auto-generated based on user)
        conversation = await ChatHistoryService.save_conversation(
            session=session,
            user=current_user,
            user_message=user_query,
            assistant_response=response,
            processing_time_ms=processing_time_ms
        )
        
        return ChatResponse(
            query=user_query,
            response=response,
            processing_time=f"{processing_time_ms}ms",
            session_id=conversation.session_id,
            conversation_id=conversation.id
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

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    current_user: T_CurrentUser,
    session: T_Session,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip")
):
    """
    Get chat history for the current user
    
    Returns the conversation history with pagination support.
    """
    try:
        history = await ChatHistoryService.get_user_conversations(
            session=session,
            user=current_user,
            limit=limit,
            offset=offset
        )
        return history
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get chat history",
                message=str(e)
            ).dict()
        )


async def get_session_conversations(
    session_id: str,
    current_user: T_CurrentUser,
    session: T_Session
):
    """
    Get all conversations from a specific session
    
    Returns all conversations in chronological order for the given session.
    """
    try:
        conversations = await ChatHistoryService.get_session_conversations(
            session=session,
            user=current_user,
            session_id=session_id
        )
        
        if not conversations:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="Session not found",
                    message=f"No conversations found for session {session_id}"
                ).dict()
            )
        
        return conversations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get session conversations",
                message=str(e)
            ).dict()
        )


@router.delete("/history", response_model=ClearHistoryResponse)
async def clear_chat_history(
    current_user: T_CurrentUser,
    session: T_Session,
    session_id: Optional[str] = Query(None, description="Specific session ID to clear (if not provided, clears all history)")
):
    """
    Clear chat history for the current user
    
    If session_id is provided, clears only that session.
    If session_id is not provided, clears all chat history.
    """
    try:
        result = await ChatHistoryService.clear_user_history(
            session=session,
            user=current_user,
            session_id=session_id
        )
        
        logger.info(f"🗑️ Cleared {result.cleared_conversations} conversations for user {current_user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to clear chat history",
                message=str(e)
            ).dict()
        )





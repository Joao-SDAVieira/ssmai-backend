from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatConversationBase(BaseModel):
    user_message: str = Field(..., example="Quantos produtos temos no estoque?")


class ChatConversationCreate(ChatConversationBase):
    session_id: str = Field(..., example="session_123456")
    assistant_response: str = Field(..., example="Você possui 22 produtos no estoque.")
    processing_time_ms: Optional[int] = Field(None, example=1500)


class ChatConversationResponse(ChatConversationBase):
    id: int
    session_id: str
    assistant_response: str
    processing_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    conversations: List[ChatConversationResponse]
    total_count: int
    session_count: int


class ChatSessionResponse(BaseModel):
    session_id: str 
    conversation_count: int
    last_message_at: datetime
    preview: str  # First 100 chars of the last message


class ChatSessionsResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    total_sessions: int


class ClearHistoryResponse(BaseModel):
    message: str
    cleared_conversations: int
    timestamp: datetime = Field(default_factory=datetime.now)

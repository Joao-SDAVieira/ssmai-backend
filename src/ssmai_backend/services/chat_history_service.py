from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.chat_conversation import ChatConversation
from ssmai_backend.models.user import User
from ssmai_backend.schemas.chat_schemas import (
    ChatConversationCreate,
    ChatConversationResponse,
    ChatHistoryResponse,
    ChatSessionResponse,
    ChatSessionsResponse,
    ClearHistoryResponse
)


class ChatHistoryService:
    """Service for managing chat conversation history"""
    
    @staticmethod
    async def get_or_create_active_session(
        session: AsyncSession,
        user: User
    ) -> str:
        """Get the current active session for a user, or create a new one"""
        
        # Look for the most recent conversation from today
        from datetime import datetime, time
        today_start = datetime.combine(datetime.now().date(), time.min)
        
        recent_conversation_query = (
            select(ChatConversation.session_id)
            .where(
                ChatConversation.user_id == user.id,
                ChatConversation.created_at >= today_start
            )
            .order_by(desc(ChatConversation.created_at))
            .limit(1)
        )
        
        result = await session.execute(recent_conversation_query)
        recent_session_id = result.scalar_one_or_none()
        
        if recent_session_id:
            # Check if the last message was more than 30 minutes ago
            last_conversation_query = (
                select(ChatConversation.created_at)
                .where(
                    ChatConversation.user_id == user.id,
                    ChatConversation.session_id == recent_session_id
                )
                .order_by(desc(ChatConversation.created_at))
                .limit(1)
            )
            
            result = await session.execute(last_conversation_query)
            last_conversation_time = result.scalar_one_or_none()
            
            if last_conversation_time:
                # If last message was less than 30 minutes ago, continue the session
                time_diff = datetime.now() - last_conversation_time
                if time_diff.total_seconds() < 1800:  # 30 minutes
                    return recent_session_id
        
        # Create new session if no recent session or it's been too long
        return ChatHistoryService.generate_session_id()
    
    @staticmethod
    async def save_conversation(
        session: AsyncSession,
        user: User,
        user_message: str,
        assistant_response: str,
        processing_time_ms: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> ChatConversation:
        """Save a conversation to the database"""
        
        # Get or create active session if not provided
        if not session_id:
            session_id = await ChatHistoryService.get_or_create_active_session(session, user)
        
        conversation = ChatConversation(
            user_id=user.id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            processing_time_ms=processing_time_ms
        )
        
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        
        return conversation
    
    @staticmethod
    async def save_conversation_new_session(
        session: AsyncSession,
        user: User,
        user_message: str,
        assistant_response: str,
        processing_time_ms: Optional[int] = None
    ) -> ChatConversation:
        """Save a conversation to a new session (force new session creation)"""
        
        new_session_id = ChatHistoryService.generate_session_id()
        
        conversation = ChatConversation(
            user_id=user.id,
            session_id=new_session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            processing_time_ms=processing_time_ms
        )
        
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        
        return conversation

    @staticmethod
    async def get_user_conversations(
        session: AsyncSession,
        user: User,
        limit: int = 50,
        offset: int = 0
    ) -> ChatHistoryResponse:
        """Get conversation history for a user"""
        
        # Get conversations
        conversations_query = (
            select(ChatConversation)
            .where(ChatConversation.user_id == user.id)
            .order_by(desc(ChatConversation.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(conversations_query)
        conversations = result.scalars().all()
        
        # Get total count
        count_query = (
            select(func.count(ChatConversation.id))
            .where(ChatConversation.user_id == user.id)
        )
        total_count = await session.scalar(count_query)
        
        # Get session count
        session_count_query = (
            select(func.count(func.distinct(ChatConversation.session_id)))
            .where(ChatConversation.user_id == user.id)
        )
        session_count = await session.scalar(session_count_query)
        
        return ChatHistoryResponse(
            conversations=[ChatConversationResponse.from_orm(conv) for conv in conversations],
            total_count=total_count or 0,
            session_count=session_count or 0
        )
    
    @staticmethod
    async def get_user_sessions(
        session: AsyncSession,
        user: User,
        limit: int = 20
    ) -> ChatSessionsResponse:
        """Get chat sessions for a user"""
        
        # First get session summaries
        sessions_query = (
            select(
                ChatConversation.session_id,
                func.count(ChatConversation.id).label('conversation_count'),
                func.max(ChatConversation.created_at).label('last_message_at')
            )
            .where(ChatConversation.user_id == user.id)
            .group_by(ChatConversation.session_id)
            .order_by(desc(func.max(ChatConversation.created_at)))
            .limit(limit)
        )
        
        result = await session.execute(sessions_query)
        sessions_data = result.all()
        
        sessions = []
        for session_data in sessions_data:
            # Get the most recent message for preview
            last_message_query = (
                select(ChatConversation.user_message)
                .where(
                    ChatConversation.user_id == user.id,
                    ChatConversation.session_id == session_data.session_id
                )
                .order_by(desc(ChatConversation.created_at))
                .limit(1)
            )
            
            last_message_result = await session.execute(last_message_query)
            last_message = last_message_result.scalar_one_or_none() or ""
            
            sessions.append(ChatSessionResponse(
                session_id=session_data.session_id,
                conversation_count=session_data.conversation_count,
                last_message_at=session_data.last_message_at,
                preview=last_message[:100] + "..." if len(last_message) > 100 else last_message
            ))
        
        return ChatSessionsResponse(
            sessions=sessions,
            total_sessions=len(sessions)
        )
    
    @staticmethod
    async def get_session_conversations(
        session: AsyncSession,
        user: User,
        session_id: str
    ) -> List[ChatConversationResponse]:
        """Get all conversations from a specific session"""
        
        conversations_query = (
            select(ChatConversation)
            .where(
                ChatConversation.user_id == user.id,
                ChatConversation.session_id == session_id
            )
            .order_by(ChatConversation.created_at)
        )
        
        result = await session.execute(conversations_query)
        conversations = result.scalars().all()
        
        return [ChatConversationResponse.from_orm(conv) for conv in conversations]
    
    @staticmethod
    async def clear_user_history(
        session: AsyncSession,
        user: User,
        session_id: Optional[str] = None
    ) -> ClearHistoryResponse:
        """Clear conversation history for a user"""
        
        if session_id:
            # Clear specific session
            query = (
                select(ChatConversation)
                .where(
                    ChatConversation.user_id == user.id,
                    ChatConversation.session_id == session_id
                )
            )
            message = f"Conversa da sessão {session_id} limpa com sucesso"
        else:
            # Clear all conversations
            query = (
                select(ChatConversation)
                .where(ChatConversation.user_id == user.id)
            )
            message = "Histórico de conversas limpo com sucesso"
        
        # Get conversations to delete
        result = await session.execute(query)
        conversations_to_delete = result.scalars().all()
        
        # Delete conversations
        for conv in conversations_to_delete:
            await session.delete(conv)
        
        await session.commit()
        
        return ClearHistoryResponse(
            message=message,
            cleared_conversations=len(conversations_to_delete)
        )
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a new session ID"""
        return f"session_{uuid4().hex[:12]}"

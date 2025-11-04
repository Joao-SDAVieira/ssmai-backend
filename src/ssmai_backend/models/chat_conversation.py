from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Text, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssmai_backend.models.produto import table_registry


@table_registry.mapped
class ChatConversation:
    """Model for storing chat conversations by user"""
    __tablename__ = "chat_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('usuarios.id', ondelete='CASCADE', name="fk_chat_conversations_users"),
        nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_response: Mapped[str] = mapped_column(Text, nullable=False)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationship to User
    user = relationship("User", back_populates="chat_conversations")


# Add relationship to User model
# This should be added to the User model, but we'll handle it through imports

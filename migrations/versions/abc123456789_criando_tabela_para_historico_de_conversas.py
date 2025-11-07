"""Criando tabela para histórico de conversas do chatbot

Revision ID: abc123456789
Revises: 92cc397165ac
Create Date: 2025-11-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123456789'
down_revision: Union[str, None] = '92cc397165ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_conversations table
    op.create_table('chat_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('assistant_response', sa.Text(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], name='fk_chat_conversations_users', ondelete='CASCADE'),
    )
    
    # Create index on session_id for faster queries
    op.create_index('ix_chat_conversations_session_id', 'chat_conversations', ['session_id'])
    
    # Create index on user_id and created_at for faster history queries  
    op.create_index('ix_chat_conversations_user_created', 'chat_conversations', ['user_id', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_chat_conversations_user_created', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_session_id', table_name='chat_conversations')
    
    # Drop table
    op.drop_table('chat_conversations')

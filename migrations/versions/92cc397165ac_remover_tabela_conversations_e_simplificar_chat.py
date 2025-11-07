"""remover_tabela_conversations_e_simplificar_chat

Revision ID: 92cc397165ac
Revises: b049a84756eb
Create Date: 2025-11-01 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '92cc397165ac'
down_revision: Union[str, None] = 'b049a84756eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar tabela chat_messages se não existir
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], name='fk_chat_messages_user_id'),
        extend_existing=True
    )
    
    # Criar index no user_id para melhor performance
    op.create_index('idx_chat_messages_user_id', 'chat_messages', ['user_id'], if_not_exists=True)
    
    # Remover tabela conversations se existir
    op.execute("DROP TABLE IF EXISTS conversations CASCADE")


def downgrade() -> None:
    op.create_table('conversations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.add_column('chat_messages', sa.Column('conversation_id', sa.String(length=36), nullable=True))
    
    op.execute("""
        INSERT INTO conversations (id, user_id, title, created_at, updated_at)
        SELECT 
            gen_random_uuid()::text,
            user_id,
            'Conversa Principal',
            MIN(created_at),
            MAX(created_at)
        FROM chat_messages
        GROUP BY user_id
    """)
    
    op.execute("""
        UPDATE chat_messages cm
        SET conversation_id = (
            SELECT id 
            FROM conversations c 
            WHERE c.user_id = cm.user_id
            LIMIT 1
        )
    """)
    
    op.alter_column('chat_messages', 'conversation_id', nullable=False)
    op.create_foreign_key('chat_messages_conversation_id_fkey', 'chat_messages', 'conversations', ['conversation_id'], ['id'])
    
    op.drop_constraint('fk_chat_messages_user_id', 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'user_id')

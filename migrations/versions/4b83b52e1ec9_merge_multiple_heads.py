"""merge_multiple_heads

Revision ID: 4b83b52e1ec9
Revises: 19554abf6ff7, 92cc397165ac
Create Date: 2025-11-04 13:19:19.614668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b83b52e1ec9'
down_revision: Union[str, Sequence[str], None] = ('19554abf6ff7', '92cc397165ac')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

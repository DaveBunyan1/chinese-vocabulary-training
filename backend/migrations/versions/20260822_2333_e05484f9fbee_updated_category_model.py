"""updated_category_model

Revision ID: e05484f9fbee
Revises: b88345d07a98
Create Date: 2026-08-22 23:33:56.197960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e05484f9fbee'
down_revision: Union[str, Sequence[str], None] = 'b88345d07a98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

category_enum = postgresql.ENUM(
    'hsk', 'topic', 'system', 'custom', name='categorytype'
)


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create Enum type first
    category_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add columns and indexes
    op.add_column('categories', sa.Column('type', category_enum, nullable=False))
    op.add_column('categories', sa.Column('hsk_level', sa.Integer(), nullable=True))
    op.drop_index(op.f('ix_categories_parent_id'), table_name='categories')
    op.create_index(op.f('ix_categories_hsk_level'), 'categories', ['hsk_level'], unique=False)
    op.create_index(op.f('ix_categories_type'), 'categories', ['type'], unique=False)
    
    # REMOVED: op.create_unique_constraint('uq_category_vocabulary', ...)


def downgrade() -> None:
    """Downgrade schema."""
    # REMOVED: op.drop_constraint('uq_category_vocabulary', ...)
    
    op.drop_index(op.f('ix_categories_type'), table_name='categories')
    op.drop_index(op.f('ix_categories_hsk_level'), table_name='categories')
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)
    op.drop_column('categories', 'hsk_level')
    op.drop_column('categories', 'type')

    category_enum.drop(op.get_bind(), checkfirst=True)
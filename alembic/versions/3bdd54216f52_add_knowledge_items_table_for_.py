"""add knowledge_items table for organizational memory

Revision ID: 3bdd54216f52
Revises: 2aa35684f8e3
Create Date: 2026-08-06 15:18:19.815652

"""
from typing import Sequence, Union

from alembic import op
import pgvector
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3bdd54216f52'
down_revision: Union[str, Sequence[str], None] = '2aa35684f8e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'knowledge_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column(
            'tier',
            sa.Enum(
                'PRIVATE',
                'CANDIDATE',
                'SHARED',
                'EXTERNAL',
                name='memorytier',
            ),
            nullable=False,
        ),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'PROPOSED',
                'APPROVED',
                'REJECTED',
                'ARCHIVED',
                name='knowledgestatus',
            ),
            nullable=False,
        ),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column(
            'embedding',
            pgvector.sqlalchemy.vector.VECTOR(dim=1536),
            nullable=True,
        ),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_knowledge_items_category'),
        'knowledge_items',
        ['category'],
        unique=False,
    )
    op.create_index(
        op.f('ix_knowledge_items_created_at'),
        'knowledge_items',
        ['created_at'],
        unique=False,
    )
    op.create_index(
        op.f('ix_knowledge_items_status'),
        'knowledge_items',
        ['status'],
        unique=False,
    )
    op.create_index(
        op.f('ix_knowledge_items_tier'),
        'knowledge_items',
        ['tier'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_knowledge_items_tier'), table_name='knowledge_items'
    )
    op.drop_index(
        op.f('ix_knowledge_items_status'), table_name='knowledge_items'
    )
    op.drop_index(
        op.f('ix_knowledge_items_created_at'), table_name='knowledge_items'
    )
    op.drop_index(
        op.f('ix_knowledge_items_category'), table_name='knowledge_items'
    )
    op.drop_table('knowledge_items')

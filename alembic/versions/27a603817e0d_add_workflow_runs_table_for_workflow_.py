"""add workflow_runs table for workflow orchestration

Revision ID: 27a603817e0d
Revises: 3bdd54216f52
Create Date: 2026-08-06 16:09:37.418885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '27a603817e0d'
down_revision: Union[str, Sequence[str], None] = '3bdd54216f52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'CREATED',
                'PLANNING',
                'DESIGNING',
                'BUILDING',
                'REVIEWING',
                'TESTING',
                'AWAITING_APPROVAL',
                'COMPLETED',
                'ESCALATED',
                'FAILED',
                name='workflowstatus',
            ),
            nullable=False,
        ),
        sa.Column('specification', sa.Text(), nullable=False),
        sa.Column('current_step', sa.String(length=100), nullable=False),
        sa.Column('artifacts', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_workflow_runs_created_at'),
        'workflow_runs',
        ['created_at'],
        unique=False,
    )
    op.create_index(
        op.f('ix_workflow_runs_status'),
        'workflow_runs',
        ['status'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_workflow_runs_status'), table_name='workflow_runs'
    )
    op.drop_index(
        op.f('ix_workflow_runs_created_at'), table_name='workflow_runs'
    )
    op.drop_table('workflow_runs')

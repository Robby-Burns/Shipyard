"""add_owner_id_to_workflow_runs

Revision ID: 4444cde0d494
Revises: 27a603817e0d
Create Date: 2026-08-07 11:35:42.762670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4444cde0d494'
down_revision: Union[str, Sequence[str], None] = '27a603817e0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('workflow_runs', sa.Column('owner_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_workflow_runs_owner_id'), 'workflow_runs', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_workflow_runs_owner_id'), table_name='workflow_runs')
    op.drop_column('workflow_runs', 'owner_id')

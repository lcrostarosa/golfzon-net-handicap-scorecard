"""add_ocr_corrections_table

Revision ID: 825adaf06c68
Revises: 6f32cb6d9759
Create Date: 2025-11-06 21:44:10.605462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '825adaf06c68'
down_revision: Union[str, None] = '6f32cb6d9759'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ocr_corrections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ocr_text', sa.String(length=200), nullable=False),
        sa.Column('corrected_text', sa.String(length=200), nullable=False),
        sa.Column('pattern_type', sa.String(length=50), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ocr_corrections_ocr_text', 'ocr_corrections', ['ocr_text'])


def downgrade() -> None:
    op.drop_index('ix_ocr_corrections_ocr_text', table_name='ocr_corrections')
    op.drop_table('ocr_corrections')

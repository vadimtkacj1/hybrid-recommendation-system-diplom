"""add als_vector to user profiles

Revision ID: 003
Revises: 002
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user_profiles',
        sa.Column('als_vector', sa.PickleType(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('user_profiles', 'als_vector')

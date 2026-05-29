"""add semantic vector to user profiles

Revision ID: 002
Revises: 001
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa
import pickle

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user_profiles',
        sa.Column('semantic_vector', sa.PickleType(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('user_profiles', 'semantic_vector')

"""add pregnancy week field

Revision ID: add_pregnancy_week
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('user', sa.Column('pregnancy_week', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('user', 'pregnancy_week') 
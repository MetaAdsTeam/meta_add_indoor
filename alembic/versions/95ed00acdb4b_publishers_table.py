"""publishers_table

Revision ID: 95ed00acdb4b
Revises: 1e63281194e3
Create Date: 2022-02-11 18:51:18.351878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95ed00acdb4b'
down_revision = '1e63281194e3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('publishers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('password', sa.LargeBinary(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('domain', sa.String(), nullable=True),
    sa.Column('platform_id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('device_id')
    )


def downgrade():
    op.drop_table('publishers')

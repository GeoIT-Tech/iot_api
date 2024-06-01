"""Certificate Table Modified

Revision ID: df24ea6f0a12
Revises: 4306c068ee11
Create Date: 2024-02-02 13:49:04.723658

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df24ea6f0a12'
down_revision = '4306c068ee11'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('certificates', 'duration')
    op.drop_column('certificates', 'amount_type')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('certificates', sa.Column('amount_type', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('certificates', sa.Column('duration', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###

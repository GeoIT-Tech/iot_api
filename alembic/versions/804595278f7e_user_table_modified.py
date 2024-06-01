"""User table modified

Revision ID: 804595278f7e
Revises: ff8e0151d937
Create Date: 2024-05-10 15:19:39.397947

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '804595278f7e'
down_revision = 'ff8e0151d937'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('signup_type', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'signup_type')
    # ### end Alembic commands ###

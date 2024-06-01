"""boost and datatime updated

Revision ID: dc2a37d9f8db
Revises: d36f6b506a36
Create Date: 2024-01-12 07:44:15.223903

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dc2a37d9f8db'
down_revision = 'd36f6b506a36'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('boost_table',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sender_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('receiver_uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['receiver_uuid'], ['users.uuid'], ),
    sa.ForeignKeyConstraint(['sender_uuid'], ['users.uuid'], ),
    sa.PrimaryKeyConstraint('uuid', 'sender_uuid', 'receiver_uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.drop_column('boosts', 'updated_at')
    op.create_foreign_key(None, 'join_e_battles', 'posts', ['post_uuid'], ['uuid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'join_e_battles', type_='foreignkey')
    op.add_column('boosts', sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_table('boost_table')
    # ### end Alembic commands ###

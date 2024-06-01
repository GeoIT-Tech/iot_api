"""Added fields to certificate and ebattle

Revision ID: 5ca6f2547e60
Revises: 2da7623785f1
Create Date: 2023-03-30 02:09:16.886410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ca6f2547e60'
down_revision = '2da7623785f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('certificates', sa.Column('amount_type', sa.String(), nullable=True))
    op.add_column('certificates', sa.Column('amount', sa.Integer(), nullable=True))
    op.add_column('certificates', sa.Column('location', sa.String(), nullable=True))
    op.add_column('certificates', sa.Column('cover_image_url', sa.String(), nullable=True))
    op.add_column('e_battles', sa.Column('category', sa.String(), nullable=True))
    op.add_column('e_battles', sa.Column('is_paid_battle', sa.Boolean(), nullable=True))
    op.add_column('e_battles', sa.Column('amount_type', sa.String(), nullable=True))
    op.add_column('e_battles', sa.Column('amount', sa.Integer(), nullable=True))
    op.add_column('e_battles', sa.Column('is_online_battle', sa.Boolean(), nullable=True))
    op.add_column('e_battles', sa.Column('location', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'ei_placement_partner', ['uuid'])
    op.add_column('join_e_battles', sa.Column('email', sa.String(), nullable=True))
    op.add_column('join_e_battles', sa.Column('mobile', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('join_e_battles', 'mobile')
    op.drop_column('join_e_battles', 'email')
    op.drop_constraint(None, 'ei_placement_partner', type_='unique')
    op.drop_column('e_battles', 'location')
    op.drop_column('e_battles', 'is_online_battle')
    op.drop_column('e_battles', 'amount')
    op.drop_column('e_battles', 'amount_type')
    op.drop_column('e_battles', 'is_paid_battle')
    op.drop_column('e_battles', 'category')
    op.drop_column('certificates', 'cover_image_url')
    op.drop_column('certificates', 'location')
    op.drop_column('certificates', 'amount')
    op.drop_column('certificates', 'amount_type')
    # ### end Alembic commands ###
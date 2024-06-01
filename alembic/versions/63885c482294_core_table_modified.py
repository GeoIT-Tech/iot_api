"""Core table modified

Revision ID: 63885c482294
Revises: 63cc0b77be2a
Create Date: 2024-01-17 03:51:57.143217

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '63885c482294'
down_revision = '63cc0b77be2a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ei_admission_details', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'ei_admission_details', 'users', ['user_uuid'], ['uuid'])
    op.add_column('ei_program_offers', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ei_program_offers', sa.Column('course_year', sa.String(), nullable=True))
    op.add_column('ei_program_offers', sa.Column('course_mode', sa.String(), nullable=True))
    op.create_foreign_key(None, 'ei_program_offers', 'users', ['user_uuid'], ['uuid'])
    op.create_unique_constraint(None, 'reports_table', ['uuid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'reports_table', type_='unique')
    op.drop_constraint(None, 'ei_program_offers', type_='foreignkey')
    op.drop_column('ei_program_offers', 'course_mode')
    op.drop_column('ei_program_offers', 'course_year')
    op.drop_column('ei_program_offers', 'user_uuid')
    op.drop_constraint(None, 'ei_admission_details', type_='foreignkey')
    op.drop_column('ei_admission_details', 'user_uuid')
    # ### end Alembic commands ###

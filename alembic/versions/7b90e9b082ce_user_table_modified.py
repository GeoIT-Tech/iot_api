"""user table modified

Revision ID: 7b90e9b082ce
Revises: 3240a284ab12
Create Date: 2024-06-07 15:55:18.723710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b90e9b082ce'
down_revision: Union[str, None] = '3240a284ab12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""user table created

Revision ID: 3240a284ab12
Revises: 275ab43c0667
Create Date: 2024-06-07 15:53:34.857232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3240a284ab12'
down_revision: Union[str, None] = '275ab43c0667'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

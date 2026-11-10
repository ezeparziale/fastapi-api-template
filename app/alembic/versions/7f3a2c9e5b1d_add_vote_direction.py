"""add_vote_direction

Revision ID: 7f3a2c9e5b1d
Revises: 39b5a098a9da
Create Date: 2026-11-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f3a2c9e5b1d"
down_revision: str | None = "39b5a098a9da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "votes",
        sa.Column(
            "direction",
            sa.SmallInteger(),
            server_default="1",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("votes", "direction")

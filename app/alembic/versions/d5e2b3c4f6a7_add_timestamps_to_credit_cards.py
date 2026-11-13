"""add_timestamps_to_credit_cards

Revision ID: d5e2b3c4f6a7
Revises: c4f1a2b3d8e9
Create Date: 2026-11-13 00:00:00.000000

Adds the TimestampMixin columns to users_credit_cards so it matches the rest
of the models.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e2b3c4f6a7"
down_revision: str | None = "c4f1a2b3d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users_credit_cards",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "users_credit_cards",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users_credit_cards", "updated_at")
    op.drop_column("users_credit_cards", "created_at")

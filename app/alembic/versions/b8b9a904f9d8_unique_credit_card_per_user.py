"""unique_credit_card_per_user

Revision ID: b8b9a904f9d8
Revises: ba7f94858bd1
Create Date: 2026-11-10 09:43:18.439717

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8b9a904f9d8"
down_revision: str | None = "ba7f94858bd1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_users_credit_cards_user_id", "users_credit_cards", ["user_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_users_credit_cards_user_id", "users_credit_cards", type_="unique"
    )

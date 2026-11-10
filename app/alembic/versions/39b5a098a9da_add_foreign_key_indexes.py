"""add_foreign_key_indexes

Revision ID: 39b5a098a9da
Revises: b8b9a904f9d8
Create Date: 2026-11-10 10:15:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "39b5a098a9da"
down_revision: str | None = "b8b9a904f9d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_posts_owner_id", "posts", ["owner_id"])
    op.create_index("ix_votes_post_id", "votes", ["post_id"])


def downgrade() -> None:
    op.drop_index("ix_votes_post_id", table_name="votes")
    op.drop_index("ix_posts_owner_id", table_name="posts")

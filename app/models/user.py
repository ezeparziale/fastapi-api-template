from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.post import Post


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, created_at={self.created_at})"

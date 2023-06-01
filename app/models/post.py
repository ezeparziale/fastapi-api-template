from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixin import TimestampMixin
from app.models.user import User


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)

    published: Mapped[bool] = mapped_column(
        Boolean, server_default="TRUE", nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner: Mapped[list["User"]] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        return f"Post(id={self.id}, title={self.title}, published={self.published}, owner_id={self.owner_id}, created_at={self.created_at}, owner={self.owner})"  # noqa: E501

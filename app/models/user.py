from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.database import Base
from app.models.encrypted import Encrypted
from app.models.mixin import TimestampMixin

if TYPE_CHECKING:
    from app.models.post import Post


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="owner")
    credit_card: Mapped["UserCreditCard"] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, created_at={self.created_at})"


class UserCreditCard(Base):
    __tablename__ = "users_credit_cards"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    credit_card: Mapped[dict[str, str]] = mapped_column(
        Encrypted(settings.ENCRYPTION_KEY), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="credit_card")

    def __repr__(self) -> str:
        return f"UserCreditCard(id={self.id}, user_id={self.user_id})"

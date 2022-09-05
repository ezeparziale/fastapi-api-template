from sqlalchemy import Column, ForeignKey, Integer

from app.db.database import Base


class Vote(Base):
    __tablename__ = "votes"
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )

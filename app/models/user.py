from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
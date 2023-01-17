from typing import Optional
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from slacker.model import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slack_user_id: Mapped[str] = mapped_column(String(255))
    github_username: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, slack={self.slack_user_id!r}, github={self.github_username!r})"

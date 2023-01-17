from typing import Optional
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from slacker.model import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slack_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    new_devs_are_reviewers: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return f"Channel(id={self.id!r}, slack_id={self.slack_id!r}, name={self.name!r}, ndar={self.new_devs_are_reviewers!r})"

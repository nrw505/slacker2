from typing import Optional
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from slacker.model import Base


class UserChannelConfig(Base):
    __tablename__ = "user_channel_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(255))
    reviews_assigned: Mapped[int] = mapped_column(Integer)
    reviewer: Mapped[bool] = mapped_column(Boolean)
    notify_on_assignement: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return f"UserChannelConfig(id={self.id!r}, user_id={self.user_id!r}, channel={self.channel!r}, reviews_assigned={self.reviews_assigned!r}, reviewer={self.reviewer!r}, notify_on_assignement={self.notify_on_assignement!r})"

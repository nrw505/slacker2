from sqlalchemy.orm import DeclarativeBase
from typing import Optional
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slack_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_username: Mapped[str] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)

    channel_configs: Mapped[list["UserChannelConfig"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    assigned_reviews: Mapped[list["AssignedReview"]] = relationship(
        foreign_keys="[AssignedReview.assignee_id]",
        back_populates="assignee",
        cascade="all, delete-orphan",
    )
    requested_reviews: Mapped[list["AssignedReview"]] = relationship(
        foreign_keys="[AssignedReview.requestor_id]",
        back_populates="requestor",
        # No cascade, if the requestor leaves marketplacer / slack we
        # still want to know about the assigned reviews
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, slack={self.slack_id!r}, name={self.name!r}, github={self.github_username!r})"


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slack_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    new_devs_are_reviewers: Mapped[bool] = mapped_column(Boolean)

    user_configs: Mapped[list["UserChannelConfig"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )
    assigned_reviews: Mapped[list["AssignedReview"]] = relationship(
        # No cascade - if a channel is removed we want to still show
        # that the user had these reviews
        back_populates="channel",
    )

    def __repr__(self) -> str:
        return f"Channel(id={self.id!r}, slack_id={self.slack_id!r}, name={self.name!r}, ndar={self.new_devs_are_reviewers!r})"


class UserChannelConfig(Base):
    __tablename__ = "user_channel_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("channels.id"), nullable=False
    )
    reviewer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notify_on_assignment: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user: Mapped[User] = relationship(back_populates="channel_configs")
    channel: Mapped[Channel] = relationship(back_populates="user_configs")

    def __repr__(self) -> str:
        return f"UserChannelConfig(id={self.id!r}, user_id={self.user_id!r}, channel_id={self.channel_id!r}, reviewer={self.reviewer!r}, notify_on_assignement={self.notify_on_assignment!r})"


class AssignedReview(Base):
    __tablename__ = "assigned_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    requestor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("channels.id"), nullable=True
    )
    pr_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rerolled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    assignee: Mapped[User] = relationship(
        foreign_keys="[AssignedReview.assignee_id]", back_populates="assigned_reviews"
    )
    requestor: Mapped[User] = relationship(
        foreign_keys="[AssignedReview.requestor_id]", back_populates="requested_reviews"
    )
    channel: Mapped[Channel] = relationship(back_populates="assigned_reviews")

    def __repr__(self) -> str:
        return f"AssignedReview(id={self.id!r}, assignee={self.assignee_id!r}, requestor={self.requestor_id!r}, pr={self.pr_url!r})"


__all__ = [
    "Base",
    "User",
    "Channel",
    "UserChannelConfig",
]

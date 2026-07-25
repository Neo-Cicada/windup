from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Plan

if TYPE_CHECKING:
    from app.models.gameplay import (
        BossSession,
        ChestUnlock,
        DailyQuest,
        Submission,
        UserAchievement,
        XpEvent,
    )


class User(UUIDMixin, TimestampMixin, Base):
    """A toy in training."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    toy_name: Mapped[str] = mapped_column(String(60), nullable=False)

    # Trainee badge number shown on the dashboard / profile banner ("No. 0471").
    trainee_no: Mapped[int] = mapped_column(Integer, autoincrement=False, nullable=False)

    avatar_body: Mapped[str] = mapped_column(String(9), default="#6FBF73", nullable=False)
    avatar_head: Mapped[str] = mapped_column(String(9), default="#F7C948", nullable=False)
    avatar_accent: Mapped[str] = mapped_column(String(9), default="#EF5B54", nullable=False)

    plan: Mapped[str] = mapped_column(String(16), default=Plan.FREE, nullable=False)

    notify_streak: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_weekly: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_bosses: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    progress: Mapped[Progress] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    submissions: Mapped[list[Submission]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chest_unlocks: Mapped[list[ChestUnlock]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_quests: Mapped[list[DailyQuest]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    xp_events: Mapped[list[XpEvent]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list[UserAchievement]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    boss_sessions: Mapped[list[BossSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Progress(UUIDMixin, TimestampMixin, Base):
    """The wind-up charge meter, shelf level, streak and counters for one user."""

    __tablename__ = "progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_max: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unaided_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active_on: Mapped[date | None] = mapped_column(Date)

    user: Mapped[User] = relationship(back_populates="progress")

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import BossStatus, SubmissionStatus, XpSource

if TYPE_CHECKING:
    from app.models.content import Achievement, Problem
    from app.models.user import User


class ChestUnlock(UUIDMixin, TimestampMixin, Base):
    """Opening a chest forfeits the unaided bonus for that problem."""

    __tablename__ = "chest_unlocks"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", "tier"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    tier: Mapped[str] = mapped_column(String(16), nullable=False)

    user: Mapped[User] = relationship(back_populates="chest_unlocks")
    problem: Mapped[Problem] = relationship()


class Submission(UUIDMixin, TimestampMixin, Base):
    """One "Run & Submit" from the workbench."""

    __tablename__ = "submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    boss_session_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("boss_sessions.id", ondelete="SET NULL")
    )

    code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    language: Mapped[str] = mapped_column(String(24), default="python", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=SubmissionStatus.PASSED, nullable=False)
    unaided: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coins_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="submissions")
    problem: Mapped[Problem] = relationship(lazy="selectin")


class DailyQuest(UUIDMixin, TimestampMixin, Base):
    """The three "today's quests" cards on the playroom dashboard."""

    __tablename__ = "daily_quests"
    __table_args__ = (UniqueConstraint("user_id", "quest_date", "problem_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    quest_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="daily_quests")
    problem: Mapped[Problem] = relationship(lazy="selectin")


class XpEvent(UUIDMixin, TimestampMixin, Base):
    """Append-only charge ledger — powers the weekly chart and streak heatmap."""

    __tablename__ = "xp_events"
    __table_args__ = (
        # The wind-up key pays out once a day; enforced here so a burst of concurrent
        # requests can't each pass the application-level check.
        Index(
            "uq_xp_events_wind_up_per_day",
            "user_id",
            "happened_on",
            unique=True,
            postgresql_where=text("source = 'wind_up'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(24), default=XpSource.SOLVE, nullable=False)
    note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    happened_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="xp_events")


class UserAchievement(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), index=True
    )
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship(back_populates="achievements")
    achievement: Mapped[Achievement] = relationship(lazy="selectin")


class BossSession(UUIDMixin, TimestampMixin, Base):
    """A timed mock-interview round against a boss toy."""

    __tablename__ = "boss_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    boss_name: Mapped[str] = mapped_column(
        String(80), default="The Jack-in-the-Box", nullable=False
    )
    total_seconds: Mapped[int] = mapped_column(Integer, default=900, nullable=False)
    remaining_seconds: Mapped[int] = mapped_column(Integer, default=900, nullable=False)
    rounds_total: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    rounds_cleared: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=BossStatus.PAUSED, nullable=False)

    # Set while the clock is running; used to compute remaining time on read.
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="boss_sessions")

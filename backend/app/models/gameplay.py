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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import BossStatus, DuelStatus, SubmissionStatus, XpSource

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
    """One "Submit" from the workbench, and its trip through the judge.

    This table doubles as the judge queue: the worker claims `pending` rows with
    FOR UPDATE SKIP LOCKED, which is why the deployment needs no broker beyond
    the Postgres that is already there.
    """

    __tablename__ = "submissions"
    __table_args__ = (
        # The worker's claim query: oldest pending first.
        Index("ix_submissions_queue", "status", "created_at"),
        # Duel round counting runs on every 2-second poll, for both players. Partial,
        # because the overwhelming majority of submissions are not part of a duel.
        Index(
            "ix_submissions_duel",
            "duel_id",
            "user_id",
            postgresql_where=text("duel_id IS NOT NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    boss_session_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("boss_sessions.id", ondelete="SET NULL")
    )
    # Set only by `resolve_duel_tag` in the submit endpoint, which refuses to write it
    # unless the toy is in that duel, the clock is still running, and the problem is
    # genuinely one of the duel's rounds.
    duel_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("duels.id", ondelete="SET NULL")
    )

    code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    language: Mapped[str] = mapped_column(String(24), default="python", nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=SubmissionStatus.PENDING, nullable=False
    )
    unaided: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coins_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ---- judge queue --------------------------------------------------------
    # Set when a worker claims the row; a claim older than JUDGE_STALE_CLAIM_SECONDS
    # is reclaimable, so a worker dying mid-run doesn't strand the submission.
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ---- verdict ------------------------------------------------------------
    judged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Payout happens once, when the verdict lands. Guards against a retried job
    # paying XP twice.
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tests_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tests_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Recorded at settle time. By the time anyone polls, progress.level already
    # reflects the new shelf, so the before/after comparison is only available
    # to the settlement itself.
    leveled_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    # The first failing case only: {ordinal, label, args, expected, actual, error}.
    # For a hidden case `expected` is omitted — args and the toy's own actual
    # output are useful for debugging and give nothing away, but handing back the
    # expected value would turn the hidden tests into a lookup table.
    failure_json: Mapped[dict | None] = mapped_column(JSONB)

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


class Duel(UUIDMixin, TimestampMixin, Base):
    """A head-to-head race: two toys, the same N problems, one clock.

    Deliberately *not* a BossSession with a second user bolted on. A duel has no pause,
    so it needs no remaining_seconds/resumed_at snapshot pair: the clock is
    `started_at + total_seconds` and nothing a client does can stretch it.
    """

    __tablename__ = "duels"
    __table_args__ = (
        # The invitee's lookup, and the uniqueness that stops a recycled code resolving
        # to somebody else's duel. Codes are unique forever, not just among live duels.
        Index("ix_duels_code", "code", unique=True),
    )

    # Six characters from an unambiguous alphabet, stored canonically uppercase.
    code: Mapped[str] = mapped_column(String(8), nullable=False)

    host_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Null until someone accepts the invite. Setting it is what starts the clock.
    opponent_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    status: Mapped[str] = mapped_column(String(16), default=DuelStatus.WAITING, nullable=False)
    rounds_total: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    total_seconds: Mapped[int] = mapped_column(Integer, default=900, nullable=False)

    # Set when the opponent joins. The clock is derived from this and nothing else.
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Null on a draw, and on a duel nobody won. Set to the *other* toy on a forfeit.
    winner_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    # Which toy walked away, if either — distinguishes a walkover from a real win.
    forfeited_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Paid once, at close-out. Non-zero is the idempotency guard, like BossSession's.
    host_xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opponent_xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    host: Mapped[User] = relationship(foreign_keys=[host_id], lazy="selectin")
    opponent: Mapped[User | None] = relationship(foreign_keys=[opponent_id], lazy="selectin")
    rounds: Mapped[list[DuelRound]] = relationship(
        back_populates="duel", cascade="all, delete-orphan", order_by="DuelRound.ordinal"
    )


class DuelRound(UUIDMixin, TimestampMixin, Base):
    """One problem in a duel's set.

    These rows do not exist until the duel starts. That *is* the reveal: there is no
    `revealed` flag anyone can forget to check, because a waiting duel has no rounds
    to leak. They are written at join time, in the same transaction that flips the duel
    to `active` — which is also the first moment both toys' solve histories are known,
    and the set is filtered against the pair of them.
    """

    __tablename__ = "duel_rounds"
    __table_args__ = (
        UniqueConstraint("duel_id", "ordinal", name="uq_duel_rounds_duel_ordinal"),
        UniqueConstraint("duel_id", "problem_id", name="uq_duel_rounds_duel_problem"),
    )

    duel_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("duels.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    duel: Mapped[Duel] = relationship(back_populates="rounds")
    problem: Mapped[Problem] = relationship(lazy="selectin")

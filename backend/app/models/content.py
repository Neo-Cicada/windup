from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Difficulty


class Zone(UUIDMixin, TimestampMixin, Base):
    """A toy corner on the quest map — one DSA pattern each."""

    __tablename__ = "zones"

    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    pattern: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(9), nullable=False)
    blurb: Mapped[str] = mapped_column(String(160), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    problems: Mapped[list[Problem]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )


class Problem(UUIDMixin, TimestampMixin, Base):
    """A broken toy to fix, with its four tiers of help."""

    __tablename__ = "problems"

    zone_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), index=True
    )

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default=Difficulty.MEDIUM, nullable=False)
    weight_label: Mapped[str] = mapped_column(String(40), default="MEDIUM WEIGHT", nullable=False)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    example_input: Mapped[str] = mapped_column(Text, default="", nullable=False)
    example_output: Mapped[str] = mapped_column(Text, default="", nullable=False)

    language: Mapped[str] = mapped_column(String(24), default="python", nullable=False)
    starter_code: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Help shelf. Tier 1 ships with the problem; tiers 2-4 are gated behind chests.
    explainer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    approach: Mapped[str] = mapped_column(Text, default="", nullable=False)
    solution: Mapped[str] = mapped_column(Text, default="", nullable=False)

    xp_reward: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    zone: Mapped[Zone] = relationship(back_populates="problems", lazy="selectin")


class Achievement(UUIDMixin, TimestampMixin, Base):
    """A merit badge on the sash."""

    __tablename__ = "achievements"

    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    color: Mapped[str] = mapped_column(String(9), nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

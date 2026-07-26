from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Difficulty, TestVisibility


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

    # ---- judging ------------------------------------------------------------
    # The function the harness calls. Every runner evaluates the same shape:
    #     _dump(entrypoint(*_build(args)))
    # so nothing here needs per-problem branching. `_build` takes the whole
    # argument list, which is what lets linked-list-cycle fold two JSON values
    # (the marbles, and the index its tail loops back to) into a single node.
    entrypoint: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    # Prepended before the toy's code. Defines whatever the problem needs
    # (ListNode, TreeNode) and may override _build/_dump, which default to
    # identity. This is what makes a bare `reverseList(head)` stub callable.
    harness_preamble: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # False bypasses the judge entirely — the SQL problem has no Python runner.
    graded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # "exact" compares dumped output verbatim; "unordered" sorts first, for
    # problems where any ordering of the answer is correct.
    compare_mode: Mapped[str] = mapped_column(String(16), default="exact", nullable=False)

    tests: Mapped[list[ProblemTest]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="ProblemTest.ordinal",
    )

    # Help shelf. Tier 1 ships with the problem; tiers 2-4 are gated behind chests.
    explainer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    approach: Mapped[str] = mapped_column(Text, default="", nullable=False)
    solution: Mapped[str] = mapped_column(Text, default="", nullable=False)

    xp_reward: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    zone: Mapped[Zone] = relationship(back_populates="problems", lazy="selectin")


class ProblemTest(UUIDMixin, TimestampMixin, Base):
    """One graded case for a problem.

    `args_json` is a list of positional arguments and `expected_json` the value
    the entrypoint should produce — both plain JSON. Anything structural (a
    linked list, a tree) is reconstituted by the problem's `_build`/`_dump`
    adapters, so this table never holds anything but JSON.

    Hidden cases are the ones that actually grade, and they never leave the
    server — the same rule that keeps a locked help chest out of the payload.
    """

    __tablename__ = "problem_tests"
    __table_args__ = (Index("ix_problem_tests_problem_ordinal", "problem_id", "ordinal"),)

    problem_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(16), default=TestVisibility.HIDDEN, nullable=False
    )
    label: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    args_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    expected_json: Mapped[object] = mapped_column(JSONB, nullable=False)

    problem: Mapped[Problem] = relationship(back_populates="tests")


class Achievement(UUIDMixin, TimestampMixin, Base):
    """A merit badge on the sash."""

    __tablename__ = "achievements"

    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    color: Mapped[str] = mapped_column(String(9), nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

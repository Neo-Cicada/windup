"""per-language benches, so a toy can pick what it solves in

Adds the two things multi-language judging needs and nothing else:

- `problems.signature_json` — what the entrypoint takes and returns. Python and
  JavaScript can generate a stub from the entrypoint name alone; a statically
  typed language cannot, so a problem without a signature simply won't offer one.
- `problem_languages` — one row per language a problem can be solved in, holding
  the stub, the preamble and (rarely) a different entrypoint name.

Deliberately absent: anything touching `problem_tests`. The cases are plain JSON
compared on the host, so one set of them grades every language. That is what
keeps this migration small.

Existing rows need no backfill. A problem with no rows still offers its own
`language`, which is what every seeded problem does today.

Revision ID: b4e19c7a5f02
Revises: 86dc7f92c234
Create Date: 2026-07-28 09:12:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'b4e19c7a5f02'
down_revision: str | None = '86dc7f92c234'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "problems",
        sa.Column("signature_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "problem_languages",
        sa.Column("problem_id", sa.UUID(), nullable=False),
        sa.Column("language", sa.String(length=24), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        # All three fall back to the problem's own when null or blank.
        sa.Column("entrypoint", sa.String(length=80), nullable=True),
        sa.Column("starter_code", sa.Text(), nullable=True),
        sa.Column("harness_preamble", sa.Text(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            name=op.f("fk_problem_languages_problem_id_problems"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_problem_languages")),
        sa.UniqueConstraint(
            "problem_id", "language", name="uq_problem_languages_problem_language"
        ),
    )
    op.create_index(
        op.f("ix_problem_languages_problem_id"), "problem_languages", ["problem_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_problem_languages_problem_id"), table_name="problem_languages")
    op.drop_table("problem_languages")
    op.drop_column("problems", "signature_json")

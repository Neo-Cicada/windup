"""real judging: test cases, judge queue, verdicts

Adds the machinery that lets the server decide whether a submission passed:
a test-case table, the harness fields that make a starter stub callable, and
the queue/verdict columns on submissions.

Every NOT NULL column is added with a server_default so it lands on tables that
already have rows, then the default is dropped once the backfill is done — the
models don't declare server defaults, and leaving them would make the next
autogenerate try to remove them.

Existing submissions predate the judge. They are backfilled as already judged
and settled, otherwise the demo history reads as perpetually pending.

Revision ID: 86dc7f92c234
Revises: 9c1f4b2ad730
Create Date: 2026-07-27 03:47:50.004654
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '86dc7f92c234'
down_revision: str | None = '9c1f4b2ad730'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (table, column, type, server_default) for every NOT NULL column being added.
_NOT_NULL_ADDS = [
    ("problems", "entrypoint", sa.String(length=80), "''"),
    ("problems", "harness_preamble", sa.Text(), "''"),
    ("problems", "graded", sa.Boolean(), sa.text("true")),
    ("problems", "compare_mode", sa.String(length=16), "'exact'"),
    ("submissions", "attempts", sa.Integer(), "0"),
    ("submissions", "tests_passed", sa.Integer(), "0"),
    ("submissions", "tests_total", sa.Integer(), "0"),
    ("submissions", "leveled_up", sa.Boolean(), sa.text("false")),
]


def upgrade() -> None:
    op.create_table(
        'problem_tests',
        sa.Column('problem_id', sa.UUID(), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False),
        sa.Column('visibility', sa.String(length=16), nullable=False),
        sa.Column('label', sa.String(length=120), nullable=False),
        sa.Column('args_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expected_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'],
                                name=op.f('fk_problem_tests_problem_id_problems'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_problem_tests')),
    )
    op.create_index(op.f('ix_problem_tests_problem_id'), 'problem_tests',
                    ['problem_id'], unique=False)
    op.create_index('ix_problem_tests_problem_ordinal', 'problem_tests',
                    ['problem_id', 'ordinal'], unique=False)

    for table, column, type_, default in _NOT_NULL_ADDS:
        op.add_column(table, sa.Column(column, type_, nullable=False, server_default=default))

    op.add_column('submissions',
                  sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('submissions',
                  sa.Column('judged_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('submissions',
                  sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('submissions', sa.Column('runtime_ms', sa.Integer(), nullable=True))
    op.add_column('submissions',
                  sa.Column('failure_json', postgresql.JSONB(astext_type=sa.Text()),
                            nullable=True))
    op.create_index('ix_submissions_queue', 'submissions', ['status', 'created_at'], unique=False)

    # Rows that predate the judge already have a verdict; mark them judged and
    # settled so nothing re-pays them and the UI doesn't show them as pending.
    op.execute(
        """
        UPDATE submissions
           SET judged_at = created_at,
               settled_at = created_at,
               tests_total = 0,
               tests_passed = 0
         WHERE status IN ('passed', 'failed')
        """
    )

    for table, column, _type, _default in _NOT_NULL_ADDS:
        op.alter_column(table, column, server_default=None)


def downgrade() -> None:
    op.drop_index('ix_submissions_queue', table_name='submissions')
    op.drop_column('submissions', 'failure_json')
    op.drop_column('submissions', 'runtime_ms')
    op.drop_column('submissions', 'leveled_up')
    op.drop_column('submissions', 'tests_total')
    op.drop_column('submissions', 'tests_passed')
    op.drop_column('submissions', 'settled_at')
    op.drop_column('submissions', 'judged_at')
    op.drop_column('submissions', 'attempts')
    op.drop_column('submissions', 'claimed_at')
    op.drop_column('problems', 'compare_mode')
    op.drop_column('problems', 'graded')
    op.drop_column('problems', 'harness_preamble')
    op.drop_column('problems', 'entrypoint')
    op.drop_index('ix_problem_tests_problem_ordinal', table_name='problem_tests')
    op.drop_index(op.f('ix_problem_tests_problem_id'), table_name='problem_tests')
    op.drop_table('problem_tests')

"""duel mode — two toys, the same problems, one clock

Two tables rather than one. `duels` is the race; `duel_rounds` is its problem set, and
it is a join table rather than a JSONB list of ids so the set has referential integrity
and the 2-second poll can load the problems in one selectinload chain.

The rounds are written at *join* time, not at create time. That is the reveal mechanism:
a waiting duel has no rounds to leak, so there is no `revealed` flag anyone can forget
to check. It also has to be that way because the set is filtered against both toys'
solve histories, and the opponent isn't known until they accept.

`submissions.duel_id` is a sibling of `boss_session_id`, not a generalisation of it —
the two count rounds by different rules and share no query. Its index is partial because
the overwhelming majority of submissions have nothing to do with a duel.

Revision ID: 92b8e2e10041
Revises: b4e19c7a5f02
Create Date: 2026-07-29 16:13:36.634239
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '92b8e2e10041'
down_revision: str | None = 'b4e19c7a5f02'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('duels',
    sa.Column('code', sa.String(length=8), nullable=False),
    sa.Column('host_id', sa.UUID(), nullable=False),
    sa.Column('opponent_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('rounds_total', sa.Integer(), nullable=False),
    sa.Column('total_seconds', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('winner_id', sa.UUID(), nullable=True),
    sa.Column('forfeited_by_id', sa.UUID(), nullable=True),
    sa.Column('host_xp_awarded', sa.Integer(), nullable=False),
    sa.Column('opponent_xp_awarded', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['forfeited_by_id'], ['users.id'], name=op.f('fk_duels_forfeited_by_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['host_id'], ['users.id'], name=op.f('fk_duels_host_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['opponent_id'], ['users.id'], name=op.f('fk_duels_opponent_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['winner_id'], ['users.id'], name=op.f('fk_duels_winner_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_duels'))
    )
    op.create_index('ix_duels_code', 'duels', ['code'], unique=True)
    op.create_index(op.f('ix_duels_host_id'), 'duels', ['host_id'], unique=False)
    op.create_index(op.f('ix_duels_opponent_id'), 'duels', ['opponent_id'], unique=False)
    op.create_table('duel_rounds',
    sa.Column('duel_id', sa.UUID(), nullable=False),
    sa.Column('problem_id', sa.UUID(), nullable=False),
    sa.Column('ordinal', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['duel_id'], ['duels.id'], name=op.f('fk_duel_rounds_duel_id_duels'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_duel_rounds_problem_id_problems'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_duel_rounds')),
    sa.UniqueConstraint('duel_id', 'ordinal', name='uq_duel_rounds_duel_ordinal'),
    sa.UniqueConstraint('duel_id', 'problem_id', name='uq_duel_rounds_duel_problem')
    )
    op.create_index(op.f('ix_duel_rounds_duel_id'), 'duel_rounds', ['duel_id'], unique=False)
    op.create_index(op.f('ix_duel_rounds_problem_id'), 'duel_rounds', ['problem_id'], unique=False)
    op.add_column('submissions', sa.Column('duel_id', sa.UUID(), nullable=True))
    op.create_index('ix_submissions_duel', 'submissions', ['duel_id', 'user_id'], unique=False, postgresql_where=sa.text('duel_id IS NOT NULL'))
    op.create_foreign_key(op.f('fk_submissions_duel_id_duels'), 'submissions', 'duels', ['duel_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(op.f('fk_submissions_duel_id_duels'), 'submissions', type_='foreignkey')
    op.drop_index('ix_submissions_duel', table_name='submissions', postgresql_where=sa.text('duel_id IS NOT NULL'))
    op.drop_column('submissions', 'duel_id')
    op.drop_index(op.f('ix_duel_rounds_problem_id'), table_name='duel_rounds')
    op.drop_index(op.f('ix_duel_rounds_duel_id'), table_name='duel_rounds')
    op.drop_table('duel_rounds')
    op.drop_index(op.f('ix_duels_opponent_id'), table_name='duels')
    op.drop_index(op.f('ix_duels_host_id'), table_name='duels')
    op.drop_index('ix_duels_code', table_name='duels')
    op.drop_table('duels')

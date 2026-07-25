from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Problem, Submission, Zone
from app.schemas.academy import ProblemOut, ZoneOut
from app.services.serialize import problem_out

router = APIRouter(prefix="/zones", tags=["quest map"])


@router.get("", response_model=list[ZoneOut])
async def list_zones(db: DbSession, user: CurrentUser) -> list[ZoneOut]:
    """The quest map: every toy corner with the caller's clear-count."""
    totals = await db.execute(
        select(Zone, func.count(Problem.id))
        .join(Problem, Problem.zone_id == Zone.id, isouter=True)
        .group_by(Zone.id)
        .order_by(Zone.sort_order)
    )

    solved = await db.execute(
        select(Problem.zone_id, func.count(func.distinct(Submission.problem_id)))
        .join(Submission, Submission.problem_id == Problem.id)
        .where(Submission.user_id == user.id, Submission.status == "passed")
        .group_by(Problem.zone_id)
    )
    done_by_zone = {zone_id: int(count) for zone_id, count in solved.all()}

    return [
        ZoneOut(
            id=zone.id,
            slug=zone.slug,
            name=zone.name,
            pattern=zone.pattern,
            color=zone.color,
            blurb=zone.blurb,
            total=int(total),
            done=done_by_zone.get(zone.id, 0),
        )
        for zone, total in totals.all()
    ]


@router.get("/{slug}/problems", response_model=list[ProblemOut])
async def list_zone_problems(slug: str, db: DbSession, user: CurrentUser) -> list[ProblemOut]:
    zone = await db.scalar(select(Zone).where(Zone.slug == slug))
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such corner of the playroom."
        )

    problems = (
        await db.scalars(
            select(Problem).where(Problem.zone_id == zone.id).order_by(Problem.sort_order)
        )
    ).all()

    solved_ids = set(
        (
            await db.scalars(
                select(Submission.problem_id).where(
                    Submission.user_id == user.id, Submission.status == "passed"
                )
            )
        ).all()
    )
    return [problem_out(p, solved=p.id in solved_ids) for p in problems]

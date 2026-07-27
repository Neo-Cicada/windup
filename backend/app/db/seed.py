"""Idempotent catalogue seeding: `python -m app.db.seed`.

Optionally creates a demo toy so the frontend has something to log into:
`python -m app.db.seed --demo`
"""

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import hash_password
from app.db.seed_data import ACHIEVEMENTS, PROBLEMS, ZONES
from app.db.session import SessionLocal, engine
from app.models import (
    Achievement,
    Problem,
    ProblemLanguage,
    ProblemTest,
    Progress,
    Submission,
    SubmissionStatus,
    TestVisibility,
    User,
    XpEvent,
    XpSource,
    Zone,
)
from app.services.achievements import evaluate
from app.services.leveling import apply_xp

DEMO_EMAIL = "bramble@playroom.com"
DEMO_PASSWORD = "windup123"


async def seed_catalogue(db: AsyncSession) -> None:
    zones_by_slug: dict[str, Zone] = {}

    for order, spec in enumerate(ZONES):
        zone = await db.scalar(select(Zone).where(Zone.slug == spec["slug"]))
        if zone is None:
            zone = Zone(**spec, sort_order=order)
            db.add(zone)
        else:
            for key, value in spec.items():
                setattr(zone, key, value)
            zone.sort_order = order
        zones_by_slug[spec["slug"]] = zone

    await db.flush()

    for order, spec in enumerate(PROBLEMS):
        data = dict(spec)
        zone = zones_by_slug[data.pop("zone")]
        cases = data.pop("tests", [])
        # `signature` reads better in the catalogue than `signature_json` does.
        data["signature_json"] = data.pop("signature", None)
        benches = data.pop("languages", {})
        problem = await db.scalar(select(Problem).where(Problem.slug == data["slug"]))
        if problem is None:
            problem = Problem(**data, zone_id=zone.id, sort_order=order)
            db.add(problem)
        else:
            for key, value in data.items():
                setattr(problem, key, value)
            problem.zone_id = zone.id
            problem.sort_order = order

        # Test cases and benches are replaced wholesale rather than diffed —
        # they're content, and re-seeding should leave exactly what seed_data
        # declares. The cases are shared by every language; only the benches are
        # per-language, which is why there is one list of them and not several.
        await db.flush()
        await db.execute(
            delete(ProblemLanguage).where(ProblemLanguage.problem_id == problem.id)
        )
        for language, bench in benches.items():
            db.add(
                ProblemLanguage(
                    problem_id=problem.id,
                    language=language,
                    entrypoint=bench.get("entrypoint"),
                    starter_code=bench.get("starter_code"),
                    harness_preamble=bench.get("harness_preamble", ""),
                )
            )

        await db.execute(delete(ProblemTest).where(ProblemTest.problem_id == problem.id))
        for ordinal, case in enumerate(cases):
            db.add(
                ProblemTest(
                    problem_id=problem.id,
                    ordinal=ordinal,
                    visibility=case.get("visibility", TestVisibility.HIDDEN),
                    label=case.get("label", ""),
                    args_json=case["args"],
                    expected_json=case["expected"],
                )
            )

    for order, spec in enumerate(ACHIEVEMENTS):
        badge = await db.scalar(select(Achievement).where(Achievement.slug == spec["slug"]))
        if badge is None:
            db.add(Achievement(**spec, sort_order=order))
        else:
            for key, value in spec.items():
                setattr(badge, key, value)
            badge.sort_order = order

    await db.commit()


async def seed_demo_user(db: AsyncSession) -> User:
    """A pre-wound toy with history, so every screen has real data to render."""
    user = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is not None:
        return user

    highest = await db.scalar(select(func.max(User.trainee_no)))
    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        toy_name="Bramble",
        trainee_no=(highest or 470) + 1,
        notify_bosses=False,
    )
    user.progress = Progress(xp_max=settings.STARTING_XP_MAX)
    db.add(user)
    await db.flush()

    rng = random.Random(471)
    today = datetime.now(UTC).date()
    problems = list(
        (
            await db.scalars(
                select(Problem).options(selectinload(Problem.tests)).order_by(Problem.sort_order)
            )
        ).all()
    )

    # Solve a handful of problems across the past two weeks.
    for offset, problem in enumerate(problems[:5]):
        day = today - timedelta(days=len(problems[:5]) - offset)
        unaided = offset % 3 != 0
        xp = problem.xp_reward * 2 if unaided else problem.xp_reward
        outcome = apply_xp(user.progress, xp)
        user.progress.solved_count += 1
        if unaided:
            user.progress.unaided_count += 1
        # These never went through the judge, so fill in the verdict columns a
        # real run would have written — otherwise the demo history reads as
        # perpetually pending on the workbench.
        judged = datetime.now(UTC) - timedelta(days=len(problems[:5]) - offset)
        total = len(problem.tests)
        db.add(
            Submission(
                user_id=user.id,
                problem_id=problem.id,
                code=problem.solution,
                language=problem.language,
                status=SubmissionStatus.PASSED,
                unaided=unaided,
                duration_seconds=rng.randint(240, 1400),
                xp_awarded=outcome.xp_awarded,
                coins_awarded=outcome.coins_awarded,
                judged_at=judged,
                settled_at=judged,
                tests_passed=total,
                tests_total=total,
                runtime_ms=rng.randint(40, 260),
            )
        )
        db.add(
            XpEvent(
                user_id=user.id,
                amount=xp,
                source=XpSource.SOLVE,
                note=f"Solved {problem.title}",
                happened_on=day,
            )
        )

    # A few wind-ups to give the weekly chart and heatmap some shape.
    for days_ago in range(0, 14):
        if rng.random() < 0.35:
            continue
        day = today - timedelta(days=days_ago)
        amount = rng.choice([40, 80, 120])
        apply_xp(user.progress, amount)
        db.add(
            XpEvent(
                user_id=user.id,
                amount=amount,
                source=XpSource.WIND_UP,
                note="Wound up the key",
                happened_on=day,
            )
        )

    user.progress.streak = 12
    user.progress.longest_streak = 12
    user.progress.last_active_on = today

    await db.flush()
    await evaluate(db, user.id, user.progress)
    await db.commit()
    return user


async def main(demo: bool) -> None:
    async with SessionLocal() as db:
        await seed_catalogue(db)
        print(f"✓ Seeded {len(ZONES)} zones, {len(PROBLEMS)} problems, {len(ACHIEVEMENTS)} badges.")
        if demo:
            user = await seed_demo_user(db)
            print(f"✓ Demo toy ready: {user.email} / {DEMO_PASSWORD}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Windup Academy database.")
    parser.add_argument("--demo", action="store_true", help="also create the demo toy 'Bramble'")
    args = parser.parse_args()
    asyncio.run(main(args.demo))

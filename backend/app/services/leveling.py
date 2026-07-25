"""Charge, shelf levels and streaks.

The arithmetic here deliberately mirrors `gainXp` in the frontend's
`app/academy/page.tsx` so the optimistic UI and the server never disagree.
"""

from dataclasses import dataclass
from datetime import date

from app.core.config import settings
from app.models import Progress

LEVEL_NAMES = [
    "",
    "Freshly Unboxed",
    "Wind-Up Rookie",
    "Shelf Climber",
    "Spring-Loaded",
    "Top-Shelf Talent",
    "Legendary Toy",
]


def level_name(level: int) -> str:
    return LEVEL_NAMES[max(1, min(level, len(LEVEL_NAMES) - 1))]


@dataclass(slots=True)
class XpOutcome:
    xp_awarded: int
    coins_awarded: int
    leveled_up: bool
    new_level: int


def apply_xp(progress: Progress, amount: int) -> XpOutcome:
    """Add charge, rolling the meter over into new shelf levels as needed."""
    if amount <= 0:
        return XpOutcome(0, 0, False, progress.level)

    xp = progress.xp + amount
    level = progress.level
    xp_max = progress.xp_max
    leveled = False

    while xp >= xp_max:
        xp -= xp_max
        level += 1
        xp_max = round(xp_max * settings.XP_MAX_GROWTH / 10) * 10
        leveled = True

    coins = round(amount / settings.COINS_PER_XP_DIVISOR)

    progress.xp = xp
    progress.xp_max = xp_max
    progress.level = level
    progress.total_xp += amount
    progress.coins += coins

    return XpOutcome(amount, coins, leveled, level)


def touch_streak(progress: Progress, today: date) -> bool:
    """Extend / reset the spinning-top streak. Returns True if today is new activity."""
    last = progress.last_active_on
    if last == today:
        return False

    if last is not None and (today - last).days == 1:
        progress.streak += 1
    else:
        progress.streak = 1

    progress.longest_streak = max(progress.longest_streak, progress.streak)
    progress.last_active_on = today
    return True


def unaided_rate(progress: Progress) -> int:
    if progress.solved_count <= 0:
        return 0
    return round(progress.unaided_count / progress.solved_count * 100)


def interview_ready(progress: Progress, solved_total: int) -> int:
    """A single feel-good readiness number: coverage, level and unaided quality."""
    coverage = min(1.0, progress.solved_count / solved_total) if solved_total else 0.0
    shelf = min(1.0, progress.level / 6)
    quality = unaided_rate(progress) / 100
    return round((coverage * 0.5 + shelf * 0.3 + quality * 0.2) * 100)


def xp_pct(progress: Progress) -> int:
    if progress.xp_max <= 0:
        return 0
    return min(100, round(progress.xp / progress.xp_max * 100))

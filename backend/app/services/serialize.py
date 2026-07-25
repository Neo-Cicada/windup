"""Model -> response shaping shared across endpoints."""

from app.models import Problem, User
from app.schemas.academy import ProblemOut
from app.schemas.user import AvatarOut, NotificationPrefs, UserOut


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        toy_name=user.toy_name,
        trainee_no=f"{user.trainee_no:04d}",
        plan=user.plan,
        avatar=AvatarOut(
            body=user.avatar_body, head=user.avatar_head, accent=user.avatar_accent
        ),
        notifications=NotificationPrefs(
            streak=user.notify_streak, weekly=user.notify_weekly, bosses=user.notify_bosses
        ),
    )


def problem_out(problem: Problem, *, solved: bool = False) -> ProblemOut:
    return ProblemOut(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        weight_label=problem.weight_label,
        xp_reward=problem.xp_reward,
        zone_slug=problem.zone.slug,
        zone_name=problem.zone.name,
        zone_color=problem.zone.color,
        solved=solved,
    )

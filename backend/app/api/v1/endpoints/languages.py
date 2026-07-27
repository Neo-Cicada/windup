"""What this deployment can judge.

The workbench's picker is driven by the problem's own `languages`, not by this —
a language being offered academy-wide doesn't mean a given toy has a bench for
it. This is the catalogue-level answer: what a deployment has fetched artifacts
for and switched on.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.judge.languages import enabled_packs
from app.schemas.academy import LanguageOut

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("", response_model=list[LanguageOut])
async def list_languages(user: CurrentUser) -> list[LanguageOut]:
    return [
        LanguageOut(
            slug=pack.slug,
            label=pack.label,
            extension=pack.extension,
            runs_in_browser=pack.runs_in_browser,
        )
        for pack in enabled_packs()
    ]

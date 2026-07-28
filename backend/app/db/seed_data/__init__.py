"""Catalogue content for the academy.

Zones and badges are lifted from the frontend's `components/academy/data.ts` so
the seeded API returns exactly what the UI was designed against.

This was a single module until the catalogue grew to cover the whole roadmap. It
is a package now, split the way the map is: one module per zone under
`problems/`, plus the preambles they share and the `problem()` spec they are
written in. The three names the seeder and the tests import are unchanged.
"""

from app.db.seed_data.achievements import ACHIEVEMENTS
from app.db.seed_data.problems import PROBLEMS
from app.db.seed_data.zones import ZONES

__all__ = ["ACHIEVEMENTS", "PROBLEMS", "ZONES"]

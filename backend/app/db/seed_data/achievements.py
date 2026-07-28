"""Badges on the merit sash.

Lifted from the frontend's `components/academy/data.ts` so the seeded API returns
exactly what the UI was designed against. The three zone-clear badges name their
zone in `app/services/achievements.py`, not here.
"""

ACHIEVEMENTS: list[dict] = [
    {
        "slug": "first-fix",
        "name": "First Fix",
        "description": "Solve your first toy",
        "color": "#6FBF73",
    },
    {
        "slug": "week-winder",
        "name": "Week Winder",
        "description": "7-day streak",
        "color": "#EF5B54",
    },
    {
        "slug": "unaided-ace",
        "name": "Unaided Ace",
        "description": "10 solves, no chests",
        "color": "#4FB0E5",
    },
    {
        "slug": "block-master",
        "name": "Block Master",
        "description": "Clear Building Blocks",
        "color": "#F7C948",
    },
    {
        "slug": "night-owl",
        "name": "Night Owl",
        "description": "Solve after midnight",
        "color": "#8B6FD6",
    },
    {
        "slug": "boss-slayer",
        "name": "Boss Slayer",
        "description": "Beat a Boss Battle",
        "color": "#E08A3C",
    },
    {
        "slug": "marble-champ",
        "name": "Marble Champ",
        "description": "Clear Marble Run",
        "color": "#4FB0E5",
    },
    {
        "slug": "century-toy",
        "name": "Century Toy",
        "description": "Solve 100 problems",
        "color": "#EF5B54",
    },
    {
        "slug": "perfect-week",
        "name": "Perfect Week",
        "description": "All quests, 7 days",
        "color": "#6FBF73",
    },
    {
        "slug": "graph-guru",
        "name": "Graph Guru",
        "description": "Clear Board Game",
        "color": "#8B6FD6",
    },
    {
        "slug": "speed-wind",
        "name": "Speed Wind",
        "description": "Solve under 5 min",
        "color": "#F7C948",
    },
    {
        "slug": "top-shelf",
        "name": "Top Shelf",
        "description": "Reach Level 5",
        "color": "#E08A3C",
    },
]

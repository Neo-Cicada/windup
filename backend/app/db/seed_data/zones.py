"""The corners of the quest map.

One zone per topic on the NeetCode roadmap, in the order the roadmap walks them,
so a toy that starts at the top-left and works right is following a real study
path rather than a pile of puzzles. Toy Kitchen is the exception and comes last:
SQL isn't on that roadmap, but the academy teaches it anyway.

`sort_order` is assigned by position here, so reordering this list reorders the
map. Three slugs are load-bearing beyond the map — `building-blocks`,
`marble-run` and `board-game` are named by the zone-clear badges in
`app/services/achievements.py`.
"""

ZONES: list[dict] = [
    {
        "slug": "building-blocks",
        "name": "Building Blocks",
        "pattern": "Arrays & Hashing",
        "color": "#6FBF73",
        "blurb": "Snap-together cubes",
    },
    {
        "slug": "rubber-bands",
        "name": "Rubber Bands",
        "pattern": "Two Pointers",
        "color": "#EF8354",
        "blurb": "Stretch in from both ends",
    },
    {
        "slug": "stacking-cups",
        "name": "Stacking Cups",
        "pattern": "Stack",
        "color": "#E08A3C",
        "blurb": "Last in, first out",
    },
    {
        "slug": "see-saw",
        "name": "See-Saw",
        "pattern": "Binary Search",
        "color": "#4FB0E5",
        "blurb": "Tip left, tip right, settle",
    },
    {
        "slug": "peek-a-boo",
        "name": "Peek-a-Boo Window",
        "pattern": "Sliding Window",
        "color": "#F7C948",
        "blurb": "A frame that slides along",
    },
    {
        "slug": "marble-run",
        "name": "Marble Run",
        "pattern": "Linked Lists",
        "color": "#3FA9A0",
        "blurb": "Chutes & pointers",
    },
    {
        "slug": "branching-mobile",
        "name": "Branching Mobile",
        "pattern": "Trees",
        "color": "#8B6FD6",
        "blurb": "Everything hangs in balance",
    },
    {
        "slug": "spelling-beads",
        "name": "Spelling Beads",
        "pattern": "Tries",
        "color": "#D6608F",
        "blurb": "Thread letters into words",
    },
    {
        "slug": "weighted-tops",
        "name": "Weighted Tops",
        "pattern": "Heap & Priority Queue",
        "color": "#5C9EAD",
        "blurb": "The heaviest spins to the top",
    },
    {
        "slug": "maze-toy",
        "name": "Maze Toy",
        "pattern": "Backtracking",
        "color": "#A3C644",
        "blurb": "Try a path, then walk it back",
    },
    {
        "slug": "board-game",
        "name": "Board Game",
        "pattern": "Graphs",
        "color": "#EF5B54",
        "blurb": "Roll, branch, explore",
    },
    {
        "slug": "puzzle-box",
        "name": "Puzzle Box",
        "pattern": "1-D Dynamic Programming",
        "color": "#7A8BD1",
        "blurb": "Solve once, reuse",
    },
    {
        "slug": "train-track",
        "name": "Train Track",
        "pattern": "Intervals",
        "color": "#B5651D",
        "blurb": "Segments that must not collide",
    },
    {
        "slug": "piggy-bank",
        "name": "Piggy Bank",
        "pattern": "Greedy",
        "color": "#F0A202",
        "blurb": "Take the best coin now",
    },
    {
        "slug": "railway-set",
        "name": "Railway Set",
        "pattern": "Advanced Graphs",
        "color": "#C97BC4",
        "blurb": "The cheapest route across the room",
    },
    {
        "slug": "quilt-squares",
        "name": "Quilt Squares",
        "pattern": "2-D Dynamic Programming",
        "color": "#6C8EBF",
        "blurb": "A grid of stitched-together answers",
    },
    {
        "slug": "light-switches",
        "name": "Light Switches",
        "pattern": "Bit Manipulation",
        "color": "#45B39D",
        "blurb": "Flip one bit at a time",
    },
    {
        "slug": "spinning-top",
        "name": "Spinning Top",
        "pattern": "Math & Geometry",
        "color": "#9B59B6",
        "blurb": "Turns, digits and spirals",
    },
    {
        "slug": "toy-kitchen",
        "name": "Toy Kitchen",
        "pattern": "SQL",
        "color": "#E2725B",
        "blurb": "Recipes & queries",
    },
]

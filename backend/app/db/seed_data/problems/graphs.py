"""Board Game — Graphs.

Roll, branch, explore. Four of these are grids, which are graphs that don't look
like one: the cells are the nodes and "next to" is the edge. The fifth drops the
disguise and hands you the edges directly.

The choice of walk is the lesson. Flood fill doesn't care whether it goes depth
or breadth first; the rotting oranges do, because the answer is a *distance* and
only breadth-first visits things in distance order.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "board-game"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="number-of-islands",
        title="Number of Islands",
        difficulty="medium",
        prompt=(
            "The board game's map has patches of land ('1') in a sea of water ('0'). Count how "
            "many separate islands the playing pieces can land on."
        ),
        example_input='grid = [["1","1","0"],["1","0","0"],["0","0","1"]]',
        example_output="2",
        entrypoint="numIslands",
        signature=sig("int", grid="matrix<string>"),
        explainer=(
            "**Flood fill.** Every time you find un-visited land, that's a brand-new island — "
            "then sink the whole connected patch so you never count it twice."
        ),
        hint=(
            "Sink visited land by writing '0' back into the grid; "
            "that's your visited set, for free."
        ),
        approach=(
            "1) Scan every cell. 2) When you hit '1', increment the count. 3) DFS/BFS out from "
            "that cell, flipping every connected '1' to '0'. 4) Continue the scan. "
            "O(rows x cols) time."
        ),
        solution=(
            "def numIslands(grid):\n"
            "    if not grid:\n"
            "        return 0\n"
            "    rows, cols = len(grid), len(grid[0])\n\n"
            "    def sink(r, c):\n"
            "        if 0 <= r < rows and 0 <= c < cols and grid[r][c] == '1':\n"
            "            grid[r][c] = '0'\n"
            "            sink(r + 1, c); sink(r - 1, c)\n"
            "            sink(r, c + 1); sink(r, c - 1)\n\n"
            "    count = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] == '1':\n"
            "                count += 1\n"
            "                sink(r, c)\n"
            "    return count"
        ),
        tests=[
            example([[["1", "1", "0"], ["1", "0", "0"], ["0", "0", "1"]]], 2),
            example([[["1", "1", "1", "1", "0"], ["1", "1", "0", "1", "0"],
                      ["1", "1", "0", "0", "0"], ["0", "0", "0", "0", "0"]]], 1),
            hidden("three separate patches",
                   [[["1", "1", "0", "0", "0"], ["1", "1", "0", "0", "0"],
                     ["0", "0", "1", "0", "0"], ["0", "0", "0", "1", "1"]]], 3),
            hidden("all water", [[["0"]]], 0),
            hidden("one square of land", [[["1"]]], 1),
            hidden("empty row", [[[]]], 0),
            hidden("stripes in a single row", [[["1", "0", "1", "0", "1"]]], 3),
        ],
    ),
    problem(
        zone=ZONE,
        slug="max-area-of-island",
        title="Max Area of Island",
        difficulty="medium",
        prompt=(
            "Same map, but the squares are 1s and 0s and you want the *biggest* island rather "
            "than the count. Return how many squares it covers, or 0 if it's all water."
        ),
        example_input="grid = [[1, 1, 0], [1, 0, 0], [0, 0, 1]]",
        example_output="3",
        entrypoint="maxAreaOfIsland",
        signature=sig("int", grid="matrix<int>"),
        explainer=(
            "**The same flood fill, counting as it goes.** Sinking a patch already visits every "
            "square of it exactly once — so have the fill return a size instead of nothing, and "
            "keep the largest you see."
        ),
        hint=(
            "The recursive fill returns 1 + the four neighbours' sizes. Sinking the square "
            "*before* you recurse is what stops it being counted again from the other side."
        ),
        approach=(
            "1) fill(r, c): 0 if off the grid or water; otherwise set it to 0 and return 1 plus "
            "the four neighbours. 2) Take the max over every starting square. "
            "O(rows × cols)."
        ),
        solution=(
            "def maxAreaOfIsland(grid):\n"
            "    if not grid or not grid[0]:\n"
            "        return 0\n"
            "    rows, cols = len(grid), len(grid[0])\n\n"
            "    def fill(r, c):\n"
            "        if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != 1:\n"
            "            return 0\n"
            "        grid[r][c] = 0\n"
            "        return (1 + fill(r + 1, c) + fill(r - 1, c)\n"
            "                + fill(r, c + 1) + fill(r, c - 1))\n\n"
            "    best = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            best = max(best, fill(r, c))\n"
            "    return best"
        ),
        tests=[
            example([[[1, 1, 0], [1, 0, 0], [0, 0, 1]]], 3),
            example([[[0, 0, 0, 0]]], 0),
            hidden("one square of land", [[[1]]], 1),
            hidden("an empty row", [[[]]], 0),
            hidden("the whole board is one island", [[[1, 1], [1, 1]]], 4),
            hidden("corners don't connect", [[[1, 0], [0, 1]]], 1),
            hidden("a diagonal staircase of squares", [[[1, 1, 0], [0, 1, 1], [0, 0, 1]]], 5),
        ],
    ),
    problem(
        zone=ZONE,
        slug="course-schedule",
        title="Course Schedule",
        difficulty="medium",
        prompt=(
            "The academy's lessons have prerequisites: [a, b] means b must be finished before "
            "a. Given how many lessons there are and the pairs, say whether every lesson can be "
            "finished."
        ),
        example_input="numCourses = 2, prerequisites = [[1, 0]]",
        example_output="true",
        entrypoint="canFinish",
        signature=sig("bool", numCourses="int", prerequisites="matrix<int>"),
        explainer=(
            "**The question is whether there's a loop.** Lessons and prerequisites form a "
            "directed graph, and every lesson is finishable exactly when that graph has no "
            "cycle. Peel off lessons with nothing left to wait for; if you run out of those "
            "before running out of lessons, what's left is a loop."
        ),
        hint=(
            "Kahn's algorithm: count how many prerequisites each lesson still has, queue the "
            "zeroes, and each time you take one off the queue, decrement its dependants."
        ),
        approach=(
            "1) Build the adjacency list and in-degree counts. 2) Queue every lesson with "
            "in-degree 0. 3) Pop, count it, decrement its dependants, queueing any that reach "
            "0. 4) Return counted == numCourses. O(lessons + pairs)."
        ),
        solution=(
            "from collections import deque\n\n"
            "def canFinish(numCourses, prerequisites):\n"
            "    unlocks = [[] for _ in range(numCourses)]\n"
            "    waiting_on = [0] * numCourses\n"
            "    for course, needs in prerequisites:\n"
            "        unlocks[needs].append(course)\n"
            "        waiting_on[course] += 1\n"
            "    queue = deque(i for i in range(numCourses) if waiting_on[i] == 0)\n"
            "    finished = 0\n"
            "    while queue:\n"
            "        course = queue.popleft()\n"
            "        finished += 1\n"
            "        for nxt in unlocks[course]:\n"
            "            waiting_on[nxt] -= 1\n"
            "            if waiting_on[nxt] == 0:\n"
            "                queue.append(nxt)\n"
            "    return finished == numCourses"
        ),
        tests=[
            example([2, [[1, 0]]], True),
            example([2, [[1, 0], [0, 1]]], False),
            hidden("one lesson, no prerequisites", [1, []], True),
            hidden("no lessons at all", [0, []], True),
            hidden("a long straight chain", [5, [[1, 0], [2, 1], [3, 2], [4, 3]]], True),
            hidden("a three-lesson loop", [3, [[0, 1], [1, 2], [2, 0]]], False),
            hidden("a diamond is not a loop", [4, [[1, 0], [2, 0], [3, 1], [3, 2]]], True),
        ],
    ),
    problem(
        zone=ZONE,
        slug="rotting-oranges",
        title="Rotting Oranges",
        difficulty="medium",
        prompt=(
            "The toy fruit basket is a grid: 0 is an empty square, 1 a fresh orange, 2 a rotten "
            "one. Every minute, a rotten orange spoils the fresh ones directly beside it. "
            "Return how many minutes until nothing fresh is left, or -1 if that never happens."
        ),
        example_input="grid = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]",
        example_output="4",
        entrypoint="orangesRotting",
        signature=sig("int", grid="matrix<int>"),
        explainer=(
            "**Breadth-first, one whole minute per layer.** All the rotten oranges start "
            "spreading at once, so seed the queue with every one of them and then process the "
            "queue a full layer at a time — each layer drained is one minute gone."
        ),
        hint=(
            "Count the fresh oranges up front. That's how you tell 'finished early' from "
            "'something was walled off' at the end, and it saves rescanning the grid."
        ),
        approach=(
            "1) Queue every rotten square, count the fresh ones. 2) While the queue has "
            "something and fresh remains: drain exactly the current layer, spoiling neighbours "
            "and decrementing fresh; add a minute. 3) Return -1 if any fresh survived."
        ),
        solution=(
            "from collections import deque\n\n"
            "def orangesRotting(grid):\n"
            "    if not grid or not grid[0]:\n"
            "        return 0\n"
            "    rows, cols = len(grid), len(grid[0])\n"
            "    queue = deque()\n"
            "    fresh = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] == 2:\n"
            "                queue.append((r, c))\n"
            "            elif grid[r][c] == 1:\n"
            "                fresh += 1\n"
            "    minutes = 0\n"
            "    while queue and fresh:\n"
            "        for _ in range(len(queue)):\n"
            "            r, c = queue.popleft()\n"
            "            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "                nr, nc = r + dr, c + dc\n"
            "                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:\n"
            "                    grid[nr][nc] = 2\n"
            "                    fresh -= 1\n"
            "                    queue.append((nr, nc))\n"
            "        minutes += 1\n"
            "    return -1 if fresh else minutes"
        ),
        tests=[
            example([[[2, 1, 1], [1, 1, 0], [0, 1, 1]]], 4),
            example([[[2, 1, 1], [0, 1, 1], [1, 0, 1]]], -1),
            hidden("nothing fresh to spoil", [[[0, 2]]], 0),
            hidden("an empty square on its own", [[[0]]], 0),
            hidden("one fresh orange and nothing rotten", [[[1]]], -1),
            hidden("side by side", [[[1, 2]]], 1),
            hidden("rot spreading from both corners", [[[2, 1, 1], [1, 1, 1], [0, 1, 2]]], 2),
        ],
    ),
    problem(
        zone=ZONE,
        slug="pacific-atlantic-water-flow",
        title="Pacific Atlantic Water Flow",
        difficulty="medium",
        prompt=(
            "The board is a height map. Water runs from a square to any neighbour of equal or "
            "lower height. The top and left edges touch one ocean, the bottom and right edges "
            "the other. Return every square that can drain to both, as [row, col] pairs in any "
            "order."
        ),
        example_input="heights = [[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1]]",
        example_output="[[0, 4], [1, 3], [1, 4], [2, 2], …]",
        entrypoint="pacificAtlantic",
        signature=sig("matrix<int>", heights="matrix<int>"),
        # Any order of the squares; each square is a pair and stays one.
        compare_mode="unordered",
        explainer=(
            "**Walk uphill from the sea instead of downhill from each square.** Asking 'where "
            "can this square reach' for every square re-treads the same ground constantly. "
            "Starting at the coast and climbing to squares that are no lower answers the "
            "question for every square in one sweep per ocean; the answer is the overlap."
        ),
        hint=(
            "Two visited sets, one per ocean, seeded with that ocean's whole coastline. The "
            "step rule reverses along with the direction: climb to a neighbour that is >= where "
            "you are."
        ),
        approach=(
            "1) flow(starts): DFS/BFS from those cells, stepping only to neighbours at least as "
            "high. 2) Run it from the top+left edges and from the bottom+right edges. "
            "3) Return the intersection. O(rows × cols)."
        ),
        solution=(
            "def pacificAtlantic(heights):\n"
            "    if not heights or not heights[0]:\n"
            "        return []\n"
            "    rows, cols = len(heights), len(heights[0])\n\n"
            "    def flow(starts):\n"
            "        seen = set(starts)\n"
            "        stack = list(starts)\n"
            "        while stack:\n"
            "            r, c = stack.pop()\n"
            "            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "                nr, nc = r + dr, c + dc\n"
            "                if (0 <= nr < rows and 0 <= nc < cols\n"
            "                        and (nr, nc) not in seen\n"
            "                        and heights[nr][nc] >= heights[r][c]):\n"
            "                    seen.add((nr, nc))\n"
            "                    stack.append((nr, nc))\n"
            "        return seen\n\n"
            "    pacific = flow([(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)])\n"
            "    atlantic = flow([(rows - 1, c) for c in range(cols)]\n"
            "                    + [(r, cols - 1) for r in range(rows)])\n"
            "    return [[r, c] for r, c in sorted(pacific & atlantic)]"
        ),
        tests=[
            example([[[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5],
                      [5, 1, 1, 2, 4]]],
                    [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]),
            example([[[1]]], [[0, 0]]),
            hidden("an empty board", [[[]]], []),
            hidden("every square reaches both", [[[2, 1], [1, 2]]],
                   [[0, 0], [0, 1], [1, 0], [1, 1]]),
            hidden("a spiral of heights", [[[1, 2, 3], [8, 9, 4], [7, 6, 5]]],
                   [[0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]),
            hidden("one row is all coast", [[[1, 2, 3]]], [[0, 0], [0, 1], [0, 2]]),
            hidden("one column is all coast", [[[1], [2], [3]]], [[0, 0], [1, 0], [2, 0]]),
        ],
    ),
]

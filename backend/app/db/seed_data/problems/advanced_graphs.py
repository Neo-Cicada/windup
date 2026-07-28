"""Railway Set — Advanced Graphs.

The same board, but the track now costs something to lay. Four shortest-path and
spanning-tree classics — Dijkstra twice in disguise, Prim, and Bellman-Ford —
plus the one that isn't about weight at all: an Euler path that has to use every
ticket exactly once.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "railway-set"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="network-delay-time",
        title="Network Delay Time",
        difficulty="medium",
        prompt=(
            "A signal starts at station k and travels down one-way tracks, each taking some "
            "time. Stations are numbered 1 to n. Return how long until every station has heard "
            "it, or -1 if some station never does."
        ),
        example_input="times = [[2, 1, 1], [2, 3, 1], [3, 4, 1]], n = 4, k = 2",
        example_output="2",
        entrypoint="networkDelayTime",
        signature=sig("int", times="matrix<int>", n="int", k="int"),
        explainer=(
            "**Dijkstra, then take the worst.** Each station hears the signal at its shortest "
            "distance from k, so settle them nearest-first out of a min-heap. The answer is the "
            "largest of those distances — a signal isn't done until the slowest station has it."
        ),
        hint=(
            "Stations are numbered from 1, not 0. And check the count at the end: if fewer than "
            "n stations were ever settled, one of them is unreachable and the answer is -1."
        ),
        approach=(
            "1) Build an adjacency list. 2) Heap of (time, station), starting at (0, k). "
            "3) Pop; skip if already settled; record and push its neighbours. 4) Return the max "
            "distance if all n were settled, else -1. O(E log V)."
        ),
        solution=(
            "import heapq\n"
            "from collections import defaultdict\n\n"
            "def networkDelayTime(times, n, k):\n"
            "    tracks = defaultdict(list)\n"
            "    for source, target, weight in times:\n"
            "        tracks[source].append((target, weight))\n"
            "    settled = {}\n"
            "    heap = [(0, k)]\n"
            "    while heap:\n"
            "        elapsed, station = heapq.heappop(heap)\n"
            "        if station in settled:\n"
            "            continue\n"
            "        settled[station] = elapsed\n"
            "        for target, weight in tracks[station]:\n"
            "            if target not in settled:\n"
            "                heapq.heappush(heap, (elapsed + weight, target))\n"
            "    return max(settled.values()) if len(settled) == n else -1"
        ),
        tests=[
            example([[[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2], 2),
            example([[[1, 2, 1]], 2, 1], 1),
            hidden("the track runs the wrong way", [[[1, 2, 1]], 2, 2], -1),
            hidden("the long way round is quicker",
                   [[[1, 2, 1], [2, 3, 2], [1, 3, 4]], 3, 1], 3),
            hidden("one station, nothing to send", [[], 1, 1], 0),
            hidden("a track back the other way", [[[1, 2, 1], [2, 1, 3]], 2, 2], 3),
            hidden("a shortcut that isn't one",
                   [[[1, 2, 1], [2, 3, 7], [1, 3, 4], [2, 1, 2]], 3, 1], 4),
        ],
    ),
    problem(
        zone=ZONE,
        slug="min-cost-to-connect-all-points",
        title="Min Cost to Connect All Points",
        difficulty="medium",
        prompt=(
            "Stations are pinned to the playmat at [x, y]. Track between two of them costs the "
            "walking distance |x1-x2| + |y1-y2|. Return the cheapest way to connect every "
            "station to every other, directly or not."
        ),
        example_input="points = [[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]",
        example_output="20",
        entrypoint="minCostConnectPoints",
        signature=sig("int", points="matrix<int>"),
        explainer=(
            "**Grow one blob of connected stations.** Start anywhere. Repeatedly lay the "
            "cheapest piece of track joining the blob to a station outside it. That's Prim's "
            "algorithm, and it provably ends up with the cheapest possible network."
        ),
        hint=(
            "Every pair of stations is joinable, so there's no adjacency list to build — the "
            "distance is a formula. Keep, for each station outside the blob, the cheapest track "
            "reaching it, and refresh those each time the blob grows."
        ),
        approach=(
            "1) best[0] = 0, everything else infinity. 2) n times: take the cheapest unjoined "
            "station, add its cost, mark it joined, and refresh best[] for the rest. 3) Return "
            "the total. O(n²), which beats sorting all n² edges."
        ),
        solution=(
            "def minCostConnectPoints(points):\n"
            "    n = len(points)\n"
            "    if n <= 1:\n"
            "        return 0\n"
            "    best = [float('inf')] * n\n"
            "    best[0] = 0\n"
            "    joined = [False] * n\n"
            "    total = 0\n"
            "    for _ in range(n):\n"
            "        here = min(\n"
            "            (i for i in range(n) if not joined[i]), key=lambda i: best[i]\n"
            "        )\n"
            "        joined[here] = True\n"
            "        total += best[here]\n"
            "        for other in range(n):\n"
            "            if not joined[other]:\n"
            "                distance = (abs(points[here][0] - points[other][0])\n"
            "                            + abs(points[here][1] - points[other][1]))\n"
            "                if distance < best[other]:\n"
            "                    best[other] = distance\n"
            "    return total"
        ),
        tests=[
            example([[[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]], 20),
            example([[[3, 12], [-2, 5], [-4, 1]]], 18),
            hidden("one station needs no track", [[[0, 0]]], 0),
            hidden("no stations at all", [[]], 0),
            hidden("two stations, one piece", [[[0, 0], [1, 1]]], 2),
            hidden("a corner and two arms", [[[0, 0], [0, 3], [4, 0]]], 7),
            hidden("four corners of a square", [[[-1, -1], [1, 1], [-1, 1], [1, -1]]], 6),
        ],
    ),
    problem(
        zone=ZONE,
        slug="cheapest-flights-within-k-stops",
        title="Cheapest Flights Within K Stops",
        difficulty="medium",
        prompt=(
            "The toy aeroplane flies between n cities at a price per hop. Get from src to dst "
            "using at most k stops in between, as cheaply as possible. Return -1 if it can't be "
            "done."
        ),
        example_input=(
            "n = 4, flights = [[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]], "
            "src = 0, dst = 3, k = 1"
        ),
        example_output="700",
        entrypoint="findCheapestPrice",
        signature=sig(
            "int", n="int", flights="matrix<int>", src="int", dst="int", k="int"
        ),
        explainer=(
            "**Count the hops, not just the price.** Plain Dijkstra settles a city at its "
            "cheapest price and never revisits it — but here a dearer route with fewer stops "
            "can be the only legal one. Bellman-Ford sidesteps that: relax every flight k + 1 "
            "times, and after round r the prices are the best reachable in r hops."
        ),
        hint=(
            "Relax from a *snapshot* of the previous round, not from the array you're writing "
            "into. Otherwise one round can chain two flights together and quietly overshoot the "
            "stop limit."
        ),
        approach=(
            "1) price[src] = 0, everything else infinity. 2) Repeat k + 1 times: copy the "
            "array, and for each flight u→v, improve the copy from the old array. 3) Return "
            "price[dst] or -1. O(k × flights)."
        ),
        solution=(
            "def findCheapestPrice(n, flights, src, dst, k):\n"
            "    price = [float('inf')] * n\n"
            "    price[src] = 0\n"
            "    for _ in range(k + 1):\n"
            "        nxt = price[:]\n"
            "        for start, end, cost in flights:\n"
            "            if price[start] + cost < nxt[end]:\n"
            "                nxt[end] = price[start] + cost\n"
            "        price = nxt\n"
            "    return -1 if price[dst] == float('inf') else price[dst]"
        ),
        tests=[
            example([4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]],
                     0, 3, 1], 700),
            example([3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1], 200),
            hidden("no stops allowed, so pay for the direct flight",
                   [3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0], 500),
            hidden("no flights at all", [2, [], 0, 1, 5], -1),
            hidden("already there", [1, [], 0, 0, 0], 0),
            hidden("the only way round is the long way",
                   [3, [[0, 1, 2], [1, 2, 1], [2, 0, 10]], 1, 0, 1], 11),
            hidden("cheaper with more hops, and they're allowed",
                   [5, [[0, 1, 5], [1, 2, 5], [0, 3, 2], [3, 1, 2], [1, 4, 1], [4, 2, 1]],
                    0, 2, 2], 7),
        ],
    ),
    problem(
        zone=ZONE,
        slug="swim-in-rising-water",
        title="Swim in Rising Water",
        difficulty="hard",
        prompt=(
            "The bath toy starts at the top-left of a square grid of depths and wants the "
            "bottom-right. At time t you may stand on any square whose depth is at most t, and "
            "moving between neighbouring squares is instant. Return the earliest time you can "
            "arrive."
        ),
        example_input="grid = [[0, 2], [1, 3]]",
        example_output="3",
        entrypoint="swimInWater",
        signature=sig("int", grid="matrix<int>"),
        explainer=(
            "**The cost of a path is its deepest square, not its total.** So instead of adding "
            "up weights, carry a running maximum: pull squares out of a min-heap shallowest "
            "first, and the first time you pop the corner, the worst square you were forced "
            "through is the answer."
        ),
        hint=(
            "This is Dijkstra with `max` where the `+` usually goes. The starting square counts "
            "too — you have to be able to stand on it before you can go anywhere."
        ),
        approach=(
            "1) Heap of (depth, r, c) starting at the top-left, plus a seen set. 2) Pop, "
            "updating the running worst depth. 3) On reaching the corner, return it. "
            "4) Otherwise push unseen neighbours. O(n² log n)."
        ),
        solution=(
            "import heapq\n\n"
            "def swimInWater(grid):\n"
            "    n = len(grid)\n"
            "    heap = [(grid[0][0], 0, 0)]\n"
            "    seen = {(0, 0)}\n"
            "    worst = 0\n"
            "    while heap:\n"
            "        depth, r, c = heapq.heappop(heap)\n"
            "        worst = max(worst, depth)\n"
            "        if r == n - 1 and c == n - 1:\n"
            "            return worst\n"
            "        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "            nr, nc = r + dr, c + dc\n"
            "            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:\n"
            "                seen.add((nr, nc))\n"
            "                heapq.heappush(heap, (grid[nr][nc], nr, nc))\n"
            "    return -1"
        ),
        tests=[
            example([[[0, 2], [1, 3]]], 3),
            example([[[0]]], 0),
            hidden("the spiral", [[[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16],
                                   [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]]], 16),
            hidden("either way round costs the same", [[[0, 1], [2, 3]]], 3),
            hidden("the start is not the shallowest", [[[3, 2], [0, 1]]], 3),
            hidden("a shallow detour beats a deep shortcut",
                   [[[0, 9, 9], [1, 9, 9], [2, 3, 4]]], 4),
            hidden("already flat", [[[0, 0], [0, 0]]], 0),
        ],
    ),
    problem(
        zone=ZONE,
        slug="reconstruct-itinerary",
        title="Reconstruct Itinerary",
        difficulty="hard",
        prompt=(
            "You hold a stack of one-way tickets and must use every one exactly once, starting "
            "from JFK. Return the airports in the order you visit them; where there's a choice, "
            "take the one that comes first alphabetically. A valid trip always exists."
        ),
        example_input='tickets = [["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]]',
        example_output='["JFK", "MUC", "LHR", "SFO", "SJC"]',
        entrypoint="findItinerary",
        signature=sig("list<string>", tickets="matrix<string>"),
        explainer=(
            "**Walk until you're stuck, then unwind.** Greedily taking the alphabetically first "
            "ticket can strand you at an airport with tickets still unused elsewhere — but the "
            "airport you got stuck at is genuinely the *last* stop. So record it on the way "
            "back out, and reverse at the end."
        ),
        hint=(
            "Hierholzer's algorithm. Sort each airport's destinations in reverse so popping off "
            "the end gives you the alphabetically first, and build the route backwards."
        ),
        approach=(
            "1) Group destinations by origin, each sorted descending. 2) Stack starting at "
            "JFK: while the top has tickets left, push the next one. 3) When it has none, pop "
            "it onto the route. 4) Reverse the route. O(E log E)."
        ),
        solution=(
            "from collections import defaultdict\n\n"
            "def findItinerary(tickets):\n"
            "    onward = defaultdict(list)\n"
            "    for origin, destination in sorted(tickets, reverse=True):\n"
            "        onward[origin].append(destination)\n"
            "    route = []\n"
            "    stack = ['JFK']\n"
            "    while stack:\n"
            "        while onward[stack[-1]]:\n"
            "            stack.append(onward[stack[-1]].pop())\n"
            "        route.append(stack.pop())\n"
            "    return route[::-1]"
        ),
        tests=[
            example([[["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]],
                    ["JFK", "MUC", "LHR", "SFO", "SJC"]),
            example([[["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"],
                      ["ATL", "SFO"]]],
                    ["JFK", "ATL", "JFK", "SFO", "ATL", "SFO"]),
            hidden("a single ticket", [[["JFK", "A"]]], ["JFK", "A"]),
            hidden("greedy first, then back to the other",
                   [[["JFK", "B"], ["JFK", "A"], ["A", "JFK"]]], ["JFK", "A", "JFK", "B"]),
            hidden("the alphabetical choice would strand you",
                   [[["JFK", "KUL"], ["JFK", "NRT"], ["NRT", "JFK"]]],
                   ["JFK", "NRT", "JFK", "KUL"]),
            hidden("a straight line out", [[["JFK", "A"], ["A", "B"], ["B", "C"]]],
                   ["JFK", "A", "B", "C"]),
            hidden("a round trip", [[["JFK", "A"], ["A", "JFK"]]], ["JFK", "A", "JFK"]),
        ],
    ),
]

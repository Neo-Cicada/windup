"""Weighted Tops — Heap & Priority Queue.

Spinning tops of different weights, and a box that always hands you the heaviest
one back. Sorting answers all of these too; a heap wins when the collection keeps
changing — every problem here but the first puts something *back* in.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "weighted-tops"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="kth-largest-element",
        title="Kth Largest Element",
        difficulty="medium",
        prompt=(
            "Line the spinning tops up by weight and hand back the kth heaviest. Duplicates "
            "count separately — the 2nd heaviest of [3, 3, 1] is 3."
        ),
        example_input="nums = [3, 2, 1, 5, 6, 4], k = 2",
        example_output="5",
        entrypoint="findKthLargest",
        signature=sig("int", nums="list<int>", k="int"),
        explainer=(
            "**You only need to remember k of them.** Keep a box holding the k heaviest tops "
            "seen so far, with the *lightest* of those on top. Every new top either displaces "
            "that one or is thrown away — and at the end, the one on top is the answer."
        ),
        hint=(
            "Sorting is O(n log n) and completely fine. A heap of size k is O(n log k), which "
            "matters when k is small and n is not."
        ),
        approach=(
            "1) Push the first k values onto a min-heap. 2) For each remaining value, if it "
            "beats the heap's smallest, pop and push. 3) Return the smallest. Or simply "
            "sorted(nums)[-k]."
        ),
        solution=(
            "import heapq\n\n"
            "def findKthLargest(nums, k):\n"
            "    heap = nums[:k]\n"
            "    heapq.heapify(heap)\n"
            "    for value in nums[k:]:\n"
            "        if value > heap[0]:\n"
            "            heapq.heapreplace(heap, value)\n"
            "    return heap[0]"
        ),
        tests=[
            example([[3, 2, 1, 5, 6, 4], 2], 5),
            example([[3, 2, 3, 1, 2, 4, 5, 5, 6], 4], 4),
            hidden("one top", [[1], 1], 1),
            hidden("the lightest of two", [[2, 1], 2], 1),
            hidden("every top the same weight", [[7, 7, 7], 2], 7),
            hidden("all negative", [[-1, -5, -3], 1], -1),
            hidden("k is the whole box", [[5, 4, 3, 2, 1], 5], 1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="last-stone-weight",
        title="Last Stone Weight",
        difficulty="easy",
        prompt=(
            "Smash the two heaviest play-stones together. Equal weights destroy each other; "
            "otherwise the lighter is destroyed and the heavier loses its weight. Repeat until "
            "at most one stone is left, and return its weight — or 0 if none is."
        ),
        example_input="stones = [2, 7, 4, 1, 8, 1]",
        example_output="1",
        entrypoint="lastStoneWeight",
        signature=sig("int", stones="list<int>"),
        explainer=(
            "**The heap is the whole algorithm.** You need the two heaviest at every step, and "
            "the result of a smash goes straight back into the pile — which is exactly the "
            "operation a heap is for. Re-sorting after each smash would be O(n² log n)."
        ),
        hint=(
            "Python's heapq is a *min*-heap, so store the weights negated and negate again on "
            "the way out. Only push the remainder back when it isn't zero."
        ),
        approach=(
            "1) Heapify the negated weights. 2) While two or more remain: pop the two heaviest; "
            "if they differ, push back the difference. 3) Return what's left, or 0. "
            "O(n log n)."
        ),
        solution=(
            "import heapq\n\n"
            "def lastStoneWeight(stones):\n"
            "    heap = [-w for w in stones]\n"
            "    heapq.heapify(heap)\n"
            "    while len(heap) > 1:\n"
            "        first = -heapq.heappop(heap)\n"
            "        second = -heapq.heappop(heap)\n"
            "        if first != second:\n"
            "            heapq.heappush(heap, -(first - second))\n"
            "    return -heap[0] if heap else 0"
        ),
        tests=[
            example([[2, 7, 4, 1, 8, 1]], 1),
            example([[1]], 1),
            hidden("no stones", [[]], 0),
            hidden("two equal stones cancel", [[2, 2]], 0),
            hidden("three stones", [[3, 7, 2]], 2),
            hidden("two pairs, one survivor", [[10, 4, 2, 10]], 2),
            hidden("the smaller is destroyed", [[1, 3]], 2),
        ],
    ),
    problem(
        zone=ZONE,
        slug="k-closest-points-to-origin",
        title="K Closest Points to Origin",
        difficulty="medium",
        prompt=(
            "Marbles are scattered across the playmat at [x, y]. Return the k nearest to the "
            "middle, in any order. No two of them are ever the same distance away."
        ),
        example_input="points = [[1, 3], [-2, 2]], k = 1",
        example_output="[[-2, 2]]",
        entrypoint="kClosest",
        signature=sig("matrix<int>", points="matrix<int>", k="int"),
        # Order among the k winners is free; the winners themselves are not.
        compare_mode="unordered",
        explainer=(
            "**Skip the square root.** Comparing x² + y² orders the marbles exactly the same "
            "way comparing √(x² + y²) does, and stays in whole numbers — so the distance never "
            "needs computing properly at all."
        ),
        hint=(
            "Same shape as Kth Largest, one dimension up: sort by the squared distance and take "
            "the front k, or keep a heap of size k if you'd rather not sort everything."
        ),
        approach=(
            "1) Sort points by x*x + y*y. 2) Return the first k. O(n log n) — or O(n log k) "
            "with a max-heap capped at k."
        ),
        solution=(
            "def kClosest(points, k):\n"
            "    return sorted(points, key=lambda p: p[0] * p[0] + p[1] * p[1])[:k]"
        ),
        tests=[
            example([[[1, 3], [-2, 2]], 1], [[-2, 2]]),
            example([[[3, 3], [5, -1], [-2, 4]], 2], [[3, 3], [-2, 4]]),
            hidden("the middle itself", [[[0, 0]], 1], [[0, 0]]),
            hidden("on the axes", [[[1, 0], [0, 2], [3, 3]], 2], [[1, 0], [0, 2]]),
            hidden("negative coordinates", [[[-5, 4], [-6, -5], [4, 6]], 1], [[-5, 4]]),
            hidden("k takes every marble", [[[1, 1], [2, 2], [3, 3]], 3],
                   [[1, 1], [2, 2], [3, 3]]),
            hidden("far and near", [[[2, 2], [-1, 0]], 1], [[-1, 0]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="task-scheduler",
        title="Task Scheduler",
        difficulty="medium",
        prompt=(
            "Sprocket has a list of chores and needs n idle turns between two goes at the *same* "
            "chore. Different chores can follow each other freely. Return the fewest turns "
            "needed to finish everything, counting the idling."
        ),
        example_input='tasks = ["A", "A", "A", "B", "B", "B"], n = 2',
        example_output="8",
        entrypoint="leastInterval",
        signature=sig("int", tasks="list<string>", n="int"),
        explainer=(
            "**The commonest chore sets the skeleton.** If a chore appears m times it carves "
            "the schedule into m - 1 gaps of n + 1 turns, plus a final run. Every other chore "
            "either slots into that idling for free, or the schedule is so crowded there's no "
            "idling at all — in which case the answer is simply the number of chores."
        ),
        hint=(
            "Take the max of the two: `(m - 1) * (n + 1) + (how many chores tie at m)` and "
            "`len(tasks)`. The second is what covers the crowded case."
        ),
        approach=(
            "1) counts = Counter(tasks); m = the largest count. 2) ties = how many chores hit "
            "m. 3) Return max(len(tasks), (m - 1) * (n + 1) + ties). O(n) time."
        ),
        solution=(
            "from collections import Counter\n\n"
            "def leastInterval(tasks, n):\n"
            "    if not tasks:\n"
            "        return 0\n"
            "    counts = Counter(tasks)\n"
            "    most = max(counts.values())\n"
            "    ties = sum(1 for c in counts.values() if c == most)\n"
            "    return max(len(tasks), (most - 1) * (n + 1) + ties)"
        ),
        tests=[
            example([["A", "A", "A", "B", "B", "B"], 2], 8),
            example([["A", "A", "A", "B", "B", "B"], 0], 6),
            hidden("no chores", [[], 2], 0),
            hidden("one chore never waits", [["A"], 5], 1),
            hidden("all different", [["A", "B", "C", "D"], 1], 4),
            hidden("a short tail", [["A", "A", "B"], 2], 4),
            hidden("plenty of filler",
                   [["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2], 16),
        ],
    ),
    problem(
        zone=ZONE,
        slug="minimum-cost-to-connect-sticks",
        title="Minimum Cost to Connect Sticks",
        difficulty="medium",
        prompt=(
            "Glue the toy sticks into one long stick. Joining two sticks costs the sum of their "
            "lengths and gives you a stick that long. Return the cheapest total cost."
        ),
        example_input="sticks = [2, 4, 3]",
        example_output="14",
        entrypoint="connectSticks",
        signature=sig("int", sticks="list<int>"),
        explainer=(
            "**Every join a stick survives, you pay for it again.** So the sticks you glue "
            "first are charged the most times — which means always reaching for the two "
            "shortest. That's a min-heap, and the greedy choice is provably optimal here."
        ),
        hint=(
            "One stick costs nothing: there's nothing to join it to. Push the sum back onto the "
            "heap after each join, because it's a stick like any other now."
        ),
        approach=(
            "1) Heapify sticks. 2) While two or more remain: pop the two shortest, add their "
            "sum to the total, push the sum back. 3) Return the total. O(n log n)."
        ),
        solution=(
            "import heapq\n\n"
            "def connectSticks(sticks):\n"
            "    heap = list(sticks)\n"
            "    heapq.heapify(heap)\n"
            "    total = 0\n"
            "    while len(heap) > 1:\n"
            "        first = heapq.heappop(heap)\n"
            "        second = heapq.heappop(heap)\n"
            "        total += first + second\n"
            "        heapq.heappush(heap, first + second)\n"
            "    return total"
        ),
        tests=[
            example([[2, 4, 3]], 14),
            example([[1, 8, 3, 5]], 30),
            hidden("one stick, nothing to join", [[5]], 0),
            hidden("no sticks at all", [[]], 0),
            hidden("two sticks, one join", [[1, 1]], 2),
            hidden("greedy order matters", [[1, 2, 3, 4, 5]], 33),
            hidden("all the same length", [[10, 10, 10, 10]], 80),
        ],
    ),
]

"""Puzzle Box — 1-D Dynamic Programming.

Solve once, reuse. Every problem here is a line of sub-answers where each one is
built from the few before it, and the whole skill is noticing what "the answer
at position i" should even mean — get that definition right and the recurrence
usually writes itself.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "puzzle-box"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="climbing-stairs",
        title="Climbing Stairs",
        difficulty="easy",
        prompt=(
            "Sprocket climbs the shelf one or two steps at a time. How many distinct ways can "
            "the little toy reach step n?"
        ),
        example_input="n = 5",
        example_output="8",
        entrypoint="climbStairs",
        signature=sig("int", n="int"),
        explainer=(
            "**Solve once, reuse.** Ways to reach step n = ways to reach n-1 plus ways to reach "
            "n-2. It's Fibonacci wearing a shelf costume."
        ),
        hint="You only ever need the last two answers — no array required.",
        approach="1) a, b = 1, 1. 2) Repeat n-1 times: a, b = b, a + b. 3) Return b.",
        solution=(
            "def climbStairs(n):\n"
            "    a, b = 1, 1\n"
            "    for _ in range(n - 1):\n"
            "        a, b = b, a + b\n"
            "    return b"
        ),
        tests=[
            example([5], 8),
            example([2], 2),
            hidden("one step", [1], 1),
            hidden("three steps", [3], 3),
            hidden("ten steps", [10], 89),
            hidden("twenty steps", [20], 10946),
            hidden("tall shelf — naive recursion will crawl", [45], 1836311903),
        ],
    ),
    problem(
        zone=ZONE,
        slug="min-cost-climbing-stairs",
        title="Min Cost Climbing Stairs",
        difficulty="easy",
        prompt=(
            "Each step on the shelf costs a few play-coins to stand on. You may start on step 0 "
            "or step 1, and from any step you climb one or two. Return the cheapest way to get "
            "past the top."
        ),
        example_input="cost = [10, 15, 20]",
        example_output="15",
        entrypoint="minCostClimbingStairs",
        signature=sig("int", cost="list<int>"),
        explainer=(
            "**Price the landing, not the step.** Let cheapest(i) be what it costs to *reach* "
            "step i — you arrive from either i-1 or i-2, and you pay for whichever you came "
            "from. The top is one past the last step, which is why the answer isn't in the "
            "array."
        ),
        hint=(
            "Reaching step 0 and step 1 are both free — that's what 'you may start on either' "
            "means. Everything after that is min of the two ways in."
        ),
        approach=(
            "1) two_back = one_back = 0. 2) For i in 2..len(cost): the new value is "
            "min(one_back + cost[i-1], two_back + cost[i-2]). 3) Return the last one. "
            "O(n) time, O(1) space."
        ),
        solution=(
            "def minCostClimbingStairs(cost):\n"
            "    two_back = one_back = 0\n"
            "    for i in range(2, len(cost) + 1):\n"
            "        two_back, one_back = one_back, min(\n"
            "            one_back + cost[i - 1], two_back + cost[i - 2]\n"
            "        )\n"
            "    return one_back"
        ),
        tests=[
            example([[10, 15, 20]], 15),
            example([[1, 100, 1, 1, 1, 100, 1, 1, 100, 1]], 6),
            hidden("two free steps", [[0, 0]], 0),
            hidden("start on the cheaper one", [[1, 2]], 1),
            hidden("skip the expensive first step", [[10, 1]], 1),
            hidden("all the same price", [[5, 5, 5]], 5),
            hidden("three steps, skip the middle", [[1, 100, 1]], 2),
        ],
    ),
    problem(
        zone=ZONE,
        slug="house-robber",
        title="House Robber",
        difficulty="medium",
        prompt=(
            "A row of dolls' houses each hold some play-coins, but robbing two houses next door "
            "to each other sets off the toy alarm. Return the most you can take."
        ),
        example_input="nums = [2, 7, 9, 3, 1]",
        example_output="12",
        entrypoint="rob",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**Two running totals.** At each house you either take it — adding it to the best "
            "you had two houses back — or skip it and keep the best you had one house back. "
            "The bigger of those is the new best."
        ),
        hint=(
            "You never need an array. Carry the best-including-this-house and "
            "best-up-to-the-last-house forwards and let them leapfrog."
        ),
        approach=(
            "1) prev, cur = 0, 0. 2) For n in nums: prev, cur = cur, max(cur, prev + n). "
            "3) Return cur. O(n) time, O(1) space."
        ),
        solution=(
            "def rob(nums):\n"
            "    prev = cur = 0\n"
            "    for n in nums:\n"
            "        prev, cur = cur, max(cur, prev + n)\n"
            "    return cur"
        ),
        tests=[
            example([[1, 2, 3, 1]], 4),
            example([[2, 7, 9, 3, 1]], 12),
            hidden("no houses", [[]], 0),
            hidden("one house", [[5]], 5),
            hidden("two houses, take the richer", [[1, 2]], 2),
            hidden("greedy would take the middle", [[2, 1, 1, 2]], 4),
            hidden("both ends", [[100, 1, 1, 100]], 200),
        ],
    ),
    problem(
        zone=ZONE,
        slug="longest-increasing-subsequence",
        title="Longest Increasing Subsequence",
        difficulty="medium",
        prompt=(
            "Pick blocks out of the row, left to right, so each is strictly taller than the "
            "last. You may skip as many as you like. Return the length of the longest run you "
            "can make."
        ),
        example_input="nums = [10, 9, 2, 5, 3, 7, 101, 18]",
        example_output="4",
        entrypoint="lengthOfLIS",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**Keep the smallest tail for each length.** The O(n²) version asks 'longest run "
            "ending here' at every block. The faster one keeps a list where entry i is the "
            "smallest possible last block of a run of length i + 1 — that list is sorted, so "
            "each block is placed by binary search."
        ),
        hint=(
            "That list is not itself a valid run — don't try to read the answer off it. Only "
            "its *length* is the answer."
        ),
        approach=(
            "1) tails = []. 2) For each n: binary search for the first tail >= n. 3) Replace it, "
            "or append if there is none. 4) Return len(tails). O(n log n)."
        ),
        solution=(
            "import bisect\n\n"
            "def lengthOfLIS(nums):\n"
            "    tails = []\n"
            "    for n in nums:\n"
            "        i = bisect.bisect_left(tails, n)\n"
            "        if i == len(tails):\n"
            "            tails.append(n)\n"
            "        else:\n"
            "            tails[i] = n\n"
            "    return len(tails)"
        ),
        tests=[
            example([[10, 9, 2, 5, 3, 7, 101, 18]], 4),
            example([[0, 1, 0, 3, 2, 3]], 4),
            hidden("no blocks", [[]], 0),
            hidden("one block", [[1]], 1),
            hidden("every block the same height", [[7, 7, 7, 7]], 1),
            hidden("strictly downhill", [[4, 3, 2, 1]], 1),
            hidden("a dip that doesn't help", [[1, 3, 6, 7, 9, 4, 10, 5, 6]], 6),
        ],
    ),
    problem(
        zone=ZONE,
        slug="coin-change",
        title="Coin Change",
        difficulty="hard",
        prompt=(
            "Pay for a gumball with the fewest play-coins possible. Given coin denominations and "
            "an amount, return the minimum number of coins, or -1 if it can't be paid."
        ),
        example_input="coins = [1, 5, 6, 9], amount = 11",
        example_output="2",
        entrypoint="coinChange",
        signature=sig("int", coins="list<int>", amount="int"),
        explainer=(
            "**Build up from zero.** Best[a] is the cheapest way to make amount a. Every coin "
            "gives a candidate: 1 + Best[a - coin]. Greedy fails here — the table doesn't."
        ),
        hint=(
            "Seed dp[0] = 0 and fill the rest with infinity, then take the min over every coin."
        ),
        approach=(
            "1) dp = [0] + [inf] * amount. 2) For a in 1..amount: for coin in coins, if "
            "coin <= a: dp[a] = min(dp[a], dp[a-coin] + 1). 3) Return dp[amount] if finite else -1."
        ),
        solution=(
            "def coinChange(coins, amount):\n"
            "    dp = [0] + [float('inf')] * amount\n"
            "    for a in range(1, amount + 1):\n"
            "        for coin in coins:\n"
            "            if coin <= a:\n"
            "                dp[a] = min(dp[a], dp[a - coin] + 1)\n"
            "    return -1 if dp[amount] == float('inf') else dp[amount]"
        ),
        tests=[
            example([[1, 5, 6, 9], 11], 2),
            example([[2], 3], -1),
            hidden("nothing to pay", [[1], 0], 0),
            hidden("standard change", [[1, 2, 5], 11], 3),
            hidden("greedy would overpay", [[2, 5, 10, 1], 27], 4),
            hidden("awkward denominations", [[186, 419, 83, 408], 6249], 20),
            hidden("cannot be paid", [[5], 3], -1),
        ],
    ),
]

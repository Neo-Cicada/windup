"""Quilt Squares — 2-D Dynamic Programming.

A grid of stitched-together answers. One dimension per thing that varies: how
far through each of two strings you are, or how much of a total is left and which
coins you're still allowed. Once the grid is the right shape, each square is a
one-line question about its neighbours.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "quilt-squares"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="unique-paths",
        title="Unique Paths",
        difficulty="medium",
        prompt=(
            "A wind-up mouse starts on the top-left square of an m × n quilt and must reach the "
            "bottom-right, moving only right or down. How many different routes are there?"
        ),
        example_input="m = 3, n = 7",
        example_output="28",
        entrypoint="uniquePaths",
        signature=sig("int", m="int", n="int"),
        explainer=(
            "**Every square is reached from above or from the left.** So the number of routes "
            "to a square is the sum of those two — and the top row and left column are all 1, "
            "since there's only one way along an edge."
        ),
        hint=(
            "You only ever read the row above, so one row of numbers is enough: update it left "
            "to right, in place, once per row."
        ),
        approach=(
            "1) row = [1] * n. 2) Repeat m - 1 times: for j in 1..n-1, row[j] += row[j-1]. "
            "3) Return row[-1]. O(m·n) time, O(n) space."
        ),
        solution=(
            "def uniquePaths(m, n):\n"
            "    row = [1] * n\n"
            "    for _ in range(m - 1):\n"
            "        for j in range(1, n):\n"
            "            row[j] += row[j - 1]\n"
            "    return row[-1]"
        ),
        tests=[
            example([3, 7], 28),
            example([3, 2], 3),
            hidden("a single square", [1, 1], 1),
            hidden("one row across", [1, 10], 1),
            hidden("one column down", [10, 1], 1),
            hidden("a small square quilt", [3, 3], 6),
            hidden("the same quilt turned sideways", [7, 3], 28),
        ],
    ),
    problem(
        zone=ZONE,
        slug="longest-common-subsequence",
        title="Longest Common Subsequence",
        difficulty="medium",
        prompt=(
            "Two ribbons have letters sewn along them. Find the longest sequence of letters "
            "appearing in both, in the same order — though not necessarily next to each other. "
            "Return its length."
        ),
        example_input='text1 = "abcde", text2 = "ace"',
        example_output="3",
        entrypoint="longestCommonSubsequence",
        signature=sig("int", text1="string", text2="string"),
        explainer=(
            "**One square per pair of positions.** If the two letters match, that pair is worth "
            "1 plus whatever the rest is worth. If they don't, one of the two letters is "
            "useless — so try skipping each and keep the better."
        ),
        hint=(
            "Give the grid an extra row and column of zeroes for 'one of the ribbons has run "
            "out'. That removes every bounds check from the body of the loop."
        ),
        approach=(
            "1) dp is (len1 + 1) × (len2 + 1) of zeroes. 2) Fill from the bottom-right "
            "backwards: match → dp[i+1][j+1] + 1, otherwise max(dp[i+1][j], dp[i][j+1]). "
            "3) Return dp[0][0]. O(len1 × len2)."
        ),
        solution=(
            "def longestCommonSubsequence(text1, text2):\n"
            "    dp = [[0] * (len(text2) + 1) for _ in range(len(text1) + 1)]\n"
            "    for i in range(len(text1) - 1, -1, -1):\n"
            "        for j in range(len(text2) - 1, -1, -1):\n"
            "            if text1[i] == text2[j]:\n"
            "                dp[i][j] = dp[i + 1][j + 1] + 1\n"
            "            else:\n"
            "                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])\n"
            "    return dp[0][0]"
        ),
        tests=[
            example(["abcde", "ace"], 3),
            example(["abc", "def"], 0),
            hidden("identical ribbons", ["abc", "abc"], 3),
            hidden("two blank ribbons", ["", ""], 0),
            hidden("one blank ribbon", ["a", ""], 0),
            hidden("only one letter in common", ["bl", "yby"], 1),
            hidden("a long pair sharing almost nothing", ["bsbininm", "jmjkbkjkv"], 1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="coin-change-ii",
        title="Coin Change II",
        difficulty="medium",
        prompt=(
            "Given coin values and an amount, count how many different combinations make the "
            "amount. Coins can be reused, and two combinations using the same coins in a "
            "different order are the same combination."
        ),
        example_input="amount = 5, coins = [1, 2, 5]",
        example_output="4",
        entrypoint="change",
        signature=sig("int", amount="int", coins="list<int>"),
        explainer=(
            "**Put the coins on the outside.** Looping over coins first and amounts second "
            "means each combination is counted once, in coin order. Swapping the two loops "
            "counts *orderings* instead, which is a different — and much larger — answer."
        ),
        hint=(
            "There is exactly one way to make 0: use nothing. Seeding dp[0] = 1 is what makes "
            "every other entry come out right."
        ),
        approach=(
            "1) dp = [1] + [0] * amount. 2) For each coin, for a from coin to amount: dp[a] += "
            "dp[a - coin]. 3) Return dp[amount]. O(coins × amount) time, O(amount) space."
        ),
        solution=(
            "def change(amount, coins):\n"
            "    dp = [0] * (amount + 1)\n"
            "    dp[0] = 1\n"
            "    for coin in coins:\n"
            "        for a in range(coin, amount + 1):\n"
            "            dp[a] += dp[a - coin]\n"
            "    return dp[amount]"
        ),
        tests=[
            example([5, [1, 2, 5]], 4),
            example([3, [2]], 0),
            hidden("one coin, exactly", [10, [10]], 1),
            hidden("nothing to make", [0, [1]], 1),
            hidden("nothing to make, and no coins", [0, []], 1),
            hidden("four ways", [4, [1, 2, 3]], 4),
            hidden("a great many ways", [500, [3, 5, 7, 8, 9, 10, 11]], 35502874),
        ],
    ),
    problem(
        zone=ZONE,
        slug="target-sum",
        title="Target Sum",
        difficulty="medium",
        prompt=(
            "Put a + or a - in front of every number on the row of cards, then add them up. "
            "Count how many ways there are to land exactly on the target."
        ),
        example_input="nums = [1, 1, 1, 1, 1], target = 3",
        example_output="5",
        entrypoint="findTargetSumWays",
        signature=sig("int", nums="list<int>", target="int"),
        explainer=(
            "**Count the running totals, not the sign patterns.** There are 2ⁿ patterns but far "
            "fewer distinct totals, so carry a map from total to how many ways reach it. Each "
            "card splits every entry in two — once plus, once minus."
        ),
        hint=(
            "Start from {0: 1}: before any card, one way to have a total of zero. A zero on a "
            "card is worth noticing — it splits an entry into two ways with the same total."
        ),
        approach=(
            "1) ways = {0: 1}. 2) For each card: build a fresh map, adding the count at each "
            "total to total + n and total - n. 3) Return ways.get(target, 0). O(n × distinct "
            "totals)."
        ),
        solution=(
            "from collections import defaultdict\n\n"
            "def findTargetSumWays(nums, target):\n"
            "    ways = {0: 1}\n"
            "    for n in nums:\n"
            "        nxt = defaultdict(int)\n"
            "        for total, count in ways.items():\n"
            "            nxt[total + n] += count\n"
            "            nxt[total - n] += count\n"
            "        ways = nxt\n"
            "    return ways.get(target, 0)"
        ),
        tests=[
            example([[1, 1, 1, 1, 1], 3], 5),
            example([[1], 1], 1),
            hidden("out of reach", [[1], 2], 0),
            hidden("no cards, and nothing to make", [[], 0], 1),
            hidden("cancelling out", [[1, 2, 1], 0], 2),
            hidden("zeroes count twice each", [[0, 0], 0], 4),
            hidden("exactly one arrangement works", [[2, 3, 4], 3], 1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="edit-distance",
        title="Edit Distance",
        difficulty="hard",
        prompt=(
            "Turn one stitched word into the other using as few edits as possible, where an "
            "edit inserts a letter, deletes one, or changes one. Return how many edits it takes."
        ),
        example_input='word1 = "horse", word2 = "ros"',
        example_output="3",
        entrypoint="minDistance",
        signature=sig("int", word1="string", word2="string"),
        explainer=(
            "**Three neighbours, one square.** If the last letters match, there's nothing to "
            "pay — the answer is the square up and to the left. If they don't, it's one edit "
            "plus the best of the three squares around it: delete, insert, or substitute."
        ),
        hint=(
            "The edges of the grid are not zeroes here. Turning a word of length i into an "
            "empty one costs exactly i deletions, so seed row 0 and column 0 with 0, 1, 2, …"
        ),
        approach=(
            "1) dp[i][0] = i and dp[0][j] = j. 2) Fill each square: equal letters → dp[i-1] "
            "[j-1]; otherwise 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]). 3) Return the "
            "bottom-right. O(len1 × len2) — Levenshtein distance."
        ),
        solution=(
            "def minDistance(word1, word2):\n"
            "    rows, cols = len(word1), len(word2)\n"
            "    dp = [[0] * (cols + 1) for _ in range(rows + 1)]\n"
            "    for i in range(rows + 1):\n"
            "        dp[i][0] = i\n"
            "    for j in range(cols + 1):\n"
            "        dp[0][j] = j\n"
            "    for i in range(1, rows + 1):\n"
            "        for j in range(1, cols + 1):\n"
            "            if word1[i - 1] == word2[j - 1]:\n"
            "                dp[i][j] = dp[i - 1][j - 1]\n"
            "            else:\n"
            "                dp[i][j] = 1 + min(\n"
            "                    dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]\n"
            "                )\n"
            "    return dp[rows][cols]"
        ),
        tests=[
            example(["horse", "ros"], 3),
            example(["intention", "execution"], 5),
            hidden("two blank words", ["", ""], 0),
            hidden("delete the only letter", ["a", ""], 1),
            hidden("insert three letters", ["", "abc"], 3),
            hidden("already identical", ["abc", "abc"], 0),
            hidden("the textbook pair", ["kitten", "sitting"], 3),
        ],
    ),
]

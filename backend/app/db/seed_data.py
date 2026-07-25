"""Catalogue content for the academy.

Zones and badges are lifted from the frontend's `components/academy/data.ts` so the
seeded API returns exactly what the UI was designed against.
"""

ZONES: list[dict] = [
    {
        "slug": "building-blocks",
        "name": "Building Blocks",
        "pattern": "Arrays & Strings",
        "color": "#6FBF73",
        "blurb": "Snap-together cubes",
    },
    {
        "slug": "marble-run",
        "name": "Marble Run",
        "pattern": "Linked Lists",
        "color": "#4FB0E5",
        "blurb": "Chutes & pointers",
    },
    {
        "slug": "board-game",
        "name": "Board Game",
        "pattern": "Graphs & Trees",
        "color": "#EF5B54",
        "blurb": "Roll, branch, explore",
    },
    {
        "slug": "toy-kitchen",
        "name": "Toy Kitchen",
        "pattern": "SQL",
        "color": "#F7C948",
        "blurb": "Recipes & queries",
    },
    {
        "slug": "stacking-cups",
        "name": "Stacking Cups",
        "pattern": "Stacks & Queues",
        "color": "#E08A3C",
        "blurb": "Last in, first out",
    },
    {
        "slug": "puzzle-box",
        "name": "Puzzle Box",
        "pattern": "Dynamic Programming",
        "color": "#8B6FD6",
        "blurb": "Solve once, reuse",
    },
]

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

PROBLEMS: list[dict] = [
    {
        "zone": "building-blocks",
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Two blocks in the bin snap together to make exactly the height Sprocket needs. "
            "Given a list of block heights and a target, return the indices of the two blocks "
            "that add up to it."
        ),
        "example_input": "nums = [2, 7, 11, 15], target = 9",
        "example_output": "[0, 1]",
        "starter_code": "def twoSum(nums, target):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Complement lookup.** Walk the bin once. For each block, ask 'which block would "
            "finish this tower?' — that's target - height. Keep every block you've seen in a "
            "dictionary so the question is answered in O(1)."
        ),
        "hint": (
            "You don't need two loops. Store each height you've already seen in a dict keyed by "
            "height, valued by index, and check for the complement *before* you insert."
        ),
        "approach": (
            "1) seen = {}. 2) For i, n in enumerate(nums): 3) need = target - n. "
            "4) If need in seen: return [seen[need], i]. 5) seen[n] = i. "
            "One pass, O(n) time, O(n) space."
        ),
        "solution": (
            "def twoSum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        need = target - n\n"
            "        if need in seen:\n"
            "            return [seen[need], i]\n"
            "        seen[n] = i\n"
            "    return []"
        ),
        "xp_reward": 50,
    },
    {
        "zone": "building-blocks",
        "slug": "valid-anagram",
        "title": "Valid Anagram",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Two alphabet-block words got shuffled in the toy chest. Decide whether one is a "
            "rearrangement of the other."
        ),
        "example_input": 's = "anagram", t = "nagaram"',
        "example_output": "true",
        "starter_code": "def isAnagram(s, t):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Count the blocks.** Anagrams use the same letters the same number of times, so "
            "compare letter counts rather than order."
        ),
        "hint": "Different lengths can never be anagrams — bail out early, then count with a dict.",
        "approach": (
            "1) If len(s) != len(t): return False. 2) Tally each letter of s in a Counter. "
            "3) Decrement for each letter of t; if any count dips below zero, return False. "
            "4) Return True. O(n) time, O(1) space for a fixed alphabet."
        ),
        "solution": (
            "from collections import Counter\n\n"
            "def isAnagram(s, t):\n"
            "    return len(s) == len(t) and Counter(s) == Counter(t)"
        ),
        "xp_reward": 50,
    },
    {
        "zone": "marble-run",
        "slug": "reverse-linked-list",
        "title": "Reverse Linked List",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "Sprocket's marble chute got tangled backwards! Given the head of a singly linked "
            "marble chute, reverse the run so the last marble drops first. Return the new head."
        ),
        "example_input": "head = [1, 2, 3, 4, 5]",
        "example_output": "[5, 4, 3, 2, 1]",
        "starter_code": (
            "def reverseList(head):\n"
            "    prev = None\n"
            "    while head:\n"
            "        # your turn, little toy…\n"
            "        pass"
        ),
        "explainer": (
            "**Two-pointer walk.** Keep a *prev* marble and a *current* marble. Each step, flip "
            "current's arrow to point at prev, then shuffle both forward one slot. When current "
            "runs off the end, prev is your new head."
        ),
        "hint": (
            "You only need one pass and O(1) extra space. Store head.next in a temp before you "
            "flip the arrow, or you'll lose the rest of the chute."
        ),
        "approach": (
            "1) prev = None. 2) While head: save nxt = head.next. 3) head.next = prev. "
            "4) prev = head. 5) head = nxt. 6) Return prev. That's the whole marble flip — "
            "O(n) time, O(1) space."
        ),
        "solution": (
            "def reverseList(head):\n"
            "    prev = None\n"
            "    while head:\n"
            "        nxt = head.next\n"
            "        head.next = prev\n"
            "        prev = head\n"
            "        head = nxt\n"
            "    return prev"
        ),
        "xp_reward": 60,
    },
    {
        "zone": "marble-run",
        "slug": "linked-list-cycle",
        "title": "Linked List Cycle",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "A marble keeps rolling past the same bend forever. Determine whether the chute "
            "loops back on itself."
        ),
        "example_input": "head = [3, 2, 0, -4], tail connects to index 1",
        "example_output": "true",
        "starter_code": "def hasCycle(head):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Two marbles, two speeds.** Roll one marble one slot at a time and another two at "
            "a time. On a looping track the fast marble laps the slow one; on a straight track "
            "it falls off the end."
        ),
        "hint": (
            "Floyd's tortoise and hare. Stop as soon as slow is fast, or fast runs out of track."
        ),
        "approach": (
            "1) slow = fast = head. 2) While fast and fast.next: slow = slow.next, "
            "fast = fast.next.next. 3) If slow is fast: return True. 4) Return False. "
            "O(n) time, O(1) space."
        ),
        "solution": (
            "def hasCycle(head):\n"
            "    slow = fast = head\n"
            "    while fast and fast.next:\n"
            "        slow = slow.next\n"
            "        fast = fast.next.next\n"
            "        if slow is fast:\n"
            "            return True\n"
            "    return False"
        ),
        "xp_reward": 60,
    },
    {
        "zone": "board-game",
        "slug": "number-of-islands",
        "title": "Number of Islands",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "The board game's map has patches of land ('1') in a sea of water ('0'). Count how "
            "many separate islands the playing pieces can land on."
        ),
        "example_input": 'grid = [["1","1","0"],["1","0","0"],["0","0","1"]]',
        "example_output": "2",
        "starter_code": "def numIslands(grid):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Flood fill.** Every time you find un-visited land, that's a brand-new island — "
            "then sink the whole connected patch so you never count it twice."
        ),
        "hint": (
            "Sink visited land by writing '0' back into the grid; "
            "that's your visited set, for free."
        ),
        "approach": (
            "1) Scan every cell. 2) When you hit '1', increment the count. 3) DFS/BFS out from "
            "that cell, flipping every connected '1' to '0'. 4) Continue the scan. "
            "O(rows x cols) time."
        ),
        "solution": (
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
        "xp_reward": 60,
    },
    {
        "zone": "board-game",
        "slug": "max-depth-binary-tree",
        "title": "Maximum Depth of Binary Tree",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": "How many branches tall is the game tree? Return its maximum depth.",
        "example_input": "root = [3, 9, 20, null, null, 15, 7]",
        "example_output": "3",
        "starter_code": "def maxDepth(root):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Ask the branches.** A tree's depth is 1 + the deeper of its two children. "
            "Recursion writes itself."
        ),
        "hint": "The base case is an empty branch — that's depth 0.",
        "approach": "1) If not root: return 0. 2) Return 1 + max(maxDepth(left), maxDepth(right)).",
        "solution": (
            "def maxDepth(root):\n"
            "    if not root:\n"
            "        return 0\n"
            "    return 1 + max(maxDepth(root.left), maxDepth(root.right))"
        ),
        "xp_reward": 50,
    },
    {
        "zone": "stacking-cups",
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Stack the cups so every one that goes down comes back up in order. Decide whether "
            "a string of brackets is balanced."
        ),
        "example_input": 's = "{[()]}"',
        "example_output": "true",
        "starter_code": "def isValid(s):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Last in, first out.** Push every opening cup. On a closing cup, the top of the "
            "stack must be its match — otherwise the tower topples."
        ),
        "hint": "A leftover stack at the end means unmatched cups. Don't forget to check for that.",
        "approach": (
            "1) pairs = {')':'(', ']':'[', '}':'{'}. 2) Push openers. 3) On a closer, pop and "
            "compare. 4) Return not stack."
        ),
        "solution": (
            "def isValid(s):\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    stack = []\n"
            "    for ch in s:\n"
            "        if ch in pairs:\n"
            "            if not stack or stack.pop() != pairs[ch]:\n"
            "                return False\n"
            "        else:\n"
            "            stack.append(ch)\n"
            "    return not stack"
        ),
        "xp_reward": 50,
    },
    {
        "zone": "puzzle-box",
        "slug": "climbing-stairs",
        "title": "Climbing Stairs",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Sprocket climbs the shelf one or two steps at a time. How many distinct ways can "
            "the little toy reach step n?"
        ),
        "example_input": "n = 5",
        "example_output": "8",
        "starter_code": "def climbStairs(n):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Solve once, reuse.** Ways to reach step n = ways to reach n-1 plus ways to reach "
            "n-2. It's Fibonacci wearing a shelf costume."
        ),
        "hint": "You only ever need the last two answers — no array required.",
        "approach": "1) a, b = 1, 1. 2) Repeat n-1 times: a, b = b, a + b. 3) Return b.",
        "solution": (
            "def climbStairs(n):\n"
            "    a, b = 1, 1\n"
            "    for _ in range(n - 1):\n"
            "        a, b = b, a + b\n"
            "    return b"
        ),
        "xp_reward": 50,
    },
    {
        "zone": "puzzle-box",
        "slug": "coin-change",
        "title": "Coin Change",
        "difficulty": "hard",
        "weight_label": "HEAVY WEIGHT",
        "prompt": (
            "Pay for a gumball with the fewest play-coins possible. Given coin denominations and "
            "an amount, return the minimum number of coins, or -1 if it can't be paid."
        ),
        "example_input": "coins = [1, 5, 6, 9], amount = 11",
        "example_output": "2",
        "starter_code": "def coinChange(coins, amount):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Build up from zero.** Best[a] is the cheapest way to make amount a. Every coin "
            "gives a candidate: 1 + Best[a - coin]. Greedy fails here — the table doesn't."
        ),
        "hint": (
            "Seed dp[0] = 0 and fill the rest with infinity, then take the min over every coin."
        ),
        "approach": (
            "1) dp = [0] + [inf] * amount. 2) For a in 1..amount: for coin in coins, if "
            "coin <= a: dp[a] = min(dp[a], dp[a-coin] + 1). 3) Return dp[amount] if finite else -1."
        ),
        "solution": (
            "def coinChange(coins, amount):\n"
            "    dp = [0] + [float('inf')] * amount\n"
            "    for a in range(1, amount + 1):\n"
            "        for coin in coins:\n"
            "            if coin <= a:\n"
            "                dp[a] = min(dp[a], dp[a - coin] + 1)\n"
            "    return -1 if dp[amount] == float('inf') else dp[amount]"
        ),
        "xp_reward": 80,
    },
    {
        "zone": "toy-kitchen",
        "slug": "second-highest-salary",
        "title": "Second Highest Recipe Rating",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "The toy kitchen keeps a table of recipe ratings. Write a query returning the second "
            "highest distinct rating, or NULL when there isn't one."
        ),
        "example_input": "ratings = [100, 200, 300]",
        "example_output": "200",
        "language": "sql",
        "starter_code": "SELECT\n  -- your turn, little toy…\n;",
        "explainer": (
            "**Skip the top, take the next.** Order distinct values descending, then offset by "
            "one. A subquery keeps NULL as the answer when the row doesn't exist."
        ),
        "hint": "DISTINCT matters — repeated top ratings would otherwise hide the runner-up.",
        "approach": (
            "1) SELECT DISTINCT rating ORDER BY rating DESC LIMIT 1 OFFSET 1. "
            "2) Wrap it in an outer SELECT so an empty result becomes NULL."
        ),
        "solution": (
            "SELECT (\n"
            "  SELECT DISTINCT rating\n"
            "  FROM recipes\n"
            "  ORDER BY rating DESC\n"
            "  LIMIT 1 OFFSET 1\n"
            ") AS second_highest;"
        ),
        "xp_reward": 60,
    },
]

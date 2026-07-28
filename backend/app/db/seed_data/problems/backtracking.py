"""Maze Toy — Backtracking.

Try a path, and if it doesn't work out, walk back to the last fork and try the
other way. The shape never changes: choose, recurse, un-choose. What differs is
only what counts as a choice and when you know to stop.

Most answers here are collections where the order is meaningless, so these
problems grade with `unordered_deep` — see `app/judge/grade.py`.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "maze-toy"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="subsets",
        title="Subsets",
        difficulty="medium",
        prompt=(
            "From a handful of distinct blocks, list every possible selection — including "
            "taking none of them and taking all of them. Any order will do."
        ),
        example_input="nums = [1, 2, 3]",
        example_output="[[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]",
        entrypoint="subsets",
        signature=sig("matrix<int>", nums="list<int>"),
        compare_mode="unordered_deep",
        explainer=(
            "**Each block is one yes-or-no.** Walk the blocks in order; at each one, recurse "
            "twice — once having taken it, once having left it. The leaves of that little tree "
            "are exactly the 2ⁿ selections."
        ),
        hint=(
            "Append a *copy* of the current selection when you reach the end, not the list "
            "itself — otherwise every answer ends up pointing at the same list, which by then "
            "is empty again."
        ),
        approach=(
            "1) out = []. 2) walk(i, current): at i == len(nums), record a copy. 3) Otherwise "
            "walk(i+1) without nums[i], then append it, walk(i+1), and pop it back off. "
            "O(n · 2ⁿ) — which is the size of the answer."
        ),
        solution=(
            "def subsets(nums):\n"
            "    out = []\n\n"
            "    def walk(i, current):\n"
            "        if i == len(nums):\n"
            "            out.append(current[:])\n"
            "            return\n"
            "        walk(i + 1, current)\n"
            "        current.append(nums[i])\n"
            "        walk(i + 1, current)\n"
            "        current.pop()\n\n"
            "    walk(0, [])\n"
            "    return out"
        ),
        tests=[
            example([[1, 2, 3]],
                    [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]),
            example([[0]], [[], [0]]),
            hidden("no blocks, one empty selection", [[]], [[]]),
            hidden("two blocks", [[1, 2]], [[], [1], [2], [1, 2]]),
            hidden("repeats are still two separate blocks", [[4, 4]],
                   [[], [4], [4], [4, 4]]),
            hidden("sixteen selections", [[1, 2, 3, 4]],
                   [[], [1], [2], [3], [4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4],
                    [1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4], [1, 2, 3, 4]]),
            hidden("negatives are blocks too", [[-1, 1]], [[], [-1], [1], [-1, 1]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="combination-sum",
        title="Combination Sum",
        difficulty="medium",
        prompt=(
            "Given distinct coin values and a total, list every way to make the total. A coin "
            "may be used as many times as you like, and two ways using the same coins the same "
            "number of times count as one."
        ),
        example_input="candidates = [2, 3, 6, 7], target = 7",
        example_output="[[2, 2, 3], [7]]",
        entrypoint="combinationSum",
        signature=sig("matrix<int>", candidates="list<int>", target="int"),
        compare_mode="unordered_deep",
        explainer=(
            "**Never step backwards through the coins.** At each coin you either use it again "
            "— staying put — or move past it for good. That's what stops [2, 3] and [3, 2] from "
            "both turning up, with no duplicate-checking needed anywhere."
        ),
        hint=(
            "Two base cases: the remainder hits zero, which is an answer, and the remainder "
            "goes negative or you run out of coins, which is a dead end."
        ),
        approach=(
            "1) walk(i, current, remaining). 2) remaining == 0: record a copy. 3) i past the "
            "end or remaining < 0: give up. 4) Take candidates[i] and recurse at i; then undo "
            "and recurse at i + 1."
        ),
        solution=(
            "def combinationSum(candidates, target):\n"
            "    out = []\n\n"
            "    def walk(i, current, remaining):\n"
            "        if remaining == 0:\n"
            "            out.append(current[:])\n"
            "            return\n"
            "        if i >= len(candidates) or remaining < 0:\n"
            "            return\n"
            "        current.append(candidates[i])\n"
            "        walk(i, current, remaining - candidates[i])\n"
            "        current.pop()\n"
            "        walk(i + 1, current, remaining)\n\n"
            "    walk(0, [], target)\n"
            "    return out"
        ),
        tests=[
            example([[2, 3, 6, 7], 7], [[2, 2, 3], [7]]),
            example([[2, 3, 5], 8], [[2, 2, 2, 2], [2, 3, 3], [3, 5]]),
            hidden("the coin is too big", [[2], 1], []),
            hidden("one coin, exactly", [[7], 7], [[7]]),
            hidden("two ways", [[2, 4], 6], [[2, 2, 2], [2, 4]]),
            hidden("only one coin value", [[1], 3], [[1, 1, 1]]),
            hidden("nothing fits", [[3, 5], 2], []),
        ],
    ),
    problem(
        zone=ZONE,
        slug="permutations",
        title="Permutations",
        difficulty="medium",
        prompt=(
            "List every order the distinct blocks could be lined up in. The lists themselves "
            "can come back in any order — but each one is an arrangement, so what's inside it "
            "matters."
        ),
        example_input="nums = [1, 2, 3]",
        example_output="[[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]",
        entrypoint="permute",
        signature=sig("matrix<int>", nums="list<int>"),
        # The arrangements can come in any order; the arrangement itself cannot.
        compare_mode="unordered",
        explainer=(
            "**Pick a first block, then permute the rest.** Every arrangement is one of the n "
            "blocks followed by an arrangement of the other n - 1 — so the recursion is the "
            "definition, read out loud."
        ),
        hint=(
            "Unlike Subsets, order is the whole point here, so `unordered_deep` would be wrong "
            "and the judge doesn't use it: [1, 2, 3] and [3, 2, 1] are two different answers, "
            "both of which must appear."
        ),
        approach=(
            "1) walk(current, remaining). 2) remaining empty: record current. 3) Otherwise for "
            "each i, recurse with remaining[i] appended and that element removed. "
            "O(n · n!) — the size of the answer."
        ),
        solution=(
            "def permute(nums):\n"
            "    out = []\n\n"
            "    def walk(current, remaining):\n"
            "        if not remaining:\n"
            "            out.append(current)\n"
            "            return\n"
            "        for i in range(len(remaining)):\n"
            "            walk(current + [remaining[i]], remaining[:i] + remaining[i + 1:])\n\n"
            "    walk([], list(nums))\n"
            "    return out"
        ),
        tests=[
            example([[1, 2, 3]],
                    [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]),
            example([[0, 1]], [[0, 1], [1, 0]]),
            hidden("one block", [[1]], [[1]]),
            hidden("no blocks, one empty arrangement", [[]], [[]]),
            hidden("two blocks", [[1, 2]], [[1, 2], [2, 1]]),
            hidden("negatives", [[-1, 2]], [[-1, 2], [2, -1]]),
            hidden("both orders of a big pair", [[9, 5]], [[9, 5], [5, 9]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="letter-combinations-of-a-phone-number",
        title="Letter Combinations of a Phone Number",
        difficulty="medium",
        prompt=(
            "The toy telephone puts three or four letters on each digit, the way phones used "
            "to: 2 is abc, 7 is pqrs, 9 is wxyz. Given a string of digits, list every word they "
            "could spell. An empty string spells nothing at all."
        ),
        example_input='digits = "23"',
        example_output='["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]',
        entrypoint="letterCombinations",
        signature=sig("list<string>", digits="string"),
        compare_mode="unordered",
        explainer=(
            "**One digit at a time, multiplying what you have.** Start with a single empty "
            "word. Each digit replaces every word so far with one copy per letter it offers — "
            "which is the same tree the recursive version walks, just written iteratively."
        ),
        hint=(
            "No digits means no words, not one empty word. That empty-list special case is the "
            "only thing separating a working answer from an off-by-one on the whole problem."
        ),
        approach=(
            "1) If digits is empty, return []. 2) words = ['']. 3) For each digit, rebuild "
            "words as every existing word plus every letter that digit offers. 4) Return words."
        ),
        solution=(
            "def letterCombinations(digits):\n"
            "    if not digits:\n"
            "        return []\n"
            "    keypad = {\n"
            "        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',\n"
            "        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz',\n"
            "    }\n"
            "    words = ['']\n"
            "    for digit in digits:\n"
            "        words = [word + ch for word in words for ch in keypad[digit]]\n"
            "    return words"
        ),
        tests=[
            example(["23"], ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]),
            example([""], []),
            hidden("a single digit", ["2"], ["a", "b", "c"]),
            hidden("the two four-letter digits", ["79"],
                   ["pw", "px", "py", "pz", "qw", "qx", "qy", "qz", "rw", "rx", "ry", "rz",
                    "sw", "sx", "sy", "sz"]),
            hidden("four letters on their own", ["7"], ["p", "q", "r", "s"]),
            hidden("nine on its own", ["9"], ["w", "x", "y", "z"]),
            hidden("two digits, one of them long", ["27"],
                   ["ap", "aq", "ar", "as", "bp", "bq", "br", "bs", "cp", "cq", "cr", "cs"]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="word-search",
        title="Word Search",
        difficulty="medium",
        prompt=(
            "Letters are printed on a grid of tiles. Say whether the word can be spelled by "
            "stepping between neighbouring tiles up, down, left or right — never reusing a tile "
            "within the same attempt."
        ),
        example_input=(
            'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED"'
        ),
        example_output="true",
        entrypoint="exist",
        signature=sig("bool", board="matrix<string>", word="string"),
        explainer=(
            "**Mark the tile on the way in, unmark it on the way out.** That's the whole "
            "backtracking idea: a tile is off-limits while it's part of the path you're "
            "currently trying, and available again the moment you give that path up."
        ),
        hint=(
            "Overwriting the tile with a character that can't appear in the word is the "
            "cheapest visited-set there is — just remember to put the real letter back before "
            "you return."
        ),
        approach=(
            "1) For every starting tile, run a DFS carrying how many letters are matched. "
            "2) Matched == len(word): found it. 3) Off the grid or the wrong letter: dead end. "
            "4) Otherwise blank the tile, try all four neighbours, restore it."
        ),
        solution=(
            "def exist(board, word):\n"
            "    if not board or not board[0]:\n"
            "        return False\n"
            "    rows, cols = len(board), len(board[0])\n\n"
            "    def walk(r, c, i):\n"
            "        if i == len(word):\n"
            "            return True\n"
            "        if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != word[i]:\n"
            "            return False\n"
            "        letter = board[r][c]\n"
            "        board[r][c] = '#'\n"
            "        found = (walk(r + 1, c, i + 1) or walk(r - 1, c, i + 1)\n"
            "                 or walk(r, c + 1, i + 1) or walk(r, c - 1, i + 1))\n"
            "        board[r][c] = letter\n"
            "        return found\n\n"
            "    return any(walk(r, c, 0) for r in range(rows) for c in range(cols))"
        ),
        tests=[
            example([[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                     "ABCCED"], True),
            example([[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                     "ABCB"], False),
            hidden("a word that doubles back",
                   [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                    "SEE"], True),
            hidden("one tile, one letter", [[["a"]], "a"], True),
            hidden("one tile, wrong letter", [[["a"]], "b"], False),
            hidden("right to left", [[["a", "b"]], "ba"], True),
            hidden("an empty board", [[[]], "a"], False),
        ],
    ),
]

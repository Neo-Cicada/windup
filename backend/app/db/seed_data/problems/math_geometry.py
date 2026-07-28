"""Spinning Top — Math & Geometry.

Turns, digits and spirals. There's no single pattern here — each of these is a
small observation about how a grid or a number is laid out, and once you have it
the code is short. Three of them are about doing something to a grid *in place*,
which is where the observation usually hides.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "spinning-top"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="rotate-image",
        title="Rotate Image",
        difficulty="medium",
        prompt=(
            "Spin the square picture tile a quarter turn clockwise and return it. The top-left "
            "corner ends up top-right."
        ),
        example_input="matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]",
        example_output="[[7, 4, 1], [8, 5, 2], [9, 6, 3]]",
        entrypoint="rotate",
        signature=sig("matrix<int>", matrix="matrix<int>"),
        explainer=(
            "**A quarter turn is a flip and a flip.** Transpose the tile — mirror it along the "
            "top-left-to-bottom-right diagonal — and then reverse each row. Between them those "
            "two mirrorings compose into exactly the rotation, with no arithmetic on indices at "
            "all."
        ),
        hint=(
            "Written directly, the cell that ends up at [i][j] came from [n-1-j][i]. Getting "
            "that index the right way round is the whole problem; check it on a 2 × 2 first."
        ),
        approach=(
            "1) For i in 0..n-1, for j in 0..n-1: out[i][j] = matrix[n-1-j][i]. 2) Return out. "
            "Or transpose then reverse each row, which does it without a second grid."
        ),
        solution=(
            "def rotate(matrix):\n"
            "    n = len(matrix)\n"
            "    return [[matrix[n - 1 - j][i] for j in range(n)] for i in range(n)]"
        ),
        tests=[
            example([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [[7, 4, 1], [8, 5, 2], [9, 6, 3]]),
            example([[[1, 2], [3, 4]]], [[3, 1], [4, 2]]),
            hidden("a single square", [[[1]]], [[1]]),
            hidden("nothing to spin", [[]], []),
            hidden("four by four",
                   [[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]],
                   [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]),
            hidden("negatives spin the same", [[[-1, -2], [-3, -4]]], [[-3, -1], [-4, -2]]),
            hidden("all the same colour", [[[7, 7], [7, 7]]], [[7, 7], [7, 7]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="spiral-matrix",
        title="Spiral Matrix",
        difficulty="medium",
        prompt=(
            "Read the picture tiles off the board in a spiral: along the top, down the right, "
            "back along the bottom, up the left, and inwards. Return them in that order."
        ),
        example_input="matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]",
        example_output="[1, 2, 3, 6, 9, 8, 7, 4, 5]",
        entrypoint="spiralOrder",
        signature=sig("list<int>", matrix="matrix<int>"),
        explainer=(
            "**Four walls, closing in.** Keep the top, bottom, left and right edges of what's "
            "left to read. Walk one edge, then move it inwards. When the top passes the bottom "
            "or the left passes the right, everything has been read."
        ),
        hint=(
            "The two extra checks before the bottom row and the left column are what stops a "
            "single leftover row or column being read twice. Every wrong answer here is that "
            "double-read."
        ),
        approach=(
            "1) top, bottom, left, right = the four edges. 2) While top <= bottom and left <= "
            "right: read the top row and lower top; read the right column and lower right; if "
            "rows remain read the bottom; if columns remain read the left. O(rows × cols)."
        ),
        solution=(
            "def spiralOrder(matrix):\n"
            "    if not matrix or not matrix[0]:\n"
            "        return []\n"
            "    out = []\n"
            "    top, bottom = 0, len(matrix) - 1\n"
            "    left, right = 0, len(matrix[0]) - 1\n"
            "    while top <= bottom and left <= right:\n"
            "        for c in range(left, right + 1):\n"
            "            out.append(matrix[top][c])\n"
            "        top += 1\n"
            "        for r in range(top, bottom + 1):\n"
            "            out.append(matrix[r][right])\n"
            "        right -= 1\n"
            "        if top <= bottom:\n"
            "            for c in range(right, left - 1, -1):\n"
            "                out.append(matrix[bottom][c])\n"
            "            bottom -= 1\n"
            "        if left <= right:\n"
            "            for r in range(bottom, top - 1, -1):\n"
            "                out.append(matrix[r][left])\n"
            "            left += 1\n"
            "    return out"
        ),
        tests=[
            example([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [1, 2, 3, 6, 9, 8, 7, 4, 5]),
            example([[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]],
                    [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]),
            hidden("a single tile", [[[1]]], [1]),
            hidden("one row", [[[1, 2]]], [1, 2]),
            hidden("one column", [[[1], [2]]], [1, 2]),
            hidden("an empty board", [[[]]], []),
            hidden("two by two", [[[1, 2], [3, 4]]], [1, 2, 4, 3]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="set-matrix-zeroes",
        title="Set Matrix Zeroes",
        difficulty="medium",
        prompt=(
            "Wherever the board has a 0, blank out that whole row and that whole column. Return "
            "the board. Blanks made by this rule don't cause more blanking."
        ),
        example_input="matrix = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]",
        example_output="[[1, 0, 1], [0, 0, 0], [1, 0, 1]]",
        entrypoint="setZeroes",
        signature=sig("matrix<int>", matrix="matrix<int>"),
        explainer=(
            "**Find them all before you blank any.** Blanking as you scan would create new "
            "zeroes that then blank their own rows, and the whole board would go out. So make "
            "two passes: one to note which rows and columns are doomed, one to apply it."
        ),
        hint=(
            "The sets of doomed rows and columns are all the memory you need — O(rows + cols) "
            "rather than a copy of the board."
        ),
        approach=(
            "1) Collect the rows containing a 0 and the columns containing one. 2) Rebuild "
            "every cell as 0 if its row or column is doomed, else its old value. "
            "O(rows × cols)."
        ),
        solution=(
            "def setZeroes(matrix):\n"
            "    if not matrix or not matrix[0]:\n"
            "        return matrix\n"
            "    rows = {i for i, row in enumerate(matrix) if 0 in row}\n"
            "    cols = {\n"
            "        j for j in range(len(matrix[0]))\n"
            "        if any(row[j] == 0 for row in matrix)\n"
            "    }\n"
            "    return [\n"
            "        [0 if i in rows or j in cols else value for j, value in enumerate(row)]\n"
            "        for i, row in enumerate(matrix)\n"
            "    ]"
        ),
        tests=[
            example([[[1, 1, 1], [1, 0, 1], [1, 1, 1]]],
                    [[1, 0, 1], [0, 0, 0], [1, 0, 1]]),
            example([[[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]],
                    [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]]),
            hidden("nothing to blank", [[[1]]], [[1]]),
            hidden("a single zero", [[[0]]], [[0]]),
            hidden("no zeroes anywhere", [[[1, 2], [3, 4]]], [[1, 2], [3, 4]]),
            hidden("an empty board", [[[]]], [[]]),
            hidden("a corner zero", [[[1, 0], [1, 1]]], [[0, 0], [1, 0]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="happy-number",
        title="Happy Number",
        difficulty="easy",
        prompt=(
            "Replace the number with the sum of the squares of its digits, over and over. If it "
            "reaches 1 the number is happy; if it goes round in circles forever it isn't. Say "
            "which."
        ),
        example_input="n = 19",
        example_output="true",
        entrypoint="isHappy",
        signature=sig("bool", n="int"),
        explainer=(
            "**It's a linked list in disguise.** The sequence has to repeat eventually, because "
            "the digit-square sum of anything is small — so the question is only whether the "
            "loop it falls into is the one at 1. Any cycle detection settles it."
        ),
        hint=(
            "A set of numbers already seen is the easy way. The tortoise-and-hare from Marble "
            "Run works here too, in O(1) space, and for exactly the same reason."
        ),
        approach=(
            "1) seen = set(). 2) While n isn't 1 and hasn't been seen: record it and replace it "
            "with the sum of its digits squared. 3) Return n == 1."
        ),
        solution=(
            "def isHappy(n):\n"
            "    seen = set()\n"
            "    while n != 1 and n not in seen:\n"
            "        seen.add(n)\n"
            "        total = 0\n"
            "        while n:\n"
            "            n, digit = divmod(n, 10)\n"
            "            total += digit * digit\n"
            "        n = total\n"
            "    return n == 1"
        ),
        tests=[
            example([19], True),
            example([2], False),
            hidden("one is already happy", [1], True),
            hidden("a single happy digit", [7], True),
            hidden("the unhappy loop", [4], False),
            hidden("a round number", [100], True),
            hidden("nearly happy", [116], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="plus-one",
        title="Plus One",
        difficulty="easy",
        prompt=(
            "A big number is written one digit per card, most significant first. Add one to it "
            "and return the cards."
        ),
        example_input="digits = [1, 2, 3]",
        example_output="[1, 2, 4]",
        entrypoint="plusOne",
        signature=sig("list<int>", digits="list<int>"),
        explainer=(
            "**Carry from the right, and stop as soon as you can.** Any digit below 9 just goes "
            "up by one and you're done. A 9 becomes 0 and passes the carry left. Only if every "
            "digit was a 9 does the number get longer."
        ),
        hint=(
            "The all-nines case is the one to get right: 999 + 1 is 1000, which needs a *new* "
            "card at the front rather than an edit to an existing one."
        ),
        approach=(
            "1) Walk the cards from the right. 2) Below 9: increment and return. 3) Otherwise "
            "set it to 0 and carry on. 4) If you fall off the front, return [1] + the zeroes. "
            "O(n)."
        ),
        solution=(
            "def plusOne(digits):\n"
            "    digits = list(digits)\n"
            "    for i in range(len(digits) - 1, -1, -1):\n"
            "        if digits[i] < 9:\n"
            "            digits[i] += 1\n"
            "            return digits\n"
            "        digits[i] = 0\n"
            "    return [1] + digits"
        ),
        tests=[
            example([[1, 2, 3]], [1, 2, 4]),
            example([[4, 3, 2, 1]], [4, 3, 2, 2]),
            hidden("a single nine grows a card", [[9]], [1, 0]),
            hidden("two nines", [[9, 9]], [1, 0, 0]),
            hidden("zero becomes one", [[0]], [1]),
            hidden("the carry stops partway", [[1, 9, 9]], [2, 0, 0]),
            hidden("all nines", [[9, 9, 9]], [1, 0, 0, 0]),
        ],
    ),
]

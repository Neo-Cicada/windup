"""Stacking Cups — Stack.

Last in, first out. Every problem here is the same realisation twice: the thing
you need next is the thing you put down most recently, so the cups themselves
remember the order and you don't have to.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "stacking-cups"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="valid-parentheses",
        title="Valid Parentheses",
        difficulty="easy",
        prompt=(
            "Stack the cups so every one that goes down comes back up in order. Decide whether "
            "a string of brackets is balanced."
        ),
        example_input='s = "{[()]}"',
        example_output="true",
        entrypoint="isValid",
        signature=sig("bool", s="string"),
        explainer=(
            "**Last in, first out.** Push every opening cup. On a closing cup, the top of the "
            "stack must be its match — otherwise the tower topples."
        ),
        hint="A leftover stack at the end means unmatched cups. Don't forget to check for that.",
        approach=(
            "1) pairs = {')':'(', ']':'[', '}':'{'}. 2) Push openers. 3) On a closer, pop and "
            "compare. 4) Return not stack."
        ),
        solution=(
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
        tests=[
            example(["{[()]}"], True),
            example(["(]"], False),
            hidden("no cups at all", [""], True),
            hidden("one cup left standing", ["("], False),
            hidden("three towers side by side", ["()[]{}"], True),
            hidden("crossed, not nested", ["([)]"], False),
            hidden("closes before it opens", [")("], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="evaluate-reverse-polish-notation",
        title="Evaluate Reverse Polish Notation",
        difficulty="medium",
        prompt=(
            "The toy calculator writes its sums back-to-front: the numbers first, then the "
            "operator. Work through the tokens and return what the sum comes to. Division "
            "chops towards zero."
        ),
        example_input='tokens = ["2", "1", "+", "3", "*"]',
        example_output="9",
        entrypoint="evalRPN",
        signature=sig("int", tokens="list<string>"),
        explainer=(
            "**The operands are already waiting.** Push every number. When an operator turns "
            "up, its two arguments are the top two cups — pop them, apply it, push the result "
            "back. When the tokens run out, the answer is the only cup left."
        ),
        hint=(
            "Order matters for - and /: the cup you pop *first* is the right-hand side. And "
            "watch the truncation — Python's // rounds towards negative infinity, which is not "
            "what this calculator does."
        ),
        approach=(
            "1) stack = []. 2) For each token: if it's an operator, pop right then left, apply, "
            "push; otherwise push int(token). 3) Return stack[0]. Use int(left / right) so "
            "-7 / 3 chops to -2 rather than -3. O(n) time and space."
        ),
        solution=(
            "def evalRPN(tokens):\n"
            "    stack = []\n"
            "    for token in tokens:\n"
            "        if token in ('+', '-', '*', '/'):\n"
            "            right = stack.pop()\n"
            "            left = stack.pop()\n"
            "            if token == '+':\n"
            "                stack.append(left + right)\n"
            "            elif token == '-':\n"
            "                stack.append(left - right)\n"
            "            elif token == '*':\n"
            "                stack.append(left * right)\n"
            "            else:\n"
            "                stack.append(int(left / right))\n"
            "        else:\n"
            "            stack.append(int(token))\n"
            "    return stack[0]"
        ),
        tests=[
            example([["2", "1", "+", "3", "*"]], 9),
            example([["4", "13", "5", "/", "+"]], 6),
            hidden("just a number", [["5"]], 5),
            hidden("a long one", [["10", "6", "9", "3", "+", "-11", "*", "/", "*",
                                  "17", "+", "5", "+"]], 22),
            hidden("a negative operand", [["-3", "2", "*"]], -6),
            hidden("division chops towards zero", [["7", "-3", "/"]], -2),
            hidden("subtraction is not commutative", [["3", "4", "-", "5", "*"]], -5),
        ],
    ),
    problem(
        zone=ZONE,
        slug="generate-parentheses",
        title="Generate Parentheses",
        difficulty="medium",
        prompt=(
            "Given n pairs of cups, list every way to stack them so the tower never topples — "
            "every cup that goes down comes back up in order."
        ),
        example_input="n = 3",
        example_output='["((()))", "(()())", "(())()", "()(())", "()()()"]',
        entrypoint="generateParenthesis",
        signature=sig("list<string>", n="int"),
        # The towers can come back in any order.
        compare_mode="unordered",
        explainer=(
            "**Build it, don't filter it.** Rather than generating all 2^2n strings and testing "
            "each, only ever add a bracket that keeps the tower standing: an opener while you "
            "have openers left, a closer only while there's something open to close."
        ),
        hint=(
            "Two counters are enough — how many openers you've used and how many closers. The "
            "rule is `open < n` to open, and `close < open` to close."
        ),
        approach=(
            "1) Recurse carrying the string so far plus the two counts. 2) At length 2n, record "
            "it. 3) Otherwise try adding '(' if open < n, and ')' if close < open. There are "
            "Catalan(n) answers, and this visits exactly those."
        ),
        solution=(
            "def generateParenthesis(n):\n"
            "    out = []\n\n"
            "    def build(current, opened, closed):\n"
            "        if len(current) == 2 * n:\n"
            "            out.append(current)\n"
            "            return\n"
            "        if opened < n:\n"
            "            build(current + '(', opened + 1, closed)\n"
            "        if closed < opened:\n"
            "            build(current + ')', opened, closed + 1)\n\n"
            "    build('', 0, 0)\n"
            "    return out"
        ),
        tests=[
            example([3], ["((()))", "(()())", "(())()", "()(())", "()()()"]),
            example([1], ["()"]),
            hidden("two pairs", [2], ["(())", "()()"]),
            hidden("fourteen towers", [4],
                   ["(((())))", "((()()))", "((())())", "((()))()", "(()(()))", "(()()())",
                    "(()())()", "(())(())", "(())()()", "()((()))", "()(()())", "()(())()",
                    "()()(())", "()()()()"]),
            hidden("no cups, one empty tower", [0], [""]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="daily-temperatures",
        title="Daily Temperatures",
        difficulty="medium",
        prompt=(
            "The playroom thermometer was read once a day. For each day, say how many days you "
            "have to wait for a warmer one — 0 if it never gets warmer."
        ),
        example_input="temperatures = [73, 74, 75, 71, 69, 72, 76, 73]",
        example_output="[1, 1, 4, 2, 1, 1, 0, 0]",
        entrypoint="dailyTemperatures",
        signature=sig("list<int>", temperatures="list<int>"),
        explainer=(
            "**A stack of days still waiting.** Walk the days once, keeping a stack of the ones "
            "that haven't seen anything warmer yet. Today's reading answers every waiting day "
            "colder than it — pop them and write down the gap."
        ),
        hint=(
            "Push *indices*, not temperatures: the answer is a distance, so you need to know "
            "how far back the waiting day was. The stack stays decreasing on its own."
        ),
        approach=(
            "1) out = [0] * n, stack = []. 2) For i, t in enumerate(temperatures): while stack "
            "and temperatures[stack[-1]] < t: j = stack.pop(); out[j] = i - j. 3) Push i. "
            "4) Return out. Each day is pushed and popped once — O(n)."
        ),
        solution=(
            "def dailyTemperatures(temperatures):\n"
            "    out = [0] * len(temperatures)\n"
            "    stack = []\n"
            "    for i, t in enumerate(temperatures):\n"
            "        while stack and temperatures[stack[-1]] < t:\n"
            "            j = stack.pop()\n"
            "            out[j] = i - j\n"
            "        stack.append(i)\n"
            "    return out"
        ),
        tests=[
            example([[73, 74, 75, 71, 69, 72, 76, 73]], [1, 1, 4, 2, 1, 1, 0, 0]),
            example([[30, 40, 50, 60]], [1, 1, 1, 0]),
            hidden("no readings", [[]], []),
            hidden("one reading", [[100]], [0]),
            hidden("steadily warmer", [[30, 60, 90]], [1, 1, 0]),
            hidden("never gets warmer", [[90, 80, 70]], [0, 0, 0]),
            hidden("a long wait then a jump", [[89, 62, 70, 58, 47, 47, 46, 76, 100, 70]],
                   [8, 1, 5, 4, 3, 2, 1, 1, 0, 0]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="largest-rectangle-in-histogram",
        title="Largest Rectangle in Histogram",
        difficulty="hard",
        prompt=(
            "A row of building blocks stands side by side, each one unit wide. Find the largest "
            "rectangle you can draw that fits entirely inside the row."
        ),
        example_input="heights = [2, 1, 5, 6, 2, 3]",
        example_output="10",
        entrypoint="largestRectangleArea",
        signature=sig("int", heights="list<int>"),
        explainer=(
            "**Every block asks how wide it can spread.** A rectangle of a given height runs "
            "until it hits something shorter, left and right. Keep a stack of blocks that are "
            "still spreading; a shorter block arriving is what finally settles their width."
        ),
        hint=(
            "When you pop a block because a shorter one arrived, the rectangle it can form "
            "starts where the *popped* block's own run started — not at its index. Carry that "
            "start along on the stack."
        ),
        approach=(
            "1) Walk heights with a sentinel 0 appended. 2) While the stack's top is taller than "
            "the current block, pop it, score height × (i - its start), and inherit its start. "
            "3) Push (start, current). 4) Return the best. O(n): each block is pushed and "
            "popped once."
        ),
        solution=(
            "def largestRectangleArea(heights):\n"
            "    stack = []\n"
            "    best = 0\n"
            "    for i, h in enumerate(heights + [0]):\n"
            "        start = i\n"
            "        while stack and stack[-1][1] > h:\n"
            "            j, height = stack.pop()\n"
            "            best = max(best, height * (i - j))\n"
            "            start = j\n"
            "        stack.append((start, h))\n"
            "    return best"
        ),
        tests=[
            example([[2, 1, 5, 6, 2, 3]], 10),
            example([[2, 4]], 4),
            hidden("no blocks", [[]], 0),
            hidden("one block", [[1]], 1),
            hidden("a flat row", [[5, 5, 5, 5]], 20),
            hidden("a dip between two equals", [[2, 1, 2]], 3),
            hidden("the answer straddles a valley", [[6, 7, 5, 2, 4, 5, 9, 3]], 16),
        ],
    ),
]

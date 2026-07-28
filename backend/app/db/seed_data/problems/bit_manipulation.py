"""Light Switches — Bit Manipulation.

A row of switches, each on or off. These problems all have a plain, obvious
solution with a dictionary or a loop; the point of the corner is that looking at
the number as its bits makes the obvious solution unnecessary.

Two facts do most of the work: `x ^ x` is 0, so pairs cancel; and `n & (n - 1)`
clears the lowest lit switch.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "light-switches"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="single-number",
        title="Single Number",
        difficulty="easy",
        prompt=(
            "Every toy in the box has an identical twin except one. Given their numbers, find "
            "the lonely one — without keeping a tally."
        ),
        example_input="nums = [4, 1, 2, 1, 2]",
        example_output="4",
        entrypoint="singleNumber",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**XOR cancels pairs.** `x ^ x` is 0 and `x ^ 0` is x, and the order doesn't "
            "matter — so XOR the whole box together and every twin annihilates, leaving only "
            "the toy that never had one."
        ),
        hint=(
            "A set or a Counter also works, in O(n) space. XOR does it in O(1), which is the "
            "constraint this problem is really about."
        ),
        approach=(
            "1) answer = 0. 2) For each n: answer ^= n. 3) Return answer. O(n) time, O(1) "
            "space."
        ),
        solution=(
            "def singleNumber(nums):\n"
            "    answer = 0\n"
            "    for n in nums:\n"
            "        answer ^= n\n"
            "    return answer"
        ),
        tests=[
            example([[4, 1, 2, 1, 2]], 4),
            example([[2, 2, 1]], 1),
            hidden("a single toy", [[1]], 1),
            hidden("the twins are zeroes", [[0, 1, 0]], 1),
            hidden("negative numbers cancel too", [[-1, -1, 5]], 5),
            hidden("the lonely toy is last", [[7, 3, 3, 7, 9]], 9),
            hidden("the lonely toy is first", [[9, 3, 3, 7, 7]], 9),
        ],
    ),
    problem(
        zone=ZONE,
        slug="number-of-1-bits",
        title="Number of 1 Bits",
        difficulty="easy",
        prompt="How many switches are on? Given a number, count its lit bits.",
        example_input="n = 11",
        example_output="3",
        entrypoint="hammingWeight",
        signature=sig("int", n="int"),
        explainer=(
            "**Turn off the lowest lit switch, and count how many times you can.** `n & "
            "(n - 1)` does exactly that — it borrows through the trailing zeroes and clears the "
            "lowest 1. So the loop runs once per lit switch, not once per switch."
        ),
        hint=(
            "Shifting right 32 times and checking the low bit works too. Kernighan's trick is "
            "faster when only a few switches are on, and never slower."
        ),
        approach=(
            "1) count = 0. 2) While n: n &= n - 1; count += 1. 3) Return count. O(lit bits)."
        ),
        solution=(
            "def hammingWeight(n):\n"
            "    count = 0\n"
            "    while n:\n"
            "        n &= n - 1\n"
            "        count += 1\n"
            "    return count"
        ),
        tests=[
            example([11], 3),
            example([128], 1),
            hidden("every switch off", [0], 0),
            hidden("one switch", [1], 1),
            hidden("a whole byte lit", [255], 8),
            hidden("the top switch of thirty-two", [2147483648], 1),
            hidden("all but one", [4294967293], 31),
        ],
    ),
    problem(
        zone=ZONE,
        slug="counting-bits",
        title="Counting Bits",
        difficulty="medium",
        prompt=(
            "For every number from 0 up to n, count its lit switches. Return the counts in "
            "order, so the answer has n + 1 entries."
        ),
        example_input="n = 5",
        example_output="[0, 1, 1, 2, 1, 2]",
        entrypoint="countBits",
        signature=sig("list<int>", n="int"),
        explainer=(
            "**Each answer is one you already have.** Dropping the lowest bit of i gives i >> 1, "
            "a smaller number you've already counted — so the count for i is that one's count "
            "plus whatever the bit you dropped was."
        ),
        hint=(
            "`dp[i] = dp[i >> 1] + (i & 1)`. Counting each number from scratch is O(n log n); "
            "this is O(n), and that's the whole exercise."
        ),
        approach=(
            "1) dp = [0] * (n + 1). 2) For i in 1..n: dp[i] = dp[i >> 1] + (i & 1). 3) Return "
            "dp. O(n) time and space."
        ),
        solution=(
            "def countBits(n):\n"
            "    dp = [0] * (n + 1)\n"
            "    for i in range(1, n + 1):\n"
            "        dp[i] = dp[i >> 1] + (i & 1)\n"
            "    return dp"
        ),
        tests=[
            example([5], [0, 1, 1, 2, 1, 2]),
            example([2], [0, 1, 1]),
            hidden("only zero", [0], [0]),
            hidden("zero and one", [1], [0, 1]),
            hidden("up to eight", [8], [0, 1, 1, 2, 1, 2, 2, 3, 1]),
            hidden("up to sixteen", [16],
                   [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, 1]),
            hidden("up to three", [3], [0, 1, 1, 2]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="reverse-bits",
        title="Reverse Bits",
        difficulty="medium",
        prompt=(
            "The row has exactly 32 switches. Read them right to left and write them back left "
            "to right — return the number the reversed row spells."
        ),
        example_input="n = 43261596",
        example_output="964176192",
        entrypoint="reverseBits",
        signature=sig("int", n="int"),
        explainer=(
            "**Pour it out one switch at a time.** Take the lowest bit of the input, push it "
            "onto the bottom of the answer, and shift the answer up. Do that 32 times and the "
            "first bit you took has been pushed all the way to the top."
        ),
        hint=(
            "The width is fixed at 32 whatever the input looks like — you must loop 32 times, "
            "not 'until n runs out', or a small number ends up in the wrong place entirely."
        ),
        approach=(
            "1) out = 0. 2) Repeat 32 times: out = (out << 1) | (n & 1); n >>= 1. 3) Return "
            "out. O(32), which is O(1)."
        ),
        solution=(
            "def reverseBits(n):\n"
            "    out = 0\n"
            "    for _ in range(32):\n"
            "        out = (out << 1) | (n & 1)\n"
            "        n >>= 1\n"
            "    return out"
        ),
        tests=[
            example([43261596], 964176192),
            example([4294967293], 3221225471),
            hidden("every switch off", [0], 0),
            hidden("the lowest becomes the highest", [1], 2147483648),
            hidden("and back again", [2147483648], 1),
            hidden("all thirty-two lit", [4294967295], 4294967295),
            hidden("a palindrome of switches", [2147483649], 2147483649),
        ],
    ),
    problem(
        zone=ZONE,
        slug="missing-number",
        title="Missing Number",
        difficulty="easy",
        prompt=(
            "The numbered blocks 0 through n are in the bin, except one has rolled under the "
            "sofa. Given the n blocks that are left, say which is missing."
        ),
        example_input="nums = [3, 0, 1]",
        example_output="2",
        entrypoint="missingNumber",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**Everything is paired except the gap.** XOR every index together with every "
            "value: each present block cancels its own index, and what survives is the index "
            "with nothing to cancel it. Adding up 0..n and subtracting works identically."
        ),
        hint=(
            "n is len(nums), not max(nums) — the missing block might be the largest one, in "
            "which case nothing in the bin mentions it at all."
        ),
        approach=(
            "1) answer = len(nums). 2) For i, n in enumerate(nums): answer ^= i ^ n. 3) Return "
            "answer. O(n) time, O(1) space, and no overflow to worry about."
        ),
        solution=(
            "def missingNumber(nums):\n"
            "    answer = len(nums)\n"
            "    for i, n in enumerate(nums):\n"
            "        answer ^= i ^ n\n"
            "    return answer"
        ),
        tests=[
            example([[3, 0, 1]], 2),
            example([[0, 1]], 2),
            hidden("an empty bin", [[]], 0),
            hidden("only zero is there", [[0]], 1),
            hidden("only one is there", [[1]], 0),
            hidden("the missing block is in the middle",
                   [[9, 6, 4, 2, 3, 5, 7, 0, 1]], 8),
            hidden("zero rolled away", [[1, 2]], 0),
        ],
    ),
]

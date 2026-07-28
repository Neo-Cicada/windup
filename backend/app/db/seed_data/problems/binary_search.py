"""See-Saw — Binary Search.

Halve the problem, then halve it again. The first two are the textbook shape;
the last three are the interesting one, where the sorted thing you're searching
isn't the input at all but the *answer*, or a row that's been rotated out of
order.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "see-saw"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="binary-search",
        title="Binary Search",
        difficulty="easy",
        prompt=(
            "The number cards are laid out in order along the see-saw. Find where the target "
            "card sits, or return -1 if it isn't there."
        ),
        example_input="nums = [-1, 0, 3, 5, 9, 12], target = 9",
        example_output="4",
        entrypoint="search",
        signature=sig("int", nums="list<int>", target="int"),
        explainer=(
            "**Tip the see-saw.** Look at the middle card. Too small, and every card to its "
            "left is too small as well — throw that half away. Too big, and the same on the "
            "other side. Each look halves what's left."
        ),
        hint=(
            "Use `left + (right - left) // 2` and keep the bounds inclusive. The loop ends when "
            "left passes right, which is exactly when there's nowhere left to look."
        ),
        approach=(
            "1) left, right = 0, len(nums) - 1. 2) While left <= right: mid = (left + right) "
            "// 2. 3) Hit? return mid. Too small? left = mid + 1. Too big? right = mid - 1. "
            "4) Return -1. O(log n) time, O(1) space."
        ),
        solution=(
            "def search(nums, target):\n"
            "    left, right = 0, len(nums) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if nums[mid] == target:\n"
            "            return mid\n"
            "        if nums[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1"
        ),
        tests=[
            example([[-1, 0, 3, 5, 9, 12], 9], 4),
            example([[-1, 0, 3, 5, 9, 12], 2], -1),
            hidden("no cards at all", [[], 1], -1),
            hidden("one card, and it matches", [[5], 5], 0),
            hidden("one card, and it doesn't", [[5], -5], -1),
            hidden("the very first card", [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 1], 0),
            hidden("the very last card", [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 10], 9),
        ],
    ),
    problem(
        zone=ZONE,
        slug="search-a-2d-matrix",
        title="Search a 2D Matrix",
        difficulty="medium",
        prompt=(
            "The number cards are pinned to a board in rows, each row sorted, and every card in "
            "a row smaller than the first card of the next. Say whether the target is pinned up "
            "there anywhere."
        ),
        example_input="matrix = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], target = 3",
        example_output="true",
        entrypoint="searchMatrix",
        signature=sig("bool", matrix="matrix<int>", target="int"),
        explainer=(
            "**It's one long row, folded.** Because each row starts above where the last one "
            "ended, reading the board left-to-right, top-to-bottom gives a single sorted "
            "sequence — so one binary search over 0..rows·cols does the whole thing."
        ),
        hint=(
            "Turn a flat index i into a cell with divmod: row = i // cols, col = i % cols. "
            "Watch out for a board with no cards on it before you read cols."
        ),
        approach=(
            "1) If the board is empty, return False. 2) rows, cols = dimensions; binary search "
            "0..rows*cols-1. 3) Read matrix[mid // cols][mid % cols] and compare. "
            "O(log(rows·cols)) time, O(1) space."
        ),
        solution=(
            "def searchMatrix(matrix, target):\n"
            "    if not matrix or not matrix[0]:\n"
            "        return False\n"
            "    rows, cols = len(matrix), len(matrix[0])\n"
            "    left, right = 0, rows * cols - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        value = matrix[mid // cols][mid % cols]\n"
            "        if value == target:\n"
            "            return True\n"
            "        if value < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return False"
        ),
        tests=[
            example([[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3], True),
            example([[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13], False),
            hidden("a single card", [[[1]], 1], True),
            hidden("a single card that doesn't match", [[[1]], 2], False),
            hidden("one row", [[[1, 3]], 3], True),
            hidden("one column", [[[1], [3], [5]], 5], True),
            hidden("a board with no cards", [[[]], 1], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="koko-eating-bananas",
        title="Koko Eating Bananas",
        difficulty="medium",
        prompt=(
            "The stuffed monkey has piles of toy bananas and h hours before the playroom "
            "closes. Each hour it picks one pile and eats up to k from it — no more that hour, "
            "even if the pile runs out. Find the smallest k that clears every pile in time."
        ),
        example_input="piles = [3, 6, 7, 11], h = 8",
        example_output="4",
        entrypoint="minEatingSpeed",
        signature=sig("int", piles="list<int>", h="int"),
        explainer=(
            "**Search the answer, not the input.** Speeds have a tipping point: below it the "
            "monkey runs out of time, above it there's time to spare, and it never flips back. "
            "That's a sorted yes/no line — so binary search it."
        ),
        hint=(
            "A pile of p at speed k takes ceil(p / k) hours, which is -(-p // k) without any "
            "floating point. The answer is never above max(piles), and never below 1."
        ),
        approach=(
            "1) lo, hi = 1, max(piles). 2) While lo < hi: mid = (lo + hi) // 2; if the total "
            "hours at mid fit in h, hi = mid, else lo = mid + 1. 3) Return lo. "
            "O(n log(max pile))."
        ),
        solution=(
            "def minEatingSpeed(piles, h):\n"
            "    lo, hi = 1, max(piles)\n"
            "    while lo < hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        hours = sum(-(-pile // mid) for pile in piles)\n"
            "        if hours <= h:\n"
            "            hi = mid\n"
            "        else:\n"
            "            lo = mid + 1\n"
            "    return lo"
        ),
        tests=[
            example([[3, 6, 7, 11], 8], 4),
            example([[30, 11, 23, 4, 20], 5], 30),
            hidden("one spare hour changes the answer", [[30, 11, 23, 4, 20], 6], 23),
            hidden("one pile, one hour", [[1], 1], 1),
            hidden("all the time in the world", [[1, 1, 1, 1], 4], 1),
            hidden("a huge pile, two hours", [[1000000000], 2], 500000000),
            hidden("exactly as many hours as piles", [[25, 10, 23, 4], 4], 25),
        ],
    ),
    problem(
        zone=ZONE,
        slug="find-minimum-in-rotated-sorted-array",
        title="Find Minimum in Rotated Sorted Array",
        difficulty="medium",
        prompt=(
            "The sorted row of cards got spun around, so it now starts somewhere in the middle "
            "and wraps. Every card is different. Find the smallest one."
        ),
        example_input="nums = [3, 4, 5, 1, 2]",
        example_output="1",
        entrypoint="findMin",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**One side is always still sorted.** Compare the middle card to the last one. If "
            "it's bigger, the spin point is somewhere to the right, so the smallest card is "
            "over there; if it's smaller, the middle card might itself be the smallest."
        ),
        hint=(
            "Compare against `nums[right]`, not `nums[left]` — comparing to the left end is the "
            "version that gets tangled up on a row that wasn't spun at all."
        ),
        approach=(
            "1) left, right = 0, len(nums) - 1. 2) While left < right: mid = (left + right) // "
            "2; if nums[mid] > nums[right]: left = mid + 1, else right = mid. 3) Return "
            "nums[left]. O(log n) time, O(1) space."
        ),
        solution=(
            "def findMin(nums):\n"
            "    left, right = 0, len(nums) - 1\n"
            "    while left < right:\n"
            "        mid = (left + right) // 2\n"
            "        if nums[mid] > nums[right]:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid\n"
            "    return nums[left]"
        ),
        tests=[
            example([[3, 4, 5, 1, 2]], 1),
            example([[4, 5, 6, 7, 0, 1, 2]], 0),
            hidden("never spun at all", [[11, 13, 15, 17]], 11),
            hidden("one card", [[1]], 1),
            hidden("two cards, spun", [[2, 1]], 1),
            hidden("spun by one", [[5, 1, 2, 3, 4]], 1),
            hidden("the smallest is in the middle", [[3, 1, 2]], 1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="search-in-rotated-sorted-array",
        title="Search in Rotated Sorted Array",
        difficulty="medium",
        prompt=(
            "The same spun row of cards, and now you want a particular one. Return where it "
            "sits, or -1 if it isn't there."
        ),
        example_input="nums = [4, 5, 6, 7, 0, 1, 2], target = 0",
        example_output="4",
        entrypoint="searchRotated",
        signature=sig("int", nums="list<int>", target="int"),
        explainer=(
            "**Work out which half is tidy, then ask whether the target lives in it.** The spin "
            "leaves at most one break, so of the two halves around the middle, at least one is "
            "properly sorted — and in a sorted half a simple range check settles it."
        ),
        hint=(
            "Compare nums[left] to nums[mid] to find the tidy half. If the target falls inside "
            "that half's range, search it; otherwise search the other one."
        ),
        approach=(
            "1) Standard binary search bounds. 2) If nums[left] <= nums[mid], the left half is "
            "sorted: go left when nums[left] <= target < nums[mid], else right. 3) Otherwise the "
            "right half is sorted; mirror the check. 4) Return -1. O(log n)."
        ),
        solution=(
            "def searchRotated(nums, target):\n"
            "    left, right = 0, len(nums) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if nums[mid] == target:\n"
            "            return mid\n"
            "        if nums[left] <= nums[mid]:\n"
            "            if nums[left] <= target < nums[mid]:\n"
            "                right = mid - 1\n"
            "            else:\n"
            "                left = mid + 1\n"
            "        else:\n"
            "            if nums[mid] < target <= nums[right]:\n"
            "                left = mid + 1\n"
            "            else:\n"
            "                right = mid - 1\n"
            "    return -1"
        ),
        tests=[
            example([[4, 5, 6, 7, 0, 1, 2], 0], 4),
            example([[4, 5, 6, 7, 0, 1, 2], 3], -1),
            hidden("no cards", [[], 5], -1),
            hidden("one card, no match", [[1], 0], -1),
            hidden("two cards", [[1, 3], 3], 1),
            hidden("the target is the first card", [[5, 1, 3], 5], 0),
            hidden("just before the break", [[4, 5, 6, 7, 8, 1, 2, 3], 8], 4),
        ],
    ),
]

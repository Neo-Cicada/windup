"""Rubber Bands — Two Pointers.

Same row of blocks as Building Blocks, walked differently: a finger at each end,
closing in. The trick is always the same one — knowing which finger to move, and
why moving the other one could not possibly help.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "rubber-bands"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="valid-palindrome",
        title="Valid Palindrome",
        difficulty="easy",
        prompt=(
            "A label on the toy box is meant to read the same forwards and backwards, once you "
            "ignore punctuation and capitals. Decide whether it does."
        ),
        example_input='s = "A man, a plan, a canal: Panama"',
        example_output="true",
        entrypoint="isPalindrome",
        signature=sig("bool", s="string"),
        explainer=(
            "**Two fingers, closing in.** One at each end of the label. Skip anything that "
            "isn't a letter or a digit, compare what's left in lowercase, and step both fingers "
            "inward until they meet."
        ),
        hint=(
            "You don't have to build a cleaned-up copy of the string. Skipping junk in place "
            "keeps it O(1) extra space — and remember the digits count as characters too."
        ),
        approach=(
            "1) left = 0, right = len(s) - 1. 2) While left < right: advance left past "
            "non-alphanumerics, retreat right past them. 3) If the two lowercased characters "
            "differ, return False. 4) Step both inward. 5) Return True. O(n) time, O(1) space."
        ),
        solution=(
            "def isPalindrome(s):\n"
            "    left, right = 0, len(s) - 1\n"
            "    while left < right:\n"
            "        while left < right and not s[left].isalnum():\n"
            "            left += 1\n"
            "        while left < right and not s[right].isalnum():\n"
            "            right -= 1\n"
            "        if s[left].lower() != s[right].lower():\n"
            "            return False\n"
            "        left += 1\n"
            "        right -= 1\n"
            "    return True"
        ),
        tests=[
            example(["A man, a plan, a canal: Panama"], True),
            example(["race a car"], False),
            hidden("nothing on the label", [""], True),
            hidden("only a space", [" "], True),
            hidden("a digit is not a letter", ["0P"], False),
            hidden("punctuation only", [".,"], True),
            hidden("underscores are junk too", ["ab_a"], True),
        ],
    ),
    problem(
        zone=ZONE,
        slug="two-sum-ii",
        title="Two Sum II",
        difficulty="medium",
        prompt=(
            "The same two-block puzzle, except this bin is already sorted shortest to tallest. "
            "Return the two positions that add up to the target — counting from 1, not 0."
        ),
        example_input="numbers = [2, 7, 11, 15], target = 9",
        example_output="[1, 2]",
        entrypoint="twoSumSorted",
        signature=sig("list<int>", numbers="list<int>", target="int"),
        explainer=(
            "**Sorted means you can steer.** Start wide. If the pair is too tall, the only way "
            "down is to pull the right finger in; if it's too short, push the left one out. "
            "Every step rules out a whole row of pairs, so no dictionary is needed at all."
        ),
        hint=(
            "This is the one place the answer is 1-indexed — add one to both positions before "
            "you return them. And O(1) extra space is the point: a hash map here is a step back."
        ),
        approach=(
            "1) left = 0, right = len(numbers) - 1. 2) total = numbers[left] + numbers[right]. "
            "3) If total == target: return [left + 1, right + 1]. 4) If total < target: "
            "left += 1, else right -= 1. O(n) time, O(1) space."
        ),
        solution=(
            "def twoSumSorted(numbers, target):\n"
            "    left, right = 0, len(numbers) - 1\n"
            "    while left < right:\n"
            "        total = numbers[left] + numbers[right]\n"
            "        if total == target:\n"
            "            return [left + 1, right + 1]\n"
            "        if total < target:\n"
            "            left += 1\n"
            "        else:\n"
            "            right -= 1\n"
            "    return []"
        ),
        tests=[
            example([[2, 7, 11, 15], 9], [1, 2]),
            example([[2, 3, 4], 6], [1, 3]),
            hidden("the only two blocks there are", [[1, 2], 3], [1, 2]),
            hidden("negatives at the front", [[-1, 0], -1], [1, 2]),
            hidden("a pair in the middle", [[1, 2, 3, 4, 4, 9, 56, 90], 8], [4, 5]),
            hidden("skips the shortest block", [[5, 25, 75], 100], [2, 3]),
            hidden("two zeroes", [[0, 0, 3, 4], 0], [1, 2]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="three-sum",
        title="Three Sum",
        difficulty="medium",
        prompt=(
            "Find every set of three blocks whose heights cancel out to zero. No two sets may "
            "hold the same three heights, and a block can't be used twice in one set."
        ),
        example_input="nums = [-1, 0, 1, 2, -1, -4]",
        example_output="[[-1, -1, 2], [-1, 0, 1]]",
        entrypoint="threeSum",
        signature=sig("matrix<int>", nums="list<int>"),
        # Any order of the triplets, and any order within one, is the same answer.
        compare_mode="unordered_deep",
        explainer=(
            "**Pin one, then it's Two Sum II.** Sort the blocks. Fix the first block of the "
            "triplet, and the other two have to add up to its negative — which is exactly the "
            "sorted two-pointer walk you already know."
        ),
        hint=(
            "Sorting is what makes duplicates skippable: after you use a height, step past every "
            "copy of it, both for the pinned block and for the left pointer once a triplet lands."
        ),
        approach=(
            "1) Sort nums. 2) For each i, skip if nums[i] == nums[i-1]. 3) Two-pointer over "
            "i+1..end looking for -nums[i]. 4) On a hit, record it and advance past duplicates. "
            "O(n²) time, O(1) space beyond the sort."
        ),
        solution=(
            "def threeSum(nums):\n"
            "    nums = sorted(nums)\n"
            "    out = []\n"
            "    for i in range(len(nums) - 2):\n"
            "        if i > 0 and nums[i] == nums[i - 1]:\n"
            "            continue\n"
            "        left, right = i + 1, len(nums) - 1\n"
            "        while left < right:\n"
            "            total = nums[i] + nums[left] + nums[right]\n"
            "            if total < 0:\n"
            "                left += 1\n"
            "            elif total > 0:\n"
            "                right -= 1\n"
            "            else:\n"
            "                out.append([nums[i], nums[left], nums[right]])\n"
            "                left += 1\n"
            "                while left < right and nums[left] == nums[left - 1]:\n"
            "                    left += 1\n"
            "    return out"
        ),
        tests=[
            example([[-1, 0, 1, 2, -1, -4]], [[-1, -1, 2], [-1, 0, 1]]),
            example([[0, 1, 1]], []),
            hidden("an empty bin", [[]], []),
            hidden("three zeroes", [[0, 0, 0]], [[0, 0, 0]]),
            hidden("three separate triplets", [[3, 0, -2, -1, 1, 2]],
                   [[-2, -1, 3], [-2, 0, 2], [-1, 0, 1]]),
            hidden("nothing cancels out", [[1, 2, -2, -1]], []),
            hidden("a repeat that must not double up", [[-2, 0, 1, 1, 2]],
                   [[-2, 0, 2], [-2, 1, 1]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="container-with-most-water",
        title="Container With Most Water",
        difficulty="medium",
        prompt=(
            "Two of the toy fence posts will hold the most bathwater between them. The water "
            "level is capped by the shorter post, and the width is how far apart they stand. "
            "Return the largest volume."
        ),
        example_input="height = [1, 8, 6, 2, 5, 4, 8, 3, 7]",
        example_output="49",
        entrypoint="maxArea",
        signature=sig("int", height="list<int>"),
        explainer=(
            "**Move the shorter post.** Start with the widest pair. Narrowing always costs "
            "width, so it's only worth it if the height can go up — and the height is capped by "
            "the shorter post, so that's the one to move. The taller one has nothing to gain."
        ),
        hint=(
            "Trying every pair is O(n²) and will pass the small cases. The two-pointer walk is "
            "O(n): move whichever post is shorter, and never look back."
        ),
        approach=(
            "1) left = 0, right = len(height) - 1, best = 0. 2) best = max(best, "
            "min(height[left], height[right]) * (right - left)). 3) Move whichever side is "
            "shorter inward. 4) Return best. O(n) time, O(1) space."
        ),
        solution=(
            "def maxArea(height):\n"
            "    left, right = 0, len(height) - 1\n"
            "    best = 0\n"
            "    while left < right:\n"
            "        best = max(best, min(height[left], height[right]) * (right - left))\n"
            "        if height[left] < height[right]:\n"
            "            left += 1\n"
            "        else:\n"
            "            right -= 1\n"
            "    return best"
        ),
        tests=[
            example([[1, 8, 6, 2, 5, 4, 8, 3, 7]], 49),
            example([[1, 1]], 1),
            hidden("no posts at all", [[]], 0),
            hidden("the two ends win", [[4, 3, 2, 1, 4]], 16),
            hidden("a tall post in the middle helps nobody", [[1, 2, 1]], 2),
            hidden("narrow beats wide", [[1, 2, 4, 3]], 4),
            hidden("two tall posts side by side", [[2, 3, 4, 5, 18, 17, 6]], 17),
        ],
    ),
    problem(
        zone=ZONE,
        slug="trapping-rain-water",
        title="Trapping Rain Water",
        difficulty="hard",
        prompt=(
            "Rain falls on a row of toy blocks of different heights. Water pools in every dip "
            "that has something taller on both sides. Return how many units are trapped."
        ),
        example_input="height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]",
        example_output="6",
        entrypoint="trap",
        signature=sig("int", height="list<int>"),
        explainer=(
            "**Each column, on its own.** The water standing on top of one block is the shorter "
            "of the tallest block to its left and the tallest to its right, minus the block "
            "itself. Add that up across the row and you're done."
        ),
        hint=(
            "Two pointers with a running left-max and right-max gets it in one pass: whichever "
            "side's max is smaller is the side whose answer is already settled, so move that one."
        ),
        approach=(
            "1) left, right = 0, len - 1; leftMax = rightMax = the two end heights; total = 0. "
            "2) While left < right: if leftMax < rightMax, step left in, refresh leftMax and add "
            "leftMax - height[left]; else do the mirror image on the right. 3) Return total. "
            "O(n) time, O(1) space."
        ),
        solution=(
            "def trap(height):\n"
            "    if not height:\n"
            "        return 0\n"
            "    left, right = 0, len(height) - 1\n"
            "    left_max, right_max = height[left], height[right]\n"
            "    total = 0\n"
            "    while left < right:\n"
            "        if left_max < right_max:\n"
            "            left += 1\n"
            "            left_max = max(left_max, height[left])\n"
            "            total += left_max - height[left]\n"
            "        else:\n"
            "            right -= 1\n"
            "            right_max = max(right_max, height[right])\n"
            "            total += right_max - height[right]\n"
            "    return total"
        ),
        tests=[
            example([[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], 6),
            example([[4, 2, 0, 3, 2, 5]], 9),
            hidden("no blocks", [[]], 0),
            hidden("one block holds nothing", [[3]], 0),
            hidden("the smallest possible dip", [[2, 0, 2]], 2),
            hidden("a downhill run", [[5, 4, 3, 2, 1]], 0),
            hidden("an uphill run", [[1, 2, 3, 4, 5]], 0),
        ],
    ),
]

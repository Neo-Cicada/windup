"""Building Blocks — Arrays & Hashing.

The first corner of the map, and the one everything after it leans on: walk a
row of blocks once, and remember what you saw in a dictionary so you never have
to walk it again.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "building-blocks"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="two-sum",
        title="Two Sum",
        difficulty="easy",
        prompt=(
            "Two blocks in the bin snap together to make exactly the height Sprocket needs. "
            "Given a list of block heights and a target, return the indices of the two blocks "
            "that add up to it."
        ),
        example_input="nums = [2, 7, 11, 15], target = 9",
        example_output="[0, 1]",
        entrypoint="twoSum",
        signature=sig("list<int>", nums="list<int>", target="int"),
        explainer=(
            "**Complement lookup.** Walk the bin once. For each block, ask 'which block would "
            "finish this tower?' — that's target - height. Keep every block you've seen in a "
            "dictionary so the question is answered in O(1)."
        ),
        hint=(
            "You don't need two loops. Store each height you've already seen in a dict keyed by "
            "height, valued by index, and check for the complement *before* you insert."
        ),
        approach=(
            "1) seen = {}. 2) For i, n in enumerate(nums): 3) need = target - n. "
            "4) If need in seen: return [seen[need], i]. 5) seen[n] = i. "
            "One pass, O(n) time, O(n) space."
        ),
        solution=(
            "def twoSum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        need = target - n\n"
            "        if need in seen:\n"
            "            return [seen[need], i]\n"
            "        seen[n] = i\n"
            "    return []"
        ),
        # Every case has exactly one valid pair, so comparing indices is fair.
        tests=[
            example([[2, 7, 11, 15], 9], [0, 1]),
            example([[3, 2, 4], 6], [1, 2]),
            hidden("duplicate blocks", [[3, 3], 6], [0, 1]),
            hidden("negative heights", [[-1, -2, -3, -4, -5], -8], [2, 4]),
            hidden("zeroes", [[0, 4, 3, 0], 0], [0, 3]),
            hidden("pair at the far end", [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 19], [8, 9]),
            hidden("skips the first block", [[5, 75, 25], 100], [1, 2]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="valid-anagram",
        title="Valid Anagram",
        difficulty="easy",
        prompt=(
            "Two alphabet-block words got shuffled in the toy chest. Decide whether one is a "
            "rearrangement of the other."
        ),
        example_input='s = "anagram", t = "nagaram"',
        example_output="true",
        entrypoint="isAnagram",
        signature=sig("bool", s="string", t="string"),
        explainer=(
            "**Count the blocks.** Anagrams use the same letters the same number of times, so "
            "compare letter counts rather than order."
        ),
        hint="Different lengths can never be anagrams — bail out early, then count with a dict.",
        approach=(
            "1) If len(s) != len(t): return False. 2) Tally each letter of s in a Counter. "
            "3) Decrement for each letter of t; if any count dips below zero, return False. "
            "4) Return True. O(n) time, O(1) space for a fixed alphabet."
        ),
        solution=(
            "from collections import Counter\n\n"
            "def isAnagram(s, t):\n"
            "    return len(s) == len(t) and Counter(s) == Counter(t)"
        ),
        tests=[
            example(["anagram", "nagaram"], True),
            example(["rat", "car"], False),
            hidden("two empty words", ["", ""], True),
            hidden("different lengths", ["a", "ab"], False),
            hidden("same letters, wrong counts", ["aacc", "ccac"], False),
            hidden("classic pair", ["listen", "silent"], True),
            hidden("two letters", ["ab", "ba"], True),
        ],
    ),
    problem(
        zone=ZONE,
        slug="contains-duplicate",
        title="Contains Duplicate",
        difficulty="easy",
        prompt=(
            "Every block in the bin is meant to be a different height. Say whether any height "
            "turns up twice."
        ),
        example_input="nums = [1, 2, 3, 1]",
        example_output="true",
        entrypoint="containsDuplicate",
        signature=sig("bool", nums="list<int>"),
        explainer=(
            "**A set remembers for you.** Tip the blocks into a set, which throws duplicates "
            "away, and see whether anything went missing."
        ),
        hint=(
            "Comparing every block against every other is O(n²). A set gets you the same answer "
            "in one pass — or compare len(set(nums)) with len(nums)."
        ),
        approach=(
            "1) seen = set(). 2) For n in nums: if n in seen, return True; else add it. "
            "3) Return False. O(n) time, O(n) space — and it stops at the first repeat rather "
            "than always reading the whole bin."
        ),
        solution=(
            "def containsDuplicate(nums):\n"
            "    seen = set()\n"
            "    for n in nums:\n"
            "        if n in seen:\n"
            "            return True\n"
            "        seen.add(n)\n"
            "    return False"
        ),
        tests=[
            example([[1, 2, 3, 1]], True),
            example([[1, 2, 3, 4]], False),
            hidden("an empty bin", [[]], False),
            hidden("one block", [[7]], False),
            hidden("every block the same", [[2, 2, 2, 2]], True),
            hidden("the repeat is at the very end", [[1, 2, 3, 4, 5, 6, 7, 8, 9, 1]], True),
            hidden("negatives and a zero", [[-1, 0, 1, -2]], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="group-anagrams",
        title="Group Anagrams",
        difficulty="medium",
        prompt=(
            "Sort the alphabet-block words into piles, one pile per set of letters, so every "
            "word in a pile is a rearrangement of the others. Return the piles."
        ),
        example_input='strs = ["eat", "tea", "tan", "ate", "nat", "bat"]',
        example_output='[["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]',
        entrypoint="groupAnagrams",
        signature=sig("matrix<string>", strs="list<string>"),
        # Any order of the piles, and any order inside a pile, is the same answer.
        compare_mode="unordered_deep",
        explainer=(
            "**Give each pile a label.** Two words belong together exactly when they have the "
            "same letters, so build a key that ignores order — the sorted letters, or a count "
            "of each — and let a dictionary do the grouping."
        ),
        hint=(
            "The key has to be hashable, so a sorted *string* works where a sorted list won't. "
            "Piles can come back in any order, and so can the words inside them."
        ),
        approach=(
            "1) piles = defaultdict(list). 2) For each word, key = ''.join(sorted(word)). "
            "3) piles[key].append(word). 4) Return list(piles.values()). "
            "O(n·k log k) for n words of length k."
        ),
        solution=(
            "from collections import defaultdict\n\n"
            "def groupAnagrams(strs):\n"
            "    piles = defaultdict(list)\n"
            "    for word in strs:\n"
            "        piles[''.join(sorted(word))].append(word)\n"
            "    return list(piles.values())"
        ),
        tests=[
            example(
                [["eat", "tea", "tan", "ate", "nat", "bat"]],
                [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]],
            ),
            example([["a"]], [["a"]]),
            hidden("no words at all", [[]], []),
            hidden("the empty word is its own pile", [[""]], [[""]]),
            hidden(
                "two piles of three",
                [["abc", "bca", "cab", "xyz", "zyx", "yxz"]],
                [["abc", "bca", "cab"], ["xyz", "zyx", "yxz"]],
            ),
            hidden(
                "same letters, different counts",
                [["ddddddddddg", "dgggggggggg"]],
                [["ddddddddddg"], ["dgggggggggg"]],
            ),
            hidden(
                "every word alone",
                [["cat", "dog", "bird"]],
                [["cat"], ["dog"], ["bird"]],
            ),
        ],
    ),
    problem(
        zone=ZONE,
        slug="top-k-frequent-elements",
        title="Top K Frequent Elements",
        difficulty="medium",
        prompt=(
            "Which block heights come out of the bin most often? Given the heights and a number "
            "k, return the k heights that appear most frequently."
        ),
        example_input="nums = [1, 1, 1, 2, 2, 3], k = 2",
        example_output="[1, 2]",
        entrypoint="topKFrequent",
        signature=sig("list<int>", nums="list<int>", k="int"),
        # The k winners are unambiguous in every case; their order is not.
        compare_mode="unordered",
        explainer=(
            "**Count, then bucket.** Tally how often each height appears, then put each height "
            "in the bucket numbered by its count. Counts can't exceed the number of blocks, so "
            "walking the buckets from the back gives you the winners without ever sorting."
        ),
        hint=(
            "Sorting the counts is O(n log n) and perfectly acceptable. Bucketing by count gets "
            "it to O(n) — there are only len(nums) + 1 possible counts."
        ),
        approach=(
            "1) counts = Counter(nums). 2) buckets = [[] for _ in range(len(nums) + 1)]; "
            "for value, c in counts.items(): buckets[c].append(value). 3) Walk buckets from the "
            "end, collecting until you have k. O(n) time and space."
        ),
        solution=(
            "from collections import Counter\n\n"
            "def topKFrequent(nums, k):\n"
            "    counts = Counter(nums)\n"
            "    buckets = [[] for _ in range(len(nums) + 1)]\n"
            "    for value, count in counts.items():\n"
            "        buckets[count].append(value)\n"
            "    out = []\n"
            "    for count in range(len(buckets) - 1, 0, -1):\n"
            "        for value in buckets[count]:\n"
            "            out.append(value)\n"
            "            if len(out) == k:\n"
            "                return out\n"
            "    return out"
        ),
        tests=[
            example([[1, 1, 1, 2, 2, 3], 2], [1, 2]),
            example([[1], 1], [1]),
            hidden("one height, many blocks", [[5, 5, 5, 5], 1], [5]),
            hidden("k covers everything", [[1, 2, 3, 4], 4], [1, 2, 3, 4]),
            hidden("negatives count too", [[-1, -1, 2, 2, 3], 2], [-1, 2]),
            hidden("a clear third place left out", [[7, 7, 8, 8, 9], 2], [7, 8]),
            hidden(
                "three tiers",
                [[4, 4, 4, 4, 5, 5, 5, 6, 6, 7], 3],
                [4, 5, 6],
            ),
        ],
    ),
]

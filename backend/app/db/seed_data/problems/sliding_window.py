"""Peek-a-Boo Window — Sliding Window.

A frame that slides along the row, growing at the front and shrinking at the
back. What makes it a pattern rather than two loops is that the back pointer
only ever moves forwards: everything the window has already ruled out stays
ruled out.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "peek-a-boo"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="best-time-to-buy-and-sell-stock",
        title="Best Time to Buy and Sell",
        difficulty="easy",
        prompt=(
            "The price of a wind-up toy was written down each day at the swap meet. Buy on one "
            "day and sell on a later one. Return the biggest profit possible, or 0 if every "
            "trade would lose money."
        ),
        example_input="prices = [7, 1, 5, 3, 6, 4]",
        example_output="5",
        entrypoint="maxProfit",
        signature=sig("int", prices="list<int>"),
        explainer=(
            "**Remember the cheapest day so far.** Walk forwards. At each day, the best you "
            "could have done selling *today* is today's price minus the cheapest day behind "
            "you — so keep that cheapest price and the best profit as you go."
        ),
        hint=(
            "One pass, two variables. You never need to look backwards, because the cheapest "
            "day behind you is the only thing about the past that matters."
        ),
        approach=(
            "1) cheapest = infinity, best = 0. 2) For each price: cheapest = min(cheapest, "
            "price); best = max(best, price - cheapest). 3) Return best. O(n) time, O(1) space."
        ),
        solution=(
            "def maxProfit(prices):\n"
            "    cheapest = float('inf')\n"
            "    best = 0\n"
            "    for price in prices:\n"
            "        cheapest = min(cheapest, price)\n"
            "        best = max(best, price - cheapest)\n"
            "    return best"
        ),
        tests=[
            example([[7, 1, 5, 3, 6, 4]], 5),
            example([[7, 6, 4, 3, 1]], 0),
            hidden("no days at all", [[]], 0),
            hidden("a single day", [[1]], 0),
            hidden("the peak comes before the dip", [[2, 4, 1]], 2),
            hidden("the price never moves", [[3, 3, 3]], 0),
            hidden("straight up", [[1, 2, 3, 4, 5]], 4),
        ],
    ),
    problem(
        zone=ZONE,
        slug="longest-substring-without-repeating",
        title="Longest Substring Without Repeats",
        difficulty="medium",
        prompt=(
            "Slide the peek-a-boo window along a row of letter beads and find the longest "
            "stretch you can see through it with no bead repeated. Return its length."
        ),
        example_input='s = "abcabcbb"',
        example_output="3",
        entrypoint="lengthOfLongestSubstring",
        signature=sig("int", s="string"),
        explainer=(
            "**When a bead repeats, jump the back of the window past its first copy.** The "
            "window always holds a stretch with no repeats; a repeat arriving is the only thing "
            "that can break that, and the smallest fix is to drop everything up to and "
            "including the earlier copy."
        ),
        hint=(
            "Store the last index of each bead in a dict. When you meet a bead you've seen, "
            "only jump the back pointer *forwards* — an old sighting from before the window "
            "must not drag it backwards."
        ),
        approach=(
            "1) last = {}, left = 0, best = 0. 2) For i, ch in enumerate(s): if ch in last and "
            "last[ch] >= left: left = last[ch] + 1. 3) last[ch] = i; best = max(best, i - left "
            "+ 1). 4) Return best. O(n) time."
        ),
        solution=(
            "def lengthOfLongestSubstring(s):\n"
            "    last = {}\n"
            "    left = 0\n"
            "    best = 0\n"
            "    for i, ch in enumerate(s):\n"
            "        if ch in last and last[ch] >= left:\n"
            "            left = last[ch] + 1\n"
            "        last[ch] = i\n"
            "        best = max(best, i - left + 1)\n"
            "    return best"
        ),
        tests=[
            example(["abcabcbb"], 3),
            example(["bbbbb"], 1),
            hidden("no beads", [""], 0),
            hidden("a single space counts", [" "], 1),
            hidden("the repeat is not at the edge", ["pwwkew"], 3),
            hidden("an old sighting must not drag the window back", ["dvdf"], 3),
            hidden("a repeat either side", ["abba"], 2),
        ],
    ),
    problem(
        zone=ZONE,
        slug="longest-repeating-character-replacement",
        title="Longest Repeating Character Replacement",
        difficulty="medium",
        prompt=(
            "You may swap out up to k beads on the string for any letter you like. Return the "
            "length of the longest run of identical beads you can end up with."
        ),
        example_input='s = "ABAB", k = 2',
        example_output="4",
        entrypoint="characterReplacement",
        signature=sig("int", s="string", k="int"),
        explainer=(
            "**A window is legal when everything that isn't the majority bead fits in k.** So "
            "the test is `window length - count of the commonest bead <= k`. Grow the window at "
            "the front; when the test fails, nudge the back along."
        ),
        hint=(
            "You don't have to recompute the commonest bead when the window shrinks. Letting "
            "that count drift high only ever makes the window refuse to grow — it can never "
            "report an answer that's too big."
        ),
        approach=(
            "1) counts = {}, left = 0, most = 0, best = 0. 2) For each bead: bump its count and "
            "`most`. 3) While (i - left + 1) - most > k: drop s[left], left += 1. 4) best = "
            "max(best, i - left + 1). O(n) time, O(alphabet) space."
        ),
        solution=(
            "def characterReplacement(s, k):\n"
            "    counts = {}\n"
            "    left = 0\n"
            "    most = 0\n"
            "    best = 0\n"
            "    for i, ch in enumerate(s):\n"
            "        counts[ch] = counts.get(ch, 0) + 1\n"
            "        most = max(most, counts[ch])\n"
            "        while (i - left + 1) - most > k:\n"
            "            counts[s[left]] -= 1\n"
            "            left += 1\n"
            "        best = max(best, i - left + 1)\n"
            "    return best"
        ),
        tests=[
            example(["ABAB", 2], 4),
            example(["AABABBA", 1], 4),
            hidden("no beads", ["", 0], 0),
            hidden("one bead, no swaps", ["A", 0], 1),
            hidden("already all one letter", ["AAAA", 2], 4),
            hidden("all different, one swap", ["ABCDE", 1], 2),
            hidden("no swaps allowed", ["AABA", 0], 2),
        ],
    ),
    problem(
        zone=ZONE,
        slug="permutation-in-string",
        title="Permutation in String",
        difficulty="medium",
        prompt=(
            "Does some stretch of the second bead string use exactly the beads of the first, in "
            "any order? Say yes or no."
        ),
        example_input='s1 = "ab", s2 = "eidbaooo"',
        example_output="true",
        entrypoint="checkInclusion",
        signature=sig("bool", s1="string", s2="string"),
        explainer=(
            "**The window never changes size.** A rearrangement of s1 is exactly len(s1) beads "
            "long, so slide a frame of that width along s2 and ask whether its bead counts "
            "match s1's."
        ),
        hint=(
            "Don't rebuild the counts at every position. Sliding one step adds one bead and "
            "removes one — two updates, not a whole recount."
        ),
        approach=(
            "1) If len(s1) > len(s2): return False. 2) need = Counter(s1); window = "
            "Counter(first len(s1) beads). 3) Slide: add the new bead, drop the old, and delete "
            "any count that hits zero so the dicts compare equal. 4) Return True on a match. "
            "O(n) time."
        ),
        solution=(
            "from collections import Counter\n\n"
            "def checkInclusion(s1, s2):\n"
            "    width = len(s1)\n"
            "    if width > len(s2):\n"
            "        return False\n"
            "    need = Counter(s1)\n"
            "    window = Counter(s2[:width])\n"
            "    if window == need:\n"
            "        return True\n"
            "    for i in range(width, len(s2)):\n"
            "        window[s2[i]] += 1\n"
            "        leaving = s2[i - width]\n"
            "        window[leaving] -= 1\n"
            "        if window[leaving] == 0:\n"
            "            del window[leaving]\n"
            "        if window == need:\n"
            "            return True\n"
            "    return False"
        ),
        tests=[
            example(["ab", "eidbaooo"], True),
            example(["ab", "eidboaoo"], False),
            hidden("right at the end", ["abc", "bbbca"], True),
            hidden("all the beads are there but never together", ["hello", "ooolleoooleh"], False),
            hidden("one bead, exact match", ["a", "a"], True),
            hidden("the needle is longer than the haystack", ["ab", "a"], False),
            hidden("the match starts at the first bead", ["adc", "dcda"], True),
        ],
    ),
    problem(
        zone=ZONE,
        slug="minimum-window-substring",
        title="Minimum Window Substring",
        difficulty="hard",
        prompt=(
            "Find the shortest stretch of the first bead string that contains every bead of the "
            "second, counting repeats. Return that stretch, or an empty string if there isn't "
            "one. There is never more than one shortest answer."
        ),
        example_input='s = "ADOBECODEBANC", t = "ABC"',
        example_output='"BANC"',
        entrypoint="minWindow",
        signature=sig("string", s="string", t="string"),
        explainer=(
            "**Grow until it's valid, then shrink while it stays valid.** Push the front along "
            "until the window covers everything t needs, then pull the back in as far as it "
            "will go. Record the width, then push the front again."
        ),
        hint=(
            "One counter does it: start it at the needs of t, and let it go negative for beads "
            "the window has spare. A single `missing` total tells you when the window is valid "
            "without comparing dicts."
        ),
        approach=(
            "1) need = Counter(t), missing = len(t). 2) For each bead at j: if need[bead] > 0, "
            "missing -= 1; need[bead] -= 1. 3) When missing == 0, advance i past every bead the "
            "window has spare, then score j - i. 4) Return the best slice. O(len(s)) time."
        ),
        solution=(
            "from collections import Counter\n\n"
            "def minWindow(s, t):\n"
            "    if not s or not t:\n"
            "        return ''\n"
            "    need = Counter(t)\n"
            "    missing = len(t)\n"
            "    start = end = 0\n"
            "    best = len(s) + 1\n"
            "    left = 0\n"
            "    for right, ch in enumerate(s, 1):\n"
            "        if need[ch] > 0:\n"
            "            missing -= 1\n"
            "        need[ch] -= 1\n"
            "        if missing == 0:\n"
            "            while need[s[left]] < 0:\n"
            "                need[s[left]] += 1\n"
            "                left += 1\n"
            "            if right - left < best:\n"
            "                best = right - left\n"
            "                start, end = left, right\n"
            "    return s[start:end]"
        ),
        tests=[
            example(["ADOBECODEBANC", "ABC"], "BANC"),
            example(["a", "a"], "a"),
            hidden("not enough copies", ["a", "aa"], ""),
            hidden("nothing to search", ["", "a"], ""),
            hidden("a single bead somewhere inside", ["ab", "b"], "b"),
            hidden("the whole string is the answer", ["aa", "aa"], "aa"),
            hidden("the answer is at the end, out of order", ["bba", "ab"], "ba"),
        ],
    ),
]

"""Piggy Bank — Greedy.

Take the best coin in front of you and never look back. The catch is that this is
usually *wrong*, and every problem here is really an argument about why it
happens to be right — a running total that can be reset, a reach that only ever
grows, a shortfall that has to be made up somewhere.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "piggy-bank"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="maximum-subarray",
        title="Maximum Subarray",
        difficulty="medium",
        prompt=(
            "A run of days added or took away play-coins from the piggy bank. Find the "
            "consecutive stretch of days that gained the most, and return that total. The "
            "stretch has to hold at least one day."
        ),
        example_input="nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]",
        example_output="6",
        entrypoint="maxSubArray",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**A negative running total is worth less than nothing.** Carry a total as you "
            "walk. If it ever drops below the day you're standing on, the days behind you were "
            "a liability — throw them away and start the stretch here."
        ),
        hint=(
            "`current = max(n, current + n)` is the whole decision. Track the best separately: "
            "the running total is allowed to dip after the best stretch has already passed."
        ),
        approach=(
            "1) best = current = nums[0]. 2) For each later n: current = max(n, current + n); "
            "best = max(best, current). 3) Return best. O(n) time, O(1) space — Kadane's "
            "algorithm."
        ),
        solution=(
            "def maxSubArray(nums):\n"
            "    if not nums:\n"
            "        return 0\n"
            "    best = current = nums[0]\n"
            "    for n in nums[1:]:\n"
            "        current = max(n, current + n)\n"
            "        best = max(best, current)\n"
            "    return best"
        ),
        tests=[
            example([[-2, 1, -3, 4, -1, 2, 1, -5, 4]], 6),
            example([[5, 4, -1, 7, 8]], 23),
            hidden("no days", [[]], 0),
            hidden("a single good day", [[1]], 1),
            hidden("a single bad day", [[-1]], -1),
            hidden("every day loses coins", [[-2, -3, -1]], -1),
            hidden("nothing is worth continuing", [[1, -1, 1, -1, 1]], 1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="jump-game",
        title="Jump Game",
        difficulty="medium",
        prompt=(
            "The hopping toy starts on the first square. Each square says the *most* squares it "
            "can hop forward. Say whether the last square can be reached."
        ),
        example_input="nums = [2, 3, 1, 1, 4]",
        example_output="true",
        entrypoint="canJump",
        signature=sig("bool", nums="list<int>"),
        explainer=(
            "**Track how far you could possibly get.** Walk the squares in order, keeping the "
            "furthest reachable index. If you ever stand on a square beyond that reach, "
            "nothing behind you could have carried you here — so the answer is no."
        ),
        hint=(
            "You never need to decide *which* jump to take. Only the maximum reach matters, "
            "because a shorter hop from the same square is always available too."
        ),
        approach=(
            "1) reach = 0. 2) For i, n in enumerate(nums): if i > reach, return False; reach = "
            "max(reach, i + n). 3) Return True. O(n) time, O(1) space."
        ),
        solution=(
            "def canJump(nums):\n"
            "    reach = 0\n"
            "    for i, n in enumerate(nums):\n"
            "        if i > reach:\n"
            "            return False\n"
            "        reach = max(reach, i + n)\n"
            "    return True"
        ),
        tests=[
            example([[2, 3, 1, 1, 4]], True),
            example([[3, 2, 1, 0, 4]], False),
            hidden("already on the last square", [[0]], True),
            hidden("no squares at all", [[]], True),
            hidden("one hop is enough", [[1, 0]], True),
            hidden("stuck on the first square", [[0, 1]], False),
            hidden("a long first hop clears the zeroes", [[2, 0, 0]], True),
        ],
    ),
    problem(
        zone=ZONE,
        slug="jump-game-ii",
        title="Jump Game II",
        difficulty="medium",
        prompt=(
            "Same hopping toy, same squares, and the last one is always reachable. Return the "
            "fewest hops it takes to get there."
        ),
        example_input="nums = [2, 3, 1, 1, 4]",
        example_output="2",
        entrypoint="jump",
        signature=sig("int", nums="list<int>"),
        explainer=(
            "**Squares fall into layers, like a breadth-first walk.** Everything reachable in "
            "one hop is layer one, everything reachable from those is layer two. Walk forwards, "
            "and every time you step past the end of the current layer, that's one more hop."
        ),
        hint=(
            "Two markers: the end of the layer you're in, and the furthest anything in it can "
            "reach. Stop the loop one square early — arriving at the last square doesn't cost "
            "another hop."
        ),
        approach=(
            "1) hops = end = furthest = 0. 2) For i in 0..len-2: furthest = max(furthest, i + "
            "nums[i]); if i == end: hops += 1, end = furthest. 3) Return hops. O(n)."
        ),
        solution=(
            "def jump(nums):\n"
            "    hops = end = furthest = 0\n"
            "    for i in range(len(nums) - 1):\n"
            "        furthest = max(furthest, i + nums[i])\n"
            "        if i == end:\n"
            "            hops += 1\n"
            "            end = furthest\n"
            "    return hops"
        ),
        tests=[
            example([[2, 3, 1, 1, 4]], 2),
            example([[2, 3, 0, 1, 4]], 2),
            hidden("already there", [[0]], 0),
            hidden("one square", [[1]], 0),
            hidden("one square at a time", [[1, 1, 1, 1]], 3),
            hidden("a single enormous hop", [[5, 1, 1, 1, 1]], 1),
            hidden("the greedy layer wins", [[1, 2, 3]], 2),
        ],
    ),
    problem(
        zone=ZONE,
        slug="gas-station",
        title="Gas Station",
        difficulty="medium",
        prompt=(
            "The wind-up car drives a circular track of filling stations. At station i it picks "
            "up gas[i] and spends cost[i] getting to the next one. Return the station it must "
            "start at to make it all the way round, or -1 if no station works. There is never "
            "more than one answer."
        ),
        example_input="gas = [1, 2, 3, 4, 5], cost = [3, 4, 5, 1, 2]",
        example_output="3",
        entrypoint="canCompleteCircuit",
        signature=sig("int", gas="list<int>", cost="list<int>"),
        explainer=(
            "**Two separate facts.** If the total gas is less than the total cost, no start "
            "works — that settles the -1. And if the tank runs dry partway, no station in the "
            "stretch you just drove could have been the start either, so the next one is the "
            "only candidate left."
        ),
        hint=(
            "One pass does both. Keep a running tank; when it goes negative, reset it to 0 and "
            "move the candidate start to the next station."
        ),
        approach=(
            "1) If sum(gas) < sum(cost): return -1. 2) start = tank = 0. 3) For each i: tank += "
            "gas[i] - cost[i]; if tank < 0: start = i + 1, tank = 0. 4) Return start. O(n)."
        ),
        solution=(
            "def canCompleteCircuit(gas, cost):\n"
            "    if sum(gas) < sum(cost):\n"
            "        return -1\n"
            "    start = tank = 0\n"
            "    for i in range(len(gas)):\n"
            "        tank += gas[i] - cost[i]\n"
            "        if tank < 0:\n"
            "            start = i + 1\n"
            "            tank = 0\n"
            "    return start"
        ),
        tests=[
            example([[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], 3),
            example([[2, 3, 4], [3, 4, 3]], -1),
            hidden("one station with gas to spare", [[5], [4]], 0),
            hidden("one station that can't make it", [[1], [2]], -1),
            hidden("the first station works", [[3, 1, 1], [1, 2, 2]], 0),
            hidden("the last station works", [[2, 0, 0, 2], [0, 1, 3, 0]], 3),
            hidden("not enough gas anywhere",
                   [[4, 5, 2, 6, 5, 3], [3, 2, 7, 3, 2, 9]], -1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="partition-labels",
        title="Partition Labels",
        difficulty="medium",
        prompt=(
            "Cut a string of sticker letters into as many pieces as possible, so that no letter "
            "appears in two different pieces. Return the length of each piece, in order."
        ),
        example_input='s = "ababcbacadefegdehijhklij"',
        example_output="[9, 7, 8]",
        entrypoint="partitionLabels",
        signature=sig("list<int>", s="list<string>"),
        starter_code="def partitionLabels(s):\n    # your turn, little toy…\n    pass",
        explainer=(
            "**A piece can't end before its letters do.** Note the last position of every "
            "letter first. Then walk forwards keeping the furthest last-position you've seen; "
            "the moment you stand on it, nothing in this piece appears later, so cut."
        ),
        hint=(
            "One pass to record the last index of each letter, one pass to cut. The greedy "
            "part is cutting the *instant* you're allowed to — waiting can only make fewer, "
            "bigger pieces."
        ),
        approach=(
            "1) last = {letter: final index}. 2) start = end = 0. 3) For i, ch: end = "
            "max(end, last[ch]); if i == end: record end - start + 1 and set start = i + 1. "
            "O(n) time."
        ),
        solution=(
            "def partitionLabels(s):\n"
            "    last = {ch: i for i, ch in enumerate(s)}\n"
            "    out = []\n"
            "    start = end = 0\n"
            "    for i, ch in enumerate(s):\n"
            "        end = max(end, last[ch])\n"
            "        if i == end:\n"
            "            out.append(end - start + 1)\n"
            "            start = i + 1\n"
            "    return out"
        ),
        # The letters travel as a list of one-character strings rather than one
        # string, because `s[i]` in a compiled language is a byte, not a letter.
        tests=[
            example([list("ababcbacadefegdehijhklij")], [9, 7, 8]),
            example([list("eccbbbbdec")], [10]),
            hidden("a single sticker", [list("a")], [1]),
            hidden("no stickers", [[]], []),
            hidden("every letter is its own piece", [list("abc")], [1, 1, 1]),
            hidden("two letters that interleave", [list("abab")], [4]),
            hidden("a repeat right at the end", [list("abcabc")], [6]),
        ],
    ),
]

"""Train Track — Intervals.

Straight pieces of track laid along a line, each with a start and an end. Four of
these five begin with a sort, and which key you sort on is the entire decision:
by start to merge things, by end to keep as many as possible.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "train-track"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="merge-intervals",
        title="Merge Intervals",
        difficulty="medium",
        prompt=(
            "Pieces of track overlap along the playroom floor. Fuse every group that touches "
            "into one piece and return what's left, in order."
        ),
        example_input="intervals = [[1, 3], [2, 6], [8, 10], [15, 18]]",
        example_output="[[1, 6], [8, 10], [15, 18]]",
        entrypoint="merge",
        signature=sig("matrix<int>", intervals="matrix<int>"),
        explainer=(
            "**Sort by start, then only ever look at the last piece you kept.** In start order, "
            "a new piece can only overlap the one you most recently laid down — everything "
            "before that ended even earlier."
        ),
        hint=(
            "Touching counts as overlapping: [1, 4] and [4, 5] fuse into [1, 5]. So the test is "
            "`start <= last_end`, not `<`."
        ),
        approach=(
            "1) Sort by start. 2) For each piece: if it starts at or before the last kept "
            "piece's end, stretch that end to the max of the two; otherwise append it. "
            "O(n log n) for the sort."
        ),
        solution=(
            "def merge(intervals):\n"
            "    out = []\n"
            "    for start, end in sorted(intervals):\n"
            "        if out and start <= out[-1][1]:\n"
            "            out[-1][1] = max(out[-1][1], end)\n"
            "        else:\n"
            "            out.append([start, end])\n"
            "    return out"
        ),
        tests=[
            example([[[1, 3], [2, 6], [8, 10], [15, 18]]], [[1, 6], [8, 10], [15, 18]]),
            example([[[1, 4], [4, 5]]], [[1, 5]]),
            hidden("no track at all", [[]], []),
            hidden("a single piece", [[[1, 4]]], [[1, 4]]),
            hidden("one piece swallows another", [[[1, 4], [2, 3]]], [[1, 4]]),
            hidden("given out of order", [[[5, 6], [1, 2]]], [[1, 2], [5, 6]]),
            hidden("one long piece covers everything",
                   [[[1, 10], [2, 3], [4, 5], [6, 7]]], [[1, 10]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="insert-interval",
        title="Insert Interval",
        difficulty="medium",
        prompt=(
            "The track pieces are already sorted and none of them overlap. Slot one more piece "
            "in, fusing whatever it touches, and return the track."
        ),
        example_input="intervals = [[1, 3], [6, 9]], newInterval = [2, 5]",
        example_output="[[1, 5], [6, 9]]",
        entrypoint="insert",
        signature=sig("matrix<int>", intervals="matrix<int>", newInterval="list<int>"),
        explainer=(
            "**Three runs, in order.** Everything that ends before the new piece starts is "
            "copied straight over. Everything that overlaps gets absorbed into it. Everything "
            "left is copied over too. No sort needed — the input already is one."
        ),
        hint=(
            "Absorbing means widening the new piece on both sides: its start becomes the "
            "smallest start it touched, its end the largest end."
        ),
        approach=(
            "1) Copy pieces whose end < the new start. 2) While the next piece starts at or "
            "before the new end, widen the new piece and skip it. 3) Append the widened piece, "
            "then the rest. O(n)."
        ),
        solution=(
            "def insert(intervals, newInterval):\n"
            "    start, end = newInterval\n"
            "    out = []\n"
            "    i = 0\n"
            "    while i < len(intervals) and intervals[i][1] < start:\n"
            "        out.append(intervals[i])\n"
            "        i += 1\n"
            "    while i < len(intervals) and intervals[i][0] <= end:\n"
            "        start = min(start, intervals[i][0])\n"
            "        end = max(end, intervals[i][1])\n"
            "        i += 1\n"
            "    out.append([start, end])\n"
            "    out.extend(intervals[i:])\n"
            "    return out"
        ),
        tests=[
            example([[[1, 3], [6, 9]], [2, 5]], [[1, 5], [6, 9]]),
            example([[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]],
                    [[1, 2], [3, 10], [12, 16]]),
            hidden("onto an empty floor", [[], [5, 7]], [[5, 7]]),
            hidden("swallowed whole", [[[1, 5]], [2, 3]], [[1, 5]]),
            hidden("goes on the end", [[[1, 5]], [6, 8]], [[1, 5], [6, 8]]),
            hidden("goes on the front", [[[3, 5]], [1, 2]], [[1, 2], [3, 5]]),
            hidden("fits in the gap", [[[1, 2], [5, 6]], [3, 4]], [[1, 2], [3, 4], [5, 6]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="non-overlapping-intervals",
        title="Non-Overlapping Intervals",
        difficulty="medium",
        prompt=(
            "Take away as few pieces of track as you can so that none of what's left overlaps. "
            "Return how many you had to take away. Pieces that merely touch are fine."
        ),
        example_input="intervals = [[1, 2], [2, 3], [3, 4], [1, 3]]",
        example_output="1",
        entrypoint="eraseOverlapIntervals",
        signature=sig("int", intervals="matrix<int>"),
        explainer=(
            "**Sort by end, and keep greedily.** Removing the fewest is the same as keeping the "
            "most, and the piece that ends soonest always leaves the most room for whatever "
            "comes after — so keeping it is never a mistake."
        ),
        hint=(
            "Sorting by *start* is the trap: a very long piece that starts first would be kept, "
            "blocking several short ones. Sort by end."
        ),
        approach=(
            "1) Sort by end. 2) Keep the first; track its end. 3) Keep each piece that starts "
            "at or after that end, updating it. 4) Return len(intervals) - kept. O(n log n)."
        ),
        solution=(
            "def eraseOverlapIntervals(intervals):\n"
            "    if not intervals:\n"
            "        return 0\n"
            "    ordered = sorted(intervals, key=lambda piece: piece[1])\n"
            "    end = ordered[0][1]\n"
            "    kept = 1\n"
            "    for start, finish in ordered[1:]:\n"
            "        if start >= end:\n"
            "            kept += 1\n"
            "            end = finish\n"
            "    return len(intervals) - kept"
        ),
        tests=[
            example([[[1, 2], [2, 3], [3, 4], [1, 3]]], 1),
            example([[[1, 2], [1, 2], [1, 2]]], 2),
            hidden("no track at all", [[]], 0),
            hidden("a single piece", [[[1, 2]]], 0),
            hidden("touching is allowed", [[[1, 2], [2, 3]]], 0),
            hidden("one long piece must go", [[[1, 100], [11, 22], [1, 11], [2, 12]]], 2),
            hidden("the greedy choice matters", [[[1, 5], [2, 3], [3, 4], [4, 6]]], 1),
        ],
    ),
    problem(
        zone=ZONE,
        slug="meeting-rooms",
        title="Meeting Rooms",
        difficulty="easy",
        prompt=(
            "The playroom has one train table, and every booking is a start and an end. Say "
            "whether all of them can go ahead. A booking may start exactly when another ends."
        ),
        example_input="intervals = [[0, 30], [5, 10], [15, 20]]",
        example_output="false",
        entrypoint="canAttendMeetings",
        signature=sig("bool", intervals="matrix<int>"),
        explainer=(
            "**In start order, only neighbours can clash.** Sort the bookings and check each "
            "against the next one — if none of those pairs collide, no pair anywhere does."
        ),
        hint=(
            "The bookings do not arrive sorted. And back-to-back is fine, so the clash test is "
            "`this end > next start`, strictly."
        ),
        approach=(
            "1) Sort by start. 2) For each adjacent pair, if the earlier one ends after the "
            "later one starts, return False. 3) Return True. O(n log n)."
        ),
        solution=(
            "def canAttendMeetings(intervals):\n"
            "    ordered = sorted(intervals)\n"
            "    for i in range(len(ordered) - 1):\n"
            "        if ordered[i][1] > ordered[i + 1][0]:\n"
            "            return False\n"
            "    return True"
        ),
        tests=[
            example([[[0, 30], [5, 10], [15, 20]]], False),
            example([[[7, 10], [2, 4]]], True),
            hidden("nothing booked", [[]], True),
            hidden("one booking", [[[1, 5]]], True),
            hidden("back to back is fine", [[[1, 5], [5, 10]]], True),
            hidden("given out of order but still fine", [[[5, 10], [1, 5]]], True),
            hidden("a one-unit overlap", [[[1, 5], [4, 10]]], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="meeting-rooms-ii",
        title="Meeting Rooms II",
        difficulty="medium",
        prompt=(
            "Same bookings, but now you can set up as many train tables as you need. Return the "
            "fewest tables that fit every booking."
        ),
        example_input="intervals = [[0, 30], [5, 10], [15, 20]]",
        example_output="2",
        entrypoint="minMeetingRooms",
        signature=sig("int", intervals="matrix<int>"),
        explainer=(
            "**The answer is the busiest instant.** Go through the bookings in start order "
            "keeping a heap of the end times of the tables currently in use. A new booking "
            "reuses the table that frees up soonest if it has already freed up; otherwise it "
            "needs a new one — and the heap's size is the answer."
        ),
        hint=(
            "You only ever compare against the *earliest* ending table, which is exactly what "
            "the top of a min-heap gives you. Back-to-back bookings share a table."
        ),
        approach=(
            "1) Sort by start; heap = []. 2) For each booking: if the heap's smallest end is "
            "<= this start, pop it. 3) Push this end. 4) Return len(heap). O(n log n)."
        ),
        solution=(
            "import heapq\n\n"
            "def minMeetingRooms(intervals):\n"
            "    tables = []\n"
            "    for start, end in sorted(intervals):\n"
            "        if tables and tables[0] <= start:\n"
            "            heapq.heappop(tables)\n"
            "        heapq.heappush(tables, end)\n"
            "    return len(tables)"
        ),
        tests=[
            example([[[0, 30], [5, 10], [15, 20]]], 2),
            example([[[7, 10], [2, 4]]], 1),
            hidden("nothing booked", [[]], 0),
            hidden("one booking, one table", [[[1, 5]]], 1),
            hidden("back to back shares a table", [[[1, 5], [5, 10]]], 1),
            hidden("one long booking across three short ones",
                   [[[1, 10], [2, 3], [3, 4], [4, 5]]], 2),
            hidden("three all at once", [[[1, 5], [2, 6], [3, 7]]], 3),
        ],
    ),
]

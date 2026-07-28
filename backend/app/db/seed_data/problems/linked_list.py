"""Marble Run — Linked Lists.

Chutes and pointers. Every problem here is really about how many marbles you can
see at once: one pointer sees the marble it's on, two pointers a fixed distance
apart see a *relationship*, and that relationship is usually the whole answer.

These are the problems that carry a `harness_preamble`, because a chute isn't
JSON. The compiled packs sit them out — a bridged `_build` can only feed a
single-argument entrypoint, and a cyclic chute has no `Box` representation.
"""

from app.db.seed_data.preambles import (
    CYCLE_BENCHES,
    CYCLE_PREAMBLE,
    LIST_AND_INT_BENCHES,
    LIST_AND_INT_PREAMBLE,
    REVERSE_LIST_BENCHES,
    REVERSE_LIST_PREAMBLE,
    TWO_LISTS_BENCHES,
    TWO_LISTS_PREAMBLE,
)
from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "marble-run"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="reverse-linked-list",
        title="Reverse Linked List",
        difficulty="medium",
        prompt=(
            "Sprocket's marble chute got tangled backwards! Given the head of a singly linked "
            "marble chute, reverse the run so the last marble drops first. Return the new head."
        ),
        example_input="head = [1, 2, 3, 4, 5]",
        example_output="[5, 4, 3, 2, 1]",
        entrypoint="reverseList",
        signature=sig("listnode", head="listnode"),
        starter_code=(
            "def reverseList(head):\n"
            "    prev = None\n"
            "    while head:\n"
            "        # your turn, little toy…\n"
            "        pass"
        ),
        harness_preamble=REVERSE_LIST_PREAMBLE,
        languages=REVERSE_LIST_BENCHES,
        explainer=(
            "**Two-pointer walk.** Keep a *prev* marble and a *current* marble. Each step, flip "
            "current's arrow to point at prev, then shuffle both forward one slot. When current "
            "runs off the end, prev is your new head."
        ),
        hint=(
            "You only need one pass and O(1) extra space. Store head.next in a temp before you "
            "flip the arrow, or you'll lose the rest of the chute."
        ),
        approach=(
            "1) prev = None. 2) While head: save nxt = head.next. 3) head.next = prev. "
            "4) prev = head. 5) head = nxt. 6) Return prev. That's the whole marble flip — "
            "O(n) time, O(1) space."
        ),
        solution=(
            "def reverseList(head):\n"
            "    prev = None\n"
            "    while head:\n"
            "        nxt = head.next\n"
            "        head.next = prev\n"
            "        prev = head\n"
            "        head = nxt\n"
            "    return prev"
        ),
        tests=[
            example([[1, 2, 3, 4, 5]], [5, 4, 3, 2, 1]),
            example([[1, 2]], [2, 1]),
            hidden("empty chute", [[]], []),
            hidden("single marble", [[1]], [1]),
            hidden("negatives", [[-1, 0, 1]], [1, 0, -1]),
            hidden("repeated values", [[7, 7, 7]], [7, 7, 7]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="linked-list-cycle",
        title="Linked List Cycle",
        difficulty="medium",
        prompt=(
            "A marble keeps rolling past the same bend forever. Determine whether the chute "
            "loops back on itself."
        ),
        example_input="head = [3, 2, 0, -4], tail connects to index 1",
        example_output="true",
        entrypoint="hasCycle",
        signature=sig("bool", head="listnode"),
        harness_preamble=CYCLE_PREAMBLE,
        languages=CYCLE_BENCHES,
        explainer=(
            "**Two marbles, two speeds.** Roll one marble one slot at a time and another two at "
            "a time. On a looping track the fast marble laps the slow one; on a straight track "
            "it falls off the end."
        ),
        hint=(
            "Floyd's tortoise and hare. Stop as soon as slow is fast, or fast runs out of track."
        ),
        approach=(
            "1) slow = fast = head. 2) While fast and fast.next: slow = slow.next, "
            "fast = fast.next.next. 3) If slow is fast: return True. 4) Return False. "
            "O(n) time, O(1) space."
        ),
        solution=(
            "def hasCycle(head):\n"
            "    slow = fast = head\n"
            "    while fast and fast.next:\n"
            "        slow = slow.next\n"
            "        fast = fast.next.next\n"
            "        if slow is fast:\n"
            "            return True\n"
            "    return False"
        ),
        # Second argument is the index the tail loops back to; -1 means no loop.
        tests=[
            example([[3, 2, 0, -4], 1], True),
            example([[1, 2], 0], True),
            hidden("single marble, no loop", [[1], -1], False),
            hidden("empty chute", [[], -1], False),
            hidden("straight run", [[1, 2, 3, 4, 5], -1], False),
            hidden("tail loops to itself", [[1, 2, 3, 4, 5], 4], True),
            hidden("two marbles, no loop", [[1, 2], -1], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="merge-two-sorted-lists",
        title="Merge Two Sorted Lists",
        difficulty="easy",
        prompt=(
            "Two marble chutes both run smallest to largest. Splice them into one chute that "
            "still does, reusing the marbles you were given. Return its head."
        ),
        example_input="list1 = [1, 2, 4], list2 = [1, 3, 4]",
        example_output="[1, 1, 2, 3, 4, 4]",
        entrypoint="mergeTwoLists",
        signature=sig("listnode", list1="listnode", list2="listnode"),
        harness_preamble=TWO_LISTS_PREAMBLE,
        languages=TWO_LISTS_BENCHES,
        explainer=(
            "**Always take the smaller head.** Whichever chute currently starts with the "
            "smaller marble is the one whose marble goes next — and then that chute has a new "
            "head. Repeat until one runs dry, then hang the rest of the other on the end."
        ),
        hint=(
            "A throwaway node in front of the answer saves you from special-casing the very "
            "first marble. Build onto its `next`, then return that at the end."
        ),
        approach=(
            "1) dummy = ListNode(); tail = dummy. 2) While both chutes have marbles: attach the "
            "smaller head, advance that chute and tail. 3) tail.next = whichever chute is left. "
            "4) Return dummy.next. O(n + m) time, O(1) space."
        ),
        solution=(
            "def mergeTwoLists(list1, list2):\n"
            "    dummy = ListNode()\n"
            "    tail = dummy\n"
            "    while list1 and list2:\n"
            "        if list1.val <= list2.val:\n"
            "            tail.next = list1\n"
            "            list1 = list1.next\n"
            "        else:\n"
            "            tail.next = list2\n"
            "            list2 = list2.next\n"
            "        tail = tail.next\n"
            "    tail.next = list1 or list2\n"
            "    return dummy.next"
        ),
        tests=[
            example([[1, 2, 4], [1, 3, 4]], [1, 1, 2, 3, 4, 4]),
            example([[], []], []),
            hidden("one chute is empty", [[], [0]], [0]),
            hidden("the other chute is empty", [[1], []], [1]),
            hidden("perfectly interleaved", [[1, 3, 5], [2, 4, 6]], [1, 2, 3, 4, 5, 6]),
            hidden("one chute runs out first", [[5], [1, 2, 3]], [1, 2, 3, 5]),
            hidden("negatives", [[-1, 0], [-2, 2]], [-2, -1, 0, 2]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="remove-nth-node-from-end",
        title="Remove Nth Node From End",
        difficulty="medium",
        prompt=(
            "Pull the nth marble counting back from the end of the chute, and return the head "
            "of what's left. n is always a real position in the chute."
        ),
        example_input="head = [1, 2, 3, 4, 5], n = 2",
        example_output="[1, 2, 3, 5]",
        entrypoint="removeNthFromEnd",
        signature=sig("listnode", head="listnode", n="int"),
        harness_preamble=LIST_AND_INT_PREAMBLE,
        languages=LIST_AND_INT_BENCHES,
        explainer=(
            "**Two pointers, n apart.** Send one marble n slots ahead, then roll both at the "
            "same speed. When the leader falls off the end, the follower is sitting exactly "
            "where you need it — one slot before the marble to pull out."
        ),
        hint=(
            "Start both pointers on a dummy node in front of the head. That's what makes "
            "removing the *first* marble need no special case at all."
        ),
        approach=(
            "1) dummy = ListNode(0, head); lead = trail = dummy. 2) Advance lead n + 1 times. "
            "3) While lead: advance both. 4) trail.next = trail.next.next. 5) Return "
            "dummy.next. One pass, O(1) space."
        ),
        solution=(
            "def removeNthFromEnd(head, n):\n"
            "    dummy = ListNode(0, head)\n"
            "    lead = trail = dummy\n"
            "    for _ in range(n + 1):\n"
            "        lead = lead.next\n"
            "    while lead:\n"
            "        lead = lead.next\n"
            "        trail = trail.next\n"
            "    trail.next = trail.next.next\n"
            "    return dummy.next"
        ),
        tests=[
            example([[1, 2, 3, 4, 5], 2], [1, 2, 3, 5]),
            example([[1], 1], []),
            hidden("the last marble", [[1, 2], 1], [1]),
            hidden("the first of two", [[1, 2], 2], [2]),
            hidden("the head of a longer chute", [[1, 2, 3], 3], [2, 3]),
            hidden("the very first marble", [[1, 2, 3, 4, 5], 5], [2, 3, 4, 5]),
            hidden("the very last marble", [[1, 2, 3, 4, 5], 1], [1, 2, 3, 4]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="middle-of-the-linked-list",
        title="Middle of the Linked List",
        difficulty="easy",
        prompt=(
            "Return the marble halfway down the chute — and if there are two middles, the "
            "second one. What comes back is that marble and everything after it."
        ),
        example_input="head = [1, 2, 3, 4, 5]",
        example_output="[3, 4, 5]",
        entrypoint="middleNode",
        signature=sig("listnode", head="listnode"),
        harness_preamble=REVERSE_LIST_PREAMBLE,
        languages=REVERSE_LIST_BENCHES,
        explainer=(
            "**Tortoise and hare again, but for position.** Roll one marble twice as fast as "
            "the other. By the time the fast one reaches the end, the slow one is exactly "
            "halfway — no counting, and no second pass."
        ),
        hint=(
            "The loop condition decides which of the two middles you land on. `while fast and "
            "fast.next` gives you the second one; dropping the second check gives the first."
        ),
        approach=(
            "1) slow = fast = head. 2) While fast and fast.next: slow = slow.next; fast = "
            "fast.next.next. 3) Return slow. One pass, O(1) space."
        ),
        solution=(
            "def middleNode(head):\n"
            "    slow = fast = head\n"
            "    while fast and fast.next:\n"
            "        slow = slow.next\n"
            "        fast = fast.next.next\n"
            "    return slow"
        ),
        tests=[
            example([[1, 2, 3, 4, 5]], [3, 4, 5]),
            example([[1, 2, 3, 4, 5, 6]], [4, 5, 6]),
            hidden("empty chute", [[]], []),
            hidden("single marble", [[1]], [1]),
            hidden("two marbles takes the second", [[1, 2]], [2]),
            hidden("three marbles", [[1, 2, 3]], [2, 3]),
            hidden("four marbles takes the third", [[1, 2, 3, 4]], [3, 4]),
        ],
    ),
]

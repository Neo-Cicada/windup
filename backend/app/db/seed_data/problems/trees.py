"""Branching Mobile — Trees.

A mobile hanging over the cot: every branch is itself a smaller mobile, which is
why almost everything here is one recursive question asked at the root. The
interesting ones are where the answer at a node isn't the answer you want to
return upwards — the diameter passes *through* a node while the depth comes
*from* it.

Cases are written as level-order lists with nulls, the shape LeetCode prints
trees in; the preamble plants them.
"""

from app.db.seed_data.preambles import (
    TREE_BENCHES,
    TREE_DUMP_BENCHES,
    TREE_DUMP_PREAMBLE,
    TREE_PREAMBLE,
    TWO_TREES_BENCHES,
    TWO_TREES_PREAMBLE,
)
from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "branching-mobile"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="max-depth-binary-tree",
        title="Maximum Depth of Binary Tree",
        difficulty="easy",
        prompt="How many branches tall is the mobile? Return its maximum depth.",
        example_input="root = [3, 9, 20, null, null, 15, 7]",
        example_output="3",
        entrypoint="maxDepth",
        signature=sig("int", root="treenode"),
        harness_preamble=TREE_PREAMBLE,
        languages=TREE_BENCHES,
        explainer=(
            "**Ask the branches.** A tree's depth is 1 + the deeper of its two children. "
            "Recursion writes itself."
        ),
        hint="The base case is an empty branch — that's depth 0.",
        approach="1) If not root: return 0. 2) Return 1 + max(maxDepth(left), maxDepth(right)).",
        solution=(
            "def maxDepth(root):\n"
            "    if not root:\n"
            "        return 0\n"
            "    return 1 + max(maxDepth(root.left), maxDepth(root.right))"
        ),
        tests=[
            example([[3, 9, 20, None, None, 15, 7]], 3),
            example([[1, None, 2]], 2),
            hidden("empty tree", [[]], 0),
            hidden("root only", [[0]], 1),
            hidden("full tree", [[1, 2, 3, 4, 5]], 3),
            hidden("leaning left", [[1, 2, None, 3, None, 4]], 4),
        ],
    ),
    problem(
        zone=ZONE,
        slug="invert-binary-tree",
        title="Invert Binary Tree",
        difficulty="easy",
        prompt=(
            "Somebody hung the mobile back to front. Swap every left branch with its right one, "
            "all the way down, and return the root."
        ),
        example_input="root = [4, 2, 7, 1, 3, 6, 9]",
        example_output="[4, 7, 2, 9, 6, 3, 1]",
        entrypoint="invertTree",
        signature=sig("treenode", root="treenode"),
        harness_preamble=TREE_DUMP_PREAMBLE,
        languages=TREE_DUMP_BENCHES,
        explainer=(
            "**Swap, then recurse — or recurse, then swap.** Both work, because swapping a "
            "node's two branches doesn't change what's inside either of them. The empty branch "
            "is the base case and needs nothing done to it."
        ),
        hint=(
            "In Python the swap is one line: `root.left, root.right = root.right, root.left`. "
            "The right-hand side is evaluated first, so no temporary is needed."
        ),
        approach=(
            "1) If root is None: return None. 2) Swap root.left and root.right. 3) Invert both "
            "children. 4) Return root. O(n) time, O(height) stack."
        ),
        solution=(
            "def invertTree(root):\n"
            "    if root is None:\n"
            "        return None\n"
            "    root.left, root.right = root.right, root.left\n"
            "    invertTree(root.left)\n"
            "    invertTree(root.right)\n"
            "    return root"
        ),
        tests=[
            example([[4, 2, 7, 1, 3, 6, 9]], [4, 7, 2, 9, 6, 3, 1]),
            example([[2, 1, 3]], [2, 3, 1]),
            hidden("nothing to hang", [[]], []),
            hidden("a single bead", [[1]], [1]),
            hidden("one branch, now on the other side", [[1, 2]], [1, None, 2]),
            hidden("and back again", [[1, None, 2]], [1, 2]),
            hidden("a lopsided mobile", [[1, 2, 3, 4, None, None, 5]],
                   [1, 3, 2, 5, None, None, 4]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="same-tree",
        title="Same Tree",
        difficulty="easy",
        prompt=(
            "Two mobiles came out of the same box. Say whether they hang identically — same "
            "shape, same beads, in the same places."
        ),
        example_input="p = [1, 2, 3], q = [1, 2, 3]",
        example_output="true",
        entrypoint="isSameTree",
        signature=sig("bool", p="treenode", q="treenode"),
        harness_preamble=TWO_TREES_PREAMBLE,
        languages=TWO_TREES_BENCHES,
        explainer=(
            "**Walk both at once.** Two trees match when their roots match and both pairs of "
            "children match. Two empty branches match; one empty and one not never does."
        ),
        hint=(
            "Check the two 'one is None' cases before you touch `.val`, or a lopsided pair will "
            "crash rather than answer."
        ),
        approach=(
            "1) If both are None: True. 2) If exactly one is None, or the values differ: False. "
            "3) Otherwise recurse on left-left and right-right. O(n) time."
        ),
        solution=(
            "def isSameTree(p, q):\n"
            "    if p is None and q is None:\n"
            "        return True\n"
            "    if p is None or q is None or p.val != q.val:\n"
            "        return False\n"
            "    return isSameTree(p.left, q.left) and isSameTree(p.right, q.right)"
        ),
        tests=[
            example([[1, 2, 3], [1, 2, 3]], True),
            example([[1, 2], [1, None, 2]], False),
            hidden("two empty mobiles", [[], []], True),
            hidden("one is empty", [[1], []], False),
            hidden("same beads, wrong branches", [[1, 2, 1], [1, 1, 2]], False),
            hidden("both lean the same way", [[1, None, 2], [1, None, 2]], True),
            hidden("a single matching bead", [[10], [10]], True),
        ],
    ),
    problem(
        zone=ZONE,
        slug="balanced-binary-tree",
        title="Balanced Binary Tree",
        difficulty="medium",
        prompt=(
            "A mobile hangs straight only if, at every single knot, the two sides differ in "
            "depth by no more than one. Say whether this one hangs straight."
        ),
        example_input="root = [3, 9, 20, null, null, 15, 7]",
        example_output="true",
        entrypoint="isBalanced",
        signature=sig("bool", root="treenode"),
        harness_preamble=TREE_PREAMBLE,
        languages=TREE_BENCHES,
        explainer=(
            "**Return the height and the verdict together.** Measuring each knot separately "
            "re-walks the same branches over and over. Instead let the recursion hand back a "
            "height, and use one impossible value — -1 — to mean 'already out of balance'."
        ),
        hint=(
            "Once a branch reports -1, stop: no amount of checking further up can put it back "
            "in balance. That short-circuit is what turns O(n²) into O(n)."
        ),
        approach=(
            "1) height(None) = 0. 2) height(node): measure left; if -1, propagate. Measure "
            "right; if -1 or the gap exceeds 1, return -1. 3) Otherwise 1 + max. 4) The tree is "
            "balanced when height(root) >= 0. O(n) time."
        ),
        solution=(
            "def isBalanced(root):\n"
            "    def height(node):\n"
            "        if node is None:\n"
            "            return 0\n"
            "        left = height(node.left)\n"
            "        if left < 0:\n"
            "            return -1\n"
            "        right = height(node.right)\n"
            "        if right < 0 or abs(left - right) > 1:\n"
            "            return -1\n"
            "        return 1 + max(left, right)\n\n"
            "    return height(root) >= 0"
        ),
        tests=[
            example([[3, 9, 20, None, None, 15, 7]], True),
            example([[1, 2, 2, 3, 3, None, None, 4, 4]], False),
            hidden("nothing to hang", [[]], True),
            hidden("a single bead", [[1]], True),
            hidden("one branch is still fine", [[1, 2]], True),
            hidden("two deep on one side", [[1, 2, None, 3]], False),
            hidden("a straight line down", [[1, None, 2, None, 3]], False),
        ],
    ),
    problem(
        zone=ZONE,
        slug="diameter-of-binary-tree",
        title="Diameter of Binary Tree",
        difficulty="medium",
        prompt=(
            "How far apart are the two furthest beads on the mobile? Return the length of the "
            "longest path between any two nodes, counted in branches. The path doesn't have to "
            "pass through the root."
        ),
        example_input="root = [1, 2, 3, 4, 5]",
        example_output="3",
        entrypoint="diameterOfBinaryTree",
        signature=sig("int", root="treenode"),
        harness_preamble=TREE_PREAMBLE,
        languages=TREE_BENCHES,
        explainer=(
            "**Two different questions at every knot.** The longest path *through* a knot is "
            "its left depth plus its right depth. The depth it reports *upwards* is 1 + the "
            "deeper side. Track the first as a running best while returning the second."
        ),
        hint=(
            "Answer in branches, not beads: a path visiting three nodes is two branches long. "
            "Adding the two child depths gives you that directly, with no ±1 to fix up."
        ),
        approach=(
            "1) best = 0. 2) depth(node): 0 for None, else l = depth(left), r = depth(right); "
            "best = max(best, l + r); return 1 + max(l, r). 3) Call it on the root and return "
            "best. O(n) time, O(height) stack."
        ),
        solution=(
            "def diameterOfBinaryTree(root):\n"
            "    best = 0\n\n"
            "    def depth(node):\n"
            "        nonlocal best\n"
            "        if node is None:\n"
            "            return 0\n"
            "        left = depth(node.left)\n"
            "        right = depth(node.right)\n"
            "        best = max(best, left + right)\n"
            "        return 1 + max(left, right)\n\n"
            "    depth(root)\n"
            "    return best"
        ),
        tests=[
            example([[1, 2, 3, 4, 5]], 3),
            example([[1, 2]], 1),
            hidden("nothing to hang", [[]], 0),
            hidden("a single bead spans nothing", [[1]], 0),
            hidden("the longest path misses the root", [[1, 2, 3, 4, 5, None, None, 6, 7]], 4),
            hidden("a straight line down", [[1, None, 2, None, 3]], 2),
            hidden("a zig-zag", [[1, 2, 3, None, 4, None, 5]], 4),
        ],
    ),
]

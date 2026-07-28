"""Catalogue content for the academy.

Zones and badges are lifted from the frontend's `components/academy/data.ts` so the
seeded API returns exactly what the UI was designed against.
"""

ZONES: list[dict] = [
    {
        "slug": "building-blocks",
        "name": "Building Blocks",
        "pattern": "Arrays & Strings",
        "color": "#6FBF73",
        "blurb": "Snap-together cubes",
    },
    {
        "slug": "marble-run",
        "name": "Marble Run",
        "pattern": "Linked Lists",
        "color": "#4FB0E5",
        "blurb": "Chutes & pointers",
    },
    {
        "slug": "board-game",
        "name": "Board Game",
        "pattern": "Graphs & Trees",
        "color": "#EF5B54",
        "blurb": "Roll, branch, explore",
    },
    {
        "slug": "toy-kitchen",
        "name": "Toy Kitchen",
        "pattern": "SQL",
        "color": "#F7C948",
        "blurb": "Recipes & queries",
    },
    {
        "slug": "stacking-cups",
        "name": "Stacking Cups",
        "pattern": "Stacks & Queues",
        "color": "#E08A3C",
        "blurb": "Last in, first out",
    },
    {
        "slug": "puzzle-box",
        "name": "Puzzle Box",
        "pattern": "Dynamic Programming",
        "color": "#8B6FD6",
        "blurb": "Solve once, reuse",
    },
]

ACHIEVEMENTS: list[dict] = [
    {
        "slug": "first-fix",
        "name": "First Fix",
        "description": "Solve your first toy",
        "color": "#6FBF73",
    },
    {
        "slug": "week-winder",
        "name": "Week Winder",
        "description": "7-day streak",
        "color": "#EF5B54",
    },
    {
        "slug": "unaided-ace",
        "name": "Unaided Ace",
        "description": "10 solves, no chests",
        "color": "#4FB0E5",
    },
    {
        "slug": "block-master",
        "name": "Block Master",
        "description": "Clear Building Blocks",
        "color": "#F7C948",
    },
    {
        "slug": "night-owl",
        "name": "Night Owl",
        "description": "Solve after midnight",
        "color": "#8B6FD6",
    },
    {
        "slug": "boss-slayer",
        "name": "Boss Slayer",
        "description": "Beat a Boss Battle",
        "color": "#E08A3C",
    },
    {
        "slug": "marble-champ",
        "name": "Marble Champ",
        "description": "Clear Marble Run",
        "color": "#4FB0E5",
    },
    {
        "slug": "century-toy",
        "name": "Century Toy",
        "description": "Solve 100 problems",
        "color": "#EF5B54",
    },
    {
        "slug": "perfect-week",
        "name": "Perfect Week",
        "description": "All quests, 7 days",
        "color": "#6FBF73",
    },
    {
        "slug": "graph-guru",
        "name": "Graph Guru",
        "description": "Clear Board Game",
        "color": "#8B6FD6",
    },
    {
        "slug": "speed-wind",
        "name": "Speed Wind",
        "description": "Solve under 5 min",
        "color": "#F7C948",
    },
    {
        "slug": "top-shelf",
        "name": "Top Shelf",
        "description": "Reach Level 5",
        "color": "#E08A3C",
    },
]

# ---- harness preambles ------------------------------------------------------
# Prepended before the toy's own code, so a bare `reverseList(head)` stub is
# actually callable. The driver in app/judge/harness.py defines `_build` and
# `_dump` as identity and then evaluates:
#
#     _dump(entrypoint(*_build(args)))
#
# `_build` receives the whole argument list and returns the real call arguments,
# which is what lets a problem fold two JSON values (a list of marbles plus the
# index its tail loops back to) into one linked structure.

LINKED_LIST_NODE = """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
"""

REVERSE_LIST_PREAMBLE = (
    LINKED_LIST_NODE
    + """

def _build(args):
    (vals,) = args
    head = None
    for v in reversed(vals):
        head = ListNode(v, head)
    return [head]


def _dump(node):
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out
"""
)

CYCLE_PREAMBLE = (
    LINKED_LIST_NODE
    + """

def _build(args):
    vals, pos = args
    if not vals:
        return [None]
    nodes = [ListNode(v) for v in vals]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if pos >= 0:
        nodes[-1].next = nodes[pos]
    return [nodes[0]]
"""
)

TREE_PREAMBLE = """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _build(args):
    \"\"\"Level-order list with nulls, the shape LeetCode prints trees in.\"\"\"
    (vals,) = args
    if not vals or vals[0] is None:
        return [None]
    root = TreeNode(vals[0])
    queue, i = [root], 1
    while queue and i < len(vals):
        node = queue.pop(0)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return [root]
"""


# ---- JavaScript benches -----------------------------------------------------
# The same structures in another syntax. Only the problems whose entrypoint takes
# something that isn't plain JSON need one of these; everywhere else the stub is
# generated from the signature and the adapters stay the identity pair.
JS_LIST_NODE = """
function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}
"""

JS_REVERSE_LIST_PREAMBLE = (
    JS_LIST_NODE
    + """
function _build(args) {
  var vals = args[0];
  var head = null;
  for (var i = vals.length - 1; i >= 0; i--) head = new ListNode(vals[i], head);
  return [head];
}

function _dump(node) {
  var out = [];
  while (node !== null && node !== undefined) {
    out.push(node.val);
    node = node.next;
  }
  return out;
}
"""
)

JS_CYCLE_PREAMBLE = (
    JS_LIST_NODE
    + """
function _build(args) {
  var vals = args[0];
  var pos = args[1];
  if (vals.length === 0) return [null];
  var nodes = vals.map(function (v) { return new ListNode(v); });
  for (var i = 0; i < nodes.length - 1; i++) nodes[i].next = nodes[i + 1];
  if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos];
  return [nodes[0]];
}
"""
)

JS_TREE_PREAMBLE = """
function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function _build(args) {
  // Level-order list with nulls, the shape LeetCode prints trees in.
  var vals = args[0];
  if (vals.length === 0 || vals[0] === null) return [null];
  var root = new TreeNode(vals[0]);
  var queue = [root];
  var i = 1;
  while (queue.length > 0 && i < vals.length) {
    var node = queue.shift();
    if (i < vals.length) {
      var left = vals[i++];
      if (left !== null) { node.left = new TreeNode(left); queue.push(node.left); }
    }
    if (i < vals.length) {
      var right = vals[i++];
      if (right !== null) { node.right = new TreeNode(right); queue.push(node.right); }
    }
  }
  return [root];
}
"""


# ---- Ruby benches -----------------------------------------------------------
RB_LIST_NODE = """
class ListNode
  attr_accessor :val, :next
  def initialize(val = 0, nxt = nil)
    @val = val
    @next = nxt
  end
end
"""

RB_REVERSE_LIST_PREAMBLE = (
    RB_LIST_NODE
    + """
def _build(args)
  head = nil
  args[0].reverse_each { |v| head = ListNode.new(v, head) }
  [head]
end

def _dump(node)
  out = []
  while node
    out << node.val
    node = node.next
  end
  out
end
"""
)

RB_CYCLE_PREAMBLE = (
    RB_LIST_NODE
    + """
def _build(args)
  vals, pos = args
  return [nil] if vals.empty?
  nodes = vals.map { |v| ListNode.new(v) }
  nodes.each_cons(2) { |a, b| a.next = b }
  nodes.last.next = nodes[pos] if pos >= 0
  [nodes.first]
end
"""
)

RB_TREE_PREAMBLE = """
class TreeNode
  attr_accessor :val, :left, :right
  def initialize(val = 0, left = nil, right = nil)
    @val = val
    @left = left
    @right = right
  end
end

def _build(args)
  # Level-order list with nulls, the shape LeetCode prints trees in.
  vals = args[0]
  return [nil] if vals.empty? || vals[0].nil?
  root = TreeNode.new(vals[0])
  queue = [root]
  i = 1
  while !queue.empty? && i < vals.length
    node = queue.shift
    if i < vals.length
      v = vals[i]
      i += 1
      if v
        node.left = TreeNode.new(v)
        queue << node.left
      end
    end
    if i < vals.length
      v = vals[i]
      i += 1
      if v
        node.right = TreeNode.new(v)
        queue << node.right
      end
    end
  end
  [root]
end
"""


# ---- PHP benches ------------------------------------------------------------
PHP_LIST_NODE = """
class ListNode {
  public $val;
  public $next;
  function __construct($val = 0, $next = null) {
    $this->val = $val;
    $this->next = $next;
  }
}
"""

PHP_REVERSE_LIST_PREAMBLE = (
    PHP_LIST_NODE
    + """
function _build($args) {
  $head = null;
  foreach (array_reverse($args[0]) as $v) $head = new ListNode($v, $head);
  return [$head];
}

function _dump($node) {
  $out = [];
  while ($node !== null) {
    $out[] = $node->val;
    $node = $node->next;
  }
  return $out;
}
"""
)

PHP_CYCLE_PREAMBLE = (
    PHP_LIST_NODE
    + """
function _build($args) {
  [$vals, $pos] = $args;
  if (count($vals) === 0) return [null];
  $nodes = array_map(fn($v) => new ListNode($v), $vals);
  for ($i = 0; $i < count($nodes) - 1; $i++) $nodes[$i]->next = $nodes[$i + 1];
  if ($pos >= 0) $nodes[count($nodes) - 1]->next = $nodes[$pos];
  return [$nodes[0]];
}
"""
)

PHP_TREE_PREAMBLE = """
class TreeNode {
  public $val;
  public $left;
  public $right;
  function __construct($val = 0, $left = null, $right = null) {
    $this->val = $val;
    $this->left = $left;
    $this->right = $right;
  }
}

function _build($args) {
  // Level-order list with nulls, the shape LeetCode prints trees in.
  $vals = $args[0];
  if (count($vals) === 0 || $vals[0] === null) return [null];
  $root = new TreeNode($vals[0]);
  $queue = [$root];
  $i = 1;
  while (count($queue) > 0 && $i < count($vals)) {
    $node = array_shift($queue);
    if ($i < count($vals)) {
      $left = $vals[$i++];
      if ($left !== null) { $node->left = new TreeNode($left); $queue[] = $node->left; }
    }
    if ($i < count($vals)) {
      $right = $vals[$i++];
      if ($right !== null) { $node->right = new TreeNode($right); $queue[] = $node->right; }
    }
  }
  return [$root];
}
"""


# ---- SQL benches ------------------------------------------------------------
# A SQL problem's preamble is its schema rather than its adapters: there is no
# entrypoint to make callable, only a table for the query to be written against.
RECIPES_SCHEMA = "CREATE TABLE recipes (rating INTEGER);"


def _ratings(values: list[int]) -> list[dict]:
    """One case's fixture — the rows that go in before the query runs."""
    return [{"table": "recipes", "rows": [[v] for v in values]}]


# Two keys carry the multi-language half of a problem:
#
# `signature` describes the *call* — what the entrypoint takes and returns, in
# the type language of app/judge/signature.py. Note that it is the call and not
# the JSON: linked-list-cycle's cases hold two values that `_build` folds into
# one `head`, so its signature has one param. Every pack generates its starter
# stub from this, which is what stops eight languages from meaning eight hundred
# hand-written stubs.
#
# `languages` overrides that generation per language — a preamble defining
# whatever the problem needs, and a stub where the generated one won't do. The
# test cases are deliberately not in there: they are plain JSON compared on the
# host, so one set of them grades every language.
PROBLEMS: list[dict] = [
    {
        "zone": "building-blocks",
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Two blocks in the bin snap together to make exactly the height Sprocket needs. "
            "Given a list of block heights and a target, return the indices of the two blocks "
            "that add up to it."
        ),
        "example_input": "nums = [2, 7, 11, 15], target = 9",
        "example_output": "[0, 1]",
        "starter_code": "def twoSum(nums, target):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Complement lookup.** Walk the bin once. For each block, ask 'which block would "
            "finish this tower?' — that's target - height. Keep every block you've seen in a "
            "dictionary so the question is answered in O(1)."
        ),
        "hint": (
            "You don't need two loops. Store each height you've already seen in a dict keyed by "
            "height, valued by index, and check for the complement *before* you insert."
        ),
        "approach": (
            "1) seen = {}. 2) For i, n in enumerate(nums): 3) need = target - n. "
            "4) If need in seen: return [seen[need], i]. 5) seen[n] = i. "
            "One pass, O(n) time, O(n) space."
        ),
        "solution": (
            "def twoSum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        need = target - n\n"
            "        if need in seen:\n"
            "            return [seen[need], i]\n"
            "        seen[n] = i\n"
            "    return []"
        ),
        "xp_reward": 50,
        "languages": {
            "javascript": {}, "ruby": {}, "php": {},
            "cpp": {}, "rust": {}, "go": {},
        },
        "signature": {
            "params": [{"name": "nums", "type": "list<int>"}, {"name": "target", "type": "int"}],
            "returns": "list<int>",
        },
        "entrypoint": "twoSum",
        # Every case has exactly one valid pair, so comparing indices is fair.
        "tests": [
            {"visibility": "example", "args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"visibility": "example", "args": [[3, 2, 4], 6], "expected": [1, 2]},
            {"visibility": "hidden", "label": "duplicate blocks", "args": [[3, 3], 6],
             "expected": [0, 1]},
            {"visibility": "hidden", "label": "negative heights",
             "args": [[-1, -2, -3, -4, -5], -8], "expected": [2, 4]},
            {"visibility": "hidden", "label": "zeroes", "args": [[0, 4, 3, 0], 0],
             "expected": [0, 3]},
            {"visibility": "hidden", "label": "pair at the far end",
             "args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 19], "expected": [8, 9]},
            {"visibility": "hidden", "label": "skips the first block",
             "args": [[5, 75, 25], 100], "expected": [1, 2]},
        ],
    },
    {
        "zone": "building-blocks",
        "slug": "valid-anagram",
        "title": "Valid Anagram",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Two alphabet-block words got shuffled in the toy chest. Decide whether one is a "
            "rearrangement of the other."
        ),
        "example_input": 's = "anagram", t = "nagaram"',
        "example_output": "true",
        "starter_code": "def isAnagram(s, t):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Count the blocks.** Anagrams use the same letters the same number of times, so "
            "compare letter counts rather than order."
        ),
        "hint": "Different lengths can never be anagrams — bail out early, then count with a dict.",
        "approach": (
            "1) If len(s) != len(t): return False. 2) Tally each letter of s in a Counter. "
            "3) Decrement for each letter of t; if any count dips below zero, return False. "
            "4) Return True. O(n) time, O(1) space for a fixed alphabet."
        ),
        "solution": (
            "from collections import Counter\n\n"
            "def isAnagram(s, t):\n"
            "    return len(s) == len(t) and Counter(s) == Counter(t)"
        ),
        "xp_reward": 50,
        "languages": {
            "javascript": {}, "ruby": {}, "php": {},
            "cpp": {}, "rust": {}, "go": {},
        },
        "signature": {
            "params": [{"name": "s", "type": "string"}, {"name": "t", "type": "string"}],
            "returns": "bool",
        },
        "entrypoint": "isAnagram",
        "tests": [
            {"visibility": "example", "args": ["anagram", "nagaram"], "expected": True},
            {"visibility": "example", "args": ["rat", "car"], "expected": False},
            {"visibility": "hidden", "label": "two empty words", "args": ["", ""],
             "expected": True},
            {"visibility": "hidden", "label": "different lengths", "args": ["a", "ab"],
             "expected": False},
            {"visibility": "hidden", "label": "same letters, wrong counts",
             "args": ["aacc", "ccac"], "expected": False},
            {"visibility": "hidden", "label": "classic pair", "args": ["listen", "silent"],
             "expected": True},
            {"visibility": "hidden", "label": "two letters", "args": ["ab", "ba"],
             "expected": True},
        ],
    },
    {
        "zone": "marble-run",
        "slug": "reverse-linked-list",
        "title": "Reverse Linked List",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "Sprocket's marble chute got tangled backwards! Given the head of a singly linked "
            "marble chute, reverse the run so the last marble drops first. Return the new head."
        ),
        "example_input": "head = [1, 2, 3, 4, 5]",
        "example_output": "[5, 4, 3, 2, 1]",
        "starter_code": (
            "def reverseList(head):\n"
            "    prev = None\n"
            "    while head:\n"
            "        # your turn, little toy…\n"
            "        pass"
        ),
        "explainer": (
            "**Two-pointer walk.** Keep a *prev* marble and a *current* marble. Each step, flip "
            "current's arrow to point at prev, then shuffle both forward one slot. When current "
            "runs off the end, prev is your new head."
        ),
        "hint": (
            "You only need one pass and O(1) extra space. Store head.next in a temp before you "
            "flip the arrow, or you'll lose the rest of the chute."
        ),
        "approach": (
            "1) prev = None. 2) While head: save nxt = head.next. 3) head.next = prev. "
            "4) prev = head. 5) head = nxt. 6) Return prev. That's the whole marble flip — "
            "O(n) time, O(1) space."
        ),
        "solution": (
            "def reverseList(head):\n"
            "    prev = None\n"
            "    while head:\n"
            "        nxt = head.next\n"
            "        head.next = prev\n"
            "        prev = head\n"
            "        head = nxt\n"
            "    return prev"
        ),
        "xp_reward": 60,
        "languages": {
            "javascript": {"harness_preamble": JS_REVERSE_LIST_PREAMBLE},
            "ruby": {"harness_preamble": RB_REVERSE_LIST_PREAMBLE},
            "php": {"harness_preamble": PHP_REVERSE_LIST_PREAMBLE},
        },
        "signature": {
            "params": [{"name": "head", "type": "listnode"}],
            "returns": "listnode",
        },
        "entrypoint": "reverseList",
        "harness_preamble": REVERSE_LIST_PREAMBLE,
        "tests": [
            {"visibility": "example", "args": [[1, 2, 3, 4, 5]], "expected": [5, 4, 3, 2, 1]},
            {"visibility": "example", "args": [[1, 2]], "expected": [2, 1]},
            {"visibility": "hidden", "label": "empty chute", "args": [[]], "expected": []},
            {"visibility": "hidden", "label": "single marble", "args": [[1]], "expected": [1]},
            {"visibility": "hidden", "label": "negatives", "args": [[-1, 0, 1]],
             "expected": [1, 0, -1]},
            {"visibility": "hidden", "label": "repeated values", "args": [[7, 7, 7]],
             "expected": [7, 7, 7]},
        ],
    },
    {
        "zone": "marble-run",
        "slug": "linked-list-cycle",
        "title": "Linked List Cycle",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "A marble keeps rolling past the same bend forever. Determine whether the chute "
            "loops back on itself."
        ),
        "example_input": "head = [3, 2, 0, -4], tail connects to index 1",
        "example_output": "true",
        "starter_code": "def hasCycle(head):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Two marbles, two speeds.** Roll one marble one slot at a time and another two at "
            "a time. On a looping track the fast marble laps the slow one; on a straight track "
            "it falls off the end."
        ),
        "hint": (
            "Floyd's tortoise and hare. Stop as soon as slow is fast, or fast runs out of track."
        ),
        "approach": (
            "1) slow = fast = head. 2) While fast and fast.next: slow = slow.next, "
            "fast = fast.next.next. 3) If slow is fast: return True. 4) Return False. "
            "O(n) time, O(1) space."
        ),
        "solution": (
            "def hasCycle(head):\n"
            "    slow = fast = head\n"
            "    while fast and fast.next:\n"
            "        slow = slow.next\n"
            "        fast = fast.next.next\n"
            "        if slow is fast:\n"
            "            return True\n"
            "    return False"
        ),
        "xp_reward": 60,
        "languages": {
            "javascript": {"harness_preamble": JS_CYCLE_PREAMBLE},
            "ruby": {"harness_preamble": RB_CYCLE_PREAMBLE},
            "php": {"harness_preamble": PHP_CYCLE_PREAMBLE},
        },
        "signature": {
            "params": [{"name": "head", "type": "listnode"}],
            "returns": "bool",
        },
        "entrypoint": "hasCycle",
        "harness_preamble": CYCLE_PREAMBLE,
        # Second argument is the index the tail loops back to; -1 means no loop.
        "tests": [
            {"visibility": "example", "args": [[3, 2, 0, -4], 1], "expected": True},
            {"visibility": "example", "args": [[1, 2], 0], "expected": True},
            {"visibility": "hidden", "label": "single marble, no loop", "args": [[1], -1],
             "expected": False},
            {"visibility": "hidden", "label": "empty chute", "args": [[], -1],
             "expected": False},
            {"visibility": "hidden", "label": "straight run", "args": [[1, 2, 3, 4, 5], -1],
             "expected": False},
            {"visibility": "hidden", "label": "tail loops to itself",
             "args": [[1, 2, 3, 4, 5], 4], "expected": True},
            {"visibility": "hidden", "label": "two marbles, no loop", "args": [[1, 2], -1],
             "expected": False},
        ],
    },
    {
        "zone": "board-game",
        "slug": "number-of-islands",
        "title": "Number of Islands",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "The board game's map has patches of land ('1') in a sea of water ('0'). Count how "
            "many separate islands the playing pieces can land on."
        ),
        "example_input": 'grid = [["1","1","0"],["1","0","0"],["0","0","1"]]',
        "example_output": "2",
        "starter_code": "def numIslands(grid):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Flood fill.** Every time you find un-visited land, that's a brand-new island — "
            "then sink the whole connected patch so you never count it twice."
        ),
        "hint": (
            "Sink visited land by writing '0' back into the grid; "
            "that's your visited set, for free."
        ),
        "approach": (
            "1) Scan every cell. 2) When you hit '1', increment the count. 3) DFS/BFS out from "
            "that cell, flipping every connected '1' to '0'. 4) Continue the scan. "
            "O(rows x cols) time."
        ),
        "solution": (
            "def numIslands(grid):\n"
            "    if not grid:\n"
            "        return 0\n"
            "    rows, cols = len(grid), len(grid[0])\n\n"
            "    def sink(r, c):\n"
            "        if 0 <= r < rows and 0 <= c < cols and grid[r][c] == '1':\n"
            "            grid[r][c] = '0'\n"
            "            sink(r + 1, c); sink(r - 1, c)\n"
            "            sink(r, c + 1); sink(r, c - 1)\n\n"
            "    count = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] == '1':\n"
            "                count += 1\n"
            "                sink(r, c)\n"
            "    return count"
        ),
        "xp_reward": 60,
        "languages": {
            "javascript": {}, "ruby": {}, "php": {},
            "cpp": {}, "rust": {}, "go": {},
        },
        "signature": {
            "params": [{"name": "grid", "type": "matrix<string>"}],
            "returns": "int",
        },
        "entrypoint": "numIslands",
        "tests": [
            {"visibility": "example",
             "args": [[["1", "1", "0"], ["1", "0", "0"], ["0", "0", "1"]]], "expected": 2},
            {"visibility": "example",
             "args": [[["1", "1", "1", "1", "0"], ["1", "1", "0", "1", "0"],
                       ["1", "1", "0", "0", "0"], ["0", "0", "0", "0", "0"]]],
             "expected": 1},
            {"visibility": "hidden", "label": "three separate patches",
             "args": [[["1", "1", "0", "0", "0"], ["1", "1", "0", "0", "0"],
                       ["0", "0", "1", "0", "0"], ["0", "0", "0", "1", "1"]]],
             "expected": 3},
            {"visibility": "hidden", "label": "all water", "args": [[["0"]]], "expected": 0},
            {"visibility": "hidden", "label": "one square of land", "args": [[["1"]]],
             "expected": 1},
            {"visibility": "hidden", "label": "empty row", "args": [[[]]], "expected": 0},
            {"visibility": "hidden", "label": "stripes in a single row",
             "args": [[["1", "0", "1", "0", "1"]]], "expected": 3},
        ],
    },
    {
        "zone": "board-game",
        "slug": "max-depth-binary-tree",
        "title": "Maximum Depth of Binary Tree",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": "How many branches tall is the game tree? Return its maximum depth.",
        "example_input": "root = [3, 9, 20, null, null, 15, 7]",
        "example_output": "3",
        "starter_code": "def maxDepth(root):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Ask the branches.** A tree's depth is 1 + the deeper of its two children. "
            "Recursion writes itself."
        ),
        "hint": "The base case is an empty branch — that's depth 0.",
        "approach": "1) If not root: return 0. 2) Return 1 + max(maxDepth(left), maxDepth(right)).",
        "solution": (
            "def maxDepth(root):\n"
            "    if not root:\n"
            "        return 0\n"
            "    return 1 + max(maxDepth(root.left), maxDepth(root.right))"
        ),
        "xp_reward": 50,
        "languages": {
            "javascript": {"harness_preamble": JS_TREE_PREAMBLE},
            "ruby": {"harness_preamble": RB_TREE_PREAMBLE},
            "php": {"harness_preamble": PHP_TREE_PREAMBLE},
        },
        "signature": {
            "params": [{"name": "root", "type": "treenode"}],
            "returns": "int",
        },
        "entrypoint": "maxDepth",
        "harness_preamble": TREE_PREAMBLE,
        "tests": [
            {"visibility": "example", "args": [[3, 9, 20, None, None, 15, 7]], "expected": 3},
            {"visibility": "example", "args": [[1, None, 2]], "expected": 2},
            {"visibility": "hidden", "label": "empty tree", "args": [[]], "expected": 0},
            {"visibility": "hidden", "label": "root only", "args": [[0]], "expected": 1},
            {"visibility": "hidden", "label": "full tree", "args": [[1, 2, 3, 4, 5]],
             "expected": 3},
            {"visibility": "hidden", "label": "leaning left", "args": [[1, 2, None, 3, None, 4]],
             "expected": 4},
        ],
    },
    {
        "zone": "stacking-cups",
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Stack the cups so every one that goes down comes back up in order. Decide whether "
            "a string of brackets is balanced."
        ),
        "example_input": 's = "{[()]}"',
        "example_output": "true",
        "starter_code": "def isValid(s):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Last in, first out.** Push every opening cup. On a closing cup, the top of the "
            "stack must be its match — otherwise the tower topples."
        ),
        "hint": "A leftover stack at the end means unmatched cups. Don't forget to check for that.",
        "approach": (
            "1) pairs = {')':'(', ']':'[', '}':'{'}. 2) Push openers. 3) On a closer, pop and "
            "compare. 4) Return not stack."
        ),
        "solution": (
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
        "xp_reward": 50,
        "languages": {
            "javascript": {}, "ruby": {}, "php": {},
            "cpp": {}, "rust": {}, "go": {},
        },
        "signature": {
            "params": [{"name": "s", "type": "string"}],
            "returns": "bool",
        },
        "entrypoint": "isValid",
        "tests": [
            {"visibility": "example", "args": ["{[()]}"], "expected": True},
            {"visibility": "example", "args": ["(]"], "expected": False},
            {"visibility": "hidden", "label": "no cups at all", "args": [""], "expected": True},
            {"visibility": "hidden", "label": "one cup left standing", "args": ["("],
             "expected": False},
            {"visibility": "hidden", "label": "three towers side by side", "args": ["()[]{}"],
             "expected": True},
            {"visibility": "hidden", "label": "crossed, not nested", "args": ["([)]"],
             "expected": False},
            {"visibility": "hidden", "label": "closes before it opens", "args": [")("],
             "expected": False},
        ],
    },
    {
        "zone": "puzzle-box",
        "slug": "climbing-stairs",
        "title": "Climbing Stairs",
        "difficulty": "easy",
        "weight_label": "LIGHT WEIGHT",
        "prompt": (
            "Sprocket climbs the shelf one or two steps at a time. How many distinct ways can "
            "the little toy reach step n?"
        ),
        "example_input": "n = 5",
        "example_output": "8",
        "starter_code": "def climbStairs(n):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Solve once, reuse.** Ways to reach step n = ways to reach n-1 plus ways to reach "
            "n-2. It's Fibonacci wearing a shelf costume."
        ),
        "hint": "You only ever need the last two answers — no array required.",
        "approach": "1) a, b = 1, 1. 2) Repeat n-1 times: a, b = b, a + b. 3) Return b.",
        "solution": (
            "def climbStairs(n):\n"
            "    a, b = 1, 1\n"
            "    for _ in range(n - 1):\n"
            "        a, b = b, a + b\n"
            "    return b"
        ),
        "xp_reward": 50,
        "languages": {
            "javascript": {}, "ruby": {}, "php": {},
            "cpp": {}, "rust": {}, "go": {},
        },
        "signature": {
            "params": [{"name": "n", "type": "int"}],
            "returns": "int",
        },
        "entrypoint": "climbStairs",
        "tests": [
            {"visibility": "example", "args": [5], "expected": 8},
            {"visibility": "example", "args": [2], "expected": 2},
            {"visibility": "hidden", "label": "one step", "args": [1], "expected": 1},
            {"visibility": "hidden", "label": "three steps", "args": [3], "expected": 3},
            {"visibility": "hidden", "label": "ten steps", "args": [10], "expected": 89},
            {"visibility": "hidden", "label": "twenty steps", "args": [20], "expected": 10946},
            {"visibility": "hidden", "label": "tall shelf — naive recursion will crawl",
             "args": [45], "expected": 1836311903},
        ],
    },
    {
        "zone": "puzzle-box",
        "slug": "coin-change",
        "title": "Coin Change",
        "difficulty": "hard",
        "weight_label": "HEAVY WEIGHT",
        "prompt": (
            "Pay for a gumball with the fewest play-coins possible. Given coin denominations and "
            "an amount, return the minimum number of coins, or -1 if it can't be paid."
        ),
        "example_input": "coins = [1, 5, 6, 9], amount = 11",
        "example_output": "2",
        "starter_code": "def coinChange(coins, amount):\n    # your turn, little toy…\n    pass",
        "explainer": (
            "**Build up from zero.** Best[a] is the cheapest way to make amount a. Every coin "
            "gives a candidate: 1 + Best[a - coin]. Greedy fails here — the table doesn't."
        ),
        "hint": (
            "Seed dp[0] = 0 and fill the rest with infinity, then take the min over every coin."
        ),
        "approach": (
            "1) dp = [0] + [inf] * amount. 2) For a in 1..amount: for coin in coins, if "
            "coin <= a: dp[a] = min(dp[a], dp[a-coin] + 1). 3) Return dp[amount] if finite else -1."
        ),
        "solution": (
            "def coinChange(coins, amount):\n"
            "    dp = [0] + [float('inf')] * amount\n"
            "    for a in range(1, amount + 1):\n"
            "        for coin in coins:\n"
            "            if coin <= a:\n"
            "                dp[a] = min(dp[a], dp[a - coin] + 1)\n"
            "    return -1 if dp[amount] == float('inf') else dp[amount]"
        ),
        "xp_reward": 80,
        "languages": {
            "javascript": {}, "ruby": {}, "php": {},
            "cpp": {}, "rust": {}, "go": {},
        },
        "signature": {
            "params": [{"name": "coins", "type": "list<int>"}, {"name": "amount", "type": "int"}],
            "returns": "int",
        },
        "entrypoint": "coinChange",
        "tests": [
            {"visibility": "example", "args": [[1, 5, 6, 9], 11], "expected": 2},
            {"visibility": "example", "args": [[2], 3], "expected": -1},
            {"visibility": "hidden", "label": "nothing to pay", "args": [[1], 0], "expected": 0},
            {"visibility": "hidden", "label": "standard change", "args": [[1, 2, 5], 11],
             "expected": 3},
            {"visibility": "hidden", "label": "greedy would overpay", "args": [[2, 5, 10, 1], 27],
             "expected": 4},
            {"visibility": "hidden", "label": "awkward denominations",
             "args": [[186, 419, 83, 408], 6249], "expected": 20},
            {"visibility": "hidden", "label": "cannot be paid", "args": [[5], 3], "expected": -1},
        ],
    },
    {
        "zone": "toy-kitchen",
        "slug": "second-highest-salary",
        "title": "Second Highest Recipe Rating",
        "difficulty": "medium",
        "weight_label": "MEDIUM WEIGHT",
        "prompt": (
            "The toy kitchen keeps a table of recipe ratings. Write a query returning the second "
            "highest distinct rating, or NULL when there isn't one."
        ),
        "example_input": "ratings = [100, 200, 300]",
        "example_output": "200",
        "language": "sql",
        "starter_code": "SELECT\n  -- your turn, little toy…\n;",
        "explainer": (
            "**Skip the top, take the next.** Order distinct values descending, then offset by "
            "one. A subquery keeps NULL as the answer when the row doesn't exist."
        ),
        "hint": "DISTINCT matters — repeated top ratings would otherwise hide the runner-up.",
        "approach": (
            "1) SELECT DISTINCT rating ORDER BY rating DESC LIMIT 1 OFFSET 1. "
            "2) Wrap it in an outer SELECT so an empty result becomes NULL."
        ),
        "solution": (
            "SELECT (\n"
            "  SELECT DISTINCT rating\n"
            "  FROM recipes\n"
            "  ORDER BY rating DESC\n"
            "  LIMIT 1 OFFSET 1\n"
            ") AS second_highest;"
        ),
        "xp_reward": 60,
        # A SQL problem has no entrypoint and no signature — the preamble is the
        # schema the query is written against, and each case's args are the rows
        # to put in it. See app/judge/languages/sql.py.
        #
        # Spelled out rather than left to the model default: this problem was
        # seeded ungraded for a long time, and re-seeding only writes the keys a
        # spec still has, so dropping the key would leave old rows ungraded.
        "graded": True,
        "harness_preamble": RECIPES_SCHEMA,
        "tests": [
            {
                "visibility": "example",
                "args": _ratings([100, 200, 300]),
                "expected": [[200]],
            },
            {
                "visibility": "example",
                "label": "nothing to come second",
                "args": _ratings([50]),
                "expected": [[None]],
            },
            {
                "visibility": "hidden",
                "label": "the top rating repeats",
                "args": _ratings([300, 300, 250, 100]),
                "expected": [[250]],
            },
            {
                "visibility": "hidden",
                "label": "every rating the same",
                "args": _ratings([80, 80, 80]),
                "expected": [[None]],
            },
            {
                "visibility": "hidden",
                "label": "an empty kitchen",
                "args": _ratings([]),
                "expected": [[None]],
            },
            {
                "visibility": "hidden",
                "label": "out of order, with a gap",
                "args": _ratings([12, 99, 7, 99, 40]),
                "expected": [[40]],
            },
            {
                "visibility": "hidden",
                "label": "negatives count too",
                "args": _ratings([-5, -1, -9]),
                "expected": [[-5]],
            },
        ],
    },
]

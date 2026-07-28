"""Harness preambles, shared by whichever problems need the same structure.

Prepended before the toy's own code, so a bare `reverseList(head)` stub is
actually callable. The driver in app/judge/harness.py defines `_build` and
`_dump` as identity and then evaluates:

    _dump(entrypoint(*_build(args)))

`_build` receives the whole argument list and returns the real call arguments,
which is what lets a problem fold two JSON values (a list of marbles plus the
index its tail loops back to) into one linked structure.

A preamble is source code, so it is never inherited across languages — each one
here exists once per language a structural problem offers. That is also why the
compiled packs sit these problems out: a cyclic list is not expressible with
Rust's `Box`, and a bridged `_build` can only feed a single-argument entrypoint.
"""

# ---- Python -----------------------------------------------------------------

LINKED_LIST_NODE = """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
"""

_PY_LIST_DUMP = """

def _dump(node):
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out
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
"""
    + _PY_LIST_DUMP
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

# Two separate chutes in, one chute out.
TWO_LISTS_PREAMBLE = (
    LINKED_LIST_NODE
    + """

def _chute(vals):
    head = None
    for v in reversed(vals):
        head = ListNode(v, head)
    return head


def _build(args):
    left, right = args
    return [_chute(left), _chute(right)]
"""
    + _PY_LIST_DUMP
)

# One chute plus a plain number the entrypoint also takes.
LIST_AND_INT_PREAMBLE = (
    LINKED_LIST_NODE
    + """

def _build(args):
    vals, n = args
    head = None
    for v in reversed(vals):
        head = ListNode(v, head)
    return [head, n]
"""
    + _PY_LIST_DUMP
)

TREE_NODE = """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
"""

_PY_TREE_BUILD = """

def _plant(vals):
    \"\"\"Level-order list with nulls, the shape LeetCode prints trees in.\"\"\"
    if not vals or vals[0] is None:
        return None
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
    return root
"""

TREE_PREAMBLE = (
    TREE_NODE
    + _PY_TREE_BUILD
    + """

def _build(args):
    (vals,) = args
    return [_plant(vals)]
"""
)

TWO_TREES_PREAMBLE = (
    TREE_NODE
    + _PY_TREE_BUILD
    + """

def _build(args):
    left, right = args
    return [_plant(left), _plant(right)]
"""
)

# Returning a tree means serialising one, and trailing nulls have to go or every
# correct answer would differ from the expected value by however many empty
# branches the level-order walk happened to visit last.
TREE_DUMP_PREAMBLE = (
    TREE_PREAMBLE
    + """

def _dump(root):
    if root is None:
        return []
    out, queue = [], [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out
"""
)


# ---- JavaScript -------------------------------------------------------------
# The same structures in another syntax. Only the problems whose entrypoint takes
# something that isn't plain JSON need one of these; everywhere else the stub is
# generated from the signature and the adapters stay the identity pair.

JS_LIST_NODE = """
function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

function _chute(vals) {
  var head = null;
  for (var i = vals.length - 1; i >= 0; i--) head = new ListNode(vals[i], head);
  return head;
}
"""

_JS_LIST_DUMP = """
function _dump(node) {
  var out = [];
  while (node !== null && node !== undefined) {
    out.push(node.val);
    node = node.next;
  }
  return out;
}
"""

JS_REVERSE_LIST_PREAMBLE = (
    JS_LIST_NODE
    + """
function _build(args) {
  return [_chute(args[0])];
}
"""
    + _JS_LIST_DUMP
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

JS_TWO_LISTS_PREAMBLE = (
    JS_LIST_NODE
    + """
function _build(args) {
  return [_chute(args[0]), _chute(args[1])];
}
"""
    + _JS_LIST_DUMP
)

JS_LIST_AND_INT_PREAMBLE = (
    JS_LIST_NODE
    + """
function _build(args) {
  return [_chute(args[0]), args[1]];
}
"""
    + _JS_LIST_DUMP
)

JS_TREE_NODE = """
function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function _plant(vals) {
  // Level-order list with nulls, the shape LeetCode prints trees in.
  if (vals.length === 0 || vals[0] === null) return null;
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
  return root;
}
"""

JS_TREE_PREAMBLE = (
    JS_TREE_NODE
    + """
function _build(args) {
  return [_plant(args[0])];
}
"""
)

JS_TWO_TREES_PREAMBLE = (
    JS_TREE_NODE
    + """
function _build(args) {
  return [_plant(args[0]), _plant(args[1])];
}
"""
)

JS_TREE_DUMP_PREAMBLE = (
    JS_TREE_PREAMBLE
    + """
function _dump(root) {
  if (root === null || root === undefined) return [];
  var out = [];
  var queue = [root];
  while (queue.length > 0) {
    var node = queue.shift();
    if (node === null || node === undefined) { out.push(null); continue; }
    out.push(node.val);
    queue.push(node.left === undefined ? null : node.left);
    queue.push(node.right === undefined ? null : node.right);
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}
"""
)


# ---- Ruby -------------------------------------------------------------------

RB_LIST_NODE = """
class ListNode
  attr_accessor :val, :next
  def initialize(val = 0, nxt = nil)
    @val = val
    @next = nxt
  end
end

def _chute(vals)
  head = nil
  vals.reverse_each { |v| head = ListNode.new(v, head) }
  head
end
"""

_RB_LIST_DUMP = """
def _dump(node)
  out = []
  while node
    out << node.val
    node = node.next
  end
  out
end
"""

RB_REVERSE_LIST_PREAMBLE = (
    RB_LIST_NODE
    + """
def _build(args)
  [_chute(args[0])]
end
"""
    + _RB_LIST_DUMP
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

RB_TWO_LISTS_PREAMBLE = (
    RB_LIST_NODE
    + """
def _build(args)
  [_chute(args[0]), _chute(args[1])]
end
"""
    + _RB_LIST_DUMP
)

RB_LIST_AND_INT_PREAMBLE = (
    RB_LIST_NODE
    + """
def _build(args)
  [_chute(args[0]), args[1]]
end
"""
    + _RB_LIST_DUMP
)

RB_TREE_NODE = """
class TreeNode
  attr_accessor :val, :left, :right
  def initialize(val = 0, left = nil, right = nil)
    @val = val
    @left = left
    @right = right
  end
end

def _plant(vals)
  # Level-order list with nulls, the shape LeetCode prints trees in.
  return nil if vals.empty? || vals[0].nil?
  root = TreeNode.new(vals[0])
  queue = [root]
  i = 1
  while !queue.empty? && i < vals.length
    node = queue.shift
    if i < vals.length
      v = vals[i]
      i += 1
      if !v.nil?
        node.left = TreeNode.new(v)
        queue << node.left
      end
    end
    if i < vals.length
      v = vals[i]
      i += 1
      if !v.nil?
        node.right = TreeNode.new(v)
        queue << node.right
      end
    end
  end
  root
end
"""

RB_TREE_PREAMBLE = (
    RB_TREE_NODE
    + """
def _build(args)
  [_plant(args[0])]
end
"""
)

RB_TWO_TREES_PREAMBLE = (
    RB_TREE_NODE
    + """
def _build(args)
  [_plant(args[0]), _plant(args[1])]
end
"""
)

RB_TREE_DUMP_PREAMBLE = (
    RB_TREE_PREAMBLE
    + """
def _dump(root)
  return [] if root.nil?
  out = []
  queue = [root]
  until queue.empty?
    node = queue.shift
    if node.nil?
      out << nil
      next
    end
    out << node.val
    queue << node.left
    queue << node.right
  end
  out.pop while !out.empty? && out.last.nil?
  out
end
"""
)


# ---- PHP --------------------------------------------------------------------
# PHP cannot redeclare a function, so a preamble here defines `_build`/`_dump`
# before the pack's own adapters get a chance to — see app/judge/languages/php.py.

PHP_LIST_NODE = """
class ListNode {
  public $val;
  public $next;
  function __construct($val = 0, $next = null) {
    $this->val = $val;
    $this->next = $next;
  }
}

function _chute($vals) {
  $head = null;
  foreach (array_reverse($vals) as $v) $head = new ListNode($v, $head);
  return $head;
}
"""

_PHP_LIST_DUMP = """
function _dump($node) {
  $out = [];
  while ($node !== null) {
    $out[] = $node->val;
    $node = $node->next;
  }
  return $out;
}
"""

PHP_REVERSE_LIST_PREAMBLE = (
    PHP_LIST_NODE
    + """
function _build($args) {
  return [_chute($args[0])];
}
"""
    + _PHP_LIST_DUMP
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

PHP_TWO_LISTS_PREAMBLE = (
    PHP_LIST_NODE
    + """
function _build($args) {
  return [_chute($args[0]), _chute($args[1])];
}
"""
    + _PHP_LIST_DUMP
)

PHP_LIST_AND_INT_PREAMBLE = (
    PHP_LIST_NODE
    + """
function _build($args) {
  return [_chute($args[0]), $args[1]];
}
"""
    + _PHP_LIST_DUMP
)

PHP_TREE_NODE = """
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

function _plant($vals) {
  // Level-order list with nulls, the shape LeetCode prints trees in.
  if (count($vals) === 0 || $vals[0] === null) return null;
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
  return $root;
}
"""

PHP_TREE_PREAMBLE = (
    PHP_TREE_NODE
    + """
function _build($args) {
  return [_plant($args[0])];
}
"""
)

PHP_TWO_TREES_PREAMBLE = (
    PHP_TREE_NODE
    + """
function _build($args) {
  return [_plant($args[0]), _plant($args[1])];
}
"""
)

PHP_TREE_DUMP_PREAMBLE = (
    PHP_TREE_PREAMBLE
    + """
function _dump($root) {
  if ($root === null) return [];
  $out = [];
  $queue = [$root];
  while (count($queue) > 0) {
    $node = array_shift($queue);
    if ($node === null) { $out[] = null; continue; }
    $out[] = $node->val;
    $queue[] = $node->left;
    $queue[] = $node->right;
  }
  while (count($out) > 0 && $out[count($out) - 1] === null) array_pop($out);
  return $out;
}
"""
)


# ---- bench bundles ----------------------------------------------------------
# What a problem actually writes down. Every structural problem offers the same
# four languages for the same reason — the interpreted packs are the ones whose
# `_build` can hand back more than a single argument.

REVERSE_LIST_BENCHES = {
    "javascript": {"harness_preamble": JS_REVERSE_LIST_PREAMBLE},
    "ruby": {"harness_preamble": RB_REVERSE_LIST_PREAMBLE},
    "php": {"harness_preamble": PHP_REVERSE_LIST_PREAMBLE},
}

CYCLE_BENCHES = {
    "javascript": {"harness_preamble": JS_CYCLE_PREAMBLE},
    "ruby": {"harness_preamble": RB_CYCLE_PREAMBLE},
    "php": {"harness_preamble": PHP_CYCLE_PREAMBLE},
}

TWO_LISTS_BENCHES = {
    "javascript": {"harness_preamble": JS_TWO_LISTS_PREAMBLE},
    "ruby": {"harness_preamble": RB_TWO_LISTS_PREAMBLE},
    "php": {"harness_preamble": PHP_TWO_LISTS_PREAMBLE},
}

LIST_AND_INT_BENCHES = {
    "javascript": {"harness_preamble": JS_LIST_AND_INT_PREAMBLE},
    "ruby": {"harness_preamble": RB_LIST_AND_INT_PREAMBLE},
    "php": {"harness_preamble": PHP_LIST_AND_INT_PREAMBLE},
}

TREE_BENCHES = {
    "javascript": {"harness_preamble": JS_TREE_PREAMBLE},
    "ruby": {"harness_preamble": RB_TREE_PREAMBLE},
    "php": {"harness_preamble": PHP_TREE_PREAMBLE},
}

TWO_TREES_BENCHES = {
    "javascript": {"harness_preamble": JS_TWO_TREES_PREAMBLE},
    "ruby": {"harness_preamble": RB_TWO_TREES_PREAMBLE},
    "php": {"harness_preamble": PHP_TWO_TREES_PREAMBLE},
}

TREE_DUMP_BENCHES = {
    "javascript": {"harness_preamble": JS_TREE_DUMP_PREAMBLE},
    "ruby": {"harness_preamble": RB_TREE_DUMP_PREAMBLE},
    "php": {"harness_preamble": PHP_TREE_DUMP_PREAMBLE},
}

# The plain case: nothing structural, so every pack generates its own stub from
# the signature and the identity adapters are left alone.
ALL_LANGUAGES = {
    "javascript": {}, "ruby": {}, "php": {},
    "cpp": {}, "rust": {}, "go": {},
}

"""Reference solutions, one per seeded problem per language.

The other half of `solution_for()`: what a toy that got it right would have
written, in each language the academy offers. They exist so the suite can prove
the claim the whole language seam rests on — that one set of hidden cases grades
every language, and grades it the same.
"""

JAVASCRIPT_SOLUTIONS = {
    "two-sum": """
function twoSum(nums, target) {
  const seen = new Map();
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (seen.has(need)) return [seen.get(need), i];
    seen.set(nums[i], i);
  }
  return [];
}
""",
    "valid-anagram": """
function isAnagram(s, t) {
  if (s.length !== t.length) return false;
  const counts = {};
  for (const ch of s) counts[ch] = (counts[ch] || 0) + 1;
  for (const ch of t) {
    if (!counts[ch]) return false;
    counts[ch]--;
  }
  return true;
}
""",
    "reverse-linked-list": """
function reverseList(head) {
  let prev = null;
  while (head !== null) {
    const next = head.next;
    head.next = prev;
    prev = head;
    head = next;
  }
  return prev;
}
""",
    "linked-list-cycle": """
function hasCycle(head) {
  let slow = head, fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next;
    fast = fast.next.next;
    if (slow === fast) return true;
  }
  return false;
}
""",
    "number-of-islands": """
function numIslands(grid) {
  if (grid.length === 0) return 0;
  const rows = grid.length, cols = grid[0].length;
  let count = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] !== "1") continue;
      count++;
      const stack = [[r, c]];
      while (stack.length > 0) {
        const [y, x] = stack.pop();
        if (y < 0 || x < 0 || y >= rows || x >= cols || grid[y][x] !== "1") continue;
        grid[y][x] = "0";
        stack.push([y + 1, x], [y - 1, x], [y, x + 1], [y, x - 1]);
      }
    }
  }
  return count;
}
""",
    "max-depth-binary-tree": """
function maxDepth(root) {
  if (root === null) return 0;
  return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}
""",
    "valid-parentheses": """
function isValid(s) {
  const pairs = { ")": "(", "]": "[", "}": "{" };
  const stack = [];
  for (const ch of s) {
    if (ch === "(" || ch === "[" || ch === "{") stack.push(ch);
    else if (stack.pop() !== pairs[ch]) return false;
  }
  return stack.length === 0;
}
""",
    "climbing-stairs": """
function climbStairs(n) {
  let a = 1, b = 1;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}
""",
    "coin-change": """
function coinChange(coins, amount) {
  const dp = new Array(amount + 1).fill(Infinity);
  dp[0] = 0;
  for (let a = 1; a <= amount; a++) {
    for (const coin of coins) {
      if (coin <= a) dp[a] = Math.min(dp[a], dp[a - coin] + 1);
    }
  }
  return dp[amount] === Infinity ? -1 : dp[amount];
}
""",
}

RUBY_SOLUTIONS = {
    "two-sum": """
def twoSum(nums, target)
  seen = {}
  nums.each_with_index do |n, i|
    return [seen[target - n], i] if seen.key?(target - n)
    seen[n] = i
  end
  []
end
""",
    "valid-anagram": """
def isAnagram(s, t)
  s.chars.sort == t.chars.sort
end
""",
    "reverse-linked-list": """
def reverseList(head)
  prev = nil
  while head
    nxt = head.next
    head.next = prev
    prev = head
    head = nxt
  end
  prev
end
""",
    "linked-list-cycle": """
def hasCycle(head)
  slow = fast = head
  while fast && fast.next
    slow = slow.next
    fast = fast.next.next
    return true if slow.equal?(fast)
  end
  false
end
""",
    "number-of-islands": """
def numIslands(grid)
  return 0 if grid.empty?
  rows, cols = grid.length, grid[0].length
  count = 0
  (0...rows).each do |r|
    (0...cols).each do |c|
      next unless grid[r][c] == "1"
      count += 1
      stack = [[r, c]]
      until stack.empty?
        y, x = stack.pop
        next if y < 0 || x < 0 || y >= rows || x >= cols || grid[y][x] != "1"
        grid[y][x] = "0"
        stack.push([y + 1, x], [y - 1, x], [y, x + 1], [y, x - 1])
      end
    end
  end
  count
end
""",
    "max-depth-binary-tree": """
def maxDepth(root)
  return 0 if root.nil?
  1 + [maxDepth(root.left), maxDepth(root.right)].max
end
""",
    "valid-parentheses": """
def isValid(s)
  pairs = { ")" => "(", "]" => "[", "}" => "{" }
  stack = []
  s.each_char do |ch|
    if pairs.key?(ch)
      return false if stack.pop != pairs[ch]
    else
      stack << ch
    end
  end
  stack.empty?
end
""",
    "climbing-stairs": """
def climbStairs(n)
  a, b = 1, 1
  n.times { a, b = b, a + b }
  a
end
""",
    "coin-change": """
def coinChange(coins, amount)
  dp = Array.new(amount + 1, Float::INFINITY)
  dp[0] = 0
  (1..amount).each do |a|
    coins.each { |c| dp[a] = [dp[a], dp[a - c] + 1].min if c <= a }
  end
  dp[amount] == Float::INFINITY ? -1 : dp[amount]
end
""",
}

PHP_SOLUTIONS = {
    "two-sum": """
function twoSum($nums, $target) {
  $seen = [];
  foreach ($nums as $i => $n) {
    if (isset($seen[$target - $n])) return [$seen[$target - $n], $i];
    $seen[$n] = $i;
  }
  return [];
}
""",
    "valid-anagram": """
function isAnagram($s, $t) {
  $a = str_split($s); $b = str_split($t);
  sort($a); sort($b);
  return $a === $b;
}
""",
    "reverse-linked-list": """
function reverseList($head) {
  $prev = null;
  while ($head !== null) {
    $next = $head->next;
    $head->next = $prev;
    $prev = $head;
    $head = $next;
  }
  return $prev;
}
""",
    "linked-list-cycle": """
function hasCycle($head) {
  $slow = $head; $fast = $head;
  while ($fast !== null && $fast->next !== null) {
    $slow = $slow->next;
    $fast = $fast->next->next;
    if ($slow === $fast) return true;
  }
  return false;
}
""",
    "number-of-islands": """
function numIslands($grid) {
  if (count($grid) === 0) return 0;
  $rows = count($grid); $cols = count($grid[0]);
  $count = 0;
  for ($r = 0; $r < $rows; $r++) {
    for ($c = 0; $c < $cols; $c++) {
      if ($grid[$r][$c] !== "1") continue;
      $count++;
      $stack = [[$r, $c]];
      while (count($stack) > 0) {
        [$y, $x] = array_pop($stack);
        if ($y < 0 || $x < 0 || $y >= $rows || $x >= $cols || $grid[$y][$x] !== "1") continue;
        $grid[$y][$x] = "0";
        $stack[] = [$y + 1, $x]; $stack[] = [$y - 1, $x];
        $stack[] = [$y, $x + 1]; $stack[] = [$y, $x - 1];
      }
    }
  }
  return $count;
}
""",
    "max-depth-binary-tree": """
function maxDepth($root) {
  if ($root === null) return 0;
  return 1 + max(maxDepth($root->left), maxDepth($root->right));
}
""",
    "valid-parentheses": """
function isValid($s) {
  $pairs = [")" => "(", "]" => "[", "}" => "{"];
  $stack = [];
  foreach (str_split($s) as $ch) {
    if (isset($pairs[$ch])) {
      if (array_pop($stack) !== $pairs[$ch]) return false;
    } else {
      $stack[] = $ch;
    }
  }
  return count($stack) === 0;
}
""",
    "climbing-stairs": """
function climbStairs($n) {
  $a = 1; $b = 1;
  for ($i = 0; $i < $n; $i++) { [$a, $b] = [$b, $a + $b]; }
  return $a;
}
""",
    "coin-change": """
function coinChange($coins, $amount) {
  $dp = array_fill(0, $amount + 1, PHP_INT_MAX);
  $dp[0] = 0;
  for ($a = 1; $a <= $amount; $a++) {
    foreach ($coins as $c) {
      if ($c <= $a && $dp[$a - $c] !== PHP_INT_MAX) $dp[$a] = min($dp[$a], $dp[$a - $c] + 1);
    }
  }
  return $dp[$amount] === PHP_INT_MAX ? -1 : $dp[$amount];
}
""",
}


# Keyed by language slug, so a test can ask for "every pack we have solutions
# for" without knowing which those are.
SOLUTIONS = {
    "javascript": JAVASCRIPT_SOLUTIONS,
    "ruby": RUBY_SOLUTIONS,
    "php": PHP_SOLUTIONS,
}

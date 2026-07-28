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



# ---- the compiled languages -------------------------------------------------
# Only the six problems whose JSON arguments *are* the call arguments. The three
# structural ones (two linked lists and a tree) are not offered in a compiled
# language: each would need its node type and `_build` written three more times,
# and linked-list-cycle in particular cannot be expressed with Rust's `Box` at
# all — a cyclic list needs `Rc<RefCell<..>>`, which is a different type for the
# toy to write against. See app/judge/languages/compiled.py.
CPP_SOLUTIONS = {
    "two-sum": """
std::vector<long long> twoSum(std::vector<long long> nums, long long target) {
  for (std::size_t i = 0; i < nums.size(); i++)
    for (std::size_t j = i + 1; j < nums.size(); j++)
      if (nums[i] + nums[j] == target) return {(long long)i, (long long)j};
  return {};
}
""",
    "valid-anagram": """
bool isAnagram(std::string s, std::string t) {
  if (s.size() != t.size()) return false;
  int counts[256] = {0};
  for (unsigned char c : s) counts[c]++;
  for (unsigned char c : t) if (--counts[c] < 0) return false;
  return true;
}
""",
    "number-of-islands": """
int numIslands(std::vector<std::vector<std::string>> grid) {
  if (grid.empty()) return 0;
  long long rows = grid.size(), cols = grid[0].size(), count = 0;
  std::vector<std::pair<long long, long long>> stack;
  for (long long r = 0; r < rows; r++) {
    for (long long c = 0; c < cols; c++) {
      if (grid[r][c] != "1") continue;
      count++;
      stack.push_back({r, c});
      while (!stack.empty()) {
        auto [y, x] = stack.back();
        stack.pop_back();
        if (y < 0 || x < 0 || y >= rows || x >= cols || grid[y][x] != "1") continue;
        grid[y][x] = "0";
        stack.push_back({y + 1, x});
        stack.push_back({y - 1, x});
        stack.push_back({y, x + 1});
        stack.push_back({y, x - 1});
      }
    }
  }
  return (int)count;
}
""",
    "valid-parentheses": """
bool isValid(std::string s) {
  std::vector<char> stack;
  for (char c : s) {
    if (c == '(' || c == '[' || c == '{') { stack.push_back(c); continue; }
    char want = c == ')' ? '(' : (c == ']' ? '[' : '{');
    if (stack.empty() || stack.back() != want) return false;
    stack.pop_back();
  }
  return stack.empty();
}
""",
    "climbing-stairs": """
long long climbStairs(long long n) {
  long long a = 1, b = 1;
  for (long long i = 0; i < n; i++) { long long next = a + b; a = b; b = next; }
  return a;
}
""",
    "coin-change": """
long long coinChange(std::vector<long long> coins, long long amount) {
  const long long BIG = 1000000000LL;
  std::vector<long long> dp(amount + 1, BIG);
  dp[0] = 0;
  for (long long a = 1; a <= amount; a++)
    for (long long coin : coins)
      if (coin <= a && dp[a - coin] + 1 < dp[a]) dp[a] = dp[a - coin] + 1;
  return dp[amount] >= BIG ? -1 : dp[amount];
}
""",
}

RUST_SOLUTIONS = {
    "two-sum": """
fn twoSum(nums: Vec<i64>, target: i64) -> Vec<i64> {
    for i in 0..nums.len() {
        for j in (i + 1)..nums.len() {
            if nums[i] + nums[j] == target {
                return vec![i as i64, j as i64];
            }
        }
    }
    vec![]
}
""",
    "valid-anagram": """
fn isAnagram(s: String, t: String) -> bool {
    let mut a: Vec<char> = s.chars().collect();
    let mut b: Vec<char> = t.chars().collect();
    a.sort();
    b.sort();
    a == b
}
""",
    "number-of-islands": """
fn numIslands(grid: Vec<Vec<String>>) -> i64 {
    let mut grid = grid;
    if grid.is_empty() { return 0; }
    let rows = grid.len() as i64;
    let cols = grid[0].len() as i64;
    let mut count = 0i64;
    for r in 0..rows {
        for c in 0..cols {
            if grid[r as usize][c as usize] != "1" { continue; }
            count += 1;
            let mut stack = vec![(r, c)];
            while let Some((y, x)) = stack.pop() {
                if y < 0 || x < 0 || y >= rows || x >= cols { continue; }
                if grid[y as usize][x as usize] != "1" { continue; }
                grid[y as usize][x as usize] = String::from("0");
                stack.push((y + 1, x));
                stack.push((y - 1, x));
                stack.push((y, x + 1));
                stack.push((y, x - 1));
            }
        }
    }
    count
}
""",
    "valid-parentheses": """
fn isValid(s: String) -> bool {
    let mut stack: Vec<char> = Vec::new();
    for c in s.chars() {
        match c {
            '(' | '[' | '{' => stack.push(c),
            _ => {
                let want = match c { ')' => '(', ']' => '[', _ => '{' };
                if stack.pop() != Some(want) { return false; }
            }
        }
    }
    stack.is_empty()
}
""",
    "climbing-stairs": """
fn climbStairs(n: i64) -> i64 {
    let (mut a, mut b) = (1i64, 1i64);
    for _ in 0..n {
        let next = a + b;
        a = b;
        b = next;
    }
    a
}
""",
    "coin-change": """
fn coinChange(coins: Vec<i64>, amount: i64) -> i64 {
    const BIG: i64 = 1_000_000_000;
    let mut dp = vec![BIG; (amount + 1) as usize];
    dp[0] = 0;
    for a in 1..=amount {
        for &coin in coins.iter() {
            if coin <= a && dp[(a - coin) as usize] + 1 < dp[a as usize] {
                dp[a as usize] = dp[(a - coin) as usize] + 1;
            }
        }
    }
    if dp[amount as usize] >= BIG { -1 } else { dp[amount as usize] }
}
""",
}

GO_SOLUTIONS = {
    "two-sum": """
func twoSum(nums []int64, target int64) []int64 {
	seen := map[int64]int64{}
	for i, n := range nums {
		if j, ok := seen[target-n]; ok {
			return []int64{j, int64(i)}
		}
		seen[n] = int64(i)
	}
	return []int64{}
}
""",
    "valid-anagram": """
func isAnagram(s string, t string) bool {
	if len(s) != len(t) {
		return false
	}
	counts := map[rune]int{}
	for _, c := range s {
		counts[c]++
	}
	for _, c := range t {
		counts[c]--
		if counts[c] < 0 {
			return false
		}
	}
	return true
}
""",
    "number-of-islands": """
func numIslands(grid [][]string) int64 {
	if len(grid) == 0 {
		return 0
	}
	rows, cols := int64(len(grid)), int64(len(grid[0]))
	var count int64
	for r := int64(0); r < rows; r++ {
		for c := int64(0); c < cols; c++ {
			if grid[r][c] != "1" {
				continue
			}
			count++
			stack := [][2]int64{{r, c}}
			for len(stack) > 0 {
				top := stack[len(stack)-1]
				stack = stack[:len(stack)-1]
				y, x := top[0], top[1]
				if y < 0 || x < 0 || y >= rows || x >= cols || grid[y][x] != "1" {
					continue
				}
				grid[y][x] = "0"
				stack = append(stack, [2]int64{y + 1, x}, [2]int64{y - 1, x},
					[2]int64{y, x + 1}, [2]int64{y, x - 1})
			}
		}
	}
	return count
}
""",
    "valid-parentheses": """
func isValid(s string) bool {
	var stack []rune
	for _, c := range s {
		if c == '(' || c == '[' || c == '{' {
			stack = append(stack, c)
			continue
		}
		var want rune = '{'
		if c == ')' {
			want = '('
		} else if c == ']' {
			want = '['
		}
		if len(stack) == 0 || stack[len(stack)-1] != want {
			return false
		}
		stack = stack[:len(stack)-1]
	}
	return len(stack) == 0
}
""",
    "climbing-stairs": """
func climbStairs(n int64) int64 {
	var a, b int64 = 1, 1
	for i := int64(0); i < n; i++ {
		a, b = b, a+b
	}
	return a
}
""",
    "coin-change": """
func coinChange(coins []int64, amount int64) int64 {
	const big int64 = 1000000000
	dp := make([]int64, amount+1)
	for i := range dp {
		dp[i] = big
	}
	dp[0] = 0
	for a := int64(1); a <= amount; a++ {
		for _, coin := range coins {
			if coin <= a && dp[a-coin]+1 < dp[a] {
				dp[a] = dp[a-coin] + 1
			}
		}
	}
	if dp[amount] >= big {
		return -1
	}
	return dp[amount]
}
""",
}


# Keyed by language slug, so a test can ask for "every pack we have solutions
# for" without knowing which those are, and without assuming they all cover the
# same problems.
SOLUTIONS = {
    "javascript": JAVASCRIPT_SOLUTIONS,
    "ruby": RUBY_SOLUTIONS,
    "php": PHP_SOLUTIONS,
    "cpp": CPP_SOLUTIONS,
    "rust": RUST_SOLUTIONS,
    "go": GO_SOLUTIONS,
}

"""Spelling Beads — Tries.

Words threaded onto a shared string, letter by letter, so everything sharing a
beginning shares a branch. Every problem here can be brute-forced by comparing
whole words; the point is noticing that the *prefix* is the thing being asked
about, and that a tree of prefixes answers all of these at once.
"""

from app.db.seed_data.spec import example, hidden, problem, sig

ZONE = "spelling-beads"

PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="longest-common-prefix",
        title="Longest Common Prefix",
        difficulty="easy",
        prompt=(
            "Several bead-words hang from the same peg. Return the longest run of beads they "
            "all start with, or an empty string if they share nothing."
        ),
        example_input='strs = ["flower", "flow", "flight"]',
        example_output='"fl"',
        entrypoint="longestCommonPrefix",
        signature=sig("string", strs="list<string>"),
        explainer=(
            "**The shared trunk.** Thread every word onto one strand: the answer is however "
            "far you get before the strand forks, or before a word simply ends. You can do "
            "that without building the strand — walk the letters in step across all the words."
        ),
        hint=(
            "The answer is never longer than the shortest word. Two edge cases decide most "
            "attempts: no words at all, and a word that is itself empty."
        ),
        approach=(
            "1) If strs is empty, return ''. 2) Take strs[0] as the candidate. 3) For each "
            "other word, chop the last letter off the candidate until the word starts with it. "
            "4) Return the candidate. O(total letters)."
        ),
        solution=(
            "def longestCommonPrefix(strs):\n"
            "    if not strs:\n"
            "        return ''\n"
            "    prefix = strs[0]\n"
            "    for word in strs[1:]:\n"
            "        while not word.startswith(prefix):\n"
            "            prefix = prefix[:-1]\n"
            "            if not prefix:\n"
            "                return ''\n"
            "    return prefix"
        ),
        tests=[
            example([["flower", "flow", "flight"]], "fl"),
            example([["dog", "racecar", "car"]], ""),
            hidden("no words on the peg", [[]], ""),
            hidden("one empty word", [[""]], ""),
            hidden("a single word is its own prefix", [["a"]], "a"),
            hidden("two identical words", [["abc", "abc"]], "abc"),
            hidden("a long shared trunk",
                   [["interspecies", "interstellar", "interstate"]], "inters"),
        ],
    ),
    problem(
        zone=ZONE,
        slug="count-words-with-prefix",
        title="Count Words With Prefix",
        difficulty="easy",
        prompt=(
            "Given a box of bead-words and a list of prefixes to look up, return how many words "
            "start with each prefix, in the order the prefixes were asked about."
        ),
        example_input='words = ["pay", "attention", "practice", "attend"], prefixes = ["at", "pr"]',
        example_output="[2, 1]",
        entrypoint="prefixCounts",
        signature=sig("list<int>", words="list<string>", prefixes="list<string>"),
        explainer=(
            "**Count on the way in.** Thread every word onto the strand and add one to a "
            "counter at every bead you pass through. Then a lookup is just walking the prefix "
            "and reading the counter where you stop — the words themselves are never compared."
        ),
        hint=(
            "The empty prefix matches every word, so the answer for it is len(words). Make sure "
            "whatever you build handles being asked about a prefix nothing starts with."
        ),
        approach=(
            "1) Build a dict from every prefix of every word to a count. 2) Answer each query "
            "with a lookup, defaulting to 0. O(total letters) to build, O(len(prefix)) to ask — "
            "against O(words × prefixes) for the direct comparison."
        ),
        solution=(
            "def prefixCounts(words, prefixes):\n"
            "    counts = {}\n"
            "    for word in words:\n"
            "        for i in range(len(word) + 1):\n"
            "            key = word[:i]\n"
            "            counts[key] = counts.get(key, 0) + 1\n"
            "    return [counts.get(prefix, 0) for prefix in prefixes]"
        ),
        tests=[
            example([["pay", "attention", "practice", "attend"], ["at", "pr", "z", ""]],
                    [2, 1, 0, 4]),
            example([["leetcode", "win", "loops", "success"], ["win", "loo", "le"]], [1, 1, 1]),
            hidden("no words in the box", [[], ["a"]], [0]),
            hidden("nothing asked about", [["a"], []], []),
            hidden("each word is a prefix of the last",
                   [["aaa", "aa", "a"], ["a", "aa", "aaa", "aaaa"]], [3, 2, 1, 0]),
            hidden("a whole word is a prefix of itself",
                   [["apple"], ["apple", "appl", "b"]], [1, 1, 0]),
            hidden("longer words count too", [["ab", "abc", "abcd"], ["abc"]], [2]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="replace-words",
        title="Replace Words",
        difficulty="medium",
        prompt=(
            "The toy dictionary holds root words. In the sentence, replace every word that "
            "begins with a root by that root — and where several roots fit, use the shortest. "
            "Words are separated by single spaces."
        ),
        example_input=(
            'dictionary = ["cat", "bat", "rat"], sentence = "the cattle was rattled by the '
            'battery"'
        ),
        example_output='"the cat was rat by the bat"',
        entrypoint="replaceWords",
        signature=sig("string", dictionary="list<string>", sentence="string"),
        explainer=(
            "**Stop at the first root you pass.** Walking a word's letters from the start, the "
            "first root you meet is by construction the shortest one that fits — so there is "
            "never anything to compare afterwards."
        ),
        hint=(
            "Split on spaces, rebuild with spaces. A word with no root in the dictionary is "
            "left exactly as it was, not dropped."
        ),
        approach=(
            "1) Put the roots in a set. 2) For each word, try its prefixes shortest first and "
            "take the first that's a root. 3) Fall back to the word itself. 4) Join with "
            "spaces. O(total letters)."
        ),
        solution=(
            "def replaceWords(dictionary, sentence):\n"
            "    roots = set(dictionary)\n"
            "    out = []\n"
            "    for word in sentence.split(' '):\n"
            "        replacement = word\n"
            "        for i in range(1, len(word) + 1):\n"
            "            if word[:i] in roots:\n"
            "                replacement = word[:i]\n"
            "                break\n"
            "        out.append(replacement)\n"
            "    return ' '.join(out)"
        ),
        tests=[
            example([["cat", "bat", "rat"], "the cattle was rattled by the battery"],
                    "the cat was rat by the bat"),
            example([["a", "b", "c"], "aadsfasf absbs bbab cadsfafs"], "a a b c"),
            hidden("an empty dictionary changes nothing", [[], "hello world"], "hello world"),
            hidden("the shortest root wins", [["catt", "cat"], "the cattle"], "the cat"),
            hidden("nested roots", [["a", "aa", "aaa"], "a aa aaa aaaa"], "a a a a"),
            hidden("a root can be the whole word", [["se", "r"], "sea rat"], "se r"),
            hidden("no word matches", [["xyz"], "abc def"], "abc def"),
        ],
    ),
    problem(
        zone=ZONE,
        slug="longest-word-in-dictionary",
        title="Longest Word in Dictionary",
        difficulty="medium",
        prompt=(
            "Find the longest bead-word that can be built up one bead at a time, where every "
            "step along the way is also a word in the box. If two are equally long, return the "
            "one that comes first alphabetically. If none can, return an empty string."
        ),
        example_input='words = ["w", "wo", "wor", "worl", "world"]',
        example_output='"world"',
        entrypoint="longestWord",
        signature=sig("string", words="list<string>"),
        explainer=(
            "**Buildable means every ancestor is present.** A word qualifies exactly when the "
            "word one bead shorter also qualifies — which makes this a walk down the strand "
            "that stops the moment it hits a bead nobody marked as a word."
        ),
        hint=(
            "Sorting the words alphabetically settles the tie-break *and* guarantees you meet "
            "every word after all of its own prefixes. Then a set of what's buildable so far "
            "is all the state you need."
        ),
        approach=(
            "1) buildable = {''}. 2) For each word in sorted(words): if word[:-1] is buildable, "
            "add it, and keep it if it beats the current best on length. 3) Return the best. "
            "O(n log n) for the sort."
        ),
        solution=(
            "def longestWord(words):\n"
            "    buildable = {''}\n"
            "    best = ''\n"
            "    for word in sorted(words):\n"
            "        if word[:-1] in buildable:\n"
            "            buildable.add(word)\n"
            "            if len(word) > len(best):\n"
            "                best = word\n"
            "    return best"
        ),
        tests=[
            example([["w", "wo", "wor", "worl", "world"]], "world"),
            example([["a", "banana", "app", "appl", "ap", "apply", "apple"]], "apple"),
            hidden("an empty box", [[]], ""),
            hidden("nothing can be started", [["abc"]], ""),
            hidden("a chain from a single bead", [["a", "b", "ab", "abc"]], "abc"),
            hidden("no word is one bead long",
                   [["yo", "ew", "fgt", "bolo", "lmm", "vin", "ncj", "wnfw", "qxi", "gengk"]], ""),
            hidden("two chains, the longer one wins",
                   [["m", "mo", "moc", "moch", "mocha", "l", "la", "lat", "latt", "latte",
                     "c", "ca", "cat"]], "latte"),
        ],
    ),
    problem(
        zone=ZONE,
        slug="search-suggestions-system",
        title="Search Suggestions System",
        difficulty="medium",
        prompt=(
            "The toy catalogue suggests as you type. After each letter of the search word, "
            "return up to three products that start with what's been typed so far, "
            "alphabetically. Give one list per letter."
        ),
        example_input=(
            'products = ["mobile", "mouse", "moneypot", "monitor", "mousepad"], '
            'searchWord = "mouse"'
        ),
        example_output=(
            '[["mobile", "moneypot", "monitor"], ["mobile", "moneypot", "monitor"], '
            '["mouse", "mousepad"], …]'
        ),
        entrypoint="suggestedProducts",
        signature=sig("matrix<string>", products="list<string>", searchWord="string"),
        explainer=(
            "**Sort once, then it's three prefixes deep.** With the catalogue in alphabetical "
            "order, everything sharing a prefix sits together — so each answer is the first "
            "three of a contiguous run, and typing another letter only ever narrows it."
        ),
        hint=(
            "There is one list per letter typed, including the first — so the answer has "
            "len(searchWord) entries, and an entry can be empty when nothing matches yet."
        ),
        approach=(
            "1) Sort products. 2) For i in 1..len(searchWord): take the products starting with "
            "searchWord[:i], keep the first three. 3) Collect the lists. Sorting dominates at "
            "O(n log n)."
        ),
        solution=(
            "def suggestedProducts(products, searchWord):\n"
            "    catalogue = sorted(products)\n"
            "    out = []\n"
            "    for i in range(1, len(searchWord) + 1):\n"
            "        prefix = searchWord[:i]\n"
            "        out.append([p for p in catalogue if p.startswith(prefix)][:3])\n"
            "    return out"
        ),
        tests=[
            example([["mobile", "mouse", "moneypot", "monitor", "mousepad"], "mouse"],
                    [["mobile", "moneypot", "monitor"], ["mobile", "moneypot", "monitor"],
                     ["mouse", "mousepad"], ["mouse", "mousepad"], ["mouse", "mousepad"]]),
            example([["havana"], "havana"],
                    [["havana"], ["havana"], ["havana"], ["havana"], ["havana"], ["havana"]]),
            hidden("fewer than three matches",
                   [["bags", "baggage", "banner", "box", "cloths"], "bags"],
                   [["baggage", "bags", "banner"], ["baggage", "bags", "banner"],
                    ["baggage", "bags"], ["bags"]]),
            hidden("one product, one letter", [["a"], "a"], [["a"]]),
            hidden("an empty catalogue still answers once per letter", [[], "ab"], [[], []]),
            hidden("more than three matches all the way",
                   [["aaa", "aab", "aac", "aad"], "aa"],
                   [["aaa", "aab", "aac"], ["aaa", "aab", "aac"]]),
            hidden("the catalogue is not given in order", [["zebra", "zoo"], "z"],
                   [["zebra", "zoo"]]),
        ],
    ),
]

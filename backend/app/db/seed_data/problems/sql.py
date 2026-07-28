"""Toy Kitchen — SQL.

The corner that isn't on the roadmap, and the one problem shape the judge treats
differently. A query is not a function call, so these problems have no entrypoint
and no signature: the `harness_preamble` is the schema, each case's `args` are
the rows to load before the query runs, and `expected` is the result set. See
`app/judge/languages/sql.py`.

Two things follow from grading a result set verbatim. Every query needs an
`ORDER BY` — without one, SQLite's row order is not something a toy can be
marked against. And a fixture is a list of tables, so a problem that joins gets
one entry per table.
"""

from app.db.seed_data.spec import example, hidden, problem

ZONE = "toy-kitchen"

RECIPES_SCHEMA = "CREATE TABLE recipes (rating INTEGER);"

INGREDIENTS_SCHEMA = "CREATE TABLE ingredients (name TEXT);"

PORTIONS_SCHEMA = "CREATE TABLE portions (shelf TEXT, amount INTEGER);"

COOKS_SCHEMA = (
    "CREATE TABLE cooks (id INTEGER, name TEXT);\n"
    "CREATE TABLE dishes (id INTEGER, cook_id INTEGER);"
)

CAKES_SCHEMA = (
    "CREATE TABLE tins (id INTEGER, name TEXT);\n"
    "CREATE TABLE cakes (name TEXT, height INTEGER, tin_id INTEGER);"
)


def _rows(**tables: list[list]) -> list[dict]:
    """One case's fixture — the rows that go in before the query runs.

    Keyword order is table order, which only matters for readability: the guest
    loads them by name.
    """
    return [{"table": name, "rows": rows} for name, rows in tables.items()]


def _ratings(values: list[int]) -> list[dict]:
    return _rows(recipes=[[v] for v in values])


def _names(values: list[str]) -> list[dict]:
    return _rows(ingredients=[[v] for v in values])


PROBLEMS: list[dict] = [
    problem(
        zone=ZONE,
        slug="second-highest-salary",
        title="Second Highest Recipe Rating",
        difficulty="medium",
        prompt=(
            "The toy kitchen keeps a table of recipe ratings. Write a query returning the second "
            "highest distinct rating, or NULL when there isn't one."
        ),
        example_input="ratings = [100, 200, 300]",
        example_output="200",
        language="sql",
        starter_code="SELECT\n  -- your turn, little toy…\n;",
        languages={},
        harness_preamble=RECIPES_SCHEMA,
        explainer=(
            "**Skip the top, take the next.** Order distinct values descending, then offset by "
            "one. A subquery keeps NULL as the answer when the row doesn't exist."
        ),
        hint="DISTINCT matters — repeated top ratings would otherwise hide the runner-up.",
        approach=(
            "1) SELECT DISTINCT rating ORDER BY rating DESC LIMIT 1 OFFSET 1. "
            "2) Wrap it in an outer SELECT so an empty result becomes NULL."
        ),
        solution=(
            "SELECT (\n"
            "  SELECT DISTINCT rating\n"
            "  FROM recipes\n"
            "  ORDER BY rating DESC\n"
            "  LIMIT 1 OFFSET 1\n"
            ") AS second_highest;"
        ),
        tests=[
            example(_ratings([100, 200, 300]), [[200]]),
            example(_ratings([50]), [[None]], "nothing to come second"),
            hidden("the top rating repeats", _ratings([300, 300, 250, 100]), [[250]]),
            hidden("every rating the same", _ratings([80, 80, 80]), [[None]]),
            hidden("an empty kitchen", _ratings([]), [[None]]),
            hidden("out of order, with a gap", _ratings([12, 99, 7, 99, 40]), [[40]]),
            hidden("negatives count too", _ratings([-5, -1, -9]), [[-5]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="duplicate-ingredients",
        title="Duplicate Ingredients",
        difficulty="easy",
        prompt=(
            "The ingredients list has the same thing written down more than once in places. "
            "Return every name that appears at least twice, one per row, alphabetically."
        ),
        example_input='ingredients = ["flour", "sugar", "flour"]',
        example_output='[["flour"]]',
        language="sql",
        starter_code="SELECT\n  -- your turn, little toy…\n;",
        languages={},
        harness_preamble=INGREDIENTS_SCHEMA,
        explainer=(
            "**GROUP BY makes the piles, HAVING throws some away.** Grouping by name gives one "
            "row per distinct ingredient; HAVING then filters those groups on a count, which is "
            "something WHERE cannot do — WHERE runs before the grouping exists."
        ),
        hint=(
            "`WHERE COUNT(*) > 1` is a syntax error, and that's the lesson. The condition "
            "belongs in HAVING. Add an ORDER BY, or the row order is anyone's guess."
        ),
        approach=(
            "1) SELECT name FROM ingredients. 2) GROUP BY name. 3) HAVING COUNT(*) > 1. "
            "4) ORDER BY name."
        ),
        solution=(
            "SELECT name\n"
            "FROM ingredients\n"
            "GROUP BY name\n"
            "HAVING COUNT(*) > 1\n"
            "ORDER BY name;"
        ),
        tests=[
            example(_names(["flour", "sugar", "flour"]), [["flour"]]),
            example(_names(["salt"]), [], "nothing written twice"),
            hidden("an empty list", _names([]), []),
            hidden("two names repeat", _names(["a", "a", "b", "b"]), [["a"], ["b"]]),
            hidden("everything is different", _names(["x", "y", "z"]), []),
            hidden("three of the same still counts once", _names(["q", "q", "q"]), [["q"]]),
            hidden("alphabetical, not insertion order",
                   _names(["zest", "apple", "zest", "apple"]), [["apple"], ["zest"]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="cooks-with-no-dishes",
        title="Cooks With No Dishes",
        difficulty="easy",
        prompt=(
            "Two tables: the cooks, and the dishes each one made. Return the names of the cooks "
            "who have never made anything, alphabetically."
        ),
        example_input="cooks = [[1, 'Pip'], [2, 'Bramble']], dishes = [[10, 1]]",
        example_output='[["Bramble"]]',
        language="sql",
        starter_code="SELECT\n  -- your turn, little toy…\n;",
        languages={},
        harness_preamble=COOKS_SCHEMA,
        explainer=(
            "**Ask for the absence.** A join finds what's there; finding what *isn't* takes "
            "either a LEFT JOIN with `WHERE dishes.id IS NULL`, or a NOT IN against the list of "
            "cooks who did make something. Both are one line."
        ),
        hint=(
            "NOT IN has a trap: if the subquery ever yields a NULL, the whole thing returns "
            "nothing at all. Filter those out, or use NOT EXISTS, which doesn't care."
        ),
        approach=(
            "1) SELECT name FROM cooks. 2) WHERE id NOT IN (SELECT cook_id FROM dishes WHERE "
            "cook_id IS NOT NULL). 3) ORDER BY name."
        ),
        solution=(
            "SELECT name\n"
            "FROM cooks\n"
            "WHERE id NOT IN (\n"
            "  SELECT cook_id FROM dishes WHERE cook_id IS NOT NULL\n"
            ")\n"
            "ORDER BY name;"
        ),
        tests=[
            example(
                _rows(cooks=[[1, "Pip"], [2, "Bramble"], [3, "Nib"]],
                      dishes=[[10, 1], [11, 1]]),
                [["Bramble"], ["Nib"]],
            ),
            example(
                _rows(cooks=[[1, "Pip"]], dishes=[[9, 1]]),
                [],
                "the only cook has been busy",
            ),
            hidden("nobody has cooked anything",
                   _rows(cooks=[[1, "Pip"]], dishes=[]), [["Pip"]]),
            hidden("an empty kitchen", _rows(cooks=[], dishes=[]), []),
            hidden("one cook is busy, the other isn't",
                   _rows(cooks=[[1, "A"], [2, "B"]], dishes=[[1, 2]]), [["A"]]),
            hidden("alphabetical, not by id",
                   _rows(cooks=[[1, "Zed"], [2, "Ada"]], dishes=[]),
                   [["Ada"], ["Zed"]]),
            hidden("a dish with no cook attached",
                   _rows(cooks=[[1, "Pip"]], dishes=[[9, None]]), [["Pip"]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="average-portion-per-shelf",
        title="Average Portion Per Shelf",
        difficulty="easy",
        prompt=(
            "Each portion served is recorded with the shelf it came from. Return each shelf "
            "with its average portion, rounded to two decimal places, ordered by shelf name."
        ),
        example_input="portions = [['top', 10], ['top', 20], ['low', 5]]",
        example_output='[["low", 5.0], ["top", 15.0]]',
        language="sql",
        starter_code="SELECT\n  -- your turn, little toy…\n;",
        languages={},
        harness_preamble=PORTIONS_SCHEMA,
        explainer=(
            "**One row in, one row per group out.** GROUP BY collapses the rows into piles and "
            "AVG summarises each pile. Anything in the SELECT list that isn't inside an "
            "aggregate has to be something you grouped by — otherwise which row would it come "
            "from?"
        ),
        hint=(
            "ROUND(AVG(amount), 2) — the rounding is part of the answer, so a shelf averaging "
            "1.666… must come back as 1.67."
        ),
        approach=(
            "1) SELECT shelf, ROUND(AVG(amount), 2). 2) FROM portions. 3) GROUP BY shelf. "
            "4) ORDER BY shelf."
        ),
        solution=(
            "SELECT shelf, ROUND(AVG(amount), 2) AS average\n"
            "FROM portions\n"
            "GROUP BY shelf\n"
            "ORDER BY shelf;"
        ),
        tests=[
            example(_rows(portions=[["top", 10], ["top", 20], ["low", 5]]),
                    [["low", 5.0], ["top", 15.0]]),
            example(_rows(portions=[["a", 1]]), [["a", 1.0]]),
            hidden("nothing served", _rows(portions=[]), []),
            hidden("an average that isn't whole",
                   _rows(portions=[["a", 1], ["a", 2]]), [["a", 1.5]]),
            hidden("alphabetical, not insertion order",
                   _rows(portions=[["b", 3], ["a", 3]]), [["a", 3.0], ["b", 3.0]]),
            hidden("rounded to two places",
                   _rows(portions=[["s", 1], ["s", 2], ["s", 2]]), [["s", 1.67]]),
            hidden("one shelf, one portion", _rows(portions=[["only", 42]]), [["only", 42.0]]),
        ],
    ),
    problem(
        zone=ZONE,
        slug="tallest-cake-per-tin",
        title="Tallest Cake Per Tin",
        difficulty="medium",
        prompt=(
            "Every cake was baked in one of the tins. For each tin, return its name, the "
            "tallest cake baked in it, and that height. If a tin has two cakes tied for "
            "tallest, return both. Order by tin name, then cake name."
        ),
        example_input=(
            "tins = [[1, 'Round'], [2, 'Square']], "
            "cakes = [['Vic', 10, 1], ['Spo', 12, 1], ['Mud', 7, 2]]"
        ),
        example_output='[["Round", "Spo", 12], ["Square", "Mud", 7]]',
        language="sql",
        starter_code="SELECT\n  -- your turn, little toy…\n;",
        languages={},
        harness_preamble=CAKES_SCHEMA,
        explainer=(
            "**Find the maximum per group, then go back for the rows that hit it.** A GROUP BY "
            "gives you the height but loses which cake it was. So join the cakes to their tins, "
            "and keep each cake whose height equals the maximum for *its own* tin — a "
            "correlated subquery, which is what makes ties come back together."
        ),
        hint=(
            "A tin with no cakes in it doesn't appear at all — an inner join drops it, which is "
            "what the problem asks for. And a cake pointing at a tin that isn't there is "
            "dropped too."
        ),
        approach=(
            "1) SELECT the tin name, cake name and height FROM cakes JOIN tins ON id = tin_id. "
            "2) WHERE height = (SELECT MAX(height) FROM cakes inner WHERE inner.tin_id = "
            "outer.tin_id). 3) ORDER BY tin name, cake name."
        ),
        solution=(
            "SELECT t.name AS tin, c.name AS cake, c.height\n"
            "FROM cakes c\n"
            "JOIN tins t ON t.id = c.tin_id\n"
            "WHERE c.height = (\n"
            "  SELECT MAX(c2.height) FROM cakes c2 WHERE c2.tin_id = c.tin_id\n"
            ")\n"
            "ORDER BY t.name, c.name;"
        ),
        tests=[
            example(
                _rows(tins=[[1, "Round"], [2, "Square"]],
                      cakes=[["Vic", 10, 1], ["Spo", 12, 1], ["Mud", 7, 2]]),
                [["Round", "Spo", 12], ["Square", "Mud", 7]],
            ),
            example(
                _rows(tins=[[1, "Round"]], cakes=[["Vic", 5, 1]]),
                [["Round", "Vic", 5]],
            ),
            hidden("a tin with nothing baked in it",
                   _rows(tins=[[1, "Round"]], cakes=[]), []),
            hidden("an empty kitchen", _rows(tins=[], cakes=[]), []),
            hidden("a tie comes back twice",
                   _rows(tins=[[1, "R"], [2, "S"]],
                         cakes=[["a", 5, 1], ["b", 5, 1], ["c", 9, 2]]),
                   [["R", "a", 5], ["R", "b", 5], ["S", "c", 9]]),
            hidden("a cake whose tin is missing",
                   _rows(tins=[[1, "R"]], cakes=[["a", 1, 2]]), []),
            hidden("ordered by tin, then cake",
                   _rows(tins=[[1, "Zed"], [2, "Ada"]],
                         cakes=[["x", 1, 1], ["y", 2, 2]]),
                   [["Ada", "y", 2], ["Zed", "x", 1]]),
        ],
    ),
]

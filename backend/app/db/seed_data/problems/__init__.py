"""Every problem in the academy, one module per corner of the quest map.

The order here is the order of `ZONES`, which is the order of the roadmap, and
`seed_catalogue` turns position in this list into `sort_order`. So a toy working
top to bottom is following a study path: the arrays that everything else is
built out of, then the two ways to walk them, then the structures, then the
patterns that need all of it.
"""

from app.db.seed_data.problems.advanced_graphs import PROBLEMS as ADVANCED_GRAPHS
from app.db.seed_data.problems.arrays_hashing import PROBLEMS as ARRAYS_HASHING
from app.db.seed_data.problems.backtracking import PROBLEMS as BACKTRACKING
from app.db.seed_data.problems.binary_search import PROBLEMS as BINARY_SEARCH
from app.db.seed_data.problems.bit_manipulation import PROBLEMS as BIT_MANIPULATION
from app.db.seed_data.problems.dp_1d import PROBLEMS as DP_1D
from app.db.seed_data.problems.dp_2d import PROBLEMS as DP_2D
from app.db.seed_data.problems.graphs import PROBLEMS as GRAPHS
from app.db.seed_data.problems.greedy import PROBLEMS as GREEDY
from app.db.seed_data.problems.heap import PROBLEMS as HEAP
from app.db.seed_data.problems.intervals import PROBLEMS as INTERVALS
from app.db.seed_data.problems.linked_list import PROBLEMS as LINKED_LIST
from app.db.seed_data.problems.math_geometry import PROBLEMS as MATH_GEOMETRY
from app.db.seed_data.problems.sliding_window import PROBLEMS as SLIDING_WINDOW
from app.db.seed_data.problems.sql import PROBLEMS as SQL
from app.db.seed_data.problems.stack import PROBLEMS as STACK
from app.db.seed_data.problems.trees import PROBLEMS as TREES
from app.db.seed_data.problems.tries import PROBLEMS as TRIES
from app.db.seed_data.problems.two_pointers import PROBLEMS as TWO_POINTERS

PROBLEMS: list[dict] = [
    *ARRAYS_HASHING,
    *TWO_POINTERS,
    *STACK,
    *BINARY_SEARCH,
    *SLIDING_WINDOW,
    *LINKED_LIST,
    *TREES,
    *TRIES,
    *HEAP,
    *BACKTRACKING,
    *GRAPHS,
    *DP_1D,
    *INTERVALS,
    *GREEDY,
    *ADVANCED_GRAPHS,
    *DP_2D,
    *BIT_MANIPULATION,
    *MATH_GEOMETRY,
    *SQL,
]

__all__ = ["PROBLEMS"]

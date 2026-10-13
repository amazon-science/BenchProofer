#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11299.

Refutes the R/I refinement leg of `assignColumnForms` (the recursive
condition-tree walk that assigns each leaf a column-reference form) modeled in
Solution.lean. There are NO axioms in this bundle: every op is a concrete
structural transformation over the condition tree, so the whole impl region is
R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched recursion instead of running
the real `Query._add_q`:
  The real `_add_q` (django/db/models/sql/query.py) walks a Q-object building a
  WhereNode; exercising it for a single constraint requires a fully set-up
  model class, Meta options, a resolved field/lookup registry, join setup and
  the auth/where machinery — essentially the F2P Django test harness. Building
  that purely to read back which column class each leaf received is impractical
  and would not isolate the modeled behavior. Per the worker prompt, the ORACLE
  is the PATCHED `_add_q` recursion transliterated VERBATIM:

      def _add_q(children, simple_col):
          out = []
          for child in children:
              if is_node(child):                       # isinstance(child, Node)
                  out.append(('group',
                              _add_q(child.children, simple_col)))   # <-- patch
              else:                                    # leaf
                  out.append(('atom', _get_col(simple_col)))
          return out

      def _get_col(simple_col):                        # query.py:71-74
          return 'SimpleCol' if simple_col else 'Col'

  The per-leaf field/lookup/value resolution (`solve_lookup_type`,
  `setup_joins`, `build_lookup`, `JoinPromoter`) is UNCHANGED by the patch and
  does not affect WHICH column form a leaf receives, so it is folded out (a leaf
  is just "this leaf received _get_col(simple_col)"). mapping.md §1/§3/§4.

  The SHADOW is the model from Solution.lean (columnForm / columnForms / formOf)
  transliterated to Python. SHADOW and ORACLE are differential-tested over
  randomly-generated condition trees (the abstraction of arbitrary nested
  Q-objects) and every selector value. Exit 0 iff zero disagreements. stdlib
  only.
"""
import random
import sys

SEED = 11299
N_FUZZ = 100_000

# Column forms (mapping.md §3): SimpleCol <-> 'bare', Col <-> 'qualified'.
BARE = "bare"
QUALIFIED = "qualified"


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def form_of(bare):
    """`formOf` (Solution.lean): selector -> resulting column form."""
    return BARE if bare else QUALIFIED


def column_form(bare, cond):
    """`columnForm` (Solution.lean): assign a column form to one condition.
    cond is ('atom',) or ('group', [child, ...])."""
    if cond[0] == "atom":
        return ("atom", form_of(bare))
    # group: descend with the SAME selector (the threaded-flag behavior)
    return ("group", column_forms(bare, cond[1]))


def column_forms(bare, conds):
    """`columnForms` (Solution.lean): front-recursive over the forest."""
    out = []
    for c in conds:
        out.append(column_form(bare, c))
    return out


# ---- ORACLE: patched query.py _add_q recursion transliterated -------------

def get_col(simple_col):
    """`_get_col` (query.py:71-74), folding the unchanged target/field/alias
    args: returns which column-reference CLASS the leaf gets."""
    return "SimpleCol" if simple_col else "Col"


def add_q(children, simple_col):
    """Patched `_add_q` recursion (query.py:1337-1352, post-patch): the
    recursive call on a Node child forwards `simple_col`."""
    out = []
    for child in children:
        if child[0] == "group":                      # isinstance(child, Node)
            out.append(("group", add_q(child[1], simple_col)))   # <-- the fix
        else:                                        # leaf -> build_filter -> _get_col
            out.append(("atom", get_col(simple_col)))
    return out


# ---- bridge the column-class identity (R-bijection, mapping.md §3) --------

_CLASS_TO_FORM = {"SimpleCol": BARE, "Col": QUALIFIED}


def bridge(oracle_tree):
    """Map the oracle's column-CLASS tags to the Lean ColForm carrier."""
    out = []
    for kind, payload in oracle_tree:
        if kind == "atom":
            out.append(("atom", _CLASS_TO_FORM[payload]))
        else:
            out.append(("group", bridge(payload)))
    return out


# ---- random condition-tree generator (abstracts nested Q-objects) ---------

def gen_forest(rng, depth):
    """A list of conditions: atoms and (depth-bounded) nested groups."""
    n = rng.randint(0, 4)
    forest = []
    for _ in range(n):
        if depth > 0 and rng.random() < 0.45:
            forest.append(("group", gen_forest(rng, depth - 1)))
        else:
            forest.append(("atom",))
    return forest


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Boundary trees: empty, single leaf, single empty group, nested groups,
    # the F2P shape Q(AND-group) | Q(leaf).
    boundary = [
        [],
        [("atom",)],
        [("group", [])],
        [("group", [("atom",)])],
        [("group", [("atom",), ("atom",)]), ("atom",)],          # F2P shape
        [("group", [("group", [("atom",)]), ("atom",)])],        # deep nesting
        [("atom",), ("group", [("atom",), ("group", [("atom",)])])],
    ]

    def check(conds):
        nonlocal count
        for bare in (True, False):
            count += 1
            shadow = column_forms(bare, conds)
            oracle = bridge(add_q(conds, bare))
            if shadow != oracle:
                disagreements.append((bare, conds, shadow, oracle))

    for conds in boundary:
        check(conds)

    for _ in range(N_FUZZ):
        check(gen_forest(rng, depth=4))
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements[:8]))
        return 1
    print("G-CONF OK: R/I shadow of assignColumnForms (columnForm/columnForms/"
          "formOf) agrees with the patched _add_q recursion on %d checks "
          "(%d boundary + fuzz trees x 2 selectors, seed=%d), 0 disagreements."
          % (count, len(boundary), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

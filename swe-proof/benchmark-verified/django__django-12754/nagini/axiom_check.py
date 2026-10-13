#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12754.

The changed selection operation is modeled DEEPLY, not behind a consumed axiom;
this check validates that deep model against the REAL CPython built-in set
algebra it stands for.

  (A-reference) the deep model `selected` (model.py pure region) ==
      `set(old).difference(new).intersection(model)` (the gold patch's
      lines 569-571). For every candidate name `c` (a key of the prior parent
      `old`), the model keeps `c` iff `c not in new and c in model`, which is
      exactly membership in `set(old).difference(new).intersection(model)`.

Field names are modeled as integers in model.py; the soundness of that
relabeling is the R-refinement of mapping.md §2 (the change performs only set
membership / equality / hashing on the names). This check uses the abstract
integer carrier directly — it tests the SET ALGEBRA, which is name-content
independent — and additionally re-runs the equivalence with real `str` field
names to confirm the relabeling is faithful.

Imports nothing repo-specific: only the standard library. Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def qualifies(name, parent_after, child):
    """Reference of model.py `qualifies`: a prior-parent name qualifies iff it
    is withdrawn from the parent (not in parent_after) and re-declared by the
    child (in child)."""
    return (name not in parent_after) and (name in child)


def selected(candidates, parent_after, child):
    """Reference of model.py `selected`: the qualifying subsequence of the
    candidate (prior-parent) names, in candidate order."""
    out = []
    for c in candidates:
        if qualifies(c, parent_after, child):
            out.append(c)
    return out


# --- the A-reference check ----------------------------------------------------

def real_set_expr(old, new, model):
    """The REAL gold-patch built-in set algebra (autodetector.py:569-571):
    set(old).difference(new).intersection(model)."""
    return set(old).difference(new).intersection(model)


def check_reference(old, new, model):
    """Assert the deep model `selected` (as a SET of emitted names) equals the
    REAL set(old).difference(new).intersection(model)."""
    # candidates enumerate the keys of the prior parent dict == set(old)
    candidates = list(dict.fromkeys(old))   # de-dup, preserve order, == set(old)
    model_emitted = set(selected(candidates, set(new), set(model)))
    real = real_set_expr(old, new, model)
    assert model_emitted == real, (
        "selected deep model unsound on old=%r new=%r model=%r: "
        "real set expr gave %r, deep model gives %r"
        % (old, new, model, real, model_emitted))
    # Every emitted name is a prior parent name (a candidate)
    for f in model_emitted:
        assert f in set(old), "emitted %r not a prior parent name" % (f,)


def main():
    # --- boundary cases over small integer name-id universes ------------------
    boundary = [
        # (old, new, model)
        ([], [], []),                                  # all empty
        ([1], [], []),                                 # withdrawn but not clashing
        ([1], [], [1]),                                # the reporter's case: title
        ([1], [1], [1]),                               # kept (not withdrawn) -> none
        ([1, 2], [2], [1]),                            # one withdrawn-and-clashing
        ([1, 2], [2], [1, 2]),                         # 1 qualifies, 2 not withdrawn
        ([1, 2, 3], [3], [1, 2]),                      # two qualify (Magazine-style)
        ([1, 2, 3], [], [1, 2, 3]),                    # all withdrawn-and-clashing
        ([1, 2, 3], [1, 2, 3], [1, 2, 3]),             # nothing withdrawn -> none
        ([1], [], [2]),                                # withdrawn but child names different
        ([1, 2], [1, 2], []),                          # child empty -> none
        ([5, 6, 7], [6], [7, 8]),                      # 7 qualifies; 5 not in child; 6 kept
        (list(range(10)), [0, 1, 2], list(range(5, 10))),
    ]
    for old, new, model in boundary:
        check_reference(old, new, model)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(12754)
    for _ in range(20000):
        universe = list(range(rng.randint(0, 14)))
        rng.shuffle(universe)
        old = [n for n in universe if rng.random() < 0.7]
        new = [n for n in old if rng.random() < 0.6]          # subset-ish of old
        new += [n for n in universe if n not in old and rng.random() < 0.2]
        model = [n for n in universe if rng.random() < 0.5]
        check_reference(old, new, model)

    # --- faithfulness of the int-relabeling: same equivalence with str names --
    str_cases = [
        (["title", "id"], ["id"], ["title"]),                 # the ticket example
        (["title", "name", "id"], ["id"], ["title", "name"]),  # Magazine variant
        (["a", "b", "c"], ["a", "b", "c"], ["a", "b", "c"]),   # nothing withdrawn
        (["x"], [], ["y"]),                                    # no clash
        (["f1", "f2", "f3"], ["f2"], ["f1", "f3", "f4"]),
    ]
    for old, new, model in str_cases:
        check_reference(old, new, model)

    print("G-AX OK: deep model `selected` == real "
          "set(old).difference(new).intersection(model) on %d boundary + "
          "20000 fuzz (int) + %d str-name faithfulness cases, 0 mismatch"
          % (len(boundary), len(str_cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

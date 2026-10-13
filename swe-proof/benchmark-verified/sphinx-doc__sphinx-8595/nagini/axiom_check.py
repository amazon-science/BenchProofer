#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8595.

This bundle consumes **no** `@ContractOnly` axioms: the changed decision is pure
structural logic, modelled deeply. G-AX therefore validates the two DEEP MODELS
(A-references) against the real Python operations they stand for, plus the
absent-vs-empty distinction that is the substance of the fix:

  (A-reference 3.1) the deep model `contains(names, v)` (model.py pure region)
      == Python's built-in membership test `v in names`.

  (A-reference 3.2) the deep model `exclusion_flags(member_names, all_names)`
      (model.py pure region) == the final per-member exclusion vector produced
      by a faithful transcription of the repo `else` loop
      (`sphinx/ext/autodoc/__init__.py:1081-1086`):
          for member in members:               # default skipped = False
              if member.__name__ not in __all__:
                  member.skipped = True
      i.e. each member's final flag is `(name not in __all__)`.

  (the fix) the branch distinction: `self.__all__ is None` is True ONLY for an
      absent (`None`) export list, whereas the pre-patch `not self.__all__` is
      True for BOTH `None` and the empty list `[]`. An empty PRESENT export
      list must be treated as present (excludes every member), which is exactly
      what the model's `all_present=True, all_names=[]` case requires.

Imports nothing repo-specific (only the standard library). Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep models) ---

def contains(names, v):
    """Reference for model.py's `contains`: front-recursive membership."""
    if len(names) == 0:
        return False
    return names[0] == v or contains(names[1:], v)


def exclusion_flags(member_names, all_names):
    """Reference for model.py's `exclusion_flags`: per-member exclusion vector,
    member k excluded iff its name is not an export name."""
    return [not contains(all_names, m) for m in member_names]


# --- faithful transcription of the repo `else` loop --------------------------

class _Member:
    """Mimics ObjectMember's two touched fields: __name__ and skipped (default
    False, per the constructor at sphinx/ext/autodoc/__init__.py:282)."""
    def __init__(self, name):
        self.__name__ = name
        self.skipped = False


def repo_else_loop(member_names, all_names):
    """Exact transcription of the unchanged repo skipping loop (lines
    1081-1086): set skipped=True for members not in __all__, default False
    otherwise. Returns the resulting skipped vector."""
    members = [_Member(n) for n in member_names]
    __all__ = list(all_names)          # a present export list (possibly empty)
    for member in members:
        if member.__name__ not in __all__:
            member.skipped = True
    return [m.skipped for m in members]


# --- the checks --------------------------------------------------------------

def check_contains(names, v):
    observed = (v in names)                       # real Python `in`
    expected = contains(names, v)                 # deep model
    assert observed == expected, (
        "contains deep model unsound: %r in %r gave %r, model gives %r"
        % (v, names, observed, expected))


def check_exclusion(member_names, all_names):
    observed = repo_else_loop(member_names, all_names)   # real repo loop
    expected = exclusion_flags(member_names, all_names)  # deep model
    assert observed == expected, (
        "exclusion_flags deep model unsound on members=%r __all__=%r: "
        "repo loop gave %r, model gives %r"
        % (member_names, all_names, observed, expected))


def check_branch_distinction(all_value):
    """`self.__all__ is None` (post-patch) vs `not self.__all__` (pre-patch)."""
    is_none = (all_value is None)
    falsy = (not all_value)
    if all_value is None:
        assert is_none and falsy, "None must be both `is None` and falsy"
    elif isinstance(all_value, (list, tuple)) and len(all_value) == 0:
        # the crux: an empty PRESENT list is falsy but is NOT None — the
        # pre-patch condition wrongly fires, the post-patch one correctly does
        # not.
        assert (not is_none) and falsy, (
            "empty present __all__ %r must be falsy but not None" % (all_value,))
    else:
        assert (not is_none) and (not falsy), (
            "non-empty present __all__ %r must be neither None nor falsy"
            % (all_value,))


def main():
    # name identifiers (model abstracts strings to ints; here we fuzz both ints
    # and strings to exercise equality-only semantics)
    name_pool_int = list(range(0, 12))
    name_pool_str = ["foo", "bar", "baz", "qux", "_x", "A", "zz", "m1"]

    # --- contains (A-reference 3.1): boundary + fuzz -----------------------
    contains_boundary = [
        ([], 0), ([0], 0), ([0], 1), ([1, 2, 3], 2), ([1, 2, 3], 9),
        ([5, 5, 5], 5), ([5, 5, 5], 6), ([0, 1, 2, 3, 4], 4),
        (["foo"], "foo"), (["foo", "bar"], "baz"), (["a", "a"], "a"),
    ]
    for names, v in contains_boundary:
        check_contains(names, v)

    rng = random.Random(8595)
    for _ in range(20000):
        pool = name_pool_int if rng.random() < 0.5 else name_pool_str
        n = rng.randint(0, 8)
        names = [rng.choice(pool) for _ in range(n)]
        v = rng.choice(pool)
        check_contains(names, v)

    # --- exclusion_flags (A-reference 3.2): boundary -----------------------
    excl_boundary = [
        ([], []),                         # no members, no exports
        (["foo", "bar", "baz"], []),      # the F2P case: empty __all__ -> all excluded
        (["foo", "bar", "baz"], ["foo", "bar", "baz"]),   # all listed -> none excluded
        (["foo", "bar", "baz"], ["bar"]),                 # partial
        (["foo", "bar", "baz"], ["zzz"]),                 # disjoint -> all excluded
        (["foo", "foo"], ["foo"]),        # duplicate member names
        (["a"], ["a", "b", "c"]),         # __all__ superset
        ([0, 1, 2], []), ([0, 1, 2], [1]), ([0, 1, 2], [0, 1, 2]),
    ]
    for members, exports in excl_boundary:
        check_exclusion(members, exports)

    # --- exclusion_flags: fuzz ---------------------------------------------
    for _ in range(20000):
        pool = name_pool_int if rng.random() < 0.5 else name_pool_str
        nm = rng.randint(0, 8)
        members = [rng.choice(pool) for _ in range(nm)]
        na = rng.randint(0, 6)
        exports = [rng.choice(pool) for _ in range(na)]
        check_exclusion(members, exports)

    # --- the fix: is-None vs truthiness ------------------------------------
    for all_value in [None, [], (), ["foo"], ["foo", "bar"], ("a",), [0]]:
        check_branch_distinction(all_value)

    print("G-AX OK: contains == Python `in` and exclusion_flags == repo skip "
          "loop over %d boundary + 40000 fuzz cases; is-None-vs-truthiness "
          "distinction holds for None/[]/present lists."
          % (len(contains_boundary) + len(excl_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

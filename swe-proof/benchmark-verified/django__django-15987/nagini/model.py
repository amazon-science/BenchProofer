"""Twin-artifact model for django__django-15987.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configured collection of directory entries is scanned to decide whether a
  particular default directory is already present in that collection.  The
  decision is a duplicate-detection guard: the default directory is reported as
  present exactly when one of the configured entries denotes the SAME directory
  path as the default one.

  Each configured entry carries two observable facts:

    * ``value_matches`` — whether that entry's directory PATH STRING equals the
      default directory's path string.  Two entries denote the same directory
      precisely when their path strings are equal, so this is the only fact a
      correct presence test may depend on.

    * ``is_path_object`` — whether that entry is supplied as a rich path object
      rather than as a plain path string.  A rich path object and a plain
      string are never the same Python value even when they denote the same
      directory, so a naive identity/value comparison against the entry object
      would silently disagree with the path-string comparison for such an
      entry.

  The presence test must compare by directory path string, so its outcome
  depends ONLY on ``value_matches``: the default directory is present exactly
  when some configured entry's path string equals the default one's, REGARDLESS
  of whether that entry happens to be a rich path object or a plain string.  In
  particular a rich path object whose path string equals the default directory's
  is detected just like the equivalent plain string would be.

The configured collection is a list of directory entries in the repository;
here each entry is reduced to the two booleans above, carried as two parallel
read-only ``List[bool]``.  The presence test mutates nothing.  The whole-list
predicate is carried by a front-recursive ``@Pure`` fold over ``PSeq[bool]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the presence test is modelled deeply over concrete
# booleans via the front-recursive fold `any_match`; nothing opaque is consumed.
# The faithfulness of the per-entry abstraction — that comparing entries by
# their path string is exactly value equality, and that a rich path object is
# never the identical value as a plain path string — is an A-reference checked
# out-of-band by axiom_check.py / G-AX against the real path machinery, not an
# axiom the proof depends on.)
# axioms-end


# pure-start
@Pure
def any_match(eqs: PSeq[bool]) -> bool:
    """Whether some configured entry's path string equals the default
    directory's path string: the disjunction of the per-entry value matches.
    Front-recursive so a single unfold is available per loop step."""
    if len(eqs) == 0:
        return False
    return eqs[0] or any_match(eqs.drop(1))
# pure-end


def default_dir_is_listed(value_matches: List[bool],
                          is_path_object: List[bool]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value_matches), 1 / 2))
    Requires(Acc(list_pred(is_path_object), 1 / 2))
    Requires(len(value_matches) == len(is_path_object))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value_matches), 1 / 2))
    Ensures(Acc(list_pred(is_path_object), 1 / 2))
    # Both parallel inputs are read-only: unchanged in length and content.
    Ensures(ToSeq(value_matches) == Old(ToSeq(value_matches)))
    Ensures(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
    # The default directory is present exactly when some configured entry's path
    # string equals the default one's.  The right-hand side names ONLY
    # value_matches: `is_path_object` does NOT appear, so the outcome is pinned
    # independently of whether matching entries are rich path objects — no
    # verifying implementation may let path-object-ness suppress a detection.
    Ensures(Result() == any_match(ToSeq(value_matches)))
    # post-conditions-end
    # impl-start
    result = False
    i = len(value_matches)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value_matches), 1 / 2))
        Invariant(Acc(list_pred(is_path_object), 1 / 2))
        Invariant(ToSeq(value_matches) == Old(ToSeq(value_matches)))
        Invariant(ToSeq(is_path_object) == Old(ToSeq(is_path_object)))
        Invariant(len(value_matches) == len(is_path_object))
        Invariant(0 <= i and i <= len(value_matches))
        Invariant(result == any_match(ToSeq(value_matches).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(value_matches).drop(i - 1)[0] == value_matches[i - 1])
        Assert(ToSeq(value_matches).drop(i - 1).drop(1) ==
               ToSeq(value_matches).drop(i))
        # Compare by path string (the entry coerced to its path string equals
        # the default directory's path string).
        if value_matches[i - 1]:
            result = True
        i = i - 1
    return result
    # impl-end

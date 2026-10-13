"""Twin-artifact model for pylint-dev__pylint-7277.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A startup routine normalises the module search path before analysis. The
  search path is a non-empty ordered list of path entries. The routine may
  remove the leading entry, but ONLY when that leading entry denotes the
  current working directory in one of its three canonical spellings: the empty
  string, the single dot, or the literal current-directory path. A leading
  entry that denotes any other location is preserved (it must not be dropped).

  Independently of that decision, an environment-driven adjustment may remove
  one further entry from the front region of the (possibly already shortened)
  list: either the new leading entry, or the entry immediately after it. This
  environment-driven adjustment is presented to the routine as a constant
  selector; the routine applies it verbatim after the leading-entry decision.

Path entries are modelled as `List[int]` (Nagini bans `str` indexing): each
distinct path string is a distinct integer code, with two reserved codes for
the empty string (0) and the single dot (1); the current-directory path is the
integer `cwd_code`. The resulting list contents are pinned exactly by the
specification, carried over `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axioms: the leading-entry decision is a membership test on a list entry;
# the environment-driven adjustment is an input selector, the working directory
# is an input code, and every operation is expressed directly over the
# path-entry sequence.)
# axioms-end


# pure-start
@Pure
def is_cwd_like(entry: int, cwd_code: int) -> bool:
    """A leading entry denotes the current working directory iff it is the
    empty string (code 0), the single dot (code 1), or the cwd path code."""
    return entry == 0 or entry == 1 or entry == cwd_code


@Pure
def remove_at(s: PSeq[int], i: int) -> PSeq[int]:
    """The sequence `s` with the element at index `i` removed (total: a
    non-removable index leaves `s` unchanged)."""
    if 0 <= i and i < len(s):
        return s.take(i) + s.drop(i + 1)
    return s


@Pure
def after_lead(s: PSeq[int], cwd_code: int) -> PSeq[int]:
    """The list after the leading-entry decision: drop index 0 only when the
    leading entry denotes the current working directory; otherwise keep it
    (total: an empty list is unchanged)."""
    if len(s) >= 1 and is_cwd_like(s[0], cwd_code):
        return s.drop(1)
    return s


@Pure
def expected_path(s: PSeq[int], cwd_code: int, pp: int) -> PSeq[int]:
    """The fully normalised list: the leading-entry decision, then the
    environment-driven adjustment `pp` (0 = none, 1 = remove new leading entry,
    2 = remove the entry immediately after the new leading entry)."""
    if pp == 1:
        return after_lead(s, cwd_code).drop(1)
    if pp == 2:
        return remove_at(after_lead(s, cwd_code), 1)
    return after_lead(s, cwd_code)
# pure-end


def normalize_search_path(path: List[int], cwd_code: int, pp: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(len(path) >= 3)
    Requires(0 <= pp and pp <= 2)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the normalised list: the leading entry is dropped
    # only when it denotes the current working directory, then the unchanged
    # environment-driven adjustment is applied.
    Ensures(ToSeq(Result()) == expected_path(ToSeq(path), cwd_code, pp))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

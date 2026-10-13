"""Twin-artifact model for django__django-11477.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a URL pattern recognizes an incoming path, it reports the captured named
  groups as a keyword mapping and (separately) a sequence of positional
  captures. A named group is "optional": the pattern can succeed even when that
  group does not participate, in which case the group has NO captured value (it
  is absent / unset), as opposed to having captured the empty string.

  The reported keyword mapping must contain an entry ONLY for those named groups
  that actually captured a value; a named group that did not participate
  contributes no entry at all -- it must not appear carrying an unset/absent
  value. Each retained entry keeps its captured value verbatim.

  The reported positional sequence is chosen against the *retained* keyword
  mapping: if at least one named group captured a value, the positional captures
  are discarded (an empty sequence is reported); only when no named group
  captured a value are the positional captures reported.

  The consequence that matters: when a path is recognized by a pattern with an
  optional named group that did not participate, the reported keyword mapping
  omits that group entirely rather than reporting it with an absent value -- so a
  caller that re-derives a path from these captures recovers the original path
  for URLs with missing optional arguments (the translate_url consequence the
  issue describes).

Modelling choices (Nagini fragment):
  * The named-group capture mapping is modelled as two parallel sequences:
    ``keys`` (the group-name tokens, distinct) and ``vals`` (the parallel
    captured values). A reserved sentinel value ``ABSENT`` in ``vals[i]`` models
    a named group that did not participate (real Python ``None``); any other
    value models a real captured value. Captured strings are irrelevant beyond
    identity, so integer tokens are the faithful carrier (mapping.md §2).
  * The positional captures are a ``List[int]``.
  * The result is the triple (retained keyword keys, retained keyword values,
    reported positional captures): the parallel key/value sequences of the
    reported keyword mapping together with the reported positional sequence. An
    additional path-tail component carried alongside in the full operation is
    unchanged by this behaviour and is omitted from the model.

No string indexing is used (Nagini bans it). The whole behaviour is modelled
deeply (the per-entry retention fold is spelled out); there is no axiomatised
callee. Sequence folds are front-recursive so a single unfold is available per
loop step. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms. The named-group retention filter and the keyword/positional choice
# are the behaviour under specification and are modelled deeply (the
# `kept_keys`/`kept_vals` folds and the impl region). The only operations the
# behaviour composes are an absence test and sequence construction, ordinary
# operations with their real Python semantics; there is no unchanged opaque
# callee to axiomatise.
# axioms-end


# pure-start
@Pure
def absent() -> int:
    """The reserved sentinel modelling a named group that did NOT participate
    (real Python ``None`` as that group's captured value). A captured value is
    any value other than this sentinel."""
    return -1


@Pure
def kept_keys(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """The retained group-name tokens: the subsequence of `keys` at positions
    whose parallel value is NOT the absence sentinel, order preserved.
    Front-recursive so a single unfold is available per loop step."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return keys.take(0)
    if vals[0] == absent():
        return kept_keys(keys.drop(1), vals.drop(1))
    return PSeq(keys[0]) + kept_keys(keys.drop(1), vals.drop(1))


@Pure
def kept_vals(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """The retained captured values: the subsequence of `vals` at positions that
    are NOT the absence sentinel, order preserved (parallel to `kept_keys`)."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return vals.take(0)
    if vals[0] == absent():
        return kept_vals(keys.drop(1), vals.drop(1))
    return PSeq(vals[0]) + kept_vals(keys.drop(1), vals.drop(1))
# pure-end


def select_captures(keys: List[int],
                   vals: List[int],
                   positional: List[int]) -> Tuple[List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(Acc(list_pred(vals), 1 / 2))
    Requires(Acc(list_pred(positional), 1 / 2))
    # The named-group capture mapping: one captured value per named group.
    Requires(len(keys) == len(vals))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs retain their fractional permission (never mutated).
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(vals), 1 / 2))
    Ensures(Acc(list_pred(positional), 1 / 2))
    # The mapping invariant survives (one captured value per named group).
    Ensures(len(keys) == len(vals))
    # The reported keyword mapping (parallel key / value sequences) and the
    # reported positional captures.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # The reported keyword mapping retains EXACTLY the named groups that captured
    # a value -- those whose value is not the absence sentinel -- in order,
    # carrying their captured value verbatim. A non-participating named group
    # contributes no entry (it is omitted, NOT reported with an absent value).
    Ensures(ToSeq(Result()[0]) == kept_keys(ToSeq(keys), ToSeq(vals)))
    Ensures(ToSeq(Result()[1]) == kept_vals(ToSeq(keys), ToSeq(vals)))
    # The absence sentinel never survives into the reported keyword values.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(Result()[1]),
        ToSeq(Result()[1])[i] != absent()),
        [[ToSeq(Result()[1])[i]]])))
    # The reported positional captures are chosen against the RETAINED mapping:
    # if any named group captured a value the positional report is empty,
    # otherwise it is the input positional captures verbatim.
    Ensures(Implies(len(Result()[0]) != 0,
                    ToSeq(Result()[2]) == ToSeq(positional).take(0)))
    Ensures(Implies(len(Result()[0]) == 0,
                    ToSeq(Result()[2]) == ToSeq(positional)))
    # post-conditions-end
    # impl-start
    # Pre-fix skeleton: the named-group mapping is reported in full -- every
    # named group, including those that did NOT participate (whose value is the
    # absence sentinel), is kept. The keyword/positional choice is made against
    # this UNFILTERED mapping (non-empty iff the pattern has any named group at
    # all). This is the buggy behaviour the spec must reject.
    r_keys = []  # type: List[int]
    r_vals = []  # type: List[int]
    i = len(keys)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(Acc(list_pred(vals), 1 / 2))
        Invariant(Acc(list_pred(r_keys)))
        Invariant(Acc(list_pred(r_vals)))
        Invariant(len(keys) == len(vals))
        Invariant(0 <= i and i <= len(keys))
        Invariant(ToSeq(r_keys) == ToSeq(keys).drop(i))
        Invariant(ToSeq(r_vals) == ToSeq(vals).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        k = keys[i - 1]
        v = vals[i - 1]
        Assert(ToSeq(keys).drop(i - 1)[0] == k)
        Assert(ToSeq(vals).drop(i - 1)[0] == v)
        Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
        Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
        r_keys = [k] + r_keys
        r_vals = [v] + r_vals
        i = i - 1
    args = []  # type: List[int]
    if len(r_keys) == 0:
        j = 0
        while j < len(positional):
            # invariants-start
            Invariant(Acc(list_pred(positional), 1 / 2))
            Invariant(Acc(list_pred(args)))
            Invariant(0 <= j and j <= len(positional))
            Invariant(ToSeq(args) == ToSeq(positional).take(j))
            Invariant(MustTerminate(len(positional) - j + 1))
            # invariants-end
            args = args + [positional[j]]
            j = j + 1
    return r_keys, r_vals, args
    # impl-end

"""Twin-artifact model for pytest-dev__pytest-8399.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A test framework automatically generates helper fixtures on behalf of the
  user (one per setup/teardown hook of a test module or class). These generated
  helpers carry no documentation of their own, so they should be treated as
  *internal* and kept out of the default fixture listing.

  The framework's fixture listing applies one visibility rule: at the default
  verbosity a fixture is omitted exactly when its name begins with the privacy
  marker code point `_` (U+005F); at a raised verbosity every fixture is shown.

  Therefore a generated helper's name must be chosen so that it begins with that
  privacy marker. Concretely, the generated name is the privacy marker code
  point followed by the descriptive label (a constant middle segment derived
  from the hook plus the owning object's qualified name). The descriptive label is
  carried through unchanged; only the leading privacy marker is guaranteed.

  Consequences the consumer relies on:
    * the generated name begins with the privacy marker `_`, so the default
      fixture listing omits it (no spurious undocumented-fixture line); and
    * a raised-verbosity listing still shows it; and
    * dropping the leading marker recovers exactly the descriptive label, so the
      name is the descriptive label with the marker prepended, never an
      unrelated or truncated string.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The listing's visibility rule is an unchanged piece of framework logic and is
modelled DEEPLY as the pure predicate `listed`; the name construction is a pure
prepend, spelled out in full. There is no axiomatized callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: both the name construction and the listing's visibility rule are
#  modeled deeply; there is no unchanged stdlib callee the proof consumes.)
# axioms-end


# pure-start
PRIVACY_MARKER = 95  # the code point '_'


@Pure
def begins_private(name: PSeq[int]) -> bool:
    """True iff the name begins with the privacy marker code point."""
    return len(name) > 0 and name[0] == PRIVACY_MARKER


@Pure
def listed(name: PSeq[int], verbose: int) -> bool:
    """The framework's listing visibility rule (unchanged framework logic):
    at the default (non-raised) verbosity a fixture is omitted exactly when its
    name begins with the privacy marker; at a raised verbosity it is always
    shown. Returns True iff the fixture named `name` appears in the listing."""
    if verbose > 0:
        return True
    return not begins_private(name)
# pure-end


def generated_fixture_name(label: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(label), 1 / 2))
    # the descriptive label is genuine and not itself already private: it is
    # non-empty and its first code point is an ordinary (non-marker) one.
    Requires(len(label) > 0)
    Requires(label[0] != PRIVACY_MARKER)
    # TERMINATION: constructing the generated name is one bounded pass over the
    # FINITE descriptive label and MUST actually complete (total correctness):
    # the real name construction is an f-string evaluation that always returns
    # the name to the fixture decorator. Under partial-correctness semantics a
    # diverging body (e.g. an endless loop inserted before the return) satisfies
    # every Ensures vacuously yet never delivers the generated name, so the
    # fixture is never registered and the --fixtures F2P is not resolved. This
    # obligation rejects any such implementation.
    Requires(MustTerminate(len(label) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The generated name is the descriptive label with the privacy marker
    # prepended: marker first, then the label unchanged.
    Ensures(len(Result()) == len(label) + 1)
    Ensures(ToSeq(Result())[0] == PRIVACY_MARKER)
    Ensures(ToSeq(Result()).drop(1) == ToSeq(label))
    # Hence the generated name begins with the privacy marker ...
    Ensures(begins_private(ToSeq(Result())))
    # ... so the default-verbosity listing omits it, while a raised-verbosity
    # listing still shows it.
    Ensures(not listed(ToSeq(Result()), 0))
    Ensures(listed(ToSeq(Result()), 1))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the generated name is the descriptive label itself,
    # with no leading privacy marker prepended.
    result = []  # type: List[int]
    i = 0
    while i < len(label):
        # invariants-start
        Invariant(Acc(list_pred(label), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(label))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(label).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(label) - i,
        # discharging MustTerminate(len(label) + 2) from the precondition.
        Invariant(MustTerminate(len(label) - i + 1))
        # invariants-end
        result = result + [label[i]]
        i = i + 1
    return result
    # impl-end

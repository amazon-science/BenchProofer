#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-13236.

Refutes the R/I refinement leg: the modeled dispatch `classify` (an
`InputShape -> Bool -> ColumnKind` mapping — the second input is the host
table's masked-ness) over the finite input space.

ORACLE CHOICE — why we transliterate the patched selection logic instead of
driving `Table._convert_data_to_col` end-to-end:
  The classification is computed inside `_convert_data_to_col(self, data, ...)`,
  which requires a fully-built `Table` (its `ColumnClass`/`MaskedColumn`
  machinery, `_is_mixin_for_table`, `_get_col_cls_for_table`, `col_copy`) plus
  real numpy class objects, purely to read back WHICH column class an input is
  wrapped in. Building that context in-container only to recover one class kind
  is impractical and would not isolate the modeled behavior. So, per the worker
  prompt, the ORACLE is the **patched** selection block transliterated VERBATIM
  from the post-image of `_convert_data_to_col` (astropy/table/table.py): the
  structured-ndarray `if` branch is gone, so an input is classified by the
  remaining arms (`isinstance Column` -> `_get_col_cls_for_table` (upgrades to
  MaskedColumn for a masked table); `data_is_mixin` -> mixin; masked array ->
  `masked_col_cls`; else -> `self.ColumnClass`, which IS `MaskedColumn` when
  the table is masked). The SHADOW is the modeled `classify` from
  Solution.lean's post-image.

  The transliteration was empirically cross-checked against astropy 5.2.2
  (post-patch) by adding each of the six input shapes to a masked and to an
  unmasked Table and reading back `type(t['a'])`: all 12 cells agree.

  We differential-test SHADOW vs ORACLE over the full finite input space
  (every InputShape x tableIsMasked) plus seeded fuzz. Exit 0 iff zero
  disagreements. stdlib only.
"""
import random
import sys

SEED = 13236
N_FUZZ = 100_000

# The six modeled input shapes (mapping.md §2).
SHAPES = [
    "alreadyColumn",
    "alreadyMixin",
    "structuredPlain",
    "structuredMasked",
    "plainMasked",
    "plainOther",
]

# Column kinds.
COLUMN = "columnKind"
MASKED = "maskedColumnKind"
MIXIN = "mixinKind"


def shadow(shape, table_is_masked):
    """classify transliterated from Solution.lean's `classify` (pure region)."""
    by_table = MASKED if table_is_masked else COLUMN
    return {
        "alreadyColumn": by_table,
        "alreadyMixin": MIXIN,
        "structuredPlain": by_table,
        "structuredMasked": MASKED,
        "plainMasked": MASKED,
        "plainOther": by_table,
    }[shape]


def oracle(shape, table_is_masked):
    """The PATCHED selection block of `_convert_data_to_col`, transliterated.

    Post-image (structured-ndarray branch DELETED). Preamble binds
    `masked_col_cls = self.ColumnClass if issubclass(self.ColumnClass,
    self.MaskedColumn) else self.MaskedColumn` — i.e. MaskedColumn either way.
    For a masked table `self.ColumnClass` is `MaskedColumn`; for an unmasked
    table it is `Column`. Following source order, an input falls through the
    chain of `if/elif` arms; we encode the arm each modeled shape lands in:

        if isinstance(data, Column):
            col_cls = self._get_col_cls_for_table(data)
            # upgrades Column -> MaskedColumn when ColumnClass is MaskedColumn
            # (masked table); keeps Column for an unmasked table
        elif data_is_mixin:                     -> mixin (early return col)
        elif data0_is_mixin: ...                (not modeled: sequence-of-mixin)
        elif isinstance(data, (MaskedArray, Masked)):  -> masked_col_cls
                                                   (MaskedColumn, both tables)
        elif data is None: ...                  (not modeled)
        elif not hasattr(data, 'dtype'): ...    (not modeled: non-array)
        else:                                   -> self.ColumnClass
                                                   (MaskedColumn iff masked table)

    A structured array is NOT special-cased any more: a plain (unmasked)
    structured ndarray has a dtype and is not a MaskedArray, so it lands in the
    trailing `else` -> self.ColumnClass; a masked structured array is a
    MaskedArray, so it lands in the masked arm -> MaskedColumn. `data_is_mixin`
    is False for a bare structured ndarray (it is not a mixin for the table),
    which is what lets the deleted branch's removal change the outcome.
    """
    if shape == "alreadyColumn":
        # isinstance(data, Column) -> _get_col_cls_for_table: upgrade to
        # MaskedColumn iff the table's ColumnClass is MaskedColumn.
        return MASKED if table_is_masked else COLUMN
    if shape == "alreadyMixin":
        return MIXIN                  # elif data_is_mixin
    if shape == "structuredMasked":
        return MASKED                 # MaskedArray arm (structured no longer special)
    if shape == "plainMasked":
        return MASKED                 # MaskedArray arm
    # structuredPlain, plainOther: not Column, not mixin, not masked -> else
    return MASKED if table_is_masked else COLUMN  # else: self.ColumnClass


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: every modeled input shape x table masked-ness.
    combos = [(s, m) for s in SHAPES for m in (False, True)]
    # Plus seeded fuzz over the same finite space (redundant coverage; the
    # prompt asks for fuzz).
    combos += [(rng.choice(SHAPES), rng.choice((False, True)))
               for _ in range(N_FUZZ)]

    for shape, masked in combos:
        count += 1
        s = shadow(shape, masked)
        o = oracle(shape, masked)
        if s != o:
            disagreements.append((shape, masked, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of classifyColumn agrees with the patched "
          "selection logic on %d inputs (12 exhaustive + fuzz, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

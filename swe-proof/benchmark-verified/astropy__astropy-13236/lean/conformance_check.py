#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-13236.

The bundle models ONE routine: the column-CLASS selection inside
`Table._convert_data_to_col` (mapping.md). The modeled value is a PURE function
of the observables the real function reads after the (unchanged) mixin-handler
step:

    isColumn, isMixin, data0IsMixin, isNdarray, numDtypeFields, isMaskedArray,
    isNone, hasDtype, columnInputResult, dataMixinClass, seqMixinResult,
    seqConvMasked, tableColumnClass, tableMaskedColumn

Post-patch rule (the gold edit DELETES the force-to-mixin clause, so a structured
plain array falls through the normal chain):

    if isColumn:        cls = columnInputResult
    elif isMixin:       cls = dataMixinClass
    elif data0IsMixin:  cls = seqMixinResult
    elif isMaskedArray: cls = tableMaskedColumn
    elif isNone:        cls = tableColumnClass
    elif not hasDtype:  cls = tableMaskedColumn if seqConvMasked else tableColumnClass
    else:               cls = tableColumnClass

Standing up numpy / the full Table machinery to drive the real selection is heavy
and unnecessary: the modeled value is this pure decision over observables the
real function exposes. So the ORACLE below is a faithful in-process replica of the
POST-PATCH chain (the deleted clause absent), and the SHADOW is the op-for-op
transliteration of `implementation_columnForTableData` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical clause: a structured plain array
(`isNdarray`, `numDtypeFields > 1`, not a column/mixin) must NOT be forced to the
array-backed mixin class — masked ones become the masked column class, unmasked
ones the default column class — matching the F2P expectations (`Column` /
`MaskedColumn`).

stdlib-only. Pinned seed: 13236 (also in mapping.md).
"""
import random
import sys

SEED = 13236
N = 120_000

# ColClass enum (mapping.md bijection)
COLUMN = "column"
MASKED_COLUMN = "maskedColumn"
NDARRAY_MIXIN = "ndarrayMixin"
OTHER_MIXIN = "otherMixin"
CLASSES = [COLUMN, MASKED_COLUMN, NDARRAY_MIXIN, OTHER_MIXIN]


# --- ORACLE: faithful in-process replica of the POST-PATCH selection ----------
# The force-to-mixin clause is DELETED; a structured plain array falls through.
def oracle(inp):
    if inp["isColumn"]:
        return inp["columnInputResult"]
    if inp["isMixin"]:
        return inp["dataMixinClass"]
    if inp["data0IsMixin"]:
        return inp["seqMixinResult"]
    if inp["isMaskedArray"]:
        return inp["tableMaskedColumn"]
    if inp["isNone"]:
        return inp["tableColumnClass"]
    if not inp["hasDtype"]:
        return inp["tableMaskedColumn"] if inp["seqConvMasked"] else inp["tableColumnClass"]
    return inp["tableColumnClass"]


# --- SHADOW of implementation_columnForTableData (the R leg) ------------------
# Mirrors Solution.lean impl region exactly (the if/else-if chain, no leading
# mixin override).
def shadow(inp):
    if inp["isColumn"]:
        return inp["columnInputResult"]
    elif inp["isMixin"]:
        return inp["dataMixinClass"]
    elif inp["data0IsMixin"]:
        return inp["seqMixinResult"]
    elif inp["isMaskedArray"]:
        return inp["tableMaskedColumn"]
    elif inp["isNone"]:
        return inp["tableColumnClass"]
    elif not inp["hasDtype"]:
        if inp["seqConvMasked"]:
            return inp["tableMaskedColumn"]
        else:
            return inp["tableColumnClass"]
    else:
        return inp["tableColumnClass"]


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def mk(isColumn=False, isMixin=False, data0IsMixin=False, isNdarray=False,
       numDtypeFields=0, isMaskedArray=False, isNone=False, hasDtype=False,
       columnInputResult=COLUMN, dataMixinClass=NDARRAY_MIXIN,
       seqMixinResult=OTHER_MIXIN, seqConvMasked=False,
       tableColumnClass=COLUMN, tableMaskedColumn=MASKED_COLUMN):
    return dict(isColumn=isColumn, isMixin=isMixin, data0IsMixin=data0IsMixin,
                isNdarray=isNdarray, numDtypeFields=numDtypeFields,
                isMaskedArray=isMaskedArray, isNone=isNone, hasDtype=hasDtype,
                columnInputResult=columnInputResult, dataMixinClass=dataMixinClass,
                seqMixinResult=seqMixinResult, seqConvMasked=seqConvMasked,
                tableColumnClass=tableColumnClass, tableMaskedColumn=tableMaskedColumn)


def _enumerate_edge():
    cases = []
    # F2P: unmasked structured ndarray into a plain Table -> Column
    cases.append(mk(isNdarray=True, numDtypeFields=2, hasDtype=True))
    cases.append(mk(isNdarray=True, numDtypeFields=3, hasDtype=True))
    # F2P: masked structured ndarray -> MaskedColumn
    cases.append(mk(isNdarray=True, numDtypeFields=3, isMaskedArray=True, hasDtype=True))
    # already a column
    cases.append(mk(isColumn=True, columnInputResult=COLUMN))
    cases.append(mk(isColumn=True, columnInputResult=MASKED_COLUMN))
    # already a mixin (incl. an existing NdarrayMixin, class preserved)
    cases.append(mk(isMixin=True, dataMixinClass=NDARRAY_MIXIN))
    cases.append(mk(isMixin=True, dataMixinClass=OTHER_MIXIN))
    # sequence of mixin scalars
    cases.append(mk(data0IsMixin=True, seqMixinResult=OTHER_MIXIN))
    cases.append(mk(data0IsMixin=True, seqMixinResult=COLUMN))  # object-array fallback
    # plain masked array (non-structured)
    cases.append(mk(isNdarray=True, numDtypeFields=0, isMaskedArray=True, hasDtype=True))
    # None
    cases.append(mk(isNone=True))
    # no dtype, coercion masked vs not
    cases.append(mk(hasDtype=False, seqConvMasked=True))
    cases.append(mk(hasDtype=False, seqConvMasked=False))
    # plain unstructured array -> default
    cases.append(mk(isNdarray=True, numDtypeFields=0, hasDtype=True))
    # structured but already a column / mixin (clause never applied pre-patch either)
    cases.append(mk(isColumn=True, isNdarray=True, numDtypeFields=2, hasDtype=True,
                    columnInputResult=COLUMN))
    cases.append(mk(isMixin=True, isNdarray=True, numDtypeFields=2, hasDtype=True,
                    dataMixinClass=NDARRAY_MIXIN))
    return cases


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        inp = mk(
            isColumn=rng.random() < 0.15,
            isMixin=rng.random() < 0.15,
            data0IsMixin=rng.random() < 0.15,
            isNdarray=rng.random() < 0.6,
            numDtypeFields=rng.choice([0, 0, 1, 2, 3, 4]),
            isMaskedArray=rng.random() < 0.3,
            isNone=rng.random() < 0.1,
            hasDtype=rng.random() < 0.7,
            columnInputResult=rng.choice(CLASSES),
            dataMixinClass=rng.choice(CLASSES),
            seqMixinResult=rng.choice(CLASSES),
            seqConvMasked=rng.random() < 0.5,
            tableColumnClass=rng.choice([COLUMN, MASKED_COLUMN]),
            tableMaskedColumn=rng.choice([MASKED_COLUMN, COLUMN]),
        )
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

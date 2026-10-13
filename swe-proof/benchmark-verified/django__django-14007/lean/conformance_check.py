#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14007.

The bundle models ONE routine: the rows `SQLInsertCompiler.execute_sql` returns
for a creating write (mapping.md). The modeled value is a PURE function of the
observables the real method exposes after the (unchanged) backend pathway has
produced the raw rows:

    returningFields  — the returned fields, each with its converter chain
    canBatch         — can_return_rows_from_bulk_insert and len(objs) > 1
    canColumns       — can_return_columns_from_insert
    batchRows        — fetch_returned_insert_rows(cursor)
    columnsRow       — fetch_returned_insert_columns(cursor, returning_params)
    lastIdRow        — (last_insert_id(...),)

Post-patch return path:

    if not returning_fields:            return []
    if canBatch:                        rows = batchRows
    elif canColumns:                    rows = [columnsRow]
    else:                               rows = [lastIdRow]
    cols = [field.get_col(...) for field in returning_fields]
    converters = get_converters(cols)
    if converters:                      rows = list(apply_converters(rows, converters))
    return rows

Standing up a real database connection + backend ops is heavy and unnecessary:
the modeled value is this pure post-processing over observables the real method
exposes. So the ORACLE below is a faithful in-process replica of the POST-PATCH
return path (converters applied to the fetched rows), and the SHADOW is the
op-for-op transliteration of `implementation_insertReturnedRows` (Solution.lean
impl region), per refinement.md.

This genuinely tests the soundness-critical step: a returning field whose
converter wraps the raw value must see that wrapping applied to the value a
creating write returns — matching the F2P expectation (`from_db_value` runs on
the inserted PK). A field with no converter must leave the row untouched.

stdlib-only. Pinned seed: 14007 (also in mapping.md).
"""
import random
import sys

SEED = 14007
N = 120_000

# A small pool of integer converters (model of field converter chains). Each is
# a deterministic Int -> Int; "wrapping" a value is modeled by the function it
# applies. Identity is represented by the empty chain (no converter declared).
CONVERTERS = [
    ("add1000", lambda x: x + 1000),   # e.g. a from_db_value-style transform
    ("double", lambda x: x * 2),
    ("neg", lambda x: -x),
    ("plus7", lambda x: x + 7),
]


def apply_chain(chain, x):
    for _, f in chain:
        x = f(x)
    return x


def convert_row(fields, row):
    # positional zip: field i converts cell i; extra cells/fields are dropped
    return [apply_chain(fields[i], row[i]) for i in range(min(len(fields), len(row)))]


def any_converter(fields):
    return any(len(chain) > 0 for chain in fields)


# --- ORACLE: faithful in-process replica of the POST-PATCH return path --------
def oracle(inp):
    fields = inp["returningFields"]
    if len(fields) == 0:
        return []
    if inp["canBatch"]:
        rows = inp["batchRows"]
    elif inp["canColumns"]:
        rows = [inp["columnsRow"]]
    else:
        rows = [inp["lastIdRow"]]
    converters = any_converter(fields)
    if converters:
        rows = [convert_row(fields, r) for r in rows]
    return rows


# --- SHADOW of implementation_insertReturnedRows (the R/I leg) ----------------
# Mirrors Solution.lean impl region exactly.
def shadow(inp):
    fields = inp["returningFields"]
    if len(fields) == 0:
        return []
    if inp["canBatch"]:
        rows = inp["batchRows"]
    elif inp["canColumns"]:
        rows = [inp["columnsRow"]]
    else:
        rows = [inp["lastIdRow"]]
    if any_converter(fields):
        rows = [convert_row(fields, r) for r in rows]
    return rows


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def mk(returningFields, canBatch=False, canColumns=False,
       batchRows=None, columnsRow=None, lastIdRow=None):
    return dict(
        returningFields=returningFields,
        canBatch=canBatch, canColumns=canColumns,
        batchRows=batchRows if batchRows is not None else [],
        columnsRow=columnsRow if columnsRow is not None else [],
        lastIdRow=lastIdRow if lastIdRow is not None else [],
    )


def _enumerate_edge():
    wrap = [CONVERTERS[0]]   # a single wrapping converter
    cases = []
    # F2P: single field, wrapping converter, last-id pathway -> wrapped value
    cases.append(mk([wrap], canBatch=False, canColumns=False, lastIdRow=[2]))
    # same via the columns pathway
    cases.append(mk([wrap], canBatch=False, canColumns=True, columnsRow=[2]))
    # same via the batch pathway (multiple rows)
    cases.append(mk([wrap], canBatch=True, batchRows=[[1], [2], [3]]))
    # no converter declared -> row untouched (all three pathways)
    cases.append(mk([[]], canBatch=False, canColumns=False, lastIdRow=[2]))
    cases.append(mk([[]], canBatch=False, canColumns=True, columnsRow=[5]))
    cases.append(mk([[]], canBatch=True, batchRows=[[1], [2]]))
    # no returning fields -> []
    cases.append(mk([], canBatch=True, batchRows=[[9]]))
    # multi-field row, mixed converter / no-converter
    cases.append(mk([wrap, []], canColumns=True, columnsRow=[10, 20]))
    cases.append(mk([[], CONVERTERS[1:3]], canColumns=True, columnsRow=[10, 20]))
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
        nfields = rng.choice([0, 1, 1, 2, 3, 4])
        fields = []
        for _ in range(nfields):
            clen = rng.choice([0, 0, 1, 1, 2, 3])  # bias toward empty/short chains
            fields.append([rng.choice(CONVERTERS) for _ in range(clen)])
        canBatch = rng.random() < 0.4
        canColumns = rng.random() < 0.5

        def mkrow():
            return [rng.randint(-50, 50) for _ in range(max(1, nfields))]

        batchRows = [mkrow() for _ in range(rng.choice([0, 1, 2, 3]))]
        inp = mk(fields, canBatch=canBatch, canColumns=canColumns,
                 batchRows=batchRows, columnsRow=mkrow(), lastIdRow=mkrow())
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

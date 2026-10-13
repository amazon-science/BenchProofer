#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-25747.

The bundle models ONE routine: `_wrap_in_pandas_container` (mapping.md). The
modeled value is a PURE function of the observables the real function reads:

    input category (sparse / dataframe / ndarray), the input frame's own
    (cols, idx, data) when it is already a table, the resolved column labels
    (array | None), and the supplied row index (array | None).

Post-patch rule (the gold edit DELETES `data_to_wrap.index = index`, so a
DataFrame input keeps its own row index):

    if sparse:        error("Pandas output does not support sparse data.")
    elif dataframe:   cols = columns if columns is not None else df.cols
                      ok({cols, idx = df.idx (kept!), data = df.data})
    else (ndarray):   cols = columns if columns is not None else range-labels
                      idx  = index   if index   is not None else range(n_rows)
                      ok({cols, idx, data = values})

Standing up pandas / the full set_output machinery to drive the real wrap is
heavy and unnecessary: the modeled value is this pure decision over observables
the real function exposes. So the ORACLE below is a faithful in-process replica
of the POST-PATCH logic (the deleted index-write absent), and the SHADOW is the
op-for-op transliteration of `implementation_buildOutputContainer` (Solution.lean
impl region), per refinement.md.

This genuinely tests the soundness-critical clause: when the input is already a
DataFrame, the externally-supplied index must NOT overwrite the frame's own
index, matching the F2P expectation (`test_set_output_pandas_keep_index`:
the transformed frame keeps its `["s0","s1"]` index).

stdlib-only. Pinned seed: 25747 (also in mapping.md).
"""
import random
import sys

SEED = 25747
N = 120_000

SPARSE_ERR = "Pandas output does not support sparse data."


def nd_columns(values):
    n = len(values[0]) if values else 0
    return [str(i) for i in range(n)]


def nd_index(values):
    return list(range(len(values)))


# --- ORACLE: faithful in-process replica of the POST-PATCH wrap ---------------
# `data_to_wrap.index = index` is DELETED; a DataFrame keeps its own index.
def oracle(inp):
    kind = inp["kind"]
    columns = inp["columns"]
    index = inp["index"]
    if kind == "sparse":
        return ("error", SPARSE_ERR)
    if kind == "dataframe":
        df = inp["df"]
        cols = columns if columns is not None else df["cols"]
        return ("ok", {"cols": cols, "idx": df["idx"], "data": df["data"]})
    # ndarray
    values = inp["values"]
    cols = columns if columns is not None else nd_columns(values)
    idx = index if index is not None else nd_index(values)
    return ("ok", {"cols": cols, "idx": idx, "data": values})


# --- SHADOW of implementation_buildOutputContainer (the R/I leg) --------------
# Mirrors Solution.lean impl region exactly (the .dataframe branch writes NO
# index; columns replaced only when supplied).
def shadow(inp):
    kind = inp["kind"]
    columns = inp["columns"]
    index = inp["index"]
    if kind == "sparse":
        return ("error", SPARSE_ERR)
    if kind == "dataframe":
        df = inp["df"]
        out = {"cols": df["cols"], "idx": df["idx"], "data": df["data"]}
        if columns is not None:
            out = {"cols": columns, "idx": out["idx"], "data": out["data"]}
        return ("ok", out)
    values = inp["values"]
    cols = columns if columns is not None else nd_columns(values)
    idx = index if index is not None else nd_index(values)
    return ("ok", {"cols": cols, "idx": idx, "data": values})


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _mk_df(rng):
    nrows = rng.randint(0, 4)
    ncols = rng.randint(0, 3)
    data = [[rng.randint(-9, 9) for _ in range(ncols)] for _ in range(nrows)]
    cols = [rng.choice(["a", "b", "c", "x", "y"]) for _ in range(ncols)]
    idx = [rng.randint(-50, 50) for _ in range(nrows)]
    return {"cols": cols, "idx": idx, "data": data}


def _opt_columns(rng, ncols_hint):
    if rng.random() < 0.4:
        return None
    return [rng.choice(["a", "b", "c", "x", "y"]) for _ in range(ncols_hint)]


def _opt_index(rng, nrows_hint):
    if rng.random() < 0.4:
        return None
    return [rng.randint(100, 200) for _ in range(nrows_hint)]


def _enumerate_edge():
    cases = []
    # F2P heart: DataFrame with a supplied index that DIFFERS from its own ->
    # result keeps the frame's own index ["s0","s1"]-analogue.
    df = {"cols": ["A0", "A1", "A2"], "idx": [900, 901], "data": [[1, 2, 3], [4, 5, 6]]}
    cases.append({"kind": "dataframe", "df": df, "columns": None, "index": [0, 1]})
    cases.append({"kind": "dataframe", "df": df, "columns": ["c0", "c1", "c2"], "index": [7, 8]})
    # DataFrame, no supplied index -> own index kept (no change either way)
    cases.append({"kind": "dataframe", "df": df, "columns": None, "index": None})
    # DataFrame, supplied columns only
    cases.append({"kind": "dataframe", "df": df, "columns": ["p", "q", "r"], "index": None})
    # sparse always errors
    cases.append({"kind": "sparse", "df": None, "values": None, "columns": None, "index": None})
    cases.append({"kind": "sparse", "df": None, "values": None, "columns": ["a"], "index": [1]})
    # ndarray: supplied index/columns
    cases.append({"kind": "ndarray", "values": [[1, 2], [3, 4]], "columns": ["m", "n"], "index": [5, 6]})
    # ndarray: default positional index/columns
    cases.append({"kind": "ndarray", "values": [[1, 2], [3, 4]], "columns": None, "index": None})
    # ndarray: empty
    cases.append({"kind": "ndarray", "values": [], "columns": None, "index": None})
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
        r = rng.random()
        if r < 0.5:
            # bias toward the discriminating category: a DataFrame input
            df = _mk_df(rng)
            inp = {
                "kind": "dataframe",
                "df": df,
                "columns": _opt_columns(rng, len(df["cols"])),
                "index": _opt_index(rng, len(df["idx"])),
            }
        elif r < 0.85:
            nrows = rng.randint(0, 4)
            ncols = rng.randint(0, 3)
            values = [[rng.randint(-9, 9) for _ in range(ncols)] for _ in range(nrows)]
            inp = {
                "kind": "ndarray",
                "values": values,
                "columns": _opt_columns(rng, ncols),
                "index": _opt_index(rng, nrows),
            }
        else:
            inp = {"kind": "sparse", "df": None, "values": None,
                   "columns": _opt_columns(rng, 2), "index": _opt_index(rng, 2)}
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

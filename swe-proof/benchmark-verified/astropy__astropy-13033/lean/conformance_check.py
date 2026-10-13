#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-13033.

The bundle models ONE routine: `BaseTimeSeries._check_required_columns`
(mapping.md). Its observable outcome is either a raised `ValueError` (we compare
the message string) or a normal return that may toggle `_required_columns_relax`.
We model it as `Except String Bool`: `('error', msg)` for the raise,
`('ok', new_relax)` for the no-error path.

Standing up the full QTable machinery to drive the real method is heavy and
unnecessary: the modeled value is a PURE function of the observables the method
reads (`_required_columns_enabled`, `_required_columns`, `_required_columns_relax`,
`colnames`, `__class__.__name__`). So the ORACLE below is a faithful in-process
replica of the POST-PATCH method (the gold edit's `as_scalar_or_list_str` plus
the full-slice found side), and the SHADOW is the op-for-op transliteration of
`implementation_checkRequiredColumns` (Solution.lean impl region), per
refinement.md.

This genuinely tests the soundness-critical clause: for a table requiring SEVERAL
columns the mismatch message must name the full expected and found column lists
(`['time', 'a']` / `['time', 'b']`), not just the first of each — matching the
F2P expectation — while preserving the single-column wording (`'time'` /
`'banana'`).

The Lean model leaves the per-element rendering used inside a rendered list
ABSTRACT (`opaque pyReprStr : String -> String`, bound to Python's `repr` of a
`str`; the binding is validated by G-AX). The SHADOW below therefore interprets
`pyReprStr` as the REAL `repr`, and the name pool includes adversarial names
(embedded single/double quotes, backslashes, control characters, non-ASCII) so
the message strings are compared byte-for-byte on exactly the inputs where a
naive quote-wrapping model would diverge from `str(list)`.

stdlib-only. Pinned seed: 13033 (also in mapping.md).
"""
import random
import sys

SEED = 13033
N = 120_000

NAME_POOL = ["time", "a", "b", "flux", "banana", "x", "y", "z",
             "a'b", 'a"b', "a\\b", "a\tb", "a\nb", "\x00", "'", '"',
             "it's", "a'b\"c", "écolønne", "", " lead", "trail "]


# --- as_scalar_or_list_str: faithful replica of the POST-PATCH helper ---------
# Both call sites always pass Python lists, so the `not hasattr(__len__)` scalar
# branch is unreachable for the modeled inputs (mapping.md). We model the two
# list branches; str(list) of strings renders as e.g. ['time', 'a'].
def as_scalar_or_list_str(obj):
    # obj is always a list[str] here
    if len(obj) == 1:
        return f"'{obj[0]}'"
    else:
        return str(obj)


# --- ORACLE: faithful in-process replica of the POST-PATCH method -------------
def oracle(inp):
    cls = inp["className"]
    enabled = inp["requiredColumnsEnabled"]
    req = inp["requiredColumns"]          # None or list[str]
    relax = inp["requiredColumnsRelax"]
    colnames = inp["colnames"]

    if not enabled:
        return ("ok", relax)
    if req is None:
        return ("ok", relax)

    if relax:
        required_columns = req[:len(colnames)]
    else:
        required_columns = req
    plural = 's' if len(required_columns) > 1 else ''

    if not relax and len(colnames) == 0:
        msg = ("{} object is invalid - expected '{}' "
               "as the first column{} but time series has no columns").format(
                   cls, required_columns[0], plural)
        return ("error", msg)
    elif colnames[:len(required_columns)] != required_columns:
        msg = ("{} object is invalid - expected {} "
               "as the first column{} but found {}").format(
                   cls, as_scalar_or_list_str(required_columns),
                   plural, as_scalar_or_list_str(colnames[:len(required_columns)]))
        return ("error", msg)

    new_relax = relax
    if relax and req == colnames[:len(req)]:
        new_relax = False
    return ("ok", new_relax)


# --- SHADOW of implementation_checkRequiredColumns (the R/I legs) -------------
# Mirrors Solution.lean impl region exactly. The opaque leaf `pyReprStr` is
# interpreted as the real Python `repr` (its G-AX-validated binding).
def py_str_repr(s):
    # pyStrRepr: verbatim single-quote wrap (the f"'{x}'" interpolation)
    return "'" + s + "'"


def py_repr_str(s):
    # pyReprStr (opaque in Lean): Python repr of a str
    return repr(s)


def py_list_repr(xs):
    return "[" + ", ".join(py_repr_str(x) for x in xs) + "]"


def render_names_shadow(xs):
    if len(xs) == 1:
        return py_str_repr(xs[0])
    else:
        return py_list_repr(xs)


def head_d(xs, default=""):
    return xs[0] if xs else default


def shadow(inp):
    cls = inp["className"]
    enabled = inp["requiredColumnsEnabled"]
    req = inp["requiredColumns"]
    relax = inp["requiredColumnsRelax"]
    colnames = inp["colnames"]

    if not enabled:
        return ("ok", relax)
    if req is None:
        return ("ok", relax)

    required = req[:len(colnames)] if relax else req
    plural = "s" if len(required) > 1 else ""

    if (not relax) and len(colnames) == 0:
        msg = (cls + " object is invalid - expected '" + head_d(required) +
               "' as the first column" + plural + " but time series has no columns")
        return ("error", msg)
    elif colnames[:len(required)] != required:
        msg = (cls + " object is invalid - expected " +
               render_names_shadow(required) + " as the first column" + plural +
               " but found " + render_names_shadow(colnames[:len(required)]))
        return ("error", msg)

    new_relax = False if (relax and req == colnames[:len(req)]) else relax
    return ("ok", new_relax)


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: 2 required columns, mismatch -> full list message
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time", "a"], requiredColumnsRelax=False,
                      colnames=["time", "b"]))
    # preserved single-column mismatch message
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time"], requiredColumnsRelax=False,
                      colnames=["banana"]))
    # single required, present empty -> no-columns message
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time"], requiredColumnsRelax=False,
                      colnames=[]))
    # 3 required, mismatch
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time", "a", "b"], requiredColumnsRelax=False,
                      colnames=["time", "x", "y"]))
    # disabled -> ok
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=False,
                      requiredColumns=["time", "a"], requiredColumnsRelax=True,
                      colnames=["time"]))
    # None required -> ok
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=None, requiredColumnsRelax=True, colnames=["x"]))
    # relaxed, leading match-as-far-as-go, not yet complete -> ok stays relaxed
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time", "a"], requiredColumnsRelax=True,
                      colnames=["time"]))
    # relaxed, fully matched -> toggles off
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time", "a"], requiredColumnsRelax=True,
                      colnames=["time", "a"]))
    # relaxed, leading mismatch -> error (list rendering, truncated to present len)
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time", "a"], requiredColumnsRelax=True,
                      colnames=["flux", "b"]))
    # matching, strict -> ok
    cases.append(dict(className="TimeSeries", requiredColumnsEnabled=True,
                      requiredColumns=["time"], requiredColumnsRelax=False,
                      colnames=["time", "extra"]))
    return cases


def _rand_names(rng, n):
    return [rng.choice(NAME_POOL) for _ in range(n)]


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
    classes = ["TimeSeries", "BinnedTimeSeries", "Foo"]
    for _ in range(N):
        enabled = rng.random() < 0.85
        has_req = rng.random() < 0.9
        # a configured required-columns list is always nonempty in practice
        # (e.g. ['time', ...]); req[0] / the head message assume that.
        req = _rand_names(rng, rng.randint(1, 4)) if has_req else None
        relax = rng.random() < 0.5
        colnames = _rand_names(rng, rng.randint(0, 5))
        inp = dict(
            className=rng.choice(classes),
            requiredColumnsEnabled=enabled,
            requiredColumns=req,
            requiredColumnsRelax=relax,
            colnames=colnames,
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

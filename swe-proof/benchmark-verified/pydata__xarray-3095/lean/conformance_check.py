#!/usr/bin/env python
"""G-CONF: differential conformance for pydata__xarray-3095.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_copy` skeleton and diffs it against the REAL patched callee
`xarray.core.variable.IndexVariable.copy` over a discrete catalogue of
(dtype, deep) configurations plus >=1e5 randomized inputs.

Modeled behavior: copying an index-backed variable (`IndexVariable`, whose
`_data` is a `PandasIndexAdapter`) must reproduce, in the copy, the SAME stored
element type (`_data._dtype`) as the original — for both deep and shallow copies
— never re-deriving it from the underlying sequence. The discriminating case is
a fixed-width unicode (`<U*`) index on `deep=True`: the recorded dtype is `<U*`
while the dtype re-inferred from the (object-typed) pandas index would be
`object`.

Bridge (mapping.md):
  Lean `IVar`               <->  an `IndexVariable('x', values)`
  Lean `data.values`        <->  the variable's element values (as str)
  Lean `data.dtype`         <->  `var._data._dtype`  (recorded element type)
  Lean `data.native`        <->  dtype re-inferred from the pandas index
  Lean `deep : Bool`        <->  `copy(deep=...)`
  Dtype encoding: `<Uw>` -> ('unicode', w); object -> ('object',); else -> ('other', str)

The Lean spec/impl says: result.dtype == input.dtype, result.values ==
input.values, result.dims/attrs == input's. The shadow returns exactly that;
we diff it against what the real patched `IndexVariable.copy` actually produces.

Exit 0 iff zero disagreements. stdlib + numpy + pandas (already in testbed);
pinned seed.
"""
import random
import sys

SEED = 20240711
N_RANDOM = 120_000  # >= 1e5


def encode_dtype(dt):
    """numpy dtype -> the Lean `Dtype` encoding used in the bijection."""
    import numpy as np
    dt = np.dtype(dt)
    if dt.kind == "U":
        return ("unicode", int(dt.itemsize // 4))  # UCS-4: 4 bytes/char
    if dt == np.dtype("O"):
        return ("object",)
    return ("other", dt.str)


# ---- Python shadow of implementation_copy (post-patch R/I leg) --------------

def input_native(values, np_dtype):
    """The underlying-sequence element type of the INPUT: the dtype re-inferred
    from the pandas index that wraps the values. Computed independently of the
    real callee (this is the `native` field of the Lean model)."""
    import numpy as np
    import pandas as pd
    idx = pd.Index(np.array(values, dtype=np_dtype))
    return encode_dtype(np.asarray(idx).dtype)


def shadow_copy(str_values, in_dtype_enc, native_enc, dims, attrs, deep):
    """Transliteration of problem_spec_copy / implementation_copy: the copy
    keeps the same values, native element type, and STORED dtype (the recorded
    input dtype), and unchanged dims/attrs — independent of `deep` (deep vs
    shallow is content-preserving). Returns the observable tuple
    (dims, attrs, values, dtype, native)."""
    arr = list(str_values)    # deep: duplicate; shallow: share — same content
    return (list(dims), list(attrs), arr, in_dtype_enc, native_enc)


# ---- real callee observation ------------------------------------------------

def real_copy(values, np_dtype, dims, attrs, deep):
    """Build the real IndexVariable, run the REAL patched .copy(deep), and read
    back the observable tuple (dims, attrs, values, native, dtype)."""
    import numpy as np
    from xarray.core.variable import IndexVariable

    arr = np.array(values, dtype=np_dtype)
    v = IndexVariable(dims, arr, dict(attrs))
    w = v.copy(deep=deep)

    out_dtype = encode_dtype(w._data._dtype)
    # native = dtype re-inferred from the wrapper's underlying pandas index
    native = encode_dtype(np.asarray(w._data.array).dtype)
    out_values = [str(x) for x in np.asarray(w.values).tolist()]
    out_dims = list(w.dims)
    out_attrs = sorted((str(k), str(v_)) for k, v_ in (w.attrs or {}).items())
    return (out_dims, out_attrs, out_values, out_dtype, native)


def main():
    import numpy as np

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # candidate element kinds: (numpy-dtype-builder, value-generator)
    def gen_unicode(width):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        return ("<U%d" % width,
                lambda n: ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, width)))
                           for _ in range(n)])

    def gen_int():
        return ("int64", lambda n: [rng.randint(-1000, 1000) for _ in range(n)])

    def gen_float():
        return ("float64", lambda n: [round(rng.uniform(-1e3, 1e3), 3) for _ in range(n)])

    builders = [gen_unicode(1), gen_unicode(3), gen_unicode(7),
                gen_int(), gen_float()]

    cases = []  # (np_dtype, values, dims, attrs, deep)

    # discrete catalogue: every kind x both deep flags, incl. the issue's <U3
    for np_dtype, gen in builders:
        for deep in (True, False):
            vals = gen(rng.randint(1, 4))
            cases.append((np_dtype, vals, ["x"], [("foo", "bar")], deep))

    # randomized fuzz
    for _ in range(N_RANDOM):
        np_dtype, gen = rng.choice(builders)
        n = rng.randint(1, 6)
        vals = gen(n)
        deep = rng.random() < 0.5
        attrs = [("foo", "bar")] if rng.random() < 0.5 else []
        cases.append((np_dtype, vals, ["x"], attrs, deep))

    for np_dtype, vals, dims, attrs, deep in cases:
        try:
            got = real_copy(vals, np_dtype, dims, attrs, deep)
        except Exception as exc:  # pragma: no cover
            disagreements += 1
            if disagreements <= 5:
                print(f"ERROR dtype={np_dtype} vals={vals} deep={deep}: {exc!r}")
            checked += 1
            continue

        str_vals = [str(x) for x in vals]
        attrs_sorted = sorted((str(k), str(v_)) for k, v_ in attrs)
        # The shadow asserts dtype is PRESERVED: expected dtype is the INPUT's
        # recorded dtype; expected native is the input's re-derived element type.
        in_dtype = encode_dtype(np_dtype)
        native = input_native(vals, np_dtype)
        exp = shadow_copy(str_vals, in_dtype, native, dims, attrs_sorted, deep)

        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH dtype={np_dtype} vals={vals} deep={deep}: "
                      f"real={got!r} shadow={exp!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

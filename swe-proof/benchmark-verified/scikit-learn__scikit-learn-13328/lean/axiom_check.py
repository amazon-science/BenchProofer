#!/usr/bin/env python3
"""G-AX — scikit-learn__scikit-learn-13328.

Validates the A-reference deep model of the unchanged input-validation callee
against the REAL repo routine, in-container.

The bundle models the element-type normalization performed by
`check_X_y(..., dtype=[np.float64, np.float32])` (which forwards to
`check_array`). `implementation_prepareInput` claims: an array whose original
element type is already in {float64, float32} keeps it; any other element type is
converted to float64.

This script drives the REAL `check_X_y` exactly as `HuberRegressor.fit` does
(`copy=False, accept_sparse=['csr'], y_numeric=True, dtype=[np.float64,
np.float32]`) over input arrays of every representative element kind, plus a
fuzzed sweep, and asserts the returned array's `.dtype` matches the model's
prediction. stdlib + numpy + sklearn only; exit 0 iff sound.
"""
import json
import sys

# --- the model under validation (mirror of implementation_prepareInput) -------
# NpKind -> resolved NpKind.  accepted = {"float64","float32"}, default float64.
ACCEPTED = ("float64", "float32")
DEFAULT = "float64"


def model_prepare(orig_kind: str) -> str:
    return orig_kind if orig_kind in ACCEPTED else DEFAULT


# numpy dtype <-> NpKind name (mapping.md bijection).  Representative kinds reached
# by fit's public input contract, plus extra non-floating numerics that all share
# the model's "else -> float64" branch.
def kind_name(np, dt) -> str:
    import numpy as _np
    if dt == _np.float64:
        return "float64"
    if dt == _np.float32:
        return "float32"
    if dt == _np.bool_:
        return "bool"
    # every remaining numeric integer kind is a non-accepted, non-object kind:
    # the model treats them all identically (-> float64).  Bucket as "int64".
    return "int64"


def main() -> int:
    try:
        import numpy as np
        from sklearn.utils.validation import check_X_y
    except Exception as e:  # pragma: no cover
        print(json.dumps({"status": "error", "instance":
                          "scikit-learn__scikit-learn-13328",
                          "reason": f"import failed: {e!r}"}))
        return 1

    rng = np.random.RandomState(13328)
    failures = []
    checked = 0

    # element kinds to drive through the real callee
    dtypes = [np.bool_, np.int8, np.int16, np.int32, np.int64,
              np.uint8, np.float16, np.float32, np.float64]

    # boundary shapes + fuzzed shapes (fit needs a 2D X with >=1 sample/feature)
    shapes = [(1, 1), (2, 1), (1, 2), (5, 3), (200, 2)]
    for _ in range(40):
        shapes.append((int(rng.randint(1, 50)), int(rng.randint(1, 6))))

    for dt in dtypes:
        for (n, m) in shapes:
            # build X of this element kind, y numeric
            base = rng.randn(n, m)
            if dt == np.bool_:
                X = base > 0
            else:
                X = (base * 3).astype(dt)
            y = rng.randn(n)
            try:
                Xc, yc = check_X_y(X, y, copy=False, accept_sparse=['csr'],
                                   y_numeric=True,
                                   dtype=[np.float64, np.float32])
            except Exception as e:
                failures.append({"dtype": str(dt), "shape": [n, m],
                                 "error": repr(e)})
                continue
            orig_kind = kind_name(np, np.dtype(dt))
            predicted = model_prepare(orig_kind)
            actual = kind_name(np, Xc.dtype)
            checked += 1
            if predicted != actual:
                failures.append({"dtype": str(dt), "shape": [n, m],
                                 "orig_kind": orig_kind,
                                 "predicted": predicted, "actual": actual})

    # object-dtype is NOT reachable for huber's float-only fix path under a list
    # dtype (object would go through a different coercion); it is excluded from
    # the model's input contract (mapping.md) and not driven here.

    ok = len(failures) == 0
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "instance": "scikit-learn__scikit-learn-13328",
        "checked": checked,
        "failures": failures[:20],
        "reason": ("A-reference deep model of check_array list-dtype resolution "
                   "matches the real check_X_y over all driven element kinds"
                   if ok else "model disagreed with real callee"),
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""G-CONF for pydata__xarray-2905.

Differential test: the R/I shadow of `implementation_prepare` (Solution.lean)
vs the behaviour of `patch.diff` at the changed site of `as_compatible_data`.

Both legs operate on a model object exposing the two traits the changed code
observes (mapping.md bijection):
  - is_container : bool   <- isinstance(data, (pd.Series, pd.Index, pd.DataFrame))
  - values      : payload or the sentinel MISSING  <- getattr(data, "values", data)

stdlib-only; exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import json, random, sys

SEED = 2905           # pinned in mapping.md
N = 200_000
MISSING = object()    # marks "no .values attribute"


def random_obj(rng):
    is_container = rng.random() < 0.5
    if rng.random() < 0.5:
        payload = rng.randint(-1000, 1000)        # exposes a .values payload
    else:
        payload = MISSING                          # no .values attribute
    # A real pandas container always exposes .values; reflect that in the model.
    if is_container and payload is MISSING:
        payload = rng.randint(-1000, 1000)
    return {"is_container": is_container, "values": payload}


def shadow_impl(obj):
    """R/I skeleton of implementation_prepare (Lean)."""
    result = obj
    if obj["is_container"]:                         # Obj.isContainer
        # data.payload.getD data
        result = obj["values"] if obj["values"] is not MISSING else obj
    return result


def gold_reference(obj):
    """Behaviour of patch.diff at the changed line."""
    data = obj
    # if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)): data = data.values
    if obj["is_container"]:
        data = obj["values"]                        # container ALWAYS has .values
    return data


def main():
    rng = random.Random(SEED)
    diffs = 0
    for _ in range(N):
        obj = random_obj(rng)
        a, b = shadow_impl(obj), gold_reference(obj)
        if a is not b and a != b:
            diffs += 1
    status = "pass" if diffs == 0 else "fail"
    print(json.dumps({"status": status, "checked": N, "disagreements": diffs}))
    sys.exit(0 if diffs == 0 else 1)


if __name__ == "__main__":
    main()

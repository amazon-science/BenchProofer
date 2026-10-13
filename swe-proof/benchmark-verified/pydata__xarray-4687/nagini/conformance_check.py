#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4687 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The impl region uses only
plain list operations, so no PSeq shim is needed for it; the @Pure helper
`empty_payload` appears only in contracts and is not called by the impl. The
single @ContractOnly callee, `default_mode_drops`, calls the REAL repo
option reader: it reports whether an unspecified attribute-handling mode
resolves to the dropping behaviour under the ambient configuration
(`xarray.core.options._get_keep_attrs(default=False)` being falsy).

ORACLE: the REAL patched repo function the model models per mapping.md —
`xarray.core.computation.where(cond, x, y, ...)`. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable.

Type bridge (mapping.md section 2):
  * an operand's attribute payload `List[int]` <-> an attrs dict, via the
    bijection [v0, v1, ...] <-> {"k0": v0, "k1": v1, ...} ([] <-> {});
    payload equality is content equality on both sides.
  * `attrs: List[List[int]]` of length 3 <-> the three operands' attrs in
    positional order (index 0 = predicate operand, 1 = first choice,
    2 = second choice).
  * `mode: int` in {0, 1} <-> the attribute-handling argument: 0 = leave it
    unspecified (omit the keyword), 1 = pass True.
The oracle's result payload is the `.attrs` dict of the returned object,
decoded back through the same bijection and compared to the shadow's list.

Input domain: Requires demands len(attrs) == 3 and mode in {0, 1}; payload
contents are unconstrained. Generation covers empty payloads, payloads equal
across slots, and fuzzed payloads of length 0..4 with values 0..1000, in both
modes.

>= 1e5 Requires-satisfying inputs: 22 boundary cases + 100000 fuzz cases.
Pinned fuzz seed: 4687.

The operand data arrays are fixed (only attrs vary — the modeled behaviour is
attribute provenance, not element selection); the three operand objects are
reused across cases with their .attrs reassigned per case, keeping the run
inside the gate budget.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

SEED = 4687
N_FUZZ = 100_000


# --- @ContractOnly callee: delegate to the REAL repo option reader ------------

def default_mode_drops():
    """True iff an unspecified attribute-handling mode resolves to the
    dropping behaviour under the ambient configuration (real repo callee)."""
    from xarray.core.options import _get_keep_attrs
    return not _get_keep_attrs(default=False)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_payload(attrs, mode):
    result = []  # type: list
    if mode == 0 and default_mode_drops():
        return result
    # PRESERVE (or a non-dropping default): copy the first-choice operand's
    # payload (positional index 1) element by element into the result.
    src = attrs[1]
    i = 0
    while i < len(src):
        result.append(src[i])
        i = i + 1
    return result


# --- bridge: List[int] payload <-> attrs dict ----------------------------------

def payload_to_dict(payload):
    return {"k%d" % i: v for i, v in enumerate(payload)}


def dict_to_payload(d):
    return [d["k%d" % i] for i in range(len(d))]


def make_oracle():
    """Build the reusable operand objects and return a callable
    oracle(attrs, mode) -> payload list, driving the REAL patched where()."""
    import xarray as xr

    cond = xr.DataArray([True, False], dims="q")
    x = xr.DataArray([1, 1], dims="q")
    y = xr.DataArray([0, 0], dims="q")

    def oracle(attrs, mode):
        cond.attrs = payload_to_dict(attrs[0])
        x.attrs = payload_to_dict(attrs[1])
        y.attrs = payload_to_dict(attrs[2])
        if mode == 0:
            # unspecified mode: omit the keyword entirely
            out = xr.where(cond, x, y)
        else:
            out = xr.where(cond, x, y, keep_attrs=True)
        return dict_to_payload(dict(out.attrs))

    return oracle


def check_case(oracle, attrs, mode):
    # Requires: len(attrs) == 3, mode in {0, 1}
    assert len(attrs) == 3 and mode in (0, 1)
    shadow = select_payload([list(p) for p in attrs], mode)
    real = oracle(attrs, mode)
    if shadow != real:
        return ("DISAGREEMENT\n  attrs=%r\n  mode=%r\n  shadow=%r\n  real=%r"
                % (attrs, mode, shadow, real))
    return None


def boundary_cases():
    triples = [
        [[], [], []],
        [[1], [2], [3]],
        [[], [7], []],
        [[7], [], [9]],                 # first-choice payload empty
        [[5], [5], [5]],                # identical payloads on all slots
        [[4], [6], [4]],                # slots 0 and 2 agree, 1 differs
        [[1, 2, 3], [4, 5], [6]],
        [[0], [0, 0, 0, 0], [0]],
        [[1000], [999, 998], []],
        [[], [], [3, 1]],
        [[2, 2], [2, 2], [2, 2]],
    ]
    return [(t, m) for t in triples for m in (0, 1)]


def rand_triple(rng):
    return [[rng.randint(0, 1000) for _ in range(rng.randint(0, 4))]
            for _ in range(3)]


def main():
    oracle = make_oracle()

    checked = 0
    n_boundary = 0
    for attrs, mode in boundary_cases():
        err = check_case(oracle, attrs, mode)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(oracle, rand_triple(rng), rng.randint(0, 1))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched selection on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

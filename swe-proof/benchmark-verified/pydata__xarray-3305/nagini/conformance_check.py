#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3305 (nagini).

SHADOW  — the impl regions of `model.py` copied VERBATIM with the contract
          statement lines (Requires/Ensures) stripped; the model IS Python,
          so no transliteration.  The @Pure helpers `resolve_keep` /
          `selected_meta` copy over as plain functions (PSeq shim: a plain
          tuple; `PSeq(0).take(0)` is the empty tuple).  The @ContractOnly
          axiom callee `ambient_keep_default` calls the REAL repo function
          it stands for, `xarray.core.options._get_keep_attrs(default=False)`
          (mapping.md §3.1).

ORACLE  — the REAL patched repo functions (PYTHONPATH=/testbed; the gate
          applies the gold patch before this script runs):
            site 1: `xarray.core.variable.Variable.quantile`
                    <-> shadow `reduce_result_metadata`
            site 2: `xarray.core.dataset.Dataset.quantile` (per-variable
                    delegation) <-> shadow `entrypoint_reduce_metadata`
          The observable per mapping.md §2 is the result's attrs payload;
          the numeric reduction is metadata-irrelevant and not modeled.

BRIDGE  — mapping.md §2's type abstraction: the metadata payload is a
          `List[int]` of code points standing for the whole attribute
          mapping, carried verbatim or dropped as a unit.  Bijection used
          here: payload [c0, .., c(n-1)]  <->  ordered attrs mapping
          {"k0": c0, .., "k(n-1)": c(n-1)} (insertion-ordered in these
          images; xarray stores attrs as an OrderedDict).  Decoding back
          validates the exact key sequence, so any oracle-side reordering,
          key change, or value change surfaces as a disagreement — payload
          equality <-> attrs-mapping equality.  An empty payload [] <->
          empty attrs (attrs=None and attrs={} are observationally the
          same empty mapping).
          The axiom's recorded flag dependency (mapping.md §3.1): the
          shadow/oracle agreement is scoped to the default ambient
          configuration OPTIONS["keep_attrs"] == "default", asserted below.

Inputs (all satisfy the Requires — any int list + Optional[bool] flag):
boundary cases (empty/singleton/duplicate/extreme-value payloads x the full
three-valued flag) + 85000 fuzzed site-1 cases + 20000 fuzzed site-2 cases
= >= 1e5 total.  Pinned seed: 3305.  Exit 0 iff zero disagreements; on
disagreement print the input and both outputs and exit 1.
stdlib + numpy + xarray (the repo under test) only.
"""
import random
import sys
import warnings

warnings.simplefilter("ignore")

SEED = 3305
N_FUZZ_SITE1 = 85_000
N_FUZZ_SITE2 = 20_000
MAX_DISAGREEMENTS = 5


# ---------------------------------------------------------------------------
# Shadow: model.py pure + impl regions, contracts stripped.
# ---------------------------------------------------------------------------

def ambient_keep_default():
    """@ContractOnly axiom callee: per the G-CONF contract it calls the REAL
    repo function it models (the ambient default-policy resolver)."""
    from xarray.core.options import _get_keep_attrs
    return _get_keep_attrs(default=False)


def resolve_keep(keep):
    if keep is None:
        return ambient_keep_default()
    return keep


def selected_meta(src, keep):
    if keep:
        return src
    return tuple()  # PSeq shim: PSeq(0).take(0) == empty sequence


def reduce_result_metadata(self_meta, keep_metadata):
    keep = keep_metadata
    if keep is None:
        keep = ambient_keep_default()
    result = []  # type: list
    if keep:
        result = list(self_meta)
    return result


def entrypoint_reduce_metadata(self_meta, keep_metadata):
    result = reduce_result_metadata(self_meta, keep_metadata)
    return result


# ---------------------------------------------------------------------------
# Bridge: payload List[int] <-> ordered attrs mapping.
# ---------------------------------------------------------------------------

def payload_to_attrs(payload):
    return dict(("k%d" % i, v) for i, v in enumerate(payload))


def attrs_to_payload(attrs):
    """Inverse bridge; returns None if the mapping is not in the bridged
    image (wrong keys / wrong order), which counts as a disagreement."""
    items = list(attrs.items())
    for i, (k, _v) in enumerate(items):
        if k != "k%d" % i:
            return None
    return [v for _k, v in items]


# ---------------------------------------------------------------------------
# Differential driver.
# ---------------------------------------------------------------------------

def check_site1(xr, np, payload, keep, q, interp, data, disagreements):
    var = xr.Variable(("x",), data, attrs=payload_to_attrs(payload))
    out = var.quantile(q, dim="x", interpolation=interp, keep_attrs=keep)
    real = attrs_to_payload(dict(out.attrs))
    shadow = reduce_result_metadata(list(payload), keep)
    if real != shadow:
        disagreements.append(
            ("site1/Variable.quantile", list(payload), keep, q, interp,
             shadow, real if real is not None else dict(out.attrs)))
    return len(disagreements) < MAX_DISAGREEMENTS


def check_site2(xr, np, payload, keep, q, interp, data, disagreements):
    ds = xr.Dataset({"v": xr.Variable(("x",), data,
                                      attrs=payload_to_attrs(payload))})
    out = ds.quantile(q, dim="x", interpolation=interp, keep_attrs=keep)
    real = attrs_to_payload(dict(out["v"].attrs))
    shadow = entrypoint_reduce_metadata(list(payload), keep)
    if real != shadow:
        disagreements.append(
            ("site2/Dataset.quantile", list(payload), keep, q, interp,
             shadow, real if real is not None else dict(out["v"].attrs)))
    return len(disagreements) < MAX_DISAGREEMENTS


def main():
    import numpy as np
    import xarray as xr
    from xarray.core.options import OPTIONS

    # Scope guard for the axiom's recorded flag dependency: the check runs
    # under the default ambient configuration (the state every repo test
    # runs under; mapping.md §3.1).
    assert OPTIONS["keep_attrs"] == "default", (
        "conformance check requires the default ambient configuration; got %r"
        % (OPTIONS["keep_attrs"],))

    rng = random.Random(SEED)
    disagreements = []
    checked = 0

    interps = ["linear", "lower", "higher", "midpoint", "nearest"]
    q_pool = [0.5, 0.0, 1.0, 0.9, [0.25, 0.75]]
    keep_choices = [True, False, None]

    # 1. Boundary payloads x the full three-valued flag x both sites.
    boundary_payloads = [
        [],                        # empty payload
        [0],                       # singleton, smallest code point
        [0x10FFFF],                # singleton, largest code point
        [65, 65, 65],              # duplicated values
        [1, 2, 3],
        list(range(16)),           # longer payload
        [0x10FFFF, 0, 42],         # mixed extremes
    ]
    data3 = np.array([0.0, 1.0, 2.0])
    for payload in boundary_payloads:
        for keep in keep_choices:
            for q in q_pool:
                for interp in interps:
                    checked += 2
                    if not check_site1(xr, np, payload, keep, q, interp,
                                       data3, disagreements):
                        break
                    if not check_site2(xr, np, payload, keep, q, interp,
                                       data3, disagreements):
                        break

    # 2. Fuzz site 1: random payloads (length 0..12, full code-point range)
    #    x random flag / q / interpolation / data.
    if not disagreements:
        for _ in range(N_FUZZ_SITE1):
            n = rng.randint(0, 12)
            payload = [rng.randint(0, 0x10FFFF) for _ in range(n)]
            keep = rng.choice(keep_choices)
            q = rng.choice(q_pool)
            interp = rng.choice(interps)
            data = np.array([rng.random() for _ in range(3)])
            checked += 1
            if not check_site1(xr, np, payload, keep, q, interp, data,
                               disagreements):
                break

    # 3. Fuzz site 2 (heavier per call: full container-level delegation).
    if not disagreements:
        for _ in range(N_FUZZ_SITE2):
            n = rng.randint(0, 12)
            payload = [rng.randint(0, 0x10FFFF) for _ in range(n)]
            keep = rng.choice(keep_choices)
            q = rng.choice(q_pool)
            interp = rng.choice(interps)
            data = np.array([rng.random() for _ in range(3)])
            checked += 1
            if not check_site2(xr, np, payload, keep, q, interp, data,
                               disagreements):
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for site, payload, keep, q, interp, shadow, real in disagreements:
            print("  %s: payload=%r keep=%r q=%r interp=%r\n"
                  "    shadow=%r\n    oracle=%r"
                  % (site, payload, keep, q, interp, shadow, real))
        return 1
    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "Variable.quantile / Dataset.quantile result-attrs behaviour on "
          "%d inputs (seed=%d), 0 disagreements." % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

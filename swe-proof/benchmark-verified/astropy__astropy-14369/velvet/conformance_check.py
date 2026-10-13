#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14369 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type, via the mapping.md bijection
              (a chain of `UnitBase` operands <-> a `List Int` exponent vector
              indexed by operand position). The backward fold of
              `reduceDivisionChain` emits one exponent per operand position:
              the head position +1 and every later position -1 (the left-grouped
              vector `expVec`). The single A-reference content (the per-operand
              power rule itself == the real parser) is out of scope for G-CONF;
              it stays with G-AX. Here we check the STRUCTURE the impl produces:
              length == #operands, head +1, tail -1, in textual order.
  * ORACLE  — patch.diff's behaviour: the patched CDS unit-format parser
              (`astropy.units.Unit(<chain>, format='cds')`) applied at
              base_commit with the gold patch applied (the real correctness
              oracle, G-RESOLVE).

They must agree on every Requires-satisfying input (a non-empty chain of
distinct named units). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + astropy
only. The fuzz seed is pinned for a deterministic verdict. Like axiom_check.py,
it establishes the post-patch grammar before importing astropy (idempotent).
"""
import itertools
import os
import random
import subprocess
import sys
import warnings

warnings.simplefilter("ignore")

SEED = 14369
N_FUZZ = 5000

_CHANGED_FILE = "astropy/units/format/cds.py"
_POSTPATCH_MARKER = "combined_units DIVISION unit_expression"

UNIT_POOL = ["km", "s", "Mpc", "kpc", "m", "g", "J", "W", "pix", "nm", "cm", "K"]


def _ensure_postpatch_source():
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED_FILE)
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER in fh.read():
                return None
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)
    candidates = ["/work/patch.diff", "/gold.patch",
                  os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "patch.diff")]
    patch_path = next((p for p in candidates if os.path.exists(p)), None)
    if patch_path is None:
        return "post-patch source required but no patch.diff found in %r" % (candidates,)
    proc = subprocess.run(["git", "apply", "-v", patch_path],
                          cwd=testbed, capture_output=True, text=True)
    if proc.returncode != 0:
        return ("git apply %s failed (rc %d): %s"
                % (patch_path, proc.returncode, (proc.stderr or proc.stdout).strip()))
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER not in fh.read():
                return "patch applied but post-patch rule absent in %s" % changed
    except OSError as exc:
        return "could not re-read %s: %r" % (changed, exc)
    return None


def shadow_exponents(chain_units):
    """expVec(len(chain)) transliterated to a per-operand-position list:
    the head position +1, every later position -1 (the R/I shadow of the
    left-grouped backward fold in reduceDivisionChain)."""
    n = len(chain_units)
    return [1 if i == 0 else -1 for i in range(n)]


def oracle_exponents(u, chain_units):
    """patch.diff's behaviour: the patched CDS parser's exponent of each
    operand, by position."""
    s = "/".join(chain_units)
    parsed = u.Unit(s, format="cds")
    base_to_power = {b: int(p) for b, p in zip(parsed.bases, parsed.powers)}
    out = []
    for cu in chain_units:
        single = u.Unit(cu, format="cds")
        base = single.bases[0] if single.bases else None
        out.append(base_to_power.get(base, 0))
    return out


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ["s"]
    yield ["km", "s"]
    yield ["km", "s", "Mpc"]
    yield ["J", "m", "s", "kpc"]
    yield ["J", "s", "kpc"]
    small = ["km", "s", "Mpc", "kpc", "m"]
    for k in range(1, 6):
        for chain in itertools.permutations(small, k):
            yield list(chain)
    for _ in range(n):
        k = rng.randint(1, min(8, len(UNIT_POOL)))
        yield rng.sample(UNIT_POOL, k)


def main():
    err = _ensure_postpatch_source()
    if err is not None:
        print("G-CONF FAIL: could not establish post-patch source: %s" % err,
              file=sys.stderr)
        return 3

    import astropy.units as u

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for chain in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_exponents(chain)
        oracle = oracle_exponents(u, chain)
        if shadow != oracle:
            disagreements.append((chain, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for c, sh, orc in disagreements:
            print("  chain=%r shadow=%r oracle=%r" % (c, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reduceDivisionChain agrees with patch.diff "
          "behaviour on %d chains (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

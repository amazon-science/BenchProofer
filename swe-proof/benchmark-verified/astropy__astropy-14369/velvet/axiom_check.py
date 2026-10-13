#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14369.

This bundle consumes NO axiom: the changed behaviour — the exponent a division
chain assigns to each operand — is modelled DEEPLY by the pure function
`chainPower(i)` in Solution.lean (the exponent of the operand at chain position
i: +1 for the leading operand, -1 for every following operand) and assembled
into the per-position exponent vector `expVec`. G-AX validates that deep model
as an **A-reference**: it runs the REAL (patched) callee — astropy's CDS
unit-format parser, `astropy.units.Unit(<chain>, format='cds')` — on division
chains and asserts that the parsed composite unit's exponent vector equals the
model's `chainPower` at EVERY operand position, on boundary + exhaustive + fuzz
inputs.

The check is the index-level equivalence the model decides
(`model_power(i) == real_power(i)` for every chain position i), NOT a value-
membership proxy: the operand identity at each position is tracked explicitly so
an over/under-flip at any position is caught (SPEC_GUIDE directive 7, "no
double-mask").

PATCH STATE (reproducibility). The modeled function IS the changed grammar rule
(deep model, empty axioms region), so the A-reference target is the *post-patch*
CDS parser. The eval image is checked out at base_commit (PRE-patch), where the
division rule is right-grouped and a chain u0/u1/.../u(n-1) yields the
ALTERNATING exponent vector (-1)**i — not the left-grouped +1 / -1 / -1 / ...
the model pins. Running the A-reference against the base parser therefore
(correctly) FAILS. So this script makes the in-container source carry the
post-patch grammar BEFORE importing astropy: it applies the bundle's gold
patch.diff (which edits both cds.py and the regenerated LALR table
cds_parsetab.py) to the writable /testbed checkout, so the patched parser is the
one loaded on first import. This runs rc 0 under the STANDARD recipe
(apply_gold=False, whole bundle mounted read-only at /work). The apply is
idempotent: if the source already carries the post-patch rule (e.g. the harness
was invoked with apply_gold=True), the script detects it and skips re-applying.
git apply failures are surfaced explicitly (rc 3), never swallowed.

Imports only the standard library plus astropy (the very package the patch
edits). Exit 0 iff every observation matches the model.
"""
import itertools
import os
import random
import subprocess
import sys
import warnings

warnings.simplefilter("ignore")

# The changed grammar file and the post-patch rule fragment that distinguishes
# the post-patch (left-grouped) division reduction from the pre-patch
# (right-grouped) one at base_commit.
_CHANGED_FILE = "astropy/units/format/cds.py"
_POSTPATCH_MARKER = "combined_units DIVISION unit_expression"


def _ensure_postpatch_source():
    """Make the in-container astropy carry the post-patch (left-grouped)
    division grammar.

    The eval image is base_commit (pre-patch, right-grouped). The A-reference
    target is the POST-patch parser, so we apply the bundle's gold patch.diff to
    the writable /testbed checkout before importing astropy. The patch edits both
    cds.py (the rule) and cds_parsetab.py (the regenerated LALR table), so the
    loaded parser is self-consistently post-patch. Idempotent: if the post-patch
    rule is already present (apply_gold or a prior apply) we do nothing. Returns
    None on success or a string error (caller exits rc 3)."""
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED_FILE)
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER in fh.read():
                return None  # already post-patch (apply_gold or prior apply)
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)

    candidates = ["/work/patch.diff", "/gold.patch",
                  os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "patch.diff")]
    patch_path = next((p for p in candidates if os.path.exists(p)), None)
    if patch_path is None:
        return ("post-patch source required but no patch.diff found in %r"
                % (candidates,))

    proc = subprocess.run(["git", "apply", "-v", patch_path],
                          cwd=testbed, capture_output=True, text=True)
    if proc.returncode != 0:
        return ("git apply %s failed (rc %d): %s"
                % (patch_path, proc.returncode,
                   (proc.stderr or proc.stdout).strip()))
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER not in fh.read():
                return ("patch applied but post-patch rule %r still absent in %s"
                        % (_POSTPATCH_MARKER, changed))
    except OSError as exc:
        return "could not re-read %s: %r" % (changed, exc)
    return None


def chain_power(i, n):
    """The model's deep characterisation (Solution.lean pure region, chainPower):
    +1 for the leading operand, -1 for every following operand."""
    return 1 if i == 0 else -1


# A pool of distinct CDS-parseable named units used to build division chains.
UNIT_POOL = ["km", "s", "Mpc", "kpc", "m", "g", "J", "W", "pix", "nm", "cm", "K"]


def real_exponent_vector(u, chain_units):
    """Parse '<u0>/<u1>/.../<u(n-1)>' with the REAL patched CDS parser and
    return the resulting integer exponent of each operand, by position."""
    s = "/".join(chain_units)
    parsed = u.Unit(s, format="cds")
    base_to_power = {b: int(p) for b, p in zip(parsed.bases, parsed.powers)}
    out = []
    for cu in chain_units:
        single = u.Unit(cu, format="cds")
        base = single.bases[0] if single.bases else None
        out.append(base_to_power.get(base, 0))
    return out, str(parsed)


def check_chain(u, chain_units):
    n = len(chain_units)
    got, rendered = real_exponent_vector(u, chain_units)
    want = [chain_power(i, n) for i in range(n)]
    if got != want:
        print(
            f"MISMATCH chain={chain_units} got={got} want={want} parsed='{rendered}'",
            file=sys.stderr,
        )
        return False
    return True


def main():
    err = _ensure_postpatch_source()
    if err is not None:
        print("G-AX FAIL: could not establish post-patch source: %s" % err,
              file=sys.stderr)
        return 3

    import astropy.units as u

    ok = True
    checked = 0

    # 1. The exact inputs the issue / F2P tests exercise (boundary cases).
    #    A single-operand "chain" (e.g. "s") has no division operator, so it is
    #    the leading operand and keeps exponent +1 — chain_power(0, 1) = +1.
    f2p_chains = [
        ["km", "s", "Mpc"],          # F2P: km/s/Mpc -> km s^-1 Mpc^-1
        ["J", "m", "s", "kpc"],      # the issue's 10+3J/m/s/kpc2 shape
        ["s"],                       # single operand, n==1 head boundary (+1)
        ["km", "s"],                 # km/s
        ["J", "s", "kpc"],           # 10-7J/s/kpc2 shape
    ]
    for c in f2p_chains:
        if not check_chain(u, c):
            ok = False
        checked += 1

    # 2. Exhaustive over all distinct-operand chains of length 1..5 from a
    #    small alphabet (ordered tuples) — every position observed directly.
    small = ["km", "s", "Mpc", "kpc", "m"]
    for n in range(1, 6):
        for chain in itertools.permutations(small, n):
            if not check_chain(u, list(chain)):
                ok = False
            checked += 1

    # 3. Randomised fuzz over the wider pool, lengths 1..8.
    random.seed(20230206)
    for _ in range(4000):
        n = random.randint(1, min(8, len(UNIT_POOL)))
        chain = random.sample(UNIT_POOL, n)
        if not check_chain(u, chain):
            ok = False
        checked += 1

    if ok:
        print(f"OK: chainPower == real CDS parser exponent vector on {checked} chains")
        return 0
    print("FAIL: deep model chainPower disagrees with the real CDS parser", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

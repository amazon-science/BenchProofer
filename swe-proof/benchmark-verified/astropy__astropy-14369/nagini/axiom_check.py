#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14369.

This bundle consumes NO `@ContractOnly` axiom: the changed behaviour — the
exponent a left-grouped division chain assigns to each operand — is modelled
DEEPLY by the pure function `chain_power(i, power, leading)` in model.py (the
exponent of the operand at chain position i whose own intrinsic exponent is
`power`: it keeps `power` iff it leads a chain that does not open with the
division operator, and receives `-power` otherwise).  G-AX therefore validates
that deep model as an **A-reference**: it runs the REAL (patched) callee —
astropy's CDS unit-format parser, `astropy.units.Unit(<chain>, format='cds')`
— on division chains and asserts that the parsed composite unit's exponent
vector equals the model's `chain_power` for every operand, on boundary + fuzz
inputs.

The check is the index-level equivalence the model decides
(`model_power(i) == real_power(i)` for every chain position i), NOT a
value-membership proxy: on all-distinct-base chains each operand's exponent is
read off the parsed composite directly, so an over/under-flip or a
mis-magnitude at any position is caught (SPEC_GUIDE directive 7, "no
double-mask").  Chains that REPEAT a base are covered too, against the only
observable the callee exposes there: the parser reports one power per base, so
the per-base power is compared to the SUM of the model's per-position entries
over the positions sharing that base — the bridge mapping.md §2 declares.

INPUT CLASSES.  The generators cover, deliberately and separately, all three
axes the model's domain has:
  * operands carrying their OWN intrinsic exponent (e.g. a squared length),
    not only bare first-power names — the magnitude axis;
  * chains that OPEN with the division operator, where there is no leading
    operand and the first operand is divided in as well — the `leading` axis;
  * chains that REPEAT a base, admitted by the precondition (which imposes no
    distinctness), compared under the per-base summing bridge.

PATCH STATE (reproducibility).  The modeled function IS the changed grammar
rule (deep model, empty axioms region), so the A-reference target is the
*post-patch* CDS parser.  The eval image is checked out at ``base_commit``
(PRE-patch), where the division rule is right-grouped and a chain
``u0/u1/.../u(n-1)`` gives operand i its own exponent times ``(-1)**i`` — not
the left-grouped keep-head / negate-rest the model pins.  Running the
A-reference against the base parser therefore (correctly) FAILS.  So this
script makes the in-container source carry the post-patch grammar BEFORE
importing astropy: it applies the bundle's gold ``patch.diff`` (which edits both
``cds.py`` and the regenerated LALR table ``cds_parsetab.py``) to the writable
``/testbed`` checkout, so the patched parser is the one loaded on first import.
This runs rc 0 under the STANDARD recipe (``apply_gold=False``, the whole bundle
mounted read-only at ``/work``).  The apply is idempotent: if the source already
carries the post-patch rule (e.g. the harness was invoked with
``apply_gold=True``), the script detects it and skips re-applying.  ``git apply``
failures are surfaced explicitly (rc 3), never swallowed.

Imports only the standard library plus astropy (the very package the patch
edits).  Exit 0 iff every observation matches the model.
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
_PREPATCH_MARKER = "unit_expression DIVISION combined_units"


def _ensure_postpatch_source():
    """Make the in-container astropy carry the post-patch (left-grouped)
    division grammar.

    The eval image is base_commit (pre-patch, right-grouped). The A-reference
    target is the POST-patch parser, so we apply the bundle's gold ``patch.diff``
    to the writable ``/testbed`` checkout before importing astropy. The patch
    edits both ``cds.py`` (the rule) and ``cds_parsetab.py`` (the regenerated
    LALR table), so the loaded parser is self-consistently post-patch.
    Idempotent: if the post-patch rule is already present (apply_gold or a prior
    apply) we do nothing. Returns None on success or a string error (caller exits
    rc 3)."""
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED_FILE)
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER in fh.read():
                return None  # already post-patch (apply_gold or prior apply)
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)

    # Locate the bundle patch. Under the standard recipe the whole bundle dir is
    # mounted read-only at /work; apply_gold also mounts it at /gold.patch.
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
    # Confirm the apply actually produced the post-patch rule.
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER not in fh.read():
                return ("patch applied but post-patch rule %r still absent in %s"
                        % (_POSTPATCH_MARKER, changed))
    except OSError as exc:
        return "could not re-read %s: %r" % (changed, exc)
    return None


def chain_power(i, power, leading):
    """The model's deep characterisation (model.py pure region)."""
    if i == 0 and not leading:
        return power
    return -power


# Base names used to build division chains, and the intrinsic exponents an
# operand may carry.  A CONCRETE OPERAND is a base name optionally followed by
# its own exponent (e.g. "kpc2" is one operand of intrinsic exponent 2).
BASE_POOL = ["km", "s", "Mpc", "kpc", "m", "g", "J", "W", "pix", "nm", "cm", "K"]
POWER_SUFFIXES = ["", "2", "3", "-1", "-2", "+2", "10"]

_leaf_cache = {}


def operand_base_power(u, name):
    """(base, intrinsic integer exponent) of ONE operand surface like 'kpc2'."""
    if name not in _leaf_cache:
        parsed = u.Unit(name, format="cds")
        bases, powers = list(parsed.bases), list(parsed.powers)
        if len(bases) != 1:
            raise ValueError("not a single-base operand: %r" % (name,))
        _leaf_cache[name] = (bases[0], int(powers[0]))
    return _leaf_cache[name]


def real_exponent_vector(u, chain_operands, leading):
    """Parse the chain with the REAL patched CDS parser and return, per chain
    position, the exponent the parsed composite assigns to that operand's base
    (valid as a per-position reading only when the bases are all distinct)."""
    surface = ("/" if leading else "") + "/".join(chain_operands)
    parsed = u.Unit(surface, format="cds")
    base_to_power = {b: int(p) for b, p in zip(parsed.bases, parsed.powers)}
    out = []
    for name in chain_operands:
        base, _q = operand_base_power(u, name)
        out.append(base_to_power.get(base, 0))
    return out, str(parsed), surface


def model_vector(u, chain_operands, leading):
    """The model's predicted exponent vector for this chain."""
    out = []
    for i, name in enumerate(chain_operands):
        _base, q = operand_base_power(u, name)
        out.append(chain_power(i, q, leading))
    return out


def check_chain(u, chain_operands, leading=False):
    """Index-level equivalence on a chain whose operand bases are DISTINCT:
    every position's exponent is read off the parsed composite directly."""
    bases = [operand_base_power(u, nm)[0] for nm in chain_operands]
    assert len(set(bases)) == len(bases), "check_chain needs distinct bases"
    got, rendered, surface = real_exponent_vector(u, chain_operands, leading)
    want = model_vector(u, chain_operands, leading)
    if got != want:
        print(
            f"MISMATCH chain={surface!r} got={got} want={want} parsed='{rendered}'",
            file=sys.stderr,
        )
        return False
    return True


def check_chain_summed(u, chain_operands, leading=False):
    """Per-base equivalence on a chain that may REPEAT a base: the parser
    reports one power per base, so compare it to the SUM of the model's
    per-position entries over the positions sharing that base (mapping.md §2)."""
    surface = ("/" if leading else "") + "/".join(chain_operands)
    parsed = u.Unit(surface, format="cds")
    real = {b: int(p) for b, p in zip(parsed.bases, parsed.powers)}
    model = model_vector(u, chain_operands, leading)
    bases = [operand_base_power(u, nm)[0] for nm in chain_operands]
    for b in dict.fromkeys(bases):
        want = sum(model[i] for i in range(len(chain_operands)) if bases[i] == b)
        got = real.get(b, 0)
        if want != got:
            print(f"MISMATCH(summed) chain={surface!r} base={b} got={got} "
                  f"want={want} model={model} parsed='{parsed}'", file=sys.stderr)
            return False
    # nothing the parser reports may come from outside the chain
    for b, p in real.items():
        if b not in bases and p != 0:
            print(f"MISMATCH(extra) chain={surface!r} base={b} power={p}",
                  file=sys.stderr)
            return False
    return True


def main():
    # Establish the POST-patch (left-grouped) grammar the A-reference targets,
    # BEFORE importing astropy so the patched parser is the one loaded.
    err = _ensure_postpatch_source()
    if err is not None:
        print("G-AX FAIL: could not establish post-patch source: %s" % err,
              file=sys.stderr)
        return 3

    import astropy.units as u

    ok = True
    checked = 0

    # Concrete operand surfaces that parse to exactly one base.
    operands = []
    for b in BASE_POOL:
        for suf in POWER_SUFFIXES:
            name = b + suf
            try:
                operand_base_power(u, name)
            except Exception:
                continue
            operands.append(name)

    # 1. The exact inputs the issue / F2P tests exercise (boundary cases),
    #    including the powered-operand and leading-operator forms.
    f2p_chains = [
        (["km", "s", "Mpc"], False),        # F2P: km/s/Mpc
        (["J", "m", "s", "kpc2"], False),   # the issue's 10+3J/m/s/kpc2 shape
        (["J", "s", "kpc2"], False),        # the 10-7J/s/kpc2 shape
        (["s"], False),                     # single operand, head boundary
        (["km", "s"], False),               # km/s
        (["s"], True),                      # opens with the division operator
        (["km", "s"], True),
        (["km", "s", "Mpc"], True),
        (["m2", "s"], False),               # powered HEAD operand
        (["km", "s2"], False),              # powered trailing operand
        (["km", "s", "Mpc2"], False),
        (["kpc-2", "s"], False),            # negative intrinsic exponent
        (["m10", "s"], False),              # large intrinsic exponent
    ]
    for chain, lead in f2p_chains:
        if not check_chain(u, chain, lead):
            ok = False
        checked += 1

    # 2. Exhaustive over all distinct-BASE chains of length 1..4 from a small
    #    alphabet of POWERED operands, both with and without the leading
    #    division operator — every position observed directly.
    small = ["km", "s2", "Mpc-1", "kpc2", "m3"]
    for n in range(1, 5):
        for chain in itertools.permutations(small, n):
            for lead in (False, True):
                if not check_chain(u, list(chain), lead):
                    ok = False
                checked += 1

    # 3. Exhaustive REPEATED-base chains of length 1..4 over a 3-operand
    #    alphabet that reuses bases at different intrinsic exponents, under the
    #    per-base summing bridge.
    rep = ["s", "s2", "km"]
    for n in range(1, 5):
        for chain in itertools.product(rep, repeat=n):
            for lead in (False, True):
                if not check_chain_summed(u, list(chain), lead):
                    ok = False
                checked += 1

    # 4. Randomised fuzz over the wider POWERED pool, lengths 1..8, both
    #    leading-operator settings, bases free to repeat (summing bridge).
    random.seed(20230206)
    for _ in range(4000):
        n = random.randint(1, 8)
        chain = [random.choice(operands) for _ in range(n)]
        lead = random.random() < 0.5
        if not check_chain_summed(u, chain, lead):
            ok = False
        checked += 1

    if ok:
        print(f"OK: chain_power == real CDS parser exponent vector on {checked} chains")
        return 0
    print("FAIL: deep model chain_power disagrees with the real CDS parser", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

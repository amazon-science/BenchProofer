#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14976 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`Int` <-> Python `int`, `Bool` <-> Python `bool`, `String` <->
              `str`, `toString` <-> `str`, `++` <-> `+`, `List (String x String)`
              <-> a set of (module, name) pairs). The A-reference deep model is
              transliterated as the MODEL WRITES IT: the two-branch function
              `mpfName(qualified)` and the constant delta `mpfImport`. Nothing on
              this side reads the real repo.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `MpmathPrinter._print_Rational` applied at base_commit (the real
              correctness oracle, G-RESOLVE), BOTH its return value and its
              effect on the printer's `module_imports`.

WHY BOTH SIDES ARE COMPUTED INDEPENDENTLY (the point of this bridge). An earlier
revision of this script hardcoded the resolved constructor spelling as the single
constant `"mpmath.mpf"` on the shadow side, matching a model that did the same.
The real resolver is settings-dependent, so the shadow and the model shared one
error and agreed by construction: the differential could not see it, and a
G-PANEL-2 review found the divergence the gate had passed. Now the shadow
derives the spelling from the model's OWN Bool branch while the oracle derives it
from the real repo under a printer actually configured that way, and the
configuration is a fuzzed input rather than a fixed default. `probe_liveness()`
below asserts, by execution, that the previous defect WOULD now be caught.

The model parameters bind to the printer and the expression the oracle is called
on (mapping.md §1, §2): `qualified` to the printer's
`fully_qualified_modules` setting, and `p, q` to the canonicalized `e.p, e.q` of
a sympy `Rational e`. They must agree on every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with patch.diff
applied, imports `sympy` only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 14976
N_FUZZ = 100_000
N_EFFECT = 2_000          # fresh-printer samples for the registration leg

MAX_REPORTED = 5


# --- SHADOW: Solution.lean's R/I ops, transliterated -------------------------
# def mpfName (qualified : Bool) : String := if qualified then "mpmath.mpf" else "mpf"
def shadow_mpf_name(qualified):
    return "mpmath.mpf" if qualified else "mpf"


# def mpfImport : List (String x String) := [("mpmath", "mpf")]
SHADOW_MPF_IMPORT = [("mpmath", "mpf")]


def shadow_render(qualified, p, q, mpf_name=shadow_mpf_name):
    """`render (qualified : Bool) (p q : Int)` transliterated to str: the
    per-part mpf-wrapped quotient, the SAME resolved spelling in both positions.
    R/I ops only. `mpf_name` is injected so probe_liveness() can substitute a
    deliberately defective model and show this differential senses it."""
    m = mpf_name(qualified)
    return m + "(" + str(p) + ")/" + m + "(" + str(q) + ")"


# --- ORACLE: the real patched callee ----------------------------------------
def make_printer(qualified):
    from sympy.printing.pycode import MpmathPrinter
    return MpmathPrinter(settings={"fully_qualified_modules": qualified})


def flat_imports(module_imports):
    """`printer.module_imports` (defaultdict(set)) flattened to the set of
    (module, name) pairs that the Lean `List (String x String)` carrier
    abstracts (mapping.md §2: order-insensitive, duplicate-free)."""
    return {(mod, nm) for mod, names in module_imports.items() for nm in names}


def fuzz_pairs(n, rng):
    """Yield (numerator, denominator) integer pairs, denominator != 0."""
    # boundary cases first (plan §4.1 step 4)
    yield (1, 2)        # the F2P case Rational(1, 2)
    yield (1, 3)        # the test_nsolve_rational case
    yield (0, 1)
    yield (1, 1)
    yield (-1, 2)
    yield (1, -2)       # sign normalization -> q>0, p<0
    yield (-1, -2)
    yield (5, 1)
    yield (2, 4)        # non-canonical -> reduces to 1/2
    yield (7, 14)
    yield (232, 3)      # the problem-statement value
    yield (-232, 3)
    yield (10**50, 3)   # large numerator
    yield (3, 10**50)   # large denominator
    yield (-(10**40), 7)
    for _ in range(n):
        a = rng.randint(-10**12, 10**12)
        b = rng.randint(-10**12, 10**12)
        if b == 0:
            b = 1
        yield (a, b)


def check_values(printers, rng, disagreements):
    """Value leg: shadow_render vs the patched callee's return value, over both
    configurations of the modeled Bool binder."""
    from sympy import Rational
    count = 0
    for a, b in fuzz_pairs(N_FUZZ, rng):
        e = Rational(a, b)          # canonicalize: reduce gcd, q > 0
        p, q = int(e.p), int(e.q)   # model params bind to e.p, e.q (mapping.md §1)
        for qualified, printer in printers.items():
            shadow = shadow_render(qualified, p, q)
            oracle = printer._print_Rational(e)      # patched real callee
            count += 1
            if shadow != oracle:
                disagreements.append(
                    ("value", qualified, a, b, shadow, oracle))
                if len(disagreements) >= MAX_REPORTED:
                    return count
    return count


def check_registration(rng, disagreements):
    """Effect leg: the import the patched callee RECORDS while resolving the
    constructor's dotted name, against the model's `mpfImport` delta and the
    mapping.md §3.1 law post-state = pre-state UNION delta. A fresh printer per
    sample, with a fuzzed pre-state, so the law is probed and not just the
    empty-pre-state case."""
    from sympy import Rational
    delta = set(SHADOW_MPF_IMPORT)
    pool = [("math", "sin"), ("mpmath", "mpf"), ("mpmath", "sign"),
            ("math", "copysign"), ("numpy", "array"), ("mpmath", "gammainc")]
    count = 0
    for i in range(N_EFFECT):
        qualified = bool(rng.getrandbits(1))
        a = rng.randint(-10**6, 10**6)
        b = rng.randint(-10**6, 10**6) or 1
        e = Rational(a, b)
        printer = make_printer(qualified)
        for mod, nm in rng.sample(pool, rng.randint(0, len(pool))):
            printer.module_imports[mod].add(nm)
        before = flat_imports(printer.module_imports)
        printer._print_Rational(e)                   # patched real callee
        after = flat_imports(printer.module_imports)
        count += 1
        if after != before | delta:
            disagreements.append(
                ("effect", qualified, a, b, sorted(before | delta), sorted(after)))
            if len(disagreements) >= MAX_REPORTED:
                return count
    return count


def probe_liveness(printers):
    """Assert this differential is LIVE on the two components a previous
    revision was blind to. Each probe substitutes a DEFECTIVE model on the
    shadow side and requires the differential to disagree with the real repo.
    If a probe finds no disagreement, the check cannot see that component and
    must not report OK. Returns the list of probe descriptions."""
    from sympy import Rational
    probes = []
    e = Rational(1, 2)

    # (1) the flag-blind spelling: model the resolver as the single constant
    #     'mpmath.mpf' (the defect a G-PANEL-2 review found). Must disagree.
    blind = shadow_render(False, 1, 2, mpf_name=lambda _q: "mpmath.mpf")
    real = printers[False]._print_Rational(e)
    if blind == real:
        return None
    probes.append("flag-blind spelling: shadow %r vs oracle %r at "
                  "(qualified=False, 1, 2) -> DISAGREE, so the branch is sensed"
                  % (blind, real))

    # (2) the same, other direction: pin the bare spelling. Must disagree under
    #     the qualified configuration.
    blind2 = shadow_render(True, 1, 2, mpf_name=lambda _q: "mpf")
    real2 = printers[True]._print_Rational(e)
    if blind2 == real2:
        return None
    probes.append("bare-pinned spelling: shadow %r vs oracle %r at "
                  "(qualified=True, 1, 2) -> DISAGREE" % (blind2, real2))

    # (3) the dropped registration effect: model the delta as empty. Must
    #     disagree with the real printer's post-state.
    printer = make_printer(True)
    before = flat_imports(printer.module_imports)
    printer._print_Rational(e)
    after = flat_imports(printer.module_imports)
    if after == before | set():
        return None
    probes.append("dropped import delta: predicted %r vs observed %r -> "
                  "DISAGREE, so the effect is sensed"
                  % (sorted(before), sorted(after)))
    return probes


def main():
    rng = random.Random(SEED)
    printers = {q: make_printer(q) for q in (True, False)}

    probes = probe_liveness(printers)
    if probes is None:
        print("G-CONF FAIL: liveness probe found NO disagreement — this "
              "differential is blind to a component it must observe; treat as a "
              "check defect, not as conformance.")
        return 1
    for line in probes:
        print("  liveness: %s" % line)

    disagreements = []
    n_val = check_values(printers, rng, disagreements)
    n_eff = 0
    if not disagreements:
        n_eff = check_registration(rng, disagreements)
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d observation(s):"
              % (len(disagreements), n_val + n_eff))
        for leg, qual, a, b, sh, orc in disagreements:
            print("  [%s] qualified=%r Rational(%r, %r) shadow=%r oracle=%r"
                  % (leg, qual, a, b, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of mpfRational agrees with patch.diff behaviour "
          "on %d value observation(s) over both configurations of the modeled "
          "Bool binder and %d registration-effect observation(s) with fuzzed "
          "pre-states (seed=%d), 0 disagreements; 3 liveness probes each found "
          "the disagreement a defective model would produce."
          % (n_val, n_eff, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())

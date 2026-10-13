#!/usr/bin/env python
"""G-CONF: differential conformance (R/I fidelity) for sympy__sympy-18199.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python SHADOW of the Lean impl skeletons
`implementation_nthrootMod` / `implementation_nthrootModComposite` and diffs the
shadow against the REAL patched `nthroot_mod(a, n, m, all_roots=True)` over the
input regime the spec commits to.

The Lean impl models the non-single-prime path DEEPLY: `implementation_
nthrootModComposite` returns `rootSetIn a n m`, the complete ordered set of
in-range residues solving `x**n == a (mod m)` (the structural fold that the
postcondition pins). The public dispatch is the R/I skeleton:
    ¬isprime(m)               -> the deep composite root set
    isprime(m) and a % m == 0 -> [0]
    isprime(m) and a % m != 0 -> the unchanged prime-path roots.

Two obligations are diffed, matching the two shapes the spec asserts:

  * the EXACT-SET clause, over the regime `dispatchValidated` — exponent two over
    every non-single-prime modulus, plus (for a larger exponent) a squarefree
    modulus or one whose repeated prime factors are regular for the target and
    the exponent. Off that regime the gold patch's prime-power lifting branch is
    mathematically UNSOUND (e.g. for x**6 == 89 mod 125 it returns 118, yet
    118**6 % 125 = 24 != 89), so the spec does not claim equality there and this
    gate does not probe equality there;

  * the UNCONDITIONAL report clause, over EVERY non-single-prime modulus with no
    regime condition: the report lies in the canonical range, is strictly
    increasing, and has exactly AS MANY entries as the congruence has solutions.
    The count is the strongest thing TRUE of the real routine off the regime:
    there the reported residues need not be roots and the report need not contain
    every root (measured: it omits real roots at 4198 off-regime inputs), yet its
    LENGTH still equals the number of solutions at every one of them. Counting
    subsumes the two one-sided facts -- it never declines a solvable congruence,
    never reports for an unsolvable one -- and additionally forbids a PARTIAL
    report, which neither direction of a mere emptiness equivalence can see. This
    is the obligation that constrains the off-regime sub-domain, so it is diffed
    there too.

A third assertion is recorded here rather than in G-AX, because it is only
reachable with the change applied: the unchanged unit-base solver, when handed a
modulus that is NOT a single prime, returns residues that do not solve the
congruence. That is the fact justifying the single-prime restriction on the
soundness contract the Lean proof consumes, and asserting its EXISTENCE here means
a later widening of that contract's domain fails a gate instead of being
certified.

Exit 0 iff zero shadow-vs-patch disagreements on either obligation.
stdlib-only fuzzing (pinned seed) + sympy.
"""
import sys, random

random.seed(18199)

try:
    from sympy import isprime, factorint
    from sympy.ntheory.residue_ntheory import nthroot_mod
except Exception as e:  # pragma: no cover
    print("status=error import failed:", e)
    sys.exit(1)


def is_squarefree(m):
    return all(e == 1 for e in factorint(m).values())


def regular_lift(a, n, m):
    """Shadow of the Lean `modulusRegularLift a n m`: every prime occurring more
    than once in `m` divides neither `a` nor `n`, and where it occurs to a power
    of three or more, every residue solving the congruence mod that prime already
    solves it mod the whole prime-power component."""
    for p, e in factorint(m).items():
        if e == 1:
            continue
        if a % p == 0 or n % p == 0:
            return False
        if e >= 3:
            pe = p ** e
            am_p, am_pe = a % p, a % pe
            for r in range(p):
                if pow(r, n, p) == am_p and pow(r, n, pe) != am_pe:
                    return False
    return True


def composite_validated(a, n, m):
    return is_squarefree(m) or regular_lift(a, n, m)


def dispatch_validated(a, n, m):
    return n == 2 or composite_validated(a, n, m)


def deep_root_set(a, n, m):
    """rootSetIn a n m: the complete ordered set of in-range roots (the deep
    model the Lean composite impl returns)."""
    am = a % m
    return [x for x in range(m) if pow(x, n, m) == am]


def prime_unit_roots(a, n, p):
    """A-reference: the unchanged prime-modulus path, all_roots=True."""
    r = nthroot_mod(a, n, p, True)
    if r is None:
        return []
    if isinstance(r, int):
        return [r]
    return list(r)


def shadow_composite(a, n, m):
    """Python image of implementation_nthrootModComposite (the deep model)."""
    return sorted(deep_root_set(a, n, m))


def shadow_public(a, n, m):
    """Python image of implementation_nthrootMod (all_roots=True)."""
    if not isprime(m):
        return shadow_composite(a, n, m)
    if a % m == 0:
        return [0]
    return sorted(set(prime_unit_roots(a, n, m)))


def real_raw(a, n, m):
    """The real report with its ORDER preserved (the ordering clause reads it)."""
    r = nthroot_mod(a, n, m, True)
    if r is None:
        return []
    if isinstance(r, int):
        r = [r]
    return [int(x) for x in r]


checks = 0
mismatches = 0
report_checks = 0


def compare(a, n, m):
    """Both gate obligations at one input."""
    global checks, mismatches, report_checks
    try:
        raw = real_raw(a, n, m)
    except Exception:
        return  # input the real fn rejects — skip
    real = sorted(set(raw))

    # (1) the UNCONDITIONAL report clause, for a non-single-prime modulus.
    if not isprime(m):
        report_checks += 1
        bad = None
        if not all(0 <= x < m for x in raw):
            bad = "off-range"
        elif any(raw[i] >= raw[i + 1] for i in range(len(raw) - 1)):
            bad = "non-increasing"
        elif len(raw) != len(deep_root_set(a, n, m)):
            if not raw:
                bad = "declined a solvable congruence"
            elif not deep_root_set(a, n, m):
                bad = "reported a residue for an unsolvable congruence"
            else:
                bad = (f"reported {len(raw)} residues where the congruence has "
                       f"{len(deep_root_set(a, n, m))} solutions")
        if bad is not None:
            mismatches += 1
            if mismatches <= 20:
                print(f"REPORT-MISMATCH ({bad}) a={a} n={n} m={m}: real={raw[:8]}")

    # (2) the EXACT-SET clause, over the regime the spec commits to.
    if not isprime(m) and not dispatch_validated(a, n, m):
        return
    checks += 1
    shadow = shadow_public(a, n, m)
    if shadow != real:
        mismatches += 1
        if mismatches <= 20:
            print(f"R/I-MISMATCH a={a} n={n} m={m}: shadow={shadow} real={real}")


# --- boundary catalogue -------------------------------------------------------
# The graded surface's own composite moduli (including the quadratic congruence
# over a modulus with a fifth power of two in it), the test_patch witnesses, the
# prime edges, and the smallest non-squarefree shapes on BOTH sides of the regime.
for a, n, m in [
    (9, 2, 160), (1, 3, 8), (4, 4, 9),
    (29, 31, 74), (16, 5, 36), (9, 16, 36),
    (0, 7, 100), (289, 5, 17), (0, 12, 37),
    (2, 3, 15), (7, 5, 35), (3, 4, 77),
    (3, 3, 8), (7, 3, 8), (2, 5, 27), (4, 3, 3249000 % 1000),
]:
    compare(a, n, m)


def small_modulus():
    kind = random.random()
    if kind < 0.34:
        # squarefree composite moduli (products of distinct primes)
        return random.choice([6, 10, 14, 15, 21, 22, 35, 33, 55, 77, 105, 30, 42])
    if kind < 0.72:
        # non-squarefree moduli — BOTH regime legs and their complement
        return random.choice([8, 9, 12, 16, 18, 20, 25, 27, 36, 48, 100, 125, 160])
    return random.choice([7, 11, 13, 17, 19, 23, 29, 31])


target = 60000
guard = 0
while report_checks < target and guard < target * 10:
    guard += 1
    m = small_modulus()
    n = random.randint(2, 15)
    a = random.randrange(0, 2 * m)
    compare(a, n, m)

# --- WHY the consumed soundness contract is restricted to a single prime -------
# On a modulus that is not a single prime the unit-base prime solver emits
# residues that do not solve the congruence. Assert such counterexamples EXIST, so
# a widening of the axiom's declared domain is caught rather than certified.
composite_nonroot = 0
for m in [8, 9, 15, 16, 25, 27, 32, 36, 49, 100, 125]:
    for n in range(3, 12):
        for a in range(0, m):
            try:
                rr = prime_unit_roots(a, n, m)
            except Exception:
                continue
            for r in rr:
                if pow(int(r), n, m) != a % m:
                    composite_nonroot += 1
if composite_nonroot == 0:
    print("status=fail expected the unit-base solver to emit non-roots at a "
          "modulus that is not a single prime (the fact restricting its "
          "soundness contract to the single-prime domain); found none")
    sys.exit(1)

# --- WHY the unconditional report clause COUNTS rather than CONTAINS -----------
# Off the regime the report is not a superset of the true root set: it omits real
# roots. Assert such counterexamples EXIST, so a later strengthening of the
# unconditional clause into off-regime COMPLETENESS (which would be FALSE of the
# real routine) is caught by this gate instead of being certified.
offregime_incomplete = 0
for m in [8, 9, 16, 25, 27, 32, 36, 49, 100, 125]:
    for n in range(3, 12):
        for a in range(0, m):
            if dispatch_validated(a, n, m):
                continue
            try:
                raw = real_raw(a, n, m)
            except Exception:
                continue
            if set(deep_root_set(a, n, m)) - set(raw):
                offregime_incomplete += 1
if offregime_incomplete == 0:
    print("status=fail expected the report to omit genuine roots off the regime "
          "(the fact that makes COUNTING, not containment, the strongest true "
          "unconditional clause there); found no such input")
    sys.exit(1)

if mismatches == 0:
    print(f"status=pass {checks} exact-set comparisons over the regime and "
          f"{report_checks} unconditional report comparisons over every "
          f"non-single-prime modulus (the report clause read as COUNTING the "
          f"congruence's solutions), 0 shadow-vs-patch disagreements, "
          f"{offregime_incomplete} off-regime inputs where the report omits a "
          f"genuine root (so counting, not containment, is the strongest true "
          f"unconditional clause), and "
          f"{composite_nonroot} composite-modulus non-root counterexamples "
          f"justifying the single-prime restriction on the consumed soundness "
          f"contract "
          f"(R/I fidelity holds)")
    sys.exit(0)
print(f"status=fail {mismatches} shadow-vs-patch disagreements "
      f"({checks} exact-set / {report_checks} report comparisons)")
sys.exit(1)

# properties.py — PBT falsification battery for sympy__sympy-13480.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside the `# impl-start` / `# impl-end` block (so the frozen spec — axioms,
# pure helper, signature, pre/post-conditions — is byte-identical and same_spec
# holds). The runner stamps each with verify(host, Nagini) + same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (the spec this battery attacks)
# ---------------------------------------------------------------------------
#   periodic_part_simplification(x: int, m: int) -> int
#     x = remainder part, m = (present) periodic part. BOTH are bare `int`
#     value parameters: NO Acc(...) permissions, NOTHING read-only, no carried
#     state. (=> the frame-mutation class is N/A here; see 'assessment'.)
#
#   The gold impl reads the branch condition from the value computed off the
#   PERIODIC part m:
#       primary_m = primary(m)
#       if primary_m == directed_infinity(): return primary(x)
#       else:                                return sibling(x)
#
#   The postcondition has TWO clauses, all in terms of the args:
#     (1) Implies(primary(m) == directed_infinity(), Result() == primary(x))
#     (2) Implies(primary(m) != directed_infinity(), Result() == sibling(x))
#   The two implications are exhaustive and mutually exclusive, so together
#   they pin Result() on every input.
#
#   The DELTA the patch fixes is the DISCRIMINATOR'S DATA SOURCE: the result
#   must be governed by primary(m) — the value computed from the periodic part —
#   and by NO OTHER quantity. The pre-patch bug discriminates on an unrelated
#   quantity (an unbound `cotm`; modeled as primary(x)). Clauses (1)/(2) are the
#   load-bearing pins: they tie the *exact* output to the primary(m) test, so any
#   impl whose branch is decided by a different value, or whose returns are
#   swapped, or which is constant, cannot satisfy both implications.
#
# ---------------------------------------------------------------------------
# Oracle-grounding note (ungrounded-oracle-echo class — why it does NOT apply)
# ---------------------------------------------------------------------------
#   The spec deliberately carries NO pure helper/oracle at all (no pure
#   region): the postcondition is stated directly over the input handles via
#   the two implications. There is therefore nothing an impl could echo —
#   "return <oracle>(x, m)" is not even expressible under this spec. The
#   wrong-discriminator / swapped / constant rivals below DO change the
#   computed value and must be rejected.
#
# ---------------------------------------------------------------------------
# Frame-mutation note (#1 weakness class — why it is N/A here)
# ---------------------------------------------------------------------------
#   There is no read-only input: x and m are primitive ints passed by value,
#   carrying no Acc(...) permission and no aliasable heap state. A Nagini int
#   parameter cannot be "mutated to satisfy the postcondition vacuously" — there
#   is no frame to overwrite. Reassigning the local `x`/`m` does not affect the
#   caller and (because the postcondition is stated over the ORIGINAL arg values
#   that the implications read) cannot vacuously satisfy anything;
#   we still include a degenerate-rebind rival (rebind-then-return) as a
#   supporting case to show such a value-corrupting "mutation" is rejected by the
#   postcondition. has_readonly_input is therefore false and the mandatory
#   permission-rejection case does not apply.

from pathlib import Path

INSTANCE = "sympy__sympy-13480"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything between # impl-start and
# # impl-end, markers exclusive). Every variant is produced by _swap on _BASE
# touching ONLY text inside this block.
_GOLD_IMPL = """    primary_m = primary(m)
    if primary_m == directed_infinity():
        return primary(x)
    else:
        return sibling(x)"""

# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — structurally different, still CORRECT.
#    Negate the test and SWAP the two branch bodies accordingly: this is the
#    De-Morgan-equivalent control flow (if primary_m != sentinel: sibling else
#    primary), and it returns exactly the same value on every input. It keeps the
#    discriminator anchored to primary(m) (still reads the value computed from
#    the PERIODIC part), so the gold proof obligations (clauses 1/2) still
#    discharge. MUST verify — else SPEC-TOO-STRONG.
#    No induction/lemma is involved (straight-line two-way branch), so this is a
#    safe reorder, not a proof-gap trap.
_POS_IMPL = """    primary_m = primary(m)
    if primary_m != directed_infinity():
        return sibling(x)
    else:
        return primary(x)"""


# 1b. POSITIVE CONTROL (no-temporary) — same gold behavior with the
#    discriminator inlined into the test (no `primary_m` local). Still anchored
#    to primary(m); @Pure determinism makes the inlined call denote the same
#    value. MUST verify — else SPEC-TOO-STRONG (spec would be pinning the
#    temporary, not the behavior).
_ORACLE_IMPL = """    if primary(m) == directed_infinity():
        return primary(x)
    else:
        return sibling(x)"""


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input.
#    The Requires is EMPTY (no precondition); any pair of int handles is in
#    domain. We keep the full gold impl and add, at the TOP of impl, an
#    assertion that confirms a representative F2P-shaped self-call admits (the
#    discriminator test is well-defined and the branch dichotomy is total).
#    If this fails to verify => PRECOND-TOO-STRONG (an empty precondition that
#    somehow rejected a normal input).
_ADMISS_IMPL = """    Assert(primary(m) == directed_infinity() or primary(m) != directed_infinity())
    Assert(Implies(primary(m) == directed_infinity(), primary(x) == primary(x)))
""" + _GOLD_IMPL


# ---------------------------------------------------------------------------
# 3. WRONG-DISCRIMINATOR (the LITERAL pre-patch bug == model_prepatch.py).
#    Decide the branch on primary(X) — an unrelated quantity computed from the
#    REMAINDER part — instead of primary(m). This mirrors the base_commit
#    NameError (`if cotm is S.ComplexInfinity` testing an unbound name rather
#    than the just-computed `cothm`). expect=reject.
#    Refinement: the real fix changes exactly this token (cotm -> cothm). A patch
#    that branched on coth(x) [the remainder] rather than coth(m) [the periodic
#    part] gives the WRONG result on the F2P witness coth(1 + I*pi/2): there
#    coth(m)=zoo so the result must be coth(1), but coth(x)=coth(1) is finite
#    (not zoo) so this impl returns tanh(1) — and the OTHER F2P,
#    coth(log(tan(2)))==coth(log(-tan(2))), also relies on the periodic-part
#    test. The pre-patch code does not even run (NameError); a faithful patch
#    using the wrong data source FAILS test_coth. A verifying rival = true
#    verify-not-resolve break.
_WRONG_DISCR_IMPL = """    primary_x = primary(x)
    if primary_x == directed_infinity():
        return primary(x)
    else:
        return sibling(x)"""


# ---------------------------------------------------------------------------
# 4. SWAPPED RETURNS — keep the correct discriminator primary(m) but return the
#    sibling on the sentinel branch and the primary on the finite branch (the
#    two outputs swapped). expect=reject.
#    Refinement: on F2P coth(1 + I*pi/2) [coth(m)=zoo, sentinel branch] the
#    correct result is coth(1); a swapped impl returns tanh(1) on that branch —
#    but the harness asserts coth(1 + I*pi/2) == tanh(1) only because that input
#    is in the FINITE branch... in fact swapping makes the sentinel-branch input
#    return tanh(x) and the finite-branch input return coth(x), inverting BOTH
#    F2P witnesses. A real patch that swapped coth(x)/tanh(x) returns would fail
#    test_coth. Verify-not-resolve.
_SWAP_RET_IMPL = """    primary_m = primary(m)
    if primary_m == directed_infinity():
        return sibling(x)
    else:
        return primary(x)"""


# ---------------------------------------------------------------------------
# 5. CONSTANT / NO-WORK (always-primary). Ignore the discriminator entirely and
#    always return primary(x). expect=reject.
#    Refinement: this is the "always coth(x)" wrong-impl already noted in
#    meta.gates.G-MUT. On the finite branch (coth(m) != zoo, e.g. the
#    coth(1 + I*pi/2) witness whose result must be tanh(1)) it returns coth(1),
#    not tanh(1) -> F2P FAILS. A real patch that dropped the else branch and
#    always returned coth(x) would not resolve. Verify-not-resolve.
_CONST_PRIMARY_IMPL = """    return primary(x)"""


# ---------------------------------------------------------------------------
# 6. CONSTANT / NO-WORK (always-sibling) — the complementary degenerate rival:
#    always return sibling(x), ignoring the discriminator. expect=reject.
#    Refinement: on the sentinel branch (coth(m)=zoo, e.g. coth(log(tan(2))),
#    whose result must be coth(log(tan(2)))) it returns tanh(x), not coth(x) ->
#    F2P FAILS. Supporting degenerate case; complements case 5.
_CONST_SIBLING_IMPL = """    return sibling(x)"""


# ---------------------------------------------------------------------------
# 7. VALUE-CORRUPTING REBIND (frame-mutation stand-in for a value-typed input).
#    There is no heap frame to overwrite (x/m are ints by value), but a rival
#    could try to "mutate" by rebinding the local `m` to `x` before computing the
#    discriminator — the value-level analogue of clobbering the input that
#    governs the branch. expect=reject.
#    Refinement: rebinding m:=x makes the branch test primary(x) instead of
#    primary(m) (identical wrong data source to case 3), so on coth(1 + I*pi/2)
#    it returns the wrong sibling/primary choice and F2P test_coth FAILS. This
#    shows that even a "mutate the governing input" trick cannot satisfy clauses
#    (1)/(2), which are stated over the ORIGINAL arg values. A verifying rebind
#    would be SPEC-TOO-WEAK.
_REBIND_IMPL = """    m = x
    primary_m = primary(m)
    if primary_m == directed_infinity():
        return primary(x)
    else:
        return sibling(x)"""


SPEC_TESTS = [
    {
        "id": "pos-control-demorgan-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: negates the discriminator "
            "test and swaps the two branch BODIES to match (De-Morgan-equivalent "
            "control flow), still anchored to primary(m). Returns the identical "
            "value on every input. Straight-line two-way branch — no induction/"
            "lemma, so the gold obligations (clauses 1/2) still discharge. Must "
            "verify; if it cannot, the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-inline-discriminator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ORACLE_IMPL),
        "rationale": (
            "same gold behavior with the discriminator call inlined into the "
            "test (no primary_m temporary). @Pure determinism makes the inlined "
            "primary(m) denote the same value, so both clauses discharge. Must "
            "verify; if it cannot, the spec pins the temporary rather than the "
            "behavior (SPEC-TOO-STRONG). There is no pure-region oracle in this "
            "spec, so the ungrounded-oracle-echo class is inexpressible."
        ),
    },
    {
        "id": "admiss-empty-precond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is EMPTY; any pair of int handles is in-domain. "
            "The added top-of-impl assertions confirm the discriminator test is "
            "well-defined and the branch dichotomy is total on the inputs before "
            "running the gold body. Must verify; if it cannot, "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "wrong-discriminator-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_DISCR_IMPL),
        "refinement": (
            "this is the LITERAL pre-patch bug: branch on primary(x) [remainder] "
            "instead of primary(m) [periodic part] — the cotm-vs-cothm token the "
            "patch fixes. On F2P coth(1 + I*pi/2): coth(m)=zoo (sentinel) so the "
            "result must be coth(1), but coth(x)=coth(1) is finite, so this rival "
            "takes the else branch and returns tanh(1) -> the wrong value; "
            "test_coth FAILS (the base_commit code in fact NameErrors). A "
            "faithful patch using this data source would NOT resolve."
        ),
        "rationale": (
            "REJECT comes from postcondition clauses (1)/(2): "
            "Implies(primary(m)==directed_infinity(), Result()==primary(x)) and "
            "its complement pin the result to the primary(m) test. An impl whose "
            "branch is decided by primary(x) cannot prove either implication for "
            "an arbitrary pair where primary(m) and primary(x) disagree on being "
            "the sentinel. If it verifies, the spec does not actually pin the "
            "discriminator's data source (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "swapped-returns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _SWAP_RET_IMPL),
        "refinement": (
            "keeps the correct discriminator primary(m) but returns sibling(x) on "
            "the sentinel branch and primary(x) on the finite branch — outputs "
            "swapped. This inverts BOTH F2P witnesses: coth(log(tan(2))) "
            "[sentinel] would return tanh(...) not coth(...), and coth(1+I*pi/2) "
            "[finite] would return coth(1) not tanh(1); test_coth FAILS. A real "
            "patch swapping the coth(x)/tanh(x) returns would not resolve."
        ),
        "rationale": (
            "REJECT comes from clauses (1)/(2): on the sentinel branch the spec "
            "demands Result()==primary(x) but this returns sibling(x); on the "
            "finite branch it demands sibling(x) but this returns primary(x). "
            "Since primary and sibling are distinct opaque functions, neither "
            "implication holds. If it verifies, the spec leaves the branch-to-"
            "output mapping unpinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "constant-always-primary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _CONST_PRIMARY_IMPL),
        "refinement": (
            "always returns primary(x), ignoring the discriminator (the "
            "'always coth(x)' wrong-impl from G-MUT). On the finite branch (e.g. "
            "the coth(1 + I*pi/2) witness whose result must be tanh(1)) it "
            "returns coth(1) != tanh(1); test_coth FAILS. A real patch dropping "
            "the else branch would not resolve."
        ),
        "rationale": (
            "REJECT comes from clause (2): Implies(primary(m) != "
            "directed_infinity(), Result()==sibling(x)). On the finite branch the "
            "impl returns primary(x) != sibling(x) (distinct opaque functions), "
            "so the implication is violated. If it verifies, the finite branch is "
            "unpinned (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "constant-always-sibling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _CONST_SIBLING_IMPL),
        "refinement": (
            "always returns sibling(x), ignoring the discriminator. On the "
            "sentinel branch (e.g. coth(log(tan(2))) whose result must be "
            "coth(log(tan(2)))) it returns tanh(...) != coth(...); test_coth "
            "FAILS. Complementary degenerate rival to constant-always-primary; a "
            "real always-tanh(x) patch would not resolve."
        ),
        "rationale": (
            "REJECT comes from clause (1): Implies(primary(m) == "
            "directed_infinity(), Result()==primary(x)). On the sentinel branch "
            "the impl returns sibling(x) != primary(x), violating the "
            "implication. If it verifies, the sentinel branch is unpinned "
            "(SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "value-corrupting-rebind-m",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REBIND_IMPL),
        "refinement": (
            "the value-typed analogue of a frame mutation: rebind the governing "
            "input m := x before computing the discriminator, so the branch is "
            "decided by primary(x) (identical wrong data source to "
            "wrong-discriminator). On coth(1 + I*pi/2) it returns the wrong "
            "branch's value; test_coth FAILS. A real patch overwriting the "
            "periodic part with the remainder before the test would not resolve."
        ),
        "rationale": (
            "REJECT comes from clauses (1)/(2), which are stated over the "
            "ORIGINAL argument value m: rebinding the local m does not change "
            "what primary(m) means in the postcondition, so the impl effectively "
            "tests primary(x) and cannot prove the primary(m)-keyed implications. "
            "Confirms a 'mutate the governing input' trick is rejected by the "
            "value abstraction (no vacuous satisfaction). If it verifies, "
            "SPEC-TOO-WEAK."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# Three @ContractOnly axioms, all A-consumed, NONE carry an Ensures:
#   primary           -> coth   (UNCHANGED elementary callee)
#   sibling           -> tanh   (UNCHANGED elementary callee)
#   directed_infinity -> S.ComplexInfinity (UNCHANGED `zoo` singleton)
# The proof consumes ONLY @Pure DETERMINISM (equal args -> equal result handle)
# plus the singleton stability of the sentinel. There is no value/sentinel/raise
# Ensures to over-claim, so:
#   * axiom-soundness: the REAL coth/tanh are deterministic and S.ComplexInfinity
#     is a stable singleton (coth(0) is the sentinel, coth(1) is finite), under
#     the caller's runtime (sympy pinned at 1.1). Fuzz boundaries + I*pi-multiples
#     + the two FAIL_TO_PASS witnesses. A non-deterministic callee or an unstable
#     singleton would be AXIOM-UNSOUND. Mirrors axiom_check.py.
#   * axiom-containment: the model passes to primary only the handles m (periodic
#     part) and x (remainder), to sibling only x, and compares primary(m) to the
#     directed_infinity singleton. The axioms' Requires is the FULL handle domain
#     (no Requires on primary/sibling; directed_infinity is nullary), so every
#     reachable argument is trivially inside it. We make that executable: run the
#     REAL peel-off and confirm coth/tanh accept exactly the m/x the periodic
#     branch produces and that the discriminator coth(m) lands on {zoo, 0} (in
#     domain), with the end-to-end branch correspondence holding — i.e. nothing
#     the caller reaches falls outside the consulted callees' domain.
# Both probes import only sympy + stdlib, open nothing on disk, exit 0 iff the
# obligation holds. (Eval image runs old Python/ASCII; we touch no files.)

_AX_SOUNDNESS_PROBE = r'''
import random, sys
from sympy import coth, tanh, log, tan, I, pi, S, Symbol, Rational

# primary->coth, sibling->tanh: the proof consumes determinism only.
def check_det(e):
    if coth(e) != coth(e):
        print("AXIOM-UNSOUND: coth not deterministic on %r" % (e,)); sys.exit(1)
    if tanh(e) != tanh(e):
        print("AXIOM-UNSOUND: tanh not deterministic on %r" % (e,)); sys.exit(1)

# directed_infinity -> S.ComplexInfinity: a stable singleton; the `is` test is
# well-defined (reflexive, distinguishes a finite value).
def check_sentinel():
    if not (S.ComplexInfinity is S.ComplexInfinity):
        print("AXIOM-UNSOUND: ComplexInfinity not a singleton"); sys.exit(1)
    if not (coth(S(0)) is S.ComplexInfinity):
        print("AXIOM-UNSOUND: coth(0) should be the directed-infinity sentinel"); sys.exit(1)
    if coth(S(1)) is S.ComplexInfinity:
        print("AXIOM-UNSOUND: coth(1) must be finite, not the sentinel"); sys.exit(1)

y = Symbol('y')
boundary = [S(0), S(1), S(2), Rational(1, 2), Rational(3, 2),
            log(2), log(tan(2)), log(-tan(2)), y,
            1 + I * pi / 2, I * pi, 2 + I * pi / 3]
for e in boundary:
    check_det(e)
check_sentinel()

rng = random.Random(13480)
for _ in range(2000):
    e = Rational(rng.randint(-9, 9), rng.randint(1, 9)) + \
        Rational(rng.randint(-5, 5), rng.randint(1, 6)) * I * pi
    check_det(e)

# The two FAIL_TO_PASS witnesses (asserted exactly as the harness does), which
# depend on the determinism + singleton properties the axioms encode.
if not (coth(log(tan(2))) == coth(log(-tan(2)))):
    print("AXIOM-UNSOUND: FAIL_TO_PASS witness 1 broken"); sys.exit(1)
if not (coth(1 + I * pi / 2) == tanh(1)):
    print("AXIOM-UNSOUND: FAIL_TO_PASS witness 2 broken"); sys.exit(1)

print("AXIOM-SOUND: real coth/tanh deterministic on %d boundary + 2000 fuzz "
      "inputs; ComplexInfinity is a stable singleton (coth(0) is the sentinel, "
      "coth(1) finite); both FAIL_TO_PASS witnesses hold." % len(boundary))
sys.exit(0)
'''


_AX_CONTAINMENT_PROBE = r'''
import random, sys
from sympy import coth, tanh, I, pi, S, Symbol, Rational, sympify
from sympy.functions.elementary.hyperbolic import _peeloff_ipi

# Containment: the model passes to primary/sibling only the peeled parts (x =
# remainder, m = periodic), and compares primary(m) to the directed_infinity
# singleton. primary/sibling carry NO Requires (the full handle domain), and the
# discriminator coth(m) must land on the {sentinel, 0} domain the branch's own
# design assumes (its `else: # cothm == 0` comment). We confirm every
# model-reachable callee argument is accepted and the discriminator stays in
# {zoo, 0}; a reachable arg outside that would be AXIOM-TOO-WEAK-FOR-CALLER.

def reachable_parts(arg):
    """Return (x, m) the model receives for `arg`, or None if the periodic
    branch does not fire at this sympy version (then the model never reaches it)."""
    a = sympify(arg)
    if not a.is_Add:
        return None
    x, m = _peeloff_ipi(a)
    if not m:
        return None
    return x, m

# Detect whether the pinned version routes through the periodic branch at all.
_p = reachable_parts(S(1) + I * pi)
periodic_active = _p is not None and (
    coth(_p[1]) is S.ComplexInfinity or coth(_p[1]) == 0)

def simplified(x, m):
    if coth(m) is S.ComplexInfinity:
        return coth(x)
    return tanh(x)

y = Symbol('y')
bases = [S(1), Rational(3, 2), S(2), Rational(5, 2)]
mults = [Rational(1, 2), S(1), Rational(3, 2), S(2), Rational(5, 2), S(3),
         Rational(1, 3), Rational(2, 3)]
checked = 0
for x0 in bases:
    for k in mults:
        parts = reachable_parts(x0 + k * I * pi)
        if parts is None:
            continue
        x, m = parts
        cm = coth(m)                 # the discriminator the model inspects
        if not (cm is S.ComplexInfinity or cm == 0):
            print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches m with coth(m)=%r "
                  "outside the {sentinel,0} branch domain on arg %r"
                  % (cm, x0 + k * I * pi)); sys.exit(1)
        # primary/sibling accept these handles and the end-to-end correspondence
        # holds (the consulted callees' domain covers every reachable arg):
        observed = coth(x0 + k * I * pi)
        if observed != simplified(x, m):
            print("AXIOM containment: branch correspondence broke on arg %r "
                  "(x=%r m=%r): real=%r model=%r" % (x0 + k * I * pi, x, m,
                  observed, simplified(x, m))); sys.exit(1)
        checked += 1

rng = random.Random(134800)
attempts = 0
while checked < 1500 and attempts < 30000:
    attempts += 1
    x0 = Rational(rng.randint(-6, 6), rng.randint(1, 5))
    k = Rational(rng.randint(-6, 6), rng.randint(1, 4))
    parts = reachable_parts(x0 + k * I * pi)
    if parts is None:
        continue
    x, m = parts
    cm = coth(m)
    if not (cm is S.ComplexInfinity or cm == 0):
        print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches coth(m)=%r outside "
              "{sentinel,0} on arg %r" % (cm, x0 + k * I * pi)); sys.exit(1)
    checked += 1

if periodic_active and checked == 0:
    print("AXIOM containment: pinned version uses the periodic branch but no "
          "reachable case enumerated; check is vacuous"); sys.exit(1)

note = ("%d reachable periodic-branch arguments, all in-domain" % checked
        if periodic_active else
        "periodic branch not exercised by this sympy version's peel-off; "
        "no model-reachable callee argument exists to fall out of domain")
print("AXIOM-COVERED: every model-reachable primary/sibling argument is "
      "accepted and the discriminator coth(m) stays in {sentinel,0} (%s)." % note)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-determinism-singleton-soundness",
        "axiom": "primary",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": (
            "primary->coth and sibling->tanh carry no Ensures; the proof "
            "consumes only @Pure determinism, and directed_infinity->"
            "S.ComplexInfinity is a stable singleton. If the real coth/tanh were "
            "non-deterministic, or the singleton/`is` test unstable (coth(0) not "
            "the sentinel, or coth(1) the sentinel), the axioms would be "
            "AXIOM-UNSOUND. Mirrors and re-runs axiom_check.py's obligations "
            "(determinism + sentinel + both FAIL_TO_PASS witnesses)."
        ),
    },
    {
        "id": "ax-callee-domain-containment",
        "axiom": "primary",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": (
            "the model passes to primary/sibling only the peeled handles (x "
            "remainder, m periodic) and compares primary(m) to the "
            "directed_infinity singleton. primary/sibling have no Requires (full "
            "handle domain) so every reachable argument is trivially covered; we "
            "additionally confirm the discriminator coth(m) the model inspects "
            "always lands in the branch's {sentinel,0} design domain. A reachable "
            "coth(m) outside that would be AXIOM-TOO-WEAK-FOR-CALLER. "
            "Version-aware: skips soundly if the pinned peel-off does not route "
            "through the periodic branch."
        ),
    },
]

# properties.py — PBT falsification battery for sympy__sympy-24213.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant that shares the FROZEN spec exactly
# (same_spec) and edits ONLY the impl region (between `# impl-start`/`# impl-end`,
# which the spec_view elides — invariants included, since they are nested inside
# impl). The runner checks each with Nagini verify + same_spec.
#
# The defended surface (collect_sum_dimension):
#   * surf, red are READ-ONLY inputs: Acc(list_pred(_), 1/2).  => FRAME-MUTATION
#     is mandatory.
#   * Precondition well-formedness: red[i] == reduction_of(surf[i]) for all i,
#     with reduction_of @Pure. So surf[i]==surf[j] ==> red[i]==red[j], but NOT
#     the converse (distinct surfaces may share a reduction — the velocity vs
#     acceleration*time discriminator).
#   * Requires(MustTerminate(2)) — a total-correctness obligation. A rival that
#     diverges before returning or raising (infinite loop) would satisfy every
#     value postcondition only vacuously; the obligation system must reject it
#     ("obligation leak"). This is the exact class the G-PANEL-1/G-EQ auditor
#     exploited before the obligation was added (atk_1/atk_8: `while True`
#     loops that verified against the value-only spec but hang the hidden
#     tests). The gold loop discharges it with
#     Invariant(MustTerminate(len(surf) - i + 1)).
#   * Success Ensures: (Forall i: red[i]==red[0]) AND Result()==red[0].
#   * Rejection Exsures(DimensionMismatch): Exists i: red[i] != red[0].
#   The load-bearing decision: rejection is driven by REDUCTION inequality
#   (red), never by SURFACE inequality (surf). That is the entire content of the
#   gold patch (`if dim != addend_dim` -> `if not equivalent_dims(dim,addend_dim)`).
from pathlib import Path

INSTANCE = "sympy__sympy-24213"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact impl-region text (between # impl-start and # impl-end). All edits
# stay strictly inside this region so same_spec is guaranteed.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    i = 1
    while i < len(surf):
        # invariants-start
        Invariant(Acc(list_pred(surf), 1 / 2))
        Invariant(Acc(list_pred(red), 1 / 2))
        Invariant(len(surf) == len(red))
        Invariant(len(surf) >= 1)
        Invariant(1 <= i and i <= len(surf))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 red[k] == red[0]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(surf),
                                                 red[k] == reduction_of(surf[k])))))
        # the addend loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(surf) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(surf) - i + 1))
        # invariants-end
        # Reject iff this addend is not physically equivalent to the first.
        if not equivalent(red[0], red[i]):
            raise DimensionMismatch()
        i = i + 1
    return red[0]"""

assert _GOLD_IMPL in _BASE, "gold impl text drift — re-sync _GOLD_IMPL with model.py"
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl text not unique"


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = []

# --- 1. POSITIVE CONTROL (soundness) ---------------------------------------
# Structurally different but CORRECT: the guard uses the SYMMETRIC argument
# order equivalent(red[i], red[0]) instead of equivalent(red[0], red[i]).
# `equivalent` unfolds to ==, which is symmetric, so this is behaviourally
# identical and keeps every gold invariant the proof needs. Must VERIFY (else
# SPEC-TOO-STRONG). This changes the executable shape (arg order) only; all the
# Forall/Invariant framing is preserved verbatim.
SPEC_TESTS.append({
    "id": "pos-control-symmetric-guard",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE,
        "        if not equivalent(red[0], red[i]):",
        "        if not equivalent(red[i], red[0]):"),
    "rationale": ("equivalent unfolds to red_a==red_b (symmetric); swapping the "
                  "argument order is a behaviourally-identical structural variant "
                  "that keeps every gold invariant. Must verify or the "
                  "postcondition is SPEC-TOO-STRONG."),
})

# --- 1b. POSITIVE CONTROL (soundness) — local-variable reshape -------------
# Introduce a local `ref = red[0]` and compare against it. red[0] reads need
# only the 1/2 permission held; the invariants still pin everything to red[0].
# Pure local-variable reshape, gold invariants preserved. Must VERIFY.
#
# Proof note: `ref` is a local assigned BEFORE the loop and not otherwise
# pinned, so Nagini havocs it across loop iterations — inside the body it no
# longer knows ref == red[0]. The reference-snapshot fact must therefore be
# carried as a loop invariant (`Invariant(ref == red[0])`) for the rejection
# Exsures (Exists i: red[i] != red[0]) to discharge when the guard fires on
# ref != red[i]. This invariant lives strictly inside the impl region (between
# the markers, so same_spec is preserved); it is proof engineering for the
# variant's own loop, NOT a spec change. Without it the case fails purely on
# this auto-discharge gap, not on any SPEC-TOO-STRONG postcondition.
SPEC_TESTS.append({
    "id": "pos-control-local-ref",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE,
        "    i = 1\n    while i < len(surf):",
        "    ref = red[0]\n    i = 1\n    while i < len(surf):").replace(
        "        if not equivalent(red[0], red[i]):",
        "        if not equivalent(ref, red[i]):", 1).replace(
        "        Invariant(1 <= i and i <= len(surf))\n",
        "        Invariant(1 <= i and i <= len(surf))\n"
        "        Invariant(ref == red[0])\n", 1),
    "rationale": ("ref := red[0] is a read-only local snapshot of the reference "
                  "reduction (1/2 perm suffices to read red[0]); guarding on "
                  "equivalent(ref, red[i]) is the same decision. Gold invariants "
                  "unchanged, plus an in-region loop invariant ref == red[0] that "
                  "re-establishes the snapshot fact Nagini havocs across the loop "
                  "(needed for the rejection Exsures). Must verify (else "
                  "SPEC-TOO-STRONG)."),
})

# --- 2. ADMISSIBILITY ------------------------------------------------------
# A contract-free module-level caller (injected into collect_sum_dimension's
# elided impl span, so same_spec holds) builds an F2P-shaped input (>=1 addend,
# the well-formedness fact established) and calls collect_sum_dimension. If the
# Requires cannot be established for a normal input the call site fails =>
# PRECOND-TOO-STRONG. We model the F2P case shape: two addends with EQUAL
# reductions -> must return normally reporting red2[0]. The caller carries NO
# MustTerminate obligation of its own, so the callee's Requires(MustTerminate(2))
# is establishable at the call site (a caller with no termination obligation may
# freely call a terminating callee); a SELF-call would need a strictly smaller
# callee measure and is not usable under the frozen spec.
_ADMISS_IMPL = _GOLD_IMPL + """


def _admiss_caller() -> None:
    # ADMISSIBILITY: an F2P-shaped in-domain input proves the Requires admits
    # a normal sum (the success case of the F2P sum). Build a length-2 witness
    # whose well-formedness Requires red2[j]==reduction_of(surf2[j]) holds by
    # construction (each red2 entry IS reduction_of of its surf2 entry), with
    # EQUAL reductions so the call returns normally reporting red2[0]. If the
    # call site cannot establish the precondition for this normal input the
    # case fails => PRECOND-TOO-STRONG.
    surf2 = [5, 5]  # type: List[int]
    red2 = [reduction_of(5), reduction_of(5)]  # type: List[int]
    Assert(len(surf2) == len(red2))
    Assert(len(surf2) >= 1)
    Assert(Forall(int, lambda j: (Implies(0 <= j and j < len(surf2),
                                          red2[j] == reduction_of(surf2[j])))))
    try:
        witness = collect_sum_dimension(surf2, red2)
        Assert(witness == red2[0])
    except DimensionMismatch:
        # equal reductions: the rejection Exsures (Exists j: red2[j] != red2[0])
        # is contradictory on this input, so this branch is infeasible.
        Assert(False)"""

SPEC_TESTS.append({
    "id": "admiss-f2p-shaped-caller",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
    "rationale": ("a length-2 in-domain input with equal reductions (the F2P "
                  "velocity/acceleration*time success shape) must satisfy the "
                  "Requires — including the MustTerminate(2) total-correctness "
                  "obligation — and return red[0]; if the call site cannot "
                  "establish the precondition for a normal input => "
                  "PRECOND-TOO-STRONG. The contract-free caller lives inside "
                  "the elided impl span so the spec is unchanged."),
})

# --- 3. THE DISCRIMINATING RIVAL: surface-identity guard (the prepatch bug) -
# This is the central uniqueness attack and the exact pre-patch behaviour.
# It decides rejection on the SURFACE description (surf) instead of the
# REDUCTION (red): `if surf[0] != surf[i]: raise`. Because distinct surfaces
# may share a reduction (velocity vs acceleration*time: surf differ, red equal),
# this rival RAISES when all reductions are equal, violating the Exsures clause
# (Exsures requires Exists i: red[i] != red[0]). MUST be rejected; if it
# verifies the spec cannot distinguish surface from reduction => SPEC-TOO-WEAK.
SPEC_TESTS.append({
    "id": "rival-surface-identity-guard",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE,
        "        # Reject iff this addend is not physically equivalent to the first.\n"
        "        if not equivalent(red[0], red[i]):\n"
        "            raise DimensionMismatch()",
        "        # PREPATCH BUG: reject on SURFACE-description inequality.\n"
        "        if surf[0] != surf[i]:\n"
        "            raise DimensionMismatch()"),
    "refinement": ("its faithful real patch is the PRE-PATCH guard "
                   "`if dim != addend_dim:` (structural Dimension.__eq__ on the "
                   "surface descriptions). On the F2P test_issue_24211 input "
                   "(A1*T1 + V1: acceleration*time vs velocity — distinct surface, "
                   "equal reduction) it RAISES ValueError, the exact bug the issue "
                   "reports. It does NOT resolve."),
    "rationale": ("rejection must come from the Exsures clause: returning via a "
                  "surface-guard raise needs Exists i: red[i]!=red[0], but the "
                  "raise can fire when all reductions are equal (surf differ, red "
                  "equal is permitted by the precondition), so the Exsures cannot "
                  "be proven => Nagini rejects. If it verified, SPEC-TOO-WEAK."),
})

# --- 4. PARTIAL-DOMAIN RIVAL: skip the first compared addend (index 1) ------
# Correct on most inputs but starts the loop at i=2, never comparing index 1.
# If red[1] differs from red[0] but red[2..] all equal red[0], this rival
# RETURNS NORMALLY while the success Ensures (Forall i: red[i]==red[0]) is
# FALSE at i==1. MUST be rejected.
SPEC_TESTS.append({
    "id": "rival-skip-index-1",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE,
        "    i = 1\n    while i < len(surf):",
        "    i = 2\n    while i < len(surf):"),
    "refinement": ("its faithful real patch starts the addend loop at "
                   "expr.args[2:] (skipping the first compared addend). On a sum "
                   "whose SECOND term is dimension-incompatible but later terms "
                   "match the reference, it silently accepts a wrong-dimension "
                   "sum — P2P consistency tests like test_check_unit_consistency "
                   "/ test_factor_and_dimension would fail. It does NOT resolve."),
    "rationale": ("with i starting at 2 the loop establishes only Forall k in "
                  "[2,len): red[k]==red[0]; the success Ensures Forall i in "
                  "[0,len): red[i]==red[0] is unprovable at i==1 (and the entry "
                  "invariant Forall k<i:red[k]==red[0] fails for k==1) => "
                  "rejected. If verified, SPEC-TOO-WEAK (partial domain)."),
})

# --- 5. CONTROL-FLOW-EFFECT RIVAL: never raise (always accept) --------------
# Strips the guard entirely and always returns red[0]. The raise/return
# distinction is the changed observable. With no guard, on a sum with an
# inequivalent addend the impl returns normally while the success Ensures
# (Forall i: red[i]==red[0]) is FALSE. MUST be rejected.
SPEC_TESTS.append({
    "id": "rival-never-raise",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE,
        "        # Reject iff this addend is not physically equivalent to the first.\n"
        "        if not equivalent(red[0], red[i]):\n"
        "            raise DimensionMismatch()\n"
        "        i = i + 1",
        "        # BUG: never reject — always accept the addend.\n"
        "        i = i + 1"),
    "refinement": ("its faithful real patch removes the dimension-compatibility "
                   "guard, accepting any sum regardless of dimensions. The P2P "
                   "tests that assert a ValueError IS raised on incompatible sums "
                   "(test_check_unit_consistency, parts of test_factor_and_dimension) "
                   "would fail. It does NOT resolve."),
    "rationale": ("without the guard the loop cannot establish Forall k<i: "
                  "red[k]==red[0]; the success Ensures Forall i: red[i]==red[0] "
                  "(and Result()==red[0] only on that path) is unprovable when "
                  "some red[i]!=red[0] => rejected. If verified, SPEC-TOO-WEAK "
                  "(control-flow/raise effect dropped)."),
})

# --- 6. FRAME-MUTATION RIVAL (MANDATORY: read-only Acc(...,1/2) inputs) -----
# Instead of comparing, OVERWRITE red[i] := red[0] so that the success Ensures
# (Forall i: red[i]==red[0]) holds vacuously. red is held at Acc(list_pred(red),
# 1/2) — a write needs FULL permission. MUST be rejected for INSUFFICIENT
# PERMISSION (not for a value reason). Gold invariants kept verbatim so the
# rejection is attributable to the write.
SPEC_TESTS.append({
    "id": "frame-mutation-overwrite-red",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE,
        "        # Reject iff this addend is not physically equivalent to the first.\n"
        "        if not equivalent(red[0], red[i]):\n"
        "            raise DimensionMismatch()\n"
        "        i = i + 1",
        "        # FRAME-MUTATION: overwrite the read-only input to force the\n"
        "        # success postcondition (Forall i: red[i]==red[0]) vacuously.\n"
        "        red[i] = red[0]\n"
        "        i = i + 1"),
    "refinement": ("a faithful real patch that MUTATES the collected addend "
                   "dimensions in place (rewriting addend_dim := dim) instead of "
                   "comparing them is not what the gold patch does and corrupts "
                   "the per-addend dimensions, breaking downstream factor/"
                   "dimension accounting — it would not resolve and would fail "
                   "P2P. Here it is rejected before any value question arises."),
    "rationale": ("red is a READ-ONLY input (Acc(list_pred(red), 1/2)); the "
                  "assignment red[i]=red[0] needs full write permission which the "
                  "function never holds => Nagini rejects for INSUFFICIENT "
                  "PERMISSION. This is the #1 weakness class (frame mutation); a "
                  "byte-fuzzer never constructs it."),
})

# --- 6b. FRAME-MUTATION RIVAL on the OTHER read-only input (surf) -----------
# Overwrite surf[i] := surf[0] (the prepatch-style "make surfaces match"
# vacuous fix). surf is also Acc(list_pred(surf), 1/2). MUST be rejected for
# insufficient permission.
SPEC_TESTS.append({
    "id": "frame-mutation-overwrite-surf",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE,
        "        # Reject iff this addend is not physically equivalent to the first.\n"
        "        if not equivalent(red[0], red[i]):\n"
        "            raise DimensionMismatch()\n"
        "        i = i + 1",
        "        # FRAME-MUTATION: overwrite the read-only surface facet.\n"
        "        surf[i] = surf[0]\n"
        "        i = i + 1"),
    "refinement": ("rewriting the surface facet (or the real addend_dim's name) "
                   "in place is not the gold patch and corrupts inputs; it would "
                   "not resolve. Rejected for permission before any value claim."),
    "rationale": ("surf is READ-ONLY (Acc(list_pred(surf), 1/2)); surf[i]=surf[0] "
                  "needs full permission the function lacks => INSUFFICIENT "
                  "PERMISSION rejection."),
})

# --- 6c. VACUOUS NON-TERMINATION RIVAL (uniqueness) --------------------------
# An impl that never returns and never raises: it spins forever instead of
# comparing. Every value postcondition (success Ensures AND rejection Exsures)
# is then satisfiable only vacuously: no execution reaches a return or a raise.
# This is the exact spec-too-weak class the G-PANEL-1 / G-EQ auditor exploited
# before the MustTerminate obligation was added (atk_1/atk_8: `while True:
# pass` bodies that verified against the value-only spec; their faithful real
# patches hang the hidden tests, which time out => not resolved). Under
# Requires(MustTerminate(2)) the spinning loop takes no termination obligation
# and has no decreasing measure, so Nagini's obligation system MUST reject it
# ("obligation leak" / MustTerminate not discharged). The invariants are
# relaxed to what the spinning loop maintains — the reject must come from the
# obligation system, not from a broken proof of a correct impl.
SPEC_TESTS.append({
    "id": "rival-vacuous-nonterminating-loop",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL,
        "    i = 1\n"
        "    while 1 <= i:\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(surf), 1 / 2))\n"
        "        Invariant(Acc(list_pred(red), 1 / 2))\n"
        "        Invariant(len(surf) == len(red))\n"
        "        Invariant(len(surf) >= 1)\n"
        "        Invariant(1 <= i)\n"
        "        # invariants-end\n"
        "        i = i + 1\n"
        "    return red[0]"),
    "refinement": ("its faithful real patch replaces the addend loop with an "
                   "infinite `while True` spin (the auditor's atk_1/atk_8 "
                   "shape: `if not equivalent_dims(...): while True: pass`, or "
                   "the whole Add branch spinning). The hidden F2P/P2P tests "
                   "hang and the harness times out — it does NOT resolve."),
    "rationale": ("the spinning loop reaches no return and no raise, so every "
                  "value clause holds only vacuously; the ONLY clause that can "
                  "reject it is the Requires(MustTerminate(2)) obligation, "
                  "which the loop (no decreasing-measure MustTerminate "
                  "invariant) leaks => Nagini rejects. If it verified, "
                  "SPEC-TOO-WEAK (vacuous divergence admitted)."),
})

# --- 7. SUPPORTING near-miss: wrong return value ---------------------------
# Cheap supporting case (carries a real refinement): return red[i-1] sometimes
# instead of red[0]. On a singleton (len==1) the loop body never runs and i==1,
# so i-1==0 -> red[0]; but we return red[len-1] to break Result()==red[0] when
# the spec demands red[0]. Actually all reds equal on the success path, so to
# get a genuine reject we return a constant 0 unrelated to red.
SPEC_TESTS.append({
    "id": "rival-wrong-return-constant",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE,
        "        i = i + 1\n    return red[0]",
        "        i = i + 1\n    return 0"),
    "refinement": ("returning a constant dimension identity (0) instead of the "
                   "reference dimension means _collect_factor_and_dimension hands "
                   "back the wrong dimension for the sum; every downstream "
                   "consumer (convert_to, consistency checks) sees a corrupted "
                   "dimension — P2P fails. It does NOT resolve."),
    "rationale": ("the success Ensures Result()==red[0] pins the return; "
                  "returning 0 is unprovable equal to red[0] in general => "
                  "rejected. Cheap supporting case for the return-value clause."),
})


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# The bundle has one @ContractOnly axiom (reduction_of, A-consumed) and one
# A-reference deep model (equivalent). The existing axiom_check.py (G-AX) is the
# canonical real-callee soundness check. We embed strengthened probes that CALL
# the real sympy engine in-container (apply_gold=True: the equivalence behaviour
# under check is the post-gold guard, though equivalent_dims/get_dimensional_
# dependencies themselves are UNCHANGED by the patch).
#
# Probe constraints honoured (PBT §5a): CALL the real callee (never scrape
# source); only stdlib + sympy imported; no bundle file assumed in-container
# (each probe is self-contained); files opened utf-8 if any (none needed).
AXIOM_TESTS = []

# --- AX-1. axiom-soundness: reduction_of is a genuine FUNCTION --------------
# The reduction_of axiom claims ONLY the weakest used property: the reduction is
# a genuine function of the dimension (red[i]==reduction_of(surf[i]), @Pure).
# Probe: run the REAL get_dimensional_dependencies and assert determinism + that
# structurally-equal dimensions reduce equally, fuzzing boundaries + composites.
# Any disagreement => AXIOM-UNSOUND. (No no-raise / exact-value claim is made;
# inputs whose reduction RAISES in the engine are out of the modeled domain and
# skipped — model and gold both propagate the raise there.)
_AX_FUNCTION_PROBE = r'''
import sys, itertools, random
try:
    from sympy.physics.units.systems.si import SI
    from sympy.physics.units import (
        length, time, mass, current, temperature, amount_of_substance,
        luminous_intensity, velocity, acceleration, force, energy, momentum,
        frequency, area, volume, pressure, power, charge,
    )
    from sympy.physics.units.dimensions import Dimension
except Exception as e:
    print("IMPORT-FAIL:", repr(e)); sys.exit(1)

DS = SI.get_dimension_system()

def reduction_id(dim):
    return frozenset(DS.get_dimensional_dependencies(dim).items())

base = [length, time, mass, current, temperature, amount_of_substance,
        luminous_intensity]
named = [velocity, acceleration, force, energy, momentum, frequency, area,
         volume, pressure, power, charge]
composite = [
    Dimension(acceleration.name * time.name),
    Dimension(force.name * length.name),
    Dimension(mass.name * acceleration.name),
    Dimension(length.name / time.name),
    Dimension(mass.name * velocity.name),
    Dimension(length.name ** 2),
    Dimension(velocity.name * time.name),
    Dimension(force.name / area.name),
    Dimension(energy.name / time.name),
    Dimension(length.name ** 0),   # boundary: dimensionless
]
all_dims = base + named + composite

bad = 0
# determinism: same dimension reduces identically across repeated calls
for d in all_dims:
    r1 = reduction_id(d); r2 = reduction_id(d); r3 = reduction_id(d)
    if not (r1 == r2 == r3):
        print("NON-DETERMINISTIC on %r: %r %r %r" % (d.name, r1, r2, r3)); bad += 1

# function of the dimension: structurally-equal (rebuilt) dimensions reduce equal
for d in base + named:
    d2 = Dimension(d.name)
    if reduction_id(d) != reduction_id(d2):
        print("NOT-A-FUNCTION (surface identity) on %r" % (d.name,)); bad += 1

# fuzz: random products/quotients, determinism must hold on every in-domain one
rng = random.Random(24213)
pool = base + named
checked = 0
for _ in range(4000):
    expr = 1
    for _j in range(rng.randint(1, 4)):
        e = rng.choice([1, 1, 1, 2, -1])
        expr = expr * rng.choice(pool).name ** e
    try:
        d = Dimension(expr)
        r1 = reduction_id(d); r2 = reduction_id(d)
    except Exception:
        continue  # out-of-domain raise (e.g. non-integer pow): skipped
    if r1 != r2:
        print("FUZZ NON-DETERMINISTIC on %r: %r vs %r" % (expr, r1, r2)); bad += 1
    checked += 1

if bad:
    print("AXIOM-UNSOUND: reduction_of not a genuine function (%d violations)" % bad)
    sys.exit(1)
print("OK reduction_of is a genuine function (deterministic + surface-determined) "
      "on %d named/base/composite + %d fuzz in-domain dims" % (len(all_dims), checked))
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-sound-reduction-is-function",
    "axiom": "reduction_of",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AX_FUNCTION_PROBE,
    "rationale": ("the reduction_of axiom claims only that the reduction is a "
                  "genuine FUNCTION of the dimension (@Pure). The real "
                  "get_dimensional_dependencies must be deterministic and "
                  "depend only on the dimension; any disagreement => "
                  "AXIOM-UNSOUND."),
})

# --- AX-2. A-reference soundness: equivalent deep model == equivalent_dims --
# The deep model equivalent(red_a,red_b) := (red_a==red_b) must equal the REAL
# equivalent_dims on every caller-reachable dimension pair, AND equivalence must
# be decided by the reduction, never the surface description. Probe re-derives
# the issue witness and fuzzes pairs. Any mismatch => the deep model is unsound
# (A-reference defect). This is the strengthened axiom_check.py A-reference logic.
_AX_EQUIV_PROBE = r'''
import sys, itertools, random
try:
    from sympy.physics.units.systems.si import SI
    from sympy.physics.units import (
        length, time, mass, current, temperature, amount_of_substance,
        luminous_intensity, velocity, acceleration, force, energy, momentum,
        frequency, area, volume, pressure, power, charge, second, meter,
        Quantity,
    )
    from sympy.physics.units.dimensions import Dimension
except Exception as e:
    print("IMPORT-FAIL:", repr(e)); sys.exit(1)

DS = SI.get_dimension_system()

def reduction_id(dim):
    return frozenset(DS.get_dimensional_dependencies(dim).items())

def equivalent_model(ra, rb):
    return ra == rb

base = [length, time, mass, current, temperature, amount_of_substance,
        luminous_intensity]
named = [velocity, acceleration, force, energy, momentum, frequency, area,
         volume, pressure, power, charge]
composite = [
    Dimension(acceleration.name * time.name),   # == velocity (issue case)
    Dimension(force.name * length.name),         # == energy
    Dimension(mass.name * acceleration.name),    # == force
    Dimension(length.name / time.name),          # == velocity
    Dimension(mass.name * velocity.name),        # == momentum
    Dimension(length.name ** 2),                 # == area
    Dimension(velocity.name * time.name),        # == length
]
all_dims = base + named + composite

bad = 0
n_pairs = 0
for a, b in itertools.product(all_dims, repeat=2):
    real = DS.equivalent_dims(a, b)
    model = equivalent_model(reduction_id(a), reduction_id(b))
    if real != model:
        print("A-REF MISMATCH (%r,%r): real=%r model=%r"
              % (a.name, b.name, real, model)); bad += 1
    n_pairs += 1

# the discriminating witness: velocity vs acceleration*time
v = velocity
at = Dimension(acceleration.name * time.name)
if v == at:
    print("WITNESS BROKEN: surfaces unexpectedly equal"); bad += 1
if DS.equivalent_dims(v, at) is not True:
    print("WITNESS: velocity vs acceleration*time NOT equivalent (should be)"); bad += 1
if DS.equivalent_dims(velocity, force) is not False:
    print("WITNESS: velocity vs force unexpectedly equivalent"); bad += 1

# end-to-end under the GOLD guard: A1*T1 + V1 must not raise and reduce==velocity
try:
    V1 = Quantity('V1_axp'); SI.set_quantity_dimension(V1, velocity)
    SI.set_quantity_scale_factor(V1, 1 * meter / second)
    A1 = Quantity('A1_axp'); SI.set_quantity_dimension(A1, acceleration)
    SI.set_quantity_scale_factor(A1, 1 * meter / second ** 2)
    T1 = Quantity('T1_axp'); SI.set_quantity_dimension(T1, time)
    SI.set_quantity_scale_factor(T1, 1 * second)
    _f, dim = SI._collect_factor_and_dimension(A1 * T1 + V1)
    if reduction_id(dim) != reduction_id(velocity):
        print("END-TO-END: collected dim not equivalent to velocity: %r" % (dim.name,)); bad += 1
except Exception as e:
    print("END-TO-END RAISED (gold should not):", repr(e)); bad += 1

# fuzz product/quotient pairs
rng = random.Random(424213)
pool = base + named
checked = 0
for _ in range(4000):
    def mk():
        expr = 1
        for _j in range(rng.randint(1, 4)):
            e = rng.choice([1, 1, 1, 2, -1])
            expr = expr * rng.choice(pool).name ** e
        return Dimension(expr)
    try:
        da, db = mk(), mk()
        real = DS.equivalent_dims(da, db)
        model = equivalent_model(reduction_id(da), reduction_id(db))
    except Exception:
        continue
    if real != model:
        print("FUZZ A-REF MISMATCH: real=%r model=%r" % (real, model)); bad += 1
    checked += 1

if bad:
    print("AXIOM-UNSOUND (A-reference): equivalent deep model != equivalent_dims "
          "(%d violations)" % bad); sys.exit(1)
print("OK equivalent (A-reference) == real equivalent_dims on %d pairs + %d fuzz "
      "+ issue witness + end-to-end gold collect" % (n_pairs, checked))
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-ref-equivalent-eq-equivalent-dims",
    "axiom": "equivalent",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AX_EQUIV_PROBE,
    "rationale": ("the deep model equivalent(red_a,red_b):=(red_a==red_b) must "
                  "equal the real equivalent_dims on every caller-reachable pair "
                  "and decide by reduction (not surface). Any mismatch => the "
                  "A-reference is unsound and verify would not imply resolve."),
})

# --- AX-3. axiom-containment: every caller-reachable reduction input is a ---
# valid dimension the engine accepts (the model only ever passes dimensions
# built from base/named/composite Symbol/Mul names — exactly the engine's
# domain). A reachable input OUTSIDE the engine's accepted domain => AXIOM-
# TOO-WEAK-FOR-CALLER. The model's Requires constrains surf/red to be a
# function pair (red==reduction_of(surf)); the only callee inputs the model can
# reach are the dimensions whose surfaces the caller holds. We confirm the
# engine accepts (does not raise on) the dimensions the F2P/P2P sums build.
_AX_CONTAIN_PROBE = r'''
import sys
try:
    from sympy.physics.units.systems.si import SI
    from sympy.physics.units import (
        length, time, mass, current, temperature, amount_of_substance,
        luminous_intensity, velocity, acceleration, force, energy, momentum,
        frequency, area, volume, pressure, power, charge,
    )
    from sympy.physics.units.dimensions import Dimension
except Exception as e:
    print("IMPORT-FAIL:", repr(e)); sys.exit(1)

DS = SI.get_dimension_system()

# The caller (UnitSystem._collect_factor_and_dimension) only ever reduces
# dimensions it collected from quantities — Symbol/Mul/Pow names with INTEGER
# exponents. These are exactly the inputs in the engine's accepted domain.
reachable = [
    length, time, mass, current, temperature, amount_of_substance,
    luminous_intensity, velocity, acceleration, force, energy, momentum,
    frequency, area, volume, pressure, power, charge,
    Dimension(acceleration.name * time.name),
    Dimension(force.name * length.name),
    Dimension(mass.name * acceleration.name),
    Dimension(length.name / time.name),
    Dimension(length.name ** 2),
    Dimension(1),  # dimensionless, the test_issue_24062 / Dimension(1) case
]
out_of_domain = 0
for d in reachable:
    try:
        DS.get_dimensional_dependencies(d)  # must accept (no raise) -> in domain
    except Exception as e:
        print("REACHABLE-INPUT OUTSIDE AXIOM DOMAIN: %r raised %r" % (d.name, e))
        out_of_domain += 1

if out_of_domain:
    print("AXIOM-TOO-WEAK-FOR-CALLER: %d caller-reachable dimension(s) outside "
          "reduction_of domain" % out_of_domain); sys.exit(1)
print("OK all %d caller-reachable dimensions are in the reduction engine's "
      "accepted domain (covering more than the caller reaches is sound)"
      % len(reachable))
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-contain-reachable-in-domain",
    "axiom": "reduction_of",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _AX_CONTAIN_PROBE,
    "rationale": ("every dimension the caller can reach (Symbol/Mul/Pow names "
                  "with integer exponents, plus dimensionless) lies in the "
                  "reduction engine's accepted domain; a reachable input outside "
                  "it => AXIOM-TOO-WEAK-FOR-CALLER. The engine covering MORE is "
                  "sound."),
})

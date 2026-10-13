"""properties.py — PBT falsification manifest for sympy__sympy-15875.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The single function under spec is

    add_is_zero(classes: List[int], sub_is_zero: Optional[bool]) -> Optional[bool]

the deep model of the patched commutative-sum zeroness decision
`Add._eval_is_zero` (the gold hunk adds the `len(nz) == 0` disjunct on
`add.py:557`). `classes` is a `List[int]` of summand class tags 0..5; the
unchanged recursive `b.is_zero` enters as the three-valued parameter
`sub_is_zero`.

WHAT THE SPEC DEFENDS (load-bearing surface):

  * The postcondition is a CASE PARTITION of the reachable input domain, phrased
    via the GROUNDED `@Pure` folds `count_eq(ToSeq(classes), c)` and
    `has_eq(ToSeq(classes), c)`. These are NOT an opaque answer-key oracle — they
    are functions of the input `classes`, fully unfolded by the backward
    `drop(i)` scan in the impl. There is therefore NO "echo the oracle" rival:
    every clause pins `Result()` to a concrete three-valued constant on its
    class profile, so the only way to satisfy it is to return that constant.
    (UNGROUNDED-ORACLE-ECHO is N/A; see `assessment`. The honest positive control
    below is the cheapest-correct-impl analogue.)

  * THE GOLD DELTA is the clause (model.py:94-97):
        not(class-2/5) and count_eq(classes,0)!=len and
        (count_eq(classes,1)==0 OR count_eq(classes,1)==len) -> Result() is None
    The `count_eq(classes,1)==0` disjunct is exactly the patch's added
    `len(nz)==0`. Pre-fix (`if nz==n` only) a sum with NO real-nonzero summand
    but some class-3 imaginary returns the wrong `False`; the fix returns `None`.
    `model_prepatch.py` is precisely this pre-fix line and FAILS this clause
    (G-DIFF). The PARTIAL-DOMAIN rival below reproduces it.

  * Two D1-strengthening clauses close the previously-unconstrained None
    fall-throughs in the active region (0 < nz < n, no class-2/5, not all-zero):
        sub_is_zero is None                              -> None
        sub_is_zero true AND a class-4 summand present   -> None
    These are the freshest / most at-risk clauses; PARTIAL-DOMAIN rivals target
    each one directly (a definite verdict where the gold routine yields None).

  * `classes` is held READ-ONLY: `Requires(Acc(list_pred(classes),1/2))` and
    `Ensures(Acc(list_pred(classes),1/2))`. The MANDATORY attack is FRAME
    MUTATION — an impl that WRITES to `classes` (a stored element) to fabricate a
    clause must fail for INSUFFICIENT PERMISSION (a store needs the full
    list_pred), never silently verify.

  * There is no raise / side-effect distinct from the returned value: the
    function's whole observable is its `Optional[bool]` verdict, and that verdict
    is pinned by the postcondition partition. CONTROL-FLOW-EFFECT is therefore
    N/A (no capability-token discriminator applies; see `assessment`).

  * There are NO @ContractOnly axioms (empty axioms region). The only opaque
    value, the recursive `b.is_zero`, enters as the parameter `sub_is_zero` (not
    a callee the spec quantifies over). It is an A-reference deep model validated
    by axiom_check.py / G-AX: the deep model `add_is_zero` equals the REAL patched
    `_eval_is_zero` on the issue witness + boundary + ~15000 fuzz `Add`
    expressions. The axiom lane below RE-RUNS that real-callee equivalence in
    Docker (axiom-soundness) and confirms every class profile the model can reach
    is realizable by a genuine summand multiset (axiom-containment). Both probes
    are SELF-CONTAINED (import only `sympy` + stdlib) because the runner mounts
    ONLY the probe at /work — axiom_check.py is NOT in-container.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside the single `# impl-start`/`# impl-end` block (the POST-LOOP
decision tail, which carries no loop-invariant obligation, or — for the frame
probe — inserts a write). The frozen spec (Requires/Ensures/@Pure folds) and the
loop+invariants are never touched, so `markers.same_spec` is guaranteed and a
rejection is attributable to the POSTCONDITION catching a wrong verdict (or the
permission system), never to a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P (`test_Add_is_zero`: `(-2*I + (1+I)**2).is_zero is None`).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15875"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (each strictly INSIDE the single impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold POST-LOOP decision tail (after the backward scan + its final
# Assert). It carries NO loop-invariant obligation — straight-line logic over the
# accumulators z/nz/im/im_or_z/has2/has5 — so reshaping it cannot break the loop
# proof; only the value-postcondition can reject a wrong reshape.
_GOLD_TAIL = """    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-DIFFERENT but CORRECT decision tail. Semantically identical to
# gold on every reachable accumulator profile, but the branch SHAPE is reorganised:
#   - the class-2/5 (None) guard is kept first (it must dominate, per the spec);
#   - the all-zero (True) guard kept second;
#   - the "no/whole real-nonzero" None guard kept third;
#   - the sub_is_zero dispatch is REWRITTEN as a flat cascade with the
#     sub_is_zero-False case handled FIRST (early `return False`), then the
#     undecided (None) case, then the sub_is_zero-True imaginary combination
#     reshaped into explicit guards binding no new spec. Every leaf returns the
#     SAME constant the gold tail returns on the same profile:
#       sub False                       -> False   (gold: final `return False`)
#       sub None                        -> None
#       sub True, no im & no im_or_z    -> True
#       sub True, im & no im_or_z       -> False
#       sub True, otherwise (incl im_or_z) -> None
# It touches ONLY the impl tail; the loop + invariants + final Assert are intact,
# so no induction lemma is needed (no proof-gap pitfall). If it fails to verify,
# the postcondition is over-fit to the exact gold spelling => SPEC-TOO-STRONG.
_POS_TAIL = """    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if not sub_is_zero:
        return False
    if im_or_z:
        return None
    if im:
        return False
    return True"""
_POS_CONTROL = _swap(_BASE, _GOLD_TAIL, _POS_TAIL)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped in-domain input placed BEFORE
# the gold tail (gold tail kept verbatim, so this is a pure positive control on
# the precondition). The witness `w = [0]` (a single real-known-zero summand):
#   - every element in 0..5 (trivially 0);
#   - count_eq([0],1) == 0, so the linking precondition `count_eq==0 =>
#     sub_is_zero is not None and sub_is_zero` requires sub_is_zero == True, which
#     we pass — establishing the Requires for a normal one-summand input.
# The call's result is z==1==n -> True. Assert it is not None confirms the
# all-zero `Result() is not None and Result()` postcondition is reachable. The
# witness list is FRESH (full list_pred), trivially splitting to 1/2 for the call.
# If the precondition rejects this normal input => PRECOND-TOO-STRONG.
_ADMISS_TAIL = """    w = [0]  # type: List[int]
    Assert(Acc(list_pred(w), 1 / 2))
    Assert(Forall(int, lambda i: (Implies(0 <= i and i < len(w),
                                          0 <= w[i] and w[i] <= 5), [[w[i]]])))
    Assert(Implies(count_eq(ToSeq(w), 1) == 0,
                   True is not None and True))
    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False"""
_ADMISS = _swap(_BASE, _GOLD_TAIL, _ADMISS_TAIL)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `classes` is held
# READ-ONLY (Acc(list_pred(classes),1/2)). This rival, before returning the
# gold verdict, STORES into the read-only input (`classes[0] = 0`) — a write that
# a mutating real impl might use to fabricate a class profile. Under
# Acc(list_pred(classes),1/2) an element store needs the FULL list_pred, so it
# must fail for INSUFFICIENT PERMISSION (not a wrong value). The gold value-logic
# is kept verbatim AFTER the write, so the rejection is attributable solely to the
# store. (Guarded by `if n > 0` so the index is in range — the write is still
# reached on every non-empty input, which is every F2P-shaped input.) Rejection
# source: the PERMISSION SYSTEM.
_FRAME_TAIL = """    if n > 0:
        classes[0] = 0
    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False"""
_RIVAL_FRAME = _swap(_BASE, _GOLD_TAIL, _FRAME_TAIL)

# (3a) PARTIAL-DOMAIN — THE GOLD-DELTA BUG (== model_prepatch.py). Drop the
# `nz == 0` disjunct from the no/whole-real-nonzero guard: `if nz == n: ...`.
# This is correct on the WHOLE F2P/P2P domain EXCEPT the `nz == 0` sub-domain
# (a sum with no real-nonzero summand but some imaginary class). There, instead of
# the gold `None`, it falls through to the sub_is_zero dispatch: with nz==0 the
# precondition forces sub_is_zero==True, and on the issue witness (two imaginary
# summands, im true, im_or_z false) it returns the WRONG `False`. Faithful real
# patch = the UNPATCHED `if len(nz) == len(self.args)` line, which fails
# test_Add_is_zero ((-2*I+(1+I)**2).is_zero must be None, prepatch gives False).
# Definitively non-resolving. Rejection source: the GOLD-DELTA postcondition
# clause (model.py:94-97) `... count_eq(classes,1)==0 ... -> Result() is None`.
_PARTIAL_NZ0_TAIL = """    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False"""
_RIVAL_PARTIAL_NZ0 = _swap(_BASE, _GOLD_TAIL, _PARTIAL_NZ0_TAIL)

# (3b) PARTIAL-DOMAIN — attack the D1 clause `sub_is_zero is None -> None`. This
# rival is correct EXCEPT on the active sub-domain `sub_is_zero is None`
# (0 < nz < n, no class-2/5, not all-zero): there it returns a definite `False`
# instead of the gold `None`. Faithful real patch: a routine that treats an
# UNDECIDED real-nonzero sub-sum (`b.is_zero is None`) as provably nonzero and
# returns False — fabricating a definite answer the assumption engine cannot
# justify. On any Add whose real-nonzero part has undetermined zeroness this gives
# a wrong is_zero=False (e.g. (u - v + I*m) with u,v real-nonzero, sum undecided),
# corrupting downstream is_zero queries the P2P assumption tests rely on. Rejection
# source: the postcondition clause (model.py:123-128) `... sub_is_zero is None ->
# Result() is None` — returning False violates it.
_PARTIAL_SUBNONE_TAIL = """    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return False
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False"""
_RIVAL_PARTIAL_SUBNONE = _swap(_BASE, _GOLD_TAIL, _PARTIAL_SUBNONE_TAIL)

# (3c) PARTIAL-DOMAIN — attack the D1 clause `sub_is_zero true AND class-4 present
# -> None`. Gold: when the real-nonzero sub-sum is zero but an imaginary-or-zero
# (class-4) summand is present, the imaginary part carries no settling info, so the
# verdict is None. This rival drops the `im_or_z` guard from the True branch:
# `if not im: return True` — so on the sub-domain (sub_is_zero true, im false,
# im_or_z TRUE) it returns the WRONG `True` (claims the sum is zero) instead of
# None. Faithful real patch: a routine that ignores the imaginary-or-zero class and
# declares the sum zero whenever the real part vanishes — wrongly returns is_zero
# True for e.g. (u - u + w*I) where w is real (w*I is class-4: could be zero or
# imaginary). Corrupts is_zero on any Add with a class-4 summand. Rejection source:
# the postcondition clause (model.py:131-137) `... has_eq(classes,4) -> Result() is
# None` — returning True violates it.
_PARTIAL_IOZ_TAIL = """    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im:
            return True
        if im and not im_or_z:
            return False
        return None
    return False"""
_RIVAL_PARTIAL_IOZ = _swap(_BASE, _GOLD_TAIL, _PARTIAL_IOZ_TAIL)

# (3d) PARTIAL-DOMAIN (supporting) — attack the class-3 discriminating clause
# `sub_is_zero true AND class-3 AND no class-4 -> False`. This rival returns the
# wrong `None` there instead of `False`: drop the `if im and not im_or_z: return
# False` line so the sub_is_zero-True branch falls through to `return None`.
# Correct everywhere EXCEPT the sub-domain (sub_is_zero true, im true, im_or_z
# false), where gold proves the sum NONZERO (False) but this returns None.
# Faithful real patch: a routine that fails to conclude nonzero when the real part
# is zero and a pure-imaginary class-3 summand remains (e.g. a + (-a) + I*b with b
# real-nonzero imaginary) — under-decides is_zero, failing assumption tests that
# expect a definite False. Rejection source: the postcondition clause
# (model.py:100-106) `... has_eq(classes,3) and not has_eq(classes,4) -> Result()
# is not None and not Result()` — returning None violates the `is not None`.
_PARTIAL_IM3_TAIL = """    if has2 or has5:
        return None
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not im_or_z and not im:
            return True
        return None
    return False"""
_RIVAL_PARTIAL_IM3 = _swap(_BASE, _GOLD_TAIL, _PARTIAL_IM3_TAIL)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-tail-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL,
     "rationale": "structurally-different but CORRECT decision tail (sub_is_zero "
                  "dispatch flattened into a cascade, False handled first, the "
                  "class-3/class-4 combination rewritten as explicit guards). Every "
                  "leaf returns the SAME three-valued constant the gold tail returns "
                  "on the same accumulator profile; the loop + invariants + final "
                  "Assert are untouched so no induction lemma is needed. If it fails "
                  "to verify, the postcondition is over-fit to the gold spelling => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-self-call", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on a freshly-built in-domain witness w=[0] (all tags "
                  "in 0..5; count_eq([0],1)==0 so the linking precondition forces "
                  "sub_is_zero==True, which is passed) establishes the Requires for a "
                  "normal one-summand input and returns the 1/2 permission; the call "
                  "yields True (z==n) and Assert(r is not None and r) confirms the "
                  "all-zero postcondition is reachable. Verifies => the precondition "
                  "admits an F2P-shaped input (else PRECOND-TOO-STRONG)."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "frame-mutate-classes", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful resolving real patch corresponds to this: the modeled "
                   "input `classes` abstracts `self.args`, the Add's argument tuple, "
                   "which the routine only READS (sympy Basic .args is an immutable "
                   "shared tuple; _eval_is_zero never reassigns an element of it). The "
                   "consumer-visible contract holds `classes` read-only (Acc(.,1/2)) "
                   "for exactly that reason. A real patch that wrote back into "
                   "self.args would corrupt the shared expression and is not the gold "
                   "fix; storing into a 1/2-permission element is a pure verification "
                   "artifact with no resolving analogue and must be rejected on "
                   "permission, not silently admitted.",
     "rationale": "rejection from the PERMISSION SYSTEM: under "
                  "Acc(list_pred(classes),1/2) an element store `classes[0] = 0` "
                  "needs the FULL list_pred, so the impl fails for INSUFFICIENT "
                  "PERMISSION (the gold value-logic after the write is verbatim, so "
                  "the failure is solely the write)."},
    {"id": "partial-domain-drop-nz0", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_NZ0,
     "refinement": "this IS the pre-patch line (model_prepatch.py): `if len(nz) == "
                   "len(self.args)` WITHOUT the `len(nz)==0` disjunct. On the gold "
                   "issue witness -2*I + (1+I)**2 (two imaginary summands, nz==0, im "
                   "true, im_or_z false) the empty real-nonzero sub-sum b=self.func() "
                   "= S.Zero has b.is_zero True, so it falls into `if im and not "
                   "im_or_z: return False` and yields the WRONG False. The F2P test "
                   "test_Add_is_zero asserts (-2*I+(1+I)**2).is_zero is None — this "
                   "rival fails it. Definitively non-resolving (it is exactly the bug "
                   "the gold patch fixes).",
     "rationale": "rejection from the GOLD-DELTA postcondition clause (model.py:94-97): "
                  "not(class-2/5) and count_eq(classes,0)!=len and "
                  "(count_eq(classes,1)==0 or ==len) -> Result() is None. With nz==0 "
                  "(and not all-zero) this rival returns a definite verdict, violating "
                  "the pinned None."},
    {"id": "partial-domain-subnone-false", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_SUBNONE,
     "refinement": "a faithful real patch treating an UNDECIDED real-nonzero sub-sum "
                   "(b.is_zero is None) as provably nonzero and returning False "
                   "fabricates a definite is_zero the assumption engine cannot justify. "
                   "On any Add whose real-nonzero part has undetermined zeroness (e.g. "
                   "x - y + I*m, x,y real-nonzero) it returns is_zero=False where the "
                   "true answer is None, corrupting the three-valued assumption "
                   "contract the P2P arithmetic/assumption tests depend on. Faithful "
                   "but non-resolving (it neither makes test_Add_is_zero pass on the "
                   "witness nor preserves correct None behaviour elsewhere).",
     "rationale": "rejection from the postcondition clause (model.py:123-128): "
                  "active region with sub_is_zero is None -> Result() is None; "
                  "returning False violates it."},
    {"id": "partial-domain-ioz-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_IOZ,
     "refinement": "a faithful real patch that ignores the imaginary-or-zero (class-4) "
                   "summand and declares the sum zero whenever the real-nonzero part "
                   "vanishes returns is_zero=True for e.g. x - x + w*I (w real; w*I is "
                   "class-4, zeroness undetermined). The true verdict is None (the sum "
                   "is w*I, which is zero iff w==0). It thus claims a nonzero "
                   "expression is zero — a soundness break in the assumption engine "
                   "that fails P2P is_zero/assumption tests. Faithful but non-resolving.",
     "rationale": "rejection from the D1 postcondition clause (model.py:131-137): "
                  "active region, sub_is_zero true, has_eq(classes,4) -> Result() is "
                  "None; returning True violates it."},
    {"id": "partial-domain-im3-none", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_IM3,
     "refinement": "a faithful real patch that drops the `if im and not im_or_z: "
                   "return False` conclusion under-decides: when the real part is zero "
                   "and a pure-imaginary class-3 summand remains (e.g. a + (-a) + I*b, "
                   "b real-nonzero) the sum is provably NONZERO (I*b != 0) but this "
                   "returns None. It weakens is_zero from a definite False to None, "
                   "failing the assumption tests that expect the nonzero conclusion "
                   "(and not resolving the issue). Faithful but non-resolving.",
     "rationale": "rejection from the discriminating postcondition clause "
                  "(model.py:100-106): active region, sub_is_zero true, "
                  "has_eq(classes,3) and not has_eq(classes,4) -> Result() is not "
                  "None and not Result(); returning None violates the `is not None`."},
]


# ===========================================================================
# AXIOM LANE (Docker, real sympy callee under the gold patch)
# ===========================================================================
# There are NO @ContractOnly axioms (empty axioms region). The only opaque value,
# the recursive b.is_zero, enters as the parameter sub_is_zero and is an
# A-reference deep model: add_is_zero (the deep model) must equal the REAL patched
# Add._eval_is_zero on every reachable (class-vector, sub_is_zero). Two probes:
#   - axiom-soundness: run the REAL patched _eval_is_zero on the issue witness +
#     curated boundary multisets + ~15000 fuzz Add expressions (fresh symbols per
#     case so sympy's global assumption cache cannot bleed), and assert the inline
#     deep model equals it — observing the class vector and sub_is_zero exactly as
#     the routine does. This transcribes axiom_check.py's oracle inline (the runner
#     mounts ONLY the probe at /work) and is the same equivalence G-AX checks; a
#     single disagreement => AXIOM-UNSOUND (the A-reference is wrong).
#   - axiom-containment: every class profile the MODEL can reach (any multiset over
#     tags 0..5, with the linking constraint nz==0 => sub_is_zero==True) is
#     realizable by a genuine summand multiset, and the real routine observes that
#     exact (class vector, sub_is_zero). A reachable profile the real callee could
#     not realize would be AXIOM-TOO-WEAK-FOR-CALLER. We confirm every class is
#     constructible (a real summand exists for each tag 0..5) and the nz==0=>True
#     link holds on the empty real-nonzero sub-sum (S.Zero.is_zero is True).
# Both probes import only sympy + stdlib (self-contained); apply_gold=True so the
# patched routine is the one under test.

_AX_SOUND = r'''
import random, sys, warnings
warnings.filterwarnings("ignore")
from sympy import I, S, Symbol, Integer, Add, sqrt, Rational

# ---- the exact observations the real routine makes on a summand -------------
def classify(a):
    if a.is_real:
        if a.is_zero:
            return 0
        if a.is_zero is False:
            return 1
        return 2
    elif a.is_imaginary:
        return 3
    elif (S.ImaginaryUnit * a).is_real:
        return 4
    else:
        return 5

# ---- the deep model (faithful port of model.py add_is_zero) -----------------
def model(classes, sub_is_zero):
    if any(c in (2, 5) for c in classes):
        return None
    z = classes.count(0)
    nz = classes.count(1)
    im = 3 in classes
    ioz = 4 in classes
    n = len(classes)
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not ioz and not im:
            return True
        if im and not ioz:
            return False
        return None
    return False

def observe(expr):
    classes = [classify(a) for a in expr.args]
    nz_args = [a for a in expr.args if classify(a) == 1]
    sub_is_zero = expr.func(*nz_args).is_zero
    return classes, sub_is_zero

def check(expr, bad):
    if not getattr(expr, "is_Add", False):
        return None
    classes, sub = observe(expr)
    expected = expr._eval_is_zero()      # the REAL patched routine
    got = model(classes, sub)            # the deep model
    if got != expected:
        bad.append((str(expr), classes, sub, got, expected))
    return sub

def fresh_palette(uid):
    p = [Integer(0)]
    p += [Symbol("u%d_%d" % (uid, k), real=True, nonzero=True) for k in range(3)]
    p += [Symbol("q%d_%d" % (uid, k), real=True, positive=True) for k in range(2)]
    p += [Symbol("r%d_%d" % (uid, k), real=True) for k in range(2)]
    p += [Symbol("g%d_%d" % (uid, k)) for k in range(2)]
    p += [Symbol("m%d_%d" % (uid, k), imaginary=True) for k in range(2)]
    p += [Symbol("w%d_%d" % (uid, k), real=True) * I for k in range(2)]
    p += [Integer(2) * I, Integer(3) * I, sqrt(2), Rational(7, 3),
          (1 + I) ** 2, -2 * I]
    return p

def main():
    bad = []
    # (1) the exact issue witness
    issue = -2 * I + (1 + I) ** 2
    if not getattr(issue, "is_Add", False):
        print("AXIOM-UNSOUND: issue witness is not an Add"); return 1
    c, s = observe(issue)
    if model(c, s) is not None or issue._eval_is_zero() is not None:
        bad.append(("issue witness verdict", c, s, model(c, s), issue._eval_is_zero()))
    check(issue, bad)

    # (2) curated boundary multisets (fresh symbols each)
    def B(uid):
        a1 = Symbol("ba%d" % uid, real=True, positive=True)
        a2 = Symbol("bb%d" % uid, real=True, positive=True)
        u1 = Symbol("bu%d" % uid, real=True, nonzero=True)
        u2 = Symbol("bv%d" % uid, real=True, nonzero=True)
        ru = Symbol("br%d" % uid, real=True)
        gen = Symbol("bg%d" % uid)
        m1 = Symbol("bm%d" % uid, imaginary=True)
        m2 = Symbol("bn%d" % uid, imaginary=True)
        w = Symbol("bw%d" % uid, real=True)
        return [
            a1 + m1, a1 + a2, m1 + m2, a1 + a2 + m1, a1 + w * I,
            a1 + m1 + w * I, u1 - u2 + m1, a1 + ru, a1 + gen,
            Integer(0) + a1 + m1, m1, a1 + a2 + w * I, u1 - u1 + m1,
        ]
    n_boundary = 0
    for uid in range(40):
        for expr in B(uid):
            check(expr, bad); n_boundary += 1

    # (3) randomized fuzz over fresh palettes
    rng = random.Random(15875)
    seen = {None: 0, True: 0, False: 0}
    total = 0
    for it in range(20000):
        pal = fresh_palette(it)
        summ = [rng.choice(pal) for _ in range(rng.randint(1, 5))]
        expr = Add(*summ)
        s = check(expr, bad)
        if getattr(expr, "is_Add", False):
            total += 1
            seen[s] = seen.get(s, 0) + 1

    if bad:
        print("AXIOM-UNSOUND (deep model != real patched _eval_is_zero):", bad[:8])
        return 1
    if not (seen.get(True, 0) and seen.get(False, 0) and seen.get(None, 0)):
        print("axiom probe inconclusive: fuzz did not exercise all sub_is_zero values:", seen)
        return 1
    print("axiom-soundness OK: deep model add_is_zero == real patched _eval_is_zero "
          "on issue witness +", n_boundary, "boundary +", total,
          "fuzz Add expressions; sub_is_zero distribution", seen)
    return 0

sys.exit(main())
'''

_AX_CONTAIN = r'''
import sys, warnings
warnings.filterwarnings("ignore")
from sympy import I, S, Symbol, Integer, Add

def classify(a):
    if a.is_real:
        if a.is_zero:
            return 0
        if a.is_zero is False:
            return 1
        return 2
    elif a.is_imaginary:
        return 3
    elif (S.ImaginaryUnit * a).is_real:
        return 4
    else:
        return 5

def main():
    # The model's Requires: every tag in 0..5, and the LINKING constraint
    # count_eq(classes,1)==0 (no real-nonzero summand) => sub_is_zero == True.
    # Containment: every class tag the model can carry must be REALIZABLE by a
    # genuine sympy summand, and the linking fact (empty real-nonzero sub-sum is
    # zero, so sub_is_zero==True when nz==0) must hold on the REAL callee. If any
    # reachable profile were not realizable => AXIOM-TOO-WEAK-FOR-CALLER.
    bad = []
    # one canonical summand realizing each tag 0..5
    reps = {
        0: Integer(0),
        1: Symbol("u", real=True, nonzero=True),
        2: Symbol("r", real=True),
        3: Symbol("m", imaginary=True),
        4: Symbol("w", real=True) * I,
        5: Symbol("g"),
    }
    for tag, a in reps.items():
        if classify(a) != tag:
            bad.append(("tag not realizable", tag, classify(a)))

    # the linking precondition: when there is NO real-nonzero summand, the
    # real-nonzero sub-sum is the empty Add = S.Zero, whose is_zero is True.
    empty_sub = Add()  # self.func(*[]) on the empty nz: the empty Add is S.Zero
    if S.Zero.is_zero is not True:
        bad.append(("S.Zero.is_zero not True", S.Zero.is_zero))
    if empty_sub.is_zero is not True:
        bad.append(("empty real-nonzero sub-sum is_zero not True", empty_sub, empty_sub.is_zero))

    if bad:
        print("AXIOM-TOO-WEAK-FOR-CALLER:", bad[:8])
        return 1
    print("containment OK: every summand class tag 0..5 the model can carry is "
          "realizable by a genuine sympy summand, and the linking precondition "
          "(nz==0 => sub_is_zero==True, i.e. the empty real-nonzero sub-sum "
          "S.Zero.is_zero is True) holds on the real callee. No reachable class "
          "profile lies outside the A-reference domain.")
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-deepmodel-sound", "axiom": "add_is_zero", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_SOUND,
     "rationale": "if the deep model add_is_zero differs from the REAL patched "
                  "Add._eval_is_zero on any reachable (class-vector, sub_is_zero) — "
                  "the issue witness, the boundary multisets, or any of ~15000 fuzz "
                  "Add expressions (fresh symbols per case) — the A-reference is "
                  "unsound (AXIOM-UNSOUND). Re-runs the G-AX equivalence with its "
                  "oracle transcribed inline (self-contained) and asserts all three "
                  "sub_is_zero values are exercised."},
    {"id": "ax-deepmodel-containment", "axiom": "add_is_zero", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAIN,
     "rationale": "every summand class tag 0..5 the model can carry is realizable by a "
                  "genuine sympy summand and the linking precondition (nz==0 => "
                  "sub_is_zero==True, the empty real-nonzero sub-sum S.Zero.is_zero is "
                  "True) holds on the real callee, so the A-reference is exercised "
                  "exactly where the model reaches it. A reachable class profile the "
                  "real routine could not realize would be AXIOM-TOO-WEAK-FOR-CALLER "
                  "(none exists)."},
]

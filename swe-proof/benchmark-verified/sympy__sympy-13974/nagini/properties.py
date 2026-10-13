"""properties.py — PBT falsification manifest for sympy__sympy-13974.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    power_of_collection(args: List[int], exp: int) -> List[int]

(the deep model of `tensor_product_simp_Pow`: distribute one exponent across the
ordered tensor factors `args`). Its load-bearing contract:

    Requires(Acc(list_pred(args), 1/2))                       # READ-ONLY input
    Requires(exp != 1)                                        # non-identity exp
    Ensures (Acc(list_pred(args), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (len(Result()) == len(args))                      # factor count/order
    Ensures (ToSeq(Result()) == pointwise_pow(ToSeq(args), exp))   # THE PIN

What the spec actually defends, and the attacks it must survive:

  * The output pin `ToSeq(Result()) == pointwise_pow(ToSeq(args), exp)` is
    GROUNDED in the input: `pointwise_pow` is a @Pure deep fold (NOT an opaque
    answer-key marker) — `PSeq(pow_expr(s[0],exp)) + pointwise_pow(s.drop(1),exp)`
    — the element-wise image of the binary power map `pow_expr` over the ACTUAL
    input factors `args[k]`. There is NO executable materialization of a @Pure
    PSeq into a list_pred list, so you cannot "echo the oracle"; the only way to
    make `ToSeq(result)` equal the fold is to build the list factor-by-factor by
    applying `pow_expr` to each input factor — which IS the real per-factor work.
    So there is no WRONG echo that verifies (UNGROUNDED-ORACLE is N/A here); the
    `echo-attempt-honest` positive control confirms the cheapest impl that
    satisfies the pin still has to apply the power map to every factor.

  * The DISCRIMINATING content is exactly the @ContractOnly axiom `pow_expr`'s
    non-triviality `pow_expr(base, exp) != base` (under `Requires(exp != 1)`): it
    is what forces the per-factor power to be OBSERVABLE — an impl that leaves a
    factor unchanged (`result[k] == args[k]`, the prepatch identity fold) cannot
    satisfy the pin, because `pow_expr(args[k], exp) != args[k]`. Every uniqueness
    rival exploits a position where it skips this work.

  * `args` is held read-only (1/2). The MANDATORY attack is FRAME MUTATION
    (`frame-mutate-args`): an impl that WRITES to `args` to satisfy the pin
    vacuously must fail for INSUFFICIENT PERMISSION (a store needs full perm).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the nested invariants live
there too), so `markers.same_spec` is guaranteed and a rejection comes from the
POSTCONDITION catching wrong behaviour (or the permission system), never from a
tampered spec. Each `expect:"reject"` rival carries the refinement argument that
its faithful real patch would NOT resolve the F2P. Axiom cases run the REAL sympy
callee (`b ** exp` / `tensor_product_simp_Pow`) in Docker against the gold patch.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13974"
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
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body between the `# invariants-end` marker and the return.
# Used as a single replaceable block for structural rewrites. The nested
# invariants are NOT part of this block (they sit above # invariants-end), so
# every variant keeps the five Invariant clauses byte-identical — only the loop
# body / setup / return below them changes. same_spec is unaffected either way
# (the impl region is fully elided in the spec view), but keeping the invariants
# fixed makes the proof obligations the gold ones, so a rejection is attributable
# to the body change, not to a broken invariant.
_GOLD_BODY = """        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT. Same backward fold and same
# front-recursive proof shape (so no induction lemma the verifier can't auto-
# discharge — per the PLAN caution against forward-append against a front-
# recursive spec helper), but the body is reshaped: the power handle is bound to
# a LOCAL `p` first and prepended via that local, and the two structural Asserts
# are REORDERED. Semantically identical to gold; different source. If this fails
# to verify, the postcondition is over-fit to the exact gold spelling =>
# SPEC-TOO-STRONG.
_POS_LOCAL_BODY = """        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        p = pow_expr(e, exp)
        result = [p] + result
        i = i - 1
    return result"""
_POS_LOCAL = _swap(_BASE, _GOLD_BODY, _POS_LOCAL_BODY)

# (5b) ECHO-ATTEMPT, HONEST. The most direct "echo the oracle" attack would be
# `result = <materialize pointwise_pow(ToSeq(args), exp)>`. There is NO
# executable materialization of a @Pure PSeq into a list_pred list, so the
# cheapest impl that satisfies the GROUNDED pin still has to apply pow_expr to
# every factor. This control is that cheapest honest impl: right before the
# return it asserts the result it built EQUALS the spec oracle
# `pointwise_pow(ToSeq(args), exp)`. It is CORRECT (expect="verify"); its purpose
# is to demonstrate there is NO wrong echo that verifies — the oracle is grounded
# in `args`, not an opaque marker. (If a wrong echo COULD verify, this would
# instead be a SPEC-TOO-WEAK reject case; no such echo exists here.)
_ECHO_TAIL = """        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result"""
_ECHO_TAIL_NEW = """        result = [pow_expr(e, exp)] + result
        i = i - 1
    Assert(ToSeq(result) == pointwise_pow(ToSeq(args), exp))
    return result"""
_ECHO_HONEST = _swap(_BASE, _ECHO_TAIL, _ECHO_TAIL_NEW)

# (6) ADMISSIBILITY. An F2P-shaped in-domain input — two distinct factor handles
# [10, 20] and a non-identity exponent 2 (the F2P `TP(A,B)**2` shape) — is built
# and EVERY Requires conjunct of power_of_collection is asserted for it
# (`Acc(list_pred(args),1/2)` and `exp != 1`). If a conjunct cannot be
# established for a legitimate input => PRECOND-TOO-STRONG. The probe list is
# built BEFORE the loop setup (still inside the impl region) so the spec is
# untouched, and it is the probe's OWN list so it consumes no permission the gold
# body still needs.
#
# Assert-style rather than the self-call this case used before:
# power_of_collection now carries Requires(MustTerminate(2)) (total correctness),
# and Nagini demands a callee's obligation level be STRICTLY below its caller's,
# so an equal-level self-call is rejected by the obligation system ("Callee
# power_of_collection might not take all unsatisfied obligations from the
# caller") — an artifact of the termination spec, unrelated to the value
# preconditions this case probes.
_ADMISS_HEAD = "    result = []  # type: List[int]\n    i = len(args)"
_ADMISS_HEAD_NEW = (
    "    probe = [10, 20]  # type: List[int]\n"
    "    probe_exp = 2\n"
    "    # every Requires conjunct of power_of_collection, for that input\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    Assert(probe_exp != 1)\n"
    "    # the F2P shape: two DISTINCT factor handles, a non-identity exponent\n"
    "    Assert(len(probe) == 2 and probe[0] != probe[1])\n"
    "    result = []  # type: List[int]\n"
    "    i = len(args)"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `args` is read-only
# (Acc(list_pred(args),1/2)). This rival WRITES `args[i-1] = pow_expr(e, exp)`
# (store the per-factor power back into the input) and then reads it. The intent
# would be to satisfy the pin while pretending the work was done in place. Under
# Acc(list_pred(args),1/2) a STORE to `args` requires FULL permission, so it must
# fail for INSUFFICIENT PERMISSION — not for a wrong value. The gold invariants
# and the two structural Asserts are kept verbatim, so the failure is
# attributable solely to the write. Rejection source: the PERMISSION SYSTEM (the
# store is unverifiable under 1/2 read-only access).
_FRAME_BODY = """        e = args[i - 1]
        args[i - 1] = pow_expr(e, exp)
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result"""
_RIVAL_FRAME = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)

# (3a) PARTIAL-DOMAIN — diverge on ONE position. This rival distributes the
# exponent to EVERY factor correctly EXCEPT the LAST factor (index len(args)-1,
# the FIRST one processed by the backward loop, i.e. iteration i == len(args)):
# there it leaves the factor UNCHANGED (`result = [e] + result`, the prepatch
# identity fold localized to one position) instead of raising it to the
# exponent. It pins only part of the F2P domain — every factor but the last is
# handled exactly like gold. A faithful real patch of this shape (a
# `tensor_product_simp_Pow` that distributes to all base.args except the last)
# would emit `TP(A**x, B)` for `TP(A,B)**x` instead of `TP(A**x, B**x)` and so
# FAIL the F2P `test_tensor_product_simp` (which asserts EVERY factor raised).
# Rejection source: the postcondition `ToSeq(Result()) == pointwise_pow(...)`,
# which pins the WHOLE sequence — the i == len(args) iteration cannot close the
# `ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp)` invariant when the
# emitted handle is `e` but the fold requires `pow_expr(e, exp)`, and the
# pow_expr non-triviality axiom (`pow_expr(e,exp) != e` under exp != 1) makes the
# two provably distinct.
_PARTIAL_LAST_BODY = """        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        if i == len(args):
            result = [e] + result
        else:
            result = [pow_expr(e, exp)] + result
        i = i - 1
    return result"""
_RIVAL_PARTIAL_LAST = _swap(_BASE, _GOLD_BODY, _PARTIAL_LAST_BODY)

# (3b) GLOBAL IDENTITY FOLD (the prepatch bug, as a uniqueness rival / cheap
# supporting case with a real refinement). Every factor is left UNCHANGED
# (`result = [e] + result`) — the exponent is never applied. This is exactly the
# pre-patch `tensor_product_simp(e.base) ** e.exp` behaviour (exponent wraps the
# whole tensor product, each factor stays `args[k]`). Its faithful real patch is
# the UNPATCHED code, which fails ALL four F2P witnesses (`TP(A,B)**x` stays
# `TP(A,B)` not `TP(A**x,B**x)`). Rejection source: the pin — `args[k]` can never
# equal `pow_expr(args[k], exp)` (pow_expr non-triviality under exp != 1), so the
# loop invariant fails on the very first iteration.
_IDENTITY_BODY = """        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [e] + result
        i = i - 1
    return result"""
_RIVAL_IDENTITY = _swap(_BASE, _GOLD_BODY, _IDENTITY_BODY)

# (3c) DOUBLE-EXPONENT / WRONG-CONSTANT MAP. A rival that applies the power map
# but with a DIFFERENT, in-spec exponent handle (a fixed `2` independent of the
# argument `exp`) instead of the actual `exp`. For inputs whose exponent is not
# 2 the emitted factor `pow_expr(e, 2)` differs from the required
# `pow_expr(e, exp)`. Faithful real patch: `TensorProduct(*[b**2 for b in
# e.base.args])` (ignore e.exp, always square) — emits `TP(A**2, B**2)` for
# `TP(A,B)**x` and FAILS the F2P `TP(A,B)**x == TP(A**x, B**x)`. Rejection
# source: the pin requires `pow_expr(e, exp)` per factor; with `exp` a free
# (universally-quantified, exp != 1) handle, `pow_expr(e, 2)` is not provably
# equal to `pow_expr(e, exp)` (pow_expr is only known deterministic in BOTH
# args — distinct second args give unconstrained, hence unequal-in-general,
# handles), so the invariant cannot close.
_WRONGEXP_BODY = """        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(e, 2)] + result
        i = i - 1
    return result"""
_RIVAL_WRONGEXP = _swap(_BASE, _GOLD_BODY, _WRONGEXP_BODY)

# (3d) WRONG-FACTOR (off-by-one read). A rival that reads the WRONG factor —
# `args[i]`-shaped neighbour instead of `args[i-1]` — for all but the boundary,
# so the emitted power is of a shifted factor. Modeled as: emit
# `pow_expr(args[0], exp)` for every position (use the FIRST factor's power
# everywhere) rather than the position's own factor. For any input with >= 2
# distinct factors this drops the per-position grounding. Faithful real patch:
# `TensorProduct(*[e.base.args[0]**e.exp for _ in e.base.args])` — emits
# `TP(A**x, A**x)` for `TP(A,B)**x` and FAILS the F2P (expects `TP(A**x, B**x)`).
# Rejection source: the pin ties `Result()[k]` to `pow_expr(args[k], exp)`; using
# `args[0]` for `k>0` is `pow_expr(args[0], exp)`, not provably equal to
# `pow_expr(args[k], exp)` (pow_expr functional in its first arg; distinct factor
# handles give unconstrained results), so the invariant fails for k != 0.
_WRONGFACTOR_BODY = """        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(args[0], exp)] + result
        i = i - 1
    return result"""
_RIVAL_WRONGFACTOR = _swap(_BASE, _GOLD_BODY, _WRONGFACTOR_BODY)


# ===========================================================================
# SECOND MODELED FUNCTION — simp_pow_factor (the routing decision)
# ===========================================================================
# simp_pow_factor(is_pow_of_tp, factors, exp) models tensor_product_simp_Mul's
# decision for ONE non-commutative factor of a product: a Pow-of-TensorProduct
# factor is replaced by its per-factor distribution (delegating to the deep
# power_of_collection); a bare TensorProduct factor passes through unchanged. Its
# contract:
#     Ensures(Implies(is_pow_of_tp, ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp)))
#     Ensures(Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)))
# These swaps edit ONLY the simp_pow_factor impl region (its routing line / its
# passthrough loop body), uniquely identified below, so same_spec is preserved and
# a rejection is attributable to the routing postcondition.

# The gold routing line (unique to simp_pow_factor's impl region).
_ROUTE_GOLD = """    if is_pow_of_tp:
        return power_of_collection(factors, exp)"""

# The gold passthrough loop body (unique: it prepends the UNCHANGED factor `e`,
# inside simp_pow_factor — power_of_collection's identical-looking loop prepends
# pow_expr(e, exp), so this exact block occurs once).
_PASS_GOLD = """        e = factors[i - 1]
        Assert(ToSeq(factors).drop(i - 1)[0] == e)
        Assert(ToSeq(factors).drop(i - 1).drop(1) == ToSeq(factors).drop(i))
        result = [e] + result
        i = i - 1
    return result"""

# (R-pos) ROUTING POSITIVE CONTROL — structurally-different but CORRECT. The
# is_pow_of_tp branch is written by binding the delegated result to a local first
# and returning it (semantically identical to the direct return). Must verify, or
# the routing postcondition is over-fit to the exact gold spelling => SPEC-TOO-STRONG.
_ROUTE_LOCAL = _swap(_BASE, _ROUTE_GOLD,
    """    if is_pow_of_tp:
        distributed = power_of_collection(factors, exp)
        return distributed""")

# (R-1) DROPPED ROUTING — the prepatch routing bug, as a uniqueness rival. The
# is_pow_of_tp branch FAILS to distribute: it falls through to the passthrough
# (returns the factors unchanged) even when the factor is a Pow-of-TensorProduct.
# This is exactly the pre-patch tensor_product_simp_Mul, whose n_nc==1 case was a
# bare `return e` (no routing into the distribution). Faithful real patch: the
# UNPATCHED dispatcher, which fails the F2P `x*TP(A,B)**2 == x*TP(A**2,B**2)` (it
# stays `x*TP(A,B)**2`, factors unchanged). Rejection source: the routing pin
# Implies(is_pow_of_tp, ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp)) —
# the passthrough returns ToSeq(factors), and factors[k] != pow_expr(factors[k],exp)
# (pow_expr non-triviality under exp != 1), so the is_pow_of_tp postcondition fails.
_ROUTE_DROPPED = _swap(_BASE, _ROUTE_GOLD,
    """    if is_pow_of_tp:
        pass  # routing dropped: fall through to the unchanged passthrough""")

# (R-2) MIS-ROUTED — the routing decision is INVERTED. The is_pow_of_tp branch
# passes through (no distribution) and the not-is_pow_of_tp branch distributes.
# A real patch that routes the bare TensorProduct factor through the per-factor
# power (and leaves the genuine Pow-of-TP factor alone) would emit the wrong
# expression for both shapes and fail the F2P. Rejection source: BOTH branch pins
# break — the is_pow_of_tp branch returns ToSeq(factors) where the pin requires the
# distribution; the not-is_pow_of_tp branch returns the distribution where the pin
# requires ToSeq(factors) unchanged (pow_expr non-triviality makes them distinct).
# Inverting the routing guard alone produces the mis-routed function: with
# `if not is_pow_of_tp: return power_of_collection(...)`, an is_pow_of_tp factor
# falls through to the (unchanged) passthrough loop (returns factors as-is) and a
# bare TensorProduct factor gets the distribution — exactly the inverted decision.
_RIVAL_MISROUTE = _swap(_BASE, _ROUTE_GOLD,
    """    if not is_pow_of_tp:
        return power_of_collection(factors, exp)""")

# (R-3) PASSTHROUGH-DISTORTED — the not-is_pow_of_tp (bare TensorProduct) branch
# wrongly applies the power map to each factor instead of passing it through. A
# real patch that re-powers a factor that is ALREADY a bare TensorProduct (no
# exponent to apply) would rewrite `...*TP(A,B)` to `...*TP(A**exp,B**exp)`, fabricating
# an exponent — failing the F2P (e.g. the `*TP(C,D)` factor in witness 3 must stay
# TP(C,D)-shaped, only multiplied in). Rejection source: the passthrough pin
# Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)) — emitting
# pow_expr(e,exp) where the pin requires the unchanged `e` (pow_expr non-triviality
# under exp != 1 makes them provably distinct), so the passthrough invariant fails.
_RIVAL_PASS_DISTORTED = _swap(_BASE, _PASS_GOLD,
    """        e = factors[i - 1]
        Assert(ToSeq(factors).drop(i - 1)[0] == e)
        Assert(ToSeq(factors).drop(i - 1).drop(1) == ToSeq(factors).drop(i))
        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result""")


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "structurally-different but CORRECT impl (power bound to a local "
                  "`p` and prepended; the two structural Asserts reordered) keeps the "
                  "backward fold + front-recursive proof shape, so it must verify. If "
                  "it fails the postcondition is over-fit to the gold spelling => "
                  "SPEC-TOO-STRONG."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the GROUNDED oracle pointwise_pow has no executable "
                  "materialization to echo; this cheapest honest impl asserts its "
                  "built result == the oracle and must verify. Demonstrates there is "
                  "no WRONG echo (UNGROUNDED-ORACLE N/A); the only way to satisfy the "
                  "pin is to apply pow_expr per factor."},
    {"id": "admiss-f2p-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the F2P-shaped input [10,20] with exp=2 (the TP(A,B)**2 shape: two "
                  "DISTINCT factor handles, a non-identity exponent) is built and EVERY "
                  "Requires conjunct of power_of_collection is asserted for it "
                  "(Acc(list_pred(args),1/2) and exp != 1). The probe owns its list so "
                  "it consumes no permission the gold body still needs. If a conjunct "
                  "could not be established for a normal input => PRECOND-TOO-STRONG. "
                  "Assert-style rather than a self-call: under "
                  "Requires(MustTerminate(2)) an equal-level recursive self-call is "
                  "rejected by the obligation system, an artifact unrelated to the "
                  "value preconditions."},
    {"id": "routing-pos-control-local", "kind": "soundness", "expect": "verify",
     "module": _ROUTE_LOCAL,
     "rationale": "simp_pow_factor's is_pow_of_tp branch, rewritten to bind the "
                  "delegated power_of_collection result to a local before returning "
                  "it, is semantically identical and must verify. If it fails, the "
                  "routing postcondition is over-fit to the exact delegation spelling "
                  "=> SPEC-TOO-STRONG."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "frame-mutate-args", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: the gold "
                   "tensor_product_simp_Pow builds a NEW TensorProduct from a list "
                   "comprehension over e.base.args and never mutates e.base.args (sympy "
                   "Expr args are immutable tuples). The write to `args` is a pure "
                   "verification artifact with no real-patch analogue, so it cannot be "
                   "a verify-but-not-resolve break — it must be rejected on permission.",
     "rationale": "rejection from the PERMISSION SYSTEM: under Acc(list_pred(args),1/2) "
                  "a store `args[i-1] = ...` needs full permission, so the impl fails "
                  "for INSUFFICIENT PERMISSION (not a wrong value)."},
    {"id": "partial-domain-last-factor", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_LAST,
     "refinement": "a real patch that distributes the exponent to every base.arg EXCEPT "
                   "the last (TP(A**x, B) for TP(A,B)**x) FAILS the F2P "
                   "test_tensor_product_simp, which asserts EVERY factor is raised "
                   "(TP(A**x, B**x)). Faithful but non-resolving.",
     "rationale": "rejection from the pin ToSeq(Result()) == pointwise_pow(...): the "
                  "i==len(args) iteration emits `e` where the fold requires "
                  "pow_expr(e,exp); pow_expr non-triviality (!= e under exp != 1) makes "
                  "them provably distinct, so the invariant cannot close."},
    {"id": "identity-fold-prepatch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_IDENTITY,
     "refinement": "this IS the pre-patch behaviour (exponent left wrapping the whole "
                   "tensor product, each factor unchanged). Its faithful real patch is "
                   "the UNPATCHED code, which fails ALL four F2P witnesses. Definitively "
                   "non-resolving (cheap supporting case, real refinement).",
     "rationale": "rejection from the pin: args[k] != pow_expr(args[k],exp) (pow_expr "
                  "non-triviality under exp != 1), so the loop invariant fails on the "
                  "first iteration."},
    {"id": "wrong-exponent-const", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONGEXP,
     "refinement": "a real patch that always squares (b**2, ignoring e.exp) emits "
                   "TP(A**2, B**2) for TP(A,B)**x and FAILS the F2P "
                   "TP(A,B)**x == TP(A**x, B**x). Faithful but non-resolving.",
     "rationale": "rejection from the pin: pow_expr(e,2) is not provably equal to "
                  "pow_expr(e,exp) for a free exp (pow_expr is only deterministic in "
                  "BOTH args; distinct second args give unconstrained handles), so the "
                  "invariant cannot close."},
    {"id": "wrong-factor-broadcast", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONGFACTOR,
     "refinement": "a real patch that raises the FIRST base.arg for every position "
                   "(TP(A**x, A**x) for TP(A,B)**x) FAILS the F2P (expects "
                   "TP(A**x, B**x)). Faithful but non-resolving.",
     "rationale": "rejection from the pin: Result()[k] is tied to pow_expr(args[k],exp); "
                  "pow_expr(args[0],exp) for k>0 is not provably equal (pow_expr "
                  "functional in its first arg; distinct factor handles give "
                  "unconstrained results), so the invariant fails for k != 0."},

    # ---- routing rivals (simp_pow_factor — must reject) ----
    {"id": "routing-dropped-prepatch", "kind": "uniqueness", "expect": "reject",
     "module": _ROUTE_DROPPED,
     "refinement": "this IS the pre-patch routing (tensor_product_simp_Mul's n_nc==1 "
                   "case was a bare `return e`, with no path into the distribution). Its "
                   "faithful real patch is the UNPATCHED dispatcher, which fails the F2P "
                   "x*TP(A,B)**2 == x*TP(A**2,B**2) (it stays x*TP(A,B)**2, factors "
                   "unchanged). Definitively non-resolving.",
     "rationale": "rejection from the routing pin Implies(is_pow_of_tp, ToSeq(Result()) "
                  "== pointwise_pow(ToSeq(factors), exp)): the is_pow_of_tp case falls "
                  "through to the passthrough returning ToSeq(factors); factors[k] != "
                  "pow_expr(factors[k],exp) (pow_expr non-triviality under exp != 1), so "
                  "the is_pow_of_tp postcondition cannot hold."},
    {"id": "routing-inverted", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MISROUTE,
     "refinement": "a real patch that distributes the exponent over a factor that is a "
                   "BARE TensorProduct (and leaves the genuine Pow-of-TP factor alone) "
                   "emits the wrong expression for both shapes — fabricating an exponent "
                   "on the bare factor and dropping it on the power factor — and FAILS "
                   "the F2P. Faithful but non-resolving.",
     "rationale": "rejection from BOTH branch pins: the is_pow_of_tp branch returns "
                  "ToSeq(factors) where the pin requires pointwise_pow(...); the "
                  "not-is_pow_of_tp branch returns the distribution where the pin "
                  "requires ToSeq(factors) unchanged — pow_expr non-triviality makes the "
                  "two provably distinct, so neither postcondition can close."},
    {"id": "routing-passthrough-distorted", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PASS_DISTORTED,
     "refinement": "a real patch that re-powers a factor that is ALREADY a bare "
                   "TensorProduct (no exponent to apply) rewrites ...*TP(C,D) to "
                   "...*TP(C**exp,D**exp), fabricating an exponent — failing the F2P "
                   "(witness 3's *TP(C,D) factor must stay TP(C,D)-shaped). Faithful but "
                   "non-resolving.",
     "rationale": "rejection from the passthrough pin Implies(not is_pow_of_tp, "
                  "ToSeq(Result()) == ToSeq(factors)): emitting pow_expr(e,exp) where the "
                  "pin requires the unchanged `e` (pow_expr non-triviality under exp != 1 "
                  "makes them provably distinct), so the passthrough invariant fails."},
]


# ===========================================================================
# AXIOM LANE (Docker, real sympy callee under the gold patch)
# ===========================================================================
# The one consumed axiom is `pow_expr` (@Pure @ContractOnly): the symbolic power
# map `b ** exp` invoked once per tensor factor inside tensor_product_simp_Pow.
# Two probes: axiom-soundness (determinism + non-triviality under exp != 1, with
# the identity boundary exp==1 asserted to PROVE the precondition necessary) and
# axiom-containment (every exponent the model can pass to pow_expr lies in the
# axiom's Requires domain exp != 1). These mirror/strengthen axiom_check.py.

# (1) axiom-soundness for pow_expr (== real `b ** exp`). Determinism is claimed
# UNCONDITIONALLY; non-triviality `b**exp != b` is claimed ONLY under exp != 1.
# The probe fuzzes the IDENTITY boundary exp == 1 explicitly and asserts the
# OPPOSITE (`b ** 1 == b`), proving the Requires(exp != 1) guard is necessary and
# weakest-sufficient (the falsifying input is EXERCISED, not omitted) — directive
# 7 / the project's #2 weakness class. Also fuzzes exp == 0 (b**0 == 1 != b for a
# non-commutative symbol) to confirm the guard removes ONLY exp==1, not more.
_AX_POW_SOUND = r'''
import random, sys
from sympy import symbols, Symbol

A, B, C, D, E = symbols('A,B,C,D,E', commutative=False)
x, y = symbols('x,y')
nc = [A, B, C, D, E]
nontrivial_exps = [x, y, Symbol('n'), 2, 3, x + 1, 2 * x, 0, -1, -2]  # all != 1

bad = []
# determinism (unconditional): same (base, exp) -> equal result on repeat.
for b in nc:
    for e in nontrivial_exps + [1]:
        if (b ** e) != (b ** e):
            bad.append(("non-deterministic", repr(b), repr(e)))
# non-triviality UNDER exp != 1: b ** exp != b.
for b in nc:
    for e in nontrivial_exps:
        if (b ** e) == b:
            bad.append(("trivial-under-exp!=1 (AXIOM-UNSOUND)", repr(b), repr(e)))
# identity boundary exp == 1 (EXCLUDED by Requires): assert the OPPOSITE so the
# guard is proven necessary, not masked. b ** 1 == b.
for b in nc:
    if (b ** 1) != b:
        bad.append(("boundary-b**1!=b (guard not justified)", repr(b), "1"))
# randomized fuzz over the axiom domain (exp != 1)
rng = random.Random(13974)
n = 0
for _ in range(800):
    b = rng.choice(nc)
    e = rng.choice(nontrivial_exps)
    if (b ** e) != (b ** e) or (b ** e) == b:
        bad.append(("fuzz", repr(b), repr(e)))
    n += 1
if bad:
    print("AXIOM-UNSOUND pow_expr:", bad[:8]); sys.exit(1)
print("pow_expr SOUND: determinism unconditional; non-triviality b**exp != b for",
      len(nontrivial_exps), "exps x", len(nc), "bases +", n,
      "fuzz; identity boundary b**1 == b confirmed (Requires(exp != 1) necessary "
      "+ weakest-sufficient: b**0==1 and all other exps non-trivial).")
sys.exit(0)
'''

# (2) axiom-containment for pow_expr. Enumerate EXACTLY the (base, exp) pairs the
# MODEL can pass to pow_expr: the impl calls `pow_expr(e, exp)` where `e` is some
# input factor args[i-1] (a base handle — pow_expr has NO restriction on its
# first arg) and `exp` is the modeled function's own argument, which carries
# `Requires(exp != 1)`. So the ONLY containment obligation is: every exp the model
# reaches satisfies the axiom's Requires(exp != 1). The model's precondition
# `exp != 1` and the fact that `exp` is passed UNCHANGED to pow_expr make this a
# direct subset. We confirm it concretely: under the gold patch, the real
# tensor_product_simp_Pow is reached for the F2P shapes, and in EVERY case the
# exponent fed to `b ** e.exp` is a Pow's e.exp, which sympy canonicalisation
# guarantees is never the identity 1 (b**1 collapses to b, so no Pow node carries
# exp 1) — exactly the axiom's covered domain. Covering MORE (e.g. exp==0) would
# be SOUND over-coverage, not a defect (the float/int containment rule).
_AX_POW_CONTAIN = r'''
import sys
from sympy import symbols, Symbol, Pow
from sympy.physics.quantum.tensorproduct import (
    TensorProduct as TP, tensor_product_simp_Pow)

A, B, C, D = symbols('A,B,C,D', commutative=False)
x = symbols('x')

# (a) The model passes `exp` UNCHANGED to pow_expr and carries Requires(exp != 1).
#     So every exp the model reaches is, by construction, != 1 — inside the
#     axiom's Requires(exp != 1) domain. Confirm with the F2P exponents the gold
#     dispatcher actually distributes: each is the e.exp of a real Pow node.
reached_exps = []
for power in [TP(A, B) ** x, TP(A, B) ** 2, TP(C, D) ** x, (TP(A, B) ** 2)]:
    assert isinstance(power, Pow), ("expected a Pow node, got %r" % power)
    e_exp = power.exp
    reached_exps.append(e_exp)
    # the axiom's covered domain is exp != 1; a Pow node never carries exp 1.
    if e_exp == 1:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches exp == 1 (outside "
              "Requires(exp != 1)) at", repr(power)); sys.exit(1)

# (b) Faithfulness of the guard: a literal Pow with exponent 1 does NOT exist —
#     b**1 canonicalises to b (no Pow), so tensor_product_simp_Pow is never
#     reached with exp == 1. Confirm the canonicalisation.
collapsed = A ** 1
if isinstance(collapsed, Pow):
    print("AXIOM faithfulness broken: A**1 stayed a Pow", repr(collapsed)); sys.exit(1)

# (c) The gold helper distributes the SAME e.exp to every factor (the exp the
#     model passes to pow_expr per factor) — so the reachable second-arg set per
#     call is exactly {power.exp}, all != 1.
helper = tensor_product_simp_Pow(TP(A, B) ** x)
# every distributed factor is base ** x, i.e. the exponent reached is x (!= 1)
assert all(isinstance(f, Pow) and f.exp == x for f in helper.args), (
    "distributed factors do not all carry exp x: %r" % (helper.args,))

print("containment OK: every exp the model passes to pow_expr is != 1 (model's "
      "Requires(exp != 1), passed unchanged; sympy guarantees no Pow node carries "
      "exp 1 so the helper is never reached with exp==1). Reached exps:",
      [str(e) for e in reached_exps], "all in Requires(exp != 1).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-pow-sound", "axiom": "pow_expr", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_POW_SOUND,
     "rationale": "if the real `b ** exp` is non-deterministic, or equals b for some "
                  "exp != 1, the axiom over-claims => AXIOM-UNSOUND. The identity "
                  "boundary b**1 == b is asserted to prove the Requires(exp != 1) guard "
                  "is necessary, not masked."},
    {"id": "ax-pow-containment", "axiom": "pow_expr", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_POW_CONTAIN,
     "rationale": "the model passes its own `exp` (Requires(exp != 1)) unchanged to "
                  "pow_expr, and sympy guarantees no Pow node carries exp 1; so every "
                  "exp the caller reaches lies in the axiom's domain. A reachable exp "
                  "outside Requires(exp != 1) would be AXIOM-TOO-WEAK-FOR-CALLER."},
]

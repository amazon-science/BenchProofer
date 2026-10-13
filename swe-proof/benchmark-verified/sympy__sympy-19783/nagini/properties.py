# properties.py — PBT falsification battery for sympy__sympy-19783.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py variant that shares the FROZEN spec
# byte-for-byte (region-surgery: only text strictly INSIDE one of the two
# # impl-start / # impl-end regions is swapped) and is checked by Nagini verify +
# markers.same_spec.
#
# ------------------------------------------------------------------ surface ---
# Two modeled functions, each a binary-product step on a quantum operand whose
# family is abstracted to an integer kind tag (0 operator, 1 identity,
# 2 conjugate, 3 other). Both return a fresh `Product` record.
#
#   identity_mul(other_kind: int) -> Product    (IdentityOperator.__mul__)
#     Requires: is_kind(other_kind)             # 0..3
#     Ensures:  (I1) left_kind == 1 and right_kind == other_kind
#               (I2) is_mul == (not (is_operator_like(other_kind)
#                                    or is_conjugate(other_kind)))   <-- DISCRIM.
#                    => collapses (is_mul False) exactly on kinds {0,1,2};
#                       the new `or is_conjugate(..)` disjunct is THE site-1 fix.
#               (I3) result_kind == other_kind
#
#   dagger_mul(other_kind: int) -> Product       (Dagger.__mul__, new method)
#     Requires: is_kind(other_kind)
#     Ensures:  (D1) left_kind == 2 and right_kind == other_kind
#               (D2) is_mul == (not is_identity(other_kind))         <-- DISCRIM.
#                    => collapses exactly on kind 1 (identity); the whole method
#                       is the site-2 fix.
#               (D3) result_kind == 2  (the surviving conjugate factor)
#
# ------------------------------------------------- applicable-class analysis ---
# * FRAME-MUTATION: N/A. Neither modeled function has a read-only Acc(x,1/2)
#   reference input — the only parameter is a pass-by-value `int` kind tag, and
#   the operand objects are abstracted away into that tag (mapping.md §2: each
#   __mul__ constructs a fresh result, never mutates an operand). The only object
#   is the freshly-built `Product`, whose fields are written under permission the
#   constructor obtains itself. There is literally nothing read-only to overwrite,
#   so the mandatory-only-if-read-only frame-mutation case does not apply here.
#   (Documented in 'assessment'.)
# * UNGROUNDED-ORACLE ECHO: N/A as a *defect* vector. The postconditions are
#   GROUNDED entirely in the arg `other_kind` via the @Pure helpers
#   is_operator_like / is_identity / is_conjugate, which unfold to plain integer
#   comparisons (k==0 or k==1 / k==1 / k==2) — there is no opaque answer-key a
#   wrong impl could echo without doing the dispatch. The honest "echo" is just
#   the gold dispatch itself (the positive control). So this class is replaced by
#   the structurally-different positive control + admissibility, per directive 2.
# * CONTROL-FLOW-EFFECT: N/A. Both functions are total, pure-functional, raise
#   nothing, and have no side effect the value abstraction hides. No capability
#   token to add.
# * PARTIAL-DOMAIN: the STRONG applicable class. The is_mul dispatch pins a
#   collapse/non-collapse decision per kind; a rival can be correct on most kinds
#   yet diverge on exactly one (the F2P-discriminating kind). The two prepatch
#   skeletons (model_prepatch.py site-1 kind-2, model_prepatch_2.py site-2 kind-1)
#   are the canonical partial-domain rivals.
# * VALUE (result_kind / left_kind facet): a rival that keeps is_mul correct on
#   every kind (so an is_mul-bit fuzzer cannot see it) but mis-states which
#   operand survives (result_kind) or the left operand kind. Targets I1/I3/D1/D3.
# * POSITIVE CONTROL (soundness): a structurally-different but correct impl
#   (branch reorder / explicit per-kind enumeration / typed local) must verify.
# * ADMISSIBILITY: a self-call on each F2P-discriminating kind must establish the
#   Requires.
#
# AXIOM_TESTS: empty. meta.axioms == [] (axioms region intentionally empty). The
# classification predicates and the two dispatch functions are A-reference deep
# models validated by axiom_check.py / G-AX in-container (real
# IdentityOperator.__mul__ / Dagger.__mul__ on every operand kind), NOT consumed
# @ContractOnly obligations the proof relies on — there is no axiom obligation a
# Docker probe could falsify. (axiom_check.py is the standing G-AX soundness
# anchor and already fuzzes all four kinds + the exact F2P equalities.)
from pathlib import Path

INSTANCE = "sympy__sympy-19783"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The two verbatim impl regions (markers inclusive), each unique in _BASE. Every
# variant swaps the BODY between the markers (keeping the markers) so that
# markers.same_spec == True by construction: only impl-region text changes.
_IMPL1 = (
    "    # impl-start\n"
    "    if is_operator_like(other_kind) or is_conjugate(other_kind):\n"
    "        return Product(False, other_kind, 1, other_kind)\n"
    "    return Product(True, other_kind, 1, other_kind)\n"
    "    # impl-end\n"
)
_IMPL2 = (
    "    # impl-start\n"
    "    if is_identity(other_kind):\n"
    "        return Product(False, 2, 2, other_kind)\n"
    "    return Product(True, 2, 2, other_kind)\n"
    "    # impl-end\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: impl block not found verbatim: {old[:40]!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old[:40]!r}")
    return src.replace(old, new, 1)


def _wrap1(body_lines):
    return "    # impl-start\n" + body_lines + "    # impl-end\n"


def _wrap2(body_lines):
    return "    # impl-start\n" + body_lines + "    # impl-end\n"


def _variant1(new_body):
    """Swap ONLY identity_mul's impl region (dagger_mul stays gold)."""
    return _swap(_BASE, _IMPL1, _wrap1(new_body))


def _variant2(new_body):
    """Swap ONLY dagger_mul's impl region (identity_mul stays gold)."""
    return _swap(_BASE, _IMPL2, _wrap2(new_body))


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls.
# Both functions are rewritten as an explicit per-kind enumeration (no shared
# disjunction guard; branch order changed) using a typed local for is_mul. No
# loops / folds => no induction lemma; the four Product-field Ensures are
# discharged exactly as in gold. MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================
# identity_mul: enumerate the non-collapse kind (3) first, then collapse; this
# is behaviourally identical to the gold guard (collapse iff kind in {0,1,2}).
_POS1 = (
    "    # Structurally-different, behaviourally-identical: dispatch on the\n"
    "    # single non-collapse kind (3 = other) first, collapse otherwise.\n"
    "    if not is_operator_like(other_kind) and not is_conjugate(other_kind):\n"
    "        return Product(True, other_kind, 1, other_kind)\n"
    "    return Product(False, other_kind, 1, other_kind)\n"
)
# dagger_mul: branch on the negation; collapse only on identity (kind 1).
_POS2 = (
    "    # Structurally-different, behaviourally-identical: handle the\n"
    "    # non-identity (non-collapse) case first.\n"
    "    if not is_identity(other_kind):\n"
    "        return Product(True, 2, 2, other_kind)\n"
    "    return Product(False, 2, 2, other_kind)\n"
)


def _pos_control_module():
    src = _swap(_BASE, _IMPL1, _wrap1(_POS1))
    src = _swap(src, _IMPL2, _wrap2(_POS2))
    return src


# ===========================================================================
# 6. ADMISSIBILITY — the precondition must admit the F2P-discriminating inputs.
# A self-call at each site on the exact discriminating kind (site 1: kind 2,
# I*Dagger(O); site 2: kind 1, Dagger(O)*I) forces Requires(is_kind(other_kind))
# to be discharged at the call site, and asserts the discriminating is_mul/field
# outcome. If a normal F2P input could not establish the precondition =>
# PRECOND-TOO-STRONG. The probe body precedes the unchanged gold logic.
# ===========================================================================
_ADMISS1 = (
    "    # Admissibility: the site-1 discriminating F2P input is I * Dagger(O)\n"
    "    # (kind 2). Requires(is_kind(2)) must hold at the call site; the result\n"
    "    # must collapse (is_mul False) to the conjugate (result_kind 2).\n"
    "    probe = identity_mul(2)  # type: Product\n"
    "    Assert(probe.is_mul == False)\n"
    "    Assert(probe.result_kind == 2 and probe.left_kind == 1)\n"
    "    # Real (gold) logic, unchanged.\n"
    "    if is_operator_like(other_kind) or is_conjugate(other_kind):\n"
    "        return Product(False, other_kind, 1, other_kind)\n"
    "    return Product(True, other_kind, 1, other_kind)\n"
)
_ADMISS2 = (
    "    # Admissibility: the site-2 discriminating F2P input is Dagger(O) * I\n"
    "    # (kind 1). Requires(is_kind(1)) must hold at the call site; the result\n"
    "    # must collapse (is_mul False) to the conjugate (result_kind 2).\n"
    "    probe = dagger_mul(1)  # type: Product\n"
    "    Assert(probe.is_mul == False)\n"
    "    Assert(probe.result_kind == 2 and probe.left_kind == 2)\n"
    "    # Real (gold) logic, unchanged.\n"
    "    if is_identity(other_kind):\n"
    "        return Product(False, 2, 2, other_kind)\n"
    "    return Product(True, 2, 2, other_kind)\n"
)


def _admiss_module():
    src = _swap(_BASE, _IMPL1, _wrap1(_ADMISS1))
    src = _swap(src, _IMPL2, _wrap2(_ADMISS2))
    return src


# ===========================================================================
# 3a. PARTIAL-DOMAIN (site 1, the prepatch bug = model_prepatch.py): correct on
# every kind EXCEPT kind 2 (conjugate), where it drops the new `is_conjugate`
# disjunct and leaves an unevaluated product (is_mul True) although the spec
# requires a collapse (is_mul False). This is exactly the gold hunk reverted to
# `if isinstance(other, Operator)`. MUST reject.  (dagger_mul kept gold.)
# ===========================================================================
_REJ1_PREPATCH = (
    "    # PRE-PATCH site 1: only operator-like operands absorbed; a conjugate\n"
    "    # factor (kind 2) on the right is NOT absorbed -> stays an unevaluated\n"
    "    # product, so I * Dagger(O) is left unsimplified.\n"
    "    if is_operator_like(other_kind):\n"
    "        return Product(False, other_kind, 1, other_kind)\n"
    "    return Product(True, other_kind, 1, other_kind)\n"
)

# ===========================================================================
# 3b. PARTIAL-DOMAIN (site 2, the prepatch bug = model_prepatch_2.py): correct on
# every kind EXCEPT kind 1 (identity), where the generic fallback always builds an
# unevaluated product (is_mul True) although the spec requires a collapse to the
# conjugate. This is the absence of Dagger.__mul__ (inherited Expr.__mul__).
# MUST reject.  (identity_mul kept gold.)
# ===========================================================================
_REJ2_PREPATCH = (
    "    # PRE-PATCH site 2: a conjugate factor has no dedicated product rule, so\n"
    "    # the generic fallback always builds an unevaluated product, even against\n"
    "    # the identity element; Dagger(O) * I stays unsimplified.\n"
    "    return Product(True, 2, 2, other_kind)\n"
)

# ===========================================================================
# 3c. PARTIAL-DOMAIN (site 1, OVER-absorb the scalar kind 3): correct on kinds
# {0,1,2} but ALSO collapses on kind 3 (a scalar/other factor), claiming
# is_mul False where the spec requires is_mul True (I * x must stay Mul). A
# different sub-domain than 3a (kind 3, not kind 2). MUST reject.
# ===========================================================================
_REJ1_OVERABSORB = (
    "    # WRONG: also absorb a scalar/other factor (kind 3). The spec requires\n"
    "    # I * x to stay an unevaluated product (is_mul True) for kind 3.\n"
    "    return Product(False, other_kind, 1, other_kind)\n"
)

# ===========================================================================
# 3d. PARTIAL-DOMAIN (site 2, OVER-absorb a non-identity): correct on kind 1 but
# ALSO collapses on the operator kind 0, claiming is_mul False where the spec
# requires is_mul True (Dagger(O) * O must stay Mul). Distinct sub-domain from
# 3b. MUST reject.  (identity_mul kept gold.)
# ===========================================================================
_REJ2_OVERABSORB = (
    "    # WRONG: collapse for the operator kind 0 too. The spec requires\n"
    "    # Dagger(O) * O to stay an unevaluated product (is_mul True).\n"
    "    if is_identity(other_kind) or other_kind == 0:\n"
    "        return Product(False, 2, 2, other_kind)\n"
    "    return Product(True, 2, 2, other_kind)\n"
)

# ===========================================================================
# 1' VALUE (site 1, wrong surviving operand): keeps is_mul CORRECT on every kind
# (so an is_mul-bit fuzzer is blind to it) but on the collapse branch records the
# WRONG surviving operand kind — claims the LEFT operand (kind 1, the identity)
# survived instead of the right operand. Violates I3 (result_kind == other_kind)
# whenever other_kind != 1. MUST reject.
# ===========================================================================
_REJ1_WRONG_RESULT = (
    "    # is_mul facet CORRECT; but record the surviving operand as the LEFT\n"
    "    # operand (the identity, kind 1) instead of the right operand. Violates\n"
    "    # the I3 pin result_kind == other_kind whenever other_kind != 1.\n"
    "    if is_operator_like(other_kind) or is_conjugate(other_kind):\n"
    "        return Product(False, 1, 1, other_kind)\n"
    "    return Product(True, other_kind, 1, other_kind)\n"
)

# ===========================================================================
# 1'' VALUE (site 2, wrong surviving operand): keeps is_mul CORRECT on every kind
# but on the collapse branch records the RIGHT operand (the identity, kind 1) as
# the survivor instead of the conjugate (kind 2). Violates D3 (result_kind == 2).
# MUST reject.  (identity_mul kept gold.)
# ===========================================================================
_REJ2_WRONG_RESULT = (
    "    # is_mul facet CORRECT; but record the surviving operand as the RIGHT\n"
    "    # operand (the identity, kind 1) instead of the conjugate (kind 2).\n"
    "    # Violates D3 result_kind == 2.\n"
    "    if is_identity(other_kind):\n"
    "        return Product(False, other_kind, 2, other_kind)\n"
    "    return Product(True, 2, 2, other_kind)\n"
)

# ===========================================================================
# 1''' VALUE (site 1, wrong left_kind): keeps is_mul AND result_kind correct on
# every kind but records the LEFT operand as a conjugate (kind 2) instead of the
# identity (kind 1). Violates I1 (left_kind == 1). A facet neither is_mul nor
# result_kind constrains. MUST reject.
# ===========================================================================
_REJ1_WRONG_LEFT = (
    "    # is_mul + result_kind facets CORRECT; but mis-record the LEFT operand as\n"
    "    # a conjugate (kind 2) instead of the identity (kind 1). Violates I1.\n"
    "    if is_operator_like(other_kind) or is_conjugate(other_kind):\n"
    "        return Product(False, other_kind, 2, other_kind)\n"
    "    return Product(True, other_kind, 2, other_kind)\n"
)

# ===========================================================================
# 3e. SUPPORTING near-miss (site 1, never-collapse): cheap corruption claiming
# every product stays unevaluated (is_mul always True). Subsumes 3a on the whole
# operator/identity/conjugate domain; kept as a cheap supporting case but it still
# carries a real refinement (I*O, I*I, I*Dagger(O) all stay unsimplified ->
# test_identity F2P fails). MUST reject.
# ===========================================================================
_REJ1_NEVER_COLLAPSE = (
    "    # WRONG (whole-domain near-miss): never collapse; every product stays\n"
    "    # unevaluated (is_mul True) even for an operator/identity/conjugate right\n"
    "    # operand. Violates I2 on kinds {0,1,2}.\n"
    "    return Product(True, other_kind, 1, other_kind)\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-enumerate-both-sites",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control_module(),
        "rationale": "Both functions rewritten as a structurally-different but "
                     "behaviourally-identical dispatch (handle the non-collapse "
                     "kind(s) first via the negated guard; no loops/folds, so no "
                     "induction lemma is needed and every Product-field Ensures is "
                     "discharged exactly as in gold). identity_mul still collapses "
                     "iff kind in {0,1,2}; dagger_mul still collapses iff kind==1. "
                     "MUST verify; if it cannot, SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-both-discriminating-kinds",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_module(),
        "rationale": "Self-calls on the two F2P-discriminating inputs — "
                     "identity_mul(2) (I*Dagger(O)) and dagger_mul(1) "
                     "(Dagger(O)*I) — force Requires(is_kind(other_kind)) to be "
                     "discharged at each call site and assert the discriminating "
                     "collapse (is_mul False, the correct surviving operand). If "
                     "the precondition rejected these normal F2P inputs, "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "uniq-site1-prepatch-kind2-not-absorbed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant1(_REJ1_PREPATCH),
        "refinement": "This IS model_prepatch.py / the pre-patch gold hunk "
                      "`if isinstance(other, Operator)` (drops the new `Dagger` "
                      "disjunct). The faithful real patch leaves I * Dagger(O) as "
                      "the unevaluated Mul(I, Dagger(O)) instead of Dagger(O), so "
                      "the F2P assertion `I * Dagger(O) == Dagger(O)` in "
                      "test_identity FAILS — the instance stays unresolved. (G-AX "
                      "confirms the real callee on the pre-patch tree leaves it "
                      "unsimplified.)",
        "rationale": "Violates Ensures (I2) is_mul == (not (is_operator_like or "
                     "is_conjugate)) on the sub-domain other_kind==2: spec demands "
                     "is_mul False (collapse) but the rival returns True. Rejection "
                     "comes from the site-1 discriminating postcondition clause.",
    },
    {
        "id": "uniq-site2-prepatch-kind1-not-absorbed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant2(_REJ2_PREPATCH),
        "refinement": "This IS model_prepatch_2.py / the absence of Dagger.__mul__ "
                      "(inherited Expr.__mul__ always builds Mul). The faithful "
                      "real patch leaves Dagger(O) * I as Mul(Dagger(O), I) instead "
                      "of Dagger(O), so the F2P assertions `Dagger(O) * I == "
                      "Dagger(O)` (test_identity) and `Dagger(O)*Dagger(I) == "
                      "Dagger(O)` (test_dagger_mul, since Dagger(I)==I) both FAIL — "
                      "the instance stays unresolved.",
        "rationale": "Violates Ensures (D2) is_mul == (not is_identity) on the "
                     "sub-domain other_kind==1: spec demands is_mul False but the "
                     "rival returns True. Rejection comes from the site-2 "
                     "discriminating postcondition clause.",
    },
    {
        "id": "uniq-site1-overabsorb-scalar-kind3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant1(_REJ1_OVERABSORB),
        "refinement": "Over-absorbs: collapses on EVERY kind, including a scalar "
                      "other factor (kind 3). The faithful real patch would make "
                      "I * x return x for a scalar Symbol x, so the F2P assertion "
                      "`isinstance(I * x, Mul)` in test_identity FAILS (I*x would "
                      "be x, not a Mul) — the instance stays unresolved.",
        "rationale": "Violates Ensures (I2) on the sub-domain other_kind==3: spec "
                     "demands is_mul True (stay unevaluated) but the rival returns "
                     "False. A DISJOINT sub-domain from the prepatch rival (kind 3 "
                     "vs kind 2).",
    },
    {
        "id": "uniq-site2-overabsorb-operator-kind0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant2(_REJ2_OVERABSORB),
        "refinement": "Over-absorbs: collapses on the operator kind 0 too. The "
                      "faithful real patch would make Dagger(O) * O return Dagger(O) "
                      "instead of the symbolic product, so the F2P assertion "
                      "`Dagger(O)*O == Dagger(O)*O` (and `Dagger(O)*O*I == "
                      "Mul(Dagger(O), O)*I`) in test_dagger_mul would no longer hold "
                      "with the gold canonical form — the instance stays unresolved.",
        "rationale": "Violates Ensures (D2) is_mul == (not is_identity) on the "
                     "sub-domain other_kind==0: spec demands is_mul True but the "
                     "rival returns False. Distinct sub-domain from the site-2 "
                     "prepatch rival (kind 0 vs kind 1).",
    },
    {
        "id": "uniq-site1-wrong-surviving-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant1(_REJ1_WRONG_RESULT),
        "refinement": "The is_mul (collapse) facet is left CORRECT on every kind, "
                      "so a fuzzer flipping only the is_mul bit is blind to it; but "
                      "on collapse it records the LEFT operand (the identity) as the "
                      "survivor. The faithful real patch returns `other` (the right "
                      "operand) on collapse; returning `self` (the identity) instead "
                      "would make I * Dagger(O) == I and I * O == I, so the F2P "
                      "assertions `I * Dagger(O) == Dagger(O)` and `I * O == O` in "
                      "test_identity FAIL — the instance stays unresolved.",
        "rationale": "Violates Ensures (I3) result_kind == other_kind whenever "
                     "other_kind != 1 (records 1). Targets the surviving-operand "
                     "facet that I2 (is_mul) does not constrain.",
    },
    {
        "id": "uniq-site2-wrong-surviving-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant2(_REJ2_WRONG_RESULT),
        "refinement": "The is_mul facet is left CORRECT, so an is_mul-bit fuzzer is "
                      "blind to it; but on collapse it records the RIGHT operand "
                      "(the identity, kind 1) as the survivor. The faithful real "
                      "patch returns `self` (the conjugate, kind 2) on collapse; "
                      "returning the identity instead would make Dagger(O) * I == I, "
                      "so the F2P assertion `Dagger(O) * I == Dagger(O)` in "
                      "test_identity FAILS — the instance stays unresolved.",
        "rationale": "Violates Ensures (D3) result_kind == 2 on the collapse "
                     "sub-domain other_kind==1 (records 1). Targets the "
                     "surviving-operand facet that D2 (is_mul) does not constrain.",
    },
    {
        "id": "uniq-site1-wrong-left-operand-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant1(_REJ1_WRONG_LEFT),
        "refinement": "Both the is_mul and the result_kind facets are left CORRECT "
                      "on every kind (so a fuzzer of either is blind), but the LEFT "
                      "operand is recorded as a conjugate (kind 2) instead of the "
                      "identity (kind 1). The model pins the left operand of "
                      "IdentityOperator.__mul__ to the identity element; recording a "
                      "conjugate left operand misidentifies which method ran (it "
                      "would be Dagger.__mul__, a different real call site), so the "
                      "refined patch would not be IdentityOperator.__mul__ at all — "
                      "an unfaithful edit that does not implement the I*… fix.",
        "rationale": "Violates Ensures (I1) left_kind == 1. Targets the left-operand "
                     "identity facet that neither is_mul nor result_kind constrains.",
    },
    {
        "id": "uniq-site1-never-collapse-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant1(_REJ1_NEVER_COLLAPSE),
        "refinement": "Cheap supporting near-miss: every product stays unevaluated "
                      "(is_mul always True). The faithful real patch would leave "
                      "I * O, I * I, and I * Dagger(O) ALL unsimplified, so the F2P "
                      "assertions `I * O == O` and `I * Dagger(O) == Dagger(O)` in "
                      "test_identity FAIL — the instance stays unresolved. Subsumes "
                      "the site-1 prepatch rival on the whole {0,1,2} domain; kept "
                      "as a cheap supporting case, not a substitute for the reasoned "
                      "sub-domain rivals.",
        "rationale": "Violates Ensures (I2) on the entire collapse domain "
                     "{0,1,2}: spec demands is_mul False on those kinds.",
    },
]

# No @ContractOnly axioms in this bundle (meta.axioms == []; axioms region empty).
# The kind classification + the two dispatch functions are A-reference deep models
# validated by axiom_check.py / G-AX in-container (real IdentityOperator.__mul__ /
# Dagger.__mul__ on all 4 operand kinds + the exact F2P discriminating
# equalities), not consumed obligations the proof relies on. There is therefore no
# axiom-soundness / axiom-containment obligation a Docker probe could falsify.
AXIOM_TESTS = []

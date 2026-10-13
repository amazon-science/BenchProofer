"""PBT falsification battery for scikit-learn__scikit-learn-13328.

NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TEST is a FULL model.py variant that shares the frozen spec exactly
(same_spec) and edits ONLY the impl region of `fit_robust_regressor` (region
surgery via `_swap`). Each AXIOM_TEST is a self-contained probe run in the
instance Docker image against the REAL sklearn/numpy callees.

Defended surface (reasoned, not corrupted):

  fit_robust_regressor(input_rep, row_values) -> List[int]
    Requires Acc(list_pred(row_values), 1/2)        # READ-ONLY input
    Requires 0 <= input_rep <= 2                     # logical|integral|floating
    Ensures  Acc(list_pred(row_values), 1/2)
    Ensures  Acc(list_pred(Result()))
    Ensures  ToSeq(Result()) == negated(ToSeq(row_values))   # GROUNDED value
    Ensures  negation_performed(input_rep, row_values)                    # capability token

The load-bearing clauses are TWO unforgeable capability tokens, both body-less
@ContractOnly @Predicates (Nagini rejects any `Fold` of them):

  - `matrix_rep(input_rep, rep)` — "the matrix ACTUALLY HAS representation
    `rep`". SOLE producer: `validate_matrix`'s postcondition, which pins
    Result() == validated_rep(input_rep, request_floating). So a representation
    tag handed to the negation step cannot be FABRICATED (e.g. a constant
    floating tag with no validation call): the only tags with token evidence
    are ones the real validation step would actually produce.
  - `negation_performed(input_rep, row_values)` — "the negation step actually
    ran, ON EXACTLY this row collection (by reference)". SOLE producer:
    `negate_rows`'s postcondition (granted for the very list it negated), gated
    by BOTH `Requires(matrix_rep(input_rep, rep))` and
    `Requires(supports_negation(rep))`. Binding the collection prevents
    laundering the token through a stand-in list (empty dummy, copy).

Hence a verifying impl must reach a SUCCESSFUL `negate_rows(input_rep, ...,
row_values)` on its OWN rows for its OWN input_rep with an HONEST
(token-evidenced) representation — which, for the logical input (input_rep=0),
is only possible after coercion to the floating representation
(validate_matrix(0, True) yields 2). This is the control-flow effect (negation
runs vs raises) that `test_huber_bool` observes; no value-level postcondition
can witness it because the negated VALUES are identical whether or not the
negation raises.

The value clause `negated(...)` is GROUNDED in the input (a fully-unfolded
structural fold over row_values), NOT an opaque answer-key oracle, so there is no
"wrong echo" of an oracle to build (see UNGROUNDED-ORACLE note in assessment).
The token is the discriminator instead.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13328"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl region body (between the # impl-start / # impl-end
# markers). All variants edit ONLY this text, guaranteeing same_spec.
_GOLD_IMPL = """    # Validation: request a floating representation so that the subsequent
    # negation is well-defined regardless of the input representation.
    rep = validate_matrix(input_rep, True)
    result = negate_rows(input_rep, rep, row_values)
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Build a full model.py with the impl region body replaced by `new_impl`.
    Edits ONLY inside # impl-start/# impl-end => same_spec preserved."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness) ---------------------------------------
    # Structurally-different but CORRECT: an explicit branch that ALWAYS
    # requests floating (both arms request floating; the validated rep is
    # therefore always REP_FLOATING=2, so supports_negation holds), threads the
    # GENUINE input_rep into negate_rows, and returns its output. No loop / no
    # fold induction needed (negate_rows hands back negated(...) directly), so
    # this does NOT trip the front-recursive-fold positive-control hazard. It
    # keeps every gold obligation: the genuine input_rep flows to the token, the
    # value comes straight from negate_rows. Must VERIFY (else SPEC-TOO-STRONG).
    {
        "id": "pos-control-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    # Structurally different: pick the floating request via an\n"
            "    # explicit branch on input_rep; every arm requests floating, so\n"
            "    # the validated representation always supports negation.\n"
            "    if input_rep == 0:\n"
            "        rep = validate_matrix(input_rep, True)\n"
            "    else:\n"
            "        rep = validate_matrix(input_rep, True)\n"
            "    out = negate_rows(input_rep, rep, row_values)\n"
            "    return out"
        ),
        "rationale": "a correct, structurally-different impl (branch reshape, "
                     "always requests floating, threads genuine input_rep) must "
                     "verify; else the spec is SPEC-TOO-STRONG. No fold lemma is "
                     "needed (negate_rows returns negated(...) directly).",
    },

    # -- ADMISSIBILITY -------------------------------------------------------
    # The gold impl, with an Assert that the precondition admits a normal
    # F2P-shaped input: the LOGICAL representation (input_rep=0) — exactly the
    # bool X of test_huber_bool — is in-domain (0 <= 0 <= 2). The Assert sits
    # before the gold body and must hold for the call to proceed. Must VERIFY
    # (else PRECOND-TOO-STRONG: the precondition would reject the very input the
    # F2P test supplies).
    {
        "id": "admiss-logical-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    # The F2P input (bool X) is the logical representation, tag 0,\n"
            "    # and must lie in the precondition's domain.\n"
            "    Assert(0 <= input_rep and input_rep <= 2)\n"
            "    rep = validate_matrix(input_rep, True)\n"
            "    result = negate_rows(input_rep, rep, row_values)\n"
            "    return result"
        ),
        "rationale": "the precondition must admit the logical (bool) input the "
                     "F2P test_huber_bool supplies; the Assert is provable from "
                     "Requires(0 <= input_rep <= 2). Else PRECOND-TOO-STRONG.",
    },

    # -- FRAME-MUTATION (MANDATORY: row_values is Acc(...,1/2) read-only) -----
    # Rival WRITES to the half-permission read-only input before returning the
    # correct value+token. Keeps all gold invariants verbatim so the rejection
    # is attributable to the write. Must be REJECTED for INSUFFICIENT PERMISSION
    # (only 1/2 permission held; append needs full). A byte-fuzzer never tries
    # mutating the input — this is the project's #1 weakness class.
    {
        "id": "frame-mutation-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    rep = validate_matrix(input_rep, True)\n"
            "    result = negate_rows(input_rep, rep, row_values)\n"
            "    # Adversarial write to the READ-ONLY input (only 1/2 perm held).\n"
            "    row_values.append(0)\n"
            "    return result"
        ),
        "refinement": "a real fit that MUTATES the validated feature slice X "
                      "(appending a row) corrupts the gradient computation and "
                      "diverges from gold on the P2P numeric tests "
                      "(test_huber_gradient / test_huber_equals_lr...); it would "
                      "not resolve. The model forbids it structurally.",
        "rationale": "row_values is Acc(list_pred(row_values), 1/2) — read-only. "
                     "`append` needs full permission; Nagini rejects for "
                     "INSUFFICIENT PERMISSION. The rejection comes from the "
                     "permission system, not a value clause.",
    },

    # -- CONTROL-FLOW-EFFECT: inline negate, never reach negate_rows ---------
    # Computes the correct negated value WITHOUT calling negate_rows (uses the
    # @Pure `negated` via a typed local — value clause satisfied), but never
    # obtains the token. Cannot Fold negation_performed (body-less abstract
    # predicate). Must be REJECTED for "insufficient permission to access
    # negation_performed(input_rep, row_values)". This is the value-invisible discriminator:
    # the negation step is mandatory and non-bypassable.
    {
        "id": "cfe-inline-no-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Produce the correct value WITHOUT running the negation step\n"
            "    # (no negate_rows call), so the capability token is never granted.\n"
            "    out = negated(ToSeq(row_values))  # type: PSeq[int]\n"
            "    res = list(out)  # type: List[int]\n"
            "    return res"
        ),
        "refinement": "this mirrors the pre-fix hole: an impl that inlines the "
                      "numpy negation over an already-validated slice WITHOUT "
                      "the new dtype request leaves a bool X as bool, so the "
                      "real `-X` RAISES TypeError on test_huber_bool — it does "
                      "NOT resolve. The model rejects it for the missing token.",
        "rationale": "the postcondition requires negation_performed(input_rep, row_values); "
                     "the only producer is negate_rows; the body-less predicate "
                     "cannot be Folded. Rejection = insufficient permission to "
                     "access negation_performed(input_rep, row_values).",
    },

    # -- PREPATCH-ROUTE: route through negate_rows but DON'T request floating -
    # The G-DIFF discriminator. validated_rep(input_rep, False) preserves the
    # logical input as logical (rep=0), so supports_negation(0)=False and the
    # precondition of negate_rows is unsatisfiable for the logical input. Must
    # be REJECTED on supports_negation(rep) — the verification-level image of
    # the runtime TypeError. This is the byte-for-byte pre-patch behaviour
    # (model_prepatch.py).
    {
        "id": "prepatch-no-floating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Pre-patch routing: validate WITHOUT requesting floating, so a\n"
            "    # logical input stays logical and negation is undefined for it.\n"
            "    rep = validate_matrix(input_rep, False)\n"
            "    result = negate_rows(input_rep, rep, row_values)\n"
            "    return result"
        ),
        "refinement": "this IS the pre-patch fit (check_X_y without "
                      "dtype=[np.float64, np.float32]); a bool X stays bool and "
                      "`-axis0_safe_slice(X, ...)` raises TypeError — "
                      "test_huber_bool FAILS. It does not resolve.",
        "rationale": "negate_rows Requires(supports_negation(rep)); for the "
                     "logical input rep=validated_rep(0,False)=0 and "
                     "supports_negation(0)=False, so the precondition fails. "
                     "Rejection comes from the negate_rows precondition.",
    },

    # -- FORGE-TOKEN via a constant input_rep --------------------------------
    # Routes through negate_rows (always floating, value clause OK) but passes a
    # CONSTANT input_rep=1 so it earns negation_performed(1, row_values). The caller's
    # postcondition needs negation_performed(input_rep, row_values) for the ACTUAL input_rep;
    # for input_rep != 1 the token is for the wrong input. Must be REJECTED:
    # the token names the input it actually serviced and cannot be relabelled.
    {
        "id": "forge-token-const-rep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Earn a token for a CONSTANT representation (1), not the real one.\n"
            "    rep = validate_matrix(1, True)\n"
            "    result = negate_rows(1, rep, row_values)\n"
            "    return result"
        ),
        "refinement": "passing a fixed dtype tag to the negation evidence means "
                      "the negation that ran did not certify the actual input "
                      "(e.g. the logical input). A faithful impl that only ever "
                      "proves success for input_rep=1 leaves the bool X path "
                      "un-coerced — test_huber_bool still raises. Does not resolve.",
        "rationale": "negate_rows grants negation_performed(input_rep, row_values) for the "
                     "input_rep ARGUMENT passed; here that is the constant 1, so "
                     "the caller only holds negation_performed(1, row_values). The "
                     "postcondition Ensures(negation_performed(input_rep, row_values)) fails "
                     "whenever input_rep != 1.",
    },

    # -- PARTIAL-DOMAIN: correct except on the logical sub-domain ------------
    # Coerces+negates correctly for non-logical inputs (input_rep != 0) but
    # takes the inline shortcut on the logical sub-domain (input_rep == 0) —
    # exactly the input test_huber_bool exercises. The logical branch produces
    # the right value but no token. Must be REJECTED: the token obligation is
    # universally quantified over input_rep, so the one bad sub-domain fails it.
    {
        "id": "partial-skip-logical",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    if input_rep == 0:\n"
            "        # Shortcut on the logical sub-domain: correct value, NO token.\n"
            "        out = negated(ToSeq(row_values))  # type: PSeq[int]\n"
            "        res = list(out)  # type: List[int]\n"
            "        return res\n"
            "    rep = validate_matrix(input_rep, True)\n"
            "    result = negate_rows(input_rep, rep, row_values)\n"
            "    return result"
        ),
        "refinement": "an impl that only requests the float dtype for non-bool "
                      "inputs but inlines the negation for bool leaves the bool "
                      "X path raising at `-X` — test_huber_bool (the sole F2P) "
                      "FAILS on exactly that sub-domain. Does not resolve.",
        "rationale": "the logical branch returns without negation_performed(0, row_values); "
                     "the postcondition Ensures(negation_performed(input_rep, row_values)) "
                     "is not discharged on the input_rep==0 path. Rejection = "
                     "insufficient permission to the token on the logical branch.",
    },

    # -- IDENTITY: return the rows unnegated (cheap supporting near-miss) -----
    # Returns row_values unchanged. Fails the value clause
    # ToSeq(Result())==negated(...) AND the token. Cheap supporting case; still
    # carries a refinement.
    {
        "id": "identity-unnegated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Identity: return the (read-only) rows without negating.\n"
            "    res = list(row_values)  # type: List[int]\n"
            "    return res"
        ),
        "refinement": "returning the slice unnegated is not the gradient "
                      "negation; the numeric P2P tests (test_huber_gradient, "
                      "test_huber_equals_lr_for_high_epsilon) compute the wrong "
                      "gradient and fail. Does not resolve.",
        "rationale": "fails ToSeq(Result())==negated(ToSeq(row_values)) (identity "
                     "!= element-wise negation unless all zero) AND the token "
                     "(no negate_rows). Rejection from the value postcondition.",
    },

    # -- FABRICATED-TAG: constant floating tag, NO validation call ------------
    # Skips validation entirely and hands negate_rows a hard-coded floating
    # tag (2). supports_negation(2) holds trivially, so without the matrix_rep
    # evidence token this shape would verify while refining to code that never
    # validates (the matrix keeps its input representation; on the logical
    # input the real negation raises). Must be REJECTED: negate_rows also
    # Requires(matrix_rep(input_rep, rep)) and the sole producer of that token
    # is validate_matrix, so a fabricated tag carries no evidence.
    {
        "id": "fabricated-const-floating-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Fabricate a floating tag without running validation.\n"
            "    result = negate_rows(input_rep, 2, row_values)\n"
            "    return result"
        ),
        "refinement": "an impl that skips the validation coercion and merely "
                      "ASSERTS the matrix is floating leaves a bool X as bool; "
                      "the real `-axis0_safe_slice(X, ...)` raises TypeError — "
                      "test_huber_bool FAILS. Does not resolve.",
        "rationale": "negate_rows Requires(matrix_rep(input_rep, rep)); the "
                     "body-less matrix_rep token cannot be Folded and its only "
                     "producer is validate_matrix, which was never called. "
                     "Rejection = insufficient permission to access "
                     "matrix_rep(input_rep, rep).",
    },

    # -- STALE-TAG: validate without floating, then claim a floating tag ------
    # Runs the pre-patch validation (no floating request) but hands negate_rows
    # the floating tag 2 anyway. The only matrix_rep token held is for the
    # PRESERVED representation validated_rep(input_rep, False) == input_rep,
    # which is not provably 2 for every admitted input (input_rep=0 in
    # particular). Must be REJECTED: the tag must match the representation the
    # matrix actually has.
    {
        "id": "stale-tag-after-no-floating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Validate WITHOUT the floating request, then claim floating.\n"
            "    rep = validate_matrix(input_rep, False)\n"
            "    result = negate_rows(input_rep, 2, row_values)\n"
            "    return result"
        ),
        "refinement": "the real pre-patch validation leaves a bool X as bool; "
                      "pretending downstream that it is floating does not stop "
                      "the real negation from raising on test_huber_bool. Does "
                      "not resolve.",
        "rationale": "the held token is matrix_rep(input_rep, "
                     "validated_rep(input_rep, False)) == matrix_rep(input_rep, "
                     "input_rep), which does not entail matrix_rep(input_rep, 2) "
                     "for input_rep != 2. Rejection = insufficient permission to "
                     "access matrix_rep(input_rep, rep) at the negate_rows call.",
    },

    # -- TOKEN-LAUNDER via a stand-in collection ------------------------------
    # Validates with the floating request (honest tag) but runs negate_rows on
    # an EMPTY dummy list, earning negation_performed(input_rep, dummy), and
    # computes the caller's value inline. The caller's postcondition demands
    # the token for its OWN row collection; the dummy token does not discharge
    # it. Must be REJECTED: the token binds the very rows it negated.
    {
        "id": "launder-token-dummy-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Earn the token on a stand-in collection, not the real rows.\n"
            "    rep = validate_matrix(input_rep, True)\n"
            "    dummy = []  # type: List[int]\n"
            "    _ = negate_rows(input_rep, rep, dummy)\n"
            "    out = negated(ToSeq(row_values))  # type: PSeq[int]\n"
            "    res = list(out)  # type: List[int]\n"
            "    return res"
        ),
        "refinement": "an impl whose (validated, coerced) negation runs on some "
                      "other array while the caller's own selected rows are "
                      "handled by an inline shortcut refines to code where the "
                      "REAL gradient negation on the caller's X never runs "
                      "coerced — on a bool X the real `-` raises. "
                      "test_huber_bool FAILS. Does not resolve.",
        "rationale": "negate_rows grants negation_performed(input_rep, dummy); "
                     "the caller's postcondition needs negation_performed("
                     "input_rep, row_values) and the token cannot be relabelled "
                     "to a different collection. Rejection = insufficient "
                     "permission to access negation_performed(input_rep, "
                     "row_values).",
    },

    # -- TOKEN-LAUNDER via a COPY of the rows ---------------------------------
    # Same shape but the stand-in is a value-equal COPY of row_values. The
    # token names the copy (a different collection), not the caller's own; the
    # postcondition is not discharged. Must be REJECTED.
    {
        "id": "launder-token-copied-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Earn the token on a copy of the rows, not the rows themselves.\n"
            "    rep = validate_matrix(input_rep, True)\n"
            "    dup = list(row_values)  # type: List[int]\n"
            "    _ = negate_rows(input_rep, rep, dup)\n"
            "    out = negated(ToSeq(row_values))  # type: PSeq[int]\n"
            "    res = list(out)  # type: List[int]\n"
            "    return res"
        ),
        "refinement": "negating a copy while the caller's own selected rows are "
                      "computed by an inline shortcut leaves the real negation "
                      "of the caller's X un-exercised on the coerced path; on a "
                      "bool X the real `-` raises. test_huber_bool FAILS. Does "
                      "not resolve.",
        "rationale": "the token earned is negation_performed(input_rep, dup) "
                     "for the copy; the postcondition needs it for row_values "
                     "(the reference, not equal contents). Rejection = "
                     "insufficient permission to access negation_performed("
                     "input_rep, row_values).",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# Two A-consumed @ContractOnly axioms: `validate_matrix` (the validation step;
# its value clause pins Result() == validated_rep and it grants the matrix_rep
# token, which has no runtime content beyond that value clause) and
# `negate_rows`, whose precondition/value clauses are grounded in three
# A-reference deep models (validated_rep, supports_negation, negated) validated
# against the REAL sklearn check_array + numpy negation. The remaining clauses
# are the body-less capability tokens (no runtime content). The probes below
# cover BOTH axioms (they share the same deep models: validate_matrix's entire
# runtime content IS validated_rep, exercised against the real check_array
# below). They RUN the real callees in Docker (never scrape
# source) and (1) assert each deep model == the real callee over the axiom's
# Requires domain incl. boundary/sentinel inputs [axiom-soundness], and (2)
# assert every callee-input the MODEL can reach lies in the axiom's Requires
# domain [axiom-containment]. apply_gold=True so check_array runs under the
# post-gold library (the dtype-selection logic check_array implements is
# unchanged by the patch; only the argument the caller passes changed).

_SOUNDNESS_PROBE = r'''
import sys

import numpy as np
from sklearn.utils import check_array

REP_LOGICAL, REP_INTEGRAL, REP_FLOATING = 0, 1, 2

# input representation tag -> a representative constructor dtype + the boundary
# dtypes within that representation that check_array / numpy negation must agree
# on. We fuzz the WHOLE representation class, not one dtype, to try to make the
# real callee DISAGREE with the model at a boundary.
_REP_DTYPES = {
    REP_LOGICAL:  [np.bool_],
    REP_INTEGRAL: [np.int8, np.int16, np.int32, np.int64,
                   np.uint8, np.uint16, np.uint32, np.uint64],
    REP_FLOATING: [np.float16, np.float32, np.float64],
}


def model_supports_negation(rep):
    return rep != REP_LOGICAL


def model_validated_rep(input_rep, request_floating):
    return REP_FLOATING if request_floating else input_rep


def model_negated(vals):
    return [-v for v in vals]


def kind_to_rep(kind):
    if kind == "b":
        return REP_LOGICAL
    if kind in ("i", "u"):
        return REP_INTEGRAL
    if kind == "f":
        return REP_FLOATING
    raise AssertionError("unexpected dtype kind %r" % kind)


def real_validated_rep(dtype_in, request_floating):
    X = np.array([[1, 0], [0, 1], [1, 1]], dtype=dtype_in)
    if request_floating:
        v = check_array(X, copy=False, accept_sparse=["csr"],
                        dtype=[np.float64, np.float32])
    else:
        v = check_array(X, copy=False, accept_sparse=["csr"])
    return kind_to_rep(v.dtype.kind)


def real_supports_negation(dtype_in):
    X = np.array([[1, 0], [0, 1]], dtype=dtype_in)
    try:
        (-X)
        return True
    except TypeError:
        return False


# (A-reference 1) validated_rep == real check_array over EVERY dtype in each
# representation class, both with and without the floating request.
for rep, dtypes in _REP_DTYPES.items():
    for dtype_in in dtypes:
        for request_floating in (False, True):
            m = model_validated_rep(rep, request_floating)
            r = real_validated_rep(dtype_in, request_floating)
            if m != r:
                print("UNSOUND validated_rep: dtype=%r rep=%d req=%s model=%d real=%d"
                      % (dtype_in, rep, request_floating, m, r))
                sys.exit(1)

# (A-reference 2) supports_negation == real numpy `-` definedness for every
# dtype in each representation class (the negate_rows precondition).
for rep, dtypes in _REP_DTYPES.items():
    for dtype_in in dtypes:
        m = model_supports_negation(rep)
        r = real_supports_negation(dtype_in)
        if m != r:
            print("UNSOUND supports_negation: dtype=%r rep=%d model=%s real=%s"
                  % (dtype_in, rep, m, r))
            sys.exit(1)

# (A-reference 3) negated == real numpy element-wise negation. Fuzz the float
# row-slice the gradient step actually negates, plus sentinels (empty, single,
# zeros, extremes).
import random
rng = random.Random(13328)
cases = [[], [0], [0, 0, 0], [-5, 5], [-1, 0, 1, 2, -2]]
for _ in range(5000):
    n = rng.randint(0, 16)
    cases.append([rng.randint(-50, 50) for _ in range(n)])
for vals in cases:
    Xf = np.array(vals, dtype=np.float64)
    real = [int(x) for x in list((-Xf).astype(np.int64))]
    if model_negated(vals) != real:
        print("UNSOUND negated on %r: model=%r real=%r"
              % (vals, model_negated(vals), real))
        sys.exit(1)

# (end-to-end / negate_rows axiom soundness) The capability token has no runtime
# content; its soundness reduces to its gating precondition supports_negation +
# the end-to-end control-flow claim. Under the CALLER's actual runtime config
# (always request floating, per fit_robust_regressor's impl), EVERY input
# representation -- including the logical (bool) of test_huber_bool -- validates
# to a representation that supports negation, so the negation RUNS (token is
# legitimately grantable). And the pre-patch routing (no floating request) on a
# logical input leaves it un-negatable (negation RAISES) -- so the token could
# NOT be granted there, i.e. the axiom never over-claims.
for rep, dtypes in _REP_DTYPES.items():
    for dtype_in in dtypes:
        patched_rep = real_validated_rep(dtype_in, True)
        if not real_supports_negation(_REP_DTYPES[patched_rep][0]):
            print("UNSOUND end-to-end: patched validation of %r -> rep %d does "
                  "not support negation" % (dtype_in, patched_rep))
            sys.exit(1)
# pre-patch logical input must be un-negatable (the reported bug reproduces)
prepatch_logical = real_validated_rep(np.bool_, False)
if real_supports_negation(_REP_DTYPES[prepatch_logical][0]):
    print("UNSOUND: pre-patch logical input was negatable; the bug would not "
          "reproduce, so the token's gating precondition would over-claim")
    sys.exit(1)

print("AXIOM-SOUND OK: validated_rep / supports_negation / negated == real "
      "sklearn check_array + numpy negation over all dtypes per representation "
      "x {request,no-request}, 5000+ negation fuzz + sentinels, and the "
      "end-to-end patched(grantable)/pre-patch(un-grantable) token control-flow.")
sys.exit(0)
'''


_CONTAINMENT_PROBE = r'''
import sys

import numpy as np
from sklearn.utils import check_array

REP_LOGICAL, REP_INTEGRAL, REP_FLOATING = 0, 1, 2
_REP_DTYPE = {REP_LOGICAL: np.bool_, REP_INTEGRAL: np.int64,
              REP_FLOATING: np.float64}


def model_validated_rep(input_rep, request_floating):
    return REP_FLOATING if request_floating else input_rep


def real_validated_rep(input_rep, request_floating):
    X = np.array([[1, 0], [0, 1], [1, 1]], dtype=_REP_DTYPE[input_rep])
    if request_floating:
        v = check_array(X, copy=False, accept_sparse=["csr"],
                        dtype=[np.float64, np.float32])
    else:
        v = check_array(X, copy=False, accept_sparse=["csr"])
    kind = v.dtype.kind
    return {"b": REP_LOGICAL, "i": REP_INTEGRAL, "u": REP_INTEGRAL,
            "f": REP_FLOATING}[kind]


def real_supports_negation(rep):
    X = np.array([[1, 0], [0, 1]], dtype=_REP_DTYPE[rep])
    try:
        (-X)
        return True
    except TypeError:
        return False


# CONTAINMENT: enumerate EXACTLY the (rep) inputs the MODEL can pass to the
# negate_rows axiom from fit_robust_regressor's control flow, and assert each is
# in the axiom's Requires domain `supports_negation(rep)`.
#
# fit_robust_regressor's impl computes `rep = validate_matrix(input_rep, True)`
# before EVERY negate_rows call. The precondition admits input_rep in {0,1,2}.
# So the reachable `rep` set is exactly { validated_rep(input_rep, True)
# : input_rep in {0,1,2} }. With request_floating=True that is {REP_FLOATING}.
reachable_reps = set()
for input_rep in (REP_LOGICAL, REP_INTEGRAL, REP_FLOATING):
    # mirror the model's call site (always requests floating)
    rep = model_validated_rep(input_rep, True)
    reachable_reps.add(rep)
    # cross-check the deep model against the real validator at this call site
    if rep != real_validated_rep(input_rep, True):
        print("model/real validated_rep disagree at caller site input_rep=%d "
              "(model=%d real=%d)" % (input_rep, rep,
                                       real_validated_rep(input_rep, True)))
        sys.exit(1)

print("reachable rep set passed by fit_robust_regressor to negate_rows:",
      sorted(reachable_reps))

# Every reachable rep must satisfy the axiom's Requires domain
# supports_negation(rep) -- confirmed against the REAL numpy `-`.
for rep in reachable_reps:
    if not real_supports_negation(rep):
        print("AXIOM-TOO-WEAK-FOR-CALLER: caller can reach rep=%d which is "
              "OUTSIDE negate_rows' Requires(supports_negation(rep)) domain "
              "(real numpy negation undefined there)" % rep)
        sys.exit(1)

# Sanity: the un-supported rep (logical) is NOT reachable from the model's
# always-floating call site -- it is exactly what the gold patch eliminates.
if REP_LOGICAL in reachable_reps:
    print("UNEXPECTED: logical rep reachable; model would hit the axiom "
          "precondition")
    sys.exit(1)

# Covering MORE than the caller reaches is SOUND, not a defect: the axiom's
# Requires(supports_negation(rep)) also admits REP_INTEGRAL, which the caller
# never produces under the floating request. That is fine (float-vs-int rule).
print("AXIOM-CONTAINMENT OK: every rep the model passes to negate_rows "
      "(== {REP_FLOATING}) lies in the axiom's Requires(supports_negation) "
      "domain; the un-supported logical rep is unreachable from the floating "
      "call site (exactly the gold fix).")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-negate-rows",
        "axiom": "negate_rows",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": "the negate_rows axiom's precondition/value clauses are "
                     "grounded in the deep models validated_rep / "
                     "supports_negation / negated; this probe runs the REAL "
                     "sklearn check_array + numpy negation over every dtype per "
                     "representation x {request,no-request} + 5000 negation fuzz "
                     "+ sentinels, and confirms the token's gating precondition "
                     "never over-claims (pre-patch logical is un-negatable). Any "
                     "real-callee disagreement => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-negate-rows",
        "axiom": "negate_rows",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": "fit_robust_regressor always computes rep = "
                     "validate_matrix(input_rep, True), whose value clause pins "
                     "rep = validated_rep(input_rep, True) = REP_FLOATING, "
                     "before each negate_rows call, so the only callee-reachable "
                     "rep is REP_FLOATING, which satisfies the axiom's "
                     "Requires(supports_negation(rep)) (the matrix_rep evidence "
                     "for it is granted by that same validate_matrix call). A "
                     "reachable rep outside that domain => "
                     "AXIOM-TOO-WEAK-FOR-CALLER; covering the also-supported "
                     "integral rep is sound, not a defect.",
    },
    {
        "id": "ax-sound-validate-matrix",
        "axiom": "validate_matrix",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": "validate_matrix's entire runtime content is its value "
                     "clause Result() == validated_rep(input_rep, "
                     "request_floating); the matrix_rep token it grants names "
                     "exactly that value and has no further runtime content. "
                     "The soundness probe exercises validated_rep against the "
                     "REAL sklearn check_array over every dtype per "
                     "representation x {request,no-request}, so any way the "
                     "real validator could produce a representation the axiom "
                     "does not claim (or vice versa) => AXIOM-UNSOUND.",
    },
]

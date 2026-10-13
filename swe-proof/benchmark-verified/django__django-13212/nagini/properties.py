"""properties.py — PBT falsification battery for django__django-13212.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap) and are checked by
Nagini verify + markers.same_spec. There are NO @ContractOnly axioms and NO
A-reference deep models that are *consumed as axioms* in this bundle
(meta.axioms == []; the param-map construction is the behaviour under
specification and is spelled out deeply in the impl region; the unchanged
%-interpolation rendering mechanism is validated by axiom_check.py / G-AX as a
model-fidelity reference, not an over-approximation of a callee with a
Requires domain to contain). So AXIOM_TESTS = [].

DEFENDED SURFACE (why these cases and not byte-fuzz):

  build_invalid_params(value: List[int]) -> Dict[int, PSeq[int]]
    Read-only input value at Acc(list_pred(value), 1/2). Postcondition pins:
      (I1) placeholder_value() in Result()                 -- value key present
      (I2) Result()[placeholder_value()] == ToSeq(value)   -- bound to the input
      (I3) Forall k: k in Result() => k == placeholder_value()
                                                           -- NOTHING else bound
    This models the gold params={'value': value} added at the bare-rejection
    raise sites (validators.py:51,103,... and the NaN DecimalValidator raise
    routed in via the DecimalField.validate removal).

  build_limit_params(value: List[int], limit: List[int]) -> Dict[int, PSeq[int]]
    Read-only inputs value AND limit, each at Acc(list_pred(.), 1/2).
    Postcondition pins:
      (L1) placeholder_limit() in Result()                 -- max key PRESERVED
      (L2) Result()[placeholder_limit()] == ToSeq(limit)   -- still renders limit
      (L3) placeholder_value() in Result()                 -- value key ADDED
      (L4) Result()[placeholder_value()] == ToSeq(value)   -- bound to the input
      (L5) Forall k: k in Result() => k == limit or k == value
                                                           -- EXACTLY those two
    This models the gold params={'max': ..., 'value': value} (and structurally
    the FileExtensionValidator raise), where 'max' is PRESERVED and 'value' is
    ADDED.

  decimal_reject_params(finite: bool, value: List[int]) -> Dict[int, PSeq[int]]
    Read-only input value at Acc(list_pred(value), 1/2); a bool finite carrier.
    Models the DecimalField.validate control-flow deletion (the duplicate
    paramless not-finite screen removed in django/forms/fields.py:350-358) so a
    not-finite decimal candidate is no longer short-circuited but flows to the
    value-binding bare rejection (DecimalValidator, validators.py:440-441).
    Postcondition pins:
      (D1) placeholder_value() in Result()                 -- value key present
      (D2) Result()[placeholder_value()] == ToSeq(value)   -- bound to the input,
                                                              REGARDLESS of finite
      (D3) Forall k: k in Result() => k == placeholder_value()
                                                           -- the outcome is
                                                              EXACTLY the
                                                              bare-rejection
                                                              map (nothing
                                                              else), REGARDLESS
                                                              of finite
    The decisive pin is D1/D2 under not finite: the prepatch that keeps the
    duplicate screen (returns {} for a not-finite candidate) fails D1. The
    closure D3 is unconditional (not guarded on `not finite`): the modeled
    raise site produces exactly {'value': value} for ANY candidate reaching
    it, so a finite-branch impl that smuggles in a spurious extra binding is
    rejected too.

  READ-ONLY INPUTS => frame-mutation is MANDATORY. All three functions hold their
  list inputs at fractional permission Acc(list_pred(.), 1/2). A rival that WRITES
  into value/limit (e.g. value.append(...)) -- a way a real impl might try to
  "produce" the rendered string by side-effecting the input -- must be REJECTED
  for INSUFFICIENT PERMISSION (1/2 < 1 needed to mutate). has_readonly_input =
  True; frame_mutation_included = True (three such cases, one per function).

  UNGROUNDED-ORACLE: there is NO opaque answer-key @Pure to echo. The two pure
  helpers placeholder_value()/placeholder_limit() are CONSTANT NAME TOKENS
  (0 and 1), not oracles over the input; the load-bearing pins
  Result()[placeholder_value()] == ToSeq(value) are GROUNDED in the argument and
  fully unfolded (ToSeq(value) is a direct function of value). There is no
  materialize(oracle(x)) a wrong impl could echo to verify vacuously. Per
  directive 2 we therefore include honest cheapest-/reshaped-correct positive
  controls instead, and attack the binding pins via wrong-value / dropped-key /
  spurious-key uniqueness rivals.

  CONTROL-FLOW-EFFECT: N/A. Both functions are pure dict constructors with a
  single return path and no raise / side-effect mode difference; the value
  abstraction (the produced Dict's membership + per-key contents) is total over
  the behaviour. There is no raise/return-mode the abstraction drops, so no
  capability-token discriminator is needed (omitted with justification).

  The genuine reasoned attacks are: (a) frame mutation of the read-only inputs;
  (b) the value placeholder bound to the WRONG string (renders the wrong text);
  (c) build_limit_params DROPPING the preserved limit binding (breaks the
  default %(max)s message); (d) a SPURIOUS extra binding (the "binds nothing
  else" / "exactly these two" closure). Each carries its refinement argument.
"""
from pathlib import Path

INSTANCE = "django__django-13212"
FLOAT_ENCODING = None  # meta.float_encoding is null; integer code-point carrier

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors: the two gold impl regions, each a unique substring, so every variant
# edits ONLY inside its own # impl-start .. # impl-end block (guarantees
# same_spec against the frozen model.py).
# ---------------------------------------------------------------------------

_GOLD_INVALID = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    return params"""

_GOLD_LIMIT = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_limit()] = ToSeq(limit)
    params[placeholder_value()] = ToSeq(value)
    return params"""

_GOLD_DECIMAL = """    return build_invalid_params(value)"""


def _invalid(new):
    return _swap(_BASE, _GOLD_INVALID, new)


def _limit(new):
    return _swap(_BASE, _GOLD_LIMIT, new)


def _decimal(new):
    return _swap(_BASE, _GOLD_DECIMAL, new)


# === POSITIVE CONTROLS (soundness — must verify) ===========================

# build_invalid_params: bind ToSeq(value) through an intermediate typed local
# (local-variable reshape). Same value, different executable shape; keeps the
# single return path and all postcondition obligations (I1/I2/I3 still hold:
# rendered == ToSeq(value), only the value key present). Must verify; if not,
# SPEC-TOO-STRONG.
_POS_INVALID = """    rendered = ToSeq(value)  # type: PSeq[int]
    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = rendered
    return params"""

# build_limit_params: REORDER the two assignments -- add the value binding
# FIRST, then the (preserved) limit binding. Identical final mapping, different
# insertion order. Keeps L1..L5. Branch/statement reorder, not a fold-direction
# flip, so no f(a+b) lemma is needed (directive 3 avoided). Must verify.
_POS_LIMIT_REORDER = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    params[placeholder_limit()] = ToSeq(limit)
    return params"""


# === ADMISSIBILITY (precondition not too strong — must verify) =============

# Inside build_invalid_params' impl: after building the gold mapping, assert the
# input is STILL readable under the retained 1/2 permission (len(value) >= 0)
# and that the postcondition target is non-vacuously establishable on this
# in-domain input (placeholder_value() in params and the binding equals
# ToSeq(value)). This confirms the Requires Acc(list_pred(value),1/2) admits a
# normal F2P-shaped input AND that the postcondition is satisfiable for it (not
# a vacuously-False precondition). Must verify; else PRECOND-TOO-STRONG.
_ADMISS_INVALID = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    # admissibility witness: the half-permission input is still readable and the
    # postcondition is establishable on it (non-vacuous Requires).
    Assert(len(value) >= 0)
    Assert(placeholder_value() in params)
    Assert(params[placeholder_value()] == ToSeq(value))
    return params"""


# === FRAME-MUTATION rivals (MANDATORY — must be REJECTED for permission) ====

# build_invalid_params: WRITE into the read-only input value (append) before
# building the mapping. Gold postcondition pins kept verbatim, so the rejection
# is attributable to the WRITE: value is held at Acc(list_pred(value),1/2) and a
# mutation needs full permission. Must REJECT for insufficient permission.
_FRAME_INVALID = """    value.append(0)
    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    return params"""

# build_limit_params: WRITE into the read-only input limit (append) before
# building the mapping. Same: limit is Acc(list_pred(limit),1/2); a write needs
# full permission. Must REJECT for insufficient permission.
_FRAME_LIMIT = """    limit.append(0)
    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_limit()] = ToSeq(limit)
    params[placeholder_value()] = ToSeq(value)
    return params"""


# === UNIQUENESS / PARTIAL-DOMAIN rivals (must be REJECTED) =================

# build_invalid_params: bind the value placeholder to the WRONG string -- here
# the empty sequence instead of ToSeq(value). Membership (I1) and the closure
# (I3) still hold; only the per-key content pin (I2) is violated.
_WRONG_INVALID_EMPTY = """    empty = PSeq()  # type: PSeq[int]
    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = empty
    return params"""

# build_invalid_params: bind a SPURIOUS extra key (placeholder_limit()) in
# addition to the correct value binding. I1 and I2 hold; the closure clause
# (I3) "binds nothing other than the value placeholder" is violated.
_SPURIOUS_INVALID = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    params[placeholder_limit()] = ToSeq(value)
    return params"""

# build_limit_params: DROP the preserved limit binding -- bind ONLY the value
# placeholder (the dual of the gold change: replace {'max':...} by {'value':...}
# instead of adding 'value' to it). L3/L4/L5 hold; the preservation pins
# L1 (placeholder_limit() in Result()) / L2 fail.
_DROP_LIMIT = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    return params"""

# build_limit_params: SWAP the value binding to render the LIMIT instead of the
# offending input (Result()[placeholder_value()] == ToSeq(limit)). L1/L2/L3/L5
# hold; the value-content pin L4 (== ToSeq(value)) fails.
_SWAP_LIMIT = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_limit()] = ToSeq(limit)
    params[placeholder_value()] = ToSeq(limit)
    return params"""

# decimal_reject_params: POSITIVE control -- build the bare-rejection map inline
# (the value binding and nothing else) instead of delegating to
# build_invalid_params. Identical produced map on BOTH finite branches; single
# return path. Keeps D1/D2/D3. Must verify; else SPEC-TOO-STRONG (the
# postcondition would reject an equivalent correct, non-delegating construction).
_POS_DECIMAL_INLINE = """    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = ToSeq(value)
    return params"""

# decimal_reject_params: the PRE-PATCH bug -- the duplicate not-finite screen is
# kept, so a not-finite candidate (finite False) is short-circuited with a
# paramless (empty) mapping before reaching the value-binding rejection. The
# value is dropped from the report. D1 (placeholder_value() in Result()) fails
# under not finite. This is the dual of model_prepatch_3.py at the PBT layer.
_SCREEN_DECIMAL = """    if not finite:
        empty = {}  # type: Dict[int, PSeq[int]]
        return empty
    return build_invalid_params(value)"""

# decimal_reject_params: on the FINITE branch, add a SPURIOUS extra binding
# (the limit placeholder) on top of the correct value binding. D1/D2 hold on
# both branches and the not-finite outcome is the exact bare map; only the
# unconditional closure D3 is violated (on finite inputs). This is exactly the
# wrong-impl shape a finiteness-guarded closure would have admitted.
_SPURIOUS_FINITE_DECIMAL = """    if finite:
        params = build_invalid_params(value)
        params[placeholder_limit()] = ToSeq(value)
        return params
    return build_invalid_params(value)"""

# decimal_reject_params: bind the value placeholder to the WRONG string (empty
# sequence) instead of the offending input. D1/D3 hold; only the per-key content
# pin D2 (== ToSeq(value)) is violated -- a custom '%(value)s' would render the
# empty string for a rejected decimal, not str(value).
_WRONG_DECIMAL_EMPTY = """    empty = PSeq()  # type: PSeq[int]
    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_value()] = empty
    return params"""

# decimal_reject_params: WRITE into the read-only input value before building the
# map (frame mutation). Gold pins kept; rejection attributable to the write
# (value held at Acc(list_pred(value),1/2); append needs full permission).
_FRAME_DECIMAL = """    value.append(0)
    return build_invalid_params(value)"""


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-invalid-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _invalid(_POS_INVALID),
        "rationale": (
            "structurally-different CORRECT impl of build_invalid_params: the "
            "value binding is routed through an intermediate typed local "
            "(rendered = ToSeq(value)). Identical produced mapping, single "
            "return path; all postcondition obligations I1/I2/I3 still hold. "
            "Must verify -- else SPEC-TOO-STRONG (the postcondition would reject "
            "an equivalent correct construction)."
        ),
    },
    {
        "id": "pos-limit-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _limit(_POS_LIMIT_REORDER),
        "rationale": (
            "structurally-different CORRECT impl of build_limit_params: the value "
            "binding is added BEFORE the (preserved) limit binding -- a statement "
            "reorder, identical final two-entry mapping. Keeps L1..L5. A reorder "
            "(not a fold-direction flip), so no f(a+b) lemma is needed "
            "(directive 3). Must verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-invalid-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _invalid(_ADMISS_INVALID),
        "rationale": (
            "admissibility: after building the gold mapping, asserts the "
            "half-permission read-only input is still readable (len(value) >= 0) "
            "and the postcondition is non-vacuously establishable on this "
            "in-domain input (value key present, bound to ToSeq(value)). Confirms "
            "Requires Acc(list_pred(value),1/2) admits a normal F2P-shaped value "
            "(else PRECOND-TOO-STRONG / a vacuously-False precondition). The gold "
            "construction is intact, so the postcondition still verifies. Must "
            "verify."
        ),
    },
    # ----- frame-mutation rivals (MANDATORY — must be rejected) -----------
    {
        "id": "frame-mutate-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _invalid(_FRAME_INVALID),
        "refinement": (
            "this rival WRITES into the offending input itself (value.append(0)) "
            "before building the map. A faithful real patch that mutated the "
            "submitted form value during validation would CORRUPT the value being "
            "validated (and the value subsequently rendered) -- the F2P "
            "test_value_placeholder_with_char_field asserts form.errors renders "
            "EXACTLY str(value), so an impl that appends to value renders the "
            "wrong, mutated string and does NOT resolve. Moreover the gold patch "
            "does no such mutation; it only constructs params={'value': value}. "
            "verify-but-not-resolve if it slipped through."
        ),
        "rationale": (
            "rejected by the PERMISSION SYSTEM: value is held at "
            "Acc(list_pred(value), 1/2); value.append(...) needs FULL list_pred "
            "permission, which the precondition does not grant. Insufficient "
            "permission => the variant cannot verify. (This is the #1 weakness "
            "class; the gold invariants are kept verbatim so the rejection is "
            "attributable to the write, not to a postcondition change.)"
        ),
    },
    {
        "id": "frame-mutate-limit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _limit(_FRAME_LIMIT),
        "refinement": (
            "build_limit_params variant that WRITES into the read-only limit "
            "(limit.append(0)). A faithful real patch mutating self.max_digits' "
            "rendered carrier would change the %(max)s text the bound-limit "
            "message surfaces (axiom_check.py asserts %(max)s still renders the "
            "limit), so it would not match the F2P/PASS_TO_PASS expectations and "
            "would not resolve. The gold patch performs no mutation. "
            "verify-but-not-resolve if it slipped through."
        ),
        "rationale": (
            "rejected by the PERMISSION SYSTEM: limit is held at "
            "Acc(list_pred(limit), 1/2); limit.append(...) needs full permission. "
            "Insufficient permission => cannot verify. Gold pins kept verbatim so "
            "the rejection is attributable to the write."
        ),
    },
    # ----- uniqueness / partial-domain rivals (must be rejected) ----------
    {
        "id": "weak-invalid-empty-binding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _invalid(_WRONG_INVALID_EMPTY),
        "refinement": (
            "binds the value placeholder to the EMPTY string instead of the "
            "offending input. A faithful real patch params={'value': ''} would "
            "render the %(value)s template to the empty string, not str(value) -- "
            "FAIL_TO_PASS test_value_placeholder_with_char_field / "
            "_with_integer_field / _with_null_character all assert form.errors "
            "renders the ACTUAL submitted value, so an empty binding fails them "
            "and does NOT resolve. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause I2: "
            "Result()[placeholder_value()] == ToSeq(value). The rival binds "
            "PSeq() (empty), which differs from ToSeq(value) for any non-empty "
            "input (every F2P value is non-empty). Membership (I1) and the closure "
            "(I3) still hold, so the rejection is precisely the value-content pin."
        ),
    },
    {
        "id": "weak-invalid-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _invalid(_SPURIOUS_INVALID),
        "refinement": (
            "adds a SPURIOUS extra binding (the limit placeholder) on top of the "
            "correct value binding -- the bare rejection is NOT supposed to "
            "publish any other parameter. A faithful real patch "
            "params={'value': value, 'max': value} injects a stray 'max' into "
            "EVERY bare-rejection error.params (RegexValidator, EmailValidator, "
            "the IPv* validators, ProhibitNullCharactersValidator, ...). That "
            "diverges from the gold params={'value': value}: any consumer/default "
            "message that does not expect '%(max)s' now carries a spurious key, "
            "and the produced params no longer equals the gold patch's on the "
            "tested inputs, so the artifact is not the gold patch and is not "
            "guaranteed to resolve. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by the closure clause I3: "
            "Forall k: k in Result() => k == placeholder_value(). The rival also "
            "binds placeholder_limit(), so there exists k = placeholder_limit() in "
            "Result() with k != placeholder_value(), violating I3. The 'binds "
            "nothing else' clause is exactly the uniqueness defense against "
            "spurious bindings."
        ),
    },
    {
        "id": "weak-limit-drop-max",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _limit(_DROP_LIMIT),
        "refinement": (
            "the dual of the gold change: instead of ADDING 'value' to the "
            "existing {'max': ...}, this REPLACES the map with {'value': value}, "
            "DROPPING the preserved limit binding. A faithful real patch "
            "params={'value': value} (no 'max') at the DecimalValidator magnitude "
            "raises breaks the DEFAULT messages 'Ensure that there are no more "
            "than %(max)s digit(s)...': rendering them raises KeyError('max') / "
            "leaves the placeholder, so PASS_TO_PASS decimal-magnitude tests that "
            "observe the default %(max)s message regress and the patch does NOT "
            "resolve. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clauses L1/L2: placeholder_limit() in "
            "Result() and Result()[placeholder_limit()] == ToSeq(limit). The rival "
            "never binds placeholder_limit(), so L1 fails (the key is absent). "
            "Rejection comes from the limit-PRESERVATION pins -- exactly the "
            "'preserve the pre-existing binding' guarantee."
        ),
    },
    {
        "id": "weak-limit-value-renders-limit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _limit(_SWAP_LIMIT),
        "refinement": (
            "binds the value placeholder to the LIMIT's string instead of the "
            "offending input (Result()[placeholder_value()] == ToSeq(limit)). A "
            "faithful real patch params={'max': L, 'value': L} would make a "
            "custom '%(value)s' template render the MAX (e.g. '8') rather than the "
            "rejected decimal -- FAIL_TO_PASS test_value_placeholder_with_decimal_"
            "field asserts the rendered value is the offending input, so it fails "
            "and does NOT resolve. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause L4: "
            "Result()[placeholder_value()] == ToSeq(value). The rival binds "
            "ToSeq(limit), which differs from ToSeq(value) whenever value != limit "
            "(true for every F2P decimal case). L1/L2/L3/L5 still hold, isolating "
            "the rejection to the value-content pin."
        ),
    },
    # ----- decimal control-flow (the DecimalField.validate deletion) ------
    {
        "id": "pos-decimal-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _decimal(_POS_DECIMAL_INLINE),
        "rationale": (
            "structurally-different CORRECT impl of decimal_reject_params: builds "
            "the bare-rejection map INLINE (value key, nothing else) instead of "
            "delegating to build_invalid_params. Identical produced map on both "
            "finite branches; single return path; D1/D2/D3 all hold. Must verify "
            "-- else SPEC-TOO-STRONG (the postcondition would reject an equivalent "
            "correct, non-delegating construction)."
        ),
    },
    {
        "id": "decimal-keeps-notfinite-screen",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _decimal(_SCREEN_DECIMAL),
        "refinement": (
            "the PRE-PATCH behaviour: keeps the duplicate not-finite screen so a "
            "not-finite decimal candidate (finite False) is short-circuited with a "
            "paramless (empty) rejection before it can reach the value-binding "
            "bare rejection. A real patch that left DecimalField.validate in place "
            "drops the offending input from a NaN/inf error -- FAIL_TO_PASS "
            "test_value_placeholder_with_decimal_field's 'NaN' case asserts "
            "form.errors == {'field': ['NaN']}, which the literal '%(value)s' "
            "template cannot produce when params is empty, so it fails and does "
            "NOT resolve. verify-but-not-resolve. This is the exact control-flow "
            "deletion the widened scope pins (dual of model_prepatch_3.py)."
        ),
        "rationale": (
            "rejected by postcondition clause D1 under the not-finite branch: "
            "Ensures(placeholder_value() in Result()) must hold for ALL inputs, "
            "but for finite == False the rival returns the empty map, so "
            "placeholder_value() not in Result(). The unconditional value-binding "
            "guarantee is exactly what senses the surviving screen."
        ),
    },
    {
        "id": "weak-decimal-finite-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _decimal(_SPURIOUS_FINITE_DECIMAL),
        "refinement": (
            "on the FINITE branch, adds a SPURIOUS extra binding (the limit "
            "placeholder) on top of the correct value binding; the not-finite "
            "branch is the exact bare map. A faithful real patch would have to "
            "special-case a finite candidate at DecimalValidator's bare "
            "'invalid' rejection and raise params={'value': value, 'max': "
            "value} there -- injecting a stray 'max' into that error's params, "
            "diverging from the gold params={'value': value} at that raise "
            "site, so the artifact is not the gold patch and is not guaranteed "
            "to resolve. verify-but-not-resolve. This is exactly the wrong-impl "
            "shape a finiteness-GUARDED closure admitted (the G-PANEL-1 "
            "weakness witness); the unconditional closure now senses it."
        ),
        "rationale": (
            "rejected by the UNCONDITIONAL closure clause D3: "
            "Forall k: k in Result() => k == placeholder_value() must hold for "
            "ALL inputs, but for finite == True the rival also binds "
            "placeholder_limit(), violating D3. D1/D2 hold on both branches, "
            "isolating the rejection to the closure pin."
        ),
    },
    {
        "id": "weak-decimal-empty-binding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _decimal(_WRONG_DECIMAL_EMPTY),
        "refinement": (
            "binds the value placeholder to the EMPTY string instead of the "
            "rejected decimal candidate. A faithful real patch params={'value': ''} "
            "would render the '%(value)s' template to the empty string for a "
            "rejected decimal, not str(value) -- FAIL_TO_PASS "
            "test_value_placeholder_with_decimal_field asserts the ACTUAL value "
            "renders, so it fails and does NOT resolve. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause D2: "
            "Result()[placeholder_value()] == ToSeq(value). The rival binds PSeq() "
            "(empty), which differs from ToSeq(value) for any non-empty input "
            "(every F2P decimal value is non-empty). D1 and D3 still hold, so the "
            "rejection is precisely the value-content pin."
        ),
    },
    {
        "id": "frame-mutate-decimal-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _decimal(_FRAME_DECIMAL),
        "refinement": (
            "decimal_reject_params variant that WRITES into the read-only input "
            "value (value.append(0)) before building the map. A real patch that "
            "mutated the submitted decimal's rendered carrier during validation "
            "would render the wrong, corrupted string -- "
            "test_value_placeholder_with_decimal_field asserts form.errors renders "
            "EXACTLY str(value), so it would not resolve. The gold patch performs "
            "no mutation. verify-but-not-resolve if it slipped through."
        ),
        "rationale": (
            "rejected by the PERMISSION SYSTEM: value is held at "
            "Acc(list_pred(value), 1/2); value.append(...) needs FULL list_pred "
            "permission, which the precondition does not grant. Insufficient "
            "permission => cannot verify. Gold pins kept verbatim so the rejection "
            "is attributable to the write."
        ),
    },
]

# No @ContractOnly axioms and no consumed A-reference deep models with a callee
# Requires domain to contain (meta.axioms == []). The param-map construction is
# the behaviour under specification, modelled deeply in the impl region; the one
# UNCHANGED mechanism the model leans on (Python %-style named interpolation in
# ValidationError.__iter__) is validated against the real Django stack by
# axiom_check.py (G-AX) as a model-fidelity reference, not consumed as an axiom
# obligation -- there is no callee whose Ensures could be unsound here and no
# callee-input domain to contain. So AXIOM_TESTS = [].
AXIOM_TESTS = []

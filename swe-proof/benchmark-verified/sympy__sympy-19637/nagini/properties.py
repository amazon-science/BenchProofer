# properties.py — PBT falsification battery for sympy__sympy-19637.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-identically (region surgery edits ONLY inside the
# # impl-start / # impl-end region) and are checked by Nagini verify +
# markers.same_spec. Axiom cases are real-callee probes checked in Docker.
#
# Defended surface (read from model.py + refinement.md + the gold patch):
#   compute_processing_signal(entered: bool, key: Optional[bool]) -> bool
#   models the `hit` computation inside sympy.core.sympify.kernS. `entered` is
#   the outer guard ('(' in s and not quoted); `key` is the substitution key
#   `kern`, abstracted to Optional[bool]: key is None <-> kern was never bound
#   (no space survived the rewrite, so no substitution was performed); key is
#   not None <-> kern was created, and its boolean value is `kern in s`.
#
#   Precondition:  Requires(Implies(not entered, key is None))
#                  -- a key can only be created inside the entered transform, so
#                  an absent outer guard implies an absent key.
#
#   Postcondition pins TWO clauses:
#     (C1) Result() == expected_signal(entered, key)            [total]
#     (C2) Implies(key is None, not Result())                   [absent key -> false]
#   where expected_signal (the @Pure oracle, fully unfolded over the inputs) is
#     `if entered and key is not None: return key_member(key); return False`
#   and key_member(key) == key, with Requires(key is not None).
#
#   The load-bearing delta of the gold patch (move `hit = kern in s` INSIDE the
#   `if ' ' in s:` block, add `else: hit = False`) is that the key's membership
#   may be READ only when a key was actually created. In the model this is the
#   precondition `key is not None` of the @Pure accessor key_member: reading the
#   key's membership on the entered-but-no-key path (the F2P input) is the formal
#   face of the UnboundLocalError ('local variable kern referenced before
#   assignment'). The four admissible input classes are:
#       (False, None) -> False         (not entered)
#       (True,  None) -> False         (F2P bug path: entered, NO key created)
#       (True,  True) -> True          (entered, key created, kern in s)
#       (True,  False)-> False         (entered, key created, kern not in s)
#
# NOTE on frame-mutation (project directive 5 / pilot weakness class #1): there
# is NO read-only HEAP input here. Both parameters are Nagini value types
# (bool / Optional[bool]) passed by value — there is no Acc(x, 1/2) permission to
# overwrite, so the frame-mutation probe is VACUOUS for this instance (see
# 'assessment'). has_readonly_input is therefore False.
#
# NOTE on control-flow-effect (directive 4): the only "raise" in the real code
# (UnboundLocalError) is modeled as a PRECONDITION on the @Pure accessor
# (key_member's Requires(key is not None)), NOT as a runtime raise / side effect.
# An impl that would inspect an absent key fails verification on that
# precondition — it is fully captured by the spec, so no capability-token rival
# is needed; the prepatch-read rival below exercises exactly this.
#
# NOTE on ungrounded-oracle echo (directive 2): `expected_signal` is a @Pure
# function fully UNFOLDED over the input facts (model.py pure region) — it is not
# an opaque answer-key. An impl that "echoes" expected_signal IS the gold
# behaviour, not a wrong echo, so there is no SPEC-TOO-WEAK echo cheat. We
# therefore include an honest cheapest-impl positive control (return
# expected_signal(...)) as a control, expect="verify".

from pathlib import Path

INSTANCE = "sympy__sympy-19637"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of model.py (everything between the markers, exclusive).
# Every rival rewrites ONLY this block, so same_spec is guaranteed.
_GOLD_IMPL = """    # Default: no processing was applied.
    hit = False
    if entered:
        # The transform is entered. A key is created and spliced in ONLY when a
        # substitution is performed (key is not None). The signal — the key's
        # membership in the rewritten text — is read ONLY in that case, when a
        # key actually exists; otherwise the signal stays false.
        if key is not None:
            hit = key_member(key)
        else:
            hit = False
    return hit
"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: old block not found")
    if src.count(old) != 1:
        raise AssertionError("not unique: old block")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Build a full model.py source whose impl region is `new_body` (the gold
    spec/pure/pre/post regions untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

# (A) PREPATCH UNCONDITIONAL READ — the F2P bug path. The signal is read from
# the key's membership UNCONDITIONALLY inside the entered branch, with NO
# `key is not None` guard. This is model_prepatch.py: on the (True, None) input
# (entered, no key created) it inspects an absent key, exactly the unbound `kern`
# read. MUST be rejected — for INSUFFICIENT INFORMATION to discharge
# key_member's precondition (the formal face of UnboundLocalError).
_IMPL_PREPATCH_READ = """    # PREPATCH rival: read the key's membership UNCONDITIONALLY inside the
    # entered branch (NO `key is not None` guard) — the pre-patch
    # `hit = kern in s` placed outside the `if ' ' in s:` block. On the entered-
    # but-no-key path this inspects a key that was never created.
    hit = False
    if entered:
        if key is not None:
            key = key
        hit = key_member(key)
    return hit
"""

# (B) PARTIAL-DOMAIN — return the outer guard directly: `hit = entered`. Correct
# on (False,None)->False and (True,True)->True, but WRONG on (True,None): returns
# True where expected_signal is False. Diverges precisely on the F2P bug path and
# also on (True,False). MUST be rejected.
_IMPL_HIT_EQ_ENTERED = """    # PARTIAL-DOMAIN rival: the signal is just the outer guard. Reports
    # processing-applied whenever the transform was entered, even when no key was
    # created (the no-substitution case). Wrong on (True, None) and (True, False).
    hit = entered
    return hit
"""

# (C) VALUE-SWAP on the key-present branch — read the NEGATION of the key's
# membership. Correct on the absent-key cases, but on (True, True) returns False
# where expected is True, and on (True, False) returns True where expected is
# False. MUST be rejected (C1).
_IMPL_NEGATE_KEY = """    # VALUE-SWAP rival: the signal is the NEGATION of the created key's
    # membership (the guarded read is kept, so key_member's precond holds, but
    # the value is flipped). Wrong on both key-present inputs.
    hit = False
    if entered:
        if key is not None:
            hit = not key_member(key)
        else:
            hit = False
    return hit
"""

# (D) ALWAYS-FALSE — the cheapest impl that satisfies C2 (absent key -> false)
# but violates C1 on the key-present-and-true input. Returns False everywhere;
# correct on three of the four input classes but WRONG on (True, True). Probes
# that C1 actually pins the POSITIVE case (C2 alone is insufficient). MUST be
# rejected.
_IMPL_ALWAYS_FALSE = """    # ALWAYS-FALSE rival: never reports processing-applied. Satisfies C2 (absent
    # key forces false) but is wrong on (True, True), where expected_signal is
    # True (the created key occurs in the rewritten text).
    hit = False
    return hit
"""

# (E) NARROW PARTIAL-DOMAIN — diverge on a SINGLE input class only: when a key
# was created but does NOT occur (key is False, i.e. (True, False)), return True
# instead of False; correct everywhere else. A surgically-minimal rival pinned to
# one sub-domain. Fails C1 on (True, False). MUST be rejected.
_IMPL_NARROW_KEYFALSE = """    # NARROW PARTIAL-DOMAIN rival: correct on every input class EXCEPT
    # (True, False) — a key was created but does not occur in the rewritten text;
    # here the rival wrongly reports processing-applied (True) instead of False.
    hit = False
    if entered:
        if key is not None:
            if key_member(key):
                hit = True
            else:
                hit = True
        else:
            hit = False
    return hit
"""

# (F) POSITIVE CONTROL — structurally DIFFERENT but CORRECT. Collapse the nested
# guards into a single short-circuit `and`: the `key is not None` test still
# guards the key_member read (short-circuit gives key is not None in the then
# branch), and the default stays False. No loops, no induction lemma; same
# semantics as the gold cascade, so it MUST verify (else SPEC-TOO-STRONG).
_IMPL_POS_FLAT = """    # POSITIVE CONTROL: collapse the nested entered/key-present guards into one
    # short-circuit `and`. The `key is not None` conjunct still guards the
    # key_member read; the default is False. Semantically equal to the gold
    # cascade.
    hit = False
    if entered and key is not None:
        hit = key_member(key)
    return hit
"""

# (G) POSITIVE CONTROL — honest cheapest impl: return the grounded oracle
# directly. Because `expected_signal` is fully unfolded over the inputs (not an
# opaque answer key), `return expected_signal(...)` IS the gold behaviour and
# MUST verify. This is the directive-2 "grounded oracle => no wrong echo"
# positive control.
_IMPL_POS_DELEGATE = """    # POSITIVE CONTROL (grounded oracle): delegate to the pure selector directly.
    # `expected_signal` is fully unfolded over the inputs, so this is the gold
    # behaviour (not a wrong echo); it must verify.
    return expected_signal(entered, key)
"""

# (H) ADMISSIBILITY — confirm the precondition admits the F2P-shaped input
# (entered, NO key created): the exact input that triggered the original
# UnboundLocalError. We edit ONLY the impl region (so same_spec holds). The
# spec carries a termination obligation (MustTerminate), which forbids a
# same-measure recursive self-call, so admissibility is exercised the
# Assert-based way: instantiate the value precondition
# (Implies(not entered, key is None)) on the concrete F2P-shaped arguments
# (True, None) — trivially establishable, proving the precondition is
# non-contradictory for this legitimate input — and pin the demanded verdict
# via the grounded pure oracle (expected_signal(True, None) is False; pure
# calls carry no termination obligation). If the precondition could not be
# established for this input the Asserts would fail => PRECOND-TOO-STRONG.
# The original gold cascade follows verbatim, so the postcondition obligation
# is unchanged.
_IMPL_ADMISS = """    # ADMISSIBILITY: instantiate the precondition on the F2P-shaped input
    # (entered, NO key created). The Requires (Implies(not entered, key is
    # None)) must admit it (else PRECOND-TOO-STRONG); the demanded verdict,
    # read off the grounded pure oracle, is False (no key -> signal false).
    # (The termination obligation in the spec forbids a same-measure recursive
    # self-call, so the call-site probe is Assert-based.)
    f2p_entered = True
    f2p_key = None  # type: Optional[bool]
    Assert(Implies(not f2p_entered, f2p_key is None))
    Assert(not expected_signal(f2p_entered, f2p_key))
    # --- gold cascade verbatim below ---
    hit = False
    if entered:
        if key is not None:
            hit = key_member(key)
        else:
            hit = False
    return hit
"""


SPEC_TESTS = [
    {
        "id": "prepatch-unconditional-read",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PREPATCH_READ),
        "refinement": (
            "This is the pre-patch placement verbatim (model_prepatch.py): "
            "`hit = kern in s` read UNCONDITIONALLY inside the entered branch, "
            "outside the `if ' ' in s:` guard. Its faithful real patch is the "
            "UNPATCHED kernS, which on the F2P input kernS('(2*x)/(x-1)') enters "
            "the guard ('(' present, unquoted) but, after the structural rewrite, "
            "no space survives so `kern` is never bound; the read `kern in s` "
            "raises UnboundLocalError: local variable 'kern' referenced before "
            "assignment. test_kernS FAILS. It does not resolve."),
        "rationale": (
            "Rejected by the PRECONDITION of the @Pure accessor key_member "
            "(Requires(key is not None)): on the entered-but-no-key path "
            "(entered True, key None) the unconditional read calls key_member "
            "with key possibly None, and Nagini cannot discharge `key is not "
            "None`. This is the formal face of the unbound `kern` read and "
            "exactly what G-DIFF senses against model_prepatch.py."),
    },
    {
        "id": "partial-domain-hit-eq-entered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_HIT_EQ_ENTERED),
        "refinement": (
            "Faithful real patch: `hit = ('(' in s and not quoted)` — report "
            "processing-applied whenever the outer guard was entered, regardless "
            "of whether a substitution actually happened. On the F2P input "
            "kernS('(2*x)/(x-1)') it would set hit=True even though no `kern` was "
            "created; the later kern post-processing (s.replace(kern, ' ')) then "
            "runs against a never-created placeholder, and on the no-key path the "
            "name `kern` is still unbound at the post-processing site -> "
            "UnboundLocalError / wrong result. test_kernS FAILS. It does not "
            "resolve."),
        "rationale": (
            "Rejected by C2 (Implies(key is None, not Result())) and C1: on "
            "(True, None) it returns True where expected_signal is False; it also "
            "diverges on (True, False). The signal is the GUARD, not the key's "
            "membership."),
    },
    {
        "id": "value-swap-negate-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_NEGATE_KEY),
        "refinement": (
            "Faithful real patch: `hit = kern not in s` (inverted membership). "
            "After s.replace(' ', kern) the freshly-chosen `kern` is GUARANTEED to "
            "occur in s, so the gold `kern in s` is True; the inverted rival "
            "reports False and SKIPS the necessary post-processing "
            "s.replace(kern, ' '), leaving the kern placeholder in the parsed "
            "expression -> a wrong/garbage Symbol. test_kernS FAILS. It does not "
            "resolve."),
        "rationale": (
            "Rejected by C1 (Result()==expected_signal): on (True, True) it "
            "returns False where expected is True (and on (True, False) returns "
            "True where expected is False). The guarded read is kept (key_member's "
            "precond holds) but the value is flipped, so the rejection is purely "
            "on the postcondition value, not on permission."),
    },
    {
        "id": "always-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_ALWAYS_FALSE),
        "refinement": (
            "Faithful real patch: delete the `hit = kern in s` read entirely and "
            "always leave `hit = False`. On the entered-and-substituted case "
            "(a space survived and a `kern` was spliced in, e.g. kernS('-(x + "
            "1)')) the kern post-processing is GATED on hit being True; with "
            "hit=False the placeholder `kern` is never substituted back to a "
            "space, so the parsed expression keeps the kern garbage and the "
            "result is wrong. test_kernS FAILS. It does not resolve."),
        "rationale": (
            "Rejected by C1 (Result()==expected_signal): on (True, True) it "
            "returns False where expected is True. It satisfies C2 (absent key -> "
            "false) but C2 alone is insufficient — this case proves C1 actually "
            "pins the POSITIVE (entered-and-substituted) verdict, not just the "
            "negative one."),
    },
    {
        "id": "narrow-partial-domain-keyfalse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_NARROW_KEYFALSE),
        "refinement": (
            "Surgically-minimal rival that diverges ONLY on (True, False) — a "
            "`kern` was created but does NOT occur in the rewritten text. Its "
            "faithful real patch reports processing-applied (hit=True) even when "
            "`kern not in s`, triggering the kern post-processing "
            "s.replace(kern, ' ') against text that contains no `kern`; a no-op or "
            "spurious replacement that, combined with the hit=True gate, can "
            "mis-route a degenerate substitution case. It diverges from the gold "
            "signal on that sub-domain, so a real patch built from it would not "
            "faithfully reproduce kernS's hit semantics and would not resolve "
            "test_kernS on that input class."),
        "rationale": (
            "Rejected by C1 (Result()==expected_signal): on (True, False) it "
            "returns True where expected is False. Demonstrates the spec is tight "
            "even on a one-point divergence in the key-present sub-domain — the "
            "guarded read is kept, so the rejection is purely on the postcondition "
            "value."),
    },
    {
        "id": "pos-control-flat-and",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_FLAT),
        "rationale": (
            "Structurally different but correct: the nested entered/key-present "
            "guards are collapsed into a single short-circuit `and`. The "
            "`key is not None` conjunct still establishes key_member's "
            "precondition in the then-branch (short-circuit), and the default "
            "stays False. No loop / no induction lemma; semantically equal to the "
            "gold cascade, so it MUST verify (else SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-control-grounded-oracle-delegate",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_DELEGATE),
        "rationale": (
            "Directive-2 grounded-oracle positive control: `expected_signal` is "
            "fully unfolded over the inputs (not an opaque answer key), so "
            "delegating to it directly IS the gold behaviour and MUST verify. "
            "There is no wrong echo to exploit, so this is a positive control, "
            "not a weakness."),
    },
    {
        "id": "admissibility-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_ADMISS),
        "rationale": (
            "A recursive self-call inside the impl region invokes "
            "compute_processing_signal on the F2P-shaped input (entered=True, "
            "key=None — the exact UnboundLocalError trigger) and asserts the "
            "result is False. The Requires (Implies(not entered, key is None)) is "
            "trivially establishable for this input (entered is True), so the call "
            "site verifies (else PRECOND-TOO-STRONG). Confirms the precondition "
            "admits the issue's F2P input. Editing only the impl region keeps "
            "same_spec true."),
    },
]

# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# The axioms region of model.py is EMPTY: no @ContractOnly axiom is consumed and
# no A-reference deep model is referenced (meta.json axioms=[],
# deep_model_references=[]). The modeled delta is a pure control-flow /
# definedness decision over R-refined boolean / Optional[bool] inputs; no opaque
# callee appears inside any Ensures. There is therefore no axiom-soundness or
# axiom-containment obligation. (axiom_check.py is a G-AX no-op-soundness check
# that validates the entered/key abstraction == the real patched kernS control
# flow; it is not a @ContractOnly axiom probe.)
AXIOM_TESTS = []

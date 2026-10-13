# properties.py — PBT manifest for django__django-12419. NOT a Nagini module; a
# record of adversarial cases. The runner (swebench_nagini.pbt) executes each
# spec case (full model.py variant, same spec, swapped impl) under Nagini verify
# + same_spec, and each axiom case as a real-callee Docker probe.
#
# DEFENDED SURFACE (reasoned, not mechanical):
#   apply_referrer_policy(slot: HeaderSlot) -> None
#   Precondition:
#     Acc(slot.present) and Acc(slot.value)        -- FULL perm on the two fields
#     Acc(list_pred(slot.value), 1/2)              -- HALF perm on the list CONTENTS
#                                                     => slot.value contents are READ-ONLY
#   Load-bearing postcondition clauses:
#     (P1) slot.present                                            -- always ends present
#     (P2) Implies(Old(slot.present), slot.value is Old(slot.value))-- setdefault: never
#                                                                     overwrite a present hdr
#     (P3) Implies(not Old(slot.present),
#                  ToSeq(slot.value) == normalized_policy(baseline_policy()))
#     (P4) Implies(not Old(slot.present),
#                  ToSeq(slot.value) == baseline_policy())          -- the EXACT 11 code
#                                                                     points of "same-origin"
#   normalized_policy is `return s` (the IDENTITY): it is GROUNDED in its argument,
#   not an opaque answer-key oracle. There is therefore no "wrong echo" of an
#   ungrounded marker (see 'assessment'); P4 pins the exact baseline constant, so
#   the uniqueness attacks instead try to slip a DIFFERENT non-empty value past P4
#   and to break the setdefault identity P2.
#
#   FRAME MUTATION is in scope: only HALF permission is held on list_pred(slot.value),
#   so any impl that mutates the incoming list contents in place (append / index-store)
#   must be rejected for INSUFFICIENT PERMISSION (the gold impl builds a FRESH list and
#   reassigns the full-perm field slot.value).
from pathlib import Path

INSTANCE = "django__django-12419"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The full gold impl-region body (everything between # impl-start / # impl-end,
# exclusive of the markers). We rebuild variants by swapping this whole block,
# editing ONLY text inside the impl region so spec_signature is preserved.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        if not slot.present:
            # Build the normalized value: trim each comma-separated token,
            # rejoin by commas. For the baseline (no comma, no whitespace) this
            # copies the token verbatim.
            value = []  # type: List[int]
            i = 0
            while i < len(policy):
                # invariants-start
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(value)))
                Invariant(0 <= i and i <= len(policy))
                Invariant(ToSeq(value) == ToSeq(policy).take(i))
                Invariant(ToSeq(policy) == baseline_policy())
                Invariant(MustTerminate(len(policy) - i + 1))
                # invariants-end
                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
                       ToSeq(policy).take(i + 1))
                value = value + [policy[i]]
                i = i + 1
            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
            slot.present = True
            slot.value = value"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"
assert _BASE.count(_GOLD_IMPL) == 1


def _with_impl(new_impl_body):
    """Return a full model.py whose impl-region body is replaced by new_impl_body,
    editing ONLY inside # impl-start / # impl-end (same_spec preserved)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ===========================================================================
# (1) POSITIVE CONTROL (soundness) — structurally different, still CORRECT.
# Reshape: drop the forward-append loop entirely and assign the baseline value as
# a single list literal, then re-establish exactly the proof obligations P3/P4
# need (ToSeq(value) == baseline_policy() and the normalized_policy identity).
# No induction lemma is required (no fold over an appended list), so the gold
# proof remains valid. Must VERIFY; else SPEC-TOO-STRONG.
# ===========================================================================
_POS = """    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        if not slot.present:
            # Structural reshape: assign the value as a single literal instead of
            # the per-element copy loop. Keep every obligation P3/P4 consume.
            value = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
            Assert(ToSeq(value) == baseline_policy())
            Assert(normalized_policy(baseline_policy()) == baseline_policy())
            slot.present = True
            slot.value = value"""

# ===========================================================================
# (2) FRAME-MUTATION (uniqueness) — MANDATORY (read-only input).
# Only Acc(list_pred(slot.value), 1/2) is held, so the list CONTENTS of
# slot.value are read-only. This rival tries to satisfy P4 by MUTATING the
# incoming list in place (append) instead of building a fresh list. The append
# needs FULL list_pred permission => must be REJECTED for insufficient permission.
# Keep the value semantics gold-faithful so the rejection is attributable purely
# to the in-place write, not a value mismatch.
# ===========================================================================
_FRAME_MUT = """    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        if not slot.present:
            # FRAME-MUTATION: write the baseline code points into the EXISTING
            # slot.value list in place. Only Acc(list_pred(slot.value), 1/2) is
            # held -> append requires FULL permission -> insufficient permission.
            i = 0
            while i < len(policy):
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(slot.value)))
                Invariant(0 <= i and i <= len(policy))
                slot.value.append(policy[i])
                i = i + 1
            slot.present = True"""

# ===========================================================================
# (3) WRONG-VALUE (uniqueness) — the core SPEC-TOO-WEAK probe for P4.
# Attaches a DIFFERENT non-empty policy ("no-referrer" code points) into a FRESH
# list. P1 (present) is satisfied, but P3/P4 demand ToSeq(slot.value) ==
# baseline_policy() (the exact "same-origin" 11 code points). Must be REJECTED.
# Refinement: a real patch setting SECURE_REFERRER_POLICY = 'no-referrer' would
# attach `Referrer-Policy: no-referrer`, and the F2P test asserts the header line
# is exactly `Referrer-Policy: same-origin` -> the patch would NOT resolve.
# ===========================================================================
_WRONG_VALUE = """    # A DIFFERENT configured policy: the code points of "no-referrer".
    # 'n','o','-','r','e','f','e','r','r','e','r'
    policy = [110, 111, 45, 114, 101, 102, 101, 114, 114, 101, 114]  # type: List[int]
    if len(policy) > 0:
        if not slot.present:
            value = [110, 111, 45, 114, 101, 102, 101, 114, 114, 101, 114]  # type: List[int]
            slot.present = True
            slot.value = value"""

# ===========================================================================
# (4) PARTIAL-DOMAIN (uniqueness) — correct on most of the value but truncated.
# Builds the baseline value but DROPS the final code point ('n'), producing
# "same-origi" (10 code points). Verifies P1, but P4 fails (length / last
# element differs). Must be REJECTED.
# Refinement: a real patch whose header-value chain dropped the final char would
# emit `Referrer-Policy: same-origi`; the F2P test asserts exactly `same-origin`
# -> would NOT resolve. This is the sub-domain (last element) divergence a tight
# postcondition must catch and a byte-fuzzer's near-miss only catches by luck.
# ===========================================================================
_PARTIAL = """    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        if not slot.present:
            # Off-by-one: copy all but the LAST code point (truncates "same-origin"
            # to "same-origi"). Correct on the 10-element prefix; diverges on the
            # last element.
            value = []  # type: List[int]
            i = 0
            while i < len(policy) - 1:
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(value)))
                Invariant(0 <= i and i <= len(policy))
                Invariant(ToSeq(value) == ToSeq(policy).take(i))
                # This value-building loop stops one short of the count, so
                # len(policy) - i stays positive and strictly decreases.
                Invariant(MustTerminate(len(policy) - i))
                value = value + [policy[i]]
                i = i + 1
            slot.present = True
            slot.value = value"""

# ===========================================================================
# (5) SETDEFAULT-OVERWRITE (uniqueness / control-flow-effect) — breaks P2.
# The gold impl only writes when `not slot.present` (setdefault: never clobber a
# present header). This rival DROPS the `if not slot.present:` guard and always
# reassigns slot.value to a fresh list. When Old(slot.present) is true, P2 demands
# slot.value is Old(slot.value) (identity), but a fresh list breaks the `is`. Must
# be REJECTED.
# Refinement: replacing response.setdefault(...) with response['Referrer-Policy']=...
# would overwrite an operator-set Referrer-Policy header. setdefault's whole point is
# not to clobber; such a patch changes observable behaviour for already-present
# headers and is not the gold behaviour (it would regress the documented
# "an already-present header is left untouched" contract).
# ===========================================================================
_OVERWRITE = """    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        # No `if not slot.present:` guard -> ALWAYS reassign (clobbers a present
        # header). Breaks P2: slot.value is Old(slot.value) when Old(slot.present).
        value = []  # type: List[int]
        i = 0
        while i < len(policy):
            Invariant(Acc(list_pred(policy)))
            Invariant(Acc(list_pred(value)))
            Invariant(0 <= i and i <= len(policy))
            Invariant(ToSeq(value) == ToSeq(policy).take(i))
            Invariant(ToSeq(policy) == baseline_policy())
            # This value-building loop runs to the count, so len(policy) - i + 1
            # stays positive and strictly decreases.
            Invariant(MustTerminate(len(policy) - i + 1))
            value = value + [policy[i]]
            i = i + 1
        slot.present = True
        slot.value = value"""

# ===========================================================================
# (6) ADMISSIBILITY (verify) — a normal F2P-shaped (absent header) input is inside
# the precondition's domain. Construct a fresh absent HeaderSlot — the constructor
# call is itself part of the probe, since it must establish the constructor's own
# Requires — and then ASSERT each Requires clause of apply_referrer_policy at that
# witness. If a legitimate absent-header slot could not meet them the asserts
# would not verify => PRECOND-TOO-STRONG. Entirely inside the impl region, with
# the gold body following verbatim so the postcondition obligation is unchanged.
#
# A self-call on the probe is no longer usable as the witness: the method carries
# a termination obligation and is never strictly below ITSELF, so Nagini reports
# `Obligation leak check failed. Callee apply_referrer_policy might not take all
# unsatisfied obligations from the caller.` — a termination fact, not a fact about
# the precondition's domain, so it would attribute nothing. (Measured both ways:
# the old self-call probe fails exactly that way, and RAISING the method's own
# level 2 -> 7 leaves the identical error, confirming no level can rescue a
# self-call.) Asserting the establishability of each Requires clause is the same
# substitution django__django-14580 uses for this reason.
#
# NEGATIVE CONTROL (proves the probe can fail, i.e. is not a tautology): moving
# the absent-header witness OUTSIDE what the constructed slot establishes — i.e.
# claiming Assert(probe.present) of a slot built absent — is REJECTED by the
# verifier with
#   error: Assert might fail. Assertion probe.present might not hold.
# and, independently, claiming the fresh value is non-empty via
# Assert(len(probe.value) >= 1) is REJECTED with
#   error: Assert might fail. Assertion (len(probe.value) >= 1) might not hold.
# So the asserts below are discharged by the witness, not by triviality. (Note a
# FULL-permission demand on probe.value would NOT discriminate here: the slot is
# built over a freshly-constructed list, so full permission genuinely is held —
# measured, and therefore not used as the control.)
# ===========================================================================
_ADMISS = """    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    # ADMISSIBILITY probe: an F2P-shaped absent-header slot is in-domain. Building
    # it must establish the constructor's Requires, and each Requires clause of
    # apply_referrer_policy must then hold of it.
    fresh = []  # type: List[int]
    probe = HeaderSlot(False, fresh)
    # Requires clause 1: both slot fields are accessible (readable AND writable —
    # the header slot is the mutated object).
    Assert(Acc(probe.present) and Acc(probe.value))
    # Requires clause 2: the half-permission on the slot's value is held, so its
    # element count is readable.
    Assert(Acc(list_pred(probe.value), 1 / 2))
    Assert(len(probe.value) == 0)
    # ...and this witness is the discriminating F2P shape: the header is ABSENT,
    # which is the input the attach clause is stated of.
    Assert(not probe.present)
    if len(policy) > 0:
        if not slot.present:
            value = []  # type: List[int]
            i = 0
            while i < len(policy):
                # invariants-start
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(value)))
                Invariant(0 <= i and i <= len(policy))
                Invariant(ToSeq(value) == ToSeq(policy).take(i))
                Invariant(ToSeq(policy) == baseline_policy())
                Invariant(MustTerminate(len(policy) - i + 1))
                # invariants-end
                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
                       ToSeq(policy).take(i + 1))
                value = value + [policy[i]]
                i = i + 1
            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
            slot.present = True
            slot.value = value"""


SPEC_TESTS = [
    {
        "id": "pos-control-literal-value",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS),
        "rationale": "A structurally-different but correct impl (single list literal "
                     "instead of the per-element copy loop) that re-establishes exactly "
                     "the obligations P3/P4 consume must verify. No fold/induction lemma "
                     "is needed (no append-against-front-recursive-fold), so the gold "
                     "proof stays valid. If it fails, SPEC-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-append-inplace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT),
        "refinement": "A real impl that mutated the existing Referrer-Policy header-value "
                      "list object in place is not what response.setdefault(key, value) "
                      "does (setdefault inserts a fresh value object under the key); it "
                      "would corrupt shared/aliased header storage rather than insert the "
                      "computed value, and is not the gold behaviour the F2P test exercises.",
        "rationale": "Permission system: only Acc(list_pred(slot.value), 1/2) is held, so "
                     "slot.value.append(...) needs FULL list_pred permission and is "
                     "rejected for insufficient permission. This is the mandatory "
                     "read-only-input frame-mutation probe.",
    },
    {
        "id": "weak-wrong-policy-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WRONG_VALUE),
        "refinement": "A real patch setting SECURE_REFERRER_POLICY = 'no-referrer' would "
                      "attach `Referrer-Policy: no-referrer`. The F2P test "
                      "(test_middleware_headers) asserts the serialized header list "
                      "contains exactly `b'Referrer-Policy: same-origin'`, so this patch "
                      "would NOT resolve -- a verifying rival here would be a true "
                      "verify-not-resolve break.",
        "rationale": "Postcondition P3/P4: ToSeq(slot.value) == baseline_policy() pins the "
                     "exact 11 'same-origin' code points; a non-empty but DIFFERENT value "
                     "satisfies P1 (present) yet violates P4 -> reject.",
    },
    {
        "id": "weak-truncated-last-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL),
        "refinement": "A real header-value chain that dropped the final character would "
                      "emit `Referrer-Policy: same-origi`; the F2P test asserts exactly "
                      "`same-origin`, so it would NOT resolve. Partial-domain: correct on "
                      "the 10-element prefix, diverges only on the last element.",
        "rationale": "Postcondition P4: ToSeq(slot.value) == baseline_policy() forces the "
                     "FULL 11 code points; a 10-element prefix fails on length/last element "
                     "-> reject. A byte-fuzzer catches a last-element drop only by luck; "
                     "this reasons about the sub-domain a tight postcondition must defend.",
    },
    {
        "id": "weak-setdefault-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_OVERWRITE),
        "refinement": "Replacing response.setdefault('Referrer-Policy', v) with an "
                      "unconditional response['Referrer-Policy'] = v would clobber a header "
                      "an operator (or earlier middleware) already set. setdefault's whole "
                      "purpose is not to overwrite; such a patch changes observable behaviour "
                      "for already-present headers and regresses the documented "
                      "'already-present header is left untouched' contract.",
        "rationale": "Postcondition P2: Implies(Old(slot.present), slot.value is "
                     "Old(slot.value)) -- the setdefault identity. Dropping the "
                     "`if not slot.present:` guard and always reassigning to a FRESH list "
                     "breaks the `is` identity when Old(slot.present) -> reject. "
                     "Control-flow-effect: the write/no-write decision is invisible to a "
                     "plain value abstraction and is pinned by the Old(...) identity clause.",
    },
    {
        "id": "admiss-absent-slot-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": "A freshly-constructed F2P-shaped absent HeaderSlot is in-domain: "
                     "building it must establish the constructor's own Requires, and the "
                     "probe then ASSERTS each Requires clause of apply_referrer_policy at "
                     "that witness (both slot fields accessible; the 1/2 share on the "
                     "slot's value held, so its length is readable; and the header ABSENT, "
                     "the discriminating F2P shape). The gold body follows verbatim, so the "
                     "postcondition obligation is unchanged. If a legitimate absent-header "
                     "slot could not meet the Requires => PRECOND-TOO-STRONG. A self-call is "
                     "no longer usable as the witness: the method is never strictly below "
                     "ITSELF, so it fails with `Obligation leak check failed. Callee "
                     "apply_referrer_policy might not take all unsatisfied obligations from "
                     "the caller.` — a termination fact attributing nothing about the domain, "
                     "and raising the method's own level 2 -> 7 leaves the identical error "
                     "(both measured). NEGATIVE CONTROL (the probe is a real check, not a "
                     "tautology): claiming Assert(probe.present) of a slot built ABSENT is "
                     "REJECTED with `error: Assert might fail. Assertion probe.present might "
                     "not hold.`, and Assert(len(probe.value) >= 1) is REJECTED with `error: "
                     "Assert might fail. Assertion (len(probe.value) >= 1) might not hold.` "
                     "(both measured).",
    },
]


# No @ContractOnly consumed axioms and no A-reference deep model that the model
# CONSUMES as an unproven contract: normalized_policy is a verified @Pure fold
# (identity) whose equality with the real ','-join/strip chain is validated
# out-of-band by axiom_check.py (G-AX). There is no in-model axiom obligation for
# the PBT axiom lane to re-discharge, so AXIOM_TESTS is empty (see assessment).
AXIOM_TESTS = []

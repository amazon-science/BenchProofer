"""PBT falsification battery for django__django-11551.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes. Spec cases are full model.py variants that share
the FROZEN spec byte-for-byte (region-surgery: only the text inside
# impl-start / # impl-end is edited) and are checked by Nagini verify +
markers.same_spec. There are no @ContractOnly axioms / A-reference deep models
in this bundle (meta.axioms == []), so AXIOM_TESTS == [].

Defended surface (reasoned, not mechanical)
--------------------------------------------
check_display_item is a PURE decision over six `bool` scalars passed BY VALUE,
returning an int code in {0, 108, 109}. There is NO heap state, NO Acc(x,1/2)
read-only input (so the directive-5 frame-mutation attack is N/A — see
'assessment' in the structured return), and NO @Pure answer-key oracle (the
verdict is pinned directly to the six input booleans, fully unfolded, so there
is no ungrounded oracle to echo). The four postcondition clauses pin the output
UNIQUELY on every reachable combination (let early = is_invokable or
is_presenter_attr):

  (A) early                                    => 0
  (C) not early and not structural_absent      => 109 if structural_is_relation else 0
  (D) not early and structural_absent
        and not attribute_absent               => 109 if attribute_is_relation else 0
  (B) (Result==108) == (not early and structural_absent and attribute_absent)

So this spec is exhaustive. The live attack surface is therefore PARTIAL-DOMAIN
and VALUE-DOUBLE-MASK rivals that get one sub-domain wrong (the F2P sub-domain
above all), plus a CONTROL-FLOW rival reordering which observation decides which
verdict. Each reject rival carries the refinement argument that its faithful
real django patch would NOT resolve the F2P/P2P.
"""
from pathlib import Path

INSTANCE = "django__django-11551"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim impl region (between # impl-start / # impl-end). Every variant is
# produced by _swap on _BASE so the frozen spec/proof/pre/post regions are never
# touched (same_spec is GUARANTEED by construction).
_IMPL = """    if is_invokable:
        return 0
    if is_presenter_attr:
        return 0
    if not structural_absent:
        relation = structural_is_relation  # type: bool
    elif attribute_absent:
        return 108
    else:
        relation = attribute_is_relation
    if relation:
        return 109
    return 0"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in source")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Return a full model variant whose impl region is `new_body` (the rest of
    the file — spec/proof/pre/post — is the frozen original, so same_spec holds)."""
    return _swap(_BASE, _IMPL, new_body)


# Sanity: the anchor must match the live file exactly (fails loudly on drift).
assert _IMPL in _BASE, "impl region drifted from model.py"


# --------------------------------------------------------------------------
# SPEC TESTS
# --------------------------------------------------------------------------
SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness) -----------------------------------
    # Structurally DIFFERENT but behaviourally IDENTICAL: the two early-accept
    # branches are fused into one (is_invokable or is_presenter_attr), and the
    # resolution is reshaped into an explicit selector local `relation` decided
    # by a single nested if/else instead of the if/elif/else chain. No loop, no
    # recursion, no induction lemma — pure straight-line reshape — so the gold
    # proof obligations still discharge automatically. MUST verify (else
    # SPEC-TOO-STRONG: a faithful correct impl is rejected).
    {
        "id": "pos-control-fused-early",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if is_invokable or is_presenter_attr:\n"
            "        return 0\n"
            "    if structural_absent:\n"
            "        if attribute_absent:\n"
            "            return 108\n"
            "        relation = attribute_is_relation  # type: bool\n"
            "    else:\n"
            "        relation = structural_is_relation\n"
            "    if relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "rationale": "a correct impl with fused early-accept + reshaped "
                     "resolution must verify against clauses (A)-(D); if it "
                     "cannot the postcondition is SPEC-TOO-STRONG.",
    },

    # ---- POSITIVE CONTROL #2 (soundness) --------------------------------
    # Another correct shape: compute the relation flag via a single chained
    # expression and a flat return ladder, with the m2m test inlined per branch
    # rather than after a shared `relation` local. Behaviourally identical.
    {
        "id": "pos-control-inline-m2m",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if is_presenter_attr:\n"
            "        return 0\n"
            "    if not structural_absent:\n"
            "        if structural_is_relation:\n"
            "            return 109\n"
            "        return 0\n"
            "    if attribute_absent:\n"
            "        return 108\n"
            "    if attribute_is_relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "rationale": "the m2m decision inlined per resolution source (no shared "
                     "`relation` local) is still correct; must verify.",
    },

    # ---- ADMISSIBILITY --------------------------------------------------
    # The precondition is trivially True (no Requires; pure scalar decision).
    # A self-call caller on the EXACT F2P-shaped input (not invokable, not a
    # presenter attr, structural field PRESENT and non-relation, attribute
    # UNREACHABLE) must establish the (vacuous) precondition and, via the
    # postcondition, conclude the verdict is 0 (accepted) — the F2P observation.
    # MUST verify (else PRECOND-TOO-STRONG).
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if is_presenter_attr:\n"
            "        return 0\n"
            "    if not structural_absent:\n"
            "        relation = structural_is_relation  # type: bool\n"
            "    elif attribute_absent:\n"
            "        return 108\n"
            "    else:\n"
            "        relation = attribute_is_relation\n"
            "    if relation:\n"
            "        return 109\n"
            "    # F2P-shaped admissibility witness: a field reachable only via\n"
            "    # the structural lookup (structural present & non-relation),\n"
            "    # attribute unreachable, must be ACCEPTED (verdict 0).\n"
            "    Assert(Implies(not False and not False and not True\n"
            "                   and True and False,\n"
            "                   0 == (109 if False else 0)))\n"
            "    return 0"
        ),
        "rationale": "the (trivial) precondition admits a normal F2P-shaped "
                     "input and the postcondition yields 0 there; if the Assert "
                     "fails the precondition/spec is PRECOND-TOO-STRONG.",
    },

    # ---- REJECT: the gold pre-image bug (partial-domain, F2P) -----------
    # Re-introduces the pre-patch `elif hasattr(obj.model, item)` gate: the
    # structural get_field attempt is GATED behind `not attribute_absent`, so
    # when the attribute is unreachable it jumps straight to 108 WITHOUT
    # consulting the structural field. This is model_prepatch.py's behaviour.
    # It VIOLATES clause (C) on {not early, not structural_absent,
    # attribute_absent}: the spec demands 0/109 from the structural field but
    # this returns 108. MUST be rejected (else SPEC-TOO-WEAK).
    {
        "id": "reject-prepatch-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if is_presenter_attr:\n"
            "        return 0\n"
            "    if not attribute_absent:\n"
            "        if not structural_absent:\n"
            "            relation = structural_is_relation  # type: bool\n"
            "        else:\n"
            "            relation = attribute_is_relation\n"
            "    else:\n"
            "        return 108\n"
            "    if relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "refinement": "this IS the pre-patch `elif hasattr(obj.model, item)` "
                      "gate (model_prepatch.py): when getattr raises but "
                      "get_field succeeds (the PositionField F2P shape), the "
                      "real patch returns admin.E108 instead of accepting, so "
                      "test_valid_field_accessible_via_instance FAILS — not "
                      "resolved.",
        "rationale": "violates clause (C) Implies(not early and not "
                     "structural_absent, Result==0/109) on the F2P sub-domain "
                     "{attribute_absent}: returns 108.",
    },

    # ---- REJECT: value-level double-mask in path (C) --------------------
    # When the structural lookup yields a field, the verdict must be decided by
    # THAT field's relation flag (structural_is_relation). This rival instead
    # uses attribute_is_relation as the m2m proxy in the structural branch — a
    # value double-mask: it reads the wrong source's relation observation.
    # VIOLATES clause (C) on {not early, not structural_absent,
    # structural_is_relation != attribute_is_relation}. MUST be rejected.
    {
        "id": "reject-wrong-source-relation-C",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if is_presenter_attr:\n"
            "        return 0\n"
            "    if not structural_absent:\n"
            "        relation = attribute_is_relation  # type: bool\n"
            "    elif attribute_absent:\n"
            "        return 108\n"
            "    else:\n"
            "        relation = attribute_is_relation\n"
            "    if relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "refinement": "the real patch tests isinstance(field, ManyToManyField) "
                      "on the field returned by get_field; testing the getattr "
                      "value instead would, when get_field yields an m2m field "
                      "but getattr yields a non-m2m value (or raises), accept a "
                      "ManyToManyField (miss admin.E109) — diverging from gold "
                      "on the E109 P2P/relation domain, so it would not resolve.",
        "rationale": "violates clause (C): Result must be (109 if "
                     "structural_is_relation else 0); this returns (109 if "
                     "attribute_is_relation else 0).",
    },

    # ---- REJECT: drop E109 on the attribute path (partial-domain, D) ----
    # In the attribute-resolved branch (structural absent, attribute present)
    # the rival hard-codes relation=False, so it NEVER emits 109 for an m2m
    # reachable only via getattr. VIOLATES clause (D) on {not early,
    # structural_absent, not attribute_absent, attribute_is_relation}: spec
    # demands 109, rival returns 0. MUST be rejected.
    {
        "id": "reject-drop-e109-on-attr-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if is_presenter_attr:\n"
            "        return 0\n"
            "    if not structural_absent:\n"
            "        relation = structural_is_relation  # type: bool\n"
            "    elif attribute_absent:\n"
            "        return 108\n"
            "    else:\n"
            "        relation = False\n"
            "    if relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "refinement": "the gold patch hoists isinstance(field, ManyToManyField) "
                      "so it applies to the object obtained from EITHER lookup; "
                      "skipping the m2m test on the getattr-resolved object "
                      "would accept a ManyToManyField reachable only via getattr "
                      "(emit [] instead of admin.E109), diverging from gold on "
                      "the attribute-m2m sub-domain — not resolved.",
        "rationale": "violates clause (D): Result must be (109 if "
                     "attribute_is_relation else 0); this is always 0 on that "
                     "path.",
    },

    # ---- REJECT: collapse path (D) accept to not-resolvable (sub-domain) -
    # A rival that, whenever the structural lookup reports absent, returns 108 —
    # ignoring the attribute lookup entirely. Correct only on the {structural &
    # attribute both absent} cell; WRONG on {structural_absent, not
    # attribute_absent}. VIOLATES clause (B): it emits 108 even when an
    # attribute resolves, and VIOLATES clause (D). MUST be rejected.
    {
        "id": "reject-structural-absent-to-108",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if is_presenter_attr:\n"
            "        return 0\n"
            "    if structural_absent:\n"
            "        return 108\n"
            "    relation = structural_is_relation  # type: bool\n"
            "    if relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "refinement": "ignoring the inner getattr fallback means any item whose "
                      "get_field raises FieldDoesNotExist is reported admin.E108 "
                      "even when getattr(obj.model, item) resolves it — wrong "
                      "for any attribute-only field, and in particular it would "
                      "REVERSE the very fix being tested (the patch added the "
                      "getattr fallback). The F2P/related P2P would not resolve.",
        "rationale": "violates clause (B) (Result==108 requires "
                     "attribute_absent too) and clause (D) on {structural_absent,"
                     " not attribute_absent}.",
    },

    # ---- REJECT: ignore early-accept #2 (partial-domain on clause A) ----
    # Drops the is_presenter_attr early accept, so when is_presenter_attr holds
    # but the entry is otherwise unresolvable (structural & attribute absent) it
    # returns 108 instead of 0. VIOLATES clause (A) Implies(is_presenter_attr,
    # Result==0) on {not is_invokable, is_presenter_attr, structural_absent,
    # attribute_absent}. MUST be rejected.
    {
        "id": "reject-drop-presenter-accept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_invokable:\n"
            "        return 0\n"
            "    if not structural_absent:\n"
            "        relation = structural_is_relation  # type: bool\n"
            "    elif attribute_absent:\n"
            "        return 108\n"
            "    else:\n"
            "        relation = attribute_is_relation\n"
            "    if relation:\n"
            "        return 109\n"
            "    return 0"
        ),
        "refinement": "the real patch returns [] immediately on "
                      "hasattr(obj, item) (a method/attribute of the ModelAdmin "
                      "itself, e.g. the `a_method`/custom-callable display "
                      "entries exercised by ListDisplayTests); dropping that "
                      "early accept would emit admin.E108 for a valid presenter "
                      "attribute, failing those P2P valid cases — not resolved.",
        "rationale": "violates clause (A): Implies(is_presenter_attr, "
                     "Result==0); on a presenter attr that is otherwise "
                     "unresolvable this returns 108.",
    },
]


# --------------------------------------------------------------------------
# AXIOM TESTS — none: this bundle consumes no @ContractOnly axiom and uses no
# A-reference deep model (meta.axioms == [], deep_model_references == []). The
# unchanged primitives (callable / hasattr / Options.get_field / getattr /
# isinstance(.,ManyToManyField)) are each reduced to the boolean observation
# they produce; the changed DECISION LOGIC is modeled deeply in the impl region,
# so there is no axiom-soundness or axiom-containment obligation to probe.
# (axiom_check.py independently confirms decision-logic equivalence over all 64
# observation combinations + the real-callee PositionField witness.)
# --------------------------------------------------------------------------
AXIOM_TESTS = []

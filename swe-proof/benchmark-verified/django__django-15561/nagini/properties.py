"""PBT falsification battery for django__django-15561.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec exactly
(every edit is confined to an `# impl-start` / `# impl-end` region, so
markers.same_spec holds) and swaps only the implementation. The runner verifies
each with Nagini on the host; expect="verify" passes iff (same_spec AND
verifies); expect="reject" passes iff (same_spec AND does NOT verify).

Defended surface (read from model.py):
  * schema_irrelevant_attrs() -> PSet[int]
      No inputs. Postcondition = EXACT set equality: Result() == the 12-element
      PSet {attr_choices() .. attr_verbose_name()} (plus the redundant
      load-bearing membership `attr_choices() in Result()`, the entire fix: the
      enumeration attribute joins the schema-irrelevant set). Equality cuts BOTH
      ways: a set MISSING any pinned code is rejected, and a SUPERSET (an extra
      code, i.e. a schema-RELEVANT attribute smuggled into the ignore-set,
      which would suppress required rebuilds) is rejected too.
  * field_alteration_needed(attrs, old_vals, new_vals, non_db, other_differs)
      (impl span 194-212, with the loop invariants at 199-206 nested inside).
      non_db: PSet[int] is a READ-ONLY input: Requires AND Ensures hold
      Acc(set_pred(non_db), 1/2). booleans/PSeq need no permission.
      Postcondition LOAD-BEARING clause:
          Result() == (other_differs or disagrees_relevant(attrs,old,new,non_db))
      disagrees_relevant is a @Pure existential FULLY UNFOLDED over the inputs
      (it is grounded in the args, not an opaque answer-key) -> there is no
      "wrong echo": echoing it IS doing the work. So the ungrounded-oracle class
      is N/A here; we instead supply a cheapest-impl positive control.

Refinement anchor (refinement.md / mapping.md): the result of
schema_irrelevant_attrs is passed as field_alteration_needed's `non_db`; the
rebuild decision is the gold _field_should_be_altered. The single F2P,
test_alter_field_choices_noop, is a choices-only field change: it must yield
Result()==False (no rebuild). P2P keeps every schema-relevant change rebuilding
(e.g. max_length differs -> rebuild) and every schema-irrelevant-only change a
no-op.
"""
from pathlib import Path

INSTANCE = "django__django-15561"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (verbatim from model.py impl regions). Editing inside these
# keeps spec_view (and therefore same_spec) identical.
# ---------------------------------------------------------------------------

# schema_irrelevant_attrs impl region (the full PSet construction + return)
_SIA_IMPL = """    # impl-start
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    return s
    # impl-end"""

# field_alteration_needed impl region (loop scan), invariants kept intact.
_FAN_IMPL = """    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False
    # impl-end"""


SPEC_TESTS = []

# ===========================================================================
# 1. POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
#    must verify (else SPEC-TOO-STRONG).
# ===========================================================================

# 1a. schema_irrelevant_attrs: build the set by adding the SAME 12 codes in a
#     different LITERAL order (set membership is order-insensitive; the gold
#     proof obligation is only membership, which is preserved). Keeps every
#     pinned member. Must verify.
_SIA_REORDER = """    # impl-start
    s = PSet(attr_verbose_name(), attr_validators(), attr_related_query_name(),
             attr_related_name(), attr_on_delete(), attr_limit_choices_to(),
             attr_help_text(), attr_error_messages(), attr_editable(),
             attr_db_column(), attr_blank(), attr_choices())
    return s
    # impl-end"""
SPEC_TESTS.append({
    "id": "pos-sia-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _SIA_IMPL, _SIA_REORDER),
    "rationale": "set built from the SAME 12 codes in reversed literal order; "
                 "PSet equality is order-insensitive so the exact-set "
                 "postcondition (and the membership clause) still holds. A "
                 "correct structural variant must verify (else SPEC-TOO-STRONG).",
})

# 1b. field_alteration_needed: cheapest correct re-shape — fold the two nested
#     `if`s into a single boolean conjunction (same control flow value, same
#     short-circuit), keeping the loop direction and ALL gold invariants. Must
#     verify.
_FAN_CONJ = """    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if (not (attrs[i] in non_db)) and old_vals[i] != new_vals[i]:
            return True
        i = i + 1
    return False
    # impl-end"""
SPEC_TESTS.append({
    "id": "pos-fan-conj",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _FAN_IMPL, _FAN_CONJ),
    "rationale": "the two nested ifs collapsed into one short-circuiting `and`; "
                 "identical value/control flow, all gold loop invariants kept. "
                 "A correct reshape must verify (else SPEC-TOO-STRONG).",
})

# ===========================================================================
# 2. ADMISSIBILITY — a positive-control caller asserts the precondition admits
#    an F2P-shaped input. expect="verify". (else PRECOND-TOO-STRONG.)
#    We exercise field_alteration_needed at the call shape the gold meets: a
#    choices-only no-op. We add an assertion AFTER an internal self-construction
#    proving the Requires (len-alignment) is establishable; for the set we
#    assert the load-bearing membership is reachable.
# ===========================================================================

# 2a. schema_irrelevant_attrs admissibility: keep the gold impl, but Assert the
#     load-bearing membership holds on the constructed result before returning
#     (a proof the postcondition's pinned member is genuinely produced, not
#     vacuously satisfied). Must verify.
_SIA_ADMISS = """    # impl-start
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    Assert(attr_choices() in s)
    Assert(attr_verbose_name() in s)
    return s
    # impl-end"""
SPEC_TESTS.append({
    "id": "admiss-sia",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _SIA_IMPL, _SIA_ADMISS),
    "rationale": "Assert that the enumeration attribute (and a legacy one) is a "
                 "genuine member of the constructed set; the postcondition is "
                 "satisfiable on a real value, not vacuously (else the spec "
                 "would be unsatisfiable / PRECOND-TOO-STRONG).",
})

# 2b. field_alteration_needed admissibility: keep the gold impl but, in the
#     `other_differs` no-op branch path, Assert the F2P discriminator is
#     reachable — when other_differs is False and the loop completes, the
#     decision is exactly False, i.e. a choices-only change (every disagreeing
#     attr is in non_db) is admitted as a no-op. We Assert at the post-loop
#     `return False` that the negation of disagrees_relevant is provable here.
_FAN_ADMISS = """    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    Assert(not other_differs)
    Assert(not disagrees_relevant(attrs, old_vals, new_vals, non_db))
    return False
    # impl-end"""
SPEC_TESTS.append({
    "id": "admiss-fan",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _FAN_IMPL, _FAN_ADMISS),
    "rationale": "at the post-loop `return False`, Assert the decision-defining "
                 "facts (no structural diff AND no schema-relevant disagreement) "
                 "are provable — the no-op (F2P choices-only) input is admitted "
                 "by the precondition (else PRECOND-TOO-STRONG).",
})

# ===========================================================================
# 3. FRAME-MUTATION (MANDATORY: non_db is a read-only Acc(set_pred,1/2) input).
#    A rival that WRITES to non_db to satisfy the postcondition must be rejected
#    for INSUFFICIENT PERMISSION. Gold invariants kept verbatim so the rejection
#    is attributable to the write, not a proof regression.
# ===========================================================================

# 3a. DEMAND FULL (WRITE) PERMISSION on the read-only set. PSet is an immutable
#     value type with no mutator method (verified: PSet exposes no .add/.pop), so
#     the genuine, expressible frame attack against a set_pred-guarded input is
#     an impl that demands Acc(set_pred(non_db), 1) — the permission an impl that
#     intends to MUTATE the shared schema-irrelevant set would need. We bump ONE
#     loop-framing invariant from 1/2 to 1; everything else (every other gold
#     invariant, the loop body, the postcondition) is verbatim, so the rejection
#     is attributable to insufficient permission, not a proof regression. The
#     precondition grants only Acc(set_pred(non_db), 1/2), so the invariant
#     cannot be established.
_FAN_FRAME_WRITE = """    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False
    # impl-end"""
SPEC_TESTS.append({
    "id": "frame-mut-non_db-write-perm",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _FAN_IMPL, _FAN_FRAME_WRITE),
    "refinement": "an impl demanding FULL write permission on set_pred(non_db) "
                  "intends to MUTATE the shared schema-irrelevant set "
                  "(field.non_db_attrs is a class-level tuple shared across the "
                  "whole process) rather than only reading membership. A "
                  "faithful real patch that rewrote non_db_attrs at "
                  "decision-time — e.g. to force an attribute in so the rebuild "
                  "is suppressed — would silently corrupt every other field's "
                  "alteration decision and skip required column rebuilds, "
                  "failing the P2P alter tests. It does NOT resolve.",
    "rationale": "REJECT comes from the PERMISSION system: the loop invariant "
                 "demands Acc(set_pred(non_db), 1) but the precondition grants "
                 "only Acc(set_pred(non_db), 1/2), so Nagini reports 'Loop "
                 "invariant might not hold ... Insufficient permission to access "
                 "set_pred(non_db)'. Only 1/2 -> 1 changed; the rejection is "
                 "attributable to the read-only frame, not the postcondition.",
})

# 3b. frame-mutation on schema_irrelevant_attrs is N/A: it has NO inputs (it
#     constructs a fresh PSet), so there is no read-only resource to over-claim.
#     Covered by the note in assessment.

# ===========================================================================
# 4. PARTIAL-DOMAIN — a rival correct on most of the domain but diverging on a
#    sub-domain. expect="reject".
# ===========================================================================

# 4a. SKIP THE FIRST listed attribute (off-by-one): scan from i=0 (so the
#     invariant ENTRY 0<=i<=len is trivially valid even when attrs is empty),
#     but guard the disagreement check with `i > 0`, so the first listed
#     attribute is never considered. Correct on every input whose first listed
#     attribute agrees or is schema-irrelevant, but WRONG when the first listed
#     attribute is the sole schema-relevant disagreement -> returns False when
#     the postcondition demands True. Rejection is attributable to the
#     postcondition existential disagrees_relevant whose witness can be j=0.
_FAN_SKIP_FIRST = """    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if i > 0:
            if not (attrs[i] in non_db):
                if old_vals[i] != new_vals[i]:
                    return True
        i = i + 1
    return False
    # impl-end"""
SPEC_TESTS.append({
    "id": "partial-skip-first",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _FAN_IMPL, _FAN_SKIP_FIRST),
    "refinement": "the faithful real patch would skip the FIRST attribute in "
                  "each kwargs bag when deciding whether to rebuild. If the only "
                  "schema-relevant difference is on the first-iterated attribute "
                  "(e.g. a max_length change that sorts/iterates first), "
                  "_field_should_be_altered returns False and Django skips a "
                  "REQUIRED column rebuild — the P2P alter tests that change a "
                  "real column attribute would fail. Does NOT resolve.",
    "rationale": "REJECT comes from the postcondition existential "
                 "disagrees_relevant which quantifies j over [0,len): with the "
                 "`i > 0` guard the loop never inspects index 0, so the "
                 "prefix-preservation invariant (and hence the post-loop "
                 "`return False`) cannot discharge Result()==(other_differs or "
                 "disagrees_relevant) when the witness is j=0 (first listed attr "
                 "schema-relevant and disagreeing).",
})

# 4b. LAST-element off-by-one: stop the scan at len(attrs)-1, dropping the final
#     listed attribute. Correct unless the sole schema-relevant disagreement is
#     the LAST attribute -> returns False when True is required.
_FAN_DROP_LAST = """    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs) - 1:
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        Invariant(MustTerminate(len(attrs) - i + 1))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False
    # impl-end"""
SPEC_TESTS.append({
    "id": "partial-drop-last",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _FAN_IMPL, _FAN_DROP_LAST),
    "refinement": "the faithful real patch would ignore the LAST kwarg key when "
                  "deciding to rebuild. A field pair whose only schema-relevant "
                  "difference is on the last-iterated attribute is then wrongly "
                  "treated as a no-op, so a needed column rebuild is skipped and "
                  "the P2P alter tests fail. Does NOT resolve.",
    "rationale": "REJECT from the postcondition: stopping at len(attrs)-1 leaves "
                 "the loop invariant proven only for k<len-1, so the post-loop "
                 "`return False` cannot discharge Result()==(other_differs or "
                 "disagrees_relevant) when the witness j=len(attrs)-1 disagrees "
                 "and is schema-relevant.",
})

# ===========================================================================
# 5. UNGROUNDED-ORACLE / structural-weakness rivals on schema_irrelevant_attrs.
#    The postcondition pins membership only (`attr_*() in Result()`); a set
#    MISSING any pinned code must be rejected. The load-bearing one is choices.
# ===========================================================================

# 5a. DROP the enumeration attribute (attr_choices) from the set — exactly the
#     pre-patch bug (model_prepatch). Must be rejected by
#     `Ensures(attr_choices() in Result())`.
_SIA_DROP_CHOICES = """    # impl-start
    s = PSet(attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    return s
    # impl-end"""
SPEC_TESTS.append({
    "id": "weak-drop-choices",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SIA_IMPL, _SIA_DROP_CHOICES),
    "refinement": "this is the PRE-PATCH behaviour: non_db_attrs omits "
                  "'choices'. Then _field_should_be_altered keeps a choices-only "
                  "change as a kwargs disagreement and rebuilds the table — the "
                  "exact SQL the issue says should not be generated. The F2P "
                  "test_alter_field_choices_noop asserts no rebuild, so this "
                  "does NOT resolve (it is literally what the gold fixes).",
    "rationale": "REJECT from the load-bearing postcondition "
                 "`Ensures(attr_choices() in Result())`: the returned set lacks "
                 "attr_choices(), so the membership postcondition fails.",
})

# 5b. DROP a legacy schema-irrelevant attribute (verbose_name): a subtler
#     omission that still violates a pinned membership clause. Must be rejected.
_SIA_DROP_VERBOSE = """    # impl-start
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators())
    return s
    # impl-end"""
SPEC_TESTS.append({
    "id": "weak-drop-verbose",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SIA_IMPL, _SIA_DROP_VERBOSE),
    "refinement": "the faithful real patch would omit 'verbose_name' from "
                  "non_db_attrs; then a verbose_name-only change would (wrongly) "
                  "trigger a table rebuild, regressing the long-standing "
                  "no-op-on-verbose_name behaviour the P2P tests rely on. Does "
                  "NOT resolve.",
    "rationale": "REJECT from the exact-set postcondition: verbose_name is "
                 "absent from the returned set, so Result() != the pinned "
                 "12-element PSet.",
})

# 5c. SUPERSET attack (the P1/G-EQ shape the audit exploited under the old
#     membership-only postconditions): add an EXTRA code -- a schema-RELEVANT
#     attribute smuggled into the schema-irrelevant set. Under mere membership
#     this VERIFIED; under exact set equality it must be rejected.
_SIA_SUPERSET = """    # impl-start
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name(), 12)
    return s
    # impl-end"""
SPEC_TESTS.append({
    "id": "weak-superset-extra-attr",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SIA_IMPL, _SIA_SUPERSET),
    "refinement": "code 12 is any attribute OUTSIDE the modelled 12 (the fixed "
                  "injection maps fresh codes to fresh attribute names, e.g. "
                  "'max_length'). The faithful real patch would add that "
                  "schema-RELEVANT attribute to Field.non_db_attrs, so "
                  "_field_should_be_altered strips it before comparing and a "
                  "max_length-only change is (wrongly) treated as a no-op: "
                  "required column rebuilds are silently skipped and the P2P "
                  "alter tests (e.g. AlterField changing max_length) FAIL. Does "
                  "NOT resolve -- this is the verify=/=>correct counterexample "
                  "the old membership-only spec admitted.",
    "rationale": "REJECT from the exact-set postcondition `Ensures(Result() == "
                 "PSet(attr_choices(), ..., attr_verbose_name()))`: the returned "
                 "set has an extra member (12), so set equality fails. Under the "
                 "previous membership-only clauses this variant verified, which "
                 "is precisely the weakness being closed.",
})

# ===========================================================================
# 6. CONTROL-FLOW-EFFECT — N/A. Both modeled functions are pure value
#    computations: schema_irrelevant_attrs returns a freshly-built set;
#    field_alteration_needed returns a bool with no raise / no side-effect on a
#    shared object that the value abstraction would miss. The only observable is
#    the returned value, fully pinned by the postcondition. (See assessment.)
# ===========================================================================

# ===========================================================================
# AXIOMS — none. meta.json axioms == []; the bundle has NO @ContractOnly axiom.
# The two A-reference deep models are validated out-of-band by axiom_check.py /
# G-AX (already passing). PBT axiom lane (real-callee soundness/containment) is
# only for @ContractOnly axioms / A-reference callee probes; here both changed
# sites are spelled out DEEPLY in the impl region and re-checked by the existing
# G-AX, so there is no axiom obligation to re-probe in Docker.
# ===========================================================================
AXIOM_TESTS = []

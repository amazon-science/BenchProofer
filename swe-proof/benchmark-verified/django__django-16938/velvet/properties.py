"""properties.py — G-PBT falsification battery for django__django-16938 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both regions the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct queryIterPlan`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a load-plan carrier):

  queryIterPlan (q : QState) return (out : QState)
    ensures planRejected out = false        -- (R) the plan is never refused
    ensures isRestricted out.related = false -- (S) no named-relation restriction survives
    ensures out.immediate = some ["pk"]      -- (P) the pk-only immediate load is preserved

``QState`` models the two facets of a relation's load plan the deferral
conflict is decided by: ``related`` (a ``RelatedPlan`` — ``unrestricted`` or
``restricted names``) and ``immediate`` (the immediate-load mask,
``Option (List String)``). The three ``ensures`` clauses are all TRANSPARENT and
DECIDABLE — ``planRejected``, ``isRestricted`` and list equality are plain
``def``s over the result, with NO opaque callee in any clause. There is no
answer-key oracle to echo (directive 8 is satisfied structurally), so the
tester+``decide`` witness path is available directly.

WHICH CLAUSE CONSTRAINS THE IMPL. The gold output is the CONSTANT plan
``{ related := .unrestricted, immediate := some ["pk"] }`` for every input ``q``.
(S) and (P) pin it exactly; (R) is a CONSEQUENCE of (S) — ``planRejected`` can
only be ``true`` when the related selection is restricted, so ``isRestricted
out.related = false`` forces ``planRejected out = false``. (R) is nonetheless a
listed top-level clause and is attacked by the central rival below (a plan that
keeps a restriction whose named relation the pk-only mask defers is refused).
The two independent load-bearing clauses are (S) and (P), and each is attacked
by at least one rival.

The implication is STRICTLY one-way, and the audit pinned the gap: (R) does NOT
imply (S). A plan restricted to names that the mask all loads immediately —
``{ .restricted ["pk"], some ["pk"] }`` — satisfies (R) and (P) while violating
(S), so (S) is independently load-bearing and a spec keeping only (R) and (P)
would be weaker. ``rival-fabricate-pk-relation`` is the case that isolates it.
Conversely the three clauses TOGETHER admit exactly one output: from (R), (S),
(P) as hypotheses, ``out = { .unrestricted, some ["pk"] }`` is provable on this
carrier (audit-checked as a standalone theorem), so no wrong impl can satisfy
the spec and the SPEC-TOO-WEAK direction is closed by proof rather than by
sampling rivals.

BINDER STRUCTURE. The postcondition has ONE input binder, ``q``, with two
sub-facets ``q.related`` and ``q.immediate``. The reject witnesses vary ``q``
across four distinct plans, moving BOTH facets: a restricted-with-no-mask plan,
an unrestricted-with-a-non-pk-mask plan, a restricted-with-a-different-mask
plan, and the ordinary default plan (unrestricted, no mask). Because gold's
output is a constant, an impl is discriminated not by how it TRANSFORMS ``q``
position-by-position but by whether it (a) discards the restriction, and (b)
forces the immediate mask to exactly ``["pk"]``; the witnesses exercise both
requirements from inputs that differ on both facets. The default plan is the
point that catches an impl which is correct on conflict-shaped input and wrong
on ordinary input — a rival no conflict-shaped witness can see.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION (nagini's mandatory #3a/#3b, held at
    ``Acc(.,1/2)``) — VACUOUS here. The sibling's rivals write the read-only
    input field (``base.restricted = False`` / ``q.restricted = False``) and are
    rejected for INSUFFICIENT PERMISSION. Lean/Velvet are referentially
    transparent: ``q`` is an immutable value, no binder is ``mut``, there is no
    heap, aliasing, or fractional-permission system to subvert. No read-only
    field to overwrite, so the class is vacuous. No substitute probe fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A: the ``axioms`` region is empty; every clause
    is a transparent ``def`` over the result. No answer key to echo.
  * GROUNDING clause (G) (nagini 4b, ``Result().requested == base.requested``) —
    HALF has no counterpart, half does; the audit split them. The velvet model
    deliberately tracks only relation *restricted-ness* and the immediate mask
    (the granularity the conflict is decided at), NOT a preserved "requested
    set". The modeled transform ``selectAllRelated`` sets ``related :=
    .unrestricted`` REGARDLESS of the input — i.e. gold itself discards the
    input's related selection by design (that is what the no-arg clearing does).
    So the BASE-PRESERVATION half of nagini's
    ``partial-drop-base-fabricate-request`` is genuinely inexpressible: there is
    no input-threaded field for a base-discarding rival to violate, and demanding
    one would contradict gold. But its FABRICATION half IS expressible — a rival
    can invent a related selection of its own, and (S) is what catches it. The
    port originally omitted the whole case; the fabrication half is now attacked
    by ``rival-fabricate-pk-relation``.
  * DIVERGENCE - CLOSED BY THE SEMANTICS, and for the right reason. The nagini
    sibling carries no ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case, so
    there is nothing to port; and this bundle runs under ``set_option
    loom.semantics.termination "total"``, under which a postcondition is claimed
    of ALL runs rather than only terminating ones, so the verifier demands a
    decreasing measure on every loop and discharges its descent. Audit-confirmed
    with real builds rather than by argument: splicing a ``while true`` loop into
    the impl region FAILS to elaborate ("Decreasing annotations are required in
    total correctness semantics"), and the sharper shape fails too, which is what
    rules out dismissing this as merely the annotation linter: a loop CARRYING a
    ``decreasing`` clause whose measure the body never shrinks is rejected on the
    measure's own goal, under that clause's own name. So a diverging rival does
    not verify here. (An earlier version of this bullet argued the disposition
    from a corpus census of ``partial`` bundles against ``total`` ones, citing an
    internal findings doc. That census is withdrawn: all 500 velvet bundles set
    ``"total"``, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness``, so no cohort exists.) No reject case written,
    none claimed dropped: the rejection fires at the ``method``, ahead of any
    appended tester, so no witness can elaborate against the rival.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the postcondition through Velvet's own tester machinery:
``queryIterPlanTester q = false`` says the extracted program's result violates
some ``ensures`` clause at that concrete input ``q``. It is checked in a file
whose ``prove_correct`` block has been stripped, so no tactic script can mask
the verdict. Every clause is decidable and every input is a concrete literal
plan, so ``derive_tester_for`` yields a computable tester and ``decide`` closes.
The frozen impl and every rival are straight-line (no loop), but the rivals
produce a DIFFERENT output value than gold, so the same
``queryIterPlanTester q = false`` statement ELABORATES against the rival (its
output really does violate the postcondition) and FAILS against gold (``decide``
proves the tester is ``true`` there — gold's output satisfies every clause).
No witness binds a hypothesis (all inputs are literal plans that ``decide``), so
no consistency probe is needed. No banned token. Each witness was run against
both the rival (exit 0) and the frozen solution (exit 1) with two real builds.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The three plan transformers
(``selectAllRelated``, ``loadOnlyPk``, ``planRejected``) are A-reference deep
models validated == their real queryset callees by G-AX (axiom_check.py); that
is G-AX's job and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16938"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the two-step chain), all
# ---- text strictly BETWEEN the method's `-- impl-start` / `-- impl-end`. Every
# ---- variant replaces exactly this text, so each edit lies wholly inside the one
# ---- impl region and same_spec holds by construction (asserted at load).
_IMPL = (
    "    let q1 := selectAllRelated q\n"
    "    let q2 := loadOnlyPk q1\n"
    "    return q2"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- impl-start marker, for injecting the in-region admissibility assert.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start marker drifted"

# ---- the frozen proof body. All variants keep it verbatim: the reshaped
# ---- positives still close under `loom_solve` alone (verified out-of-band), and
# ---- the reject rivals' rejection is carried by the witness, not by whether the
# ---- frozen tactic happens to break on the reshape.
_PROOF = "prove_correct queryIterPlan by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The postcondition is decidable (no opaque callee), so
# ---- the tester machinery yields a computable `queryIterPlanTester` and `decide`
# ---- reduces it. `queryIterPlanTester q = false` says the extracted program's
# ---- result violates some `ensures` clause at input `q`. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the verdict.
_TESTER = (
    "extract_program_for queryIterPlan\n"
    "prove_precondition_decidable_for queryIterPlan\n"
    "prove_postcondition_decidable_for queryIterPlan\n"
    "derive_tester_for queryIterPlan\n\n"
)


def _witness(plan_literal):
    return _TESTER + (
        f"example : queryIterPlanTester {plan_literal} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # three-clause obligation and only reshapes the executable surface; the
    # frozen `loom_solve` proof closes for each (verified out-of-band).
    # =====================================================================
    {
        "id": "pos-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        # Construct the gold-chain output value DIRECTLY in one fresh plan,
        # bypassing the two transformer calls. `{ .unrestricted, some ["pk"] }`
        # IS the value the gold chain produces; (S) and (P) are immediate and
        # (R) follows from (S). If this faithful correct impl cannot verify =>
        # SPEC-TOO-STRONG. Ports nagini pos-build-direct-construct.
        "module": _impl(
            "    return { related := RelatedPlan.unrestricted, immediate := some [\"pk\"] }"),
        "rationale": (
            "structurally-different CORRECT impl: instead of chaining the two "
            "plan transformers, construct the gold-chain output value "
            "`{ .unrestricted, some [\"pk\"] }` directly. (S) `isRestricted "
            "out.related = false` and (P) `out.immediate = some [\"pk\"]` are "
            "immediate; (R) `planRejected out = false` follows from (S). The "
            "output is GROUNDED in the modeled behaviour (a constant the spec "
            "pins), not an opaque answer key, so this doubles as proof the spec "
            "is not echo-vulnerable. If it cannot verify => SPEC-TOO-STRONG. "
            "Ports nagini pos-build-direct-construct."),
    },
    {
        "id": "pos-reorder-transforms",
        "kind": "soundness",
        "expect": "verify",
        # REORDER the two transitions: narrow the immediate mask FIRST
        # (loadOnlyPk), then clear the related restriction (selectAllRelated).
        # Both orders yield the same constant output; each transformer touches a
        # disjoint facet, so the composition commutes. Must verify.
        "module": _impl(
            "    let q1 := loadOnlyPk q\n"
            "    let q2 := selectAllRelated q1\n"
            "    return q2"),
        "rationale": (
            "structurally-different CORRECT impl: the two plan transitions are "
            "applied in the opposite order (loadOnlyPk then selectAllRelated). "
            "Each touches a disjoint QState facet (`immediate` vs `related`), so "
            "the composition commutes and yields the same gold output "
            "`{ .unrestricted, some [\"pk\"] }`. If it cannot verify => "
            "SPEC-TOO-STRONG. Ports nagini pos-build-reorder."),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape: bind the chain's result to a typed local before
        # returning it. Identical value flow, different control shape. Must
        # verify. Re-expresses nagini pos-onlypk-local-reshape (whose helper
        # `only_pk` is a pure `def` here, not a method — see accounting).
        "module": _impl(
            "    let q1 := selectAllRelated q\n"
            "    let q2 := loadOnlyPk q1\n"
            "    let out := q2\n"
            "    return out"),
        "rationale": (
            "local-variable reshape: bind the chain's result to a typed local "
            "before returning it (same value flow, different control shape). A "
            "correct reshape must verify (else SPEC-TOO-STRONG). Re-expresses "
            "nagini pos-onlypk-local-reshape on this carrier (the per-facet "
            "transformers are pure `def`s here, so the local-reshape control "
            "shape is carried by the modeled method itself)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause (pre-conditions
    # region empty), so the classic "a normal input is excluded" probe is
    # vacuous. Re-aimed at the nagini admiss argument: the issue's worst-case
    # reproducer input (a related selection RESTRICTED to a named relation, with
    # a pk-only immediate mask that DEFERS that relation — exactly the FieldError
    # trigger) flows through the gold transformer chain to a WELL-FORMED,
    # non-refused plan. An in-region assert (auto-discharged by loom_solve,
    # verified out-of-band) witnesses this; the real impl and frozen proof are
    # kept verbatim so all three ensures still discharge. Else PRECOND-TOO-STRONG
    # / the modeled behaviour would not handle the reproducer.
    # =====================================================================
    {
        "id": "admiss-reproducer-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT-STRENGTHENED. The original assert claimed only
        # `planRejected ... = false` at the reproducer. That is the WEAKEST of
        # the three facts about that point and is implied by the other two, so
        # it left the reproducer's mask and restricted-ness unpinned: an assert
        # that holds of any unrestricted plan whatsoever. Replaced with the
        # assert that pins the reproducer's image EXACTLY (both facets), which
        # is what "the modeled behaviour handles the reproducer" has to mean.
        # Both forms build; a deliberately FALSE assert in the same slot fails
        # to build (checked), so the slot is load-bearing and not ignored.
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START +
            "    assert (with_name_prefix `adm\n"
            "      ((loadOnlyPk (selectAllRelated\n"
            "        { related := RelatedPlan.restricted [\"master\"], immediate := some [\"pk\"] }))\n"
            "        = { related := RelatedPlan.unrestricted, immediate := some [\"pk\"] }))\n"),
        "rationale": (
            "the modeled behaviour must accept the issue's worst-case reproducer: "
            "a related selection RESTRICTED to a named relation with a pk-only "
            "immediate mask that DEFERS that relation (the exact conflict "
            "trigger). The in-region assert pins the reproducer's image under the "
            "gold transformer chain EXACTLY — `{ .unrestricted, some [\"pk\"] }`, "
            "both facets — which entails the plan is not refused AND that the "
            "pk-only optimisation survived on precisely the input that used to "
            "collide. loom_solve discharges the assert VC automatically, and the "
            "real impl + frozen proof are kept verbatim so all three ensures "
            "still discharge. Re-aims nagini admiss-reproducer-shaped-input "
            "(whose read-only fractional-permission half has no counterpart on "
            "this carrier)."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input plan and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P. The input binder `q` is varied
    # across three plans, moving both facets `q.related` and `q.immediate`.
    # =====================================================================
    {
        "id": "rival-keep-restriction",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BUG: narrow the immediate mask to pk-only but NEVER clear
        # the related restriction. On a plan restricted to a named relation, the
        # pk-only mask defers that relation, so planRejected is true. Rejected by
        # (S) (restriction survives) AND (R) (the plan is refused).
        "module": _impl(
            "    let q2 := loadOnlyPk q\n"
            "    return q2"),
        "refinement": (
            "this IS the pre-patch behaviour: the iterator narrows the immediate "
            "load to the primary key but never clears the arriving related "
            "selection. For a related collection whose custom manager bakes a "
            "restricted named-relation selection, the pk-only mask defers that "
            "named relation and the database refuses the plan — exactly the "
            "reported FieldError. The failing tests "
            "(test_serialize_prefetch_related_m2m / test_serialize_only_pk over a "
            "manager with a restricted default selection) fail. Does NOT resolve "
            "— it is literally the bug the fix corrects."),
        "rationale": (
            "REJECT from (S) `isRestricted out.related = false` and (R) "
            "`planRejected out = false`: on an input restricted to a named "
            "relation with no immediate mask, the rival keeps the restriction "
            "(so isRestricted out.related = true, violating (S)) and the pk-only "
            "mask it adds defers that relation (so planRejected out = true, "
            "violating (R)). Refuted at input "
            "`{ .restricted [\"master\"], none }`. If it verified => "
            "SPEC-TOO-WEAK (admits the bug). Ports nagini "
            "partial-prepatch-keep-restriction."),
        "witness": _witness(
            "{ related := RelatedPlan.restricted [\"master\"], immediate := none }"),
    },
    {
        "id": "rival-no-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        # Clear the restriction but OMIT the pk-only narrowing (thread the
        # arriving immediate mask through). Well-formed (unrestricted) and never
        # refused, so (S) and (R) hold; correct only when q.immediate already
        # equals some ["pk"], WRONG otherwise. Rejected by (P).
        "module": _impl(
            "    let q1 := selectAllRelated q\n"
            "    return q1"),
        "refinement": (
            "clears the related selection but omits the pk-only immediate load "
            "(carries the arriving mask through). The serialized related read "
            "would then load every column of each related row instead of just "
            "the primary key — the by-reference / no-superfluous-columns "
            "guarantee is lost. test_serialize_only_pk / "
            "test_serialize_no_only_pk_with_natural_keys assert the cascade "
            "SELECT carries ONLY the pk (no extra relation column); over-loading "
            "columns fails those assertNotIn checks. Does NOT resolve."),
        "rationale": (
            "REJECT from (P) `out.immediate = some [\"pk\"]`: threading the "
            "arriving mask through means `out.immediate = q.immediate`, which "
            "differs from `some [\"pk\"]` whenever the input mask was not already "
            "exactly the primary key. (S) and (R) alone would admit it — (P) is "
            "what rejects it. Refuted at input `{ .unrestricted, some [\"name\"] }` "
            "— a distinct plan from the keep-restriction rival, varying both "
            "facets of `q`. Ports nagini partial-no-projection-narrow."),
        "witness": _witness(
            "{ related := RelatedPlan.unrestricted, immediate := some [\"name\"] }"),
    },
    {
        "id": "rival-overload-immediate",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on (P): clear the restriction AND set an immediate mask that
        # loads the primary key but ALSO an extra named field. Well-formed
        # (unrestricted) so (S) and (R) hold; the mask contains "pk" so a spec
        # that only checked membership would miss it — (P) demands the mask be
        # EXACTLY ["pk"]. Rejected by (P).
        "module": _impl(
            "    let q1 := selectAllRelated q\n"
            "    return { q1 with immediate := some [\"pk\", \"master\"] }"),
        "refinement": (
            "clears the related selection but sets the immediate mask to the "
            "primary key PLUS an extra named field. The cascade SELECT would then "
            "carry a superfluous column beyond the primary key, so "
            "test_serialize_only_pk's assertion that the related query loads ONLY "
            "the pk (no extra relation column) fails. A faithful real patch of "
            "this shape over-selects and does NOT resolve. A genuine near-miss: "
            "the pk IS loaded, but not EXCLUSIVELY."),
        "rationale": (
            "REJECT from (P) `out.immediate = some [\"pk\"]` (EXACT list "
            "equality, not membership): the rival's mask `some [\"pk\", "
            "\"master\"]` contains the primary key but is not equal to "
            "`[\"pk\"]`, so (P) fails. A spec pinning only \"pk\" ∈ mask would "
            "MISS this => SPEC-TOO-WEAK. Refuted at input "
            "`{ .restricted [\"a\", \"b\"], some [\"x\"] }` — a third distinct "
            "plan, again moving both facets of `q`. A near-miss the no-narrow "
            "rival (wrong mask contents entirely) does not subsume; witnessed at "
            "its own distinguishing point."),
        "witness": _witness(
            "{ related := RelatedPlan.restricted [\"a\", \"b\"], immediate := some [\"x\"] }"),
    },

    # =====================================================================
    # ADDED BY AUDIT. The three rivals above are all TOTAL-domain: each is wrong
    # at every input where it is wrong at all, so each is caught at an input that
    # already carries a restriction or a non-pk mask. Neither of the two rivals
    # below is caught by ANY of the three existing witness points (machine-
    # checked: at `{ .restricted ["master"], none }` and
    # `{ .restricted ["a","b"], some ["x"] }` the conditional rival agrees with
    # gold on every observed projection). They probe two genuinely unattacked
    # directions.
    # =====================================================================
    {
        "id": "rival-conditional-clear",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN rival: do the right thing ONLY when the arriving plan is
        # already in conflict, and otherwise pass the plan through untouched. On
        # the reproducer input it is INDISTINGUISHABLE from gold — it clears the
        # restriction and narrows the mask exactly as gold does — so every
        # conflict-shaped witness point misses it. It is wrong on the ordinary
        # input (the default plan: unrestricted, no mask), where it skips the
        # pk-only narrowing entirely. This is the "fix the reported symptom, not
        # the behaviour" rival, and it is the shape a spec that only pinned the
        # non-refusal clause would admit.
        "module": _impl(
            "    let e := if isRestricted q.related then"
            " { related := RelatedPlan.unrestricted, immediate := some [\"pk\"] }\n"
            "             else { related := q.related, immediate := q.immediate }\n"
            "    return e"),
        "refinement": (
            "narrows to the primary key ONLY for a relation whose default "
            "queryset arrived with a restricted named-relation selection, and "
            "leaves every other relation's plan untouched. The conflict-shaped "
            "case is handled, so the reported failure stops reproducing — but for "
            "an ordinary relation the pk-only immediate load is never applied, so "
            "the cascade read loads every column instead of just the primary key. "
            "test_serialize_only_pk asserts the pk-only read for the ORDINARY "
            "relations too (its assertNotIn checks over the earlier queries in "
            "the batch, not only the restricted one), and the query-count "
            "assertions in test_serialize_prefetch_related_m2m are taken over the "
            "whole batch. Does NOT resolve: it makes the optimisation "
            "conditional on the very state the fix exists to make irrelevant."),
        "rationale": (
            "REJECT from (P) `out.immediate = some [\"pk\"]`: on the DEFAULT "
            "arriving plan `{ .unrestricted, none }` the rival takes its else "
            "branch and returns `q` unchanged, so `out.immediate = none ≠ "
            "some [\"pk\"]`. (R) and (S) both HOLD at that point (the plan is "
            "unrestricted and so cannot be refused), which is exactly why the "
            "case matters: the rival is refuted by (P) alone and by no other "
            "clause. Refuted at a FOURTH distinct input — the only one of the "
            "battery's points that is unrestricted AND maskless, the ordinary "
            "non-conflict plan the three existing witnesses never visit. "
            "Machine-checked to AGREE with gold on both observed facets at the "
            "two conflict-shaped witness points, so no existing case subsumes "
            "it. If it verified => SPEC-TOO-WEAK (admits a fix that is "
            "conditional on the conflict). No nagini sibling."),
        "witness": _witness(
            "{ related := RelatedPlan.unrestricted, immediate := none }"),
    },
    {
        "id": "rival-fabricate-pk-relation",
        "kind": "uniqueness",
        "expect": "reject",
        # (S)-ISOLATING rival. It returns a plan whose related selection is
        # RESTRICTED, but restricted to the primary key itself — the one family of
        # restricted plans that does NOT trip the refusal predicate, since the
        # single named relation is the very field the mask loads immediately.
        # So (R) `planRejected out = false` and (P) hold, and ONLY (S) rejects it.
        # This is the analogue the port recorded as having "no carrier
        # counterpart" for nagini's base-discarding rival: the model does drop the
        # arriving selection by design, but it can still be caught FABRICATING a
        # selection of its own, which is the half that is expressible here.
        "module": _impl(
            "    return { related := RelatedPlan.restricted [\"pk\"],"
            " immediate := some [\"pk\"] }"),
        "refinement": (
            "keeps the primary-key-only immediate load but hands the database a "
            "related selection that is still RESTRICTED — naming the primary key "
            "as the relation to follow. Because the named relation is the one "
            "field the mask does load, the deferral conflict does not fire, so "
            "this rival never raises; it fails the other way. A restricted "
            "selection joins the named relation into the cascade read, so the "
            "read carries columns beyond the primary key and "
            "test_serialize_only_pk's assertNotIn on the related query's SQL "
            "fails; the extra join also changes the query counts the "
            "prefetch_related test pins. Does NOT resolve — and it shows the "
            "spec's no-restriction clause is doing work its non-refusal clause "
            "cannot do."),
        "rationale": (
            "REJECT from (S) `isRestricted out.related = false` ALONE. This is "
            "the only rival in the battery that isolates (S): the manifest notes "
            "(R) follows from (S), but the converse fails, and the gap is exactly "
            "the restricted-to-loaded-names plans. Machine-checked on this "
            "carrier: `planRejected { .restricted [\"pk\"], some [\"pk\"] } = "
            "false`, so (R) holds; (P) holds by construction; only (S) refutes "
            "it. A spec that had dropped (S) as redundant and kept only (R) and "
            "(P) would ADMIT this impl => SPEC-TOO-WEAK. Refuted at the ordinary "
            "default plan, where the tester sees the fabricated restriction. "
            "Re-aims the nagini partial-drop-base-fabricate-request rival: its "
            "base-preservation half is genuinely absent here (gold discards the "
            "arriving selection by design), but its FABRICATION half is "
            "expressible and is attacked here."),
        "witness": _witness(
            "{ related := RelatedPlan.unrestricted, immediate := none }"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts THREE functions (clear_specific_request, only_pk,
# build_pk_iterator) over a fractional-permission `Fetch` carrier and ships 8
# SPEC cases. This bundle models a NARROWER surface: ONE method `queryIterPlan`
# (nagini's build_pk_iterator) over an immutable `QState` load-plan carrier;
# `clear_specific_request` / `only_pk` become pure `def`s (`selectAllRelated` /
# `loadOnlyPk`), not separately-contracted methods, so cases attached to them
# have no method obligation to attack. This is carrier narrowing, not a gap.
#
#   nagini case                          -> here
#   -----------------------------------------------------------------------
#   pos-build-direct-construct           -> pos-direct-construct       PORTED
#   pos-build-reorder                    -> pos-reorder-transforms     PORTED
#   pos-onlypk-local-reshape             -> pos-local-reshape          RE-EXPRESSED
#   admiss-reproducer-shaped-input       -> admiss-reproducer-shaped-input RE-AIMED
#   frame-mut-base-restricted-write      -> (none)                     VACUOUS
#   frame-mut-clear-q-restricted-write   -> (none)                     VACUOUS
#   partial-prepatch-keep-restriction    -> rival-keep-restriction     PORTED (central)
#   partial-drop-base-fabricate-request  -> rival-fabricate-pk-relation HALF-PORTED (audit)
#   partial-no-projection-narrow         -> rival-no-narrow            PORTED
#   (new, no sibling)                    -> rival-overload-immediate   ADDED
#   (new, no sibling)                    -> rival-conditional-clear    ADDED (audit)
#   AXIOM_TESTS (empty)                  -> (none)                     DROPPED (G-AX lane)
#
# 9 velvet SPEC cases: 3 soundness, 1 admissibility, 5 uniqueness.
#
# PORTED (pos-direct-construct, pos-reorder-transforms): the two nagini positives
#   carry over intact — construct the gold output directly, and reorder the two
#   transforms (which commute here because each touches a disjoint QState facet).
#   Both keep the frozen `loom_solve` proof (it closes for each reshape; verified
#   out-of-band).
# RE-EXPRESSED (pos-onlypk-local-reshape -> pos-local-reshape): the nagini case
#   is a local-variable reshape of the `only_pk` HELPER, which on this carrier is
#   the pure `def loadOnlyPk`, not a contracted method — there is no `only_pk`
#   obligation to defend separately. The same "a correct local-variable reshape
#   must verify" argument is carried by a local-binding reshape of the modeled
#   method itself.
# RE-AIMED (admiss-reproducer-shaped-input): the nagini case builds the worst-case
#   reproducer input, feeds it through the gold chain, and asserts the built
#   result is well-formed, backed by the read-only fractional-permission
#   precondition being establishable. This carrier has no `require` and no heap
#   permission, so that half is vacuous; the WELL-FORMEDNESS half is re-aimed as
#   an in-region assert that the reproducer plan flows to a non-refused plan
#   (`planRejected ... = false`), which loom_solve discharges automatically.
# VACUOUS (frame-mut-base-restricted-write, frame-mut-clear-q-restricted-write):
#   both nagini rivals write a read-only input field held at `Acc(.,1/2)` and are
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent, declares no `mut` binder, and has no heap / aliasing / permission
#   system — no read-only field to overwrite. Not fabricated (porting map: this
#   class is vacuous here).
# HALF-PORTED (partial-drop-base-fabricate-request -> rival-fabricate-pk-relation):
#   the nagini rival violates the GROUNDING clause (G) `Result().requested ==
#   base.requested` by fabricating the request as {pk}. Its BASE-PRESERVATION half
#   is genuinely inexpressible here: the model tracks only restricted-ness and the
#   immediate mask, and gold's `selectAllRelated` sets `related := .unrestricted`
#   REGARDLESS of the input, so gold itself discards the arriving selection and a
#   clause demanding it be preserved would be false of gold. But its FABRICATION
#   half survives the narrowing, and the port's original "no analogue" verdict was
#   too broad: a rival can still invent a restricted selection, and (S) rejects
#   it. Landed by the audit as `rival-fabricate-pk-relation`, restricted to ["pk"]
#   so that (R) and (P) both HOLD and (S) is the sole refuting clause.
# PORTED (rival-keep-restriction): the nagini pre-patch bug — narrow the immediate
#   load but never clear the restriction — is the CENTRAL rival, attacking (S) and
#   (R). It is the exact modeled prepatch behaviour. PORTED (rival-no-narrow): the
#   nagini no-projection-narrow rival — clear the restriction but omit the pk-only
#   narrowing — attacks (P). ADDED (rival-overload-immediate): a near-miss on (P)
#   that loads the pk PLUS an extra field, forcing (P) to be EXACT list equality
#   rather than membership. A real divergence with a machine-checked witness.
#
# CLAUSE / BINDER / POINT COVERAGE. The two independent load-bearing clauses (S)
#   `isRestricted out.related = false` and (P) `out.immediate = some ["pk"]` are
#   each attacked: (S) by rival-keep-restriction (jointly with (R)) and by
#   rival-fabricate-pk-relation (in ISOLATION — the only case where (S) is the
#   sole refuting clause), (P) by rival-no-narrow, rival-overload-immediate and
#   rival-conditional-clear. (R) `planRejected out = false` — a consequence of
#   (S), true whenever isRestricted is false — is also attacked by
#   rival-keep-restriction (a surviving restriction whose named relation the mask
#   defers is refused). The sole input binder `q` is varied across FOUR distinct
#   plans — `{ .restricted ["master"], none }`, `{ .unrestricted, some ["name"] }`,
#   `{ .restricted ["a","b"], some ["x"] }`, and the ordinary default plan
#   `{ .unrestricted, none }` — moving BOTH facets `q.related` and `q.immediate`
#   and covering both values of each facet's shape, so no binder facet is held
#   fixed by every witness.
#
#   The fourth point is what the audit added and it is not a fourth spelling of
#   the same place: the first three all carry a restriction or a non-pk mask, so
#   every rival they catch is one that is wrong on conflict-shaped input. A
#   PARTIAL-DOMAIN rival that repairs only the conflict case and passes ordinary
#   plans through untouched agrees with gold on both observed facets at all three
#   of the original points (machine-checked) and is caught only at the default
#   plan. rival-conditional-clear is that rival. The three positives and the
#   admissibility case defend all three clauses on gold-shaped and
#   reproducer-shaped inputs.
#
# WITNESS MECHANICS: the postcondition is fully DECIDABLE (no opaque callee — every
#   clause is a transparent `def` over the result), so `derive_tester_for` yields a
#   computable `queryIterPlanTester` and `decide` closes at a concrete literal
#   plan. Each rival produces a different output value than gold's constant plan,
#   so `queryIterPlanTester q = false` ELABORATES against the rival (its output
#   violates the postcondition at that input) and FAILS against gold (`decide`
#   proves the tester true there). No witness binds a hypothesis, so no consistency
#   probe is needed. All FIVE checked with scripts/lean_verify.sh: rival exit 0,
#   gold build exit 1. The audit re-derived each of the five gold-side builds and
#   confirmed the failure is a SEMANTIC refutation, not a syntactic accident: the
#   error text is "Tactic `decide` proved that the proposition
#   queryIterPlanTester <that plan> = false is false" — the kernel evaluated the
#   claim and found gold satisfies the postcondition there. No unknown
#   identifier, no type error, no stuck reduction, no timeout.
#
# AXIOM_TESTS: dropped. The three plan transformers are A-reference deep models
#   validated == their real queryset callees by G-AX (axiom_check.py / mapping.md);
#   that is G-AX's lane and the G-PBT gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []

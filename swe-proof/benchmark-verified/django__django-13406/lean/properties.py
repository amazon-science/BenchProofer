"""properties.py — G-PBT falsification battery for django__django-13406 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_installQuery`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts ``attach_description(rs, value)`` over a heap-object carrier
(``ResultSet``/``LookupDescription`` with fractional permissions) and pins the
producer-tag switch on an integer field-count. This Lean bundle models the SAME
single purely-functional core — installing a prepared query into a result set,
switching the row-building strategy when the query projects specific fields —
over a ``ResultSet``/``StoredQuery`` structure carrier, and the SAME grounding:
the postcondition relates ``result`` to the inputs structurally (identity store
+ two conditional strategy clauses), with no opaque answer key to echo. Every
nagini SPEC case carries over as an attack on one of the three top-level
postcondition clauses, or as a faithful correct positive. The nagini
frame/permission-mutation class and the AXIOM lane are re-dispositioned below
(see ``assessment`` at the bottom).

DEFENDED SURFACE (one modeled behavior; three independent top-level clauses).
``problem_spec_installQuery rs value result`` pins EXACTLY:

  * (C1 identity)  ``result.storedQuery = value`` — the installed query is the
    stored one, in every case (frame: the query component always equals its
    input);
  * (C3 project)   ``value.selectedFields ≠ [] → result.rowMode =
    fieldValuesDict`` — a field-projecting query switches the row-builder to the
    field-value-mapping strategy, regardless of the prior strategy. THIS is the
    fix;
  * (C4 preserve)  ``value.selectedFields = [] → result.rowMode = rs.rowMode`` —
    a query that projects no specific fields leaves the prior row-builder
    untouched (frame: the unchanged branch pins the component to its input).

The BEHAVIOURAL DISCRIMINATOR (the fix) is grounded entirely in the argument
``value.selectedFields`` (a list; the test is non-emptiness). There is no opaque
oracle in the contract an impl could echo without doing the work — doing the
conditional switch IS the work — so there is no ungrounded-echo SPEC-TOO-WEAK
shortcut, and the honest cheapest correct impl is a positive control rather than
a rival (ports the nagini reasoning at its lines 40-47).

BINDER STRUCTURE. The spec predicate has THREE input binders: ``rs`` (the result
set, observed through ``rs.rowMode`` and ``rs.storedQuery``) and ``value``
(observed through ``value.selectedFields``). The load-bearing sub-inputs are
``rs.rowMode`` (the prior row-builder, load-bearing only on the C4 empty branch),
``rs.storedQuery`` (the prior query, load-bearing only for C1), and
``value.selectedFields`` (the discriminator for C3 vs C4). All three are varied
across the reject witnesses (see the point-spread block at the bottom):
``value.selectedFields ∈ {[], ["name"], ["a","b"]}``, ``rs.rowMode ∈
{modelInstances, fieldValuesTuple}``, ``rs.storedQuery ∈ {[], ["old"]}``. The
six reject witnesses probe six DISTINCT input tuples, and C1 is pinned on BOTH
branches of the guard (a field-projecting install and an empty one).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION-MUTATION as such — VACUOUS on this carrier. The nagini
    sibling's mandatory ``frame-mutate-count`` rival writes through the
    read-only (``Acc(...,1/2)``) reference to ``value.value_field_count`` and is
    rejected by the PERMISSION SYSTEM. That rejection source does not exist
    here: ``value`` is an immutable structure value, there is no fractional
    permission and no read-only cell to overwrite, so nothing in this bundle
    checks frame protection and no case below should be read as attesting that
    it holds.

    What IS portable is the BEHAVIOUR the sibling probe exists to forbid — an
    impl declining to honour the input it was handed — which on an immutable
    carrier is written by shadowing the argument with a cleared copy. That is
    attacked by ``frame-shadow-input`` below. NOTE the honest attribution: that
    rival is rejected by the ordinary postcondition clauses (C1 identity and C3
    projection), exactly as the partial-domain rivals are — NOT by any frame or
    permission machinery. It is a worthwhile extra input-handling rival, not a
    substitute for the sibling's permission check, and the sibling's
    permission-system coverage is genuinely UNREPLACED here.

  * DIVERGENCE / NON-TERMINATION — VACUOUS. ``implementation_installQuery`` is a
    total Lean ``def``; a diverging implementation cannot be written at all on
    this backend, so the class is genuinely vacuous (not a spec hole).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: never switching the row-builder (the pre-fix
    bug, attacks C3); switching unconditionally (attacks C4 on the empty branch);
    an off-by-one guard that misses the single-field case (attacks C3 at
    length 1); and omitting the store (attacks C1).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate at one CONCRETE
ground input (all inputs are literal structures, so the witness head binds
NOTHING and there are no hypotheses whose consistency could be in question),
unfolds the impl and spec, and closes by ``simp only [Id.run]`` then ``decide``.
Each was checked with FOUR real ``lake env lean`` builds: it HOLDS of its rival,
it FAILS on the frozen solution, and — the check that makes the second build
evidence rather than noise — the FLIPPED claim (assert the spec HOLDS at the same
input) ELABORATES on the frozen solution while FAILING on the rival. So gold's
exit code tracks the CLAIM, not merely the file, and the discrimination is a
refutation rather than a reduction artifact. See the AUDIT REPAIR note at the
bottom for the three cases where this was not initially true.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` carries over the nagini argument that its
faithful real counterpart mishandles the pickled-query reinstall, so a reloaded
query yields the wrong row shape (model instances where value-dicts are demanded
or vice versa) and the F2P pickle tests (test_annotation_values /
test_annotation_values_list / test_annotation_with_callable_default) would
mismatch — so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the row-builder strategies are modeled directly as ``RowMode``
constructors, sentinels selected but never invoked); the axiom lane belongs to
G-AX, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-13406"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The conditional row-builder switch (the fix). Lies wholly inside
# `-- impl-start`/`-- impl-end`.
_I_SWITCH = ("  if value.selectedFields ≠ [] then\n"
             "    rs := { rs with rowMode := RowMode.fieldValuesDict }")
# The switch condition alone.
_I_COND = "  if value.selectedFields ≠ [] then"
# The store of the installed query, followed by the return.
_I_STORE_RET = ("  rs := { rs with storedQuery := value }\n"
                "  return rs")
# The switch block followed by the store (the whole tail of the loop body), used
# by the reorder positive and the prepatch rival.
_I_SWITCH_STORE = ("  if value.selectedFields ≠ [] then\n"
                   "    rs := { rs with rowMode := RowMode.fieldValuesDict }\n"
                   "  rs := { rs with storedQuery := value }")

# The frozen proof's `intro` line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro rs value"


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one ground input, unfolds, and
# closes. EVERY case closes with `simp only [Id.run]` then `decide`, and the
# uniformity is load-bearing rather than stylistic — see the AUDIT REPAIR note in
# the accounting block at the bottom. A bare `simp [Id.run]` also "closes" the
# three row-mode cases against their rivals, but on the FROZEN solution it leaves
# an unreduced `pure { ... }` residual and so fails for a REDUCTION reason rather
# than by refuting anything: the flipped claim (assert the spec HOLDS at the same
# point) fails on gold with the same `unsolved goals ... (pure {...})` shape, so
# gold's exit code carried no information about the claim. `decide` runs the
# `DecidableEq` instances the carrier derives for `RowMode` and `StoredQuery`
# through the kernel, which DOES evaluate the `Id.run` do-block: gold then reports
# `decide proved the proposition ¬(...) is false` (a refutation of the concrete
# claim) and the flipped claim ELABORATES on gold while failing on the rival.
# That asymmetry is what makes each rejection attributable to the spec.
# ---------------------------------------------------------------------------
def _w(prior_mode, prior_fields, fields, closer):
    """Refute `problem_spec_installQuery` at a ground input.

    prior_mode  : the prior `rs.rowMode` (a `RowMode` constructor name)
    prior_fields: the prior `rs.storedQuery.selectedFields` (a Lean list literal)
    fields      : the installed `value.selectedFields` (a Lean list literal)
    closer      : the closing tactic line(s)
    """
    rs = (f"{{ rowMode := RowMode.{prior_mode}, "
          f"storedQuery := {{ selectedFields := {prior_fields} }} }}")
    val = f"{{ selectedFields := {fields} }}"
    return (
        f"example : ¬ problem_spec_installQuery\n"
        f"    {rs}\n"
        f"    {val}\n"
        f"    (implementation_installQuery\n"
        f"      {rs}\n"
        f"      {val}) := by\n"
        f"  unfold problem_spec_installQuery implementation_installQuery\n"
        f"{closer}")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_installQuery` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Store the query FIRST, then apply the conditional switch. The store does
        # not touch rowMode, so reordering is behaviourally identical; C1/C3/C4 all
        # still hold. The frozen proof closes unchanged (verified: real build).
        "module": _swap(
            _BASE, _I_SWITCH_STORE,
            "  rs := { rs with storedQuery := value }\n"
            "  if value.selectedFields ≠ [] then\n"
            "    rs := { rs with rowMode := RowMode.fieldValuesDict }"),
        "rationale": "structurally-different but correct: install the query FIRST, "
                     "then apply the conditional row-builder switch. The store does "
                     "not touch rowMode so the reorder is behaviourally identical; "
                     "C1/C3/C4 all hold. If this fails to verify => the spec is "
                     "over-fit to the gold statement order (SPEC-TOO-STRONG). Also "
                     "the honest no-ungrounded-echo control: the discriminator is "
                     "the argument selectedFields, so the conditional switch IS the "
                     "work, not an echo. Ports nagini pos-control-reorder.",
    },
    {
        "id": "pos-control-explicit-else",
        "kind": "soundness",
        "expect": "verify",
        # Explicit two-armed if/else whose empty arm re-writes rowMode to its own
        # current value (a value-preserving self-assignment). Behaviourally
        # identical (the else writes the same mode), so C3 and C4 both hold. The
        # frozen proof closes unchanged (verified: real build).
        "module": _swap(
            _BASE, _I_SWITCH,
            "  if value.selectedFields ≠ [] then\n"
            "    rs := { rs with rowMode := RowMode.fieldValuesDict }\n"
            "  else\n"
            "    rs := { rs with rowMode := rs.rowMode }"),
        "rationale": "structurally-different but correct: an explicit two-armed "
                     "if/else whose empty-selection arm re-writes rowMode to its own "
                     "current value (value-preserving self-assignment). "
                     "Behaviourally identical to the gold implicit-else, so C3 "
                     "(non-empty -> fieldValuesDict) and C4 (empty -> prior "
                     "preserved) both hold. A branch-reshape, not a new induction. "
                     "If it fails => the spec is over-fit to the implicit-else shape "
                     "(SPEC-TOO-STRONG). Ports nagini pos-control-explicit-else.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition binder
    # to attack (every input is admissible), so the nagini precondition-admission
    # self-call re-expresses as: discharge the spec predicate by evaluation at a
    # concrete F2P-shaped install (a fresh model-instance result set fed a
    # single-field query — the values('name') case) as a `have`, then close the
    # frozen obligation verbatim. Nothing assumed: no new declaration, statement
    # byte-identical, ground instance is a `have` prepended to the tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-value-bearing",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_installQuery\n"
            "      { rowMode := RowMode.modelInstances, "
            "storedQuery := { selectedFields := [] } }\n"
            "      { selectedFields := [\"name\"] }\n"
            "      (implementation_installQuery\n"
            "        { rowMode := RowMode.modelInstances, "
            "storedQuery := { selectedFields := [] } }\n"
            "        { selectedFields := [\"name\"] }) := by\n"
            "    unfold problem_spec_installQuery implementation_installQuery\n"
            "    simp only [Id.run]\n"
            "    refine ⟨rfl, ?_, ?_⟩\n"
            "    · intro _; rfl\n"
            "    · intro h; exact absurd h (by decide)\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at an F2P-shaped install (a "
                     "fresh model-instance result set fed a single-field query — the "
                     "values('name') case of test_annotation_values) by evaluation "
                     "as a `have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable at "
                     "exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, ground instance is a `have` in the "
                     "existing tactic body. Ports nagini admiss-value-bearing.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the pre-patch bug: never switch the row-builder (attacks C3) ----
    {
        "id": "partial-prepatch-no-switch",
        "kind": "uniqueness",
        "expect": "reject",
        # The EXACT pre-patch behaviour: store the query but NEVER switch the
        # row-builder. Correct on every empty-selection input (C4 holds) but on
        # every field-projecting input the row-builder is left at its prior value.
        "module": _swap(_BASE, _I_SWITCH_STORE,
                        "  rs := { rs with storedQuery := value }"),
        "refinement": "this is the EXACT pre-patch behaviour: the pre-patch setter "
                      "stored the query only, leaving the row-builder at its prior "
                      "(model-instance) default. Its faithful real patch is the "
                      "pre-patch setter, which FAILS the F2P tests "
                      "test_annotation_values / test_annotation_values_list (a "
                      "reloaded field-projecting query then yields model instances, "
                      "so the reloaded result is a model object, not the expected "
                      "field-value mapping). So it would NOT resolve.",
        "rationale": "partial-domain: correct on every empty-selection input (C4 "
                     "holds) but on every field-projecting input it leaves the "
                     "row-builder at its prior value. Rejection source: C3 "
                     "(value.selectedFields ≠ [] → result.rowMode = "
                     "RowMode.fieldValuesDict). Refuted at "
                     "value=[\"a\",\"b\"], prior rowMode = fieldValuesTuple (a "
                     "field-projecting prior that the fix must still collapse to "
                     "fieldValuesDict). If it verified => SPEC-TOO-WEAK (admits the "
                     "pre-patch no-switch bug).",
        "witness": _w("fieldValuesTuple", "[]", '["a", "b"]',
                      "  simp only [Id.run]\n  decide\n"),
    },

    # ---- switch unconditionally: drop the guard (attacks C4) ----
    {
        "id": "partial-uncond-switch",
        "kind": "uniqueness",
        "expect": "reject",
        # Always switch the row-builder to fieldValuesDict, dropping the guard.
        # Correct on every field-projecting input (C3 holds) but on an
        # empty-selection input it overwrites the prior row-builder.
        "module": _swap(_BASE, _I_SWITCH,
                        "  rs := { rs with rowMode := RowMode.fieldValuesDict }"),
        "refinement": "this corresponds to dropping the projects-fields guard so the "
                      "setter installs the field-value-mapping row-builder for EVERY "
                      "installed query, including plain model queries. Its faithful "
                      "real patch would make a reloaded plain query yield field-value "
                      "mappings instead of model instances, breaking the "
                      "model-instance pickle PASS_TO_PASS tests (which expect a "
                      "reloaded plain queryset to still produce model objects). So it "
                      "would NOT resolve.",
        "rationale": "partial-domain: correct on every field-projecting input (C3 "
                     "holds) but on an empty-selection input it overwrites the prior "
                     "row-builder. Rejection source: C4 (selectedFields = [] → "
                     "rowMode = rs.rowMode) — when the prior rowMode is not "
                     "fieldValuesDict the unconditional write violates it. Refuted "
                     "at value=[], prior rowMode = modelInstances. If it verified => "
                     "SPEC-TOO-WEAK (admits the guard-dropped bug).",
        "witness": _w("modelInstances", "[]", "[]",
                      "  simp only [Id.run]\n  decide\n"),
    },

    # ---- off-by-one guard: switch only when more than one field (attacks C3) ----
    {
        "id": "partial-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one guard: switch only when MORE THAN ONE field is projected, so a
        # single-field query (the common values('name') case) is wrongly left at
        # the prior row-builder. Correct on empty (preserved) and length>=2
        # (switched), diverges only on the length==1 sub-domain.
        "module": _swap(_BASE, _I_COND,
                        "  if value.selectedFields.length > 1 then"),
        "refinement": "this corresponds to a guard testing 'more than one projected "
                      "field' instead of the real 'projects any field' test. A "
                      "single-field query (e.g. values('name'), the "
                      "test_annotation_values case, whose projection has exactly one "
                      "field) would be left at the model-instance row-builder, so "
                      "the reloaded query yields a model instance instead of the "
                      "expected field-value mapping. So it would FAIL the F2P and "
                      "NOT resolve.",
        "rationale": "partial-domain off-by-one: correct on length==0 (preserved) "
                     "and length>=2 (switched), diverges only on the length==1 "
                     "sub-domain (the common single-field case). Rejection source: "
                     "C3 at length==1 (selectedFields ≠ [] holds, but rowMode is not "
                     "set to fieldValuesDict). Refuted at value=[\"name\"], prior "
                     "rowMode = modelInstances. If it verified => SPEC-TOO-WEAK "
                     "(drops the single-field case).",
        "witness": _w("modelInstances", "[]", '["name"]',
                      "  simp only [Id.run]\n  decide\n"),
    },

    # ---- drop the store: never install the query (attacks C1) ----
    {
        "id": "drop-store",
        "kind": "uniqueness",
        "expect": "reject",
        # Switch the row-builder correctly but never store the installed query, so
        # rs.storedQuery keeps its pre-call value. C3/C4 hold; C1 fails.
        "module": _swap(_BASE, _I_STORE_RET, "  return rs"),
        "refinement": "this corresponds to dropping the query store from the setter: "
                      "the row-builder is configured but the pickled query is never "
                      "actually installed, so the reloaded result set keeps running "
                      "its original (empty) query and the reloaded result does not "
                      "reflect the pickled projection at all. A faithful real patch "
                      "omitting the store would leave the reloaded queryset on its "
                      "original query, so the F2P tests would FAIL. So it would NOT "
                      "resolve.",
        "rationale": "value-identity miss: the row-builder is set correctly (C3/C4 "
                     "hold) but the store is omitted, so rs.storedQuery keeps its "
                     "pre-call value. Rejection source: C1 (result.storedQuery = "
                     "value) — the stored query is not the installed value. Refuted "
                     "at prior storedQuery = [\"old\"], value=[\"name\"] (distinct "
                     "queries), so the retained prior query ≠ the installed one. If "
                     "it verified => SPEC-TOO-WEAK (the identity-store guarantee is "
                     "hollow).",
        "witness": _w("modelInstances", '["old"]', '["name"]',
                      "  simp only [Id.run]\n  decide\n"),
    },

    # ---- conditional store: install only on the field-projecting branch -----
    # (attacks C1 on the EMPTY branch, which `drop-store` leaves unprobed)
    {
        "id": "cond-store-nonempty-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Switch AND store, but both only under the guard: an installed query
        # that projects no specific fields is never stored at all. C3 holds and
        # C4 holds (the prior row-builder survives), but C1 fails on exactly the
        # empty-projection branch — the sub-domain `drop-store` cannot reach,
        # since its witness installs a field-projecting query.
        "module": _swap(
            _BASE, _I_SWITCH_STORE,
            "  if value.selectedFields ≠ [] then\n"
            "    rs := { rs with rowMode := RowMode.fieldValuesDict }\n"
            "    rs := { rs with storedQuery := value }"),
        "refinement": "this corresponds to folding the query store INSIDE the "
                      "projects-fields guard, so installing a plain (no specific "
                      "fields) query leaves the result set running its previous "
                      "query. Its faithful real patch would make reinstalling a "
                      "pickled plain query a silent no-op, so a reloaded plain "
                      "result set keeps answering the old query — the "
                      "model-instance pickle PASS_TO_PASS tests (which reload a "
                      "plain queryset and expect its own rows back) would "
                      "mismatch. So it would NOT resolve.",
        "rationale": "value-identity miss on the OTHER branch: C3 holds "
                     "(field-projecting installs still switch and store) and C4 "
                     "holds (the prior row-builder survives an empty "
                     "projection), but the store is skipped when "
                     "selectedFields = [], so the stored query is stale exactly "
                     "there. Rejection source: C1 (result.storedQuery = value) "
                     "on the empty branch. Refuted at prior storedQuery = "
                     "[\"old\"], value=[] (distinct queries). Complements "
                     "drop-store, which pins C1 only at a field-projecting "
                     "value and so cannot see a guard that stores there "
                     "correctly. If it verified => SPEC-TOO-WEAK (C1 is only "
                     "enforced on the branch the fix touches).",
        "witness": _w("modelInstances", '["old"]', "[]",
                      "  simp only [Id.run]\n  decide\n"),
    },

    # ---- shadow the input with a cleared copy (the frame class, re-expressed) -
    {
        "id": "frame-shadow-input",
        "kind": "uniqueness",
        "expect": "reject",
        # The referentially-transparent analogue of the nagini frame-mutation
        # rival: rather than WRITE to the read-only argument (impossible here),
        # shadow it with a copy whose projection has been cleared, then run the
        # gold body verbatim against the copy. The impl now never observes the
        # projection it was handed: the guard always fails (no switch) and the
        # query it stores is the cleared copy, not the installed value.
        "module": _swap(
            _BASE, _I_SWITCH_STORE,
            "  let value := { value with selectedFields := ([] : List String) }\n"
            "  if value.selectedFields ≠ [] then\n"
            "    rs := { rs with rowMode := RowMode.fieldValuesDict }\n"
            "  rs := { rs with storedQuery := value }"),
        "refinement": "no faithful real patch corresponds to this: the setter "
                      "only READS the projection off the query it is installing "
                      "and must never blank it (that would corrupt the pickled "
                      "query being reinstalled). The rival exists to test "
                      "whether an impl can dodge the discriminator by "
                      "substituting a cleared stand-in for its own input — the "
                      "referentially-transparent analogue of the sibling's "
                      "read-only-mutation probe. Its faithful counterpart "
                      "reinstalls a blanked query with the model-instance row "
                      "builder, so the F2P pickle tests "
                      "(test_annotation_values / test_annotation_values_list) "
                      "see model instances and the wrong query. So it would NOT "
                      "resolve.",
        "rationale": "discriminator-clearing (the frame class, re-expressed for "
                     "an immutable carrier). Both output components are wrong at "
                     "once on a field-projecting input: C1 fails (the stored "
                     "query is the cleared copy, not value) and C3 fails (the "
                     "guard reads the cleared copy, so the row-builder is never "
                     "switched). Rejection source: C1 primarily, C3 "
                     "concurrently. Refuted at value=[\"name\"], prior rowMode = "
                     "modelInstances. If it verified => SPEC-TOO-WEAK: an impl "
                     "could satisfy the contract by ignoring the projection it "
                     "was handed. Carries over the BEHAVIOUR the nagini "
                     "frame-mutate-count rival forbids, but NOT its rejection "
                     "source: that rival is caught by the permission system, "
                     "which has no counterpart on this immutable carrier, "
                     "whereas this one is caught by the ordinary postcondition "
                     "clauses. It is an extra input-handling attack, not "
                     "evidence that frame protection is checked here.",
        "witness": _w("modelInstances", "[]", '["name"]',
                      "  simp only [Id.run]\n  decide\n"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 2-probe AXIOM lane.
# This bundle models the SAME single purely-functional core (installing a query
# + the conditional row-builder switch) and re-expresses EVERY sibling SPEC
# case. Every sibling case is recorded below.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder          -> pos-control-reorder        PORTED
#   pos-control-explicit-else    -> pos-control-explicit-else  PORTED
#   admiss-value-bearing         -> admiss-value-bearing       RE-EXPRESSED
#   partial-prepatch-no-switch   -> partial-prepatch-no-switch PORTED (C3)
#   partial-uncond-switch        -> partial-uncond-switch      PORTED (C4)
#   partial-off-by-one           -> partial-off-by-one         PORTED (C3)
#   drop-store                   -> drop-store                 PORTED (C1)
#   frame-mutate-count           -> frame-shadow-input         RE-EXPRESSED (C1+C3)
#   (none; audit addition)       -> cond-store-nonempty-only   ADDED (C1, empty branch)
#   AXIOM_TESTS (2)              -> (none)                     DROPPED (G-AX)
#
# AUDIT NOTE (independent audit of this port). The sibling's MANDATORY
# frame-mutation class splits into two things that must not be conflated:
#   (a) its REJECTION SOURCE — the permission system refusing a write through a
#       1/2 reference. This is genuinely VACUOUS/UNREPLACED here: there is no
#       fractional permission on this carrier, so no case in this battery
#       exercises frame protection and none should be read as attesting to it.
#   (b) the BEHAVIOUR it forbids — an impl declining to honour the input it was
#       handed. This IS expressible, by shadowing the argument with a cleared
#       copy, and is landed as `frame-shadow-input` (rival build exit 0,
#       frozen-solution build exit 1 where `decide` proves the negation false, so
#       the discrimination is semantic and not a stuck reduction).
# AUDIT REPAIR (second, independent audit — witness closers). The three row-mode
# rivals (`partial-prepatch-no-switch`, `partial-uncond-switch`,
# `partial-off-by-one`) previously closed their witnesses with a bare
# `simp [Id.run]`. Those cases PASSED the gate, and the pass was HOLLOW: the
# closer discharges the goal against each rival, but against the FROZEN solution
# it left an unreduced `pure { ... }` and failed with `unsolved goals`, i.e. for a
# REDUCTION reason. Re-derived with the forgery experiment — build a second file
# differing ONLY in what it claims, by dropping the `¬` so it asserts the spec
# HOLDS at the same input:
#
#   closer                     gold(¬spec)  gold(spec)  rival(spec)
#   simp [Id.run]              1            1  <-- SAME  1
#   simp only [Id.run]; decide 1            0           1
#
# With the old closer gold failed identically whether the witness claimed the spec
# was violated there or satisfied there, so its exit code carried NO information
# about the claim and the gate would have recorded `rejected` for a witness
# asserting the frozen solution is CORRECT at that point. `decide` runs the
# `DecidableEq` instances derived for `RowMode`/`StoredQuery` through the kernel,
# which DOES evaluate the `Id.run` do-block: gold then reports `decide proved the
# proposition ¬(...) is false` — a refutation of the concrete claim — and the
# flipped claim elaborates on gold (exit 0) while failing on the rival (exit 1).
# All three witnesses now use that closer, matching the three C1 cases, which were
# already `decide`-closed and already passed the forgery test unchanged. The
# rivals, the spec, the statements and every case's expected outcome are
# unchanged; only the three closers moved.
#
# `frame-shadow-input` is rejected by C1+C3, the same clauses that reject the
# partial-domain rivals — it is an additional input-handling attack, NOT a
# port of the permission check. An earlier revision of this docstring recorded
# the class as "APPLIES", which overclaimed (b) into a defence of (a). The same audit
# added `cond-store-nonempty-only` after finding C1 was pinned only on the
# field-projecting branch: `drop-store` installs a non-empty projection, so a
# rival that stores correctly there and skips the store on the empty branch was
# unreached. Both were confirmed rejected by real builds before being recorded
# here.
#
# RE-EXPRESSED (admiss-value-bearing): the sibling self-calls attach_description
#   on an F2P-shaped input to prove the PRECONDITION (Acc(...) permissions) is
#   establishable. This carrier has no precondition binder (every input is
#   admissible), so the honest analogue discharges the POSTCONDITION at the same
#   F2P-shaped install (fresh model-instance result set fed a single-field query,
#   the values('name') case) as a `have`, proving the modeled behavior is
#   satisfiable at a normal input, then closes the frozen obligation verbatim.
#
# RE-EXPRESSED (frame-mutate-count -> frame-shadow-input): the sibling's
#   MANDATORY frame-mutation rival writes value.value_field_count = 0 through a
#   read-only (Acc(...,1/2)) reference and must fail for INSUFFICIENT PERMISSION.
#   That exact write is unavailable here (`value` is an immutable structure value
#   and there is no fractional permission), but the class is NOT vacuous: what it
#   forbids is an impl refusing to honour the input it was handed, and on this
#   carrier that is written by shadowing the argument with a cleared copy
#   (`let value := { value with selectedFields := [] }`) and running the gold
#   body against the copy. The rival then stores a blanked query and never
#   switches the row-builder, so C1 and C3 both fail; it is rejected with a
#   witness at value=["name"] that fails semantically on the frozen solution.
# VACUOUS (divergence/non-termination): implementation_installQuery is a total
#   Lean def; a diverging impl cannot be written, so this class (a KNOWN HOLE on
#   velvet under partial semantics) is genuinely vacuous on lean.
#
# POINT SPREAD. The six reject witnesses probe six DISTINCT input tuples:
#   (prior rowMode, prior storedQuery, value.selectedFields) =
#     (fieldValuesTuple, [],      ["a","b"])  partial-prepatch-no-switch  C3
#     (modelInstances,   [],      [])         partial-uncond-switch       C4
#     (modelInstances,   [],      ["name"])   partial-off-by-one          C3
#     (modelInstances,   ["old"], ["name"])   drop-store                  C1 (non-empty)
#     (modelInstances,   ["old"], [])         cond-store-nonempty-only    C1 (empty)
#     (modelInstances,   [],      ["name"])   frame-shadow-input          C1+C3
#   Across them value.selectedFields ∈ {[], ["name"], ["a","b"]} (empty,
#   singleton, two-field), prior rowMode ∈ {modelInstances, fieldValuesTuple},
#   and prior storedQuery ∈ {[], ["old"]}, so no input sub-field is pinned: the
#   C4 rival is the only one holding the prior rowMode at a value the fix must
#   preserve, the C3 rivals vary the projection width across the length==1
#   boundary, and C1 is now pinned on BOTH branches of the guard — at a
#   non-trivial prior storedQuery with a field-projecting install (drop-store)
#   and with an empty install (cond-store-nonempty-only), the two points that
#   together forbid a store conditioned on the discriminator.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the row-builder strategies are RowMode constructors, sentinels selected
# but never invoked), so there is nothing to probe and the gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []

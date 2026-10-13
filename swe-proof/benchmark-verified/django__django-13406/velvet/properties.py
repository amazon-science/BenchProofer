"""properties.py — G-PBT falsification battery for django__django-13406 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a container carrier). Re-seating a
supplied query carrier into a container and reconciling the container's row
shaper with it:

  assignQuery (mut storedQuery : Query) (mut shaper : Shaper) (incoming : Query)
      return (unit : Unit)
    ensures storedQuery = incoming                      -- (C1) identity install
    ensures shaper = shaperAfter incoming shaperOld     -- (C2) reconcile/preserve

where ``shaperAfter incoming prior = if projectsColumns incoming then
Shaper.namedValues else prior`` and ``projectsColumns q = !q.projection.isEmpty``.
Two independent behaviours are pinned, exactly the fix + its complement:

  * (C2, projecting arm) a carrier that requests a non-empty explicit column
    projection forces the row shaper to the named-values shaper regardless of the
    prior shaper — THIS is the fix;
  * (C2, empty arm) a carrier that projects no columns leaves the prior shaper
    exactly as it was (``shaperOld``) — the preserve-on-empty complement;
  * (C1) the supplied carrier is always installed as the container's carrier
    (identity install), unconditionally.

The carrier is FULLY TRANSPARENT: ``Query`` is a ``structure`` with one
``List String`` field and ``Shaper`` a 5-constructor ``inductive``, both
``DecidableEq``; ``shaperAfter``/``projectsColumns`` are transparent ``def``s;
the ``axioms`` region declares no ``axiom`` and there is NO opaque answer key to
echo (directive 8: both clauses ground the post-state in the method inputs
``incoming`` / ``shaperOld``). So the whole reject lane is expressible by
``decide`` at concrete literal inputs.

BINDER STRUCTURE (read before judging binder coverage). The postcondition's
input binders are:

  * ``incoming`` — appears in BOTH clauses; C1 pins the installed carrier to it,
    C2 consults ``projectsColumns incoming`` (i.e. only whether its projection
    list is empty) to choose the arm. The load-bearing discriminator.
  * ``shaperOld`` (the prior shaper) — appears in C2's empty arm: it is the value
    the shaper must be preserved AT when the carrier projects no columns.
  * ``storedQueryOld`` (the prior carrier) — does NOT appear in either clause; C1
    demands the post-state carrier be ``incoming`` regardless of the prior. It is
    varied by the drop-store witness only to make the C1 miss observable (the
    rival that omits the install leaves the prior carrier in place, so the prior
    must DIFFER from ``incoming`` for the violation to fire).

The reject witnesses below move all three (see the accounting block): the
projecting/empty arms of C2 are both attacked, the identity install C1 is
attacked, and ``shaperOld`` ranges over three distinct prior shapers so the
preserve arm is not pinned at one value.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION (nagini's MANDATORY ``frame-mutate-count``) —
    VACUOUS here. The nagini sibling holds the count input at a fractional heap
    permission (``Acc(value.value_field_count, 1/2)``) an impl can illegally
    overwrite, and ships a rival that WRITES to it. Lean/Velvet are referentially
    transparent: ``incoming`` is an immutable value declared NOT ``mut``, there is
    no heap, no aliasing and no fractional-permission system — a rival cannot
    even name a mutation of ``incoming`` in scope. So there is no read-only field
    to overwrite and no substitute probe to build. Not fabricated (per the
    porting map: this class is vacuous here). The read-only frame that nagini's
    permission enforced is instead pinned by directive 5: ``incoming`` is not
    ``mut``, so C1/C2 quantify over the genuine input and no impl can satisfy them
    by mutating it.

  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

  * UNGROUNDED-ORACLE ECHO — N/A. Both clauses are total relations of the input
    binders (``incoming`` / ``shaperOld`` via ``shaperAfter`` / equality); the
    ``axioms`` region is empty, so there is no opaque answer key to echo.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the postcondition through Velvet's own tester machinery:
``extract_program_for`` -> ``assignQueryExec``, then
``prove_precondition_decidable_for`` / ``prove_postcondition_decidable_for`` /
``derive_tester_for`` synthesize the ``Decidable`` instances and the boolean
tester ``assignQueryTester storedQuery shaper incoming`` (the three args are the
method's inputs — the two ``mut`` fields at their ENTRY values and the read-only
carrier). ``assignQueryTester s0 sh0 inc = false`` says the extracted program's
(storedQuery, shaper) post-state violates C1 ∧ C2 at that concrete input. It is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict; there are no ``require`` clauses, so every input
reaches the postcondition (nothing is vacuously excluded); every equality is
over decidable carriers, so no assumption (axiom/sorry/native_decide) is needed
and the ``example`` head binds nothing (the consistency probe is trivially
satisfied). Each reject witness below was run against BOTH the rival (elaborates,
exit 0) and the frozen solution (``decide`` proves the tester is ``true``, so the
``= false`` claim fails to build, exit 1) with two real builds — the required
discrimination.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the operation is
modeled deeply, no callee's contract is consumed). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13406"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The three executable lines lie ENTIRELY inside the
# ---- single `-- impl-start` / `-- impl-end` block and occur exactly once in
# ---- Solution.lean (both facts asserted at load by _swap), so a _swap on them
# ---- touches only the elided impl region and `same_spec` holds. ----
_IMPL = (
    "    shaper := if projectsColumns incoming then Shaper.namedValues else shaper\n"
    "    storedQuery := incoming\n"
    "    return ()"
)

# ---- the frozen proof body (everything under the `prove_correct` header). The
# ---- reject rivals keep it verbatim (their rejection is carried by the witness,
# ---- not by whether the frozen script happens to break on the reshape); the
# ---- explicit-else positive retunes it, since that reshape leaves an extra goal
# ---- `loom_solve` does not close alone. ----
_PROOF = (
    "prove_correct assignQuery by\n"
    "  loom_solve\n"
    "  simp_all [shaperAfter]"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery. `assignQueryTester s0 sh0 inc = false` says the extracted
# ---- program's (storedQuery, shaper) post-state violates C1 ∧ C2 at that input.
# ---- Query / Shaper are DecidableEq, so `decide` settles it with no assumption.
_TESTER = (
    "extract_program_for assignQuery\n"
    "prove_precondition_decidable_for assignQuery\n"
    "prove_postcondition_decidable_for assignQuery\n"
    "derive_tester_for assignQuery\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # `ensures storedQuery = incoming` / `ensures shaper = shaperAfter incoming
    # shaperOld` obligation and only reshapes the executable surface. Both were
    # verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-reorder-install-first",
        "kind": "soundness",
        "expect": "verify",
        # Reorder: install the carrier FIRST, then apply the shaper
        # reconciliation. The install writes `storedQuery`, which the
        # reconciliation neither reads nor writes, so the reorder is
        # behaviourally identical; C1 and C2 both still hold. The frozen proof
        # (`loom_solve; simp_all [shaperAfter]`) closes the byte-identical
        # obligation with no retune.
        "module": _with_impl(
            "    storedQuery := incoming\n"
            "    shaper := if projectsColumns incoming then Shaper.namedValues else shaper\n"
            "    return ()"),
        "rationale": "structurally-different CORRECT reshape: install the supplied "
                     "carrier first, then reconcile the row shaper. The install "
                     "writes `storedQuery`, which the reconciliation neither reads "
                     "nor writes, so the two statements commute and (storedQuery, "
                     "shaper) is identical to the frozen impl — C1 (storedQuery = "
                     "incoming) and C2 (shaper = shaperAfter incoming shaperOld) "
                     "both hold. If this failed to verify the spec would be "
                     "over-fit to the frozen statement order => SPEC-TOO-STRONG. "
                     "Also the honest no-ungrounded-echo control: the discriminator "
                     "is `projectsColumns incoming`, so doing the conditional "
                     "reconciliation IS the work, not an echo of any oracle. "
                     "(Sibling: pos-control-reorder.)",
    },
    {
        "id": "pos-explicit-else",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: an explicit two-armed if/else whose
        # empty arm re-asserts preservation by writing the shaper back to its own
        # current value (a value-preserving self-assignment). Behaviourally
        # identical (the else writes the same shaper), so C2's projecting arm
        # (namedValues) and empty arm (shaperOld preserved) both hold. A
        # branch-reshape; the frozen script leaves the empty-arm goal, closed by a
        # one-token retune (`loom_solve <;> simp_all [shaperAfter]`).
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "    storedQuery := incoming\n"
                "    if projectsColumns incoming then\n"
                "      shaper := Shaper.namedValues\n"
                "    else\n"
                "      shaper := shaper\n"
                "    return ()"),
            _PROOF,
            "prove_correct assignQuery by\n"
            "  loom_solve <;> simp_all [shaperAfter]"),
        "rationale": "structurally-different CORRECT reshape: an explicit two-armed "
                     "if/else whose empty-selection arm re-writes the shaper to its "
                     "own current value (value-preserving self-assignment). "
                     "Behaviourally identical to the frozen implicit-preserve, so "
                     "C2's projecting arm (shaper = namedValues) and empty arm "
                     "(shaper = shaperOld) both hold, and C1 is untouched. A "
                     "branch-reshape, not a new induction; the frozen `loom_solve` "
                     "leaves the empty-arm preservation goal, closed by "
                     "`simp_all [shaperAfter]` on both goals. If it failed => the "
                     "spec is over-fit to the implicit-preserve shape => "
                     "SPEC-TOO-STRONG. (Sibling: pos-control-explicit-else.)",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The pre-conditions region is
    # empty, so there is no `require` to admit — but the analogue on a TOTAL
    # carrier is the obligation being UNSATISFIABLE / DEGENERATE at exactly an
    # F2P-shaped input, which a positive that discharges the obligation at that
    # concrete input tests directly. The in-region `assert` is discharged by
    # evaluation (`decide`) BEFORE the frozen obligation is closed verbatim, so
    # if the post-image collapsed at the F2P corner — both arms demanding the
    # same shaper, i.e. a reconciliation rule that distinguishes nothing — this
    # case would FAIL while the frozen impl still verified.
    # =====================================================================
    {
        "id": "admiss-reconcile-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "    assert (with_name_prefix `admiss\n"
                "      (shaperAfter { projection := [\"name\"] } Shaper.entity = Shaper.namedValues\n"
                "        ∧ shaperAfter { projection := [] } Shaper.entity = Shaper.entity))\n"
                + _IMPL),
            _PROOF,
            "prove_correct assignQuery by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [shaperAfter]"),
        "rationale": "the post-image is SATISFIABLE and NON-DEGENERATE at the "
                     "F2P-shaped corner: at a single-column projecting carrier "
                     "({ projection := [\"name\"] }) with a prior full-object "
                     "shaper, C2 demands namedValues; at the empty carrier with "
                     "the SAME prior shaper it demands that prior shaper back. "
                     "Both are discharged by evaluation in an in-region assert, "
                     "and the two demanded values are DISTINCT — so the "
                     "reconciliation rule genuinely separates the two arms at the "
                     "input the failing scenario exercises, rather than being a "
                     "clause every impl meets. The frozen impl follows verbatim, "
                     "so the ensures obligation discharges too. If the assert "
                     "could not discharge => the obligation is unsatisfiable / "
                     "degenerate at an F2P-shaped input => PRECOND-TOO-STRONG. "
                     "(Sibling: admiss-value-bearing, whose `require`-admission "
                     "reading has no analogue here — there is no `require` — but "
                     "whose non-degeneracy-at-the-F2P-corner reading does.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "prepatch-no-switch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch defect: install the carrier but NEVER reconcile the row
        # shaper. Correct on every empty-projection input (C2's empty arm holds)
        # but on every projecting input the shaper is left at its prior value
        # instead of the named-values shaper. Diverges only on the projecting
        # sub-domain.
        "module": _with_impl(
            "    storedQuery := incoming\n"
            "    return ()"),
        "refinement": "this is the EXACT pre-patch behaviour: the container's carrier "
                      "is installed but its row shaper is left at the freshly-"
                      "constructed default (a full-object shaper). Its faithful real "
                      "counterpart is the pre-patch code, which FAILS the F2P tests "
                      "(a reloaded column-projecting carrier then yields "
                      "full-object rows instead of the expected plain-named-value "
                      "rows, and the reloaded fetch crashes / returns the wrong "
                      "shape). So it would NOT resolve.",
        "rationale": "REJECT from C2 (shaper = shaperAfter incoming shaperOld): on "
                     "every projecting input the rival leaves the shaper at "
                     "shaperOld where the projecting arm demands namedValues. "
                     "C1 still holds (the carrier is installed), so the rejection "
                     "is attributable solely to the reconciliation clause. Refuted "
                     "at shaperOld = entity, incoming = { projection := [\"a\", "
                     "\"b\"] } (a two-column projecting carrier), where the frozen "
                     "post demands namedValues but the rival leaves entity. If it "
                     "verified => SPEC-TOO-WEAK (admits the pre-patch no-switch bug). "
                     "(Sibling: partial-prepatch-no-switch.)",
        "witness": _witness(
            "assignQueryTester default Shaper.entity { projection := [\"a\", \"b\"] }"),
    },
    {
        "id": "uncond-switch",
        "kind": "uniqueness",
        "expect": "reject",
        # Reconcile UNCONDITIONALLY (drop the guard): always set the named-values
        # shaper. Correct on every projecting input (C2's projecting arm holds)
        # but on an empty-projection input it overwrites the prior shaper instead
        # of preserving it. Diverges only on the empty sub-domain (when the prior
        # shaper is not already the named-values shaper).
        "module": _with_impl(
            "    shaper := Shaper.namedValues\n"
            "    storedQuery := incoming\n"
            "    return ()"),
        "refinement": "this corresponds to dropping the projection guard so the row "
                      "shaper is forced to the named-values shaper for EVERY "
                      "installed carrier, including plain non-projecting ones. Its "
                      "faithful real counterpart would make a reloaded plain "
                      "(full-object) carrier yield plain-named-value rows instead "
                      "of full domain objects, breaking the PASS_TO_PASS "
                      "full-object pickle tests (which expect a reloaded plain "
                      "query to still produce domain objects). So it would NOT "
                      "resolve.",
        "rationale": "REJECT from C2's EMPTY arm (projectsColumns incoming = false "
                     "=> shaper = shaperOld): on an empty-projection input the "
                     "unconditional write forces namedValues where the empty arm "
                     "demands the prior shaper. Refuted at shaperOld = "
                     "namedValuesTuple, incoming = { projection := [] } (empty "
                     "projection, a prior shaper other than namedValues), where the "
                     "frozen post demands namedValuesTuple preserved but the rival "
                     "writes namedValues. If it verified => SPEC-TOO-WEAK (admits "
                     "the guard-dropped bug). (Sibling: partial-uncond-switch.)",
        "witness": _witness(
            "assignQueryTester default Shaper.namedValuesTuple { projection := [] }"),
    },
    {
        "id": "off-by-one-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one guard: reconcile only when the projection has MORE THAN ONE
        # column, so a carrier projecting EXACTLY ONE column is wrongly left at
        # the prior shaper. Correct on empty (preserved) and >=2 columns
        # (switched), diverges only on the single-column sub-domain — the common
        # single-projected-column case of the F2P scenario.
        "module": _with_impl(
            "    shaper := if incoming.projection.length > 1 then Shaper.namedValues else shaper\n"
            "    storedQuery := incoming\n"
            "    return ()"),
        "refinement": "this corresponds to a guard `len(projection) > 1` instead of "
                      "the truthiness test `projection is non-empty`. A "
                      "single-column projecting carrier (the common case the F2P "
                      "tests exercise, whose projection has exactly one entry) "
                      "would be left at the full-object shaper, so the reloaded "
                      "query yields a full domain object instead of the expected "
                      "single-key plain-named-value row. So it would FAIL the F2P "
                      "and NOT resolve.",
        "rationale": "REJECT from C2's projecting arm at the singleton point "
                     "(projectsColumns incoming = true, but length = 1): the guard "
                     "`length > 1` is false, so the rival leaves shaperOld where "
                     "the projecting arm demands namedValues. Refuted at shaperOld "
                     "= entity, incoming = { projection := [\"name\"] } (exactly "
                     "one projected column). A near-miss the prepatch-no-switch "
                     "rival (wrong on ALL projecting inputs) subsumes only at "
                     ">=2 columns, so this rival is refuted at its own "
                     "distinguishing singleton point. If it verified => "
                     "SPEC-TOO-WEAK (drops the single-column case). (Sibling: "
                     "partial-off-by-one.)",
        "witness": _witness(
            "assignQueryTester default Shaper.entity { projection := [\"name\"] }"),
    },
    {
        "id": "reconcile-only-from-entity",
        "kind": "uniqueness",
        "expect": "reject",
        # PRIOR-SHAPER near-miss (added by audit): reconcile only when the prior
        # shaper is the full-object one, so a projecting carrier arriving at a
        # container that already carries some OTHER configured shaper is wrongly
        # left alone. Correct on every empty input (preserved) and on every
        # projecting input whose prior shaper is `entity`, so the three existing
        # projecting-arm rivals do not subsume it: it diverges only on the
        # sub-domain (projecting AND prior shaper not entity, not namedValues) —
        # the one place the `shaperOld` binder is load-bearing in C2's PROJECTING
        # arm rather than its preserve arm.
        "module": _with_impl(
            "    shaper := if projectsColumns incoming && shaper == Shaper.entity then\n"
            "        Shaper.namedValues\n"
            "      else shaper\n"
            "    storedQuery := incoming\n"
            "    return ()"),
        "refinement": "this corresponds to conditioning the shaper reconciliation on "
                      "the container ALSO still carrying its freshly-constructed "
                      "full-object shaper, instead of switching unconditionally "
                      "whenever the carrier projects columns. Its faithful real "
                      "counterpart would leave a container that had already been "
                      "configured with any other row shaper yielding the wrong row "
                      "shape for a column-projecting carrier, so the reloaded query "
                      "produces rows of the prior shape rather than plain named "
                      "values. So it would NOT resolve.",
        "rationale": "REJECT from C2's PROJECTING arm with a non-entity prior "
                     "shaper: the projecting arm demands namedValues regardless of "
                     "shaperOld, but the extra `shaper == Shaper.entity` conjunct "
                     "makes the rival preserve the prior shaper there. Refuted at "
                     "shaperOld = namedValuesFlat, incoming = { projection := "
                     "[\"a\"] }. Distinct from prepatch-no-switch / "
                     "off-by-one-guard, which are already wrong at shaperOld = "
                     "entity and so never exercise the prior-shaper dependence of "
                     "the projecting arm; and distinct from uncond-switch, which "
                     "attacks the EMPTY arm. If it verified => SPEC-TOO-WEAK (the "
                     "projecting arm would only be pinned from the default prior "
                     "shaper).",
        "witness": _witness(
            "assignQueryTester default Shaper.namedValuesFlat { projection := [\"a\"] }"),
    },
    {
        "id": "drop-install",
        "kind": "uniqueness",
        "expect": "reject",
        # Identity-install miss — drop the install entirely: reconcile the shaper
        # correctly but never install the supplied carrier, so the container's
        # carrier is NOT the supplied value. Correct on the shaper (C2 holds) but
        # C1 (storedQuery = incoming) fails because storedQuery keeps its prior
        # (arbitrary) value.
        "module": _with_impl(
            "    shaper := if projectsColumns incoming then Shaper.namedValues else shaper\n"
            "    return ()"),
        "refinement": "this corresponds to dropping the carrier install from the "
                      "setter: the row shaper is reconciled but the supplied "
                      "carrier is never actually installed, so the container keeps "
                      "running its original carrier. A faithful real counterpart "
                      "that omitted the install would leave the reloaded container "
                      "running its original (empty) query, so a fetch would not "
                      "reflect the supplied projecting query at all and the F2P "
                      "tests would FAIL. So it would NOT resolve.",
        "rationale": "REJECT from C1 (storedQuery = incoming): the rival omits the "
                     "install, so storedQuery keeps its prior value storedQueryOld, "
                     "which differs from incoming whenever the two differ. C2 still "
                     "holds (the shaper is reconciled), so the rejection is "
                     "attributable solely to the identity-install clause. Refuted "
                     "at storedQueryOld = { projection := [\"x\"] }, shaperOld = "
                     "namedValues, incoming = { projection := [\"name\"] }, where "
                     "the frozen post demands storedQuery = incoming but the rival "
                     "leaves the prior carrier. This is the ONLY witness that moves "
                     "the prior-carrier binder off its default, which is what makes "
                     "the C1 miss observable. If it verified => SPEC-TOO-WEAK (the "
                     "identity-install guarantee is hollow). (Sibling: drop-store.)",
        "witness": _witness(
            "assignQueryTester { projection := [\"x\"] } Shaper.namedValues "
            "{ projection := [\"name\"] }"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 4 uniqueness rivals) plus a
# 2-case AXIOM lane. This battery carries 8: the 2 positives, the admissibility
# case and one uniqueness rival added by audit, and the 4 ported rivals. This bundle models the SAME single function (the query
# setter) but over a referentially-transparent carrier: `storedQuery : Query`
# and `shaper : Shaper` are `mut` fields, `incoming : Query` is read-only, and
# the count discriminator is folded into `projectsColumns incoming`
# (emptiness of the projection list). The accounting below records every sibling
# case.
#
#   sibling case (nagini)          -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder            -> pos-reorder-install-first    PORTED
#   pos-control-explicit-else      -> pos-explicit-else            PORTED
#   admiss-value-bearing           -> admiss-reconcile-nondegenerate PORTED (audit)
#   frame-mutate-count             -> (none)                       VACUOUS (no heap)
#   partial-prepatch-no-switch     -> prepatch-no-switch           PORTED
#   partial-uncond-switch          -> uncond-switch                PORTED
#   partial-off-by-one             -> off-by-one-guard             PORTED
#   drop-store                     -> drop-install                 PORTED
#   (none — new, audit)            -> reconcile-only-from-entity   ADDED (audit)
#   AXIOM_TESTS (2)                -> (none)                        DROPPED (G-AX)
#
# PORTED (positives): pos-control-reorder ports directly (install first, then
#   reconcile — behaviourally identical, frozen proof unchanged). pos-control-
#   explicit-else ports as an explicit two-armed if/else with a value-preserving
#   self-assignment on the empty arm (proof retuned by one token, verified to
#   build).
# PORTED (admissibility) — LANDED BY AUDIT; the original port dropped this lane
#   as "VACUOUS (no pre)" and that reason was wrong. It is true that this bundle
#   declares no `require` clause, so the sibling's literal reading (can the
#   precondition be established for an F2P-shaped input?) has no analogue. But the
#   ANALOGUE ON A TOTAL CARRIER is not vacuous: the obligation can still be
#   UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input, and that is what
#   PRECOND-TOO-STRONG detects here. The original note claimed the two positives
#   already discharge it; they do not — a positive closes the obligation
#   UNIVERSALLY by tactic, which says nothing about whether the reconciliation
#   rule separates its two arms AT a concrete F2P point (a degenerate rule that
#   demanded the same shaper on both arms would let both positives verify
#   unchanged). admiss-reconcile-nondegenerate discharges that separation by
#   EVALUATION in an in-region assert, at the single-column projecting carrier the
#   failing scenario exercises, before closing the frozen obligation verbatim.
#   Verified with a real build (exit 0).
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because the count
#   input is held at Acc(value.value_field_count, 1/2) an impl can illegally
#   write. This backend is referentially transparent: `incoming` is declared NOT
#   `mut`, there is no heap / aliasing / fractional-permission system, and a rival
#   cannot even name a mutation of `incoming` in scope. So there is no read-only
#   field to overwrite and no substitute probe (porting map: vacuous here). The
#   read-only frame nagini's 1/2 permission enforced is instead pinned by
#   directive 5 — `incoming` is not `mut`, so C1/C2 quantify over the genuine
#   input and no impl can vacuously satisfy C2 by zeroing the projection.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# PORTED (uniqueness rivals): prepatch-no-switch (the exact pre-patch bug: install
#   but never reconcile, wrong on the projecting sub-domain, REJECT from C2's
#   projecting arm); uncond-switch (drop the guard, wrong on the empty sub-domain,
#   REJECT from C2's empty/preserve arm); off-by-one-guard (guard on length > 1,
#   wrong on the single-column sub-domain, REJECT from C2's projecting arm at the
#   singleton point — a near-miss the prepatch rival subsumes only at >= 2
#   columns, so refuted at its own singleton point); drop-install (omit the
#   carrier install, REJECT from C1 the identity-install clause). Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   the frozen solution (two real builds per case).
#
#   The five reject witnesses probe five DISTINCT input tuples. Across them:
#   incoming.projection takes {["a","b"], [], ["name"], ["a"], ["name"]} — the
#   empty arm, the single-column projecting arm, and a two-column projecting arm
#   are all exercised; shaperOld takes {entity, namedValuesTuple, entity,
#   namedValuesFlat, namedValues} — four distinct prior shapers, so neither arm is
#   pinned at one prior value; storedQueryOld takes {default, default, default,
#   default, {["x"]}} — moved off its default by drop-install, the one rival whose
#   C1 miss depends on it. Both independent clauses are attacked: C1 by
#   drop-install, C2's projecting arm by prepatch-no-switch and off-by-one-guard
#   (both at prior shaper = entity) and by reconcile-only-from-entity (at a
#   NON-entity prior shaper, which is what makes the projecting arm's independence
#   from shaperOld load-bearing), C2's empty/preserve arm by uncond-switch. pts=5.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   axiom (the operation is modeled deeply; the `axioms` region is empty and no
#   callee's contract is consumed), so there is nothing to probe and the gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []

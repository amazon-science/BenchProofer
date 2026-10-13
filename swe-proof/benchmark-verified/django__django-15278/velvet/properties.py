"""properties.py — G-PBT falsification battery for django__django-15278 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region is changed — a region the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct requiresTableRebuild``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes iff
(in scope AND verifies). ``expect:"reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over three Bool observations). A schema
operation must choose how a new column can be materialized — appended in place
with a lightweight column-addition primitive, or introduced only by rebuilding
the whole table:

  requiresTableRebuild (isUnique : Bool) (acceptsNull : Bool)
                       (hasServerDefault : Bool) return (out : Bool)
    ensures out = (isUnique || !acceptsNull || hasServerDefault)      -- (Q)

ONE top-level postcondition clause, (Q), pinning the decision in BOTH directions
to a three-way disjunction over the method's own arguments. THREE input binders,
each an independent free ``Bool``: there is no ``require`` clause (the domain is
the full 2^3 cube) and the ``axioms``/``pure`` regions are EMPTY.

CARRIER NOTE — the surface is FULLY TRANSPARENT. Unlike the opaque-callee
bundles, (Q)'s right-hand side is a closed boolean expression in the three
arguments: nothing is deferred to an ``opaque`` term, so every point of the cube
COMPUTES and every witness below is a plain ``decide`` at concrete literals. No
conditioning on the carrier is needed anywhere in this battery, and no witness
carries a hypothesis binder (so the gate's consistency probe has nothing to
check — there are no assumptions that could be jointly unsatisfiable).

Because (Q) is an equality (not an implication), it pins the decision in both
directions at once: a rival that answers ``true`` where the disjunction is false
is refutable exactly as readily as one that answers ``false`` where it is true.
That is what makes the whole 8-point cube available as witness material, and the
reject lane below spends 7 distinct points of it.

BINDER STRUCTURE — why all three must be varied. (Q) is a DISJUNCTION, so each
binder is load-bearing on exactly the sub-cube where the other two disjuncts are
absent:

  * ``isUnique`` is observable only at (acceptsNull = true, hasServerDefault =
    false) — elsewhere another disjunct already forces ``true``. That single
    point (T,T,F) is the F2P shape.
  * ``acceptsNull`` is observable only at (isUnique = false, hasServerDefault =
    false), i.e. at (F,F,F) vs (F,T,F).
  * ``hasServerDefault`` is observable only at (isUnique = false, acceptsNull =
    true), i.e. at (F,T,T) vs (F,T,F).

A battery that held any one of them fixed would admit a rival that dropped
exactly that disjunct and never notice. So the three near-miss rivals below are
built one per disjunct, each refuted at its own observability point, and the
witnesses drive all three binders to BOTH values across 6 distinct input points.

REFINEMENT GROUND-TRUTH (what makes a reject a TRUE
verify-does-not-imply-resolve break rather than a resolve-preserving artifact).
The engine underneath cannot append a column in place when the column carries a
uniqueness obligation ("Cannot add a UNIQUE column") or when it disallows an
absent value with no value to backfill ("Cannot add a NOT NULL column with
default value NULL"); and it cannot later retract a server-side default it
attached, because the retraction statement does not exist in its dialect. So the
rebuild route is not a preference on any of the three sub-domains — it is the
only route that works, and a rival that routes any of them to the in-place
primitive raises at the engine. Conversely the harness pins the OTHER direction
too: the failing-then-passing test for a value-optional uniquely-valued column
requires the column to appear (rebuild), while a passing test for a plain
value-optional column with no default and no uniqueness obligation asserts that
NO table rebuild happens (it captures the emitted statements and asserts no
table creation and no table drop). Every rival below therefore has a faithful
real counterpart that breaks a named test in one direction or the other; each
case's ``refinement`` says which.

ADVERSARIAL READ of the sibling (nagini) classes on this carrier:

  * SOUNDNESS / positive controls — APPLY, and are the cheapest honest evidence
    the spec is not over-fitted to the frozen impl's SHAPE. Three reshapes ship:
    operand permutation, a branch-and-return-literals form testing the NEGATED
    (in-place-suffices) condition first, and a two-step ``let`` staging that
    RE-ASSOCIATES the disjunction. None of the three is definitionally the
    frozen return — each was checked directly with a real build, and ``rfl``
    FAILS on all three equations (``d || !n || u`` vs ``u || !n || d``, the
    ``if``-form vs the disjunction, and the re-associated staging vs the frozen
    parse), so each genuinely obliges ``loom_solve`` to reason about (Q) rather
    than to close a zeta/eta-reduction. The frozen ``loom_solve`` nevertheless
    closes the byte-identical obligation for all three (each confirmed with a
    real build, EXIT 0).

    (Audit note, measured: ``u || !n || d`` parses as ``(u || !n) || d`` — a
    LEFT-associated staging that names ``u || !n`` first is therefore the frozen
    parse tree with a sub-term named, definitionally equal by ``rfl`` and worth
    nothing as a reshape. The staging positive below is right-associated for
    exactly this reason.)

  * ADMISSIBILITY — the sibling's probe rests on its fractional-permission
    precondition admitting a normally-shaped column. There is no ``require``
    clause here, so nothing could exclude an in-domain input and that probe is
    degenerate. The residual risk on a total domain is a DEGENERATE post-image —
    a clause no impl can distinguish reads exactly like one every impl meets —
    so the case is re-aimed at non-degeneracy: an in-region ``assert`` pinning
    four points of the cube at which (Q)'s right-hand side takes genuinely
    different values (three ``true`` for three DIFFERENT reasons, one ``false``),
    with the frozen body kept verbatim so the method's own obligation still
    discharges.

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    this class as MANDATORY: its sharpest rival WRITES back into a column flag
    held at a fractional read-only permission, and must be rejected for
    insufficient permission. This backend is referentially transparent — no heap,
    no aliasing, no fractional permission, no ``Old`` — and this bundle declares
    NO ``mut`` binder: all three observations enter as immutable ``Bool`` values.
    There is no read-only field to overwrite and no substitute probe to build.
    NOT ported and NOT replaced by a fabricated stand-in (porting map: this class
    is vacuous on a referentially-transparent backend).

  * DIVERGENCE / non-termination - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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

  * UNGROUNDED-ORACLE ECHO — N/A. (Q)'s right-hand side is a fully unfolded
    boolean expression in the method's own three arguments; the ``axioms`` region
    declares nothing and the ``pure`` region declares no helper. There is no
    answer-key term for an impl to echo, so the only way to satisfy (Q) is to
    compute the decision — which is what the positives exercise.

  * PARTIAL-DOMAIN / VALUE / CONTROL-FLOW-EFFECT — these carry the reject lane.
    The sibling's route-label swap is observable here because (Q) pins the
    returned decision itself, and its per-disjunct partial-domain rivals port one
    for one onto this carrier's three disjuncts.

AXIOM lane: the sibling's ``AXIOM_TESTS`` are DROPPED. The axiom lane is G-AX's
job and this gate ignores ``AXIOM_TESTS`` regardless; here there is additionally
no ``axiom`` at all, because the presence of a server-side default enters as a
free boolean input with nothing asserted about how it is produced (mapping.md §3
records the G-AX skip). See the footer for the full case-by-case accounting.
"""
from pathlib import Path

INSTANCE = "django__django-15278"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen return, verbatim (the single code line
# ---- strictly inside requiresTableRebuild's -- impl-start / -- impl-end). It
# ---- lies wholly inside the elided impl region and is unique in Solution.lean
# ---- (both facts asserted at load, by _swap and by the assert below), so every
# ---- variant's edit is confined to the impl region and never touches the spec
# ---- (the method signature, the `ensures`, and the axioms/pure/pre/post
# ---- regions). The frozen `prove_correct requiresTableRebuild by loom_solve`
# ---- is kept as-is by every case.
_IMPL = "    return (isUnique || !acceptsNull || hasServerDefault)"
assert _BASE.count(_IMPL) == 1, "impl-region anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique). The admissibility case inserts an
# ---- in-region `assert` immediately after it and keeps the whole frozen body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"


def _impl(new_body):
    """Full Solution.lean with ONLY requiresTableRebuild's impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `requiresTableRebuildTester u a d = false` says the extracted program's
# ---- result VIOLATES the method's postcondition at that concrete input. It is
# ---- checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. All three arguments are concrete Bool
# ---- literals and (Q) is closed over them, so `decide` reduces the extracted
# ---- program without getting stuck and without any hypothesis binder — there
# ---- are no assumptions here that could be jointly unsatisfiable.
def _witness(is_unique, accepts_null, has_server_default):
    def b(x):
        return "true" if x else "false"
    args = f"{b(is_unique)} {b(accepts_null)} {b(has_server_default)}"
    return (
        "extract_program_for requiresTableRebuild\n"
        "prove_precondition_decidable_for requiresTableRebuild\n"
        "prove_postcondition_decidable_for requiresTableRebuild\n"
        "derive_tester_for requiresTableRebuild\n\n"
        f"example : requiresTableRebuildTester {args} = false := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl of a different SHAPE cannot
    # verify, the spec is SPEC-TOO-STRONG. Each keeps the frozen
    # `prove_correct requiresTableRebuild by loom_solve` script. None of the
    # three is definitionally the frozen return (`rfl` fails on each of the
    # three equations, measured), so each genuinely tests that `loom_solve`
    # reasons about (Q) rather than closing a reduction; all three nevertheless
    # verify (real builds, EXIT 0).
    # =====================================================================
    {
        "id": "pos-disjunct-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The SAME three-way disjunction with the operands permuted (default
        # first, then value-absence, then uniqueness). `||` is commutative and
        # associative on total bools, so the guard equals the frozen one.
        "module": _impl("    return (hasServerDefault || !acceptsNull || isUnique)"),
        "rationale": (
            "structurally-different CORRECT impl: the same three-way disjunction "
            "with the operands permuted (server-side default first, then "
            "value-absence, then uniqueness). `||` is commutative on total "
            "bools, so this returns the frozen decision at every point of the "
            "cube — but it is NOT definitionally equal to it (measured: `rfl` "
            "fails on `(d || !n || u) = (u || !n || d)`), so `loom_solve` must "
            "actually reason about (Q) `out = (isUnique || !acceptsNull || "
            "hasServerDefault)` rather than close a reduction. It still "
            "discharges under the frozen `loom_solve`. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected for its operand "
            "order). (Nagini sibling: pos-disjunct-reorder.)"),
    },
    {
        "id": "pos-negated-inplace-first",
        "kind": "soundness",
        "expect": "verify",
        # Branch reshape: test the NEGATED condition (the in-place-suffices case
        # — a value-optional column with no default and no uniqueness
        # obligation) FIRST and return the literal `false` there, else `true`.
        # De Morgan of the frozen guard; a different control-flow shape with the
        # same 8-point truth table.
        "module": _impl(
            "    if (!isUnique && acceptsNull && !hasServerDefault) then\n"
            "      return false\n"
            "    else\n"
            "      return true"),
        "rationale": (
            "structurally-different CORRECT impl: test the NEGATED condition "
            "first — the in-place-suffices case, a value-optional column with no "
            "server-side default and no uniqueness obligation — returning the "
            "literal `false` there and `true` otherwise. De Morgan of the frozen "
            "guard, so the same 8-point truth table; it is NOT definitionally "
            "the frozen return (measured: `rfl` fails on `(if (!u && n && !d) "
            "then false else true) = (u || !n || d)`), so `loom_solve` must "
            "reason about (Q), and (Q) still discharges "
            "under the frozen `loom_solve`; this is the reshape that exercises "
            "the FALSE arm of (Q) as an explicit branch rather than as a "
            "fall-through. If it FAILS => SPEC-TOO-STRONG. (Nagini sibling: "
            "pos-negated-append-first.)"),
    },
    {
        "id": "pos-staged-locals",
        "kind": "soundness",
        "expect": "verify",
        # Two-step `let` staging that RE-ASSOCIATES: combine the two
        # value-shape observations (value-absence, server-side default) first,
        # then fold in the uniqueness observation. `u || !n || d` parses as
        # `(u || !n) || d`, so this right-associated staging is a genuinely
        # different term (measured: `rfl` fails), unlike a left-associated
        # staging which would merely name the frozen parse tree's own sub-term.
        # A third distinct shape (named intermediates rather than one
        # expression), and the closest analogue on this carrier of the sibling's
        # route-via-a-helper positive.
        "module": _impl(
            "    let forcedByValueShape : Bool := !acceptsNull || hasServerDefault\n"
            "    let forced : Bool := isUnique || forcedByValueShape\n"
            "    return forced"),
        "rationale": (
            "structurally-different CORRECT impl: stage the decision through two "
            "named intermediates — first combine the two value-shape "
            "observations (value-absence, server-side default), then fold in "
            "the uniqueness observation. This RE-ASSOCIATES the disjunction: "
            "`isUnique || !acceptsNull || hasServerDefault` parses as "
            "`(isUnique || !acceptsNull) || hasServerDefault`, so grouping the "
            "OTHER two operands first yields a term that is NOT definitionally "
            "the frozen return (measured: `rfl` fails on the re-associated "
            "equation, and would have SUCCEEDED on the left-associated staging "
            "— which is why the staging is oriented this way rather than the "
            "obvious way). (Q) still discharges under the frozen `loom_solve`. "
            "A third distinct shape (let-staging rather "
            "than a single expression), and the closest analogue on this carrier "
            "of the sibling's compute-the-decision-via-a-helper positive: the "
            "sibling's @Pure helper is not modeled here (the `pure` region is "
            "empty), so the decision is staged in locals instead. If it FAILS => "
            "SPEC-TOO-STRONG. (Nagini sibling: pos-call-helper.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed from the sibling's fractional-permission probe
    # (this backend has no `require` clause and no permission surface, so
    # "a normally-shaped column is in-domain" is degenerate) to POST-IMAGE
    # NON-DEGENERACY: (Q)'s right-hand side must actually take different values
    # at different points of the cube, and take `true` for each of its three
    # reasons SEPARATELY. The frozen body is kept verbatim so (Q) itself still
    # discharges. Confirmed with a real build (EXIT 0).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START +
            "    assert (with_name_prefix `admiss (\n"
            "      ((true || !true || false : Bool) = true) ∧\n"
            "      ((false || !false || false : Bool) = true) ∧\n"
            "      ((false || !true || true : Bool) = true) ∧\n"
            "      ((false || !true || false : Bool) = false)))\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate on the modeled "
            "cube: (Q)'s right-hand side is TRUE at each of its three reasons "
            "taken SEPARATELY — a value-optional defaultless column with a "
            "uniqueness obligation (the failing test's shape, `true || !true || "
            "false`), a column disallowing an absent value with no default and "
            "no uniqueness obligation (`false || !false || false`), and a "
            "value-optional column supplying a default (`false || !true || "
            "true`) — and FALSE at the one point where all three are absent "
            "(`false || !true || false`), which is the in-place-suffices shape a "
            "passing test asserts is NOT rebuilt. Four points, four genuinely "
            "distinct reasons, so the clause is not degenerate (a clause no impl "
            "could distinguish would read exactly like one every impl meets). "
            "The in-region assert must discharge and the frozen body is kept "
            "verbatim so (Q) still verifies; if it FAILS => the obligation is "
            "degenerate or the domain excludes a legitimately-shaped column. "
            "(Nagini sibling: admiss-reads, re-aimed — that probe asserted the "
            "three flags are READABLE under their half-permissions, which has no "
            "counterpart on a carrier with no permission surface and no "
            "`require` clause.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve. The seven rivals attack (Q) in BOTH
    # directions (three near-misses dropping one disjunct each; two constants;
    # one label swap; one overlap carve-out) at SEVEN DISTINCT input points,
    # driving all three binders to both values. Every witness confirmed with
    # real builds (all seven pairs rebuilt independently): it
    # ELABORATES against its rival (EXIT 0) and FAILS on the frozen solution
    # (EXIT 1, `decide` proving the tester equals `true` there — a SEMANTIC
    # refutation, checked to be neither a stuck reduction nor a missing name).
    # =====================================================================
    {
        "id": "weak-drop-unique",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image behaviour: drop the `isUnique` disjunct, deciding on
        # value-absence and the server-side default alone. Wrong on EXACTLY one
        # point of the cube — (T,T,F) — which is exactly the failing test's
        # shape. The sharpest near-miss in the battery.
        "module": _impl("    return (!acceptsNull || hasServerDefault)"),
        "refinement": (
            "this is the pre-image state verbatim (the decision considered only "
            "value-absence and the server-side default, ignoring whether the "
            "column carried a uniqueness obligation), so its faithful real "
            "counterpart is the UNCHANGED code — precisely what the failing test "
            "fails on. On a value-optional, defaultless column that nonetheless "
            "carries a uniqueness obligation it selects the in-place "
            "column-addition primitive, and the engine rejects an in-place "
            "addition of a uniquely-valued column outright ('Cannot add a UNIQUE "
            "column'), so the column never appears and the failing test's "
            "presence assertion stays RED. It does NOT resolve — a verifying "
            "rival here would be a genuine verify-does-not-imply-resolve break."),
        "rationale": (
            "REJECT from (Q) `out = (isUnique || !acceptsNull || "
            "hasServerDefault)`: at (isUnique, acceptsNull, hasServerDefault) = "
            "(true, true, false) the clause pins `out = true`, but with the "
            "`isUnique` disjunct dropped the rival returns `false || false = "
            "false`. That point is the SOLE observability point of the "
            "`isUnique` binder — everywhere else another disjunct already forces "
            "`true` — so it is the only input that can discriminate this rival, "
            "and it is the failing test's own shape. Refuted decidably (the "
            "carrier is fully transparent; no conditioning needed). If it "
            "VERIFIES => SPEC-TOO-WEAK (the uniqueness disjunct unpinned). "
            "(Nagini siblings: weak-prepatch / weak-drop-unique, which the "
            "carrier collapses into this single rival — see the footer.)"),
        "witness": _witness(True, True, False),
    },
    {
        "id": "weak-drop-value-absence",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: drop ONLY the value-absence disjunct, keeping
        # uniqueness and the default. Wrong on EXACTLY (F,F,F) — a column that
        # disallows an absent value, with no default and no uniqueness
        # obligation. This is the binder the other rivals cannot reach.
        "module": _impl("    return (isUnique || hasServerDefault)"),
        "refinement": (
            "dropping only the value-absence disjunct is what a real counterpart "
            "that kept the uniqueness and default conditions but lost the "
            "no-absent-value one would do. It routes a column that disallows an "
            "absent value — with no default to backfill and no uniqueness "
            "obligation — to the in-place primitive, and the engine refuses that "
            "outright ('Cannot add a NOT NULL column with default value NULL'), "
            "so the operation raises. A passing test that adds exactly such a "
            "column (a non-value-optional text column with a non-default "
            "collation and no default) would fail. It does NOT resolve."),
        "rationale": (
            "REJECT from (Q): at (isUnique, acceptsNull, hasServerDefault) = "
            "(false, false, false) the clause pins `out = (false || !false || "
            "false) = true`, but the rival returns `false || false = false`. "
            "(F,F,F) is the SOLE observability point of the `acceptsNull` binder "
            "on this rival's shape, and no other rival in the battery is "
            "witnessed with `acceptsNull = false` and `hasServerDefault = "
            "false` — this case is what varies that binder. PARTIAL-DOMAIN: "
            "correct on 7 of the 8 cube points. Refuted decidably. If it "
            "VERIFIES => SPEC-TOO-WEAK on the value-absence sub-domain. (Nagini "
            "sibling: none directly — the sibling's weak-drop-pk attacked the "
            "primary-key disjunct, which this carrier folds into `isUnique`; "
            "this rival attacks the disjunct that sibling case left uncovered. "
            "See the footer.)"),
        "witness": _witness(False, False, False),
    },
    {
        "id": "weak-drop-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: drop ONLY the server-side-default disjunct. Wrong on
        # EXACTLY (F,T,T) — a value-optional column with no uniqueness
        # obligation that DOES supply a default. The third disjunct, and the
        # third binder.
        "module": _impl("    return (isUnique || !acceptsNull)"),
        "refinement": (
            "dropping only the server-side-default disjunct is what a real "
            "counterpart that lost the original default condition while adding "
            "the uniqueness one would do. It appends a value-optional column "
            "that supplies a default in place, which attaches that default to "
            "the stored column definition; the engine's dialect has no statement "
            "for retracting a column default afterwards, so the default is left "
            "permanently in place. Passing tests that add exactly such a column "
            "and then assert the stored definition carries NO default (both the "
            "nullable-char-with-default and nullable-text-with-default cases) "
            "would fail. It does NOT resolve."),
        "rationale": (
            "REJECT from (Q): at (isUnique, acceptsNull, hasServerDefault) = "
            "(false, true, true) the clause pins `out = true`, but with the "
            "default disjunct dropped the rival returns `false || !true = "
            "false`. (F,T,T) is the SOLE observability point of the "
            "`hasServerDefault` binder, and this is the only reject case "
            "witnessed at `hasServerDefault = true` with the other two disjuncts "
            "absent — so it is what varies that binder against the near-miss "
            "rivals. PARTIAL-DOMAIN: correct on 7 of the 8 cube points. Refuted "
            "decidably. If it VERIFIES => SPEC-TOO-WEAK on the "
            "server-side-default sub-domain. (Nagini sibling: none directly — "
            "the sibling's three near-misses all attacked the two disjuncts its "
            "gold patch ADDED; this rival attacks the third, pre-existing "
            "disjunct the frozen clause here also pins. See the footer.)"),
        "witness": _witness(False, True, True),
    },
    {
        "id": "weak-always-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant `true`: always take the rebuild route. Correct on 7 of 8
        # points, wrong on the single in-place-suffices point (F,T,F) — the
        # opposite direction of (Q) from the near-misses above.
        "module": _impl("    return true"),
        "refinement": (
            "always demanding the rebuild route is what a real counterpart that "
            "deleted the decision and unconditionally rebuilt would do. It "
            "rebuilds the entire table even for a plain value-optional column "
            "with no default and no uniqueness obligation, which the in-place "
            "primitive handles. A passing test that adds exactly such a column "
            "captures the emitted statements and asserts that NO table creation "
            "and NO table drop occur — the signature of a rebuild — so it fails. "
            "It does NOT resolve: it breaks the in-place route the change "
            "deliberately preserves."),
        "rationale": (
            "REJECT from (Q) in the OTHER direction: at (isUnique, acceptsNull, "
            "hasServerDefault) = (false, true, false) all three disjuncts are "
            "absent, so the clause pins `out = false`, but the rival returns "
            "`true`. This is the one cube point the three near-miss rivals can "
            "never expose (they are all too WEAK, not too strong), so it is what "
            "demonstrates (Q) is an equality rather than a one-directional "
            "implication — the in-place route is pinned as tightly as the "
            "rebuild route. Refuted decidably. If it VERIFIES => SPEC-TOO-WEAK "
            "(the in-place route unpinned). (Nagini sibling: "
            "weak-always-rebuild.)"),
        "witness": _witness(False, True, False),
    },
    {
        "id": "weak-always-inplace",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant `false`: never rebuild. The dual constant; wrong on 7 of 8
        # points. Witnessed at (T,T,T) — the all-signals-present corner, which
        # no other case in the battery probes.
        "module": _impl("    return false"),
        "refinement": (
            "always taking the in-place route is what a real counterpart that "
            "deleted the decision and unconditionally used the lightweight "
            "column-addition primitive would do. It attempts an in-place "
            "addition for every column, including the uniquely-valued, the "
            "non-value-optional and the default-supplying ones the engine cannot "
            "append; the failing test's column raises at the engine ('Cannot add "
            "a UNIQUE column') and several passing tests raise likewise. It does "
            "NOT resolve."),
        "rationale": (
            "REJECT from (Q): at (isUnique, acceptsNull, hasServerDefault) = "
            "(true, true, true) the clause pins `out = true` (all three "
            "disjuncts present at once), but the rival returns `false`. Refuted "
            "at the all-signals-present corner, which no other case in this "
            "battery probes — deliberately NOT at the failing test's (T,T,F), so "
            "this constant rival and the weak-drop-unique near-miss are "
            "discriminated at DIFFERENT inputs rather than sharing one (they "
            "fail for different reasons: this one ignores every signal, that one "
            "only the uniqueness signal, and it is the near-miss that agrees "
            "with the frozen decision over the rest of the domain). Refuted "
            "decidably. If it VERIFIES => SPEC-TOO-WEAK (the rebuild route "
            "unpinned). (Nagini sibling: weak-always-append.)"),
        "witness": _witness(True, True, True),
    },
    {
        "id": "weak-swap-route",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW / label swap: compute the CORRECT decision, then emit its
        # negation. Wrong on all 8 points. Witnessed at (F,F,T) — a point no
        # other case probes, and one where the correct answer is `true` for two
        # independent reasons.
        "module": _impl("    return !(isUnique || !acceptsNull || hasServerDefault)"),
        "refinement": (
            "computing the correct decision and then acting on its negation is "
            "what a real counterpart that wired the two route bodies backwards "
            "would do — the lightweight in-place primitive on the columns that "
            "require a rebuild, and a full table rebuild on the ones the "
            "in-place primitive handles. Every column then takes the wrong "
            "route: the failing test's uniquely-valued column raises at the "
            "engine, and the passing test that asserts no table creation and no "
            "table drop for a plain value-optional column sees a rebuild. It "
            "does NOT resolve."),
        "rationale": (
            "REJECT from (Q): the rival returns the exact negation of the "
            "clause's right-hand side, so (Q) fails at EVERY point of the cube. "
            "Witnessed at (isUnique, acceptsNull, hasServerDefault) = (false, "
            "false, true), where the clause pins `out = true` for two "
            "independent reasons (value-absence and the default) and the rival "
            "returns `false` — a point no other case in this battery probes, and "
            "chosen over the failing test's shape precisely so this rival does "
            "not share a witness with weak-drop-unique. CONTROL-FLOW-EFFECT: the "
            "returned decision IS the route label, so a swap is fully observable "
            "to the value abstraction and needs no separate effect channel. "
            "Refuted decidably. If it VERIFIES => SPEC-TOO-WEAK (the route "
            "labels not pinned to the decision). (Nagini sibling: "
            "weak-swap-route.)"),
        "witness": _witness(False, False, True),
    },
    {
        "id": "weak-carve-unique-and-value-absence",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every rival above is refuted somewhere in the
        # `acceptsNull = true` half or at (F,F,*); the two points (T,F,F) and
        # (T,F,T) — a uniquely-valued column that ALSO disallows an absent value
        # — were probed by nothing. This rival carves exactly the
        # `isUnique && !acceptsNull` corner out of the frozen decision and
        # answers `false` there: an OVERLAP rival, wrong only where two
        # rebuild-forcing reasons coincide, which the per-disjunct near-misses
        # structurally cannot express (each of them drops a whole disjunct, so
        # each is still correct wherever a second reason is present).
        "module": _impl(
            "    return (if (isUnique && !acceptsNull) then false else "
            "(isUnique || !acceptsNull || hasServerDefault))"),
        "refinement": (
            "carving out the overlap is what a real counterpart that guarded the "
            "rebuild route with an exclusivity test — treating the two "
            "column-shape reasons as mutually exclusive alternatives rather than "
            "as independent disjuncts — would do. A column that is both uniquely "
            "valued and disallows an absent value then routes to the in-place "
            "primitive, and the engine refuses such an addition on BOTH counts "
            "(it can neither append a uniquely-valued column nor append a column "
            "disallowing an absent value with nothing to backfill), so the "
            "operation raises. Named passing tests that add a non-value-optional "
            "uniquely-valued column fail. It does NOT resolve."),
        "rationale": (
            "REJECT from (Q): at (isUnique, acceptsNull, hasServerDefault) = "
            "(true, false, false) the clause pins `out = true` (two reasons "
            "present at once — the uniqueness obligation and the value-absence), "
            "but the rival's exclusivity guard fires and returns `false`. This "
            "closes the last structural gap in the reject lane: the six rivals "
            "above are refuted only in the `acceptsNull = true` half or at "
            "(F,F,*), leaving the two OVERLAP points (T,F,F) and (T,F,T) — where "
            "two rebuild-forcing reasons coincide — probed by nothing, and a "
            "per-disjunct near-miss can never reach them (dropping one disjunct "
            "is invisible wherever another disjunct still holds). So this rival "
            "attacks the one thing the disjunct-wise lane cannot: that (Q)'s "
            "disjuncts are INDEPENDENT rather than exclusive. Refuted decidably. "
            "If it VERIFIES => SPEC-TOO-WEAK (the overlap sub-domain unpinned). "
            "(Nagini sibling: none — the sibling's rivals are per-disjunct too.)"),
        "witness": _witness(True, False, False),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 11 SPEC cases (3
# soundness positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 6
# uniqueness rivals) plus 2 AXIOM_TESTS. Every one is accounted for below.
#
# The two surfaces model the SAME decision, but over different carriers. The
# sibling contracts `add_column(col)` over a heap `ColumnSpec` object whose three
# flags are held at fractional read-only permissions, with a @Pure helper
# computing a FOUR-way disjunction (primary-key, unique, value-absence, default)
# and a @ContractOnly callee for the default observation, pinned by seven
# postcondition clauses (a two-valued route discriminator, the load-bearing
# both-directions pin, four one-directional fortifications, and the
# in-place-only-when-every-signal-absent converse). This bundle contracts ONE
# method over THREE immutable `Bool` values with ONE `ensures`, because on this
# carrier (a) the effective-uniqueness observation SUBSUMES the primary-key one
# (mapping.md §2 — a primary column is always uniquely valued, so the two
# sibling disjuncts collapse to one binder), and (b) an equality clause pins the
# decision in both directions on its own, making the sibling's Q0/Q2..Q6
# fortifications redundant rather than absent: each is implied by (Q).
#
#   sibling case            kind            -> here
#   -----------------------------------------------------------------------
#   pos-call-helper         soundness       -> pos-staged-locals        PORTED
#   pos-disjunct-reorder    soundness       -> pos-disjunct-reorder     PORTED
#   pos-negated-append-first soundness      -> pos-negated-inplace-first PORTED
#   admiss-reads            admissibility   -> admiss-nondegenerate     PORTED (re-aimed)
#   frame-mut-write         uniqueness      -> (none)                   VACUOUS
#   weak-prepatch           uniqueness      -> weak-drop-unique         PORTED (merged)
#   weak-drop-unique        uniqueness      -> weak-drop-unique         PORTED (merged)
#   weak-drop-pk            uniqueness      -> (none)                   VACUOUS (carrier collapse)
#   weak-always-append      uniqueness      -> weak-always-inplace      PORTED
#   weak-always-rebuild     uniqueness      -> weak-always-rebuild      PORTED
#   weak-swap-route         uniqueness      -> weak-swap-route          PORTED
#   (added, per-disjunct)   uniqueness      -> weak-drop-value-absence  ADDED
#   (added, per-disjunct)   uniqueness      -> weak-drop-default        ADDED
#   (added, overlap)        uniqueness      -> weak-carve-unique-and-value-absence
#                                                                       ADDED (audit)
#   ax-sound-has_effective_default  axiom   -> (none)                   G-AX / no axiom
#   ax-cover-has_effective_default  axiom   -> (none)                   G-AX / no axiom
#
# 8 ported (3 soundness, 1 admissibility, 4 uniqueness — two sibling rivals
# merging into one) + 3 added uniqueness = 11 velvet cases.
#
# PORTED — soundness (3). pos-disjunct-reorder carries over directly (operand
#   permutation; `||` commutes). pos-negated-append-first -> pos-negated-inplace-
#   first (test the negated in-place-suffices condition first; De Morgan). pos-
#   call-helper -> pos-staged-locals: the sibling routes via its @Pure helper,
#   which this bundle does not model (the `pure` region is empty and the decision
#   is inlined), so the "compute the decision through a named intermediate rather
#   than one expression" argument is carried over as two-step `let` staging,
#   RE-ASSOCIATED (grouping value-absence with the default) so that it is not
#   merely the frozen parse tree with a sub-term named. All three verify under the
#   frozen `loom_solve` (real builds, EXIT 0) and none is definitionally the
#   frozen return (`rfl` fails on each of the three equations, measured), so each
#   is a real shape test rather than a reduction. No soundness positive was
#   dropped for a proof that would not close.
# PORTED — admissibility (1), re-aimed. admiss-reads asserted the three column
#   flags are READABLE under their half-permissions, i.e. that the precondition
#   admits a normally-shaped column. There is no `require` clause here and no
#   permission surface, so that probe is degenerate; the case is re-aimed at the
#   residual total-domain risk, post-image NON-DEGENERACY, asserting (Q)'s
#   right-hand side is `true` at each of its three reasons separately and `false`
#   at the all-absent point. Frozen body kept verbatim (real build, EXIT 0).
# PORTED — uniqueness (4, from 5 sibling rivals). weak-prepatch and
#   weak-drop-unique MERGE into one rival here: the sibling's pre-image drops the
#   two disjuncts its gold added (primary-key AND unique) while its
#   weak-drop-unique drops only the unique one, but this carrier has a single
#   `isUnique` binder subsuming both (mapping.md §2), so the two sibling impls are
#   the SAME impl on this carrier — `!acceptsNull || hasServerDefault`, which is
#   also this bundle's own Solution_prepatch. Shipping it twice would be two case
#   ids for one rival, so it ships once, as the pre-image, carrying the stronger
#   refinement of the two. weak-always-append -> weak-always-inplace,
#   weak-always-rebuild and weak-swap-route carry over directly. All four
#   witnesses confirmed out-of-band: each ELABORATES against its rival (EXIT 0)
#   and FAILS on the frozen solution (EXIT 1, `decide` proving the tester is
#   `true` at that input).
# ADDED — uniqueness (2), and this is the load-bearing addition of the port.
#   The sibling's near-misses attack only the two disjuncts its gold patch ADDED,
#   leaving the two pre-existing ones (value-absence, server-side default)
#   attacked by nothing sharper than its two constants. But the frozen clause
#   here pins all THREE disjuncts, and each binder has exactly ONE observability
#   point (the sub-cube where the other two disjuncts are absent), so a battery
#   without these two cases would hold `acceptsNull` and `hasServerDefault` at
#   values where a rival dropping either could not be distinguished — precisely
#   the gap that lets a rival ignore a binder and verify. weak-drop-value-absence
#   (refuted at (F,F,F)) and weak-drop-default (refuted at (F,T,T)) close it,
#   each a 7-of-8-correct partial-domain rival whose faithful counterpart breaks a
#   named passing test. Both witnesses confirmed out-of-band (rival EXIT 0, gold
#   EXIT 1).
# VACUOUS — uniqueness (1), carrier collapse: weak-drop-pk. The sibling drops its
#   `primary_key` disjunct and is refuted by a value-optional, defaultless,
#   non-unique PRIMARY-KEY column. That column does not exist on this carrier: the
#   effective-uniqueness observation this bundle models is `_unique or
#   primary_key` (mapping.md §2 records the collapse and G-CONF differential-tests
#   it over the full raw cube), so a primary column necessarily has `isUnique =
#   true` and the sibling's discriminating input maps to (T,T,F) — the SAME point
#   that already refutes weak-drop-unique, by the SAME clause. The rival's impl
#   maps to the identical Lean text as weak-drop-unique's, so it is not a distinct
#   rival on this carrier at all. Dropped as an abstraction collapse, per the
#   porting rule that a rival the carrier does not keep distinct is not actually
#   wrong here in its own right — NOT dropped for difficulty.
# VACUOUS — frame/permission-mutation (1): frame-mut-write keeps the sibling's
#   body verbatim and adds a no-op STORE back into a column flag held at a
#   fractional read-only permission, which its verifier must reject for
#   insufficient permission. This backend is referentially transparent — no heap,
#   no aliasing, no fractional permission, no `Old` — and this bundle declares NO
#   `mut` binder: all three observations are immutable `Bool` values. There is no
#   read-only field to overwrite, no permission to under-hold, and no substitute
#   probe. NOT ported and NOT replaced by a fabricated stand-in (porting map:
#   this class is vacuous on a referentially-transparent backend).
#   DEMONSTRATED rather than asserted (audit): the nearest analogue of the
#   sibling's no-op store, `isUnique := isUnique` inserted in the impl region with
#   the frozen body otherwise verbatim, does not even ELABORATE here — the build
#   fails with "`isUnique` cannot be mutated, only variables declared using `let
#   mut` can be mutated" (a parse/elaboration rejection at the binder, followed by
#   `Failed to parse an assertion without names: WPGen sorry`). So the rival is
#   rejected by the LANGUAGE before any spec is consulted, which is precisely why
#   it attributes nothing to the spec and cannot be a reject case: its refutation
#   would be a syntax error, not a witness. This is the demonstration the porting
#   rule requires ("the carrier collapses this distinction"), not an appeal to
#   difficulty.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless. Additionally there is no `axiom` here to probe: the
#   sibling's A-consumed @ContractOnly callee for the default observation is
#   modeled on this carrier as the FREE boolean input `hasServerDefault`, with
#   nothing asserted about how it is produced, so there is nothing to validate
#   against a real callee (mapping.md §3 records the G-AX skip).
#
# COVERAGE. The single obligation `prove_correct requiresTableRebuild` is
# DEFENDED by 3 soundness positives + 1 admissibility case and ATTACKED by 7
# uniqueness rivals. The sole top-level clause (Q) is attacked in BOTH directions
# — three near-misses, the label swap and the overlap carve-out for the `true`
# direction, weak-always-rebuild for the `false` direction. All THREE input
# binders are VARIED by the reject witnesses, each at its own observability
# point: `isUnique` at (T,T,F) vs (F,T,F), `acceptsNull` at (F,F,F) vs (F,T,F),
# `hasServerDefault` at (F,T,T) vs (F,T,F). The witnesses probe SEVEN DISTINCT
# points of the 8-point cube — (T,T,F), (F,F,F), (F,T,T), (F,T,F), (T,T,T),
# (F,F,T), (T,F,F) — so pts = 7 and no two rivals lean on the same input: in
# particular each near-miss (correct on 7 of 8 points) is discriminated at ITS
# point rather than sharing a constant rival's, so every rationale's claimed
# sub-domain is the one its witness demonstrates. Only (T,F,T) is unprobed, and
# it is the sole point at which all three reasons but one coincide with a point
# already covered — every impl this battery's shapes can express that is wrong
# at (T,F,T) is also wrong at (T,F,F), which weak-carve-unique-and-value-absence
# holds. The reject lane is NON-EMPTY, so SPEC-TOO-WEAK is detectable.
#
# AUDIT ADDENDUM (independent re-derivation, real builds). Attack D wrote FIVE
# new wrong impls the battery did not contain, aimed at the least-probed
# structure: two overlap carve-outs (`isUnique && !acceptsNull` -> false, and
# the same with the default present), an exclusive-or reshape
# (`(isUnique != acceptsNull) || hasServerDefault`), a conjunction-instead-of-
# disjunction, and an UNCONSTRAINED demonic choice (`let r :| True; return r`).
# All five FAILED to verify (EXIT 1) — no spec hole found; the first was strong
# enough to be worth shipping and is now the seventh rival. Attack E wrote FIVE
# new correct reshapes — a `match` truth table over the three bools, a nested
# `if` ladder, a single De Morgan negation, a `decide` over the Prop-level
# disjunction, and a `:|` choice echoing the frozen decision — and ALL FIVE
# VERIFIED (EXIT 0), so the spec rejects no faithful correct impl this audit
# could construct. No spec-level gap remains: the divergence lane is closed by
# this bundle's `total` semantics (see the DIVERGENCE entry), unchanged.
AXIOM_TESTS = []

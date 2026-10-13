"""properties.py — G-PBT falsification battery for django__django-16315 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves or prepends a ground ``have``, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_renderUpsertClause``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

PORT NOTE — carrier narrowing vs the nagini sibling.
The nagini battery contracts TWO functions with fractional-permission,
read-only-input contracts — ``lookup(name, field_names, field_columns) -> int``
(resolve one requested field name to its storage COLUMN) and
``conflict_columns(...) -> List[int]`` (map every requested name to its column) —
over a ``PSeq`` carrier with a grounded front-recursive ``column_for`` oracle.
This Lean bundle models the SAME purely-functional core one level DOWN the
pipeline: the renderer that consumes the already-resolved field objects and emits
the SQL suffix, over a ``List FieldRef`` carrier (each ``FieldRef`` carries the
two touched attributes, its declared ``name`` and its database ``column``). The
single load-bearing obligation is the equation pinning the rendered suffix:

  result =
    "ON CONFLICT(" ++ join ", " (uniqueFields.map (quoteName ∘ .column))
      ++ ") DO UPDATE SET " ++ join ", " (updateFields.map assignColumn)

where ``assignColumn f`` is ``q ++ " = EXCLUDED." ++ q`` with ``q = quoteName
f.column``. Both rendered slots are keyed by each field's database ``column``,
never its declared ``name``, and both are pinned element-wise to the input lists,
so no component is unconstrained.

The BEHAVIOURAL DISCRIMINATOR (the fix): render each field by its ``.column``,
not its ``.name``. The two collapse only when a field declares no distinct
database column; when one does (the reported ``db_column`` case, name != column)
they diverge, and the pre-fix code rendered the ``.name``. The nagini
name-vs-column rivals (``rej-lookup-returns-name`` / ``rej-lookup-returns-arg``)
carry over directly, and here they apply to BOTH rendered slots — the conflict
target list AND the DO UPDATE SET list — because the observable spans both.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``uniqueFields`` (the
conflict-target fields) and ``updateFields`` (the assigned fields). Both are
load-bearing and both are varied across the reject witnesses: the conflict-target
slot is attacked with ``uniqueFields`` non-empty and ``updateFields`` empty; the
assignment slot with ``updateFields`` non-empty and ``uniqueFields`` empty; and
one witness has BOTH binders non-empty at the reported arity. The six reject
witnesses probe six DISTINCT input tuples (``pts=6``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling carries two
    frame-mutation rivals (write into a read-only ``field_columns`` held at 1/2
    or 1/4 permission, which Viper rejects for insufficient permission). Lean is
    referentially transparent: ``uniqueFields`` / ``updateFields`` are immutable
    values, there is no ``mut`` input binder, no aliasing, and no read-only cell
    to overwrite. The class has no expressible instance here; no substitute is
    fabricated (porting map: vacuous on lean).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def``; a diverging implementation cannot be written at all, so
    there is nothing to port and no known spec hole to record.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by a structural equation over the two input lists (the literal
    template text is verbatim; each slot is ``map``/``intercalate`` over the
    inputs). There is no opaque answer key an implementation could echo —
    quoting each field's own ``.column`` IS the work. In its place the battery
    carries honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on the (name == column)
    sub-domain but diverging where the fix bites (name != column): render the
    conflict-target slot by ``.name``; render the assignment slot by ``.name``;
    plus three structural rivals — drop the first conflict target, drop the
    first assignment, and reverse the assignment order — that attack the
    element-wise / ordering content of the two slots, and one value rival that
    bypasses the quote-once guard so it diverges only on an already-quoted
    identifier.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl``/``rw`` proof is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it by ``decide`` (the
carrier is fully computable: ``List Char`` with concrete ``quoteName`` /
``assignColumn``, no opaque term). Each witness binds NOTHING in its head (all
inputs are ground ``FieldRef`` list literals), so there are no hypotheses whose
consistency could be in question. Each was checked with two real ``lake env
lean`` builds to HOLD of its rival (elaborates) and to FAIL on the frozen
solution (``decide`` proves the spec DOES hold there), so it discriminates
rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real patch renders the
emitted suffix by the field NAME (or mis-orders / drops a rendered field), so on
the reported ``db_column`` scenario the ``ON CONFLICT`` / ``DO UPDATE SET`` clause
names an identifier that does not exist in the database and the produced SQL is
invalid — exactly the reported defect, so the F2P db_column test would NOT
resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (``quoteName`` / ``assignColumn`` are modeled concretely); the axiom
lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` (an A-reference probe there)
are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-16315"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# All anchors lie ENTIRELY inside the impl region (or, for the admissibility
# positive, at the proof-body intro line) so same_spec stays byte-identical.

# The conflict-target (unique-fields) loop body — renders each field's COLUMN.
_I_UNIQUE_BODY = "    uniqueCols := uniqueCols ++ [quoteName f.column]"
# The whole conflict-target loop (header + body), for structural reshapes.
_I_UNIQUE_LOOP = (
    "  for f in uniqueFields do\n"
    "    uniqueCols := uniqueCols ++ [quoteName f.column]")
# The assignment (update-fields) loop body — renders each field's COLUMN.
_I_ASSIGN_BODY = "    assigns := assigns ++ [assignColumn f]"
# The whole assignment loop (header + body), for structural reshapes.
_I_ASSIGN_LOOP = (
    "  for f in updateFields do\n"
    "    assigns := assigns ++ [assignColumn f]")

# The frozen proof-body intro line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro uf vf\n"

# The whole impl body (unique inside Solution.lean), for a positive that replaces
# the accumulate-and-join loops with a different ALGORITHM rather than a locally
# reshaped loop body.
_I_WHOLE = (
    "def implementation_renderUpsertClause\n"
    "    (uniqueFields updateFields : List FieldRef) : List Char := Id.run do\n"
    "  let mut uniqueCols : List (List Char) := []\n"
    "  for f in uniqueFields do\n"
    "    uniqueCols := uniqueCols ++ [quoteName f.column]\n"
    "  let mut assigns : List (List Char) := []\n"
    "  for f in updateFields do\n"
    "    assigns := assigns ++ [assignColumn f]\n"
    "  return \"ON CONFLICT(\".toList ++ List.intercalate \", \".toList uniqueCols\n"
    "    ++ \") DO UPDATE SET \".toList ++ List.intercalate \", \".toList assigns\n")

# The frozen proof body AFTER the intro line, for a positive whose reshape is not
# definitionally the frozen loop and so must genuinely RE-PROVE the obligation.
# Only the tactic body changes; the theorem STATEMENT stays byte-identical, and
# no new top-level declaration / axiom / assumption token is introduced.
_P_BODY_TAIL = (
    "  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause\n"
    "  simp only [Id.run, bind]\n"
    "  rw [foldMapHelper_renderUpsertClause (fun f => quoteName f.column) uf [],\n"
    "      foldMapHelper_renderUpsertClause assignColumn vf []]\n"
    "  simp only [List.nil_append]\n"
    "  rfl\n")


# ---- FieldRef literals + witness scaffold -----------------------------------
def _fr(name, col):
    return '{ name := "%s".toList, column := "%s".toList }' % (name, col)


def _w(uf, vf):
    """Refute the render equation at one concrete (uniqueFields, updateFields)."""
    return (
        "example : ¬ problem_spec_renderUpsertClause\n"
        f"    {uf} {vf}\n"
        f"    (implementation_renderUpsertClause {uf} {vf}) := by\n"
        "  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_renderUpsertClause` statement byte-identical and reuses
    # the frozen proof (the reshape is definitionally the frozen loop body, so
    # `foldMapHelper` + `rfl` still close — no proof authoring, no helper lemma,
    # no assumption token). (Verified: real build.)
    # =====================================================================
    {
        "id": "pos-unique-quote-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the quoted conflict-target column to a local before appending.
        "module": _swap(
            _BASE, _I_UNIQUE_BODY,
            "    let q := quoteName f.column\n"
            "    uniqueCols := uniqueCols ++ [q]"),
        "rationale": "correct reshape that binds the quoted conflict-target column "
                     "to a local before appending; it computes the SAME slot on "
                     "every input, so the render equation still holds — else "
                     "SPEC-TOO-STRONG. Definitionally the frozen loop body, so the "
                     "frozen proof (foldMapHelper + rfl) still closes; statement "
                     "byte-identical, no new axiom/lemma. Ports the nagini "
                     "pos-lookup-local-reshape positive (there: bind the matched "
                     "slot's column to a typed local; here the quoted column is "
                     "bound in the conflict-target loop).",
    },
    {
        "id": "pos-assign-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the assignment text to a local before appending.
        "module": _swap(
            _BASE, _I_ASSIGN_BODY,
            "    let a := assignColumn f\n"
            "    assigns := assigns ++ [a]"),
        "rationale": "correct reshape that binds the per-field assignment text to a "
                     "local around the forward-append; identical value on every "
                     "input, so the render equation still holds — else "
                     "SPEC-TOO-STRONG. Definitionally the frozen loop body, so the "
                     "frozen proof still closes; statement byte-identical, no new "
                     "axiom/lemma. Ports the nagini pos-cc-local-reshape positive "
                     "(there: an extra local alias around the forward-append).",
    },

    # =====================================================================
    # AUDIT-ADDED POSITIVES. The two positives above are only DEFINITIONALLY
    # equal to the frozen loop body (`let q := e` in place of `e`), so the frozen
    # proof closes unchanged and the spec is never asked to accept a genuinely
    # different computation — a weak soundness test. These two replace the
    # ALGORITHM and therefore have to re-prove the obligation from the reshaped
    # term: one drops the imperative accumulation entirely, the other accumulates
    # the conflict-target slot backwards and reverses at the end. Both keep the
    # theorem STATEMENT byte-identical and add no declaration, axiom, or
    # assumption token — only the tactic body differs, which variant_scope
    # permits. If the spec rejected either, it would be pinning the frozen
    # loop's SHAPE rather than the rendered suffix — SPEC-TOO-STRONG.
    # (Both verified: real builds.)
    # =====================================================================
    {
        "id": "pos-pure-functional-noloop",
        "kind": "soundness",
        "expect": "verify",
        # No do-block, no mutable accumulator: map/intercalate directly.
        "module": _swap(
            _swap(
                _BASE, _I_WHOLE,
                "def implementation_renderUpsertClause\n"
                "    (uniqueFields updateFields : List FieldRef) : List Char :=\n"
                "  \"ON CONFLICT(\".toList\n"
                "    ++ List.intercalate \", \".toList "
                "(uniqueFields.map (fun f => quoteName f.column))\n"
                "    ++ \") DO UPDATE SET \".toList\n"
                "    ++ List.intercalate \", \".toList (updateFields.map assignColumn)\n"),
            _P_BODY_TAIL,
            "  unfold problem_spec_renderUpsertClause "
            "implementation_renderUpsertClause\n"
            "  rfl\n"),
        "rationale": "correct reshape that abandons the imperative accumulation "
                     "entirely — the suffix is rendered as a direct "
                     "map/intercalate expression with no do-block and no mutable "
                     "accumulator. It computes the SAME suffix on every input, so "
                     "the render equation still holds; the reshape is NOT "
                     "definitionally the frozen loop, so the proof is re-derived "
                     "(the loop lemma is no longer needed and `rfl` closes the "
                     "reshaped term directly). Statement byte-identical, no new "
                     "axiom/lemma/assumption token. A rejection here would mean "
                     "the spec pins the frozen loop's SHAPE rather than the "
                     "rendered suffix — SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-unique-prepend-reverse",
        "kind": "soundness",
        "expect": "verify",
        # Accumulate the conflict-target slot by PREPENDING, then reverse it.
        "module": _swap(
            _swap(
                _swap(
                    _BASE, _I_UNIQUE_BODY,
                    "    uniqueCols := quoteName f.column :: uniqueCols"),
                "  return \"ON CONFLICT(\".toList ++ List.intercalate \", \".toList "
                "uniqueCols",
                "  return \"ON CONFLICT(\".toList ++ List.intercalate \", \".toList "
                "uniqueCols.reverse"),
            _P_BODY_TAIL,
            # Re-prove the prepending accumulation in place: a ground `have`
            # inside the existing tactic body, not a new top-level lemma.
            "  unfold problem_spec_renderUpsertClause "
            "implementation_renderUpsertClause\n"
            "  simp only [Id.run, bind]\n"
            "  have hpre : ∀ (xs : List FieldRef) (init : List (List Char)),\n"
            "      (forIn (m := Id) xs init\n"
            "        (fun f acc => pure (ForInStep.yield "
            "(quoteName f.column :: acc))))\n"
            "        = (xs.map (fun f => quoteName f.column)).reverse ++ init := by\n"
            "    intro xs\n"
            "    induction xs with\n"
            "    | nil => intro init; simp; rfl\n"
            "    | cons a as ih =>\n"
            "      intro init\n"
            "      rw [List.forIn_cons]\n"
            "      simp only [bind] at ih ⊢\n"
            "      rw [ih]\n"
            "      simp [List.append_assoc]\n"
            "  rw [hpre uf [], "
            "foldMapHelper_renderUpsertClause assignColumn vf []]\n"
            "  simp only [List.append_nil, List.nil_append, "
            "List.reverse_reverse]\n"
            "  rfl\n"),
        "rationale": "correct reshape that builds the conflict-target slot in "
                     "REVERSE (cons onto the front) and reverses it at the end — "
                     "the same rendered slot by a different accumulation order, so "
                     "the render equation still holds. The frozen forward-append "
                     "loop lemma does not apply to a prepending loop, so this "
                     "positive re-proves the accumulation in place with a ground "
                     "`have` induction inside the existing tactic body (no new "
                     "top-level lemma, statement byte-identical, no assumption "
                     "token). A rejection would mean the spec pins the "
                     "accumulation ORDER rather than the rendered slot — "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission self-call (admiss-lookup-precond-establishable) has
    # no binder to attack here; the honest analogue is to discharge the spec
    # predicate by evaluation at a ground db_column-shaped input (name != column
    # in both a conflict target and an assigned field), then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, ground instance is a `have` prepended to the tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-dbcolumn-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_renderUpsertClause "
            f"[{_fr('rank', 'rAnK')}] [{_fr('sectorid', 'SectorID')}]\n"
            "      (implementation_renderUpsertClause "
            f"[{_fr('rank', 'rAnK')}] [{_fr('sectorid', 'SectorID')}]) := by\n"
            "    unfold problem_spec_renderUpsertClause implementation_renderUpsertClause\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at a ground db_column-shaped "
                     "input (a conflict target and an assigned field, each with a "
                     "declared database column distinct from its name — the "
                     "reported scenario) by evaluation as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input "
                     "— the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, statement byte-identical, ground instance is "
                     "a `have` in the existing tactic body. Ports nagini's "
                     "admiss-lookup-precond-establishable.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself, conflict-target slot: render by NAME not COLUMN ----
    {
        "id": "weak-unique-renders-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior on the conflict-target slot: quote each field's declared
        # NAME instead of its database column.
        "module": _swap(
            _BASE, _I_UNIQUE_BODY,
            "    uniqueCols := uniqueCols ++ [quoteName f.name]"),
        "refinement": "this IS the pre-fix dataflow on the conflict-target slot: it "
                      "renders each field's declared name rather than its database "
                      "column. When a conflict-target field declares a distinct "
                      "database column the emitted ON CONFLICT(...) names an "
                      "identifier that does not exist in the database, producing "
                      "invalid SQL — exactly the reported defect. The F2P db_column "
                      "test asserts the column-keyed clause, so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from the render equation: the spec pins the first slot "
                     "to `uniqueFields.map (quoteName ∘ .column)` but the rival "
                     "emits `quoteName ∘ .name`, which differ whenever a "
                     "conflict-target field's column != its name. Refuted with a "
                     "single conflict target whose name/column differ and no "
                     "assigned fields.",
        "witness": _w("[%s]" % _fr("rank", "rAnK"), "[]"),
    },

    # ---- the fix itself, assignment slot: render by NAME not COLUMN ----
    {
        "id": "weak-assign-renders-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior on the DO UPDATE SET slot: build the assignment from the
        # field's declared NAME instead of its database column.
        "module": _swap(
            _BASE, _I_ASSIGN_BODY,
            "    let q := quoteName f.name\n"
            "    assigns := assigns ++ [q ++ \" = EXCLUDED.\".toList ++ q]"),
        "refinement": "this IS the pre-fix dataflow on the assignment slot: it "
                      "builds `col = EXCLUDED.col` from each field's declared name "
                      "rather than its database column. When an assigned field "
                      "declares a distinct database column the emitted DO UPDATE "
                      "SET names an identifier that does not exist, producing "
                      "invalid SQL. The F2P db_column test asserts the column-keyed "
                      "clause, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the render equation: the spec pins the second "
                     "slot to `updateFields.map assignColumn` (each keyed by "
                     "`.column`) but the rival keys each assignment by `.name`, "
                     "which differ whenever an assigned field's column != its name. "
                     "Refuted with a single assigned field whose name/column differ "
                     "and no conflict targets — a DISTINCT point exercising the "
                     "updateFields binder.",
        "witness": _w("[]", "[%s]" % _fr("rank", "rAnK")),
    },

    # ---- structural, conflict-target slot: drop the first conflict target ----
    {
        "id": "weak-unique-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Iterate the conflict-target list with its first element dropped, omitting
        # one conflict target from the rendered ON CONFLICT(...) slot.
        "module": _swap(
            _BASE, _I_UNIQUE_LOOP,
            "  for f in uniqueFields.drop 1 do\n"
            "    uniqueCols := uniqueCols ++ [quoteName f.column]"),
        "refinement": "drops the FIRST conflict-target field from the rendered "
                      "ON CONFLICT(...) list. A faithful patch that omitted a "
                      "conflict target would key the upsert on a strict subset of "
                      "the requested unique fields, so the generated statement no "
                      "longer matches on the intended row and the F2P upsert "
                      "behaves differently — it would NOT resolve.",
        "rationale": "REJECT from the render equation: the spec pins the first slot "
                     "to a comma-joined map over ALL conflict "
                     "targets, but the rival renders only the tail, so for a "
                     "non-empty conflict-target list the rendered suffix differs. "
                     "Refuted with a two-element conflict-target list (distinct "
                     "columns) and no assigned fields — a distinct point.",
        "witness": _w(
            "[%s, %s]" % (_fr("a", "aa"), _fr("b", "bb")), "[]"),
    },

    # ---- structural, assignment slot: reverse the assignment order ----
    {
        "id": "weak-assign-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Render the assignment list with its field order reversed.
        "module": _swap(
            _BASE, _I_ASSIGN_LOOP,
            "  for f in updateFields.reverse do\n"
            "    assigns := assigns ++ [assignColumn f]"),
        "refinement": "renders the DO UPDATE SET assignments in REVERSED field "
                      "order. Equal to gold only when the assignment sequence is a "
                      "palindrome — which INCLUDES the one-element assignment list, "
                      "so this rival is NOT refutable at the narrowest reported "
                      "scenario and a faithful patch flipping the assignment order "
                      "would still pass a single-assigned-field regression test "
                      "(machine-checked: the witness at that one-element input fails "
                      "against this rival). It is kept because the modeled behavior "
                      "is the general renderer, which the reported usage drives with "
                      "SEVERAL assigned fields: with two or more, a faithful patch "
                      "emits the assignment components in the wrong sequence, so the "
                      "clause does not match what the caller requested. The "
                      "F2P-input-refutable structural attack on this slot is carried "
                      "separately by weak-assign-drop-first.",
        "rationale": "REJECT from the render equation: the spec pins the second "
                     "slot to a comma-joined map (updateFields.map assignColumn) in "
                     "caller order, but the rival maps over `updateFields.reverse`; "
                     "for a non-palindromic list (length ≥ 2, distinct columns) the "
                     "rendered suffix differs. Refuted with a two-element "
                     "assignment list and no conflict targets — a distinct point "
                     "exercising the updateFields binder structurally.",
        "witness": _w(
            "[]", "[%s, %s]" % (_fr("a", "aa"), _fr("b", "bb"))),
    },

    # ---- structural, assignment slot: drop the first assignment -------------
    # AUDIT-ADDED. The reject lane's two structural rivals were an order attack
    # on the assignment slot and an omission attack on the conflict-target slot,
    # so the assignment slot had no rival refutable at the narrowest reported
    # input: reversal is the identity on a one-element list. This one omits an
    # assigned field, so it diverges at a single assigned field — the arity the
    # reported scenario's regression coverage actually pins — and it is refuted
    # at the FULL reported tuple (a conflict target AND an assigned field, each
    # with a database column distinct from its name), the only witness in the
    # battery that exercises both binders non-empty at once.
    {
        "id": "weak-assign-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ASSIGN_LOOP,
            "  for f in updateFields.drop 1 do\n"
            "    assigns := assigns ++ [assignColumn f]"),
        "refinement": "drops the FIRST assigned field from the rendered DO UPDATE "
                      "SET list. A faithful patch that omitted an assignment would "
                      "leave the conflicting row's column un-updated, so after the "
                      "upsert the stored values are the pre-existing ones rather "
                      "than the supplied ones and the asserted post-upsert rows "
                      "differ — it would NOT resolve. Unlike the order attack this "
                      "bites at a SINGLE assigned field (dropping it renders an "
                      "empty assignment slot), so it is refutable at the reported "
                      "scenario's own arity.",
        "rationale": "REJECT from the render equation: the spec pins the second slot "
                     "to a comma-joined map over ALL assigned fields "
                     "(updateFields.map assignColumn), but the rival renders only "
                     "the tail, so for any non-empty assignment list the rendered "
                     "suffix differs. Refuted at the full reported tuple — one "
                     "conflict target and one assigned field, each with a database "
                     "column distinct from its declared name — the only point in "
                     "the battery with BOTH binders non-empty.",
        "witness": _w("[%s]" % _fr("rank", "rAnK"),
                      "[%s]" % _fr("sectorid", "SectorID")),
    },

    # ---- value, conflict-target slot: bypass the quote-once guard -----------
    # AUDIT-ADDED. Coverage probe: every other rival differs from gold on which
    # identifier is rendered or on how the slot is sequenced, so the quoting
    # helper's already-quoted branch was pinned by the spec but attacked by no
    # rival. This rival quotes UNCONDITIONALLY; it agrees with gold on every
    # bare identifier and diverges only on an already-quoted one, which is the
    # branch's whole content.
    {
        "id": "weak-unique-double-quotes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_UNIQUE_BODY,
            "    uniqueCols := uniqueCols ++ ['\"' :: (f.column ++ ['\"'])]"),
        "refinement": "wraps every conflict-target identifier in quotes without "
                      "checking whether it is already wrapped, so an "
                      "already-quoted database column is emitted doubly quoted. A "
                      "faithful patch that re-quoted an identifier would emit a "
                      "conflict target the database reads as a different (and "
                      "non-existent) identifier, so the generated statement is "
                      "again invalid — it would NOT resolve.",
        "rationale": "REJECT from the render equation: the spec pins the first slot "
                     "to `uniqueFields.map (quoteName ∘ .column)`, and quoteName is "
                     "quote-ONCE — it returns an already-wrapped identifier "
                     "unchanged. The rival always wraps, so the two differ on any "
                     "pre-quoted column. Refuted at a single conflict target whose "
                     "database column is already quoted: a sub-domain no other "
                     "rival reaches, since all the others agree with gold there.",
        "witness": _w('[{ name := "q".toList, column := "\\"Pre\\"".toList }]', "[]"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 4 uniqueness rivals, 2 frame-mutation rivals, 1 admissibility) plus
# an AXIOM lane (an A-reference probe). This bundle models the SAME purely-
# functional core one level down the pipeline (the renderer over already-resolved
# `List FieldRef`), which fuses the sibling's two contracted functions
# (`lookup` + `conflict_columns`) into one obligation covering BOTH rendered
# slots. Every sibling case is recorded below.
#
#   sibling case                        -> here
#   -----------------------------------------------------------------------
#   pos-lookup-local-reshape            -> pos-unique-quote-local     RE-EXPRESSED
#   pos-cc-local-reshape                -> pos-assign-local           RE-EXPRESSED
#   rej-lookup-returns-name             -> weak-unique-renders-name   PORTED (unique slot)
#                                          + weak-assign-renders-name PORTED (assign slot)
#   rej-lookup-returns-arg-name         -> (folded into the two above) DROPPED (equivalent:
#                                          on this carrier name == f.name; there is no
#                                          separate "requested arg" identifier to echo,
#                                          the requested name IS f.name)
#   rej-lookup-off-by-one-column        -> weak-assign-reversed       RE-EXPRESSED (wrong-field
#                                          / wrong-position rendering; no separately
#                                          modeled `lookup` on this carrier, so the
#                                          neighbour-slot attack becomes an order attack
#                                          on the rendered slot)
#   rej-cc-skip-first                   -> weak-unique-drop-first     PORTED
#                                          + weak-assign-drop-first   AUDIT-ADDED (the same
#                                          omission attack on the OTHER rendered slot,
#                                          refutable at the reported arity)
#   (no sibling case)                   -> weak-unique-double-quotes  AUDIT-ADDED (the
#                                          quote-once sub-domain has no nagini analogue:
#                                          there the resolved column is an opaque int, so
#                                          identifier quoting is not modeled at all)
#   rej-frame-mutate-field-columns      -> (none)                     VACUOUS (referential
#                                          transparency — see assessment)
#   rej-frame-mutate-lookup-columns     -> (none)                     VACUOUS
#   admiss-lookup-precond-establishable -> admiss-ground-dbcolumn…    RE-EXPRESSED
#   AXIOM_TESTS (A-reference probe)     -> (none)                     DROPPED (G-AX)
#
# The sibling's name-vs-column attack is expressed twice here (once per rendered
# slot) because the observable spans both the ON CONFLICT(...) conflict targets
# and the DO UPDATE SET assignments, and the spec keys BOTH by `.column`. This is
# not case-count padding: each attacks a distinct sub-term of the one equation,
# and each is refuted at its own input point (different binder non-empty).
#
# POINT SPREAD. The six reject witnesses probe six DISTINCT input tuples (pts=6):
#   (uniqueFields, updateFields) =
#     ([{rank,rAnK}], [])                weak-unique-renders-name  (unique value)
#     ([], [{rank,rAnK}])                weak-assign-renders-name  (assign value)
#     ([{a,aa},{b,bb}], [])              weak-unique-drop-first    (unique structure)
#     ([], [{a,aa},{b,bb}])              weak-assign-reversed      (assign structure)
#     ([{rank,rAnK}], [{sectorid,…}])    weak-assign-drop-first    (assign structure,
#                                          BOTH binders non-empty, reported arity)
#     ([{q,"Pre"}], [])                  weak-unique-double-quotes (quoting sub-domain)
#   Both binders are varied (uniqueFields non-empty in three, updateFields
#   non-empty in three, both non-empty in one; empty, single- and multi-element
#   shapes all appear), so neither input binder is pinned across the rivals.
#
# AUDIT NOTE — refutability at the reported arity. `weak-assign-reversed` is NOT
# refutable at a ONE-element assignment list (reversal is the identity there),
# so on its own the assignment slot's structural lane said nothing at the arity
# the narrowest reported usage drives. Machine-checked, then closed by adding
# `weak-assign-drop-first`, which diverges at a single assigned field. The order
# rival is kept for the multi-assignment case, with its refinement corrected.
# `weak-unique-double-quotes` closes the quote-once sub-domain, which the spec
# pins and no other rival attacked (all the others agree with gold on a
# pre-quoted identifier).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# `opaque` callee and consumes no `axiom` (`quoteName` / `assignColumn` are
# modeled concretely), so there is nothing to probe and the gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []

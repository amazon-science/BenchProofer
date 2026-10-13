"""properties.py — G-PBT falsification battery for django__django-13089 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct cullStep`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  cullStep (fetched : Option (List Int)) return (out : Option Int)
    require ∀ row, fetched = some row → row ≠ []
    ensures fetched = none → out = none                          -- C1
    ensures ∀ row, fetched = some row → out = some (row.head!)   -- C2

A maintenance step consults a single-row lookup whose result is EITHER one row
of column values (``some row``) OR absent (``none``). A boundary-dependent action
is taken ONLY when a row is present, parameterised by the row's FIRST column:

  * C1 (discriminating clause) — absent lookup ⇒ NO boundary is produced
    (``out = none``); the absent row is never read from.
  * C2 (grounded oracle) — present lookup ⇒ the produced boundary is EXACTLY the
    row's first column (``row.head!``), grounded in the argument's own content.

The two clauses are the two independent top-level halves of the postcondition;
the single input binder is ``fetched`` (an ``Option (List Int)``), whose absent
case, present-singleton case, and present-multi-column case are the sub-domains
the rivals abuse.

There is NO opaque answer key to echo: both clauses ground the result in the
input (``none`` mirrors the input's absence, ``row.head!`` mirrors the input's
own first column). The ``axioms`` region is empty — no callee is axiomatized —
so the UNGROUNDED-ORACLE-ECHO class is N/A; the cheapest correct impl just reads
``fetched``, which the positive controls cover honestly.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this
    MANDATORY because its ``row`` input is held at a fractional heap permission
    (``Acc(list_pred(row), 1/2)``) an impl can illegally overwrite, and the spec
    must reject the write for INSUFFICIENT PERMISSION. Lean and Velvet are
    referentially transparent: ``fetched`` is an immutable value, this bundle
    declares no ``mut`` binder, there is no heap and no aliasing — so there is no
    read-only field to mutate and no substitute probe to build. Not fabricated
    (per the porting map, this class is legitimately dropped here).
  * DIVERGENCE / NON-TERMINATION: INAPPLICABLE as a shipped reject case, closed by
    the verifier, and NOT vacuous. Two claims here are corrected. The frozen ``do``
    block genuinely has no recursion and no loop, so there is no loop in the frozen
    body to make spin and this bundle ships no divergence rival. But "a diverging
    impl cannot even be written" is withdrawn, since a rival rewrites the whole
    impl region and may splice a loop; and there is no ``partial``-semantics
    KNOWN-HOLE disposition to contrast with, because all 500 velvet bundles set
    ``loom.semantics.termination "total"`` and open ``TotalCorrectness``. Under
    ``total`` a postcondition is claimed of ALL runs, not only terminating ones, so
    the verifier demands a decreasing measure on every loop AND discharges its
    descent; the option cannot drift from the file's ``open`` because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` with body
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. (The nagini sibling
    carries no ``diverge-*`` case anyway.)
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: the
    prepatch defect (unconditional read fabricates a boundary on the absent
    lookup — the reported 'NoneType is not subscriptable' bug); a present-branch
    wrong constant boundary; a present-branch wrong COLUMN (reads the last column
    instead of the first — a near-miss agreeing with gold on single-column rows);
    and the doubly-wrong flip.

CARRIER FOLD (read before judging case count). Nagini distinguishes NOGUARD
(the subscript CRASHES on the absent row) from ABSENT-FABRICATES-KEY (a present
row read correctly, but the absent case invents boundary ``0``). On this carrier
the first-column read is TOTAL (``(fetched.getD []).head! = 0`` when absent — no
crash), so the literal prepatch skeleton (read the first column
UNCONDITIONALLY) IS the "return ``some 0`` on the absent lookup" function: the
two nagini rivals denote the SAME impl here and fold into one prepatch-defect
rival (``weak-prepatch-unconditional-read``). This is a genuine carrier fact
(the totalised read collapses nagini's crash-vs-fabricate distinction), not an
omission for effort.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``cullStepTester args = false`` says the extracted program's result violates the
postcondition at that concrete input. Each rival is a straight-line ``match`` so
its extracted ``…Exec`` kernel-reduces, and every clause is over transparent
carriers (``Option``, ``List Int``, ``head!``) so ``decide`` settles it. The
witness is checked in a file whose ``prove_correct`` block has been stripped, so
no tactic script can mask the verdict. All eight half-checks (four rivals ×
{elaborates against rival, fails against gold}) were confirmed out of band with
real builds.

WITNESS PLACEMENT. The four reject witnesses sit at FOUR DISTINCT ``fetched``
points — ``none``, ``some [5]``, ``some [5, 9]``, ``some [7]`` — so the sole
binder moves across the battery (absent / present-singleton / present-two-column
/ present-singleton-other) and no clause is demonstrated at a single pinned
point. C1 (absent ⇒ none) is attacked by ``weak-prepatch-unconditional-read`` at
``none``. C2 (present ⇒ first column) is attacked by ``weak-present-wrong-key``
at ``some [5]`` (wrong constant), ``weak-reads-wrong-column`` at ``some [5, 9]``
(right shape, WRONG column — a near-miss that AGREES with gold on every
single-column row, so it is refuted only at a ≥2-column row), and
``weak-flip-doubly-wrong`` at ``some [7]`` (present ⇒ none). The flip also
violates C1 (``some 0`` on ``none``); it is witnessed on its C2 sub-domain so it
does not share a point with the prepatch rival.
"""
from pathlib import Path

INSTANCE = "django__django-13089"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen guarded read. Lies wholly inside
# ---- the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). ----
_GOLD_IMPL = (
    "    let lastKey := fetched\n"
    "    if lastKey.isSome then\n"
    "      return some ((lastKey.getD []).head!)\n"
    "    else\n"
    "      return none"
)

assert _BASE.count(_GOLD_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script (`loom_solve`) is elided from
# ---- the consumer spec view, so a case that introduces an in-region `assert`
# ---- may retune the tactic body without touching the spec or dropping the
# ---- `prove_correct cullStep` obligation (its statement stays byte-identical).
# ---- Unique in the file. ----
_GOLD_PROOF = "prove_correct cullStep by\n  loom_solve"

assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Solution.lean with ONLY the impl region body replaced (frozen tactic
    script kept — used for reject rivals, expected NOT to verify)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body (soundness /
    admissibility positives whose in-region change needs a retuned script)."""
    return _swap(_swap(_BASE, _GOLD_IMPL, new_body), _GOLD_PROOF, new_proof)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `cullStepTester args = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. The `require` clause holds at every witnessed input
# ---- (each present row is non-empty; the absent input satisfies it vacuously),
# ---- so nothing is excluded vacuously. ----
_TESTER = (
    "extract_program_for cullStep\n"
    "prove_precondition_decidable_for cullStep\n"
    "prove_postcondition_decidable_for cullStep\n"
    "derive_tester_for cullStep\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `prove_correct cullStep`
    # obligation and only reshapes the executable surface; `loom_solve` still
    # closes it (confirmed out of band with real builds).
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Handle the ABSENT case first via a `match`, then read the present
        # row's first column — the sibling's branch-reorder positive. A
        # different control-flow shape (case-analysis on the Option rather than
        # an `isSome` guard) computing the identical result on both arms.
        "module": _impl(
            "    match fetched with\n"
            "    | none => return none\n"
            "    | some r => return some (r.head!)"),
        "rationale": "branch-reorder: case-analyse `fetched` and handle the "
                     "absent arm first, then read the present row's first "
                     "column. Behaviourally identical to the frozen guarded read "
                     "(C1 holds on the `none` arm, C2 on the `some r` arm), so a "
                     "faithful correct reshape MUST verify — else SPEC-TOO-STRONG. "
                     "(Sibling: pos-control-reorder.)",
    },
    {
        "id": "pos-control-let-bind",
        "kind": "soundness",
        "expect": "verify",
        # Bind the produced Option to a local via a `match` expression, then
        # return it — the sibling's conditional-expression 'echo' of the
        # grounded oracle. A distinct executable surface (no statement-level
        # branch), same value flow.
        "module": _impl(
            "    let out : Option Int := match fetched with\n"
            "      | none => none\n"
            "      | some r => some (r.head!)\n"
            "    return out"),
        "rationale": "conditional-expression form: compute `some row.head!` when "
                     "present and `none` when absent, bind to a local, return it. "
                     "Because both clauses are GROUNDED in `fetched`, this grounded "
                     "'echo' IS the correct impl and must verify. Doubles as the "
                     "UNGROUNDED-ORACLE lane's positive control (no wrong echo "
                     "exists — the answer key is the input). (Sibling: "
                     "pos-control-ternary.)",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method DOES carry a `require` clause
    # (`∀ row, fetched = some row → row ≠ []`), but it is trivially satisfiable
    # for any F2P-shaped input (a genuine result row is non-empty; the absent
    # lookup satisfies it vacuously), so "a normal input satisfies the
    # precondition" is not where the risk sits. This case is re-aimed at the
    # residual admissibility risk: that the post-image is UNSATISFIABLE /
    # DEGENERATE at the interesting point (a spec no impl can meet reads exactly
    # like one every impl meets). It discharges an in-region `assert` pinning the
    # grounded boundary at F2P-shaped rows — a single-column row reports its own
    # value, a multi-column row reports its FIRST column. The surrounding impl is
    # kept verbatim so the method's own `ensures` still discharges; the assert is
    # live (a false claim about the same points leaves an unsolved goal), and the
    # proof gains one `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-firstcol-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (([5] : List Int).head! = 5 ∧ ([7, 9] : List Int).head! = 7))\n"
            + _GOLD_IMPL,
            "prove_correct cullStep by\n  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped rows: the produced boundary is the row's FIRST "
                     "column — a single-column row reports its own value "
                     "(`[5].head! = 5`) and a multi-column row reports its first, "
                     "NOT last, column (`[7, 9].head! = 7`). The in-region assert "
                     "must discharge (else the modeled boundary is degenerate at a "
                     "normal input / PRECOND-TOO-STRONG); the impl is kept verbatim "
                     "so C1/C2 still discharge. (Sibling: admiss-present-and-absent, "
                     "re-aimed at post-image non-degeneracy.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line `match` (so its extracted
    # `…Exec` kernel-reduces) with a machine-checked refutation witness at a
    # DISTINCT concrete `fetched`, and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    # F2P: test_cull_delete_when_store_empty — forces the cull with the store
    # effectively empty so the culling lookup returns NO boundary row, then
    # asserts the just-set record SURVIVES (no boundary delete may be issued).
    # =====================================================================
    {
        "id": "weak-prepatch-unconditional-read",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch defect. Read the first column UNCONDITIONALLY (as the
        # buggy skeleton in Solution_prepatch.lean does). Because the read is
        # totalised, the absent lookup yields `some 0` rather than `none`: a
        # boundary is produced where none is due. Folds nagini's NOGUARD (crash)
        # and ABSENT-FABRICATES-KEY (invent 0) — the same function on this
        # carrier (see CARRIER FOLD in the module docstring).
        "module": _impl(
            "    match fetched with\n"
            "    | none => return some 0\n"
            "    | some r => return some (r.head!)"),
        "refinement": "this is the reported bug: the boundary is read from the "
                      "culling lookup with no presence guard. On the empty-store "
                      "F2P scenario the lookup returns no row, yet a boundary is "
                      "still produced and the delete is issued against a phantom "
                      "boundary — the just-set record can be removed, so "
                      "test_cull_delete_when_store_empty asserting it SURVIVES "
                      "FAILS. Its faithful real patch does NOT resolve.",
        "rationale": "REJECT from C1 (`fetched = none → out = none`): on the absent "
                     "lookup the rival returns `some 0`, not `none`. Refuted at "
                     "`none`. If it verified the spec would be SPEC-TOO-WEAK — it "
                     "would admit the exact prepatch defect (this is what "
                     "Solution_prepatch.lean reproduces, G-DIFF).",
        "witness": _witness("cullStepTester none"),
    },
    {
        "id": "weak-present-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Absent handled correctly (`none`), but a PRESENT row produces a constant
        # boundary (0) instead of the row's first column. Correct on the absent
        # sub-domain, wrong on every present row whose first column is not 0.
        "module": _impl(
            "    match fetched with\n"
            "    | none => return none\n"
            "    | some _ => return some 0"),
        "refinement": "the absent case is handled correctly (no boundary), so it "
                      "passes the empty-store F2P. But on a present row it reports "
                      "a constant boundary (0) instead of the culling row's first "
                      "column, i.e. its real patch would delete against the wrong "
                      "boundary on a populated store — pruning the wrong rows and "
                      "breaking test_cull / test_zero_cull (P2P). Does NOT resolve.",
        "rationale": "REJECT from C2 (`fetched = some row → out = some row.head!`): "
                     "a present row must produce its first column, not the constant "
                     "0. Refuted at `some [5]` (first column 5 ≠ 0). Verifying would "
                     "be SPEC-TOO-WEAK on the boundary value.",
        "witness": _witness("cullStepTester (some [5])"),
    },
    {
        "id": "weak-reads-wrong-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: right SHAPE (present ⇒ some, absent ⇒ none) and
        # even reads a real column of the row, but the LAST column instead of the
        # first. Agrees with gold on EVERY single-column row, so it is refutable
        # only at a ≥2-column row — a strictly sharper discriminator than
        # weak-present-wrong-key, which a first-column test at a singleton row
        # would miss.
        "module": _impl(
            "    match fetched with\n"
            "    | none => return none\n"
            "    | some r => return some (r.getLast!)"),
        "refinement": "reading the row's LAST column instead of its first uses the "
                      "wrong boundary whenever the culling row carries more than "
                      "one column, deleting against a different threshold than the "
                      "documented one — the populated-store cull tests (P2P) read "
                      "back a different boundary. It AGREES with gold on every "
                      "single-column row, so only a multi-column row exposes it; "
                      "its faithful real patch does NOT resolve.",
        "rationale": "REJECT from C2: the spec pins the FIRST column (`row.head!`), "
                     "this rival returns the last. Equal to gold on singleton rows, "
                     "so refuted only at `some [5, 9]` (`head! = 5`, `getLast! = 9`) "
                     "— a distinct input from weak-present-wrong-key's singleton "
                     "that a first-column-only witness set would never probe. This "
                     "is the near-miss that exercises the row-CONTENT binder beyond "
                     "a single column.",
        "witness": _witness("cullStepTester (some [5, 9])"),
    },
    {
        "id": "weak-flip-doubly-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # Doubly wrong: no boundary for a PRESENT row (a delete skipped though
        # due) and a fabricated boundary (0) for the ABSENT row (a delete issued
        # though none is due). Constants only, so the rejection is attributable to
        # the SPEC's two clauses, not a read error.
        "module": _impl(
            "    match fetched with\n"
            "    | none => return some 0\n"
            "    | some _ => return none"),
        "refinement": "doubly wrong: the real patch issues the delete exactly "
                      "backwards — a boundary on the empty store (empty-store F2P "
                      "fails: the just-set record is removed) and no boundary on a "
                      "populated store (test_cull P2P fails: nothing pruned). Does "
                      "NOT resolve on either sub-domain.",
        "rationale": "REJECT from BOTH C1 (returns `some 0` on `none`) and C2 "
                     "(returns `none` where a present row demands `some row.head!`). "
                     "Witnessed on its C2 sub-domain at `some [7]` (a present row "
                     "gets `none`) — a distinct point from the prepatch rival's "
                     "`none`, so it demonstrates C2 rather than re-probing C1 at the "
                     "same input.",
        "witness": _witness("cullStepTester (some [7])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 4 uniqueness rivals) plus an
# EMPTY AXIOM lane. This bundle models the SAME single behaviour (the boundary
# decision of the cull step) as one `method cullStep`, so the value surface
# carries across intact; the permission surface does not exist here. Every
# sibling case is accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder             -> pos-control-branch-reorder     PORTED
#   pos-control-ternary             -> pos-control-let-bind           PORTED
#   admiss-present-and-absent       -> admiss-firstcol-nondegenerate  RE-AIMED
#   frame-mutation-write-row        -> (none)                         VACUOUS
#   noguard-prepatch-defect         -> weak-prepatch-unconditional-read  PORTED
#   partial-absent-fabricates-key   -> weak-prepatch-unconditional-read  FOLDED
#   partial-present-wrong-key       -> weak-present-wrong-key         PORTED
#   flip-doubly-wrong               -> weak-flip-doubly-wrong         PORTED
#   AXIOM_TESTS ([])                -> (none)                         N/A (empty)
#   (new)                           -> weak-reads-wrong-column        ADDED
#
# 5 ported, 1 folded, 1 re-aimed, 1 vacuous; 1 rival ADDED.
#
# VACUOUS (frame-mutation-write-row): the sibling's MANDATORY frame-mutation
#   rival writes to a `row` held at Acc(list_pred(row), 1/2) and is rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: `fetched`
#   is an immutable value, this bundle declares no `mut` binder, there is no heap
#   and no aliasing. There is no read-only field to overwrite and no permission
#   system to trip, so the class is vacuous. No substitute is fabricated (per the
#   porting map, this class is legitimately dropped here rather than replaced).
# FOLDED (partial-absent-fabricates-key): on this carrier the first-column read
#   is TOTAL ((fetched.getD []).head! = 0 on the absent lookup, no crash), so the
#   literal prepatch (unconditional read) IS the "return some 0 on absent"
#   function — nagini's NOGUARD (crash) and ABSENT-FABRICATES-KEY (invent 0)
#   denote the SAME impl here. Both fold into weak-prepatch-unconditional-read.
#   A genuine carrier fact (the totalised read collapses nagini's
#   crash-vs-fabricate distinction), not an effort gap.
# RE-AIMED (admissibility): the sibling establishes the present-row precondition
#   inside the present branch. The `require` clause here (a present row is
#   non-empty) is trivially satisfiable for every F2P-shaped input, so that probe
#   is not where the risk sits. Re-aimed at the residual admissibility risk on
#   this surface: that the post-image is unsatisfiable / degenerate at the
#   interesting point. Discharges an in-region assert pinning the grounded
#   boundary (the FIRST column) at a single-column and a multi-column row.
# ADDED (weak-reads-wrong-column): a near-miss that reads a real column of the
#   present row but the LAST instead of the FIRST — it agrees with gold on every
#   single-column row, so it exercises the row-CONTENT sub-domain (≥2 columns)
#   that the constant-boundary rival's singleton witness never reaches. Without
#   it the C2 clause would be attacked only at single-column rows, leaving the
#   "which column" dependence of `row.head!` untested.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
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
#
# BINDER / CLAUSE COVERAGE. The two independent top-level clauses are each
#   attacked: C1 (`fetched = none → out = none`) by weak-prepatch-unconditional-
#   read at `none`; C2 (`∀ row, fetched = some row → out = some row.head!`) by
#   weak-present-wrong-key (constant boundary), weak-reads-wrong-column (wrong
#   column), and weak-flip-doubly-wrong (no boundary on present). The sole input
#   binder `fetched` is varied across FOUR distinct witness points — `none`,
#   `some [5]`, `some [5, 9]`, `some [7]` (pts=4) — spanning the absent case, two
#   distinct single-column present rows, and a two-column present row, so the
#   post-image's dependence on presence, on the row's content, and on WHICH
#   column is read is each demonstrated at an input no other rival shares.
#
# AXIOM_TESTS: empty in the sibling and here — no callee is axiomatized (the
#   lookup result is the modeled input, the follow-up delete is observed through
#   its boundary). The axiom lane is G-AX's job and this gate ignores it anyway.
AXIOM_TESTS = []

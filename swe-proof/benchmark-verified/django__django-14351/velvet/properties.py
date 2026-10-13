"""properties.py — G-PBT falsification battery for django__django-14351 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: it must ELABORATE against the rival and FAIL against the frozen
solution).

DEFENDED SURFACE (one contracted method over one mut carrier + read-only inputs):

  inGroupByCols (mut rhsSelect) (rhsIsExpr) (rhsHasSelectFields)
                (lhsCols) (rhsCols) (pkCol) return (out : List Col)
    ensures rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields
                                      rhsSelectOld pkCol            -- C_SELECT
    ensures out       = contributedCols rhsIsExpr lhsCols rhsCols   -- C_OUT

  A membership test against a right operand contributes grouping columns AND, as
  a side effect, reconciles the right operand's output-column list. Two entirely
  independent clauses:

    C_SELECT (the mut-carrier post-state): the right operand's output-column list
      is clamped to the single key column EXACTLY when the right operand is a
      column-contributing sub-result that names no explicit output columns
      (``rhsIsExpr ∧ ¬rhsHasSelectFields``); in every other configuration it is
      PRESERVED at its entry value ``rhsSelectOld``. This is a directive-5
      mut-frame property — the changed frame pinned to its exact post-state, the
      preserved frame pinned against the entry value — and it is the load-bearing
      behaviour the failing test observes (an un-clamped sub-result renders more
      than one column and the subquery is rejected).

    C_OUT (the return value): the contributed grouping columns are the left
      operand's columns always, extended by the right operand's columns exactly
      when the right operand is a column-contributing sub-result; a direct value
      right operand contributes nothing. This is independent of the clamp.

  BINDERS. C_SELECT reads ``rhsIsExpr``, ``rhsHasSelectFields``, ``rhsSelectOld``
  (the entry value of the mut carrier) and ``pkCol``. C_OUT reads ``rhsIsExpr``,
  ``lhsCols`` and ``rhsCols``. ``clampedSelect`` / ``contributedCols`` /
  ``mustClamp`` are total, fully-unfolded ``def``s of the method's own arguments
  (``pure`` region); the ``axioms`` region declares NO ``axiom`` — there is no
  opaque answer key to echo, and no ``require`` clause, so every configuration is
  admissible and refutable at a concrete point.

CARRIER — witness form. The spec is a ``method`` CONTRACT, not a bare predicate,
so each reject witness reaches the post-image through Velvet's own tester
machinery: ``extract_program_for`` → ``inGroupByColsExec``, then
``prove_precondition_decidable_for`` / ``prove_postcondition_decidable_for`` /
``derive_tester_for`` synthesize the ``Decidable`` instances and the boolean
tester ``inGroupByColsTester : List Col → Bool → Bool → List Col → List Col →
Col → Bool``. ``inGroupByColsTester args = false`` says the extracted program's
``(rhsSelect, out)`` violates the method's postcondition at that concrete input.
Every carrier is fully transparent (``List Col`` with ``++``; ``Col`` derives
``DecidableEq``), so ``decide`` reduces the tester fully and no assumption
(axiom/sorry/native_decide) is needed. Each witness is checked in a file whose
``prove_correct`` block is stripped (no tactic script can mask the verdict) and
binds nothing at its ``example`` head (concrete literal inputs), so the
consistency probe is trivially satisfied.

ADVERSARIAL READ of the nagini classes:

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries two such rivals (a write to the read-only ``lhs_cols`` list, and a
    write to the read-only ``rhs.default_cols`` facet), each rejected for
    INSUFFICIENT (fractional) PERMISSION. Velvet is referentially transparent:
    there is no heap, no aliasing, and no fractional-permission system. ``lhsCols``
    / ``rhsCols`` / ``pkCol`` are plain (non-``mut``) free inputs — a functional
    impl cannot write them at all — and the ONE mutable facet, the select-clause
    list, is the legitimate ``mut`` carrier ``rhsSelect`` (it is SUPPOSED to be
    written on the clamp branch), so there is no read-only facet to overwrite and
    no substitute probe to fabricate. IMPORTANTLY the behavioural content those
    permission rivals guard — that the mutable carrier is written ONLY where the
    clamp applies and PRESERVED everywhere else — is not lost: it is pinned by the
    preserve arm of C_SELECT and attacked directly by ``weak-clamp-explicit`` and
    ``weak-clamp-literal`` below. Reported as an omission of the permission
    mechanism, not faked.

  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
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

  * UNGROUNDED-ORACLE ECHO — N/A. ``clampedSelect`` / ``contributedCols`` are
    total, fully-unfolded functions of the method's own arguments (concrete
    ``def``s in the ``pure`` region; the ``axioms`` region declares NO ``axiom``).
    There is no opaque answer key a wrong impl could echo. The nagini
    "ungrounded-oracle echo" rival (fabricate the pk contribution WITHOUT running
    the normalisation) ports as ``weak-no-clamp-fieldless``: an impl that gets the
    contributed columns right but omits the clamp side effect on the field-less
    sub-domain violates C_SELECT.

  * PARTIAL-DOMAIN / VALUE — the heart of this surface. A rival can be right on
    one branch of ``rhsIsExpr`` / ``rhsHasSelectFields`` and wrong on another
    (clamp omitted where it applies, clamp fired where the frame must be
    preserved, the wrong column list contributed). All five reject rivals are of
    this kind, split across the two independent clauses.

WITNESS PLACEMENT / BINDER COVERAGE. Both clauses are DEFENDED (structurally
different correct reshapes verify) and ATTACKED (>=1 reject each: C_SELECT by
R1/R2/R3, C_OUT by R4/R5). The five reject witnesses sit at five DISTINCT input
points and move every input binder off any fixed value:
  * ``rhsIsExpr`` ∈ {true (R1,R2,R5), false (R3,R4)} — both.
  * ``rhsHasSelectFields`` ∈ {false (R1,R3,R4), true (R2,R5)} — both.
  * ``rhsSelectOld`` ∈ {[⟨1⟩,⟨2⟩], [⟨3⟩], [⟨4⟩,⟨5⟩]} — varied (load-bearing for
    the C_SELECT preserve arm: R2/R3 discriminate only because rhsSelectOld ≠
    [pkCol] at their points).
  * ``lhsCols`` ∈ {[⟨9⟩], [⟨5⟩], [⟨2⟩], [⟨7⟩,⟨9⟩]} — varied.
  * ``rhsCols`` ∈ {[⟨8⟩], [⟨6⟩], [⟨1⟩], [⟨4⟩]} — varied.
  * ``pkCol``   ∈ {⟨0⟩, ⟨7⟩} — varied (load-bearing for the C_SELECT clamp arm:
    R1 discriminates only because gold's [pkCol] ≠ the un-clamped rhsSelectOld).
Confirmed empirically with scripts/lean_verify.sh: every positive verifies, the
admissibility assert is live (a false claim leaves an unsolved goal), and every
reject witness ELABORATES against its rival and FAILS against the frozen solution
(pts = 5).

AXIOM lane: DROPPED. The nagini sibling carries three AXIOM_TESTS over the
unchanged Django callees; the axiom lane is G-AX's job and this gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` (the delegated
column observations are FREE inputs ``lhsCols`` / ``rhsCols``; meta.json
axioms == []), so there is nothing here for this spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "django__django-14351"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. The impl block is the whole `-- impl-start` / `-- impl-end` region
# (elided from the spec view, so a _swap here keeps `same_spec`); the proof block
# is the `prove_correct` tactic body (also elided). Both are asserted unique in
# the file by _swap.
# ---------------------------------------------------------------------------
_IMPL_GOLD = (
    "    -- impl-start\n"
    "    -- Start the contributed grouping columns from the left operand's columns.\n"
    "    let mut cols : List Col := lhsCols\n"
    "    -- Only when the right operand is itself a column-contributing sub-result do\n"
    "    -- we reconcile its output shape and fold in its columns.\n"
    "    if rhsIsExpr then\n"
    "      -- A sub-result that names no explicit output columns would expose every\n"
    "      -- default output column; clamp its output list to the single key column so\n"
    "      -- it is a well-formed single-column operand. A sub-result that already\n"
    "      -- names its output columns is left untouched.\n"
    "      if !rhsHasSelectFields then\n"
    "        rhsSelect := [pkCol]\n"
    "      else\n"
    "        rhsSelect := rhsSelect\n"
    "      cols := cols ++ rhsCols\n"
    "    else\n"
    "      rhsSelect := rhsSelect\n"
    "    return cols\n"
    "    -- impl-end"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: inGroupByCols body not verbatim"

_PROOF_GOLD = (
    "prove_correct inGroupByCols by\n"
    "  loom_solve\n"
    "  all_goals simp_all [clampedSelect, mustClamp, contributedCols]"
)
assert _PROOF_GOLD in _BASE, "proof anchor drift"


def _impl(body):
    """Wrap a bare impl body (no markers) in the frozen impl-region markers."""
    return "    -- impl-start\n" + body + "\n    -- impl-end"


# ---- witness preamble. `inGroupByColsTester args = false` says the extracted
# ---- program's (rhsSelect, out) violates the method postcondition at that
# ---- concrete input. Checked in a `prove_correct`-stripped file; every argument
# ---- is a concrete literal so `decide` reduces the tester fully. `Col` literals
# ---- are anonymous-constructor `⟨n⟩` (the single `ref : Nat` field). ----
_TESTER = (
    "extract_program_for inGroupByCols\n"
    "prove_precondition_decidable_for inGroupByCols\n"
    "prove_postcondition_decidable_for inGroupByCols\n"
    "derive_tester_for inGroupByCols\n\n"
)


def _witness(args):
    return _TESTER + f"example : inGroupByColsTester {args} = false := by decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. Each keeps the method's `ensures` and the frozen
    # `prove_correct` obligation verbatim; only the impl region changes (the
    # frozen `all_goals simp_all [...]` closes the reshaped bodies unchanged). If
    # a faithful correct impl cannot verify, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-let-bind-clamp",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the reconciled select-clause into a local via a
        # `let … if … then … else …` ladder, then assign it once — instead of the
        # nested imperative `if`. Same (rhsSelect, out) on every configuration.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      let newSelect := if !rhsHasSelectFields then [pkCol] else rhsSelect\n"
                "      rhsSelect := newSelect\n"
                "      cols := cols ++ rhsCols\n"
                "    else\n"
                "      rhsSelect := rhsSelect\n"
                "    return cols")),
        "rationale": "computing the reconciled select list into a local via a "
                     "`let`-ladder before assigning it yields the identical "
                     "(rhsSelect, out) as the frozen nested `if`, so C_SELECT "
                     "(rhsSelect = clampedSelect …) and C_OUT (out = "
                     "contributedCols …) both discharge under the frozen proof; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "clamp's control-flow shape.",
    },
    {
        "id": "pos-fold-before-clamp",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: fold the right operand's columns into the result BEFORE
        # reconciling the select clause (the two effects are independent, so the
        # order is immaterial). Same (rhsSelect, out) on every configuration.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      cols := cols ++ rhsCols\n"
                "      if !rhsHasSelectFields then\n"
                "        rhsSelect := [pkCol]\n"
                "      else\n"
                "        rhsSelect := rhsSelect\n"
                "    else\n"
                "      rhsSelect := rhsSelect\n"
                "    return cols")),
        "rationale": "the column fold (C_OUT) and the select-clause clamp "
                     "(C_SELECT) touch disjoint outputs, so folding rhsCols before "
                     "the clamp leaves both post-images unchanged; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on the ordering of "
                     "the two independent effects.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause here, so the usual "a normal input
    # satisfies the precondition" probe is vacuous: nothing could exclude an
    # F2P-shaped input. Re-aimed at the residual total-domain risk that the
    # post-image is UNSATISFIABLE / DEGENERATE at the interesting corners. An
    # in-region assert pins, at F2P-shaped points, BOTH clauses' non-degenerate
    # behaviour: the field-less sub-result clamps to exactly the single key column
    # (and NOT its multi-column entry value), an explicit sub-result is preserved,
    # a literal contributes only the lhs, and an expression contributes lhs+rhs.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof body is retuned only to clear the extra `decide` goal
    # (allowed — the tactic body is elided). The assert is LIVE: a false claim in
    # its place leaves an unsolved goal (verified by hand).
    # =====================================================================
    {
        "id": "admiss-clamp-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                _impl(
                    "    assert (with_name_prefix `admiss\n"
                    "      (clampedSelect true false [⟨1⟩, ⟨2⟩] ⟨0⟩ = [⟨0⟩]\n"
                    "        ∧ clampedSelect true true [⟨1⟩, ⟨2⟩] ⟨0⟩ = [⟨1⟩, ⟨2⟩]\n"
                    "        ∧ contributedCols false [⟨9⟩] [⟨8⟩] = [⟨9⟩]\n"
                    "        ∧ contributedCols true [⟨9⟩] [⟨8⟩] = [⟨9⟩, ⟨8⟩]))\n"
                    "    let mut cols : List Col := lhsCols\n"
                    "    if rhsIsExpr then\n"
                    "      if !rhsHasSelectFields then\n"
                    "        rhsSelect := [pkCol]\n"
                    "      else\n"
                    "        rhsSelect := rhsSelect\n"
                    "      cols := cols ++ rhsCols\n"
                    "    else\n"
                    "      rhsSelect := rhsSelect\n"
                    "    return cols")),
            _PROOF_GOLD,
            "prove_correct inGroupByCols by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [clampedSelect, mustClamp, contributedCols]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at concrete "
                     "F2P-shaped points: a field-less column-contributing "
                     "sub-result clamps to EXACTLY the single key column (and not "
                     "its multi-column entry value), an explicit sub-result is "
                     "preserved, a literal right operand contributes only the lhs "
                     "columns, and an expression contributes lhs followed by rhs — "
                     "the behaviours the failing test demands. The in-region assert "
                     "must discharge (else the modeled clamp/contribution is "
                     "degenerate at the interesting corner); the impl is kept "
                     "verbatim so C_SELECT and C_OUT still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-no-clamp-fieldless",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image / ungrounded-echo shape: contribute the columns correctly
        # but NEVER clamp — the field-less sub-result's select clause is left at
        # its multi-column entry value.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      rhsSelect := rhsSelect\n"
                "      cols := cols ++ rhsCols\n"
                "    else\n"
                "      rhsSelect := rhsSelect\n"
                "    return cols")),
        "refinement": "this is the pre-image behaviour the fix removes: on a "
                      "field-less column-contributing sub-result the output-column "
                      "list is left exposing every default column instead of being "
                      "clamped to the single key column. The failing test uses "
                      "exactly such a sub-result as a single-column membership "
                      "operand; a faithful counterpart that omits the clamp leaves "
                      "the sub-result rendering more than one column, so the "
                      "database rejects it (subquery must return only one column) "
                      "and the test stays RED. It does NOT resolve. (It contributes "
                      "the columns correctly, so it is a genuine partial-domain "
                      "rival — right on C_OUT, wrong on C_SELECT.)",
        "rationale": "REJECT from C_SELECT (rhsSelect = clampedSelect …): on the "
                     "clamp sub-domain (rhsIsExpr ∧ ¬rhsHasSelectFields) the "
                     "post-image demands [pkCol] and the rival leaves rhsSelectOld. "
                     "Refuted at rhsSelectOld = [⟨1⟩, ⟨2⟩], pkCol = ⟨0⟩ (the clamp "
                     "arm's exact antecedent): gold yields [⟨0⟩], the rival [⟨1⟩, "
                     "⟨2⟩]. Discriminates only because rhsSelectOld ≠ [pkCol].",
        "witness": _witness("[⟨1⟩, ⟨2⟩] true false [⟨9⟩] [⟨8⟩] ⟨0⟩"),
    },
    {
        "id": "weak-clamp-explicit",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: clamp UNCONDITIONALLY on the expression branch — so it
        # also clamps an already-explicit sub-result whose select clause must be
        # preserved. (This subsumes the nagini "unconditional-normalise" and
        # "trailing-normalise-of-explicit-rhs" rivals, which collapse to the same
        # C_SELECT-preserve violation on this carrier.)
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      rhsSelect := [pkCol]\n"
                "      cols := cols ++ rhsCols\n"
                "    else\n"
                "      rhsSelect := rhsSelect\n"
                "    return cols")),
        "refinement": "a counterpart that clamps every column-contributing "
                      "sub-result rewrites the output-column list of one that "
                      "ALREADY names explicit columns down to just the key column. "
                      "A sub-result built to project a chosen column carries that "
                      "column, not the key; the fix leaves it UNTOUCHED. Clamping "
                      "it changes the emitted SQL for every explicit-fields "
                      "membership lookup, regressing the pass-to-pass semantics — "
                      "not the real behaviour. It does NOT resolve. (It is correct "
                      "on the field-less sub-domain, so it is a genuine "
                      "partial-domain rival.)",
        "rationale": "REJECT from the PRESERVE arm of C_SELECT: when rhsIsExpr ∧ "
                     "rhsHasSelectFields the post-image demands rhsSelectOld and "
                     "the rival returns [pkCol]. Refuted at rhsSelectOld = [⟨3⟩], "
                     "pkCol = ⟨7⟩ in an explicit sub-result (rhsHasSelectFields = "
                     "true): gold preserves [⟨3⟩], the rival gives [⟨7⟩]. "
                     "Discriminates only because rhsSelectOld ≠ [pkCol]; this is "
                     "the only rival that probes pkCol = ⟨7⟩.",
        "witness": _witness("[⟨3⟩] true true [⟨5⟩] [⟨6⟩] ⟨7⟩"),
    },
    {
        "id": "weak-clamp-literal",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the literal branch: clamp the select clause even when
        # the right operand is a direct value list, corrupting its post-state.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      if !rhsHasSelectFields then\n"
                "        rhsSelect := [pkCol]\n"
                "      else\n"
                "        rhsSelect := rhsSelect\n"
                "      cols := cols ++ rhsCols\n"
                "    else\n"
                "      rhsSelect := [pkCol]\n"
                "    return cols")),
        "refinement": "when the right operand is a direct value list (not a "
                      "column-contributing sub-result) the fix never touches its "
                      "output-column list at all; clamping it there rewrites a "
                      "carrier that must be preserved and has no counterpart in the "
                      "real change. A faithful patch that mutated the literal "
                      "branch's carrier would diverge from the shipped behaviour "
                      "and regress lookups whose right operand is a plain value "
                      "list (the common case). It does NOT resolve. (Correct on "
                      "every rhsIsExpr configuration — partial-domain on the "
                      "literal branch.)",
        "rationale": "REJECT from the PRESERVE arm of C_SELECT: when ¬rhsIsExpr the "
                     "clamp never applies, so the post-image demands rhsSelectOld "
                     "and the rival returns [pkCol]. Refuted at ¬rhsIsExpr with "
                     "rhsSelectOld = [⟨4⟩, ⟨5⟩], pkCol = ⟨0⟩: gold preserves [⟨4⟩, "
                     "⟨5⟩], the rival gives [⟨0⟩]. This is the only rival that "
                     "attacks C_SELECT on the ¬rhsIsExpr sub-domain.",
        "witness": _witness("[⟨4⟩, ⟨5⟩] false false [⟨2⟩] [⟨1⟩] ⟨0⟩"),
    },
    {
        "id": "weak-drop-lhs-literal",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: drop the lhs contribution on the literal branch — return
        # the empty list instead of the left operand's columns. Attacks C_OUT.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      if !rhsHasSelectFields then\n"
                "        rhsSelect := [pkCol]\n"
                "      else\n"
                "        rhsSelect := rhsSelect\n"
                "      cols := cols ++ rhsCols\n"
                "    else\n"
                "      cols := []\n"
                "      rhsSelect := rhsSelect\n"
                "    return cols")),
        "refinement": "when the right operand is a direct value list the fix "
                      "returns the left operand's grouping columns unchanged; "
                      "dropping them emits the wrong GROUP BY for the common "
                      "literal-right-operand lookup, regressing the aggregation "
                      "tests. It does NOT resolve. (Correct on every rhsIsExpr "
                      "configuration — partial-domain on the literal branch, and "
                      "it leaves rhsSelect preserved there, so the rejection is "
                      "attributable solely to C_OUT.)",
        "rationale": "REJECT from C_OUT (out = contributedCols …): when ¬rhsIsExpr "
                     "the post-image demands lhsCols and the rival returns []. "
                     "Refuted at ¬rhsIsExpr with lhsCols = [⟨9⟩]: gold yields "
                     "[⟨9⟩], the rival []. Attacks C_OUT's lhs term on the "
                     "literal branch.",
        "witness": _witness("[⟨3⟩] false false [⟨9⟩] [⟨8⟩] ⟨0⟩"),
    },
    {
        "id": "weak-drop-rhs-fold-expr",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the expression branch: reconcile the select clause
        # correctly but NEVER fold the right operand's columns into the result.
        # Attacks C_OUT's rhs term (complementary to weak-drop-lhs-literal).
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _impl(
                "    let mut cols : List Col := lhsCols\n"
                "    if rhsIsExpr then\n"
                "      if !rhsHasSelectFields then\n"
                "        rhsSelect := [pkCol]\n"
                "      else\n"
                "        rhsSelect := rhsSelect\n"
                "    else\n"
                "      rhsSelect := rhsSelect\n"
                "    return cols")),
        "refinement": "when the right operand is a column-contributing sub-result "
                      "the fix contributes the left operand's columns followed by "
                      "the sub-result's own columns; omitting the sub-result's "
                      "contribution emits a GROUP BY missing those columns, "
                      "changing the aggregation for every sub-result-right-operand "
                      "lookup. It does NOT resolve. (It reconciles the select "
                      "clause correctly on both sub-domains, so the rejection is "
                      "attributable solely to C_OUT.)",
        "rationale": "REJECT from C_OUT (out = contributedCols …): when rhsIsExpr "
                     "the post-image demands lhsCols ++ rhsCols and the rival "
                     "returns lhsCols only. Refuted at rhsIsExpr with lhsCols = "
                     "[⟨7⟩, ⟨9⟩], rhsCols = [⟨4⟩]: gold yields [⟨7⟩, ⟨9⟩, ⟨4⟩], "
                     "the rival [⟨7⟩, ⟨9⟩]. Attacks C_OUT's rhs term on the "
                     "expression branch — the complement of weak-drop-lhs-literal.",
        "witness": _witness("[⟨3⟩] true true [⟨7⟩, ⟨9⟩] [⟨4⟩] ⟨0⟩"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals) plus 3 AXIOM_TESTS, contracting
# ONE function `membership_group_by_cols` whose postconditions split into P1-P6
# over the returned list AND the rhs post-state facets. This bundle models the
# SAME purely-functional core as one `method inGroupByCols` with two independent
# clauses: C_SELECT (rhsSelect = clampedSelect …, the mut-carrier post-state,
# carrying the nagini P3/P4/P6 clamp-and-frame content) and C_OUT (out =
# contributedCols …, the returned grouping columns, carrying P1/P2/P3/P5).
#
#   sibling case (nagini)                        -> here
#   -----------------------------------------------------------------------
#   pos-control-local-reshape                    -> pos-let-bind-clamp        PORTED
#                                                   + pos-fold-before-clamp    ADDED
#   admiss-fieldless-shaped                      -> admiss-clamp-nondegenerate RE-AIMED
#   frame-mut-lhs-cols                           -> (none)                     VACUOUS
#   frame-mut-rhs-default-cols                   -> (none)                     VACUOUS
#   echo-fabricate-pk-no-normalise               -> weak-no-clamp-fieldless    PORTED
#   uncond-normalise-explicit-rhs                -> weak-clamp-explicit         PORTED
#   partial-domain-drop-lhs-literal              -> weak-drop-lhs-literal       PORTED
#   gratuitous-normalise-explicit-after-result   -> weak-clamp-explicit         COLLAPSED
#   gratuitous-normalise-literal-rhs             -> weak-clamp-literal          PORTED
#   (no sibling counterpart)                     -> weak-drop-rhs-fold-expr     ADDED
#
# 5 ported, 1 re-aimed, 1 collapsed, 2 vacuous; 1 positive + 1 uniqueness ADDED.
#
# RE-AIMED (admiss-fieldless-shaped -> admiss-clamp-nondegenerate): the sibling
#   asserts the read-only-facet half-permissions admit a normal F2P-shaped input
#   (a Requires-domain probe). This backend has no `require` clause, so nothing
#   could exclude an F2P-shaped input — that probe is vacuous. Re-aimed at the
#   residual total-domain risk that the post-image is unsatisfiable / degenerate
#   at the interesting corners: a live in-region assert pins the clamp arm, the
#   preserve arm, and both C_OUT arms at concrete F2P-shaped points; the impl and
#   obligation are kept verbatim.
#
# VACUOUS (frame-mut-lhs-cols, frame-mut-rhs-default-cols): both sibling rivals
#   WRITE a read-only input held at a fractional (Acc(.,1/2)) permission and are
#   rejected for INSUFFICIENT PERMISSION. Velvet is referentially transparent —
#   no heap, no aliasing, no fractional-permission system. lhsCols / rhsCols /
#   pkCol are plain (non-mut) free inputs a functional impl cannot write, and the
#   only mutable facet (the select-clause list) is the legitimate `mut` carrier
#   rhsSelect that the clamp is SUPPOSED to write; so there is no read-only facet
#   to overwrite and no substitute probe. The behavioural content those rivals
#   guard — write the carrier ONLY where the clamp applies, preserve it elsewhere
#   — is not lost: it is the preserve arm of C_SELECT, attacked by
#   weak-clamp-explicit and weak-clamp-literal. No substitute fabricated.
#
# COLLAPSED (gratuitous-normalise-explicit-after-result -> weak-clamp-explicit):
#   the sibling case builds the result correctly, then AFTERWARDS clamps an
#   already-explicit rhs (a G-PANEL-1 trailing-side-effect attack). On this
#   carrier its only observable is rhsSelect = [pkCol] where the preserve arm of
#   C_SELECT demands rhsSelectOld on the (rhsIsExpr ∧ rhsHasSelectFields) point —
#   byte-for-byte the same violation, at the same discriminating input, as the
#   unconditional-normalise rival weak-clamp-explicit. Merging them (rather than
#   shipping two rivals refuted at the same point for the same reason) keeps the
#   battery honest; no coverage is lost.
#
# ADDED (2): pos-fold-before-clamp (a second cheapest-reshape positive, over the
#   ORDER of the two independent effects, so both clauses are defended by a
#   structurally-different correct impl) and weak-drop-rhs-fold-expr (the
#   complement of weak-drop-lhs-literal: it attacks C_OUT's rhs-contribution term
#   on the expression branch, which no ported rival reaches — its faithful
#   counterpart emits a GROUP BY missing the sub-result's columns and does NOT
#   resolve).
#
# COVERAGE. Independent clauses: C_SELECT attacked by weak-no-clamp-fieldless
#   (clamp arm), weak-clamp-explicit (preserve arm, expr branch), weak-clamp-
#   literal (preserve arm, literal branch); C_OUT attacked by weak-drop-lhs-
#   literal (lhs term) and weak-drop-rhs-fold-expr (rhs term). Both clauses
#   defended by pos-let-bind-clamp, pos-fold-before-clamp, admiss-clamp-
#   nondegenerate. Binders moved by the reject witnesses: rhsIsExpr ∈ {true,
#   false}; rhsHasSelectFields ∈ {false, true}; rhsSelectOld ∈ {[⟨1⟩,⟨2⟩], [⟨3⟩],
#   [⟨4⟩,⟨5⟩]}; lhsCols ∈ {[⟨9⟩], [⟨5⟩], [⟨2⟩], [⟨7⟩,⟨9⟩]}; rhsCols ∈ {[⟨8⟩],
#   [⟨6⟩], [⟨1⟩], [⟨4⟩]}; pkCol ∈ {⟨0⟩, ⟨7⟩}. Five distinct input points, pts = 5.
#
# DIVERGENCE: N/A. The sibling carries no diverge-*/nonterm-*/weak-diverge case,
#   and this is a `total` bundle (Solution.lean line 4) which rejects a diverging
#   impl anyway — the `partial` known-hole disposition does not apply.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the delegated column observations lhsCols/rhsCols
#   are FREE inputs; meta.json axioms == []), so there is nothing here to probe.
AXIOM_TESTS = []

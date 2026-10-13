"""properties.py — G-PBT falsification battery for django__django-11138 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — which the consumer spec view elides,
so ``markers.same_spec`` holds and the ``prove_correct buildTzAdjustedExpr``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a string carrier, ``List Char`` of
code points):

  buildTzAdjustedExpr
    (active : Bool) (expr queryZone storedZone : List Char) return (out : List Char)
    ensures out = tzAdjustedExpr active expr queryZone storedZone

``tzAdjustedExpr`` is a fully TRANSPARENT ``def`` on the input carrier: a guarded
concatenation

    if active ∧ storedZone ≠ queryZone then
      "CONVERT_TZ(" ++ expr ++ ", '" ++ storedZone ++ "', '" ++ queryZone ++ "')"
    else
      expr

It is NOT an opaque answer key — it is a computable function of the four inputs
(directive 8: the post-image is grounded in the inputs, not an axiomatized
oracle; the ``axioms`` region is empty). So a wrong impl cannot ECHO an oracle to
pass; it must reproduce the guarded string exactly. Every clause below is
decidable at concrete literal inputs, so the reject lane is fully expressible
with ``decide``-able witnesses (no opaque term forces conditioning on the
carrier).

CLAUSE / BINDER STRUCTURE (read before judging coverage). The single
postcondition ``out = tzAdjustedExpr ...`` bundles several independent sub-facts,
each attacked by at least one reject rival:
  * the WRAP GUARD is a conjunction of two independent conditions —
      (a) ``active`` (the time-zone-support flag), and
      (b) ``storedZone ≠ queryZone`` (the two zones actually differ);
    a rival that drops either conjunct wraps on a sub-domain where gold returns
    ``expr`` unchanged;
  * the WRAPPED STRING must (c) use ``storedZone`` as the conversion source
    (NOT a hardcoded ``"UTC"``), (d) use ``queryZone`` as the target, in that
    ORDER, and (e) embed the original ``expr``; and it must (f) place them inside
    the exact constant fragments the emitted expression requires — getting every
    slot right but the delimiters wrong is still wrong (weak-unquoted-zones);
  * the ELSE branch returns ``expr`` verbatim (identity when no conversion is
    needed).

The four INPUT BINDERS are each varied and each abused by a rival's witness:
``active`` — held ``false`` by rival-drop-active (its whole point) and ``true``
by the rest; ``storedZone`` — the load-bearing source, wrong-sourced by
rival-utc / rival-prepatch and swapped by rival-swap; ``queryZone`` — swapped
into the source slot by rival-swap and driven to its EMPTY boundary by
rival-empty-zone-skip; ``expr`` — dropped from the wrap by rival-drop-expr and
driven to its EMPTY boundary by rival-empty-expr-skip. Across the ten reject
witnesses the concrete inputs are all distinct (see the accounting footer), so no
binder is pinned at one value, and both ``List Char`` binders that can be empty
are probed at that boundary.

The ADMISSIBILITY lane is present (``admiss-f2p-nondegenerate``). The obligation
carries no ``require``, but that is exactly why the lane is needed rather than a
reason to drop it: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
obligation being UNSATISFIABLE or DEGENERATE at an F2P-shaped input, which that
case discharges by evaluation before closing the frozen obligation verbatim.

ADVERSARIAL READ of the nagini classes on this carrier (the nagini sibling
models a DIFFERENT, narrower-mapped function — see the accounting footer):
  * FRAME-MUTATION — VACUOUS here. Lean/Velvet are referentially transparent:
    every input is an immutable value, no binder is ``mut``, there is no heap and
    no fractional permission. There is no read-only field to overwrite and no
    substitute probe to build. Not fabricated (porting map: this class is vacuous
    here); the nagini docstring itself already notes the inputs are immutable
    scalars with no ``Acc(x,1/2)`` carrier.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent ``def`` of the
    inputs, not an axiomatized oracle; the ``axioms`` region is empty.
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

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the postcondition through Velvet's own tester machinery.
``buildTzAdjustedExprTester active expr queryZone storedZone = false`` says the
extracted program's result violates ``out = tzAdjustedExpr ...`` at that concrete
input. It is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict. Both the rival (straight-line ``if``)
and the frozen solution have extracted programs that kernel-reduce under
``decide``; the discriminator is that at the chosen input the RIVAL's string
differs from ``tzAdjustedExpr`` (so ``… = false`` holds and the witness
elaborates) while GOLD's equals it (so ``… = false`` is provably FALSE and the
witness fails). Every reject witness below was run against both the rival (exit
0) and the frozen solution (exit 1) with two real builds — and each was then
FORGERY-TESTED with two more: flipping the asserted claim to ``… = true``
inverts both exit codes, which is what shows gold's failure carries information
about the CLAIM rather than being an artifact of the file or the tactic.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the result is a
pure string computation from the four inputs, an A-reference band with no
consumed contract — mapping.md §3.1). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11138"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region (the guarded concatenation) and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). Anchoring on the
# ---- whole block keeps the surgery inside the elided region, so `same_spec`
# ---- holds and the `prove_correct` statement is byte-identical. ----
_IMPL = (
    "    let out : List Char :=\n"
    "      if active ∧ storedZone ≠ queryZone then\n"
    "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ storedZone\n"
    "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
    "      else\n"
    "        expr\n"
    "    return out"
)

# Sanity: the gold impl block must be present exactly once in the frozen base.
assert _BASE.count(_IMPL) == 1, "drift: _IMPL not byte-identical to Solution.lean impl region"


_PROOF = "prove_correct buildTzAdjustedExpr by\n  loom_solve\n"
assert _BASE.count(_PROOF) == 1, "drift: _PROOF not byte-identical to Solution.lean"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_assert(assertion: str) -> str:
    """Gold impl kept VERBATIM, an in-region `assert` prepended, proof retuned.

    Used only by the admissibility case. The assert sits inside the elided
    `impl` region (so `same_spec` holds and the `prove_correct` header survives),
    and the proof gains `all_goals decide` purely to clear the extra assert goal
    — the tactic body is elided from the spec view, and the frozen `loom_solve`
    still discharges the `ensures` itself because the impl is untouched.
    """
    return _swap(_swap(_BASE, _IMPL, assertion + _IMPL), _PROOF,
                 "prove_correct buildTzAdjustedExpr by\n"
                 "  loom_solve\n"
                 "  all_goals decide\n")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `buildTzAdjustedExprTester active expr queryZone storedZone =
# ---- false` says the extracted program's result violates the postcondition at
# ---- that concrete input. There are no `require` clauses, so no input is
# ---- vacuously excluded. All literals are small, so `decide` reduces. ----
_TESTER = (
    "extract_program_for buildTzAdjustedExpr\n"
    "prove_precondition_decidable_for buildTzAdjustedExpr\n"
    "prove_postcondition_decidable_for buildTzAdjustedExpr\n"
    "derive_tester_for buildTzAdjustedExpr\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # `ensures out = tzAdjustedExpr ...` obligation and only reshapes the
    # executable surface; the frozen `prove_correct ... by loom_solve` closes
    # both unchanged (the `@[grind] tzAdjustedExpr_def` unfold lemma discharges
    # the reshaped guard). Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest impl: return the grounded pure model directly.
        # This is the "is the grounded post-image correct" positive control —
        # the post-image is GROUNDED (a transparent def), so returning it is
        # CORRECT and MUST verify; if it failed, the spec would be too strong.
        "module": _with_impl(
            "    let out : List Char := tzAdjustedExpr active expr queryZone storedZone\n"
            "    return out"),
        "rationale": "The grounded pure model is the postcondition target; "
                     "returning it directly is the cheapest CORRECT impl and MUST "
                     "verify (positive control for the grounded-post-image lane; "
                     "if it failed the spec would be unprovable / too strong). "
                     "Sibling: pos-cheapest. Frozen loom_solve proof unchanged.",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but equivalent: negate the guard (De Morgan) and
        # flip the branches — return `expr` on the no-conversion side, wrap on the
        # other. Same value at every input; a fresh branch shape.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if ¬ active ∨ storedZone = queryZone then\n"
            "        expr\n"
            "      else\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ storedZone\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "    return out"),
        "rationale": "Structurally different CORRECT reshape: the guard is negated "
                     "by De Morgan (¬active ∨ storedZone = queryZone) and the "
                     "branches flipped, returning `expr` on the no-conversion arm. "
                     "Same value at every input, so `out = tzAdjustedExpr ...` "
                     "holds. Must verify (else SPEC-TOO-STRONG). Sibling: "
                     "pos-reorder. Frozen loom_solve proof unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED BY AUDIT. The obligation carries no `require`, so the
    # sibling's "a normal input satisfies the precondition" probe has no clause to
    # aim at. That is NOT a reason to drop the lane: on a total carrier the
    # analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE or
    # DEGENERATE at exactly an F2P-shaped input — a post-image no impl can meet,
    # or one that collapses to a constant, reads like a spec every impl meets. So
    # this case discharges, BY EVALUATION at a concrete F2P-shaped point (a quoted
    # column reference for `expr`, two region/city zone names), three facts about
    # the post-image before closing the frozen obligation verbatim:
    #   (i)   at EQUAL zones it is satisfiable and equals `expr` unchanged;
    #   (ii)  at DISTINCT zones it is satisfiable and equals the fully assembled
    #         wrapped expression, sourcing from the stored zone; and
    #   (iii) those two are DISTINCT — so the post-image genuinely discriminates
    #         the two sub-domains the fix turns on, rather than collapsing.
    # The impl is kept BYTE-IDENTICAL to gold so the method's own `ensures` is
    # still discharged by the frozen `loom_solve`; the proof gains only
    # `all_goals decide` to clear the extra assert goal. The assert is LIVE, not
    # decoration: the audit built the same case with clause (iii) inverted
    # (claiming the distinct-zone and equal-zone images are EQUAL) and it failed,
    # `decide` refuting that proposition — so a false claim here does not pass.
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_assert(
            "    assert (with_name_prefix `admiss\n"
            "      (tzAdjustedExpr true \"`m`.`d`\".toList \"Region/One\".toList "
            "\"Region/One\".toList\n"
            "         = \"`m`.`d`\".toList ∧\n"
            "       tzAdjustedExpr true \"`m`.`d`\".toList \"Region/One\".toList "
            "\"Region/Two\".toList\n"
            "         = \"CONVERT_TZ(`m`.`d`, 'Region/Two', 'Region/One')\".toList ∧\n"
            "       tzAdjustedExpr true \"`m`.`d`\".toList \"Region/One\".toList "
            "\"Region/Two\".toList\n"
            "         ≠ tzAdjustedExpr true \"`m`.`d`\".toList \"Region/One\".toList "
            "\"Region/One\".toList))\n"),
        "rationale": "ADMISSIBILITY at an F2P-shaped input. The obligation has no "
                     "`require`, so the analogue of PRECOND-TOO-STRONG here is an "
                     "obligation UNSATISFIABLE or DEGENERATE at the interesting "
                     "point. Discharged by evaluation at a concrete F2P-shaped "
                     "input (a quoted column reference, two region/city zone "
                     "names): the post-image is satisfiable on BOTH sub-domains — "
                     "`expr` unchanged at equal zones, the fully assembled wrap "
                     "sourcing from the stored zone at distinct zones — and those "
                     "two images are DISTINCT, so the obligation neither excludes "
                     "the F2P shape nor collapses to a constant. The impl is "
                     "byte-identical to gold so the frozen `loom_solve` still "
                     "discharges the `ensures`; only the extra assert goal is "
                     "cleared. Sibling: admiss-self (re-expressed for a "
                     "precondition-free total obligation, per the sibling velvet "
                     "cells that carry an admissibility positive despite having no "
                     "`require` clause).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each keeps the frozen `prove_correct` verbatim (the
    # rejection is carried by the witness, not by whether the frozen script
    # happens to break on the reshape), and each carries a `witness` that
    # ELABORATES against the rival and FAILS against the frozen solution at a
    # concrete input, plus the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-hardcode-utc",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central bug: source zone hard-wired to "UTC" instead of the stored
        # (connection) zone, while keeping the equal-zone guard. Wrong whenever
        # the stored zone is not UTC.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active ∧ storedZone ≠ queryZone then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ \"UTC\".toList\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "This is the exact pre-patch behaviour: the conversion "
                      "source is forced to a fixed reference zone regardless of the "
                      "stored (connection) zone. Its faithful real patch is the "
                      "UNPATCHED source line, which the F2P test FAILS "
                      "whenever the stored "
                      "zone is not the fixed reference zone (the issue's Paris→Paris "
                      "case): the date lookup reads the wrong instant. A verifying "
                      "rival here would be a true verify-does-not-resolve break.",
        "rationale": "REJECT from `out = tzAdjustedExpr ...` clause (c): the "
                     "wrapped string must source from `storedZone`, not a hardcoded "
                     "literal. Refuted at active=true, expr=\"D\", "
                     "queryZone=\"Paris\", storedZone=\"Kolkata\": gold sources from "
                     "\"Kolkata\", the rival from \"UTC\". Sibling: weak-prepatch / "
                     "the sibling's dropped source-offset term.",
        "witness": _witness(
            'buildTzAdjustedExprTester true "D".toList "Paris".toList "Kolkata".toList'),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The FULL pre-patch skeleton: source hard-wired to "UTC" AND the
        # equal-zone guard dropped (wrap whenever support is active). Combines
        # clause (b) and clause (c) failures.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ \"UTC\".toList\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "The complete pre-patch shape: the source zone is forced to "
                      "the fixed reference zone AND the conversion is emitted "
                      "whenever support is active (no skip when the two zones "
                      "coincide). Its faithful real patch is the unpatched code, "
                      "which the F2P FAILS on both the distinct-zone case (wrong "
                      "source) and the equal-zone case (a needless conversion "
                      "against an unpopulated zone table). It does NOT resolve.",
        "rationale": "REJECT from clauses (b)+(c): produces "
                     "CONVERT_TZ(expr, 'UTC', queryZone) whenever active, wrong "
                     "source and wrong on equal zones. Refuted at active=true, "
                     "expr=\"X\", queryZone=\"Bangkok\", storedZone=\"Nairobi\": "
                     "gold sources from \"Nairobi\", the rival from \"UTC\". "
                     "Sibling: weak-prepatch.",
        "witness": _witness(
            'buildTzAdjustedExprTester true "X".toList "Bangkok".toList "Nairobi".toList'),
    },
    {
        "id": "weak-drop-eqguard",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: correct source zone, but drop ONLY the `storedZone ≠
        # queryZone` conjunct — so it wraps even when the two zones coincide.
        # Correct on the distinct-zone domain; wrong exactly on the equal-zone
        # sub-domain (issue's tz1==tz2 case). Witnessed at its own distinguishing
        # point (equal zones), which no other rival probes.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ storedZone\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Drops only the equal-zone skip while keeping the correct "
                      "source. Its faithful real patch omits the zone-inequality "
                      "guard so a conversion is emitted even when the stored and query "
                      "zones are identical — precisely the case the issue says must "
                      "work WITHOUT a zone table. The F2P's equal-zone branch "
                      "(connection zone == current zone, no conversion expected) "
                      "then reads through a conversion against an unpopulated table "
                      "and FAILS. It does NOT resolve.",
        "rationale": "Partial-domain REJECT from guard clause (b): correct on "
                     "distinct zones, but wraps on the equal-zone sub-domain where "
                     "gold returns `expr`. A spec that forgot the zone-inequality "
                     "guard would MISS this => SPEC-TOO-WEAK. Refuted at "
                     "active=true, expr=\"F\", queryZone=\"UTC\", storedZone=\"UTC\" "
                     "(equal zones): gold returns \"F\", the rival wraps it. A "
                     "near-miss no distinct-zone rival subsumes; witnessed at its "
                     "own equal-zone point. Sibling: weak-partial-equalzone.",
        "witness": _witness(
            'buildTzAdjustedExprTester true "F".toList "UTC".toList "UTC".toList'),
    },
    {
        "id": "weak-drop-active",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the OTHER guard conjunct: ignore the `active` flag, wrapping
        # whenever the zones differ even with time-zone support OFF. Correct when
        # active; wrong on the (¬active, distinct-zone) sub-domain.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if storedZone ≠ queryZone then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ storedZone\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Drops the support-active conjunct so the conversion is "
                      "emitted even when time-zone support is off. Its faithful "
                      "real patch wraps the field expression while support is "
                      "disabled — the legacy/naive path that must read the stored "
                      "value UNCONVERTED. It corrupts the support-off reads the "
                      "PASS_TO_PASS legacy tests cover and does NOT resolve.",
        "rationale": "Partial-domain REJECT from guard clause (a): correct when "
                     "active, but wraps on the (¬active, distinct-zone) sub-domain "
                     "where gold returns `expr`. Refuted at active=false, "
                     "expr=\"G\", queryZone=\"B\", storedZone=\"A\": gold returns "
                     "\"G\", the rival wraps it. This is the ONLY rival holding "
                     "active=false, so it is what varies the `active` binder. "
                     "Sibling: weak-partial-notarget (a precond-admitted "
                     "sub-domain the gold leaves unconverted).",
        "witness": _witness(
            'buildTzAdjustedExprTester false "G".toList "B".toList "A".toList'),
    },
    {
        "id": "weak-swap-zones",
        "kind": "uniqueness",
        "expect": "reject",
        # Convert in the WRONG DIRECTION: put queryZone in the source slot and
        # storedZone in the target slot. Correct only when the two coincide
        # (then the guard is false anyway). Attacks the source/target ORDER,
        # clauses (c)+(d).
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active ∧ storedZone ≠ queryZone then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ queryZone\n"
            "          ++ \"', '\".toList ++ storedZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Reverses the conversion: it re-interprets FROM the query "
                      "zone INTO the stored zone. Its faithful real patch swaps the "
                      "two zone arguments — it does not produce the "
                      "stored→query value the date lookup expects, so the F2P reads "
                      "the wrong instant and it does NOT resolve.",
        "rationale": "REJECT from source/target ORDER clauses (c)+(d): produces "
                     "CONVERT_TZ(expr, queryZone, storedZone), equal to gold only "
                     "when the two zones coincide (guard false). Refuted at "
                     "active=true, expr=\"H\", queryZone=\"q\", storedZone=\"s\": "
                     "gold emits source 's' target 'q', the rival the reverse. "
                     "Sibling: weak-sign (the directional/sign-flip attack).",
        "witness": _witness(
            'buildTzAdjustedExprTester true "H".toList "q".toList "s".toList'),
    },
    {
        "id": "weak-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheapest wrong impl: never wrap, return `expr` unconditionally. Correct
        # on the no-conversion sub-domains, wrong on the main convert domain.
        "module": _with_impl(
            "    let out : List Char := expr\n"
            "    return out"),
        "refinement": "Pure identity: the conversion is never applied. Its "
                      "faithful real patch removes the wrapping entirely, leaving "
                      "the stored value read in the stored zone. A date lookup in a "
                      "distinct query zone then reads the wrong date and the F2P "
                      "FAILS to resolve.",
        "rationale": "Cheapest wrong impl: REJECT from the wrap clause — returns "
                     "`expr` even when active and the zones differ, where gold "
                     "wraps. Refuted at active=true, expr=\"I\", queryZone=\"tgt\", "
                     "storedZone=\"src\": gold wraps, the rival returns \"I\". "
                     "Sibling: weak-zero.",
        "witness": _witness(
            'buildTzAdjustedExprTester true "I".toList "tgt".toList "src".toList'),
    },
    {
        "id": "weak-drop-expr",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the field expression from the wrapped string. Attacks clause (e):
        # the wrap must embed `expr`. This is the rival that ABUSES the `expr`
        # binder (every other rival holds it inert inside the wrap or returns it).
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active ∧ storedZone ≠ queryZone then\n"
            "        \"CONVERT_TZ(\".toList ++ \", '\".toList ++ storedZone\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Drops the field expression from the CONVERT_TZ wrapper. Its "
                      "faithful real patch builds a conversion around nothing — the "
                      "generated SQL references no column, so the query is "
                      "malformed and every date lookup FAILS. It does NOT resolve.",
        "rationale": "REJECT from clause (e): the wrapped string must embed the "
                     "input `expr`. Refuted at active=true, expr=\"J\", "
                     "queryZone=\"B\", storedZone=\"A\": gold's wrap contains \"J\", "
                     "the rival's does not. This is the rival that VARIES/abuses the "
                     "`expr` binder (no nagini sibling — the nagini carrier is a "
                     "scalar wall-clock with no field-expression argument; ADDED).",
        "witness": _witness(
            'buildTzAdjustedExprTester true "J".toList "B".toList "A".toList'),
    },
    {
        "id": "weak-unquoted-zones",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every pre-existing rival abuses a zone SLOT (which zone
        # goes where) or the guard; none attacks the LITERAL FRAGMENTS that
        # delimit the emitted expression. This rival puts both zone names in the
        # right slots, in the right order, with the right guard and the right
        # `expr` — and only drops the quoting around the two zone names. It is
        # the near-miss the source/target/order rivals leave unprobed: the
        # emitted text is well-formed-looking but is not the required string.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active ∧ storedZone ≠ queryZone then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", \".toList ++ storedZone\n"
            "          ++ \", \".toList ++ queryZone ++ \")\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Emits the conversion with the two zone names UNQUOTED. Its "
                      "faithful real patch interpolates the zone names without the "
                      "surrounding quotes, so each is parsed as an identifier rather "
                      "than a zone-name string literal: the generated statement is "
                      "rejected by the database instead of returning the converted "
                      "value, and every date lookup on the converting path errors "
                      "out. It does NOT resolve.",
        "rationale": "REJECT from the literal-fragment half of clauses (c)+(d): the "
                     "wrap must place each zone name inside the quoting the emitted "
                     "expression requires, not merely pass the two names in the "
                     "correct order. Refuted at active=true, expr=\"K\", "
                     "queryZone=\"Lima\", storedZone=\"Oslo\": gold quotes both zone "
                     "names, the rival neither. This is the only rival attacking the "
                     "constant fragments rather than which input lands in which slot "
                     "(no nagini sibling — the sibling's integer carrier has no "
                     "string delimiters to drop; ADDED by audit).",
        "witness": _witness(
            'buildTzAdjustedExprTester true "K".toList "Lima".toList "Oslo".toList'),
    },
    {
        "id": "weak-empty-expr-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (second pass). The NARROWEST near-miss on the `expr`
        # binder that the battery leaves unprobed. Every pre-existing rival —
        # weak-drop-expr included — attacks `expr` only at NON-EMPTY values, and
        # all eight prior witnesses pin `expr` to a one-character literal. This
        # rival is byte-identical to gold on every input with a non-empty `expr`
        # and diverges ONLY at `expr = []`, where it declines to wrap. So it is
        # correct on the entire sub-domain the other eight witnesses cover, and
        # can be refuted only at the empty-expression point. It is the case that
        # shows the postcondition pins the wrap for an EMPTY field expression
        # too, rather than merely for the non-empty ones the battery samples.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active ∧ storedZone ≠ queryZone ∧ expr ≠ [] then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ storedZone\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Adds an unwarranted emptiness test on the field expression, "
                      "so the conversion is silently skipped when that expression "
                      "is empty. Its faithful real patch guards the wrap on the "
                      "field expression being non-empty; on the converting path an "
                      "empty expression is then returned bare instead of wrapped, "
                      "so the emitted statement omits the conversion the query "
                      "needs and the read is evaluated in the wrong zone. It does "
                      "NOT resolve.",
        "rationale": "Partial-domain REJECT from the wrap clause at the boundary "
                     "value of the `expr` binder: the postcondition requires the "
                     "wrap whenever the guard holds, with NO side condition on "
                     "`expr`, so an impl may not condition the wrap on `expr` "
                     "being non-empty. Refuted at active=true, expr=\"\", "
                     "queryZone=\"Zurich\", storedZone=\"Recife\": gold wraps the "
                     "empty expression, the rival returns it bare. Correct on "
                     "every non-empty `expr`, hence refutable at NO input any "
                     "other witness uses (all eight pin `expr` to a single "
                     "character) — this is the case that varies `expr` to its "
                     "boundary value. No nagini sibling: the sibling's scalar "
                     "carrier has no field-expression argument, so it has no "
                     "empty-value boundary to probe (ADDED by audit).",
        "witness": _witness(
            'buildTzAdjustedExprTester true "".toList "Zurich".toList "Recife".toList'),
    },
    {
        "id": "weak-empty-zone-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (third pass). The remaining unprobed boundary: the two
        # ZONE-NAME binders. weak-empty-expr-skip closed the empty boundary of
        # `expr`, but all ten prior witnesses hold BOTH `queryZone` and
        # `storedZone` at non-empty names, so an impl that declines to wrap
        # exactly when the target zone name is empty is byte-identical to gold at
        # every input the battery samples and is refuted by NONE of its witnesses
        # (checked mechanically against all ten). This rival is that impl: correct
        # on the whole non-empty-zone domain, wrong only at the empty target-zone
        # point. It shows the postcondition pins the wrap with NO side condition
        # on the zone-name binders either, not merely on `expr`.
        "module": _with_impl(
            "    let out : List Char :=\n"
            "      if active ∧ storedZone ≠ queryZone ∧ queryZone ≠ [] then\n"
            "        \"CONVERT_TZ(\".toList ++ expr ++ \", '\".toList ++ storedZone\n"
            "          ++ \"', '\".toList ++ queryZone ++ \"')\".toList\n"
            "      else\n"
            "        expr\n"
            "    return out"),
        "refinement": "Adds an unwarranted emptiness test on the TARGET zone name, "
                      "so the conversion is silently skipped when that name is "
                      "empty. Its faithful real patch guards the wrap on the target "
                      "zone name being non-empty; on the converting path the "
                      "expression is then returned bare instead of wrapped, so the "
                      "emitted statement omits the conversion the query needs and "
                      "the stored value is read in the wrong zone. It does NOT "
                      "resolve.",
        "rationale": "Partial-domain REJECT from the wrap clause at the boundary "
                     "value of the ZONE-NAME binders: the postcondition requires "
                     "the wrap whenever the guard holds, with no side condition on "
                     "`queryZone`, so an impl may not condition the wrap on the "
                     "target zone name being non-empty. Refuted at active=true, "
                     "expr=\"M\", queryZone=\"\", storedZone=\"Denver\": gold wraps "
                     "with an empty target name, the rival returns \"M\" bare. "
                     "Correct on every non-empty `queryZone`, hence refutable at NO "
                     "input any other witness uses (all ten pin both zone names to "
                     "non-empty values) — this is the case that varies the zone-name "
                     "binders to their boundary. No nagini sibling: the sibling's "
                     "integer-offset carrier has no zone-NAME argument, so it has no "
                     "empty-name boundary to probe (ADDED by audit).",
        "witness": _witness(
            'buildTzAdjustedExprTester true "M".toList "".toList "Denver".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# CARRIER NARROWING (read first). The nagini sibling and this velvet bundle
# model DIFFERENT functions of the SAME underlying fix. The nagini sibling
# contracts an integer wall-clock ARITHMETIC surface over zone offsets. Velvet
# models `buildTzAdjustedExpr` — the SQL-expression builder (mapping.md §1), a
# pure `List Char` string computation. Both carry the *complete* discriminating logic
# of the fix (use the stored/connection zone as the conversion source instead of
# a fixed reference zone, and skip the conversion when stored == query), so every
# nagini clause has a faithful counterpart here — but expressed over a string
# carrier and a two-condition guard rather than integer offsets. The nagini
# arithmetic sign/offset attacks re-express as string source/target/guard
# attacks. This is carrier re-expression, not parity chasing.
#
#   sibling case (nagini)      -> here                     disposition
#   ------------------------------------------------------------------------
#   pos-cheapest               -> pos-cheapest             PORTED (grounded model echo)
#   pos-reorder                -> pos-reorder              RE-EXPRESSED (De Morgan guard flip)
#   admiss-self                -> admiss-f2p-nondegenerate RE-EXPRESSED (see below)
#   weak-prepatch              -> weak-prepatch            RE-EXPRESSED (UTC source + no guard)
#   weak-drop-conn             -> weak-hardcode-utc        RE-EXPRESSED (source = fixed literal)
#   weak-sign                  -> weak-swap-zones          RE-EXPRESSED (wrong direction)
#   weak-partial-equalzone     -> weak-drop-eqguard        RE-EXPRESSED (equal-zone sub-domain)
#   weak-partial-notarget      -> weak-drop-active         RE-EXPRESSED (support-off sub-domain)
#   weak-zero                  -> weak-identity            PORTED (cheapest wrong)
#   (new, no sibling)          -> weak-drop-expr           ADDED (abuses the `expr` binder)
#   (new, no sibling)          -> weak-unquoted-zones      ADDED by audit (literal fragments)
#   (new, no sibling)          -> weak-empty-expr-skip     ADDED by audit (empty-`expr` boundary)
#   (new, no sibling)          -> weak-empty-zone-skip     ADDED by audit (empty zone-NAME boundary)
#   AXIOM_TESTS (empty)        -> (none)                   DROPPED (G-AX)
#   FRAME-MUTATION (N/A there) -> (none)                   VACUOUS (no heap)
#   DIVERGENCE                 -> (none)                   see note (no sibling case)
#
# RE-EXPRESSED. The sibling's value-level arithmetic attacks map cleanly to the
#   string guard/wrap: dropping the source-offset term (source forced to the zero
#   offset) becomes the source zone forced to the "UTC" literal
#   (weak-hardcode-utc / weak-prepatch); the
#   offset sign-flip becomes swapping the source and
#   target zone slots (weak-swap-zones); the equal-zone +1 off-by-one becomes
#   dropping the `storedZone ≠ queryZone` conjunct so a needless conversion is
#   emitted on the equal-zone sub-domain (weak-drop-eqguard); the no-target
#   un-restored relabel becomes dropping the `active` conjunct so a conversion is
#   emitted with support off (weak-drop-active). pos-reorder's "net-shift-up-front"
#   restructure becomes a De Morgan guard negation with flipped branches.
# RE-EXPRESSED (admiss-self -> admiss-f2p-nondegenerate). CORRECTED BY AUDIT.
#   An earlier revision of this footer DROPPED the lane, reasoning that
#   `buildTzAdjustedExpr` has no `require` clause so there is no precondition to
#   probe and an admissibility positive "would assert nothing". That reason is
#   WRONG and the omission was a real defect: the absence of a precondition is
#   precisely the case the lane still has to cover, because on a TOTAL carrier the
#   analogue of PRECOND-TOO-STRONG is not an over-strong `require` but an
#   obligation that is UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input.
#   A post-image no impl can meet, or one that collapses to a constant, would make
#   every reject case above pass for a reason that has nothing to do with the
#   spec's real content. Sibling velvet cells whose obligations likewise carry no
#   `require` ship an admissibility positive for this reason, and the coverage
#   reporter independently flagged the lane as missing here. So the case is now
#   LANDED (admiss-f2p-nondegenerate): it discharges, by evaluation at a concrete
#   F2P-shaped input, that the post-image is satisfiable on BOTH sub-domains and
#   that the two images are DISTINCT, as a `have`-style in-region `assert` before
#   the frozen obligation closes verbatim over a byte-identical gold impl. Its
#   assert is live: the audit built the same case with the distinctness clause
#   inverted and it FAILED, `decide` refuting the false proposition.
# VACUOUS (frame-mutation). Referentially transparent backend, no `mut` binder,
#   no heap — no read-only field to overwrite. Not fabricated (porting map).
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
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
# PORTED (pos-cheapest, weak-identity). Direct counterparts.
# ADDED (weak-drop-expr). The velvet carrier has a field-expression argument
#   (`expr`) the nagini scalar carrier lacks; this rival attacks the clause that
#   the wrap must embed `expr`, and is the case that varies/abuses that binder.
# ADDED BY AUDIT (weak-unquoted-zones). The pre-existing rivals all attack which
#   INPUT lands in which slot, or the guard; none attacked the CONSTANT fragments
#   that delimit the emitted expression. This rival gets every slot, the order,
#   the guard and `expr` right and only drops the quoting around the two zone
#   names, closing that gap.
#
#   The ten reject witnesses probe ten DISTINCT input tuples. `active` takes
#   {true (×9), false (×1)} — varied by weak-drop-active; `storedZone` takes
#   {Kolkata, Nairobi, UTC, A, s, src, A, Oslo, Recife, Denver}; `queryZone` takes
#   {Paris, Bangkok, UTC, B, q, tgt, B, Lima, Zurich, ""} — driven to its EMPTY
#   boundary by weak-empty-zone-skip, the only witness that does; `expr` takes
#   {D, X, F, G, H, I, J, K, "", M} — varied by weak-drop-expr (which drops it from
#   the wrap) and by weak-empty-expr-skip (which takes it to its EMPTY boundary,
#   the only witness that does). Every independent clause of the postcondition —
#   the two guard conjuncts (a),(b), the source (c), the target/order (d), the
#   embedded expr (e) including its empty-value boundary, the zone-NAME binders
#   including their empty-value boundary, and the constant fragments delimiting
#   them — is attacked by at least one rival. pts=10.
#
#   Each witness was SEEN to discriminate: it ELABORATES against the rival
#   (straight-line tester reduces under `decide`) and FAILS against the frozen
#   solution, the required two-build check. The second audit re-derived all 20
#   builds independently rather than trusting the recorded outcomes: every
#   rival-side witness exit 0, every gold-side witness exit 1, and every gold-side
#   failure was the message `Tactic 'decide' proved that the proposition ... is
#   false` — i.e. `decide` REFUTED the concrete claim semantically. That
#   distinction is the one the gate cannot make: a gold-side exit 1 from a stuck
#   reduction, an unknown identifier or a type error would be a non-discriminating
#   witness with the same exit code. None of the ten fails that way.
#
#   FORGERY-TESTED (20 further builds). Reading an error and calling it "semantic"
#   is not evidence, so each gold-side exit code was shown to CARRY INFORMATION
#   ABOUT THE CLAIM rather than merely to be an exit code. For every reject case a
#   second file was built differing from the witness ONLY in what it asserts —
#   `... = true` in place of `... = false` — on both sides. The flip INVERTS both
#   exit codes in every one of the ten cases: gold goes 1 -> 0 and the rival goes
#   0 -> 1. So gold's failure tracks the claim exactly, and no case could have
#   recorded `rejected` for a witness asserting gold is CORRECT at that input.
#   These are not tautologies and not tactic-mismatch artifacts.
#
#   Audit probes that found NO defect (recorded so the next reader need not
#   re-run them). Three NEW wrong impls beyond the shipped rivals were built
#   against the frozen spec to look for a spec hole, and all three were REJECTED
#   (exit 1, `unsolved goals` on the `ensures`): a guard conditioned on `expr`
#   being non-empty (kept — it is the shipped weak-empty-expr-skip), a guard
#   comparing the two zone NAME LENGTHS instead of the names, and a wrap whose
#   source zone is truncated to three characters. Three NEW correct reshapes were
#   built to look for a soundness hole: an `(active = true) ∧ queryZone ≠
#   storedZone` symmetric guard and a nested-if guard both VERIFY under the frozen
#   `loom_solve` (exit 0), so the spec is not too strong on either. A third
#   reshape building the wrap through `String` `++` and back via `String.mk`/
#   `.toList` does NOT close under the frozen `loom_solve` alone (`unsolved
#   goals`) but DOES close under `loom_solve <;> rfl` (exit 0) — so that shape is
#   provable and the spec admits it; the gap is in the frozen tactic script's
#   reach, not in the spec, and it is not a soundness hole. Not shipped as a
#   positive case: a `verify` case must close with the frozen proof unchanged.
#
#   SECOND-AUDIT probes, all built (recorded so the next reader need not re-run
#   them). FIVE further NEW wrong impls were aimed at angles no shipped rival
#   covers, and the frozen spec REJECTED all five (exit 1, `unsolved goals` on the
#   `ensures`), so no spec hole: the closing delimiter of the emitted expression
#   dropped while every other fragment is kept; an exclusive-or guard that wraps
#   iff exactly one of the two conditions holds; the source zone case-folded
#   (identity on any single-case zone name, so a very narrow near-miss); the field
#   expression embedded TWICE; and a guard conditioned on the TARGET zone name
#   being non-empty — that last one turned out to be refutable by NONE of the ten
#   witnesses then shipped, which is why it is now the shipped
#   weak-empty-zone-skip rather than a discarded probe. FOUR further NEW correct
#   reshapes were built to look for a soundness hole and ALL FOUR VERIFY under the
#   UNCHANGED frozen `loom_solve` (exit 0), so the spec is not too strong on any of
#   them: a `match` on the support flag with a nested equality test; a three-`let`
#   fragment chain concatenated in the guarded branch; a guard written as a `Bool`
#   conjunction through `&&` and `decide`; and an early-`return` two-exit control
#   flow rather than a single `let`-then-`return`. Together with the three earlier
#   reshapes that is seven correct shapes the spec admits.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (mapping.md §3.1: fully deep model, `axioms = []`), so there is nothing to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []

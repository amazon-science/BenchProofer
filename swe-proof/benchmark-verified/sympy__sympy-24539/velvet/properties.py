"""properties.py — G-PBT falsification battery for sympy__sympy-24539 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct asExpr`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  asExpr (d) (ringSymbols) (symbols)   ensures out = asExprSpec d ringSymbols symbols

Three INPUT binders. ``d`` is an opaque datum handle; ``ringSymbols`` and
``symbols`` are TRANSPARENT ``List Int`` (the datum's own ordered names, and the
caller's optional names). The whole outcome is pinned as a total function of
those three by ``asExprSpec``, which has THREE independent top-level legs — the
first two produce a value through the ONLY opaque callee ``exprFromDict``, whose
SECOND argument (the chosen name list) is the load-bearing observable:

  (E-empty) symbols.isEmpty                        -> ok (exprFromDict d ringSymbols)
  (E-honor) ¬isEmpty ∧ len symbols = len ringSymbols -> ok (exprFromDict d symbols)
  (E-reject) ¬isEmpty ∧ len symbols ≠ len ringSymbols -> error wrongNumberOfSymbols

E-honor is the discriminating behaviour the public issue reports: a
correctly-sized caller list must be RENDERED OVER (honored), not silently
replaced by the datum's own names. A wrong rival must violate one of the three
legs.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION (both nagini frame-mutation rivals) — VACUOUS here. The nagini
    class exists because an input carries a fractional heap permission an impl can
    overwrite (a value no-op write that only a permission system, not the value
    abstraction, can reject). This backend is referentially transparent and this
    bundle declares NO ``mut`` binder in its signature: ``d``, ``ringSymbols`` and
    ``symbols`` are immutable values, there is no heap and no aliasing, so there
    is no read-only input to mutate and no substitute probe to build. Not
    fabricated; see the accounting block for the two omitted cases.
  * PARTIAL-DOMAIN / CONTROL-FLOW — APPLY. The selection decision is transparent
    (``symbols.isEmpty`` and the two lengths), so a rival right on part of the
    input space but diverging on a sub-region is the natural falsifier. The rivals
    below partition the space along the three legs.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. ``asExprSpec`` is a total
    ``def`` in the ``pure`` region written directly over the transparent selection
    decision and the ONE opaque callee ``exprFromDict``; it is not an opaque
    answer-key the impl could echo without doing the work (the impl must itself
    reproduce the leg dispatch and forward the same list). The ``axioms`` region
    declares no ``axiom`` — ``exprFromDict`` is ``opaque`` with no ``ensures`` — so
    there is no consumed contract to attack. Honest positive controls stand in for
    the ungrounded-echo probe.

THE WITNESS ON THIS CARRIER. The rendered value flows through the opaque
``exprFromDict``, so a ``decide`` on a literal cannot compute it. Two shapes are
used, both reaching the extracted program via Velvet's own extractor
(``extract_program_for asExpr`` gives ``asExprExec = NonDetT.run ∘ asExpr``):

  * When the two legs disagree only in WHICH list is forwarded to the SAME
    ``exprFromDict d`` (E-empty vs E-honor swaps, and the drop-last off-by-one),
    the witness fixes ``d`` to a literal and HYPOTHESISES that the renderer
    distinguishes the two lists (``exprFromDict 0 [2] ≠ exprFromDict 0 [1]`` — the
    ``uses-gens`` fact G-AX validates against the real callee). It then shows the
    program's output differs from ``asExprSpec`` there. ONE hypothesis per witness,
    about a single opaque term — never two hypotheses about the same term (which
    would be a contradictory forgery the gate's ``consistency_probe`` rejects); the
    gate's derive-``False``-from-binders check leaves each of these consistent
    (verified during authoring).
  * When the legs disagree in the OUTCOME SHAPE (ok vs error — the never-reject
    rival), no hypothesis is needed: ``ok _ ≠ error _`` is a constructor clash the
    kernel decides directly, so that witness binds nothing at all.

Each witness ELABORATES against its rival and FAILS against the frozen solution —
the two halves of the discrimination check, verified with real builds. The gold-
side failure is SEMANTIC, not a reduction artifact of the frozen impl's
``mut``/early-return shape: at each probed point gold's extracted program
provably EQUALS the spec (``asExprExec 0 [2] [1] = DivM.res (asExprSpec 0 [2]
[1])`` closes by ``rfl`` after ``unfold``, and likewise at the other three
points), so the witness's ``≠`` is contradicted by a fact about gold's VALUE
rather than left unreduced. Cross-checked in the other direction too: each
witness also FAILS against a CORRECT straight-line impl of the same shape as the
rivals (there the goal reduces all the way to ``False``), and the E-honor witness
HOLDS of a wrong impl written in gold's own ``mut``/early-return shape. So the
witnesses discriminate WRONGNESS, not syntactic form.
The witnesses are stated positionally (``asExprExec <d> <ringSymbols> <symbols>``)
so the coverage tool can read which input point each probes. No
``sorry``/``admit``/``native_decide``/``axiom``.

WITNESS PLACEMENT / BINDER COVERAGE. The four reject witnesses probe FOUR distinct
input points and move every input binder: ``d`` at {0, 1}; ``symbols`` at {[1],
[1,2], []} (the honored, off-by-one, and empty cases); ``ringSymbols`` at {[2],
[2,3], [9,9], [5]}. No binder is pinned across the battery, and every top-level
leg of ``asExprSpec`` (E-empty, E-honor, E-reject) is attacked by some rival.

ADMISSIBILITY lane: PRESENT (``admiss-f2p-legs``). This bundle has no ``require``
clause, so the classical "does the precondition admit a normal input" probe has
no precondition to test; the analogue on a TOTAL carrier is the obligation being
unsatisfiable — or degenerate — at exactly an F2P-shaped input, which the case
discharges by EVALUATION as an in-region ``assert`` at concrete inputs before
closing the frozen obligation verbatim. See the case comment for the liveness
builds. (An earlier revision of this battery omitted the lane, on a reason the
audit disproved with real builds; see the accounting block.)

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; ``exprFromDict`` is
``opaque`` with no asserted ``ensures``, owed no contract — it is an A-reference
validated by G-AX, mapping.md §3). There is no axiom-soundness / axiom-containment
obligation to probe here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24539"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole gold selection body, wholly inside the one
# ---- `-- impl-start` / `-- impl-end` region and unique in the file (both facts
# ---- asserted at load by _swap). Every variant reshapes exactly this block. ----
_GOLD_IMPL = (
    "    -- Choose the list of generator names to render over, then hand the datum and\n"
    "    -- that list to the unchanged renderer. The caller's own names are honored\n"
    "    -- when one per generator is supplied; the datum's names are used when the\n"
    "    -- caller supplies none; any other caller length is rejected.\n"
    "    let mut chosen : List Int := symbols\n"
    "    if symbols.isEmpty then\n"
    "      chosen := ringSymbols\n"
    "    else\n"
    "      if symbols.length = ringSymbols.length then\n"
    "        chosen := symbols\n"
    "      else\n"
    "        return Except.error AsExprErr.wrongNumberOfSymbols\n"
    "    return Except.ok (exprFromDict d chosen)"
)

# ---- Note: both positive controls reshape ONLY the impl region; the frozen
# ---- `prove_correct asExpr by loom_solve <;> simp_all [asExprSpec]` tactic body
# ---- still closes for each, so neither retunes it (no proof-region swap needed).


def _with_impl(new_body):
    """`_BASE` with the frozen impl body replaced (impl region only). The spec,
    the method signature and the `prove_correct` header/statement are untouched,
    so same_spec holds and the obligation survives."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT whose value flows through
# ---- the opaque `exprFromDict`, so a witness reaches the impl through Velvet's
# ---- extractor and either hypothesises that the renderer distinguishes two name
# ---- lists (when the legs differ only in the forwarded list) or relies on an
# ---- `ok`/`error` constructor clash (when they differ in outcome shape).
# ---- Checked in a file whose `prove_correct` block is stripped, so no tactic
# ---- script can interfere.
_EXTRACT = "extract_program_for asExpr\n\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = asExprSpec …`
    # obligation and the frozen tactic body, reshaping only the selection.
    # =====================================================================
    {
        "id": "pos-guard-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the length guard is checked BEFORE the empty case rather than
        # after. Logically equivalent — an empty caller list has length 0, which
        # equals ringSymbols.length only when the datum has no generators, and in
        # that sub-case rendering over `symbols` (=[]) and over `ringSymbols`
        # (=[]) forward the same list — so every leg computes the same
        # `Except AsExprErr Int`. The frozen tactic body still closes.
        "module": _with_impl(
            "    -- structurally reordered: the length guard is checked first\n"
            "    let mut chosen : List Int := symbols\n"
            "    if symbols.length = ringSymbols.length then\n"
            "      if symbols.isEmpty then\n"
            "        chosen := ringSymbols\n"
            "      else\n"
            "        chosen := symbols\n"
            "    else\n"
            "      if symbols.isEmpty then\n"
            "        chosen := ringSymbols\n"
            "      else\n"
            "        return Except.error AsExprErr.wrongNumberOfSymbols\n"
            "    return Except.ok (exprFromDict d chosen)"),
        "rationale": "reordering the empty/length guards computes the same "
                     "`Except AsExprErr Int` on every leg of `asExprSpec` (an "
                     "empty caller list matches the length only when the datum "
                     "has no generators, where both branches forward the same "
                     "empty list), so `out = asExprSpec d ringSymbols symbols` "
                     "still holds; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on guard order).",
    },
    {
        "id": "pos-straightline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the mutable local and the fall-through render are replaced by a
        # straight-line three-way dispatch that returns from each arm directly.
        # Identical value flow on all three legs; the frozen tactic body closes.
        "module": _with_impl(
            "    -- straight-line three-way selection, no mutable local\n"
            "    if symbols.isEmpty then\n"
            "      return Except.ok (exprFromDict d ringSymbols)\n"
            "    else if symbols.length = ringSymbols.length then\n"
            "      return Except.ok (exprFromDict d symbols)\n"
            "    else\n"
            "      return Except.error AsExprErr.wrongNumberOfSymbols"),
        "rationale": "a straight-line three-way selection returning from each arm "
                     "computes the identical outcome on every leg of `asExprSpec`, "
                     "so `out = asExprSpec d ringSymbols symbols` holds; a correct "
                     "reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE, and non-degenerate, at
    # an F2P-shaped input. This bundle declares no `require` clause, so the
    # classical "a normal input clears the precondition" probe has no
    # precondition to clear; on a TOTAL carrier the residual risk in this
    # direction is that the post-image is unsatisfiable or COLLAPSED at exactly
    # the interesting point — a spec no impl can meet, or one that cannot tell
    # the legs apart, reads like a spec every impl meets. This case discharges
    # that by EVALUATION as an in-region `assert` at concrete F2P-shaped inputs
    # (three generators; a correctly-sized caller list of three DIFFERENT names)
    # covering all three legs, then closes the frozen obligation verbatim with
    # the frozen tactic body — so nothing is retuned and the method's own
    # `ensures` still discharges.
    #
    # AUDIT REPAIR (this case is new). The battery shipped with NO admissibility
    # case, on the recorded reason that the lane is "inexpressible" here because
    # an impl-region self-call `let probe ← asExpr d ringSymbols symbols` fails
    # with `fail to show termination for asExpr`. Re-measured: the self-call does
    # fail that way (exit 1) — but the conclusion does not follow, because a
    # self-call is not the only shape the lane has on a total carrier, and the
    # `assert`-at-a-concrete-input shape the sibling cells use DOES land here
    # (exit 0, frozen tactic body, no proof retune). The omission was a real gap,
    # not a carrier limit. (The dropped note attributed the failure to "this
    # bundle's `partial` semantics", which was true when it was written and is
    # now STALE: line 4 of the frozen file sets
    # `loom.semantics.termination "total"`. The self-call still fails, on the
    # termination obligation `total` demands, so the observation survives the
    # flip even though its stated reason no longer names the live setting.)
    #
    # The assert is LIVE, not decoration — each of the three conjuncts was
    # falsified in turn and each falsification leaves an unsolved goal under the
    # frozen tactic body (exit 1):
    #   * honored leg wrong  (`... [4,5,6]` -> `ok (exprFromDict 0 [1,2,3])`):
    #     residual `⊢ exprFromDict 0 [4,5,6] = exprFromDict 0 [1,2,3]`;
    #   * empty leg wrong    (`... []` -> `ok (exprFromDict 0 [4,5,6])`):
    #     unsolved goal on that conjunct;
    #   * reject leg wrong   (`... [4]` -> `ok (exprFromDict 0 [4])`):
    #     unsolved goal on that conjunct.
    # So a false claim about the same point does not slip through, which is what
    # makes the true one evidence.
    # =====================================================================
    {
        "id": "admiss-f2p-legs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(
            "    -- Admissibility at an F2P-shaped input: three generators, and a\n"
            "    -- correctly-sized caller list of three DIFFERENT names. The\n"
            "    -- obligation is satisfiable AND non-degenerate here — the three\n"
            "    -- legs of `asExprSpec` take three DISTINCT outcomes at this one\n"
            "    -- generator count, so no leg is unreachable and the post-image\n"
            "    -- is not a constant collapse.\n"
            "    assert (with_name_prefix `admiss\n"
            "      (asExprSpec 0 [1, 2, 3] [4, 5, 6] = Except.ok (exprFromDict 0 [4, 5, 6]) ∧\n"
            "       asExprSpec 0 [1, 2, 3] [] = Except.ok (exprFromDict 0 [1, 2, 3]) ∧\n"
            "       asExprSpec 0 [1, 2, 3] [4] = Except.error AsExprErr.wrongNumberOfSymbols))\n"
            + _GOLD_IMPL),
        "rationale": "PRECOND-TOO-STRONG probe, re-sited to a total carrier. "
                     "There is no `require` clause, so the analogue is the "
                     "obligation being unsatisfiable or DEGENERATE at an "
                     "F2P-shaped input; this case discharges, by evaluation at a "
                     "three-generator datum, that all three legs of `asExprSpec` "
                     "are simultaneously reachable and take DISTINCT outcomes "
                     "there: a correctly-sized caller list of three different "
                     "names renders over the CALLER's names, no caller list "
                     "renders over the datum's own names, and a wrong-count list "
                     "is rejected. So `out = asExprSpec d ringSymbols symbols` is "
                     "satisfiable at exactly the interesting point and does not "
                     "collapse the legs together. The surrounding impl and the "
                     "frozen tactic body are kept verbatim, so the method's own "
                     "obligation still discharges; the assert is live (falsifying "
                     "any one conjunct leaves an unsolved goal).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input point and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================

    # ---- E-honor: a correctly-sized caller list must be RENDERED OVER ----
    {
        "id": "weak-ignores-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-patch bug: on a correctly-sized caller list, render over
        # the datum's OWN names instead of the caller's. Correct on E-empty and
        # E-reject; wrong exactly on E-honor.
        "module": _with_impl(
            "    -- render over the datum's own names even when the caller supplies a\n"
            "    -- correctly-sized list\n"
            "    if symbols.isEmpty then\n"
            "      return Except.ok (exprFromDict d ringSymbols)\n"
            "    else if symbols.length = ringSymbols.length then\n"
            "      return Except.ok (exprFromDict d ringSymbols)\n"
            "    else\n"
            "      return Except.error AsExprErr.wrongNumberOfSymbols"),
        "refinement": "this is exactly the reported defect: a correctly-sized "
                      "caller list is silently discarded and the datum's own "
                      "names are used, so the rendered expression is the one "
                      "built over the datum's names, not the caller's. The "
                      "failing test supplies a matching-length list of DIFFERENT "
                      "names and asserts the result equals the expression over "
                      "THOSE names; the datum's-names rendering is a different "
                      "expression, so the assertion stays RED. It would NOT "
                      "resolve.",
        "rationale": "REJECT from E-honor (¬isEmpty ∧ len symbols = len "
                     "ringSymbols -> ok (exprFromDict d symbols)): at a matching "
                     "non-empty caller list the impl forwards `ringSymbols` where "
                     "the post-image demands `symbols`. Probes symbols=[1], "
                     "ringSymbols=[2] (distinct, both length 1); the witness "
                     "hypothesises the renderer distinguishes the two lists.",
        "witness": _EXTRACT +
                   "example (h : exprFromDict 0 [2] ≠ exprFromDict 0 [1]) :\n"
                   "    asExprExec 0 [2] [1] ≠ DivM.res (asExprSpec 0 [2] [1]) := by\n"
                   "  unfold asExprExec asExpr asExprSpec\n"
                   "  simpa [NonDetT.run, pure] using h\n",
    },

    # ---- E-reject: a wrong-count caller list must be REJECTED, not rendered ----
    {
        "id": "weak-never-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        # Never rejects: on a wrong-count caller list, falls back to the datum's
        # own names and returns a value. Correct on E-empty and E-honor; wrong
        # exactly on E-reject (returns `ok` where the post-image demands `error`).
        "module": _with_impl(
            "    -- never reject: fall back to the datum's own names on a wrong-count list\n"
            "    let chosen : List Int := if symbols.isEmpty then ringSymbols\n"
            "      else if symbols.length = ringSymbols.length then symbols else ringSymbols\n"
            "    return Except.ok (exprFromDict d chosen)"),
        "refinement": "a counterpart that silently falls back to the datum's own "
                      "names on a wrong-count caller list renders an expression "
                      "instead of raising. The failing test supplies a "
                      "wrong-count list and asserts a ValueError is raised; a "
                      "rendered value raises nothing, so that assertion stays "
                      "RED. It would NOT resolve.",
        "rationale": "REJECT from E-reject (¬isEmpty ∧ len symbols ≠ len "
                     "ringSymbols -> error wrongNumberOfSymbols): on a wrong-count "
                     "non-empty caller list the impl returns `ok` where the "
                     "post-image demands `error`. Probes symbols=[1], "
                     "ringSymbols=[2,3] (lengths 1≠2); an `ok`/`error` "
                     "constructor clash the kernel decides with no hypothesis.",
        "witness": _EXTRACT +
                   "example : asExprExec 1 [2, 3] [1] ≠ "
                   "DivM.res (asExprSpec 1 [2, 3] [1]) := by\n"
                   "  unfold asExprExec asExpr asExprSpec\n"
                   "  simp [NonDetT.run, pure]\n",
    },

    # ---- E-honor, tail sub-domain: the WHOLE caller list must be forwarded ----
    {
        "id": "weak-drops-last-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Honors the caller's list but forwards it with its FINAL name dropped
        # (an off-by-one on the tail). Correct on E-empty and E-reject, and on the
        # HEAD of the caller list; wrong exactly on E-honor whenever the caller
        # list is non-empty — the tail-of-sequence sub-domain a head-only check
        # would miss.
        "module": _with_impl(
            "    -- honor the caller's list but drop its final name\n"
            "    if symbols.isEmpty then\n"
            "      return Except.ok (exprFromDict d ringSymbols)\n"
            "    else if symbols.length = ringSymbols.length then\n"
            "      return Except.ok (exprFromDict d symbols.dropLast)\n"
            "    else\n"
            "      return Except.error AsExprErr.wrongNumberOfSymbols"),
        "refinement": "forwarding the caller's list minus its final name renders "
                      "the expression over too few names — the last generator's "
                      "contribution is dropped from every monomial that used it. "
                      "The failing test's expected expression uses the final "
                      "generator, so the truncated rendering differs and the "
                      "assertion stays RED. It would NOT resolve.",
        "rationale": "REJECT from E-honor (ok (exprFromDict d symbols)): the "
                     "impl forwards `symbols.dropLast` where the post-image "
                     "demands the whole `symbols`. Probes symbols=[1,2], "
                     "ringSymbols=[9,9] (both length 2, so the length guard "
                     "passes); the witness hypothesises the renderer "
                     "distinguishes [1] from [1,2] — the tail sub-domain no "
                     "other rival exercises.",
        "witness": _EXTRACT +
                   "example (h : exprFromDict 0 [1] ≠ exprFromDict 0 [1, 2]) :\n"
                   "    asExprExec 0 [9, 9] [1, 2] ≠ "
                   "DivM.res (asExprSpec 0 [9, 9] [1, 2]) := by\n"
                   "  unfold asExprExec asExpr asExprSpec\n"
                   "  simpa [NonDetT.run, pure] using h\n",
    },

    # ---- E-empty: no caller list must select the datum's OWN names ----
    {
        "id": "weak-empty-uses-caller-list",
        "kind": "uniqueness",
        "expect": "reject",
        # On an EMPTY caller list, renders over that empty list instead of the
        # datum's own names. Correct on E-honor and E-reject; wrong exactly on
        # E-empty. Probes symbols=[] — the empty case no other rival exercises,
        # moving the `symbols` binder to [].
        #
        # AUDIT REPAIR. The impl this case shipped with dropped the empty-list
        # guard entirely:
        #     if symbols.length = ringSymbols.length then ok (exprFromDict d symbols)
        #     else error
        # which does NOT render over the empty caller list anywhere its prose
        # claimed. At `symbols = []` that guard holds only when
        # `ringSymbols = []` too — and there gold forwards `[]` as well, so the
        # two agree (machine-checked: gold-shaped `rfl` closes
        # `asExprExec 1 [] [] = DivM.res (asExprSpec 1 [] [])`). Its only real
        # divergence was `ok` vs `error` at a non-empty datum, i.e. a DUPLICATE
        # of weak-never-rejects' constructor clash on the OTHER side, and its
        # witness's `exprFromDict 1 [] ≠ exprFromDict 1 [5]` hypothesis was DEAD
        # (Lean reported `unused variable h`; the same witness elaborates with no
        # hypothesis at all). So the case rejected for a reason its rationale did
        # not name and left E-empty's forwarded-list observable unprobed.
        # Repaired to the rival the prose describes: keep the empty-list guard
        # and forward the empty `symbols` on that leg, which is a VALUE-level
        # divergence on E-empty. Re-verified: the hypothesis is now load-bearing
        # (no `unused variable`), the witness elaborates against this rival
        # (exit 0) and fails on gold (exit 1) with a residual `≠` over the SAME
        # `exprFromDict 1 [5]` term the hypothesis is about.
        "module": _with_impl(
            "    -- on an empty caller list, render over that empty caller list instead\n"
            "    -- of the datum's own names\n"
            "    if symbols.isEmpty then\n"
            "      return Except.ok (exprFromDict d symbols)\n"
            "    else if symbols.length = ringSymbols.length then\n"
            "      return Except.ok (exprFromDict d symbols)\n"
            "    else\n"
            "      return Except.error AsExprErr.wrongNumberOfSymbols"),
        "refinement": "when the caller supplies no names, the datum's own names "
                      "must be used; a counterpart that renders over the empty "
                      "list instead produces an expression over no generators "
                      "(the coefficients with every generator stripped). The "
                      "unchanged default-path test asserts the no-argument render "
                      "equals the expression over the datum's own names, so the "
                      "empty-list rendering differs and that test stays RED. It "
                      "would NOT resolve.",
        "rationale": "REJECT from E-empty (symbols.isEmpty -> ok (exprFromDict d "
                     "ringSymbols)): on an empty caller list the impl forwards "
                     "the empty `symbols` where the post-image demands the "
                     "datum's `ringSymbols`, so it returns `ok` of the WRONG "
                     "rendered value — a value-level divergence on this leg, not "
                     "an `ok`/`error` shape clash (that is weak-never-rejects' "
                     "job on the E-reject leg). Probes symbols=[], "
                     "ringSymbols=[5]; the witness hypothesises the renderer "
                     "distinguishes [] from [5], and that hypothesis is "
                     "load-bearing — the goal reduces to exactly "
                     "`exprFromDict 1 [] ≠ exprFromDict 1 [5]`.",
        "witness": _EXTRACT +
                   "example (h : exprFromDict 1 [] ≠ exprFromDict 1 [5]) :\n"
                   "    asExprExec 1 [5] [] ≠ DivM.res (asExprSpec 1 [5] []) := by\n"
                   "  unfold asExprExec asExpr asExprSpec\n"
                   "  simpa [NonDetT.run, pure] using h\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals, 2 of them frame-mutation);
# every one is accounted for below. The two carriers are NOT the same partition:
# the sibling models `select_render_symbols(symbols, default_symbols, ngens)`
# returning the SELECTED int LIST and materialising it element-by-element under a
# loop with fractional heap permissions, whereas this bundle models the whole
# render dispatch `asExpr d ringSymbols symbols` returning `Except AsExprErr Int`,
# with the chosen list forwarded to ONE opaque renderer. The nagini rivals over
# the list-materialisation carrier re-site onto the three legs of `asExprSpec`.
#
#   sibling case                    -> here                              status
#   ---------------------------------------------------------------------------
#   frame-mut-symbols               -> (none, VACUOUS)                   OMITTED
#   frame-mut-default               -> (none, VACUOUS)                   OMITTED
#   uniq-prepatch-always-default    -> weak-ignores-supplied            RE-SITED
#   uniq-drop-last                  -> weak-drops-last-name             RE-SITED
#   uniq-no-raise-wrong-count       -> weak-never-rejects               RE-SITED
#   pos-control-reorder             -> pos-guard-reordered              PORTED
#   admiss-f2p-selfcall             -> admiss-f2p-legs                  RE-SITED
#
# 1 ported, 4 re-sited, 2 omitted (both vacuous frame-mutation).
# ADDED (2): pos-straightline (2nd positive control) and weak-empty-uses-caller-
# list. See below.
#
# RE-SITED (the argument is unchanged; only the carrier is):
#  * uniq-prepatch-always-default attacks nagini E2 (a correctly-sized SUPPLIED
#    sequence must be the selected one). Here that IS leg E-honor (¬isEmpty ∧
#    matching length -> render over `symbols`); the rival renders over
#    `ringSymbols`. This is the discriminating F2P behaviour the public issue
#    reports.
#  * uniq-drop-last attacks the tail of the selected sequence (E2/E3 with the
#    last element dropped). Here the chosen list is a single opaque forward, so
#    the re-siting drops the caller list's final NAME (`symbols.dropLast`) before
#    forwarding — same tail-sub-domain attack, refuted by hypothesising the
#    renderer distinguishes the full list from the truncated one.
#  * uniq-no-raise-wrong-count attacks nagini E1 (a VALUE is produced only on the
#    non-rejected domain). Here that IS leg E-reject (wrong-count -> error); the
#    rival returns `ok` where the post-image demands `error`, refuted by a bare
#    constructor clash.
#
# ADDED (2, sharpening coverage on this carrier):
#  * weak-empty-uses-caller-list. The nagini battery has no rival attacking the
#    empty-supplied leg directly (its E3 is only defended by the drop-last and
#    positive cases). This carrier's E-empty leg (no caller list -> datum's own
#    names) is an independent top-level clause; a rival that renders over the
#    empty caller list instead attacks it. Added for CLAUSE + BINDER coverage:
#    it is the only rival that moves `symbols` to `[]`, so without it the empty
#    case would never be probed and a rival mishandling it would go uncaught. A
#    real divergence from E-empty with a machine-checked witness and a refinement
#    argument (the unchanged default-path test would stay red).
#    AUDIT REPAIR: as first shipped this case's impl dropped the empty-list guard
#    rather than mis-forwarding on it, so it never rendered over the empty caller
#    list at all — its only divergence was an `ok`/`error` clash duplicating
#    weak-never-rejects, and its witness's hypothesis was DEAD (`unused variable
#    h`). The impl is now the one the prose describes, so the E-empty forwarded-
#    list observable is genuinely probed and the hypothesis is load-bearing. See
#    the case comment for the exact builds.
#  * pos-straightline. A 2nd structurally-different positive control (no mutable
#    local, direct returns) beside the guard-reorder, both defending the whole
#    obligation is dischargeable by a faithful impl.
#
# OMITTED (2):
#  * frame-mut-symbols, frame-mut-default. Nagini-specific (fractional heap
#    permissions: a value-no-op write `symbols[0]=symbols[0]` the value
#    abstraction cannot see but the permission system rejects). This backend is
#    referentially transparent and the method declares no `mut` binder — `d`,
#    `ringSymbols`, `symbols` are immutable values with no heap and no aliasing —
#    so there is no read-only input to overwrite and no substitute probe.
#    VACUOUS; no substitute fabricated (per the porting map's frame/permission
#    row). AUDIT: re-derived mechanically rather than taken on the prose. The
#    binder list is part of the method SIGNATURE, which lives in the consumer
#    spec view, so a variant cannot even introduce a `mut` binder to mutate:
#    declaring `mut ringSymbols` makes `variant_problems` report `spec view
#    differs (same_spec failed)`, i.e. out of scope as a malformed test rather
#    than a rival. Confirmed inexpressible on this carrier.
# NOTE (audit): the third omission below is NO LONGER an omission. The
# admissibility lane is now carried by `admiss-f2p-legs` above; the accounting
# row is kept, with its disposition corrected, because the reason it was dropped
# was measurably wrong and that is worth recording rather than erasing.
#
#  * admiss-f2p-selfcall -> RE-SITED as `admiss-f2p-legs` (was: OMITTED).
#    The sibling's admissibility case discharges a precondition
#    `Requires(ngens == len(default_symbols))` plus two `Acc(list_pred,1/2)`
#    halves at a representative call site. This bundle has NO `require` clause
#    (the admitted domain is total — every `(d, ringSymbols, symbols)` is in
#    scope) and no fractional permissions, so the sibling's LITERAL shape — a
#    self-call whose call site must clear a precondition — has no counterpart:
#    re-measured, an impl-region `let probe ← asExpr d ringSymbols symbols`
#    fails with `fail to show termination for asExpr` (exit 1).
#    But that is a fact about the SELF-CALL shape, not about the lane, and the
#    battery previously drew the wrong conclusion from it. On a total carrier the
#    lane's analogue is the obligation being unsatisfiable or DEGENERATE at an
#    F2P-shaped input, which an in-region `assert` discharged BY EVALUATION at
#    that concrete input tests directly — and that shape lands here cleanly
#    (exit 0 under the frozen tactic body, no retune, `variant_problems()==[]`).
#    So the lane is EXPRESSIBLE and is now shipped. Two further corrections to
#    the dropped note: it attributed the self-call failure to "this bundle's
#    `partial` semantics" when line 4 of the frozen file sets
#    `loom.semantics.termination "total"`; and it argued the residual risk
#    "does not arise" because `asExprSpec` is total, which answers only
#    unsatisfiability and not DEGENERACY (whether the legs are distinguishable at
#    the interesting point) — which is the half the shipped case actually probes.
#
#  * DIVERGENCE / non-termination (F′). Not a nagini row, but the class this
#    carrier's semantics decides, so it is dispositioned here. Re-measured AFTER
#    this bundle was migrated from `partial` to `total` termination semantics —
#    under the old `partial` setting a diverging impl verified vacuously and the
#    class was a known spec hole with nothing to ship; the flip is what makes the
#    measurement below meaningful. This bundle sets
#    `loom.semantics.termination "total"`, so a rival whose loop carries no
#    decreasing measure IS genuinely rejected — measured: adding a measure-free
#    `while i < 1 do i := i` to the gold body fails with `Decreasing annotations
#    are required in total correctness semantics` (exit 1). It is nonetheless NOT
#    SHIPPABLE as a reject case on this backend, and the reason is a WITNESS
#    limit rather than a spec limit: the rejection happens at ELABORATION of the
#    method itself, before any obligation is reached, so the rival module is not
#    a well-formed Lean file and NO witness can be built against it. Measured
#    both ways in the witness file (obligations stripped): the refutation witness
#    fails (exit 1) and so does a trivial `example : (1:Nat) + 1 = 2 := by decide`
#    (exit 1) — the same `Decreasing annotations` error, i.e. the file errors
#    regardless of what is claimed, so the rival build could never satisfy the
#    half of the discrimination check that must SUCCEED. A case whose witness
#    cannot elaborate against its own rival records `witness-unproven`
#    (inconclusive => gate error), so shipping it would break the battery rather
#    than strengthen it. Recorded as a BACKEND/harness limit on the divergence
#    lane for this carrier, not as a spec hole and not as a vacuous class: the
#    termination obligation demonstrably does its job.
#
# BINDER / CLAUSE COVERAGE. Three input binders `d`, `ringSymbols`, `symbols`.
# The four reject witnesses probe four DISTINCT input points and move every
# binder: `d` at {0, 1}; `symbols` at {[1] (honored), [1,2] (off-by-one tail),
# [] (empty)}; `ringSymbols` at {[2], [2,3], [9,9], [5]}. No binder is pinned
# across the battery. Every top-level leg of `asExprSpec` (E-empty, E-honor,
# E-reject) is attacked by some rival, and both positive controls defend the
# whole obligation. `admiss-f2p-legs` adds a FIFTH input region the rivals do not
# reach — a three-generator datum (`ringSymbols = [1,2,3]`, caller list
# `[4,5,6]`), the F2P shape itself, where the rivals all sit at lengths 0-2 — and
# pins all three legs at that one generator count simultaneously.
#
# WITNESS DISCRIMINATION (verified with real builds, re-checked by the gate's two
# builds per reject case): each witness ELABORATES against its rival (the rival's
# output provably differs from `asExprSpec` at the probed point) and FAILS against
# the frozen solution. The gold-side failure is SEMANTIC, not a reduction artifact
# of gold's `mut`/early-return shape — an earlier revision of this block claimed
# the latter and the audit disproved it. At every probed point gold's extracted
# program provably EQUALS the spec: `asExprExec d ringSymbols symbols =
# DivM.res (asExprSpec d ringSymbols symbols)` closes by `rfl` after `unfold` at
# (0,[2],[1]), (1,[2,3],[1]), (0,[9,9],[1,2]) and (1,[5],[]), so the witness's `≠`
# is refuted by gold's VALUE. Two further cross-checks separate wrongness from
# shape: each witness also FAILS against a CORRECT straight-line impl of the same
# shape as the rivals (goal reduces to `False`), and the E-honor witness HOLDS of
# a wrong impl written in gold's own `mut`/early-return shape.
# Three witnesses carry ONE hypothesis about a single opaque `exprFromDict`
# application (the `uses-gens` fact G-AX validates) — the gate's
# `consistency_probe` cannot derive `False` from any of them (checked), and each
# hypothesis is LOAD-BEARING (Lean reports no `unused variable`; an earlier
# revision of the E-empty case failed this and was repaired). The never-rejects
# witness binds nothing (a bare `ok`/`error` clash). No
# `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# SPEC-STRENGTH PROBES run by the audit and NOT shipped as cases (all rejected by
# the frozen spec, so none is a hole): forwarding `symbols.reverse`; accepting a
# too-SHORT caller list via a `≤` guard; forwarding `symbols ++ ringSymbols`;
# rendering a perturbed datum handle; rejecting EVERY non-empty caller list.
# A SECOND audit pass added six more wrong impls, all likewise REJECTED (exit 1),
# aimed at what the shipped rivals leave unattacked — the guard PREDICATE itself
# and the leg-to-outcome pairing, rather than the forwarded list:
#   * reject on the EMPTY caller list and render over the datum's names on a
#     wrong-count one (all three legs permuted at once) -> residual `⊢ False`
#     under `if_pos : symbols = []`;
#   * `symbols.length ≥ ringSymbols.length` in place of `=`, admitting a too-LONG
#     caller list -> residual `⊢ symbols.length = ringSymbols.length`;
#   * `symbols.length = ringSymbols.length + 1`, an off-by-one on the GUARD (not
#     on the list) -> residual `⊢ False`;
#   * forwarding `symbols.take (ringSymbols.length - 1)`, a length-relative
#     truncation rather than a literal `dropLast`;
#   * forwarding `symbols.take 1 ++ symbols.drop 1` — extensionally equal to
#     `symbols` but not syntactically, a probe of whether the spec is checking
#     the VALUE or the spelling: correctly leaves `⊢ exprFromDict d (List.take 1
#     symbols ++ symbols.drop 1) = exprFromDict d symbols`, i.e. the frozen
#     tactic body does not close it, so this one is a TACTIC gap of the same
#     family as the `symbols.length = 0` reshape below, NOT a spec hole;
#   * `symbols.length = 0` as the empty test together with rendering over
#     `ringSymbols` on the honored leg -> caught by E-honor.
# Correct reshapes probed and accepted: a `match`-on-list dispatch, a single
# conjoined reject-guard-first ladder, and echoing the transparent `asExprSpec`
# directly; the second pass added three more, all VERIFYING (exit 0) under the
# frozen tactic body — a `match symbols with | [] | s :: rest` dispatch, an
# `≠`-guard ladder that rejects first and renders in the `else`, and appending
# `[]` to each forwarded list. One correct reshape (`symbols.length = 0` in place of
# `symbols.isEmpty`) is NOT accepted by the frozen tactic body, which leaves the
# contradictory residual goal `symbols = [] → exprFromDict d [] = exprFromDict d
# ringSymbols` under `if_neg : ¬ringSymbols = []`; it closes once the tactic is
# strengthened (`... <;> (rintro rfl; cases ringSymbols <;> simp_all)`), so that
# is a TACTIC gap in the frozen proof script, not a spec-too-strong hole — the
# spec admits the reshape. Recorded here rather than shipped because a positive
# control may not retune the frozen tactic body.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (`exprFromDict` is `opaque` with no asserted `ensures` — an A-reference,
# mapping.md §3), so there is nothing there to probe.
AXIOM_TESTS = []

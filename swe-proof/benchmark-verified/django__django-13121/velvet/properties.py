"""properties.py — G-PBT falsification battery for django__django-13121 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method over four scalar/enum inputs:

  selectRenderer (native : Bool) (conn : Connector)
                 (lt rt : Option FieldTag) return (out : NodeKind)
    ensures out = dispatchNode native conn lt rt        -- THE load-bearing clause

There is NO ``require`` clause and NO ``axiom`` in this bundle. ``dispatchNode``
is a fully unfolded ``def`` in the ``pure`` region — a total function of the four
inputs, with no opaque answer key to echo. Its shape is a three-way selection:

  * when the backend lacks a native interval type AND the operands MIX an
    interval-typed operand with a differently-typed one, the interval renderer is
    selected (``isIntervalMix``: at least one operand carries the interval tag AND
    the two tags DIFFER — so two equal interval tags do NOT mix);
  * otherwise, when the connector is the difference of two EQUAL point-in-time
    tags, the point-in-time-difference renderer is selected (``conn = minus``,
    ``isTemporalTag lt``, ``lt = rt``);
  * otherwise the generic renderer is selected.

So the single ``ensures`` clause pins a decision over FOUR input binders
(``native``, ``conn``, ``lt``, ``rt``). ``dispatchNode`` decomposes into SIX
independent conjuncts across its two branch guards, and there is one rival per
conjunct, so no conjunct is left unattacked:

  interval branch: (1) the native-capability gate ``native = false``;
                   (2) the interval-tag MEMBERSHIP disjunct of ``isIntervalMix``;
                   (3) the tag-INEQUALITY conjunct ``lt ≠ rt`` of ``isIntervalMix``;
  temporal branch: (4) the difference-connector requirement ``conn = minus``;
                   (5) the point-in-time family membership ``isTemporalTag lt``;
                   (6) the equal-tags requirement ``lt = rt``.

Each rival below drops exactly one of the six and is refuted at a point in the
sub-domain that conjunct alone governs.

NAGINI -> VELVET NARROWING. The nagini sibling contracts TWO decision functions
(``select_arithmetic_path`` and ``operand_format_flag``). This Lean-family bundle
models only the renderer selection — the purely-functional core the fix's
F2P-observable behaviour turns on (mapping.md §1). ``operand_format_flag`` and
its two nagini rivals (``rival-literal-exemption``, ``rival-format-inverted``)
have NO counterpart here: the per-operand format decision is folded away as an
R-refinement of how a literal operand acquires its tag (mapping.md §1.1), not a
separately-contracted function. Omitting those two rivals is carrier narrowing,
not an evasion — see the accounting block at the foot of this file.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling would carry this class as
    MANDATORY where its inputs hold fractional heap permissions an impl can
    illegally overwrite; here (and in nagini) both functions take only
    pass-by-value primitives, so nagini itself records has_readonly_input=False.
    Lean and Velvet are referentially transparent: all four inputs are immutable
    values, there is no ``mut`` binder among the parameters, no heap and no
    aliasing — no read-only input to mutate and no substitute probe to build. Not
    fabricated (per the porting map this class is vacuous here).
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
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class: the post-image is a total,
    fully unfolded function of the method's own inputs (``dispatchNode`` and its
    helpers ``isIntervalMix``/``isTemporalTag`` are concrete ``def``s; the
    ``axioms`` region is empty), so there is no answer key to echo. Any WRONG
    constant fails the single ``ensures``, and ``pos-inlined-guards`` shows the
    converse — the clause is satisfied by an impl that recomputes the decision
    from scratch without naming those helpers at all, so it pins the DECISION
    rather than a reference to gold's own definitions. (No constant rival is
    shipped: it is strictly weaker than the six conjunct-precise rivals below,
    each of which is wrong on a narrow sub-domain and right everywhere else.)
  * PARTIAL-DOMAIN / VALUE — APPLIES: the nagini uniqueness rivals for
    ``select_arithmetic_path`` port directly onto the single ``ensures`` clause,
    each diverging from gold on the exact sub-domain its dropped guard governs.

WITNESS PLACEMENT. Each reject rival is refuted at a concrete input chosen so the
points together move all four binders across the modeled structure:
  * prepatch-mix-neq  — false / plus / (durationTag, durationTag): two EQUAL
    interval tags where the rival wrongly fires the interval branch;
  * drop-native-gate  — true  / plus / (durationTag, dateTimeTag): a native
    backend where the rival wrongly fires the interval branch anyway;
  * drop-diff-conn    — false / plus / (dateTag, dateTag): equal point-in-time
    tags but a NON-difference connector, where the rival wrongly fires temporal;
  * widen-temporal    — false / minus / (otherType, otherType): a non-temporal
    same-type difference, where the rival wrongly fires temporal;
  * drop-interval-tag — false / plus / (dateTag, dateTimeTag): two DIFFERING tags
    NEITHER of which is the interval tag, where the rival wrongly fires interval;
  * drop-equal-tags   — false / minus / (timeTag, none): a difference whose left
    operand is point-in-time but whose right tag does NOT match (it is
    unresolvable), where the rival wrongly fires temporal.
Each witness ELABORATES against its rival and FAILS against the frozen solution
(two real builds per case), so its sub-domain claim is machine-checked. No two
rivals are refuted at the same point (pts = 6), and the six points jointly move
``native`` across both values, ``conn`` across both connectors, and the tag pair
across equal/unequal, interval/point-in-time/other and ``some``/``none``.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY by ``dispatchNode``). There is no axiom-soundness / axiom-
containment obligation to probe here, and the gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-13121"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole straight-line body, lying wholly inside the
# ---- single impl region and unique in Solution.lean (both asserted by _swap). --
_IMPL = (
    "    let mut out := NodeKind.combined\n"
    "    if native = false ∧ isIntervalMix lt rt then\n"
    "      out := NodeKind.durationNode\n"
    "    else\n"
    "      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
    "        out := NodeKind.temporalNode\n"
    "      else\n"
    "        out := NodeKind.combined\n"
    "    return out\n"
)

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct selectRenderer by\n"
    "  loom_solve <;> simp only [dispatchNode] <;> split_ifs <;> simp_all\n"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `selectRendererTester native conn lt rt = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. There is no `require` clause, so
# ---- every input reaches the postcondition (no vacuous pass on an excluded one).
_TESTER = (
    "extract_program_for selectRenderer\n"
    "prove_precondition_decidable_for selectRenderer\n"
    "prove_postcondition_decidable_for selectRenderer\n"
    "derive_tester_for selectRenderer\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl: return
    # `dispatchNode` directly. The single `ensures` clause IS
    # `out = dispatchNode ...` and dispatchNode is a total, grounded function
    # of the four inputs (no opaque oracle), so returning it is a correct,
    # fully-grounded implementation, not an echo. MUST verify; else the
    # postcondition is over-fit to the accumulate-and-return SHAPE =>
    # SPEC-TOO-STRONG. The frozen tactic script still closes the (byte-identical)
    # obligation.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl("    return dispatchNode native conn lt rt\n"),
        "rationale": "clause `out = dispatchNode native conn lt rt` is pinned to a "
                     "total, grounded function of the four inputs, so directly "
                     "returning it is the honest cheapest CORRECT impl. A correct "
                     "reshape MUST verify, else SPEC-TOO-STRONG; it also shows the "
                     "spec is not echo-vulnerable (any WRONG constant fails it).",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — branch reorder. The temporal-difference
    # branch is tested BEFORE the interval-mix branch. The two branch guards are
    # MUTUALLY EXCLUSIVE (the temporal branch needs lt = rt while the interval
    # branch needs lt ≠ rt via isIntervalMix), so the reorder is semantically
    # identical to the frozen dispatch on every input. A structurally-different
    # but faithful impl MUST verify; else the postcondition is over-fit to the
    # gold branch ORDER => SPEC-TOO-STRONG. The tactic script is retuned (the
    # reorder changes the goal shape the frozen script was tuned to) but the
    # obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    let mut out := NodeKind.combined\n"
            "    if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "      out := NodeKind.temporalNode\n"
            "    else\n"
            "      if native = false ∧ isIntervalMix lt rt then\n"
            "        out := NodeKind.durationNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n",
            "prove_correct selectRenderer by\n"
            "  loom_solve <;> simp only [dispatchNode] <;> split_ifs <;> "
            "simp_all [isIntervalMix, isTemporalTag]\n"),
        "rationale": "the interval-mix and temporal-difference branch guards are "
                     "mutually exclusive (temporal needs lt = rt, interval needs "
                     "lt ≠ rt), so testing them in the opposite order is "
                     "semantically identical to the frozen dispatch. A faithful "
                     "reshape MUST verify; else the postcondition is over-fit to "
                     "the branch ORDER => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the point-in-time family membership tested
    # on the RIGHT operand instead of the left. Under the temporal branch's own
    # `lt = rt` conjunct the two spellings are interchangeable, so this is a
    # faithful correct reshape that MUST verify; else the postcondition is
    # over-fit to WHICH operand the family test names => SPEC-TOO-STRONG. The
    # reshape breaks the frozen `split_ifs`-based script (the equality has to be
    # used to rewrite the disjunction before it can close), so the tactic is
    # retuned to case-split the carriers exhaustively; the obligation statement
    # is byte-identical.
    # =====================================================================
    {
        "id": "pos-rt-family",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    let mut out := NodeKind.combined\n"
            "    if native = false ∧ isIntervalMix lt rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ isTemporalTag rt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n",
            "prove_correct selectRenderer by\n"
            "  loom_solve <;> simp only [dispatchNode, isTemporalTag, isIntervalMix] at * <;>\n"
            "    rcases lt with _ | lt <;> rcases rt with _ | rt <;>\n"
            "    cases conn <;> cases native <;> first\n"
            "      | (cases lt <;> cases rt <;> simp_all)\n"
            "      | (cases lt <;> simp_all)\n"
            "      | (cases rt <;> simp_all)\n"
            "      | simp_all\n"),
        "rationale": "the temporal branch also requires lt = rt, so testing the "
                     "point-in-time family on the RIGHT tag rather than the left "
                     "selects exactly the same renderer on every input. A faithful "
                     "reshape MUST verify; else the postcondition is over-fit to "
                     "which operand the family test names => SPEC-TOO-STRONG. This "
                     "defends the `isTemporalTag lt` conjunct against being pinned "
                     "more tightly than the behaviour it abstracts.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — both pure helpers INLINED and the
    # capability gate written as a negation of the positive Bool rather than an
    # equality against `false`. Nothing about the decision changes: this is the
    # same predicate spelled without the `def`s the spec's post-image uses. It
    # MUST verify, else the postcondition is over-fit to the impl REFERENCING
    # the very helpers the ensures clause is stated over — which would make the
    # positive controls above test only that gold's own definitions unfold.
    # =====================================================================
    {
        "id": "pos-inlined-guards",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    let mut out := NodeKind.combined\n"
            "    if ¬ native = true ∧ ((lt = some FieldTag.durationTag ∨ "
            "rt = some FieldTag.durationTag) ∧ ¬ (lt = rt)) then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ (lt = some FieldTag.dateTag ∨ "
            "lt = some FieldTag.dateTimeTag ∨ lt = some FieldTag.timeTag) ∧ rt = lt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n",
            "prove_correct selectRenderer by\n"
            "  loom_solve <;> simp only [dispatchNode, isIntervalMix, isTemporalTag] at * <;>\n"
            "    rcases lt with _ | lt <;> rcases rt with _ | rt <;>\n"
            "    cases conn <;> cases native <;> first\n"
            "      | (cases lt <;> cases rt <;> simp_all)\n"
            "      | (cases lt <;> simp_all)\n"
            "      | (cases rt <;> simp_all)\n"
            "      | simp_all\n"),
        "rationale": "spells both branch guards out by hand — the helper `def`s "
                     "inlined, the capability gate as `¬ native = true` instead of "
                     "`native = false`, the equality flipped to `rt = lt` — so the "
                     "impl shares NO syntax with the post-image it must equal. A "
                     "faithful reshape MUST verify; else the clause is satisfiable "
                     "only by an impl that literally names gold's own helpers, and "
                     "the other positives would be testing definitional unfolding "
                     "rather than the decision => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling self-calls on the F2P-shaped input to
    # establish the modeled behaviour is ADMITTED. This bundle has no `require`
    # clause (nothing can be PRECOND-TOO-STRONG), so the probe is expressed as an
    # in-region assertion that the F2P-shaped configuration (a non-native backend,
    # a difference connector, two EQUAL point-in-time tags — the bare temporal
    # subtraction the issue is about) classifies as the temporal-difference node,
    # i.e. the post-image is non-degenerate there. The assert is LIVE (replacing
    # the claimed kind with a wrong one leaves an unsolved goal); the frozen body
    # follows it so the `ensures` obligation still discharges. The tactic script
    # is retuned only to also close the added assertion goal.
    # =====================================================================
    {
        "id": "admiss-f2p-temporal-diff",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    assert (with_name_prefix `admiss\n"
            "      (dispatchNode false Connector.minus "
            "(some FieldTag.dateTimeTag) (some FieldTag.dateTimeTag)\n"
            "        = NodeKind.temporalNode))\n"
            + _IMPL,
            "prove_correct selectRenderer by\n"
            "  loom_solve <;> simp only [dispatchNode] <;> split_ifs <;> "
            "simp_all [isIntervalMix, isTemporalTag]\n"),
        "rationale": "the F2P-shaped configuration (non-native backend, difference "
                     "connector, two EQUAL point-in-time tags) classifies as the "
                     "point-in-time-difference node — the exact behaviour the "
                     "failing tests exercise. The in-region assert is live (a wrong "
                     "claimed kind leaves an unsolved goal) and the frozen body "
                     "keeps the ensures obligation intact, so the module verifies; "
                     "this witnesses the spec ADMITS the modeled F2P behaviour "
                     "rather than being vacuous or over-strong there.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "rival-prepatch-mix-neq",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the tag-inequality requirement of the interval-mix predicate: EITHER
        # operand carrying the interval tag now routes to the interval renderer,
        # including two EQUAL interval-tag operands (gold leaves those generic).
        # This is exactly the PRE-PATCH interval guard.
        "module": _with_impl(
            "    let mut out := NodeKind.combined\n"
            "    if native = false ∧ "
            "(lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "drops the tag-inequality conjunct so EITHER side being an "
                      "interval routes to the interval renderer — exactly the "
                      "pre-patch guard. Its faithful real patch is the unchanged "
                      "pre-patch renderer-selection head, which routes an "
                      "interval+interval-literal arithmetic (both interval-typed) "
                      "through the specialised interval renderer and so re-raises "
                      "the mixed-types arithmetic error on the F2P scenario — it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = dispatchNode ...`: on two EQUAL "
                     "interval-tag operands the selection is generic (isIntervalMix "
                     "is false because the tags are equal), but the rival returns "
                     "the interval renderer. Refuted at the equal-interval "
                     "sub-domain (lt = rt = durationTag, non-native), where this "
                     "rival diverges from gold while agreeing on every "
                     "differing-tag input. If it verified => SPEC-TOO-WEAK (admits "
                     "the very bug the patch fixes).",
        "witness": _TESTER +
                   "example : selectRendererTester false Connector.plus "
                   "(some FieldTag.durationTag) (some FieldTag.durationTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-drop-native-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `native = false` capability gate: a mixed interval/non-interval
        # pairing routes to the interval renderer even on a backend that exposes a
        # native interval type (gold leaves those to the generic renderer).
        "module": _with_impl(
            "    let mut out := NodeKind.combined\n"
            "    if isIntervalMix lt rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "removes the native-capability conjunct from the interval "
                      "guard, routing a mixed interval+point-in-time pairing to the "
                      "interval renderer even on a native-interval backend. Its "
                      "faithful real patch drops the native-capability check, so on "
                      "a native-interval backend a mixed interval arithmetic wrongly "
                      "routes to the interval renderer instead of the generic "
                      "combination, changing rendered SQL on the native-backend "
                      "scenarios the differential suite exercises — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = dispatchNode ...`: on a native backend the "
                     "interval branch is disabled (native = false is false), so a "
                     "mixed interval/point-in-time pairing is generic, but the rival "
                     "returns the interval renderer. Refuted at the native "
                     "sub-domain (native = true, mixed durationTag/dateTimeTag), "
                     "which VARIES the native binder that every other witness holds "
                     "at false. If it verified => SPEC-TOO-WEAK (the native gate is "
                     "unconstrained).",
        "witness": _TESTER +
                   "example : selectRendererTester true Connector.plus "
                   "(some FieldTag.durationTag) (some FieldTag.dateTimeTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-drop-difference-connector",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the difference-connector requirement on the temporal branch: a
        # NON-difference combination of two equal point-in-time tags now routes to
        # the point-in-time-difference renderer (gold requires the difference
        # connector).
        "module": _with_impl(
            "    let mut out := NodeKind.combined\n"
            "    if native = false ∧ isIntervalMix lt rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if isTemporalTag lt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "removes the difference-connector conjunct from the temporal "
                      "guard, so same-type point-in-time operands route to the "
                      "point-in-time-difference renderer for ANY connector. Its "
                      "faithful real patch drops the difference-connector check, so "
                      "a same-type point-in-time ADDITION (or any non-difference "
                      "combination) wrongly routes through the difference renderer "
                      "instead of the generic combination, corrupting that rendered "
                      "SQL across the differential suite — it would NOT resolve.",
        "rationale": "REJECT from `out = dispatchNode ...`: with a non-difference "
                     "connector the selection is generic even for two equal "
                     "point-in-time tags (the temporal branch requires conn = "
                     "minus), but the rival returns the difference renderer. Refuted "
                     "at the non-difference sub-domain (conn = plus, "
                     "dateTag/dateTag), which VARIES the conn binder against the "
                     "frozen difference value. If it verified => SPEC-TOO-WEAK (the "
                     "difference gate is unconstrained).",
        "witness": _TESTER +
                   "example : selectRendererTester false Connector.plus "
                   "(some FieldTag.dateTag) (some FieldTag.dateTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-widen-temporal-family",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the point-in-time family membership on the temporal branch: ANY
        # same-type difference (incl. non-point-in-time tags like otherType) routes
        # to the point-in-time-difference renderer (gold restricts it to the three
        # point-in-time tags).
        "module": _with_impl(
            "    let mut out := NodeKind.combined\n"
            "    if native = false ∧ isIntervalMix lt rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "replaces the point-in-time family membership with a bare "
                      "same-type test, so ANY same-type difference (incl. "
                      "non-point-in-time tags like a plain numeric type) routes to "
                      "the point-in-time-difference renderer. Its faithful real "
                      "patch drops the point-in-time family membership, so a plain "
                      "numeric same-type subtraction wrongly routes through the "
                      "difference renderer instead of the generic combination, "
                      "corrupting ordinary numeric-subtraction SQL across the "
                      "differential suite — it would NOT resolve.",
        "rationale": "REJECT from `out = dispatchNode ...`: on a non-point-in-time "
                     "same-type difference the selection is generic (isTemporalTag "
                     "is false), but the rival returns the difference renderer. "
                     "Refuted at the non-point-in-time sub-domain (conn = minus, "
                     "otherType/otherType), where this rival diverges from gold "
                     "while agreeing on every point-in-time difference. If it "
                     "verified => SPEC-TOO-WEAK (the point-in-time family is "
                     "unconstrained).",
        "witness": _TESTER +
                   "example : selectRendererTester false Connector.minus "
                   "(some FieldTag.otherType) (some FieldTag.otherType) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-drop-interval-tag-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the interval-tag MEMBERSHIP disjunct of the interval-mix predicate,
        # keeping only the tag-inequality conjunct: ANY two differing tags now
        # route to the interval renderer on a non-native backend, even when
        # NEITHER operand is interval-typed (gold requires at least one to be).
        "module": _with_impl(
            "    let mut out := NodeKind.combined\n"
            "    if native = false ∧ lt ≠ rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "keeps the tag-inequality conjunct but drops the requirement "
                      "that at least one operand actually be interval-typed, so on "
                      "a backend without a native interval type EVERY pairing of two "
                      "differently-typed operands routes to the specialised interval "
                      "renderer. Its faithful real patch widens the interval guard to "
                      "any type mismatch, so an ordinary heterogeneous arithmetic "
                      "with no interval operand at all is handed to the interval "
                      "renderer instead of the generic combination — corrupting that "
                      "rendered SQL wholesale on the non-native backends the "
                      "differential suite exercises. It would NOT resolve.",
        "rationale": "REJECT from `out = dispatchNode ...`: when neither tag is the "
                     "interval tag the selection is generic (isIntervalMix needs the "
                     "membership disjunct as well as the inequality), but the rival "
                     "returns the interval renderer. Refuted at the "
                     "no-interval-operand sub-domain (non-native, differing "
                     "point-in-time tags dateTag/dateTimeTag), which is the ONE "
                     "conjunct of isIntervalMix the equal-interval rival above "
                     "leaves untouched — that rival drops the inequality, this one "
                     "drops the membership. If it verified => SPEC-TOO-WEAK (the "
                     "interval-tag membership is unconstrained).",
        "witness": _TESTER +
                   "example : selectRendererTester false Connector.plus "
                   "(some FieldTag.dateTag) (some FieldTag.dateTimeTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-drop-equal-tags",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the equal-tags requirement of the temporal branch: a difference
        # whose LEFT operand is point-in-time now routes to the
        # point-in-time-difference renderer whatever the right operand is (gold
        # requires the two tags to match).
        "module": _with_impl(
            "    let mut out := NodeKind.combined\n"
            "    if native = false ∧ isIntervalMix lt rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ isTemporalTag lt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "drops the equal-tags conjunct from the temporal guard, so a "
                      "difference is handed to the point-in-time-difference renderer "
                      "on the strength of the LEFT operand's tag alone. Its faithful "
                      "real patch stops comparing the two operand types, so "
                      "subtracting a differently-typed (or type-unresolvable) "
                      "operand from a point-in-time one is rendered as a "
                      "point-in-time difference instead of the generic combination "
                      "— a mis-render on every mixed subtraction the differential "
                      "suite covers. It would NOT resolve.",
        "rationale": "REJECT from `out = dispatchNode ...`: a difference whose two "
                     "tags DIFFER is generic (the temporal branch requires lt = rt), "
                     "but the rival returns the difference renderer whenever the "
                     "left tag is point-in-time. Refuted at the mismatched-tag "
                     "difference sub-domain (conn = minus, lt = timeTag, "
                     "rt = none) — the only witness point in the battery that "
                     "exercises an UNRESOLVABLE operand tag, i.e. the `none` "
                     "inhabitant of the Option carrier. If it verified => "
                     "SPEC-TOO-WEAK (the equal-tags conjunct is unconstrained).",
        "witness": _TESTER +
                   "example : selectRendererTester false Connector.minus "
                   "(some FieldTag.timeTag) none = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) + 3 AXIOM_TESTS entries. It
# contracts TWO functions; this Lean-family bundle models only the renderer
# selection (`select_arithmetic_path` -> `selectRenderer`), so the port is a
# narrowed re-expression onto the one `ensures` clause.
#
#   sibling case                       -> here
#   ------------------------------------------------------------------------
#   pos-control-path-single-return     -> pos-direct + pos-reorder        PORTED (2 shapes)
#                                         + pos-rt-family                ADDED (audit)
#                                         + pos-inlined-guards           ADDED (audit)
#   pos-control-format-inverted-test   -> (none)                          OMITTED (unmodeled fn)
#   admiss-self-calls                  -> admiss-f2p-temporal-diff        PORTED (reshaped)
#   rival-prepatch-dur-dur             -> rival-prepatch-mix-neq          PORTED
#   rival-drop-native-gate             -> rival-drop-native-gate          PORTED
#   rival-drop-subtract-gate           -> rival-drop-difference-connector PORTED
#   rival-widen-temporal-family        -> rival-widen-temporal-family     PORTED
#   rival-literal-exemption            -> (none)                          OMITTED (unmodeled fn)
#   rival-format-inverted              -> (none)                          OMITTED (unmodeled fn)
#   (no sibling counterpart)           -> rival-drop-interval-tag-membership  ADDED (audit)
#   (no sibling counterpart)           -> rival-drop-equal-tags               ADDED (audit)
#   (nagini has no frame-mutation case) -> (none)                         VACUOUS class
#   ax-* (3 entries)                   -> (dropped)                       AXIOM LANE
#
# ADDED BY AUDIT (4 cases; the port was a faithful 1:1 port of the sibling and
#   inherited the sibling's coverage shape, which does not decompose this
#   carrier's `ensures` clause conjunct-by-conjunct):
#   * rival-drop-interval-tag-membership and rival-drop-equal-tags close the two
#     conjuncts of `dispatchNode` that the four ported rivals left unattacked.
#     The nagini sibling has no counterpart for either, because its `ensures` is
#     a set of one-directional Implies pins rather than a single equation: its
#     DURATION pin fires only when a duration operand is present, so a rival that
#     widens the guard to any type mismatch violates its PLAIN pin only, and the
#     sibling's rival set happens not to include it. Here the clause is an
#     EQUATION over the whole domain, so both conjuncts are independently
#     attackable and both are now attacked. Each was built and measured: the
#     rival is rejected under the FROZEN tactic script, and its witness
#     elaborates against the rival while failing on the frozen solution with a
#     semantic refutation (`decide` proving the tester equation false at the
#     stated input), not a name/type/unfolding error.
#   * pos-rt-family and pos-inlined-guards close the SPEC-TOO-STRONG direction.
#     The two ported positives both keep gold's own helper `def`s and its guard
#     spelling, so neither shows the clause admits an impl that computes the
#     decision WITHOUT naming the definitions the postcondition is stated over.
#     Both were measured to verify (with retuned tactic scripts; the statements
#     are byte-identical), so the clause is not over-fit to gold's syntax.
#
# OMITTED (operand_format_flag and its two rivals rival-literal-exemption,
#   rival-format-inverted): the nagini sibling contracts a SECOND function, the
#   per-operand format decision. This bundle does not model it — the format
#   decision is folded away as an R-refinement of how a literal interval operand
#   acquires its type tag (mapping.md §1.1), captured by the `lt`/`rt` INPUT to
#   selectRenderer rather than a separately-contracted function. There is no
#   `ensures` clause here those two rivals could attack, so they have no
#   counterpart. This is carrier narrowing (the Lean-family bundle models only the
#   purely-functional renderer-selection core), NOT an omission for difficulty:
#   the nagini G-DIFF #2 (the literal-exemption bug) is an unmodeled behaviour on
#   this carrier, so it is a known gap in the modeled surface, not a dropped case.
# PORTED (positives): the nagini single-return positive is split into two
#   genuinely different correct shapes here — a single-return `dispatchNode` form
#   (pos-direct) and a branch REORDER (pos-reorder, temporal tested before
#   interval; the two guards are mutually exclusive so the reorder is
#   semantically identical). Both, however, still spell the guards using gold's
#   own `isIntervalMix`/`isTemporalTag` helpers, which is why the audit added
#   pos-rt-family (family test moved to the other operand — sound under the
#   branch's own `lt = rt`) and pos-inlined-guards (both helpers inlined, the
#   capability gate written as a negation, the equality flipped). The four
#   together defend the obligation against over-fit to shape, to branch order, to
#   which operand the family test names, and to the impl referencing the
#   definitions the clause is stated over.
# PORTED (admissibility, reshaped): the nagini sibling establishes the
#   precondition ADMITS the F2P input via self-calls. This bundle has NO `require`
#   clause, so there is no precondition to be too-strong; the argument is carried
#   instead by an in-region assertion that the F2P-shaped configuration
#   (non-native, difference connector, two equal point-in-time tags) classifies as
#   the point-in-time-difference node (the post-image is non-degenerate there).
#   The assert is live and the frozen `ensures` obligation still discharges.
# VACUOUS (frame-mutation): referentially-transparent backend, no `mut`
#   parameter, no heap — no read-only input to overwrite. Nagini itself records
#   has_readonly_input=False (both functions take only pass-by-value primitives),
#   so this class is vacuous in nagini AND here. Not fabricated.
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
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
# PORTED (the four path rivals) + ADDED (two more): the nagini uniqueness rivals
#   for select_arithmetic_path port directly onto the single
#   `out = dispatchNode ...` clause; the audit added the two rivals needed to
#   reach one-per-conjunct. Each of the SIX carries a machine-checked witness that
#   ELABORATES against the rival and FAILS against the frozen solution (two real
#   builds per case, and on gold the failure is `decide` proving the tester
#   equation FALSE at the stated input — a semantic refutation, not a missing
#   identifier or an unfolding gap). The six witness points are an equal-interval
#   pair (lt = rt = durationTag, non-native), a native backend (native = true), a
#   non-difference connector (conn = plus), a non-point-in-time same-type
#   difference (conn = minus, otherType), a differing pair with NO interval
#   operand (dateTag/dateTimeTag), and a difference against an UNRESOLVABLE right
#   tag (timeTag/none). So both `native` values, both connectors, equal and
#   unequal tag pairs, all three tag families and both Option inhabitants are
#   exercised, and no rival is refuted at the same point as another (pts = 6).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the selection is modeled deeply by dispatchNode; mapping.md §3 notes
# there is no axiom_check.py / no A-reference for this bundle), so there is
# nothing to probe.
AXIOM_TESTS = []

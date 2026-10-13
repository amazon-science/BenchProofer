"""properties.py — G-PBT falsification battery for django__django-13128 (velvet).

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

  resolveCombined (selfKind : NodeKind) (conn : Connector)
                  (lt rt : Option FieldTag) return (out : NodeKind)
    ensures out = dispatchKind selfKind conn lt rt      -- THE load-bearing clause

There is NO ``require`` clause and NO ``axiom`` in this bundle. ``dispatchKind``
is a fully unfolded ``def`` in the ``pure`` region — a total function of the four
inputs, with no opaque answer key to echo. Its shape is a three-way selection:

  * a receiver that is already one of the specialised kinds keeps its kind
    (the ``selfKind ≠ combined`` guard);
  * otherwise a generic receiver becomes the interval node when exactly one
    operand carries the interval tag and the two tags differ (``isIntervalMix``);
  * otherwise it becomes the temporal-difference node when the connector is the
    difference of two EQUAL point-in-time tags (``conn = minus``, ``isTemporalTag``,
    ``lt = rt``);
  * otherwise it stays generic.

So the single ``ensures`` clause pins a decision over FOUR input binders
(``selfKind``, ``conn``, ``lt``, ``rt``), and each rival below abuses a distinct
one: the interval branch's tag-inequality requirement, the already-specialised
guard, the difference-connector requirement, the temporal branch's EQUAL-tags
requirement, and the whole selection at once.

The temporal branch is a THREE-conjunct guard (``conn = minus`` ∧
``isTemporalTag lt`` ∧ ``lt = rt``), so it needs more than one rival: dropping
each conjunct diverges from gold on a DIFFERENT sub-domain, and a battery that
attacks only one of them leaves the other two unpinned by any machine-checked
counterexample. Two of the three are attacked below (the difference connector and
the equal-tags requirement); the third (``isTemporalTag``) is covered by the
none/none point re-derived during audit.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this class as MANDATORY
    because its inputs hold fractional heap permissions an impl can illegally
    overwrite. Lean and Velvet are referentially transparent: all four inputs are
    immutable values, there is no ``mut`` binder among the parameters, no heap and
    no aliasing — so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated (per the porting map this class is vacuous here).
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
    fully unfolded function of the method's own inputs (``dispatchKind`` and its
    helpers ``isIntervalMix``/``isTemporalTag`` are concrete ``def``s; the
    ``axioms`` region is empty), so there is no answer key to echo. Any WRONG
    constant/echo fails the single ``ensures`` — demonstrated by the const rival.
  * PARTIAL-DOMAIN / VALUE — APPLIES: the nagini uniqueness rivals port directly
    onto the single ``ensures`` clause, each diverging from gold on the exact
    sub-domain its dropped guard governs.

WITNESS PLACEMENT. Each reject rival is refuted at a concrete input chosen so
the four points together move all four binders across the modeled structure:
  * neq-guard  — combined / plus / (durationTag, durationTag): two EQUAL interval
    tags, where the rival wrongly fires the interval branch;
  * iat-guard  — durationNode / minus / (dateTag, dateTag): an ALREADY-specialised
    receiver, where the rival re-classifies instead of keeping the kind;
  * sub-req    — combined / plus / (dateTag, dateTag): equal point-in-time tags but
    a NON-difference connector, where the rival wrongly fires the temporal branch;
  * equal-tags — combined / minus / (dateTag, dateTimeTag): a difference of two
    DIFFERING point-in-time tags, where the rival wrongly fires the temporal
    branch (the only point that moves lt and rt to two distinct temporal tags);
  * const      — combined / minus / (dateTimeTag, dateTimeTag): the F2P shape,
    where gold selects the temporal node and the rival stays generic.
Each witness ELABORATES against its rival and FAILS against the frozen solution
(two real builds per case), so its sub-domain claim is machine-checked. No two
rivals are refuted at the same point.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY by ``dispatchKind``). There is no axiom-soundness / axiom-
containment obligation to probe here, and the gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-13128"
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
    "    let mut out := selfKind\n"
    "    if selfKind = NodeKind.combined then\n"
    "      if isIntervalMix lt rt then\n"
    "        out := NodeKind.durationNode\n"
    "      else\n"
    "        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
    "          out := NodeKind.temporalNode\n"
    "        else\n"
    "          out := NodeKind.combined\n"
    "    return out\n"
)

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct resolveCombined by\n"
    "  loom_solve <;> simp_all [dispatchKind]\n"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `resolveCombinedTester selfKind conn lt rt = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. There is no `require` clause, so
# ---- every input reaches the postcondition (no vacuous pass on an excluded one).
_TESTER = (
    "extract_program_for resolveCombined\n"
    "prove_precondition_decidable_for resolveCombined\n"
    "prove_postcondition_decidable_for resolveCombined\n"
    "derive_tester_for resolveCombined\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl: return
    # `dispatchKind` directly. The single `ensures` clause IS
    # `out = dispatchKind ...` and dispatchKind is a total, grounded function
    # of the four inputs (no opaque oracle), so returning it is a correct,
    # fully-grounded implementation, not an echo. MUST verify; else the
    # postcondition is over-fit to the early-return SHAPE => SPEC-TOO-STRONG.
    # The frozen tactic script still closes the (byte-identical) obligation.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl("    return dispatchKind selfKind conn lt rt\n"),
        "rationale": "clause `out = dispatchKind selfKind conn lt rt` is pinned to "
                     "a total, grounded function of the four inputs, so directly "
                     "returning it is the honest cheapest CORRECT impl. A correct "
                     "reshape MUST verify, else SPEC-TOO-STRONG; it also shows the "
                     "spec is not echo-vulnerable (any WRONG constant fails it).",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — branch reorder. The temporal-difference
    # branch is tested BEFORE the interval-mix branch. The two branch guards
    # are MUTUALLY EXCLUSIVE (the temporal branch needs lt = rt while the
    # interval branch needs lt ≠ rt), so the reorder is semantically identical
    # to the frozen dispatch on every input. A structurally-different but
    # faithful impl MUST verify; else the postcondition is over-fit to the gold
    # branch ORDER => SPEC-TOO-STRONG. The tactic script is retuned (the reorder
    # changes the goal shape the frozen `simp_all` was tuned to) but the
    # obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    let mut out := selfKind\n"
            "    if selfKind = NodeKind.combined then\n"
            "      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        if isIntervalMix lt rt then\n"
            "          out := NodeKind.durationNode\n"
            "        else\n"
            "          out := NodeKind.combined\n"
            "    return out\n",
            "prove_correct resolveCombined by\n"
            "  loom_solve <;> "
            "simp_all [dispatchKind, isIntervalMix, isTemporalTag] <;> grind\n"),
        "rationale": "the interval-mix and temporal-difference branch guards are "
                     "mutually exclusive (temporal needs lt = rt, interval needs "
                     "lt ≠ rt), so testing them in the opposite order is "
                     "semantically identical to the frozen dispatch. A faithful "
                     "reshape MUST verify; else the postcondition is over-fit to "
                     "the branch ORDER => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — data-flow reshape. Each guard is bound to
    # its own immutable local FIRST and the kind is then selected by a pure
    # `let` ladder: no `mut` accumulation, single binding, single return. This is
    # a genuinely different DATA FLOW from the frozen body (which mutates an
    # accumulator through nested `if`s), so it probes whether the postcondition
    # is over-fit to the mutable-accumulator SHAPE. MUST verify; else
    # SPEC-TOO-STRONG. Tactic script retuned (the ladder changes the goal shape);
    # the obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "pos-local-predicates",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    let specialised := selfKind ≠ NodeKind.combined\n"
            "    let wantsInterval := isIntervalMix lt rt\n"
            "    let wantsTemporal := conn = Connector.minus ∧ isTemporalTag lt "
            "∧ lt = rt\n"
            "    let out := if specialised then selfKind\n"
            "      else if wantsInterval then NodeKind.durationNode\n"
            "      else if wantsTemporal then NodeKind.temporalNode\n"
            "      else NodeKind.combined\n"
            "    return out\n",
            "prove_correct resolveCombined by\n"
            "  loom_solve <;> "
            "simp_all [dispatchKind, isIntervalMix, isTemporalTag] <;> grind\n"),
        "rationale": "data-flow reshape: bind each guard to its own immutable "
                     "local and select the kind through a pure `let` ladder, "
                     "instead of mutating an accumulator through nested `if`s. "
                     "Same logical selection, different data flow. MUST verify; "
                     "else the postcondition is over-fit to the mutable-"
                     "accumulator SHAPE => SPEC-TOO-STRONG. Complements "
                     "pos-reorder (control-flow reshape) and pos-direct (the "
                     "single-call form).",
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling self-calls on the F2P-shaped input to
    # establish the modeled behaviour is ADMITTED. This bundle has no `require`
    # clause (nothing can be PRECOND-TOO-STRONG), so the probe is expressed as
    # an in-region assertion that the F2P-shaped configuration (a generic
    # difference of two EQUAL DateTimeField operands — the bare datetime
    # subtraction the issue is about) classifies as the temporal-difference
    # node, i.e. the post-image is non-degenerate there. The assert is LIVE:
    # replacing the claimed kind with the generic one makes the module FAIL to
    # build, with `decide` reporting the claimed equation false (re-measured by
    # a real build during audit); the frozen body follows it so the `ensures`
    # obligation still discharges. The tactic script is retuned only to also
    # close the added assertion goal.
    # =====================================================================
    {
        "id": "admiss-f2p-datetime-diff",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    assert (with_name_prefix `admiss\n"
            "      (dispatchKind NodeKind.combined Connector.minus "
            "(some FieldTag.dateTimeTag) (some FieldTag.dateTimeTag)\n"
            "        = NodeKind.temporalNode))\n"
            + _IMPL,
            "prove_correct resolveCombined by\n"
            "  loom_solve <;> simp_all [dispatchKind] <;> decide\n"),
        "rationale": "the F2P-shaped configuration (generic receiver, difference "
                     "connector, two EQUAL point-in-time tags) classifies as the "
                     "temporal-difference node — the exact behaviour the failing "
                     "tests exercise. The in-region assert is live (a wrong claimed "
                     "kind leaves an unsolved goal) and the frozen body keeps the "
                     "ensures obligation intact, so the module verifies; this "
                     "witnesses the spec ADMITS the modeled F2P behaviour rather "
                     "than being vacuous or over-strong there.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-drop-interval-neq-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the tag-inequality requirement on the interval branch: ANY
        # operand carrying the interval tag now dispatches to the interval node,
        # including two EQUAL interval-tag operands (gold keeps those generic).
        "module": _with_impl(
            "    let mut out := selfKind\n"
            "    if selfKind = NodeKind.combined then\n"
            "      if lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag then\n"
            "        out := NodeKind.durationNode\n"
            "      else\n"
            "        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "          out := NodeKind.temporalNode\n"
            "        else\n"
            "          out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "dropping the tag-inequality requirement makes the real "
                      "patch wrap a same-type interval arithmetic (two interval "
                      "operands of EQUAL type) in the specialised interval node. "
                      "The gold selection requires the two operand tags to DIFFER, "
                      "leaving equal-interval operands a generic node; wrapping "
                      "them would emit the mixed interval-arithmetic form for a "
                      "plain interval result and diverge from the gold dispatch "
                      "(which G-CONF differential-tests against the real callee), "
                      "so it would NOT resolve.",
        "rationale": "REJECT from `out = dispatchKind ...`: on two EQUAL "
                     "interval-tag operands the selection is generic (isIntervalMix "
                     "is false because the tags are equal), but the rival returns "
                     "the interval node. Refuted at the equal-interval sub-domain "
                     "(binder pair lt = rt = durationTag), where this rival diverges "
                     "from gold while agreeing on every differing-tag input.",
        "witness": _TESTER +
                   "example : resolveCombinedTester NodeKind.combined Connector.plus "
                   "(some FieldTag.durationTag) (some FieldTag.durationTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-drop-already-specialised-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `selfKind = combined` guard: an already-specialised receiver
        # is now re-classified by the operand tags instead of keeping its kind.
        "module": _with_impl(
            "    let mut out := selfKind\n"
            "    if isIntervalMix lt rt then\n"
            "      out := NodeKind.durationNode\n"
            "    else\n"
            "      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then\n"
            "        out := NodeKind.temporalNode\n"
            "      else\n"
            "        out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "dropping the already-specialised guard makes the real patch "
                      "RE-classify a receiver that is already a specialised node "
                      "when it re-resolves itself: it would re-enter the selection "
                      "and re-wrap, contradicting the guard whose whole purpose is "
                      "to stop the recursive resolution from re-wrapping an "
                      "already-specialised expression. A faithful patch without it "
                      "recurses/re-wraps and does not match the gold dispatch, so "
                      "it would NOT resolve.",
        "rationale": "REJECT from `out = dispatchKind ...`: on an already-"
                     "specialised receiver (selfKind ≠ combined) the selection "
                     "keeps that kind, but the rival re-derives from the tags. "
                     "Refuted at an already-specialised receiver that is a "
                     "difference of two equal point-in-time tags (selfKind = "
                     "durationNode, minus, dateTag/dateTag), where gold returns "
                     "durationNode and the rival returns temporalNode. This point "
                     "varies the selfKind binder, which every other witness holds "
                     "at combined.",
        "witness": _TESTER +
                   "example : resolveCombinedTester NodeKind.durationNode Connector.minus "
                   "(some FieldTag.dateTag) (some FieldTag.dateTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-drop-difference-connector",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the difference-connector requirement on the temporal branch: a
        # NON-difference connector of two equal point-in-time tags now dispatches
        # to the temporal node (gold requires the difference connector).
        "module": _with_impl(
            "    let mut out := selfKind\n"
            "    if selfKind = NodeKind.combined then\n"
            "      if isIntervalMix lt rt then\n"
            "        out := NodeKind.durationNode\n"
            "      else\n"
            "        if isTemporalTag lt ∧ lt = rt then\n"
            "          out := NodeKind.temporalNode\n"
            "        else\n"
            "          out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "dropping the difference-connector requirement makes the "
                      "real patch wrap a NON-difference combination of two equal "
                      "point-in-time operands (e.g. an addition of two dates) in "
                      "the temporal-difference node. The gold selection only "
                      "produces that node for the difference connector; wrapping a "
                      "non-difference combination would emit difference SQL for a "
                      "non-difference operation and diverge from gold, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = dispatchKind ...`: with a non-difference "
                     "connector the selection is generic even for two equal "
                     "point-in-time tags (the temporal branch requires conn = "
                     "minus), but the rival returns the temporal node. Refuted at "
                     "the non-difference sub-domain (conn = plus, dateTag/dateTag), "
                     "which varies the conn binder against the frozen difference "
                     "value.",
        "witness": _TESTER +
                   "example : resolveCombinedTester NodeKind.combined Connector.plus "
                   "(some FieldTag.dateTag) (some FieldTag.dateTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-drop-equal-tags-requirement",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the EQUAL-tags requirement from the temporal branch: a difference
        # of two DIFFERING point-in-time tags now dispatches to the temporal
        # node. The other temporal-branch rival drops the connector conjunct
        # instead, so this is the only case that pins THIS conjunct.
        "module": _with_impl(
            "    let mut out := selfKind\n"
            "    if selfKind = NodeKind.combined then\n"
            "      if isIntervalMix lt rt then\n"
            "        out := NodeKind.durationNode\n"
            "      else\n"
            "        if conn = Connector.minus ∧ isTemporalTag lt then\n"
            "          out := NodeKind.temporalNode\n"
            "        else\n"
            "          out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "dropping the equal-tags requirement makes the real patch "
                      "wrap a difference of two DIFFERENT point-in-time operand "
                      "types (e.g. a date minus a time-of-day) in the "
                      "specialised difference node. The gold selection produces "
                      "that node only when the two operand tags are EQUAL, "
                      "because only then is the difference a well-defined "
                      "interval; wrapping a mismatched pair would claim an "
                      "interval result for a combination whose operand types do "
                      "not agree and diverge from the gold dispatch (which "
                      "G-CONF differential-tests against the real callee), so it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = dispatchKind ...`: on a difference of "
                     "two DIFFERING point-in-time tags the selection is generic "
                     "(the temporal branch requires lt = rt, and isIntervalMix "
                     "is false because neither tag is the interval tag), but the "
                     "rival returns the temporal node. Refuted at the "
                     "differing-temporal-tags sub-domain (lt = dateTag, "
                     "rt = dateTimeTag) — the only witness point that drives lt "
                     "and rt to two DISTINCT point-in-time tags, which every "
                     "other case holds equal or interval-tagged.",
        "witness": _TESTER +
                   "example : resolveCombinedTester NodeKind.combined Connector.minus "
                   "(some FieldTag.dateTag) (some FieldTag.dateTimeTag) = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-const-generic-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant generic node — exactly the pre-patch behaviour (no resolve-
        # time re-classification). Fails the ensures on every interval/temporal
        # case. Cheap supporting baseline, still a real refinement.
        "module": _with_impl(
            "    let out := NodeKind.combined\n"
            "    return out\n"),
        "refinement": "returning the generic node unconditionally is the pre-patch "
                      "behaviour: no resolve-time re-classification happens, so a "
                      "bare temporal subtraction is never specialised and its "
                      "output type never resolves — the mixed-types error the issue "
                      "reports is still raised and every failing test still fails. "
                      "It would NOT resolve (this is the same failure recorded for "
                      "the prepatch skeleton).",
        "rationale": "REJECT from `out = dispatchKind ...`: on the F2P shape (a "
                     "generic difference of two equal point-in-time tags) the "
                     "selection is the temporal-difference node, but the rival "
                     "returns generic. Refuted at that F2P input (combined, minus, "
                     "dateTimeTag/dateTimeTag) — the exact bare datetime "
                     "subtraction the issue is about.",
        "witness": _TESTER +
                   "example : resolveCombinedTester NodeKind.combined Connector.minus "
                   "(some FieldTag.dateTimeTag) (some FieldTag.dateTimeTag) = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (3 soundness
# positives, 1 admissibility, 4 uniqueness rivals) + 1 AXIOM_TESTS entry. This
# bundle models the SAME single behaviour (the resolve-time node-kind selection),
# so the port is a near-parity re-expression onto the one `ensures` clause.
#
#   sibling case                       -> here
#   ------------------------------------------------------------------------
#   pos-control-reorder                -> pos-reorder                     PORTED
#   pos-control-direct                 -> pos-direct                      PORTED
#   pos-control-local-predicates       -> pos-local-predicates            PORTED
#   admiss-f2p-datetime-sub            -> admiss-f2p-datetime-diff        PORTED (reshaped)
#   weak-drop-duration-neq-guard       -> weak-drop-interval-neq-guard    PORTED
#   weak-drop-already-temporal-guard   -> weak-drop-already-specialised-guard PORTED
#   weak-drop-sub-requirement          -> weak-drop-difference-connector  PORTED
#   (no sibling case)                  -> weak-drop-equal-tags-requirement ADDED
#   weak-const-plain-prepatch          -> weak-const-generic-prepatch     PORTED
#   (nagini has no frame-mutation case) -> (none)                         VACUOUS class
#   ax-ref-resolved-kind-equals-...    -> (dropped)                       AXIOM LANE
#
# PORTED (pos-control-local-predicates -> pos-local-predicates): the sibling's
#   third positive is a data-flow reshape (accumulate the kind via the pure
#   predicates). It is NOT redundant with the frozen body on this carrier: the
#   frozen impl accumulates through a `mut` local under nested `if`s, whereas this
#   positive binds each guard to an immutable local and selects through a pure
#   `let` ladder — no mutation at all. So it probes over-fitting to the MUTABLE-
#   accumulator shape, which neither pos-reorder (which keeps the `mut`
#   accumulator and only reorders the branches) nor pos-direct (a single call)
#   reaches. The proof closes with the same retuned script as pos-reorder.
# PORTED (admissibility, reshaped): the sibling establishes the precondition
#   ADMITS the F2P input via a self-call. This bundle has NO `require` clause, so
#   there is no precondition to be too-strong; the argument is carried instead by
#   an in-region assertion that the F2P-shaped configuration classifies as the
#   temporal-difference node (the post-image is non-degenerate there). The assert
#   is live and the frozen `ensures` obligation still discharges. Verified to build.
# VACUOUS (frame-mutation): referentially-transparent backend, no `mut`
#   parameter, no heap — no read-only input to overwrite. Per the porting map this
#   class is vacuous on Lean/Velvet. Not fabricated.
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
# PORTED (the four value rivals) + ONE ADDED: the sibling's four uniqueness
#   rivals port directly onto the single `out = dispatchKind ...` clause, and a
#   fifth (weak-drop-equal-tags-requirement) is ADDED here because the temporal
#   branch is a THREE-conjunct guard and the sibling attacks only one of its
#   conjuncts — leaving the equal-tags conjunct pinned by no counterexample.
#   Each carries a machine-checked witness that ELABORATES against the rival and
#   FAILS against the frozen solution (two real builds per case), and every gold-
#   side failure is SEMANTIC (`decide` proves the tester is `true` at that input),
#   not a missing identifier or an unfolding failure. The five witnesses probe all
#   four input binders — an equal-interval pair (lt = rt = durationTag), an
#   already-specialised receiver (selfKind = durationNode), a non-difference
#   connector (conn = plus), two DIFFERING point-in-time tags (dateTag /
#   dateTimeTag), and the F2P datetime-difference shape — so every binder is
#   varied at more than one meaningful value and no rival is refuted at the same
#   point as another (pts = 5).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the selection is modeled deeply by dispatchKind; mapping.md §2/§3 note
# there is no axiom_check.py), so there is nothing to probe.
AXIOM_TESTS = []

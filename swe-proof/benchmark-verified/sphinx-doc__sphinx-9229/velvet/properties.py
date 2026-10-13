"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9229 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a FULL ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches only text inside an ``-- impl-start`` /
``-- impl-end`` region (and, for the admissibility case, an in-region ``assert``),
both of which the consumer spec view elides, so ``markers.same_spec`` holds by
construction and both ``prove_correct`` headers survive verbatim.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"`` passes
iff (in scope AND does NOT verify AND its refutation ``witness`` discriminates:
elaborates against the rival, FAILS against the frozen solution).

DEFENDED SURFACE (two contracted methods; the ``axioms`` region is EMPTY, so
every sub-computation is a closed total function of the free inputs — there is no
opaque callee anywhere on this carrier).

  * ``aliasDocstrings isAlias varComment normalDoc``
        -> ``Option (List (List String))``
      (A1) ensures out = docForAlias isAlias varComment normalDoc
             the whole decision: for an alias, an EMPTY docstring container
             (``some []``) when a doc-comment is present and NO container
             (``none``) when it is not; otherwise the ordinary documentation
             ``normalDoc``, untouched.
      (A2) ensures (isAlias ∧ commentPresent varComment) → out = some []
             the present-container arm, pinned independently of (A1).
      (A3) ensures (isAlias ∧ ¬commentPresent varComment) → out = none
             the absent-container arm, pinned independently of (A1).
      (A2)/(A3) pin the decision in BOTH directions; the ``some []`` vs ``none``
      distinction is the whole point (an empty container and no container are
      genuinely different results that drive different downstream rendering), and
      no value-level proxy can collapse them on this carrier.

  * ``aliasContentOverride isAlias varComment incoming aliasLabel``
        -> ``List String``
      (B1) ensures out = contentForAlias isAlias varComment incoming aliasLabel
             the whole gate: the content is replaced by the rendered alias label
             exactly when the entry is an alias AND carries no doc-comment;
             otherwise the incoming content is forwarded unchanged.
      (B2) ensures (isAlias ∧ commentPresent varComment) → out = incoming
             the pass-through arm — an alias WITH a doc-comment keeps its own
             documentation rather than being replaced.
      (B3) ensures (isAlias ∧ ¬commentPresent varComment) → out = aliasLabel
             the override arm — a bare alias shows the label.

``commentPresent`` collapses ``none`` (source could not be analysed) and
``some []`` (analysed, no comment) to the SAME decision while keeping them
DISTINCT inputs, so a rival that keys on ``isSome``/``isNone`` rather than on
non-emptiness is wrong on exactly one of them. Neither method has a ``require``
clause: every input is free, which is what makes each partial-domain rival
refutable at a concrete literal point.

ADVERSARIAL READ of the nagini classes (full accounting in the footer):
  * FRAME-MUTATION — VACUOUS here. The nagini sibling rejects impls that WRITE a
    read-only half-permission input, to show the read-only frame is not hollow.
    Velvet is referentially transparent and neither method declares a ``mut``
    binder, so there is no read-only carrier to overwrite and no substitute probe
    to build. Reported N/A, not fabricated.
  * OBJECT-IDENTITY / VALUE-DOUBLE-MASK — VACUOUS here. The nagini clauses it
    attacks demand ``Result() is prepared`` / ``is more_content``, and its rivals
    return a value-equal fresh copy. This carrier has no object identity: a
    ``List String`` equal to ``incoming`` IS ``incoming``, so a "fresh copy"
    rival is not a rival at all. The ARGUMENT behind those cases — that the
    untouched paths must forward the incoming value and not something rebuilt —
    is carried over as value-level attacks instead (A-normaldoc-leak,
    B-blank-label), which are refutable here.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. Every frozen impl region
    is LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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
  * UNGROUNDED-ORACLE ECHO — N/A. ``docForAlias`` / ``contentForAlias`` /
    ``commentPresent`` are concrete ``def``s over each method's own arguments and
    the ``axioms`` region is empty, so there is no answer-key an impl could echo.
    The honest control is the cheapest faithful reshape (the two positives).
  * PARTIAL-DOMAIN — the main class, heavily exercised. Every rival is correct on
    most of the four-way ``(isAlias, comment ∈ {none, some [], non-empty})``
    domain and diverges on one sub-domain, matching the F2P/P2P split.

WITNESS MECHANICS. Each spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery (``extract_program_for``
/ ``derive_tester_for``): ``<name>Tester args = false`` says the extracted
program's observable VIOLATES the postcondition at that concrete input. Every
input here is a ``Bool`` / ``Option (List String)`` / ``List String`` literal and
both impls are loop-free, so the extracted program reduces under kernel
``decide`` and the witness ELABORATES against the rival. The frozen impl
satisfies its postcondition at every point, so its tester returns ``true`` and
``= false`` FAILS against gold — the discriminator. Re-derived INDEPENDENTLY by
audit with real builds, all fourteen: rival build exit 0, gold build exit 1, gold
failing with ``Tactic `decide` proved that the proposition ... is false`` (i.e.
gold's tester really is ``true`` there), never with an elaboration error, an
unknown name, or a stuck reduction. No witness binds anything, so no consistency
probe applies and none can be vacuous through a contradictory hypothesis.

BINDER / CLAUSE COVERAGE. Fourteen reject witnesses at fourteen DISTINCT input
points. Case IDs below are the real ones; every claim here names a case that
exists, and every binder listed as varied is varied at a point where the spec's
verdict actually DEPENDS on it — which is a stronger requirement than "two
spellings appear", and is where the shipped version of this docstring was wrong
(see AUDIT REPAIRS at the end of this note).
  * ``aliasDocstrings``: ``isAlias`` moves off ``true``
    (weak-A-ignore-alias, weak-A-nonalias-none-to-empty); ``varComment`` takes
    all three shapes — non-empty single- and multi-line (weak-A-prepatch,
    weak-A-swap, weak-A-forward-instead-of-empty), ``none``
    (weak-A-always-empty), ``some []`` (weak-A-presence-is-someness);
    ``normalDoc`` is varied where it is OBSERVABLE, i.e. under
    ``isAlias = false``: a two-element container (weak-A-ignore-alias) and
    ``none`` (weak-A-nonalias-none-to-empty). ``normalDoc`` values under
    ``isAlias = true`` are NOT coverage of that binder — the spec ignores it
    there — except in weak-A-forward-instead-of-empty, where the RIVAL reads it
    and a two-element value is what makes the substitution observable.
  * ``aliasContentOverride``: ``isAlias`` off ``true`` (weak-B-ignore-alias);
    ``varComment`` non-empty single- and multi-line (weak-B-prepatch,
    weak-B-swap), ``none`` (weak-B-never-override, weak-B-blank-content,
    weak-B-guard-on-incoming), ``some []`` (weak-B-absence-is-noneness);
    ``incoming`` takes one-element, two-element and EMPTY values and
    ``aliasLabel`` six distinct values, always distinct from the paired
    ``incoming``. weak-B-blank-content moves ``aliasLabel`` while returning
    neither binder; weak-B-guard-on-incoming is the only case at which either
    sequence binder is EMPTY, which is what pins the override arm at its
    boundary rather than only on non-empty content.
Clause coverage: (A1) by every site-A rival, (A2) by weak-A-prepatch /
weak-A-swap / weak-A-forward-instead-of-empty, (A3) by weak-A-always-empty /
weak-A-swap / weak-A-presence-is-someness, (A1)-only by weak-A-ignore-alias and
weak-A-nonalias-none-to-empty (both implications have a false antecedent there —
the cases that show (A1) is load-bearing on its own); (B1) by every site-B rival,
(B2) by weak-B-prepatch / weak-B-swap, (B3) by weak-B-never-override /
weak-B-swap / weak-B-absence-is-noneness / weak-B-blank-content /
weak-B-guard-on-incoming, (B1)-only by weak-B-ignore-alias.

AXIOM lane: dropped. The bundle declares no axiom and no deep-model reference
(``meta.json`` ``axioms == []``, ``deep_model_references == []``); the G-AX lane
is not this gate's job and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9229"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl-region anchors. Each lies WHOLLY inside its method's
# `-- impl-start` / `-- impl-end` region and is unique in the file (both facts
# re-asserted at load by _swap / the asserts below), so the manifest breaks
# loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

_IMPL_A = (
    "    if isAlias then\n"
    "      if commentPresent varComment then\n"
    "        return (some [])\n"
    "      else\n"
    "        return none\n"
    "    else\n"
    "      return normalDoc"
)
assert _BASE.count(_IMPL_A) == 1, "site-A impl region drifted from expected text"

_IMPL_B = (
    "    if isAlias && !commentPresent varComment then\n"
    "      return aliasLabel\n"
    "    else\n"
    "      return incoming"
)
assert _BASE.count(_IMPL_B) == 1, "site-B impl region drifted from expected text"


def _impl_a(new_body):
    """Full Solution.lean variant with ONLY aliasDocstrings' impl body replaced."""
    return _swap(_BASE, _IMPL_A, new_body)


def _impl_b(new_body):
    """Full Solution.lean with ONLY aliasContentOverride's impl body replaced."""
    return _swap(_BASE, _IMPL_B, new_body)


# ---------------------------------------------------------------------------
# Witness preambles. The tester directives come from `Velvet.Std` (the frozen
# import) and are appended to BOTH the rival file and the gold file, so
# `<name>Exec` / `<name>Tester` exist on both sides by construction — the witness
# never references a name only the variant declares.
# ---------------------------------------------------------------------------
_TA = (
    "extract_program_for aliasDocstrings\n"
    "prove_precondition_decidable_for aliasDocstrings\n"
    "prove_postcondition_decidable_for aliasDocstrings\n"
    "derive_tester_for aliasDocstrings\n\n"
)
_TB = (
    "extract_program_for aliasContentOverride\n"
    "prove_precondition_decidable_for aliasContentOverride\n"
    "prove_postcondition_decidable_for aliasContentOverride\n"
    "derive_tester_for aliasContentOverride\n\n"
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT. Both
# verify with the frozen `loom_solve` untouched (confirmed during authoring).
# ---------------------------------------------------------------------------

# Handle the ORDINARY (non-alias) regime FIRST, then the two alias sub-cases as a
# nested if/else. Same three observable outcomes on exactly the same inputs.
_POS_A = (
    "    if !isAlias then\n"
    "      return normalDoc\n"
    "    else\n"
    "      if commentPresent varComment then\n"
    "        return (some [])\n"
    "      else\n"
    "        return none"
)

# The De Morgan dual of the frozen gate: pull the FORWARD-UNCHANGED case out
# first (`not an alias, OR an alias that does carry a comment`), leaving the
# override on exactly the remaining sub-domain.
_POS_B = (
    "    if !isAlias || commentPresent varComment then\n"
    "      return incoming\n"
    "    else\n"
    "      return aliasLabel"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (re-aimed). Neither method has a `require` clause, so nagini's
# "the fractional precondition admits a normal F2P-shaped input" probe is
# VACUOUS: nothing could exclude an in-domain input. Re-aimed at the residual
# risk on a total domain — that the post-image is UNSATISFIABLE or DEGENERATE at
# the interesting points (a spec no impl can meet reads exactly like a spec every
# impl meets). The assert claims all FOUR observable outcomes of the decision at
# once, including that the two comment-absent shapes agree; the impl is kept
# verbatim so all three of the method's own ensures clauses still discharge.
# ---------------------------------------------------------------------------
_ADMISS_A = (
    "    assert (with_name_prefix `assert\n"
    "      (docForAlias true (some [\"c\"]) (some [[\"d\"]]) = some [] ∧\n"
    "       docForAlias true none (some [[\"d\"]]) = none ∧\n"
    "       docForAlias true (some []) (some [[\"d\"]]) = none ∧\n"
    "       docForAlias false (some [\"c\"]) (some [[\"d\"]]) = some [[\"d\"]]))\n"
    + _IMPL_A
)

# Site-B admissibility, restored by audit. The port folded this into the site-A
# case on the ground that one probe covers "the fact nagini's two separate probes
# were jointly establishing". That is not so: the site-A assert mentions only
# `docForAlias`, so nothing in the shipped battery claimed the site-B decision is
# satisfiable and non-degenerate at any point. Re-derived as expressible and
# LIVE: negating any single conjunct leaves an unsolved goal (measured).
_ADMISS_B = (
    "    assert (with_name_prefix `assert\n"
    "      (contentForAlias true (some [\"c\"]) [\"I\"] [\"L\"] = [\"I\"] ∧\n"
    "       contentForAlias true none [\"I\"] [\"L\"] = [\"L\"] ∧\n"
    "       contentForAlias true (some []) [\"I\"] [\"L\"] = [\"L\"] ∧\n"
    "       contentForAlias false none [\"I\"] [\"L\"] = [\"I\"] ∧\n"
    "       ([\"I\"] : List String) ≠ [\"L\"]))\n"
    + _IMPL_B
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — one per obligation.
    # =====================================================================
    {
        "id": "pos-A-regime-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_a(_POS_A),
        "rationale": (
            "structurally-different but CORRECT aliasDocstrings: the ORDINARY "
            "(non-alias) regime is handled FIRST (`if !isAlias then return "
            "normalDoc`), then the two alias sub-cases as a nested if/else. Pure "
            "branch logic — no loop, invariant or fold to lose. The three "
            "observable outcomes (empty container, no container, the ordinary "
            "documentation forwarded) are produced on exactly the same inputs, so "
            "(A1), (A2) and (A3) all still discharge and the frozen `loom_solve` "
            "closes untouched. If it FAILS => SPEC-TOO-STRONG on branch order."
        ),
    },
    {
        "id": "pos-B-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_b(_POS_B),
        "rationale": (
            "structurally-different but CORRECT aliasContentOverride: the De Morgan "
            "dual of the frozen gate — the forward-unchanged case (`!isAlias || "
            "commentPresent varComment`) returns `incoming` first, leaving the "
            "label override on exactly the remaining sub-domain. Identical "
            "semantics on every input, so (B1), (B2) and (B3) all still discharge "
            "and the frozen `loom_solve` closes untouched. If it FAILS => "
            "SPEC-TOO-STRONG on gate shape."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed from nagini's precondition-admits probe).
    # =====================================================================
    {
        "id": "admiss-A-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_a(_ADMISS_A),
        "rationale": (
            "the decision is SATISFIABLE and NON-DEGENERATE at every point that "
            "matters: with a doc-comment present an alias must expose the EMPTY "
            "container (`some []`); with the comment absent — in BOTH of its "
            "shapes, unanalysable (`none`) and analysed-but-empty (`some []`) — it "
            "must expose NO container (`none`); and a non-alias must forward the "
            "ordinary documentation. A live in-region assert claims all four; a "
            "false claim would leave an unsolved goal. The impl is kept verbatim so "
            "(A1)/(A2)/(A3) discharge too. Re-aimed because neither method has a "
            "`require` clause, making nagini's admits-a-normal-input probe vacuous "
            "here. If it FAILS => the obligation is unsatisfiable at the point the "
            "modeled behaviour targets."
        ),
    },
    {
        "id": "admiss-B-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_b(_ADMISS_B),
        "rationale": (
            "the SITE-B decision is satisfiable and NON-DEGENERATE, claimed in its "
            "own right rather than inferred from site A: an alias WITH a "
            "doc-comment forwards the incoming content; an alias with the comment "
            "absent — in BOTH shapes, unanalysable (`none`) and analysed-but-empty "
            "(`some []`) — exposes the rendered label; a non-alias forwards the "
            "incoming content. The final conjunct pins `incoming ≠ aliasLabel` at "
            "the probed values, without which the middle two claims could be "
            "satisfied by the two binders coinciding and the assert would be "
            "degenerate exactly where it is supposed to bite. A live in-region "
            "assert claims all five; the impl is kept verbatim so (B1)/(B2)/(B3) "
            "discharge too. If it FAILS => the site-B obligation is unsatisfiable "
            "at the point the modeled behaviour targets."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals against aliasDocstrings. Each is loop-free (its extracted
    # program reduces under `decide`) and carries a machine-checked witness at a
    # concrete input, plus the argument that its faithful counterpart would NOT
    # resolve.
    # =====================================================================
    {
        "id": "weak-A-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image behaviour (= Solution_prepatch_1): an alias NEVER exposes
        # a docstring container; the doc-comment is not consulted at all.
        "module": _impl_a(
            "    if isAlias then\n"
            "      return none\n"
            "    else\n"
            "      return normalDoc"),
        "refinement": (
            "this is the pre-image decision exactly: an alias entry exposes no "
            "docstring container whatever, so an alias that DOES carry a "
            "doc-comment attached to its name is documented as though it had none "
            "— the comment is dropped and the entry falls back to the default "
            "label rendering. That is precisely the behaviour the failing test "
            "asserts is gone: it expects the alias entry to render its own comment "
            "text as the documentation. A faithful counterpart therefore does NOT "
            "resolve the F2P."
        ),
        "rationale": (
            "REJECT from (A2) (and (A1)): when the entry is an alias AND a "
            "doc-comment is present the spec demands `out = some []` (a present, "
            "empty container), but the rival returns `none`. PARTIAL-DOMAIN — "
            "correct on the comment-absent and non-alias sub-domains, wrong only "
            "where a comment is present. Refuted at "
            "(true, some [\"c\"], some [[\"d\"]]). If it VERIFIES => SPEC-TOO-WEAK "
            "(the present-vs-absent container decision is unpinned). This is the "
            "G-DIFF prepatch_1."
        ),
        "witness": _TA + (
            'example : aliasDocstringsTester true (some ["c"]) (some [["d"]]) '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-A-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual revert: an alias ALWAYS exposes the empty container, comment or
        # not. Correct where a comment is present, wrong where it is absent.
        "module": _impl_a(
            "    if isAlias then\n"
            "      return (some [])\n"
            "    else\n"
            "      return normalDoc"),
        "refinement": (
            "a counterpart that exposed an empty docstring container for EVERY "
            "alias would make a bare alias — one with no comment attached to its "
            "name — look as though it had documentation of its own, suppressing "
            "the default label rendering that the passing suite pins for exactly "
            "that case. So it regresses a P2P test and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A3) (and (A1)): when the entry is an alias and NO "
            "doc-comment is present the spec demands `out = none` (no container), "
            "but the rival returns `some []`. PARTIAL-DOMAIN, the dual of the "
            "pre-image. Refuted at (true, none, some [[\"d\"]]) — the only site-A "
            "witness whose `varComment` is the unanalysable shape `none`. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _TA + (
            "example : aliasDocstringsTester true none (some [[\"d\"]]) "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-A-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # The comment decision INVERTED: comment present -> no container, comment
        # absent -> the empty container. Wrong on BOTH alias sub-domains.
        "module": _impl_a(
            "    if isAlias then\n"
            "      if commentPresent varComment then\n"
            "        return none\n"
            "      else\n"
            "        return (some [])\n"
            "    else\n"
            "      return normalDoc"),
        "refinement": (
            "the doc-comment decision inverted. Its faithful counterpart is the "
            "exact opposite of the intended behaviour and is wrong on BOTH alias "
            "sub-domains at once: it drops the comment of an alias that has one "
            "(failing the F2P) AND fabricates a documentation container for a bare "
            "alias, suppressing the default label the passing suite pins (failing "
            "a P2P). So it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A2) on the comment-present sub-domain (returns `none` "
            "where `some []` is demanded) and INDEPENDENTLY from (A3) on the "
            "comment-absent sub-domain (returns `some []` where `none` is "
            "demanded) — a branch-inversion rival hitting both load-bearing arms. "
            "Refuted at (true, some [\"x\", \"y\"], none), a point no other "
            "witness uses: a MULTI-line comment with the ordinary documentation "
            "itself absent, so neither the comment length nor `normalDoc` could be "
            "masking the disagreement. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _TA + (
            'example : aliasDocstringsTester true (some ["x", "y"]) none '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-A-ignore-alias",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the isAlias regime selector entirely: the alias decision is
        # applied to every entry, so an ORDINARY entry loses its documentation.
        # Built to move the isAlias binder off `true`.
        "module": _impl_a(
            "    if commentPresent varComment then\n"
            "      return (some [])\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "a counterpart that applied the alias-specific decision to EVERY "
            "documented entry would discard the ordinary documentation of every "
            "non-alias class in the suite — replacing it with an empty container "
            "or none at all — so essentially the whole passing suite regresses. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A1) ALONE: at `isAlias = false` both implication clauses "
            "(A2)/(A3) have a FALSE antecedent and say nothing, so this is the "
            "case that shows the equation `out = docForAlias …` is load-bearing on "
            "its own — the spec demands the ordinary documentation be forwarded "
            "(`out = normalDoc`), and the rival returns `some []` instead. Refuted "
            "at (false, some [\"c\"], some [[\"d\"], [\"e\"]]) — the only site-A "
            "witness that moves `isAlias` off `true`, with a TWO-element "
            "`normalDoc` so the forwarded value cannot coincide with `some []`. If "
            "it VERIFIES => SPEC-TOO-WEAK (the regime selector is unpinned)."
        ),
        "witness": _TA + (
            'example : aliasDocstringsTester false (some ["c"]) '
            '(some [["d"], ["e"]]) = false := by\n  decide\n'),
    },
    {
        "id": "weak-A-presence-is-someness",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: keys the decision on whether the lookup produced ANYTHING
        # (`isSome`) rather than on whether it produced a NON-EMPTY comment. Agrees
        # with the frozen decision on the unanalysable shape and on every non-empty
        # comment; diverges on exactly `some []`.
        "module": _impl_a(
            "    if isAlias then\n"
            "      if varComment.isSome then\n"
            "        return (some [])\n"
            "      else\n"
            "        return none\n"
            "    else\n"
            "      return normalDoc"),
        "refinement": (
            "a counterpart that treated a SUCCESSFUL-but-empty comment lookup as "
            "though a comment were present would give every bare alias in an "
            "analysable module an empty documentation container, suppressing the "
            "default label rendering the passing suite pins for a bare alias — the "
            "common case, since a bare alias in an analysable module is exactly "
            "the analysed-and-empty shape. So it regresses a P2P and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (A3) (and (A1)): the spec's notion of presence is "
            "NON-EMPTINESS, so an analysed-but-empty lookup (`some []`) counts as "
            "ABSENT and demands `out = none`; keying on `isSome` returns "
            "`some []`. A NEAR-MISS that agrees with gold on `none` and on every "
            "non-empty comment, so it gets its own discriminating point: refuted "
            "at (true, some [], some [[\"d\"]]) — the ONLY site-A witness at the "
            "analysed-but-empty comment shape, which is precisely the sub-domain "
            "its rationale claims. If it VERIFIES => SPEC-TOO-WEAK (the spec would "
            "not distinguish `none` from `some []` in the way it states)."
        ),
        "witness": _TA + (
            "example : aliasDocstringsTester true (some []) (some [[\"d\"]]) "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-A-forward-instead-of-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Right DECISION, wrong CONTENT: on the comment-present arm it forwards the
        # ordinary documentation instead of the empty container. This is the
        # value-level heir of nagini's object-identity rivals — that carrier has no
        # `is` here, but the CONTENT of the container is still fully observable.
        "module": _impl_a(
            "    if isAlias then\n"
            "      if commentPresent varComment then\n"
            "        return normalDoc\n"
            "      else\n"
            "        return none\n"
            "    else\n"
            "      return normalDoc"),
        "refinement": (
            "a counterpart that, for an alias carrying a doc-comment, exposed the "
            "ordinary documentation it would have produced for a non-alias instead "
            "of the empty container would render the aliased target's own "
            "docstring under the alias entry rather than the comment attached to "
            "the alias name. The failing test pins the alias entry's rendered body "
            "to the comment text exactly, so the wrong body fails it. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (A2) (and (A1)) on the CONTENT of the container, not the "
            "decision: the spec pins `out = some []`, an EMPTY container, while the "
            "rival forwards `normalDoc`. They agree only when `normalDoc` happens "
            "to be `some []`. Refuted at (true, some [\"k\"], "
            "some [[\"v\"], [\"w\"]]) — the only witness with a two-element "
            "`normalDoc` on the alias regime, which is what makes the substituted "
            "content observable rather than accidentally equal. This is the "
            "value-level heir of the nagini identity rivals (see the footer). If "
            "it VERIFIES => SPEC-TOO-WEAK (the container's content is unpinned)."
        ),
        "witness": _TA + (
            'example : aliasDocstringsTester true (some ["k"]) '
            '(some [["v"], ["w"]]) = false := by\n  decide\n'),
    },
    {
        "id": "weak-A-nonalias-none-to-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Forwards `normalDoc` on the ordinary regime EXCEPT when
        # the ordinary documentation is itself absent, where it substitutes an
        # empty container. The narrowest site-A rival in the battery: it agrees
        # with the frozen decision everywhere except the single point
        # (isAlias = false, normalDoc = none).
        "module": _impl_a(
            "    if isAlias then\n"
            "      if commentPresent varComment then\n"
            "        return (some [])\n"
            "      else\n"
            "        return none\n"
            "    else\n"
            "      if normalDoc.isNone then\n"
            "        return (some [])\n"
            "      else\n"
            "        return normalDoc"),
        "refinement": (
            "a counterpart that manufactured an empty documentation container for "
            "an ordinary, non-alias entry that has no documentation of its own "
            "would make every undocumented ordinary class look as though it "
            "carried an empty body, changing the rendering the passing suite pins "
            "for an undocumented class. So it regresses a P2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (A1) on the ORDINARY regime at the one input the rest of "
            "the battery leaves unprobed: the spec demands the ordinary "
            "documentation be forwarded VERBATIM, including when it is absent "
            "(`out = normalDoc = none`), and the rival returns `some []` there. "
            "Refuted at (false, none, none) — the ONLY witness at which "
            "`normalDoc` is both `none` AND observable (`isAlias = false`); every "
            "other site-A witness that sets `normalDoc = none` does so under "
            "`isAlias = true`, where the spec ignores it entirely, so before this "
            "case nothing in the battery depended on the absent shape of "
            "`normalDoc`. If it VERIFIES => SPEC-TOO-WEAK (the forwarded "
            "documentation is unpinned at its absent value)."
        ),
        "witness": _TA + (
            "example : aliasDocstringsTester false none none = false := by\n"
            "  decide\n"),
    },

    # =====================================================================
    # UNIQUENESS rivals against aliasContentOverride. Same witness mechanics;
    # each attacks a specific clause and moves a distinct binder.
    # =====================================================================
    {
        "id": "weak-B-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image gate (= Solution_prepatch_2): the label overrides the
        # content for EVERY alias, regardless of the doc-comment.
        "module": _impl_b(
            "    if isAlias then\n"
            "      return aliasLabel\n"
            "    else\n"
            "      return incoming"),
        "refinement": (
            "this is the pre-image gate exactly: an alias entry's content is "
            "always replaced by the rendered label. So an alias that DOES carry a "
            "doc-comment has its own documentation overwritten by the default "
            "label text — the very symptom the failing test asserts is gone (it "
            "pins the alias entry's body to the comment text, with no label line). "
            "A faithful counterpart does NOT resolve the F2P."
        ),
        "rationale": (
            "REJECT from (B2) (and (B1)): when the entry is an alias AND a "
            "doc-comment is present the spec demands `out = incoming` (forward "
            "unchanged), but the rival returns `aliasLabel`. PARTIAL-DOMAIN — "
            "correct on the comment-absent and non-alias sub-domains. Refuted at "
            "(true, some [\"c\"], [\"I\"], [\"L\"]), where `incoming` and "
            "`aliasLabel` are distinct so the substitution is observable. If it "
            "VERIFIES => SPEC-TOO-WEAK. This is the G-DIFF prepatch_2."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester true (some ["c"]) ["I"] ["L"] '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-B-never-override",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual revert: the label NEVER overrides; every entry forwards its
        # incoming content.
        "module": _impl_b("    return incoming"),
        "refinement": (
            "a counterpart that never substituted the rendered label would leave a "
            "bare alias — one with no comment attached to its name — with no label "
            "line at all, while the passing suite pins exactly that line for a "
            "bare alias. So it regresses a P2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B3) (and (B1)): when the entry is an alias and no "
            "doc-comment is present the spec demands `out = aliasLabel`, but the "
            "rival returns `incoming`. PARTIAL-DOMAIN / dual revert — correct on "
            "the whole forward-unchanged sub-domain. Refuted at (true, none, "
            "[\"P\"], [\"Q\"]) — the comment-absent-by-unanalysability shape, with "
            "`incoming` and `aliasLabel` distinct. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester true none ["P"] ["Q"] '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-B-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # The comment condition INVERTED: override exactly when a comment IS
        # present. Wrong on BOTH alias sub-domains.
        "module": _impl_b(
            "    if isAlias && commentPresent varComment then\n"
            "      return aliasLabel\n"
            "    else\n"
            "      return incoming"),
        "refinement": (
            "the doc-comment condition inverted, so the counterpart is wrong on "
            "both alias sub-domains at once: it overwrites the documentation of an "
            "alias that HAS a comment with the label (failing the F2P) and it "
            "leaves a bare alias with no label line (failing a P2P). It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (B2) on the comment-present sub-domain (returns "
            "`aliasLabel` where `incoming` is demanded) and INDEPENDENTLY from "
            "(B3) on the comment-absent sub-domain (returns `incoming` where "
            "`aliasLabel` is demanded). Refuted at (true, some [\"c\", \"d\"], "
            "[\"R\"], [\"S\"]) — a MULTI-line comment, a point no other witness "
            "uses, so the disagreement cannot be an artifact of a single-line "
            "comment. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester true (some ["c", "d"]) ["R"] '
            '["S"] = false := by\n  decide\n'),
    },
    {
        "id": "weak-B-ignore-alias",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the isAlias gate: the label override is applied to any entry
        # lacking a doc-comment. Built to move the isAlias binder off `true`.
        "module": _impl_b(
            "    if !commentPresent varComment then\n"
            "      return aliasLabel\n"
            "    else\n"
            "      return incoming"),
        "refinement": (
            "a counterpart that dropped the alias gate would replace the content "
            "of every ordinary documented entry that has no comment attached to "
            "its name with an alias label line — mislabelling classes that are not "
            "aliases at all. The whole passing suite of ordinary class rendering "
            "regresses, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B1) ALONE: at `isAlias = false` both implication clauses "
            "(B2)/(B3) have a FALSE antecedent, so this case shows the equation "
            "`out = contentForAlias …` is load-bearing by itself — it demands the "
            "incoming content be forwarded, and the rival returns `aliasLabel`. "
            "Refuted at (false, none, [\"X\"], [\"Y\"]) — the only site-B witness "
            "that moves `isAlias` off `true`. If it VERIFIES => SPEC-TOO-WEAK (the "
            "alias gate is unpinned)."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester false none ["X"] ["Y"] '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-B-absence-is-noneness",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS mirroring weak-A-presence-is-someness on site B: overrides
        # only when the lookup produced NOTHING (`isNone`), so an analysed-but-empty
        # lookup wrongly counts as a comment being present. Agrees with gold
        # everywhere except at `some []`.
        "module": _impl_b(
            "    if isAlias && varComment.isNone then\n"
            "      return aliasLabel\n"
            "    else\n"
            "      return incoming"),
        "refinement": (
            "a counterpart that substituted the label only when the comment lookup "
            "produced nothing at all would leave a bare alias in an ANALYSABLE "
            "module — the ordinary case, whose lookup succeeds and yields an empty "
            "result — with no label line, since it would mistake the empty result "
            "for a comment being present. The passing suite pins that label line, "
            "so it regresses a P2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B3) (and (B1)): the spec's notion of absence is "
            "EMPTINESS-or-nothing, so an analysed-but-empty lookup (`some []`) "
            "counts as ABSENT and demands `out = aliasLabel`; keying on `isNone` "
            "forwards `incoming` instead. A NEAR-MISS that agrees with gold at "
            "`none` and at every non-empty comment, so it gets its own "
            "discriminating point: refuted at (true, some [], [\"I\"], [\"T\"]) — "
            "the ONLY site-B witness at the analysed-but-empty shape, the exact "
            "sub-domain its rationale claims. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester true (some []) ["I"] ["T"] '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-B-blank-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Right DECISION, wrong CONTENT: takes the override branch on exactly the
        # right sub-domain but emits an EMPTY sequence instead of the rendered
        # label. Attacks the VALUE (B3) pins, and is the only rival that returns
        # neither `incoming` nor `aliasLabel`.
        "module": _impl_b(
            "    if isAlias && !commentPresent varComment then\n"
            "      return []\n"
            "    else\n"
            "      return incoming"),
        "refinement": (
            "a counterpart that took the override branch on exactly the right "
            "entries but emitted nothing in place of the rendered label would leave "
            "a bare alias with an EMPTY body — neither its incoming content nor the "
            "label line the passing suite pins for that case. So it regresses a "
            "P2P and does NOT resolve, even though its branch decision is right."
        ),
        "rationale": (
            "REJECT from (B3) (and (B1)) on the VALUE, not the branch decision: "
            "the spec pins `out = aliasLabel` on the override arm, and the rival "
            "returns `[]`. This is the site-B content attack — the routing is "
            "correct, so only the pinned value can refute it. Refuted at "
            "(true, none, [\"m\", \"n\"], [\"Z\"]) — a two-element `incoming` "
            "distinct from both `aliasLabel` and `[]`, so neither the forwarded "
            "value nor the empty result could coincide with what the spec demands. "
            "This is the only witness that moves `aliasLabel` while the rival "
            "returns neither binder. If it VERIFIES => SPEC-TOO-WEAK (the "
            "overriding content is unpinned)."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester true none ["m", "n"] ["Z"] '
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-B-guard-on-incoming",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Takes the override branch only when there is incoming
        # content to override — a plausible extra guard, and the narrowest site-B
        # rival in the battery: it agrees with the frozen gate on every input
        # EXCEPT where the incoming content is the EMPTY sequence, a value no
        # other witness gives to either sequence binder.
        "module": _impl_b(
            "    if isAlias && !commentPresent varComment && !incoming.isEmpty then\n"
            "      return aliasLabel\n"
            "    else\n"
            "      return incoming"),
        "refinement": (
            "a counterpart that substituted the rendered label only when the entry "
            "already had some content of its own would leave a bare alias that "
            "carries NO content with no label line — and a bare alias carrying no "
            "content is the ordinary case for the entry the passing suite pins that "
            "label line for. So it regresses a P2P and does NOT resolve."
        ),
        "rationale": (
            "REJECT from (B3) (and (B1)): on the override sub-domain the spec "
            "demands `out = aliasLabel` UNCONDITIONALLY in the incoming content, "
            "and the rival forwards `incoming` whenever that content is empty. "
            "Refuted at (true, none, [], [\"L\"]) — the ONLY witness in the battery "
            "at which either sequence binder takes the EMPTY value. Every other "
            "site-B witness gives `incoming` and `aliasLabel` non-empty, distinct "
            "values, so no shipped case distinguished `out = aliasLabel` from the "
            "weaker `out = aliasLabel whenever incoming is non-empty`; this case "
            "is what makes the override arm's value pinned at the boundary. If it "
            "VERIFIES => SPEC-TOO-WEAK (the override is unpinned on empty incoming "
            "content)."
        ),
        "witness": _TB + (
            'example : aliasContentOverrideTester true none [] ["L"] '
            "= false := by\n  decide\n"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING
#
# The nagini sibling ships 13 SPEC cases (2 soundness positives, 2
# admissibility, and 9 uniqueness rivals, of which 2 are frame-mutation) plus 2
# AXIOM_TESTS. (The shipped version of this note said 12 cases / 6 uniqueness
# rivals; corrected by audit against a real count of nagini's SPEC_TESTS.) It
# contracts the same TWO changed decisions this bundle models, so the port is
# unusually close to one-for-one; case count is 17 here because the free-input
# structure of the two `method` contracts admits binder-coverage rivals nagini's
# carrier could not express.
#
#   nagini case              -> here                                status
#   ------------------------------------------------------------------------
#   pos-A-reorder            -> pos-A-regime-first                  PORTED
#   pos-B-reorder            -> pos-B-demorgan                      PORTED
#   admiss-A                 -> admiss-A-nondegenerate              RE-AIMED
#   admiss-B                 -> admiss-B-nondegenerate              RE-AIMED
#   frame-mut-A              -> (none)                              VACUOUS
#   frame-mut-B              -> (none)                              VACUOUS
#   weak-A-prepatch          -> weak-A-prepatch                     PORTED
#   weak-A-always-present    -> weak-A-always-empty                 PORTED
#   weak-A-swap              -> weak-A-swap                         PORTED
#   weak-A-copy              -> weak-A-forward-instead-of-empty     RE-AIMED
#   weak-B-prepatch          -> weak-B-prepatch                     PORTED
#   weak-B-never             -> weak-B-never-override               PORTED
#   weak-B-copy              -> weak-B-blank-content                RE-AIMED
#   AXIOM_TESTS (x2)         -> (none)                              DROPPED
#   (no nagini counterpart)  -> weak-A-ignore-alias                 ADDED
#   (no nagini counterpart)  -> weak-A-presence-is-someness         ADDED
#   (no nagini counterpart)  -> weak-B-swap                         ADDED
#   (no nagini counterpart)  -> weak-B-ignore-alias                 ADDED
#   (no nagini counterpart)  -> weak-B-absence-is-noneness          ADDED
#   (no nagini counterpart)  -> weak-A-nonalias-none-to-empty       ADDED (audit)
#   (no nagini counterpart)  -> weak-B-guard-on-incoming            ADDED (audit)
#
# PORTED (8). The two prepatch reverts, the two dual reverts, the site-A branch
#   inversion and the two positive reshapes carry over directly: the nagini
#   `is_attr_alias` / `has_authored_comment(comment)` guards are this carrier's
#   `isAlias` / `commentPresent varComment`, and the `Optional[List[int]]`
#   present-empty-vs-absent result is `some [] vs none`. Each keeps the nagini
#   partial-domain ARGUMENT and its F2P/P2P grounding, restated over the modeled
#   carrier.
#
# RE-AIMED (3).
#   * admissibility: nagini's two cases assert that the fractional
#     half-permission preconditions ADMIT a normal F2P-shaped input (reading a
#     length, reading a first element). Neither method here has a `require`
#     clause, so nothing could exclude an in-domain input and that probe is
#     vacuous as WRITTEN. It is re-aimed at the residual admissibility risk on a
#     total domain: that the post-image is unsatisfiable or degenerate at the
#     interesting points. ONE CASE PER SITE, as in nagini. The shipped port kept
#     only the site-A case and claimed the site-B case was "folded into" it
#     because the single assert established "the fact nagini's two separate
#     probes were jointly establishing"; audit rejected that reasoning — the
#     site-A assert mentions only `docForAlias` and says nothing whatever about
#     the site-B decision, so folding left `aliasContentOverride`'s post-image
#     unclaimed. admiss-B-nondegenerate restores it, and was re-derived as both
#     EXPRESSIBLE and LIVE (negating any one conjunct leaves an unsolved goal).
#     Its fifth conjunct pins `incoming ≠ aliasLabel` at the probed values, so
#     the assert cannot be satisfied by the two binders coinciding.
#   * weak-A-copy / weak-B-copy: nagini's VALUE-DOUBLE-MASK rivals return a
#     value-equal FRESH LIST to break `Result() is prepared` / `is more_content`.
#     This carrier has no object identity — a `List String` equal to `incoming`
#     IS `incoming` — so the rivals as written are not rivals at all and their
#     clauses cannot be attacked that way. What survives is the ARGUMENT: the
#     paths that forward a value must forward THAT value and not something
#     rebuilt. Re-aimed as value-level content attacks that this carrier CAN
#     refute — weak-A-forward-instead-of-empty substitutes the ordinary
#     documentation for the empty container, weak-B-blank-content substitutes an
#     empty sequence for the rendered label. Both take the right branch, so only
#     the pinned VALUE can refute them, which is the same defect class one level
#     down.
#
# VACUOUS (2, frame-mutation). The nagini sibling calls this its #1 weakness
#   class and rejects an impl that writes a read-only `Acc(...,1/2)` input
#   (`prepared[0] = prepared[0]`, `target[0] = target[0]`) for INSUFFICIENT
#   PERMISSION. Velvet is referentially transparent and neither method declares a
#   `mut` binder, so there is no read-only carrier an impl could overwrite and no
#   substitute probe to build. Per the porting map, this class is vacuous on the
#   Lean family: NOT fabricated.
#
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
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
#
# DROPPED (2, AXIOM_TESTS). The nagini sibling consumes one `@ContractOnly`
#   axiom (`placeholder_seq` / `make_placeholder`, the unchanged label formatter)
#   and probes its soundness and containment. This bundle has NO axiom: the
#   `axioms` region is empty and the rendered label is carried as the free input
#   `aliasLabel` (an R-refinement validated by G-CONF), so there is no axiom face
#   to probe. The axiom lane is G-AX's job and this gate ignores AXIOM_TESTS
#   regardless.
#
# ADDED (5, binder/clause coverage). The nagini carrier could not express these,
#   and a battery that never moves an input says nothing about the spec's
#   dependence on it:
#   * weak-A-ignore-alias / weak-B-ignore-alias — the ONLY witnesses that move
#     `isAlias` off `true`. Both refute the equation clause (A1)/(B1) where both
#     implication clauses are vacuously true, which is what shows the equation is
#     load-bearing on its own rather than implied by the two arms.
#   * weak-A-presence-is-someness / weak-B-absence-is-noneness — NEAR-MISSES that
#     key on `isSome`/`isNone` rather than non-emptiness. They agree with the
#     frozen decision at `none` and at every non-empty comment and diverge only at
#     `some []`, so each is refuted AT `some []` — the analysed-but-empty shape
#     that no other witness probes. This is the axis the carrier introduces (the
#     nagini `has_authored_comment` predicate hid the two absent shapes behind one
#     boolean), and without these two rivals nothing in the battery would depend
#     on the distinction the spec's comment carrier is modeled to preserve.
#   * weak-B-swap — the site-B branch inversion, the mirror of the ported
#     weak-A-swap; nagini attacks the inversion on site A only.
#
# WITNESS DISCRIMINATION. The fourteen reject witnesses sit at fourteen DISTINCT
#   input points (seven on aliasDocstrings, seven on aliasContentOverride); no two
#   share a point, and the two NEAR-MISSES are each refuted at the input that
#   distinguishes them from gold rather than at a point a coarser rival already
#   covers. Every input binder of both obligations is moved by some witness AT A
#   POINT WHERE THE SPEC DEPENDS ON IT: `isAlias` (both regimes), `varComment`
#   (all three shapes: `none`, `some []`, non-empty single- and multi-line),
#   `normalDoc` (`none` and a two-element container, both under `isAlias = false`
#   where the spec reads it), `incoming` (empty, one- and two-element),
#   `aliasLabel` (six distinct values, always distinct from the paired
#   `incoming`). Re-derived independently by audit with real builds: rival build
#   exit 0 and gold build exit 1 for all fourteen, with gold failing as
#   `Tactic \x60decide\x60 proved that the proposition ... is false` — i.e. gold's
#   tester genuinely returns `true` at that point — never with an elaboration
#   error, an unknown name, or a stuck reduction. No witness binds a variable, so
#   none can be a forgery resting on contradictory hypotheses.
#
# ===========================================================================
# AUDIT REPAIRS (independent adversarial re-derivation of this battery)
#
# What held up. Statement integrity is exact: the non-impl slice of all shipped
#   variants is byte-identical to the frozen file (one sha256 over all of them),
#   so no case reformats or weakens an obligation, and all six `ensures` clauses
#   plus both `prove_correct` headers survive verbatim everywhere. Every shipped
#   rival was confirmed OBSERVABLY wrong by exhaustive evaluation of gold vs
#   rival over the finite input domain — none is a mere reshape, none is
#   definitionally equal to gold on this carrier — and every one differs from
#   gold AT its own declared witness point. Both positives were confirmed
#   observably IDENTICAL to gold on the same domain, so neither is a wrong impl
#   passing as a positive, and neither is the frozen impl verbatim.
#
# What did NOT hold up, and was repaired here:
#   1. admiss-B-nondegenerate ADDED. The port dropped nagini's second
#      admissibility case as "folded into" the site-A one. It was not folded: the
#      site-A assert names only `docForAlias`, leaving the site-B post-image
#      unclaimed by any case. Re-derived as expressible and live.
#   2. weak-A-nonalias-none-to-empty ADDED. The shipped battery claimed
#      `normalDoc` "moves off `none`", but every witness that set
#      `normalDoc = none` did so under `isAlias = true`, where the spec IGNORES
#      that binder — two spellings of the same point, not meaningful variation.
#      This rival is wrong at exactly (false, none, none), the one input at which
#      `normalDoc = none` is observable.
#   3. weak-B-guard-on-incoming ADDED. No shipped witness gave either sequence
#      binder the EMPTY value, so nothing distinguished `out = aliasLabel` from
#      the weaker "`out = aliasLabel` whenever `incoming` is non-empty".
#   4. Prose corrected: nagini's real case count (13, not 12; 9 uniqueness
#      rivals, not 6), the stale coverage IDs (`A-normaldoc-leak`,
#      `A-some-counts`, `B-blank-label`, `B-none-only`, `B-never` — none of which
#      is a case in this file), and the overstated `normalDoc` / `aliasLabel`
#      coverage claims.
#
# SPEC-TOO-WEAK probe (6 NEW wrong impls beyond this battery, aimed at whatever
#   the shipped rivals left unattacked): a container holding one EMPTY LINE
#   instead of no lines (`some [[]]` for `some []`); the absent arm forwarding
#   `normalDoc` instead of `none`; the override arm APPENDING the label to the
#   incoming content instead of replacing it; a presence test keyed on comment
#   LENGTH >= 2; plus the two rivals adopted above. ALL SIX WERE REJECTED
#   (`unsolved goals`) — no spec hole found. The frozen (A1)/(B1) equations pin
#   `out` uniquely at every input, which is what leaves no room for one.
#
# SPEC-TOO-STRONG probe (6 NEW correct reshapes): the comment test hoisted
#   outermost with the regime test duplicated into both arms; a `match` on the
#   option instead of the boolean helper; a single `return` of an if-EXPRESSION;
#   the comment test first with the regime test nested; and two reshapes that
#   avoid `commentPresent` ENTIRELY, collapsing the two absent comment shapes
#   with `getD []`. Four verified under the frozen `loom_solve` untouched. The
#   two `getD []` reshapes did NOT — but their residual goals were checked to be
#   semantically TRUE (the bridge `commentPresent vc = !((vc.getD []).isEmpty)`
#   was proven), and each then VERIFIED once reproven with
#   `loom_solve <;> (cases varComment <;> simp_all [...])`, which the scope rules
#   permit (only the statement is frozen; the tactic body may differ). So that is
#   a reach limit of the frozen tactic script, NOT a spec-too-strong hole: the
#   spec admits every faithful reshape tried, and nothing was recorded as a spec
#   defect on the strength of a proof this audit merely failed to close.
# ===========================================================================
AXIOM_TESTS = []

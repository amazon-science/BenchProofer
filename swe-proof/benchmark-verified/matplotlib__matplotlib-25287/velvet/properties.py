"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25287 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the two ``-- impl-start`` /
``-- impl-end`` regions — the impl body is byte-identical in both modeled
methods, so it occurs twice — is changed; the consumer spec view elides those
regions, so ``markers.same_spec`` holds and both ``prove_correct`` obligations
survive with their headers intact) and swaps in a candidate implementation; it
is checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness ELABORATES against the rival
and FAILS against the frozen solution).

DEFENDED SURFACE (two byte-identical contracted methods, one per independently-
observable site — the two axes — that select the color a secondary exponent
(offset) text should be painted with):

  xAxisOffsetColor (tickColor : String) (labelColor : String) return (out : String)
    ensures out = offsetColor tickColor labelColor      -- only clause
  yAxisOffsetColor (tickColor : String) (labelColor : String) return (out : String)
    ensures out = offsetColor tickColor labelColor      -- same clause

where the TRANSPARENT ``def`` (directive 8; NOT an opaque answer-key) is

  offsetColor tickColor labelColor =
    if labelColor = "inherit" then tickColor       -- sentinel ⟹ fall back to tick color
    else labelColor                                -- configured label color GOVERNS

On concrete inputs the whole clause reduces to a comparison of two ``String``
values that ``decide`` computes, so no rival can "echo an opaque oracle": the
only way to satisfy the clause is to compute exactly this selection. The
``axioms`` region is empty; ``offsetColor`` is a fully-unfolded ``def`` over the
method's own two arguments (mapping.md §3: no axiomatized callee, no deep model).

WHAT THE SPEC DEFENDS. The whole content of the modeled fix is that an
explicitly-configured label color takes precedence over the tick color; the
sentinel value ``"inherit"`` is the ONLY case that falls back to the tick color.
That precedence lives in the ``else labelColor`` arm and is pinned by the whole
equality, together with the sentinel branch (``labelColor = "inherit" ⟹
tickColor``). The pre-change defect — always using the tick color and ignoring a
configured label color — is exactly a rival correct on the sentinel sub-domain
and wrong on the ordinary one.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on BOTH inputs:

  * ``labelColor`` selects the branch AND, on the ordinary branch, IS the result.
    A rival that ignores a configured label color is refuted at a
    ``labelColor ≠ "inherit"`` point; a rival wrong only on the sentinel is
    refuted at ``labelColor = "inherit"``. The battery carries both, so
    ``labelColor`` is not pinned at one value.
  * ``tickColor`` is the fallback color used on the sentinel branch and the
    distractor an ordinary-branch rival wrongly returns; the witnesses vary it
    and at least one rival's refutation turns on it differing from ``labelColor``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Three structurally-different but
    behaviourally-identical correct impls (test the ordinary branch first; a
    single ``let``-bound conditional; return the grounded ``offsetColor`` model
    directly) must verify, else the spec is over-fit to the impl shape
    (SPEC-TOO-STRONG). Each reproves with the frozen tactic script (the tactic
    body is elided from the spec view, so ``same_spec`` and both obligation
    headers are untouched).
  * FRAME / PERMISSION-MUTATION — VACUOUS, and the reason is measured rather
    than asserted. The nagini sibling carries a MANDATORY frame rival that WRITES
    through a read-only input held at a fractional heap permission
    (``Acc(list_pred(base_color), 1/2)``). Lean and Velvet are referentially
    transparent: ``tickColor`` and ``labelColor`` are immutable ``String``
    values, no ``mut`` binder is declared, and there is no heap and no aliasing.
    Demonstrated during the audit: the direct analogue (assign to the input
    binder, ``tickColor := "black"``, then do the gold work) does not even PARSE
    here — ```tickColor` cannot be mutated, only variables declared using `let
    mut` can be mutated``, followed by ``Failed to parse an assertion without
    names: WPGen sorry``. So the rejection would be attributable to the parser,
    not to the spec, and no witness could make it a spec-attributable case. That
    is a genuine carrier fact, not a difficulty claim, and it is why the class is
    dropped rather than ported as a reject case. See the footer.
  * ADMISSIBILITY — APPLIES, and is PORTED (``admiss-f2p-shaped``). An earlier
    reading called this degenerate because both methods declare no ``require``,
    so there is no permission surface to establish. That reasoning was wrong on
    this carrier: the sibling's probe is a CALL on a freshly-built F2P-shaped
    input, and one contract here IS reachable from the other's body, so the
    class ports directly as a call-admissibility check. Confirmed with a real
    build (exit 0), i.e. it was expressible all along. An empty precondition
    should make it trivially true, which is precisely why a case that fails
    would be a real PRECOND-TOO-STRONG finding rather than noise.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a fully-unfolded pure function
    of the two input binders; there is no answer-key term a wrong impl could echo.
    The cheapest correct impl computes the selection honestly (the third positive).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``if`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
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
  * AXIOM lane — none in the sibling (AXIOM_TESTS = []); the modeled operation is
    a direct two-way selection between two available color strings, so there is no
    axiomatized callee. Dropped regardless (the axiom lane is G-AX's job).

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``xAxisOffsetColorTester tickColor labelColor = false`` says the extracted
program's result violates the postcondition at that concrete input. The gate
checks it in a file whose ``prove_correct`` blocks have been stripped (so no
tactic script can mask the verdict) and there are no ``require`` clauses, so
every input reaches the postcondition. The two methods are byte-identical but each
``ensures`` is a SEPARATE obligation, so every witness exercises BOTH testers at
each of its points — both ``xAxisOffsetColor`` and ``yAxisOffsetColor`` see every
reject input point. A witness may carry SEVERAL points, and a rival whose
rationale claims two broken sub-domains carries one per claim, so the witness
attests to exactly what the prose says and no less. ``String`` literals are fully
concrete, so ``decide`` settles the whole equality — no opaque term, no
conditioning, no head binders (hence no joint-satisfiability obligation). Every
witness here was rebuilt INDEPENDENTLY during the audit with two real
``scripts/lean_verify.sh`` builds: it ELABORATES green (exit 0) against its rival
and ERRORS (exit 1, ``decide proved that the proposition … is false`` — a decided
semantic refutation, not a missing name or a stuck reduction) against the frozen
solution.

CASE COUNT: 8 SPEC cases — 3 soundness positives, 4 uniqueness rivals, 1
admissibility control. Three cases changed during the audit; see the footer
accounting for what changed and why.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25287"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap_both(src, old, new):
    """Replace `old` in BOTH (byte-identical) impl regions.

    The two modeled methods (one per axis) have byte-identical gold impl bodies,
    so the body appears exactly twice and both lie strictly inside a
    ``-- impl-start``/``-- impl-end`` region. Replacing both keeps every spec
    region byte-identical (=> same_spec holds) while applying the attack/control
    symmetrically to both sites. Asserts the count so silent drift (Solution.lean
    edited) fails loudly at load.
    """
    n = src.count(old)
    if n == 0:
        raise AssertionError(f"drift: {old!r} not present")
    if n != 2:
        raise AssertionError(f"expected 2 impl occurrences, found {n}: {old!r}")
    return src.replace(old, new, 2)


# ---- impl-region anchor. The COMPLETE gold impl body shared by both methods;
# ---- lies wholly inside the `-- impl-start`/`-- impl-end` regions and occurs
# ---- exactly twice (asserted at load by _swap_both). Anchoring on the whole
# ---- body keeps every surgery inside the elided regions — the frozen spec (the
# ---- two `method` headers, the `ensures` clauses, and the `pure` region that
# ---- also spells out the selection) is never touched. ----
_IMPL = (
    '    if labelColor = "inherit" then\n'
    "      return tickColor\n"
    "    else\n"
    "      return labelColor"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the (doubled) impl body replaced."""
    return _swap_both(_BASE, _IMPL, new_impl)


def _with_second_impl(new_impl: str) -> str:
    """Solution.lean with only the SECOND (later-declared) impl body replaced.

    Needed by the admissibility case, whose probe CALLS the first-declared
    method: applied to both regions it would make that method call itself. The
    replaced text still lies wholly inside the second `-- impl-start`/
    `-- impl-end` region, so every spec region stays byte-identical and
    `markers.same_spec` still holds. Asserts the doubled anchor so drift in
    Solution.lean fails loudly at load, exactly as `_swap_both` does.
    """
    n = _BASE.count(_IMPL)
    if n != 2:
        raise AssertionError(f"expected 2 impl occurrences, found {n}")
    i = _BASE.rindex(_IMPL)
    return _BASE[:i] + new_impl + _BASE[i + len(_IMPL):]


# ---- witness preamble: reach the contract through Velvet's tester machinery.
# ---- The two methods are byte-identical, but each `ensures` is a SEPARATE
# ---- obligation, so every witness exercises BOTH testers at its point — that
# ---- way both `xAxisOffsetColor` and `yAxisOffsetColor` see every reject input
# ---- point (neither obligation is left probed at a single input). ----
def _tester(method: str) -> str:
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n")


def _witness(*points: tuple) -> str:
    """A refutation witness asserting the contract is violated at each point.

    Accepts SEVERAL `(tick, label)` points, not just one: a rival wrong on BOTH
    sub-domains must be refuted on both, else the witness attests to strictly
    less than the rationale claims (audit finding — the inverted-sentinel rival
    below claimed two broken sub-domains while its witness probed one).
    Every point is asserted against BOTH testers.
    """
    out = _tester("xAxisOffsetColor") + _tester("yAxisOffsetColor")
    for method in ("xAxisOffsetColor", "yAxisOffsetColor"):
        for tick, label in points:
            out += (f'example : {method}Tester "{tick}" "{label}" = false := by\n'
                    "  decide\n\n")
    return out.rstrip() + "\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each verified out-of-band with a
    # real build against the frozen proof script.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different: test the ORDINARY (non-sentinel) branch first,
        # the sentinel fallback second — the mirror image of the frozen control
        # flow. Same selection, different source. Ports the nagini branch-reorder
        # positive (`pos-control-reordered`). No induction/lemma (a single if/else
        # over a decidable String equality), so the frozen proof still closes.
        "module": _with_impl(
            '    if labelColor ≠ "inherit" then\n'
            "      return labelColor\n"
            "    else\n"
            "      return tickColor"),
        "rationale": (
            "structurally-different (ordinary branch first, sentinel fallback "
            "second) but semantically identical impl must verify against `out = "
            "offsetColor tickColor labelColor`. If it fails to verify the "
            "postcondition is over-fit to one branch ordering => SPEC-TOO-STRONG. "
            "Verified out-of-band with a real build against the frozen proof "
            "script. (Sibling: pos-control-reordered.)"),
    },
    {
        "id": "pos-single-let",
        "kind": "soundness",
        "expect": "verify",
        # A different executable shape: bind the selection to a single `let` local
        # via a conditional expression, then return it (one local, no branching
        # return). Observationally identical to gold. Ports the sibling's
        # single-assignment positive (`pos-control-single-assign`).
        "module": _with_impl(
            '    let result := if labelColor = "inherit" then tickColor else labelColor\n'
            "    return result"),
        "rationale": (
            "a correct impl with a different executable shape — the selection is "
            "bound to a single `let` local via a conditional expression, then "
            "returned — must verify. Same value on both branches. If it fails the "
            "spec is over-fit to the explicit branching-return form => "
            "SPEC-TOO-STRONG. Verified out-of-band with a real build. (Sibling: "
            "pos-control-single-assign.)"),
    },
    {
        "id": "pos-cheapest-echo",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent selection
        # `offsetColor tickColor labelColor` directly. Because `offsetColor` is a
        # spelled-out `def` over the two inputs (not an opaque oracle), this still
        # performs the real selection — there is no wrong echo that verifies.
        # Re-expresses the sibling's honest cheapest-impl control (`echo-honest`).
        "module": _with_impl("    return offsetColor tickColor labelColor"),
        "rationale": (
            "the cheapest impl satisfying the clause returns the transparent "
            "selection directly. Because the post-image `offsetColor` is a "
            "spelled-out function of the two inputs — not an axiomatized answer "
            "key — this still does the real work; there is no wrong echo that "
            "could verify (else this would be a reject case). Demonstrates the "
            "spec is NOT echo-vulnerable. Must verify. (Sibling: echo-honest.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input (ELABORATES against the rival, FAILS against gold —
    # both halves confirmed out-of-band with real builds) and the refinement
    # argument for why its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "rival-tick-always-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (the pre-change behaviour): always paint with the tick
        # color, ignoring the configured label color. Correct on the sentinel
        # sub-domain (labelColor = "inherit" ⟹ tick color, which gold also
        # returns) but WRONG on the ordinary sub-domain (a configured label color
        # must govern) — the exact sub-domain the failing test exercises.
        "module": _with_impl("    return tickColor"),
        "refinement": (
            "this IS the base-commit behaviour: the exponent text is painted with "
            "the axis tick color unconditionally, ignoring a configured "
            "tick-label color. The failing test configures a distinct label color "
            "and asserts the exponent text follows it; this rival keeps the tick "
            "color, so the assertion FAILS — it does NOT resolve. This is the "
            "modeled bug and the prepatch discriminator (G-DIFF). Correct on every "
            "input where the label color is the inherit sentinel (a true "
            "partial-domain break, not a blanket wrong impl)."),
        "rationale": (
            "REJECT from `out = offsetColor tickColor labelColor`: on `labelColor "
            "≠ \"inherit\"` the post-image is `labelColor` but this impl returns "
            "`tickColor`, so the two Strings differ. Correct on the sentinel "
            "sub-domain, wrong on exactly the ordinary sub-domain. If it verified "
            "=> SPEC-TOO-WEAK (admits the original bug). Refuted at "
            "tickColor=\"red\", labelColor=\"blue\" — the point where a configured "
            "label color must win. (Sibling: rival-base-always-prepatch.)"),
        "witness": _witness(("red", "blue")),
    },
    {
        "id": "rival-label-always",
        "kind": "uniqueness",
        "expect": "reject",
        # The OPPOSITE half-bug: drop the sentinel fallback entirely and always
        # paint with the label color. Correct on the ordinary sub-domain
        # (labelColor ≠ "inherit" ⟹ label color) but WRONG on the sentinel
        # sub-domain, where the text must fall back to the tick color: this returns
        # the literal string "inherit" instead. Carries the sentinel point so
        # `labelColor` is not pinned at a configured value.
        "module": _with_impl("    return labelColor"),
        "refinement": (
            "drops the sentinel fallback: the exponent text always follows the "
            "tick-label color setting. When that setting is left at the inherit "
            "sentinel, this stores the literal sentinel string rather than falling "
            "back to the tick color; a scenario with the label color at the "
            "sentinel and a distinct tick color asserts the exponent text follows "
            "the tick color, and this rival shows the sentinel string — the "
            "assertion FAILS, so it does NOT resolve. Correct on every input with "
            "a configured (non-sentinel) label color."),
        "rationale": (
            "REJECT from `out = offsetColor tickColor labelColor`: on `labelColor "
            "= \"inherit\"` the post-image is `tickColor` but this impl returns "
            "`labelColor` (the sentinel string), so the two Strings differ. Pins "
            "the sentinel sub-domain the prepatch rival satisfies — the ONLY rival "
            "on which the tick-color fallback is the deciding value. If it "
            "verified => SPEC-TOO-WEAK (the sentinel fallback clause unenforced). "
            "Refuted at tickColor=\"red\", labelColor=\"inherit\". (Sibling: "
            "rival-label-always.)"),
        "witness": _witness(("red", "inherit")),
    },
    {
        "id": "rival-inverted-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow flip: take the LABEL color on the sentinel and the TICK
        # color otherwise — the branches selected on the inverted condition. Wrong
        # on BOTH sub-domains, and the witness now refutes it on BOTH: at a
        # configured label color distinct from the tick color (where it wrongly
        # returns the tick color) AND at the sentinel (where it wrongly returns
        # the sentinel string instead of falling back to the tick color).
        "module": _with_impl(
            '    if labelColor = "inherit" then\n'
            "      return labelColor\n"
            "    else\n"
            "      return tickColor"),
        "refinement": (
            "inverts the sentinel comparison: a configured label color is ignored "
            "(the tick color is used) and the sentinel case emits the sentinel "
            "string. A faithful patch of this shape mis-colors every exponent "
            "text — a configured label color loses to the tick color and the "
            "sentinel default shows the literal sentinel string — so both failing "
            "assertions fail; it would NOT resolve."),
        "rationale": (
            "wrong on BOTH sub-domains: on `labelColor ≠ \"inherit\"` the "
            "post-image is `labelColor` but this returns `tickColor`; "
            "(independently, on the sentinel it returns the sentinel string where "
            "the post-image wants `tickColor`). REJECT from `out = offsetColor "
            "tickColor labelColor`. If it verified => SPEC-TOO-WEAK (the "
            "conditional direction unconstrained). Refuted at BOTH claimed "
            "points, so the witness attests to everything this rationale says: "
            "tickColor=\"green\", labelColor=\"yellow\" (ordinary arm — a "
            "configured label ≠ tick color must win) AND tickColor=\"green\", "
            "labelColor=\"inherit\" (sentinel arm — the fallback must be the "
            "tick color, not the sentinel string). "
            "(Sibling: rival-inverted-sentinel.)"),
        "witness": _witness(("green", "yellow"), ("green", "inherit")),
    },
    {
        "id": "rival-widened-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D landed as a case). A NEAR-MISS the three ported
        # rivals leave unattacked: they all break a WHOLE sub-domain, so nothing in
        # the battery pinned the sentinel's EXTENSION — that the fallback triggers
        # on exactly one distinguished value and not on any other
        # "no color configured"-looking value. This rival keeps the frozen shape and
        # both branch bodies, and only widens the fallback test to a second value,
        # so it agrees with gold on every input except that one.
        "module": _with_impl(
            '    if labelColor = "inherit" || labelColor = "none" then\n'
            "      return tickColor\n"
            "    else\n"
            "      return labelColor"),
        "refinement": (
            "treats a second value as a second 'nothing configured' sentinel. That "
            "value is a legitimate explicitly-configured color setting, so a "
            "faithful patch of this shape silently substitutes the tick color for "
            "it: a scenario configuring that label color and asserting the exponent "
            "text follows it sees the tick color instead — the assertion FAILS, so "
            "it does NOT resolve. Agrees with the desired behaviour on every other "
            "input, which is exactly what makes it the sharp near-miss."),
        "rationale": (
            "REJECT from `out = offsetColor tickColor labelColor`: the post-image "
            "falls back to `tickColor` on the ONE sentinel value and returns "
            "`labelColor` for every other, so at labelColor=\"none\" the post-image "
            "is \"none\" while this impl returns `tickColor`. Pins the sentinel's "
            "EXTENSION rather than a whole sub-domain — the clause no ported rival "
            "probes: all three break an entire branch, so a spec that only forced "
            "'some fallback set containing inherit' would still reject them. If it "
            "verified => SPEC-TOO-WEAK (the sentinel under-determined). Refuted at "
            "tickColor=\"black\", labelColor=\"none\"; adds a fourth distinct input "
            "point and two new binder values. (No sibling: this closes a gap the "
            "nagini battery also left open.)"),
        "witness": _witness(("black", "none")),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # ADDED BY AUDIT (attack F: the port recorded the sibling's admissibility
        # case as DEGENERATE/inexpressible; it is expressible here). The class does
        # NOT reduce to "there is no `require` clause": on this carrier one contract
        # is reachable from the other's body, so the sibling's probe — drive the
        # sister contract on a freshly-built F2P-shaped literal input, discard the
        # result, then do the real work — ports directly as a CALL admissibility
        # check. It asks whether a representative input is actually admitted at a
        # call site, which an empty precondition should make trivially true but
        # which nothing else in the battery demonstrates.
        # Only the SECOND (later-declared) method's body carries the probe: the
        # call names the FIRST method, so applying it to both would turn that one
        # into a self-call. `_with_second_impl` keeps the surgery inside the second
        # impl region, so every spec region is still byte-identical.
        "module": _with_second_impl(
            '    let _probe ← xAxisOffsetColor "yellow" "blue"\n'
            '    if labelColor = "inherit" then\n'
            "      return tickColor\n"
            "    else\n"
            "      return labelColor"),
        "rationale": (
            "a call on a freshly-built representative input (an ordinary "
            "configured label color distinct from the tick color — the shape the "
            "failing scenario uses) must be ADMITTED, and the caller's own "
            "obligation must still discharge afterwards. Both methods declare no "
            "`require`, so the precondition should admit every input; if this "
            "cannot be established => PRECOND-TOO-STRONG. Verified with a real "
            "build (exit 0). (Sibling: admiss-f2p-shaped — ported, not dropped.)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (3 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation rival, 3 uniqueness
# rivals; AXIOM_TESTS = []). This bundle models the SAME functional core (the
# per-axis exponent-text color selection) at BOTH sites as two byte-identical
# `method`s over two `String` inputs, pins each with a single `ensures out =
# offsetColor tickColor labelColor`, runs with NO precondition and NO permission
# surface. The soundness/uniqueness lanes port directly; the permission and
# precondition classes are vacuous/degenerate on this carrier.
#
#   sibling case                  kind          -> here                       disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-reordered         soundness     -> pos-branch-reorder         PORTED
#   pos-control-single-assign     soundness     -> pos-single-let             PORTED (re-shaped)
#   echo-honest                   soundness     -> pos-cheapest-echo          RE-EXPRESSED
#   admiss-f2p-shaped             admissibility -> admiss-f2p-shaped          PORTED (audit: was wrongly dropped)
#   frame-mutation-base           uniqueness    -> (none)                     VACUOUS (no heap; parse-level, measured)
#   rival-base-always-prepatch    uniqueness    -> rival-tick-always-prepatch PORTED (the bug)
#   rival-label-always            uniqueness    -> rival-label-always         PORTED
#   rival-inverted-sentinel       uniqueness    -> rival-inverted-sentinel    PORTED (audit: witness widened to both arms)
#   AXIOM_TESTS ([])              axiom         -> (none)                     N/A (empty in sibling)
#   (no sibling)                  uniqueness    -> rival-widened-sentinel     ADDED by audit (sentinel EXTENSION)
#
# 4 uniqueness (3 ported + 1 added) + 3 soundness ported (one re-shaped, one
# re-expressed) + 1 admissibility ported; 1 frame-mutation vacuous; no axiom lane
# in sibling. 8 SPEC cases (3 soundness, 4 uniqueness, 1 admissibility).
#
# RE-SHAPED (pos-control-single-assign -> pos-single-let): the sibling's positive
#   initialises a local to the label color then overrides to base on the sentinel.
#   On this carrier the natural single-local reshape binds the whole conditional
#   to one `let` and returns it — one local, no branching return, same value.
# RE-EXPRESSED (echo-honest -> pos-cheapest-echo): the sibling asserts the built
#   color equals the grounded @Pure oracle before returning. Here `offsetColor` is
#   a transparent `def` (no opaque answer-key), so returning it directly is the
#   honest cheapest correct impl and carries the same no-wrong-echo argument.
# PORTED, was wrongly dropped (admiss-f2p-shaped): an earlier reading recorded
#   this class as DEGENERATE on the grounds that both methods declare no `require`
#   clause, so there is no permission surface to establish. The AUDIT overturned
#   that: the sibling's probe is a CALL on a freshly-built F2P-shaped input, and
#   one contract here is reachable from the other's body, so the class ports
#   directly as a call-admissibility check (built during the audit, exit 0). It is
#   now a real case. The empty precondition makes it cheap and expected to pass —
#   which is the point of a control: were it to fail, PRECOND-TOO-STRONG. The
#   separate non-degeneracy question (a post-image every impl meets) is answered
#   by the reject lane, now four rivals at four distinct input points.
# VACUOUS (frame-mutation-base): the sibling's MANDATORY frame rival item-assigns
#   into the read-only `base_color` input, held at `Acc(list_pred(base_color),
#   1/2)`, and is rejected by the insufficient-permission check. This backend is
#   referentially transparent: `tickColor` and `labelColor` are immutable `String`
#   values, no `mut` binder is declared, and there is no heap, no aliasing, and no
#   permission system. MEASURED during the audit rather than asserted: the direct
#   analogue (`tickColor := "black"` ahead of the gold work) fails to PARSE —
#   "`tickColor` cannot be mutated, only variables declared using `let mut` can be
#   mutated", then "Failed to parse an assertion without names: WPGen sorry". A
#   rejection at the parser attributes nothing to the spec and no witness can
#   repair that, so the class has no carrier analogue as a reject case. Omitted as
#   a demonstrated carrier fact, NOT fabricated and NOT a difficulty claim.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
#   frozen impl region is LOOP-FREE (straight-line ``if`` over immutable
#   values, no loop and no recursion), so there is no control flow here to make
#   diverge: a diverging rival cannot be obtained by mutating this body, it has
#   to bring a loop of its own. When it does, the semantics refuse it. This
#   bundle sets ``loom.semantics.termination "total"`` AND carries
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
# BINDER / CLAUSE COVERAGE. The single `ensures out = offsetColor tickColor
#   labelColor` (identical at both methods) binds `out`, `tickColor`, and
#   `labelColor`; the model combines the SENTINEL branch (labelColor = "inherit"
#   ⟹ tickColor) and the ORDINARY branch (labelColor ≠ "inherit" ⟹ labelColor).
#   Both branches are attacked, and so is the sentinel's EXTENSION:
#     * ORDINARY (configured label color governs): rival-tick-always-prepatch (the
#       bug) and rival-inverted-sentinel both fail here.
#     * SENTINEL (fall back to tick color): rival-label-always fails here, and
#       rival-inverted-sentinel is now ALSO refuted here (audit: its witness
#       covered only the ordinary arm while its rationale claimed both, so it
#       attested to less than it said; widened to both points).
#     * SENTINEL EXTENSION (the fallback fires on exactly ONE value):
#       rival-widened-sentinel fails here. Added by the audit — all three ported
#       rivals break a WHOLE sub-domain, so none of them distinguished this spec
#       from a weaker one admitting any fallback set containing the sentinel.
#   The four reject witnesses probe FIVE distinct input tuples, each exercising
#   BOTH obligations (`xAxisOffsetColor` AND `yAxisOffsetColor`):
#     * rival-tick-always-prepatch  ("red",   "blue")
#     * rival-label-always          ("red",   "inherit")
#     * rival-inverted-sentinel     ("green", "yellow") AND ("green", "inherit")
#     * rival-widened-sentinel      ("black", "none")
#   So `labelColor` ranges over {"blue", "inherit", "yellow", "none"} (the
#   sentinel, two ordinary configured colors, and one near-miss value that only a
#   correct sentinel test rejects as a fallback trigger) and `tickColor` over
#   {"red", "green", "black"}; on every ordinary-branch witness tickColor differs
#   from labelColor, so the tick/label distinction is observable at each. Both
#   obligations see all five input points. Every top-level clause of the
#   postcondition is attacked and every input binder is varied MEANINGFULLY (each
#   value changes which arm the model takes or which input the result equals).
# WITNESS DISCRIMINATION (re-derived INDEPENDENTLY during the audit with two real
#   builds per reject case, not merely inherited from authoring): each witness
#   ELABORATES against its loop-free rival (exit 0 — the extracted program's
#   result provably violates the ensures at the probed input, `<method>Tester … =
#   false` closing by `decide`) and FAILS against the frozen solution (exit 1)
#   with the SEMANTIC message `Tactic `decide` proved that the proposition
#   <method>Tester "<tick>" "<label>" = false is false` at every probed point —
#   i.e. gold's result agrees with the model there. That message is the thing that
#   matters: the gold-side failure is a decided refutation of the concrete claim,
#   not an unknown identifier, a type error, an unfolding failure, a stuck
#   reduction, or a timeout, any of which would make the exit code attest to
#   nothing. The carrier is fully concrete at every witness (String literals), so
#   each closes by `decide` with no hypothesis and there is no joint-
#   satisfiability obligation (consistency_probe is None for all four). No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
# SPEC STRENGTH, probed beyond the battery (audit attacks D and E, real builds):
#   five ADDITIONAL wrong impls not in this battery were built against the frozen
#   spec and ALL were rejected on the postcondition with `unsolved goals` —
#   sentinel test against the empty string; the sentinel tested on the wrong input;
#   the two selection arguments transposed; a length-equality side condition; and
#   the widened fallback (which was good enough to keep, above). Six correct
#   reshapes were built and ALL verify — orientation-flipped equality, a
#   double-negated test, a `let`-bound sentinel name, a `match` on `==`, a `let
#   mut` initialise-then-override, and one method delegating to the other's
#   contract. So the spec is neither too weak nor over-fit on this surface: no
#   hole found, and no faithful correct impl rejected.
#
# AXIOM_TESTS: none in the sibling (the modeled operation is a direct two-way
# selection between two available color strings — no axiomatized callee, no deep
# model; mapping.md §3). The axiom lane is G-AX's job and this gate ignores it
# regardless.
AXIOM_TESTS = []

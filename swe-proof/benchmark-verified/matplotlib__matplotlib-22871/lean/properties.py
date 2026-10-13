"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-22871 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_tickOffset``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the decision as a six-argument function over six separate read-only
integer columns ``c0..c5``, with two ``@Pure`` helpers (``col_varies`` /
``col_has_one``) and fractional-permission contracts on every column. This Lean
bundle models the SAME single behavior over a DIFFERENT carrier: one
``List (List Nat)`` of per-tick component rows plus the default display flag,
returning the pair ``(chosen level, resulting display flag)``. So the six
per-column binders collapse into ONE list binder whose inner rows carry the
components positionally, and a second ``Bool`` binder appears that nagini does
not have (see the CARRIER DELTA note). Every nagini spec-lane case maps to a
counterpart here except the permission-mutation lane; the per-case mapping and
the principled omissions are in the module ``assessment`` of the submitted
payload and are restated inline below.

DEFENDED SURFACE (one modeled obligation, ``correct_tickOffset``, over two
independent top-level conjuncts of ``problem_spec_tickOffset``):

  * CLAUSE 1 — ``result.1 = specLevel td``. The chosen level is the FIRST
    component, scanning finest→coarsest over the fixed index sequence
    ``[5,4,3,2,1,0]``, that takes more than one distinct value across the ticks;
    and the FINEST index (5) when every component is constant. This pins both
    the scan DIRECTION and the all-constant fallback.
  * CLAUSE 2 — ``result.2 = specShowOffset td s0``. The display flag is the
    default ``s0``, turned off exactly when the selected component index is one
    of the two coarsest (``j < 2``) AND the value ``1`` occurs in that component
    across the ticks. Three independent sub-terms live here: the ``j < 2``
    coarseness threshold, the ``contains 1`` conjunct, and the pass-through of
    ``s0`` on every other input.

The BEHAVIOURAL DISCRIMINATOR (the fix) is the ``contains 1`` conjunct on the
coarse-level suppression guard: a coarse component that varies but never takes
the value ``1`` must KEEP the summary label displayed. The reported scenario is
exactly that shape — a sub-year span whose coarse component varies over a range
that skips the value ``1`` — and the pre-fix behavior hid the label there, which
is the defect. Rival ``weak-coarse-suppress-unconditional`` IS that pre-fix
behavior, transcribed onto this carrier.

CARRIER DELTA (why this port is NOT a case-count match to nagini). Two
differences, both of which move coverage rather than shrink it:

  * COLLAPSED BINDERS. nagini's six independent column arguments ``c0..c5``
    become positional slots inside the rows of one ``td`` binder. nagini's
    separate month-level and year-level offset clauses (its cases 2 and 3) are
    therefore not two clauses here — they are the SAME clause instantiated at
    ``j = 1`` and ``j = 0``. Both instantiations are still attacked, by
    ``weak-coarse-suppress-unconditional`` (which fires at the month slot) and
    ``weak-year-suppress-unconditional`` (which fires at the year slot and is
    CORRECT at the month slot, so it is a strict NEAR-MISS of the first and
    carries its own refutation point rather than sharing one).
  * A NEW BINDER. This spec takes the default display flag ``s0`` as an explicit
    input and pins the result to pass it through everywhere the suppression guard
    does not fire; nagini's model hardcodes the default. That binder is
    load-bearing and gets its own rival (``weak-ignore-default-flag``), refuted
    at ``s0 = false`` — the ONLY witness that moves it, so the spec's dependence
    on it is demonstrated live rather than assumed.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. nagini's mandatory lane (case 1,
    ``frame-mutation-write-c1``: store into a column held at half permission so
    the value-``1`` test becomes vacuously true) has no expressible instance
    here. Lean is referentially transparent: ``td`` is a value, there is no heap
    permission to be short of, no aliasing, and no store form in the impl region
    to write. The rival cannot be TYPED, let alone rejected for the reason nagini
    rejects it. No substitute is fabricated — a rival that merely computed the
    wrong answer would be a different case, already covered by the
    partial-domain lane, and labelling it a frame case would misattribute the
    rejection.
  * DIVERGENCE / NON-TERMINATION — APPLIES, and ships (``diverge-measure-free-
    scan``). CORRECTED BY AUDIT. This entry previously recorded the class as
    VACUOUS on the claim that "a diverging rival cannot be WRITTEN at all: the
    elaborator demands termination before the spec is ever consulted". That claim
    is FALSE and was measured false: a plain recursive ``def`` with no decreasing
    measure is indeed refused (``fail to show termination for``, so THAT shape is
    unwritable), but ``partial def`` is accepted by the elaborator and yields a
    well-typed impl carrying no termination argument. This bundle sets no
    ``loom.semantics.termination``, so the frozen obligation must still be
    discharged for such an impl and it is genuinely REJECTED — i.e. the class was
    shippable all along, and the port was UNDERPORTED here rather than complete.
    The residual difficulty is only the WITNESS: a ``partial`` term is
    kernel-irreducible, so the plain ``decide`` every other witness uses gets
    stuck on the rival (measured: ``did not reduce to `isTrue` or `isFalse` ``),
    and the naive ``omega`` refutation gets stuck symmetrically on GOLD's
    unreduced ``do`` block — with an error byte-identical to the one the FLIPPED
    claim produces, i.e. carrying no information. The shipped witness is stated so
    that its failure tracks the claim on both sides; see that case's own note.
    (Backend note retained: on velvet under partial termination semantics this
    same class is instead a genuine SPEC HOLE, since a non-terminating impl
    satisfies every ensures clause vacuously and VERIFIES while its faithful patch
    hangs the test; see ``the corpus-wide termination-semantics finding``. Here the obligation is
    not vacuous, so the case is a normal reject.) The nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` case, so this one is originated here, not ported.
  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``problem_spec_tickOffset`` is fully
    GROUNDED: both conjuncts equate ``result`` to terms built only from ``td``
    and ``s0`` by transparent list operations (``map`` / ``dedup.length`` /
    ``contains`` / ``find?``). The bundle declares NO ``opaque`` callee and
    consumes NO ``axiom``, so there is no answer key for an impl to echo and no
    term that blocks refutation. Consequently every witness below is a plain
    ``decide`` at literal inputs — the conditioning-on-the-carrier technique is
    not needed here, and no witness binds a hypothesis (so none can be
    ``witness-inconsistent``). The one exception is the divergence rival, whose
    IMPL (not the spec) is irreducible; its witness leads with the same ``decide``
    and falls back to an arithmetic refutation only where that cannot reduce.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the reject lane. Seven
    rivals, each correct on part of the domain and diverging where one sub-term of
    one clause bites.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen proof normalizes the ``Id.run`` loop through an
explicitly transcribed nested-``if`` term, so ANY change to the loop body breaks
it whether or not the change is wrong. (Measured here: TWO of the five CORRECT
reshapes in the soundness lane below fail to build under the unmodified frozen
tactic script even though they are behaviourally identical to it, which is
precisely why those two ship a re-proof; the other three survive it because their
added locals zeta-reduce. Sentence corrected by audit — it previously read "all
five ... also fail", which the same paragraph then contradicted and which the
recorded per-case outcomes disprove.) A rejection alone therefore attributes
nothing to the spec. Every ``expect="reject"`` case accordingly carries a Lean
snippet stating ``¬ problem_spec_tickOffset td s0 (implementation_tickOffset td
s0)`` at ONE concrete input. Each was built both ways before shipping: it
ELABORATES against its rival, and on the frozen solution ``decide`` reports that
it proved the proposition FALSE — i.e. gold satisfies the spec at that point — so
each is a real discriminator rather than a tautology. (The divergence rival is
the one case whose rival side cannot be decided, because a ``partial`` term does
not reduce in the kernel; its witness keeps the same ``decide`` as the leading
alternative — which is what fires on GOLD — so the gold-side exit still tracks
the claim. Verified by flipping the claim: gold then builds clean.)

BINDER / POINT SPREAD. The eight reject witnesses probe SEVEN DISTINCT inputs
(the eighth, the divergence rival, reuses the reported-shape point — see below)
and move both spec binders:

  * ``s0`` takes ``true`` (seven witnesses) and ``false``
    (``weak-ignore-default-flag``) — the flag is not held fixed.
  * ``td`` ranges over: a single row (all components constant); two rows varying
    only in the finest component; two rows varying in the finest AND the coarsest
    component simultaneously; a coarse component varying WITH the value ``1``
    present; a coarse component varying WITHOUT it; the month slot varying vs the
    year slot varying; and a mid-level (day) component varying with ``1``
    present. Row COUNT varies (1 and 2) and the varying SLOT ranges over
    ``{0, 1, 2, 5}``, so both the scan direction and the coarseness threshold are
    probed from each side.
  * No two VALUE rivals share a witness. The two nearest neighbours
    (``weak-coarse-suppress-unconditional`` and
    ``weak-year-suppress-unconditional``) are refuted at the month slot and the
    year slot respectively, because the second AGREES with gold at the month slot
    and a shared point would claim a sub-domain the manifest never demonstrates.
    Cross-checked by build rather than by argument: the month witness does NOT
    elaborate against the year rival (which is correct there), while the year
    witness DOES elaborate against the month rival (which is wrong at both), so
    the near-miss containment the two rationales claim is the measured one.
  * ``diverge-measure-free-scan`` deliberately REUSES the reported-shape point of
    ``weak-coarse-suppress-unconditional``, and this is not a spread gap: its
    defect is not a wrong value at a distinguishing input but the absence of a
    terminating computation at EVERY input, so any input refutes it and picking a
    fresh one would only imply the choice mattered. It is refuted on a different
    CONJUNCT than that rival (the level, not the flag) and by a different
    mechanism (an arithmetic bound rather than evaluation of the rival).

AUDIT RESIDUE — a TACTIC-BRITTLENESS boundary, recorded because it is a real
property of this bundle and not a spec hole. The frozen impl tests
``1 < column.dedup.length``; the reshape that spells the SAME proposition
``2 ≤ column.dedup.length`` is behaviourally identical (the two are the same
``Nat.le`` term up to notation) but does NOT verify under the frozen tactic body,
and does not verify either when the transcribed normal form and the six
``by_cases`` hypotheses are rewritten to match — that route hits
``(deterministic) timeout at `whnf` `` rather than a spec failure. It DOES verify
once the normalization step additionally carries ``Nat.lt_iff_add_one_le`` in its
``simp only`` set. So the reshape is admissible and the spec accepts it; what
rejects the naive port of it is the proof script's normalization set, which is
tactic brittleness rather than SPEC-TOO-STRONG. Not shipped as a positive: a case
whose pass depends on that particular ``simp`` lemma would document the frozen
script's normalization set rather than the spec's tolerance, which is not what the
soundness lane is for. Recorded here so the next reader does not re-derive it and
mistake the timeout for a soundness hole.

AXIOM lane: EMPTY. This bundle declares no ``opaque`` and consumes no ``axiom``
(both column observations are modeled deeply), so G-AX has nothing to check
here. The nagini ``AXIOM_TESTS`` (two deep-model probes executing real numpy
reductions) belong to the G-AX lane, which this gate ignores; they are dropped.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22871"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is verified unique at load time by `_swap`, and each lies
# ENTIRELY inside the impl region (or, for the two cases that legitimately
# re-prove, inside the proof region) so the spec view stays byte-identical.
# ---------------------------------------------------------------------------

# The coarse-level suppression guard: the CHANGED sub-term of clause 2.
_I_GUARD = ("      if decide (lvl < 2) && column.contains 1 then\n"
            "        showOffset := false\n")

# The initialisation of the running display flag from the default input.
_I_SHOW0 = "  let mut showOffset : Bool := s0\n"

# The initialisation of the running level.
_I_LEVEL0 = "  let mut level : Nat := 5\n"

# The scan header over the fixed finest→coarsest index sequence.
_I_FOR = "  for lvl in levels do\n"

# The all-constant fallback that resets to the finest index.
_I_RESET = "    else if lvl = 0 then\n      level := 5\n"

# The column binding at the head of the loop body.
_I_COL = "    let column := colVals td lvl\n"

# The level assignment that precedes the suppression guard.
_I_ASSIGN = "      level := lvl\n"

# The `varies` test plus the two statements that follow it, as one block.
_I_TESTBLOCK = (_I_COL
                + "    if 1 < column.dedup.length then\n"
                + _I_ASSIGN
                + _I_GUARD)

# The frozen proof body of the obligation (proof region).
_P_FROZEN = "  intro td s0\n  exact ⟨level_eq td s0, show_eq td s0⟩"

# The WHOLE impl definition, for the one rival that replaces the loop outright
# rather than editing inside it. Sliced from the impl region's markers so it
# cannot silently drift, and asserted non-empty at load time.
_I_IMPL = _BASE[_BASE.index("def implementation_tickOffset"):
                _BASE.index("-- impl-end")].rstrip("\n")
if "Id.run" not in _I_IMPL:
    raise AssertionError("drift: impl region no longer holds the monadic loop")


def _guard(new):
    """A variant differing ONLY in the coarse-level suppression guard."""
    return _swap(_BASE, _I_GUARD, new)


def _deepen_splits(src):
    """Deepen the proof's per-scan-step branch tactic by one `split`.

    The frozen script closes each scan step of the impl/normal-form match with
    `split <;> rfl`, which handles the guard's single `if`. A variant that splits
    that guard into two nested `if`s has one more branch level at every step, so
    each step's tactic gains one `split` on the arm that carries it. Inside the
    proof region; the obligation's statement is untouched and nothing is assumed.
    """
    for h in ("h5", "h4", "h3", "h2", "h1", "h0"):
        src = _swap(src,
                    f"  · simp only [{h}, if_true]; split <;> rfl",
                    f"  · simp only [{h}, if_true]; "
                    f"split <;> [split <;> rfl; rfl]")
    return src


def _reprove_impl_bridge(src, tactic):
    """Replace the impl-normalization lemma's TACTIC BODY with `tactic`.

    The frozen script bridges the monadic loop to the transcribed nested-`if`
    normal form with a six-step `simp`/`by_cases` script tuned to `Id.run` and
    `List.forIn_cons`. A variant that abandons the loop has no monadic binds to
    eliminate, so that script no longer applies — and for a shape that reduces to
    the normal form definitionally the honest bridge is simply `rfl`. Only the
    lemma's tactic body changes: its STATEMENT, both atom lemmas, and the
    obligation's own body are untouched, so the obligation is re-proved for the
    new impl rather than weakened. Inside the proof region.
    """
    head = ("theorem impl_to_nestedIf (td : List (List Nat)) (s0 : Bool) :\n"
            "    implementation_tickOffset td s0 = runReduce td s0 := by")
    if src.count(head) != 1:
        raise AssertionError("drift: impl_to_nestedIf header")
    start = src.index(head) + len(head)
    end = src.index("/-- Atom 1", start)
    return src[:start] + "\n" + tactic + "\n\n" + src[end:]


def _reprove_normal_form(src, rewrite):
    """Apply `rewrite` to the proof region's transcribed normal form.

    The frozen proof normalizes the loop by transcribing it as an explicit
    nested-`if` term (`runReduce`) and matching definitionally. A variant that
    changes the guard's SYNTACTIC form therefore breaks that match even when it
    is behaviourally identical, so such a variant must commute the SAME change
    into the transcribed term. Both edits are inside the proof region, the
    obligation's statement is untouched, and nothing is assumed — the obligation
    is re-proved for the new impl rather than weakened.
    """
    for j in (5, 4, 3, 2, 1, 0):
        old = (f"    ({j}, if decide ({j} < 2) && (colVals td {j}).contains 1 "
               f"then false else s0)")
        src = _swap(src, old, rewrite(j))
    return src


# A witness: the spec predicate refuted at one concrete, fully literal input.
# `decide` reaches it because the whole carrier computes — no opaque term, and
# hence no hypothesis binder to be inconsistent.
def _witness(td, s0, note):
    return (f"{note}\n"
            f"example : ¬ problem_spec_tickOffset {td} {s0}\n"
            f"    (implementation_tickOffset {td} {s0}) := by\n"
            f"  unfold problem_spec_tickOffset\n"
            f"  decide\n")


# Reusable literal tick tables. Component order is coarsest→finest within a row:
# slot 0 the coarsest, slot 5 the finest.
_TD_MONTH_NO_ONE = "[[1997, 2, 1, 0, 0, 0], [1997, 3, 1, 0, 0, 0]]"
_TD_MONTH_HAS_ONE = "[[1997, 1, 1, 0, 0, 0], [1997, 2, 1, 0, 0, 0]]"
_TD_YEAR_NO_ONE = "[[1996, 1, 1, 0, 0, 0], [1997, 1, 1, 0, 0, 0]]"
_TD_DAY_HAS_ONE = "[[1997, 1, 1, 0, 0, 0], [1997, 1, 2, 0, 0, 0]]"
_TD_FINE_AND_COARSE = "[[1996, 1, 1, 0, 0, 1], [1997, 1, 1, 0, 0, 2]]"
_TD_ALL_CONSTANT = "[[2021, 3, 4, 5, 6, 7]]"
_TD_F2P_SHAPED = ("[[1997, 2, 14, 0, 0, 0], [1997, 3, 14, 0, 0, 0], "
                  "[1997, 7, 14, 0, 0, 0]]")


SPEC_TESTS = [
    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each is a wrong implementation
    # sharing the frozen spec that MUST be rejected, and each carries (a) the
    # refinement argument that its faithful real patch would NOT resolve the
    # F2P, so a VERIFYING rival would be a true verify-does-not-imply-resolve
    # break rather than an artifact of tactic breakage, and (b) a refutation
    # witness pinning the violation at one concrete input, checked to hold of
    # the rival and to fail on the frozen solution.
    # =====================================================================

    # ---- the fix itself (ports nagini case 2, its month-level pre-patch
    # ---- rival, onto the collapsed carrier) ----
    {
        "id": "weak-coarse-suppress-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: once the selected component is one of the two
        # coarsest, hide the summary label UNCONDITIONALLY — never test whether
        # the value 1 occurs in that component.
        "module": _guard("      if decide (lvl < 2) then\n"
                         "        showOffset := false\n"),
        "refinement": "this IS the pre-fix behavior, and the whole content of "
                      "the fix is the dropped conjunct. In the reported "
                      "scenario the span covers under a year and its coarse "
                      "component varies over a range that never takes the "
                      "value 1, so this rival hides the summary label and the "
                      "coarser context is displayed NOWHERE — exactly the "
                      "user-visible defect the issue reports and the F2P "
                      "asserts against (it demands the coarse summary be "
                      "non-empty for that span). The faithful real patch of "
                      "this rival is the UNFIXED code, so it plainly does NOT "
                      "resolve. It is a partial-domain miss, not a total one: "
                      "every span whose varying coarse component DOES contain "
                      "the value 1 still behaves correctly, which is why the "
                      "pre-existing assertions in the same test continue to "
                      "hold and only the newly added one fails.",
        "rationale": "REJECT from clause 2 (`result.2 = specShowOffset td s0`), "
                     "specifically its `colHasOne td j` conjunct: with the "
                     "month slot varying, the value 1 ABSENT from it, and the "
                     "default flag set, the spec keeps the flag displayed "
                     "(`specShowOffset = s0 = true`) while the rival returns "
                     "`false`. Clause 1 is untouched — the rival picks the same "
                     "level — so the rejection is attributable to the "
                     "suppression conjunct alone. Binder spread: `td` has the "
                     "coarse (month) slot varying WITHOUT the value 1, `s0` is "
                     "true.",
        "witness": _witness(
            _TD_MONTH_NO_ONE, "true",
            "-- Refuted at the reported shape: a sub-year span whose coarse\n"
            "-- component varies (2, 3) but never takes the value 1, so the\n"
            "-- summary label must stay displayed. Fully literal, so `decide`\n"
            "-- evaluates both sides; on the frozen solution `decide` instead\n"
            "-- proves the proposition FALSE, which is the discrimination."),
    },

    # ---- the year-slot instantiation, a strict NEAR-MISS of the rival above
    # ---- (ports nagini case 3, its year-level analogue) ----
    {
        "id": "weak-year-suppress-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the value-1 test ONLY at the month slot; at the coarsest (year)
        # slot suppress unconditionally. Strictly closer to gold than the rival
        # above — it agrees with gold on the whole month sub-domain — so it gets
        # its own refutation point at the year slot.
        "module": _guard(
            "      if decide (lvl = 0) || (decide (lvl = 1) "
            "&& column.contains 1) then\n"
            "        showOffset := false\n"),
        "refinement": "a faithful real patch that applied the new value-1 "
                      "conjunct at only ONE of the two coarsest components "
                      "would leave the other half of the fix un-made: a span "
                      "whose coarsest component varies over values none of "
                      "which is 1 would still have its summary label hidden, "
                      "so that context appears nowhere. The condition the fix "
                      "adds is guarded by a single threshold test covering both "
                      "coarse components, not by a per-component special case, "
                      "and the F2P demands a non-empty summary for a span in "
                      "that regime; a patch correct on only one component does "
                      "NOT resolve it in general. This is the more dangerous "
                      "rival of the pair precisely BECAUSE it is a near-miss: "
                      "it passes every check the previous rival fails.",
        "rationale": "REJECT from clause 2, the same `colHasOne td j` conjunct "
                     "but at the OTHER instantiation of the coarseness "
                     "threshold: with only the coarsest slot varying and the "
                     "value 1 absent from it, the spec keeps the flag "
                     "displayed and the rival returns `false`. Refuted at an "
                     "input DISTINCT from `weak-coarse-suppress-uncondi"
                     "tional`'s — it agrees with gold at that one — so each "
                     "rival demonstrates the sub-domain its rationale claims. "
                     "Binder spread: `td` has the coarsest (year) slot varying "
                     "WITHOUT the value 1, all finer slots constant; `s0` true.",
        "witness": _witness(
            _TD_YEAR_NO_ONE, "true",
            "-- Refuted where the COARSEST component varies (1996, 1997) and\n"
            "-- never takes the value 1. Distinct from the month-slot point:\n"
            "-- this rival is CORRECT there, so sharing a witness would claim\n"
            "-- a sub-domain the manifest never shows."),
    },

    # ---- the complement half of the offset domain (ports nagini case 6) ----
    {
        "id": "weak-never-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        # Never hide the summary label: keep the default flag on every input,
        # even at a coarse level whose component DOES contain the value 1.
        "module": _guard(
            "      -- the summary label keeps its default on every input\n"),
        "refinement": "a faithful real patch that never hid the summary label "
                      "would reintroduce the redundant duplication an EARLIER "
                      "accepted fix removed: when the ticks themselves already "
                      "show the start-of-period value, the separate summary "
                      "repeats information already on the axis. The suppression "
                      "behavior is asserted by pre-existing cases in the same "
                      "test module (they expect an EMPTY summary for spans in "
                      "that regime, including the very first and last "
                      "assertions of the F2P test itself, which are not new in "
                      "the test patch). So this rival breaks assertions that "
                      "already pass at base, and does NOT resolve — it fails "
                      "the F2P test outright even though it happens to satisfy "
                      "the newly added assertion.",
        "rationale": "REJECT from clause 2 in the opposite direction: with the "
                     "month slot varying and the value 1 PRESENT in it, the "
                     "spec turns the flag off (`specShowOffset = false`) and "
                     "the rival keeps `s0 = true`. Together with "
                     "`weak-coarse-suppress-unconditional` this pins the "
                     "suppression guard as a biconditional — one rival attacks "
                     "each direction — so no constant-valued flag can satisfy "
                     "the clause. Binder spread: `td` has the coarse slot "
                     "varying WITH the value 1 present, the complement of the "
                     "first rival's point.",
        "witness": _witness(
            _TD_MONTH_HAS_ONE, "true",
            "-- Refuted where the coarse component varies AND takes the value\n"
            "-- 1 (slots 1, 2), so the summary label must be hidden. This is\n"
            "-- the complement of the first rival's point: the guard has to\n"
            "-- fire here and must not fire there."),
    },

    # ---- the coarseness threshold itself (no nagini counterpart: nagini's
    # ---- threshold is spread across six separate column arguments and cannot
    # ---- be off-by-one; the collapsed carrier makes it a single sub-term) ----
    {
        "id": "weak-coarseness-threshold-too-wide",
        "kind": "uniqueness",
        "expect": "reject",
        # Widen the coarseness threshold by one: also hide the summary label
        # when the selected component is the third-coarsest.
        "module": _guard("      if decide (lvl < 3) && column.contains 1 then\n"
                         "        showOffset := false\n"),
        "refinement": "a faithful real patch that widened the threshold to "
                      "include the third-coarsest component would hide the "
                      "summary label for spans of a few days that happen to "
                      "include a start-of-period tick — spans where the "
                      "coarser context is NOT on the axis and so must be shown "
                      "separately. Pre-existing assertions in the same test "
                      "module cover exactly that regime and expect the summary "
                      "to be present, so this rival breaks tests green at "
                      "base. The change the fix makes adds a conjunct to the "
                      "guard; it does not move the threshold, so a patch that "
                      "moves it does NOT resolve.",
        "rationale": "REJECT from clause 2's `decide (j < 2)` sub-term: with "
                     "the third-coarsest slot selected and the value 1 present "
                     "in it, the spec leaves the flag at `s0` (the threshold "
                     "excludes that slot) while the rival turns it off. This is "
                     "the only rival attacking the threshold rather than the "
                     "conjunct, and it moves the varying slot to 2 — a value no "
                     "other witness selects — so the boundary is probed from "
                     "the excluded side.",
        "witness": _witness(
            _TD_DAY_HAS_ONE, "true",
            "-- Refuted where the selected component is the third-coarsest\n"
            "-- (slot 2 varies over 1, 2) and does contain the value 1: the\n"
            "-- threshold excludes that slot, so the flag keeps its default."),
    },

    # ---- the default-flag pass-through: the binder nagini's carrier does not
    # ---- have (see CARRIER DELTA) ----
    {
        "id": "weak-ignore-default-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the caller's default and start the running flag at `true`, so
        # the summary label is displayed even when the caller asked for it off.
        "module": _swap(_BASE, _I_SHOW0,
                        "  let mut showOffset : Bool := true\n"),
        "refinement": "a faithful real patch that ignored the caller's default "
                      "and always started the flag on would force the summary "
                      "label to appear for every caller that explicitly "
                      "configured it OFF — a documented, public option of the "
                      "formatter, honoured by initialising the running flag "
                      "from the stored setting. The fix does not touch that "
                      "initialisation at all; it only adds a conjunct to the "
                      "guard that may later turn the flag off. So a patch that "
                      "hardcodes the initial value regresses an unrelated "
                      "configured behavior while leaving the reported defect "
                      "un-fixed on part of its domain, and does NOT resolve.",
        "rationale": "REJECT from clause 2's pass-through of `s0`: on an input "
                     "where the suppression guard never fires (every component "
                     "constant, so nothing varies) the spec pins the result "
                     "flag to `s0` exactly, and at `s0 = false` the rival "
                     "returns `true`. This is the ONLY rival that moves the "
                     "`s0` binder — every other witness holds it at `true` — so "
                     "without it a rival mishandling only that input would "
                     "verify and the battery would never notice. It also "
                     "demonstrates that the spec does not leave the flag "
                     "unconstrained on the all-constant branch.",
        "witness": _witness(
            _TD_ALL_CONSTANT, "false",
            "-- Refuted with the default flag OFF and nothing varying, so the\n"
            "-- spec must hand back `false` unchanged. The only witness that\n"
            "-- moves the `s0` binder off `true`."),
    },

    # ---- scan direction (ports nagini case 4) ----
    {
        "id": "weak-wrong-scan-direction",
        "kind": "uniqueness",
        "expect": "reject",
        # Scan the index sequence in the opposite order, so the COARSEST varying
        # component is selected instead of the finest.
        "module": _swap(_BASE, _I_FOR, "  for lvl in levels.reverse do\n"),
        "refinement": "a faithful real patch that reversed the scan would "
                      "select the coarsest varying component instead of the "
                      "finest, so the tick labels and the summary string would "
                      "be drawn at the wrong resolution for every span in which "
                      "more than one component varies — which is nearly all of "
                      "them. Many pre-existing assertions in the same test "
                      "module pin the exact rendered label strings for such "
                      "spans and would break, so this rival regresses tests "
                      "green at base and does NOT resolve; it is orthogonal to "
                      "the reported defect, which concerns only whether the "
                      "summary is displayed.",
        "rationale": "REJECT from clause 1 (`result.1 = specLevel td`): "
                     "`specLevel` is `find?` over the sequence "
                     "`[5,4,3,2,1,0]`, so when BOTH the finest and the "
                     "coarsest component vary the spec pins the level to 5 "
                     "while the reversed scan returns 0. The only rival "
                     "attacking clause 1's scan order, and the only witness "
                     "whose input has two components varying at once — every "
                     "other witness has exactly one varying slot, at which the "
                     "two scan directions agree.",
        "witness": _witness(
            _TD_FINE_AND_COARSE, "true",
            "-- Refuted where the FINEST and the COARSEST component both vary\n"
            "-- (slot 5 over 1, 2 and slot 0 over 1996, 1997): the finest-first\n"
            "-- scan must select 5. At a single varying slot the two directions\n"
            "-- coincide, so this point is the one that separates them."),
    },

    # ---- the all-constant fallback (ports nagini case 5) ----
    {
        "id": "weak-allconstant-wrong-level",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the reset to the finest index and let the all-constant case fall
        # through with the coarsest index instead.
        "module": _swap(_swap(_BASE, _I_LEVEL0, "  let mut level : Nat := 0\n"),
                        _I_RESET, ""),
        "refinement": "a faithful real patch that dropped the reset would label "
                      "a degenerate span — every tick identical down to the "
                      "finest modeled component — at the COARSEST resolution "
                      "instead of the finest, selecting the wrong format for "
                      "both the tick labels and the summary string. The "
                      "sub-second span cases in the same test module pin those "
                      "rendered strings and expect the finest resolution, so "
                      "this rival breaks assertions green at base. The fix "
                      "leaves the fallback untouched, so a patch that changes "
                      "it does NOT resolve.",
        "rationale": "REJECT from clause 1's all-constant fallback: `specLevel` "
                     "is `(find? ...).getD 5`, so when no component varies the "
                     "level is pinned to the FINEST index 5, and this rival "
                     "returns 0. The only rival attacking the fallback arm, and "
                     "it moves `td` to a single row — a row count no other "
                     "witness uses — which is the cleanest way to reach the "
                     "arm (one tick cannot vary in anything).",
        "witness": _witness(
            _TD_ALL_CONSTANT, "true",
            "-- Refuted on a single-tick table: nothing can vary, so the\n"
            "-- fallback fires and the level must reset to the finest index 5.\n"
            "-- Same table as the default-flag rival but at `s0 = true`, and\n"
            "-- refuting the OTHER conjunct (the level, not the flag)."),
    },

    # ---- the DIVERGENCE lane. Added by audit: the port recorded this class as
    # ---- VACUOUS on the claim that a diverging rival "cannot be WRITTEN at
    # ---- all", which is false on this carrier (see the corrected note in the
    # ---- module docstring). No nagini counterpart — originated here. ----
    {
        "id": "diverge-measure-free-scan",
        "kind": "uniqueness",
        "expect": "reject",
        # A scan carrying NO decreasing measure: the recursive call repeats the
        # SAME index, so the search never advances and the definition is admitted
        # only under `partial`. This bundle sets no partial-termination semantics,
        # so the frozen obligation must still be discharged for this impl — and
        # cannot be, since nothing is known about the value the measure-free scan
        # returns. The `+ 6` makes the violation arithmetic rather than merely
        # unknown, which is what lets the witness refute it without reducing the
        # irreducible term.
        "module": _swap(
            _BASE, _I_IMPL,
            "partial def spinLevel (td : List (List Nat)) (j : Nat) : Nat :=\n"
            "  if 1 < (colVals td j).dedup.length then j else spinLevel td j\n"
            "\n"
            "def implementation_tickOffset\n"
            "    (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=\n"
            "  (spinLevel td 5 + 6, s0)"),
        "refinement": "a faithful real patch whose level scan never advanced "
                      "would hang the draw path instead of returning a "
                      "resolution, so no tick label and no summary string would "
                      "ever be produced: the F2P test calls the draw path and "
                      "asserts on the summary it yields, and a call that does not "
                      "return cannot satisfy that assertion — nor can any of the "
                      "pre-existing assertions in the same module that exercise "
                      "the same path. So it does NOT resolve, and it regresses "
                      "everything green at base rather than only the new "
                      "assertion. This is the reason the class is worth a case at "
                      "all on a carrier with no partial-termination semantics: "
                      "the obligation here is NOT discharged vacuously by a "
                      "non-returning impl, so the spec really does exclude it.",
        "rationale": "REJECT from clause 1 (`result.1 = specLevel td`): the "
                     "measure-free scan supplies no information about the level "
                     "it returns, and the impl offsets it past the whole index "
                     "range, while `specLevel` pins the level to a member of "
                     "`[5,4,3,2,1,0]` — here 1, since only the month slot "
                     "varies. Clause 2 is untouched (the flag passes `s0` "
                     "through), so the rejection is attributable to the level "
                     "conjunct alone. Note this is the ONLY rival in the lane "
                     "whose defect is not a wrong VALUE on part of the domain: "
                     "it is the absence of a terminating computation, which is "
                     "the third direction this gate tests and which the port had "
                     "recorded as inexpressible.",
        # NOT the shared `_witness` helper: a `partial` term is
        # kernel-irreducible, so the plain `decide` those use gets STUCK on this
        # rival (`did not reduce to isTrue or isFalse`). The refutation is
        # therefore stated over a computable PROJECTION — an arithmetic lower
        # bound on the level — with `decide` kept as the LEADING alternative so
        # that gold, which does reduce, is still refuted by evaluation exactly as
        # every other case is. Measured, four builds: rival 0, gold 1; and with
        # the `¬` dropped (claiming the impl is CORRECT at this point) gold 0,
        # rival 1. Both exit codes invert with the claim, so gold's failure
        # carries information about the claim rather than about the carrier —
        # which the naive `omega`-only form did NOT: there gold failed with an
        # error byte-identical to the flipped claim's.
        "witness": (
            "-- Refuted over a computable projection of the level: whatever the\n"
            "-- measure-free scan returns, this rival's level is at least 6,\n"
            "-- while the spec pins it to 1 at this input (only the month slot\n"
            "-- varies). `decide` closes the first alternative on any impl that\n"
            "-- reduces — so on the frozen solution `decide` proves the\n"
            "-- proposition FALSE, the same discrimination every other witness\n"
            "-- rests on — and the arithmetic alternative closes it against the\n"
            "-- irreducible `partial` term.\n"
            f"example : ¬ problem_spec_tickOffset {_TD_MONTH_NO_ONE} true\n"
            f"    (implementation_tickOffset {_TD_MONTH_NO_ONE} true) := by\n"
            "  unfold problem_spec_tickOffset\n"
            "  first\n"
            "  | decide\n"
            "  | (rintro ⟨h1, -⟩\n"
            f"     rw [show specLevel {_TD_MONTH_NO_ONE} = 1 from by decide] at h1\n"
            "     simp only [implementation_tickOffset] at h1\n"
            "     omega)\n"),
    },

    # =====================================================================
    # SOUNDNESS positives — structurally different but CORRECT implementations
    # that MUST verify. If a faithful correct implementation of the modeled
    # behavior cannot satisfy the frozen obligation, the spec is
    # SPEC-TOO-STRONG. Each keeps the `theorem correct_tickOffset` statement
    # byte-identical and introduces no axiom, no helper lemma, no `sorry` and
    # no `native_decide`. Three of the six reshape the impl in a way the
    # frozen tactic script still closes; two change the guard's SYNTACTIC form,
    # which the frozen script cannot absorb, so they re-prove honestly inside
    # the proof region by reshaping the proof's own transcribed normal form to
    # match; and the sixth (added by audit) abandons the monadic loop entirely
    # and re-proves the impl-normalization step for the new shape. In every case
    # the obligation is closed for the NEW impl, not weakened.
    #
    # Ports nagini cases 7 and 8 (its two branch-reshape positives) and
    # broadens them: nagini's positives reshape the offset sub-branch, and the
    # shapes here additionally exercise local-binding of the two column
    # observations, reordering of the level assignment across the guard, and —
    # the one axis the ported lane left untested, since all five inherited
    # cases keep the frozen `for`/`Id.run` machinery — a loop-free impl.
    # =====================================================================
    {
        "id": "pos-observations-bound-to-locals",
        "kind": "soundness",
        "expect": "verify",
        # Bind both column observations (does it vary / does it contain the
        # value 1) to locals before testing them. Same value flow, so the
        # result is unchanged on every input and the frozen script still closes
        # after the locals zeta-reduce.
        "module": _swap(
            _BASE, _I_TESTBLOCK,
            "    let column := colVals td lvl\n"
            "    let varies := 1 < column.dedup.length\n"
            "    let hasOne := column.contains 1\n"
            "    if varies then\n"
            "      level := lvl\n"
            "      if decide (lvl < 2) && hasOne then\n"
            "        showOffset := false\n"),
        "rationale": "a correct reshape binding the two column observations to "
                     "locals before the tests, mirroring nagini's typed-local "
                     "positive. Both conjuncts of the spec are satisfied "
                     "identically on every input, so `result.1 = specLevel` and "
                     "`result.2 = specShowOffset` still hold. Must verify, else "
                     "the obligation is SPEC-TOO-STRONG about the syntactic "
                     "form of the impl rather than about its behavior. Proof: "
                     "the frozen tactic body is retained unchanged (the locals "
                     "zeta-reduce, so the transcribed normal form still "
                     "matches) — nothing is assumed and no new declaration "
                     "appears.",
    },
    {
        "id": "pos-assignment-after-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two statements inside the varying branch: decide the
        # display flag first, then record the selected level. Independent
        # updates, so the returned pair is unchanged.
        "module": _swap(_BASE, _I_ASSIGN + _I_GUARD, _I_GUARD + _I_ASSIGN),
        "rationale": "a correct reshape reordering the two independent updates "
                     "inside the varying branch (the flag decision now precedes "
                     "recording the level). Neither reads the other's target, "
                     "so the returned pair is identical on every input and both "
                     "spec conjuncts hold. Must verify. Proof: frozen tactic "
                     "body retained. This positive defends the clause-1 "
                     "assignment specifically, whereas the other positives "
                     "reshape the clause-2 guard — so both conjuncts of the "
                     "obligation are defended by a reshape that touches them.",
    },
    {
        "id": "pos-distinct-count-bound",
        "kind": "soundness",
        "expect": "verify",
        # Bind the distinct-value count to a local and compare against that.
        "module": _swap(
            _BASE,
            _I_COL + "    if 1 < column.dedup.length then\n",
            "    let column := colVals td lvl\n"
            "    let distinct := column.dedup.length\n"
            "    if 1 < distinct then\n"),
        "rationale": "a correct reshape naming the distinct-value count before "
                     "comparing it, which is the observation clause 1's scan "
                     "turns on. Behaviourally identical on every input, so both "
                     "spec conjuncts hold. Must verify. Proof: frozen tactic "
                     "body retained (the local zeta-reduces). A third, "
                     "independent region of the impl from the two positives "
                     "above, so no single reshape site carries the whole "
                     "soundness lane.",
    },
    {
        "id": "pos-guard-conjuncts-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Commute the two conjuncts of the coarse-level suppression guard. Both
        # sides are pure Bool tests, so the conjunction is unchanged — but the
        # frozen script's transcribed normal form no longer matches the impl
        # syntactically, so the proof region commutes the SAME conjunction in
        # that normal form. The obligation is re-proved for the new impl; its
        # statement is byte-identical and nothing is assumed.
        "module": _reprove_normal_form(
            _guard("      if column.contains 1 && decide (lvl < 2) then\n"
                   "        showOffset := false\n"),
            lambda j: (f"    ({j}, if (colVals td {j}).contains 1 "
                       f"&& decide ({j} < 2) then false else s0)")),
        "rationale": "a correct reshape commuting the two conjuncts of the "
                     "coarse-level suppression guard — the CHANGED sub-term of "
                     "clause 2. Both operands are pure `Bool` tests with no "
                     "short-circuit-visible effect, so the conjunction and hence "
                     "the returned pair are identical on every input and both "
                     "spec conjuncts hold. Must verify, else clause 2 pins the "
                     "guard's syntactic ORDER rather than its truth value, which "
                     "would be SPEC-TOO-STRONG. Proof: the frozen script matches "
                     "the impl against an explicitly transcribed nested-`if` "
                     "normal form, which a commuted guard no longer matches "
                     "syntactically, so the SAME commutation is applied to that "
                     "transcribed term inside the proof region. The obligation's "
                     "statement is byte-identical, no lemma is added, nothing is "
                     "assumed — this is a genuine re-proof for the new impl, and "
                     "it is the positive that most directly defends the fix's own "
                     "sub-term.",
    },
    {
        "id": "pos-guard-nested-ifs",
        "kind": "soundness",
        "expect": "verify",
        # Split the guard's conjunction into two nested `if`s. Behaviourally
        # identical (nested tests of pure Bools), but a different syntactic form
        # again, so the transcribed normal form is split the same way and the
        # case-splitting tactic is deepened by one level to match.
        "module": _deepen_splits(
            _reprove_normal_form(
                _guard("      if decide (lvl < 2) then\n"
                       "        if column.contains 1 then\n"
                       "          showOffset := false\n"),
                lambda j: (f"    ({j}, if decide ({j} < 2) then "
                           f"(if (colVals td {j}).contains 1 then false "
                           f"else s0) else s0)"))),
        "rationale": "a correct reshape splitting the guard's conjunction into "
                     "two nested tests — the shape a reader would write to "
                     "handle the coarseness threshold and the value-1 test "
                     "separately. Identical on every input (both operands are "
                     "pure), so both spec conjuncts hold. Must verify. Proof: "
                     "the transcribed normal form is split the same way and "
                     "EVERY scan step's branch-case tactic is deepened by one "
                     "`split` to match the extra nesting (all six steps carry "
                     "the guard, so all six need it). Statement byte-identical, no new "
                     "lemma, no assumption token. Together with the commuted "
                     "positive this shows clause 2 constrains the guard's "
                     "MEANING and not its shape, across two different "
                     "syntactic rewrites.",
    },
    # ---- Added by audit (attack E). Every pre-existing positive keeps the
    # ---- monadic `Id.run` loop and edits inside it, so the whole soundness lane
    # ---- shared one control-flow shape and the spec's independence from THAT
    # ---- choice was assumed rather than shown. This one abandons the loop. ----
    {
        "id": "pos-loop-free-direct-recursion",
        "kind": "soundness",
        "expect": "verify",
        # No loop and no monad: a helper `def` recursing structurally down the
        # index sequence, with the impl a direct application of it. This is the
        # shape a functional author would write, and it is the FIRST positive that
        # does not inherit the frozen loop — so it tests that clause 1's scan is
        # pinned by its RESULT and not by the `for`/`Id.run` machinery the frozen
        # normalization lemma is written against. Terminates structurally on the
        # list argument, so no measure is needed and the divergence rival above
        # stays the only measure-free impl in the battery.
        "module": _reprove_impl_bridge(
            _swap(_BASE, _I_IMPL,
                  "def scanLevels (td : List (List Nat)) (s0 : Bool) :\n"
                  "    List Nat → Nat × Bool\n"
                  "  | [] => (5, s0)\n"
                  "  | j :: rest =>\n"
                  "    if 1 < (colVals td j).dedup.length then\n"
                  "      (j, if decide (j < 2) && (colVals td j).contains 1 then\n"
                  "            false else s0)\n"
                  "    else scanLevels td s0 rest\n"
                  "\n"
                  "def implementation_tickOffset\n"
                  "    (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=\n"
                  "  scanLevels td s0 levels"),
            "  rfl"),
        "rationale": "a correct reshape that drops the monadic loop entirely and "
                     "scans by structural recursion over the index sequence "
                     "instead. Behaviourally identical on every input — it "
                     "returns at the first index whose column has more than one "
                     "distinct value, applies the same suppression guard there, "
                     "and falls through to the finest index on the empty tail — "
                     "so both spec conjuncts hold. Must verify, else the "
                     "obligation pins the impl's CONTROL-FLOW machinery (a "
                     "bounded `for` inside `Id.run`) rather than the "
                     "input→output relation, which would be SPEC-TOO-STRONG in "
                     "the most consequential way: every other positive in this "
                     "lane keeps that machinery, so without this case the spec's "
                     "independence from it is assumed and never shown. Proof: the "
                     "impl-normalization step becomes `rfl` — this shape reduces "
                     "to the transcribed nested-`if` normal form definitionally, "
                     "where the loop needed a six-step `simp`/`by_cases` script — "
                     "and the two atom lemmas and the obligation's own body are "
                     "retained verbatim. Statement byte-identical, no new "
                     "theorem, no assumption token.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the
    # normal, F2P-shaped input rather than only in the abstract. The frozen
    # theorem carries NO precondition hypothesis (the modeled behavior is total,
    # so the `∀` is unguarded), so nagini's precondition-admission probe
    # (case 9: read the first element under the read permission and assert the
    # column lengths agree) has no precondition binder to attack here — its
    # length and permission obligations simply do not exist on this carrier.
    # The honest analogue is to discharge the spec predicate by evaluation at a
    # ground instance of the reported scenario, alongside the frozen
    # obligation. Ports nagini case 9.
    # =====================================================================
    {
        "id": "admiss-ground-reported-scenario",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the spec predicate at a ground input shaped like the
        # reported scenario (a sub-year span, three ticks, the coarse component
        # varying over a range that skips the value 1, default flag on), then
        # close the frozen obligation verbatim. Nothing is assumed: no new
        # declaration, the theorem statement is byte-identical, and the ground
        # instance is a `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _P_FROZEN,
            f"  have _ground : problem_spec_tickOffset {_TD_F2P_SHAPED} true\n"
            f"      (implementation_tickOffset {_TD_F2P_SHAPED} true) := by\n"
            f"    unfold problem_spec_tickOffset; decide\n"
            + _P_FROZEN),
        "rationale": "the obligation is discharged at a ground instance of the "
                     "reported scenario — three ticks spanning under a year "
                     "whose coarse component varies over values none of which "
                     "is 1, with the default flag on — by evaluation, and then "
                     "the frozen obligation is closed verbatim. This must "
                     "verify: if the modeled behavior were unsatisfiable at "
                     "exactly the input the F2P exercises, the spec would be "
                     "vacuous or over-constrained there (the analogue of "
                     "PRECOND-TOO-STRONG on a carrier with no precondition), "
                     "and every reject case above would be refuting a spec no "
                     "implementation can meet. It also confirms the spec "
                     "predicate is DECIDABLE at a literal input, which is the "
                     "premise every witness relies on. Nothing is assumed: no "
                     "new declaration, statement byte-identical, no assumption "
                     "token.",
    },
]

# No AXIOM lane: this bundle declares no `opaque` and consumes no `axiom` (both
# column observations are modeled deeply), so G-AX has nothing to check. The
# nagini AXIOM_TESTS belong to that lane, which this gate ignores; dropped.
AXIOM_TESTS = []

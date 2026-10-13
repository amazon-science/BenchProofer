"""properties.py — G-PBT falsification battery for sympy__sympy-14248 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct joinSignedMatrixTerms`` obligation survives) and swaps in a
candidate implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, one load-bearing clause):

  joinSignedMatrixTerms (terms : List (List Char)) return (out : List Char)
    require terms ≠ []
    ensures out = joinSignedTerms terms

``terms`` is a sequence of already-rendered term texts; the method returns the
rendering of the whole sequence. The single ``ensures`` pins it to
``joinSignedTerms``, a total ``def`` in the ``pure`` region (the ``axioms`` region
declares nothing), fully unfolded over the method's OWN input. Its structure is
four nested decisions, and each one is a sub-domain a rival can get wrong:

  * the LEADING term is emitted VERBATIM — it keeps any leading negative marker
    and gains no separator and no sign glyph of its own;
  * every NON-LEADING term contributes ``' ' :: termSign t :: ' ' :: termBody t``,
    which splits into three independent decisions:
      - the SIGN GLYPH is that term's own (``'-'`` when it carries a leading
        negative marker, ``'+'`` otherwise) — this is the behaviour the issue is
        about: a negated summand must render as a subtraction, not as an addition
        of a negative;
      - the BODY is the term with that leading marker REMOVED (so the marker is
        not emitted twice);
      - the two SEPARATING SPACES bracket the sign glyph;
  * the ORDER of contributions follows the input order.

ADVERSARIAL READ of the sibling's classes:

  * FRAME-MUTATION — VACUOUS on this backend, and NOT fabricated. The sibling
    carries three MANDATORY frame-mutation probes (one per contracted function),
    because there a read-only input is held at a fractional heap permission that
    an impl can overwrite, so an impl that writes to its input must be rejected
    for insufficient permission. This backend is referentially transparent: every
    parameter is an immutable value, ``terms`` is not declared ``mut``, and there
    is no heap and no aliasing — so there is no read-only input to mutate and no
    substitute probe exists. The sibling's "inputs are not mutated" obligation is
    structurally guaranteed here by the ABSENCE of a ``mut`` binder, which the
    frozen spec already encodes (spec_guide directive 5).

  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason the sibling records. The
    post-image is pinned to ``joinSignedTerms``, a total spelled-out function of
    the method's own input, not to an opaque answer key: evaluating it IS the
    correct answer, so a "return the oracle" impl reduces to the correct
    computation and there is no wrong echo to build. Honest cheapest-reshape
    positive controls (``pos-*``) stand in.

  * PARTIAL-DOMAIN / CROSS-ALGORITHM — APPLIES, and is where this spec is
    actually attackable. Every rival below is correct on a genuine part of the
    domain and wrong on the sub-domain the failing tests exercise.

  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS on this carrier. The spec is a ``method`` CONTRACT, not a bare
predicate, so each witness reaches it through Velvet's own tester machinery:
``joinSignedMatrixTermsTester <terms> = false`` says the extracted program's
result violates the method's postcondition at that concrete input. It is checked
in a file whose ``prove_correct`` block has been stripped, so no tactic script can
mask the verdict. All inputs are concrete ``List (List Char)`` literals, the sole
``require`` (``terms ≠ []``) decides trivially at each of them, and every witness
``decide``s. No ``sorry`` / ``admit`` / ``native_decide`` / ``axiom``, and no
witness binds a hypothesis (the carrier computes, so none needs to condition on
it — there is nothing that could be inconsistent).

One property of this carrier is worth stating, because it is what makes the
witnesses substantive rather than an artifact. The frozen impl is a ``while``
loop, and the extracted program of a loop routes through a fixpoint that
``decide`` cannot reduce — so on the frozen solution every witness fails as
"reduction got stuck", not as "the tester decided ``true``".

That FAIL half therefore carries NO information on its own, and this file does
not claim it does. Verified by the audit's forgery experiment (attack B'), eight
witness points, both directions:

  * the witness (``... = false``) against the frozen solution -> exit 1,
    ``Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse` ``;
  * the FORGERY, differing only in flipping the claim to ``... = true`` (i.e.
    asserting the frozen impl is WRONG's opposite — that the rival's value is
    what gold produces) against the frozen solution -> exit 1, byte-identical
    error.

Gold's exit code is thus identical for a claim and its negation, which is
precisely why the gate does not rest on it: it takes the ``witness_reference``
fallback and re-refutes each witness against a VERIFYING positive from this
battery that DOES reduce (``meta.json`` records ``witness_subject`` = "a
verifying positive from this battery (gold cannot decide)" and
``gold_stuck_screen`` = "reduction" on all eight cases). Against that loop-free
subject the exit code tracks the claim, which is the actual attestation:

  * witness ``= false`` vs the verifying loop-free positive -> exit 1,
    ``Tactic `decide` proved that the proposition ... = false is false``;
  * forgery ``= true``  vs the same positive               -> exit 0.

Each ``= false`` is therefore a real, KERNEL-DECIDED violation of the post-image
at that input, discriminated against an impl the verifier accepts — not a
reduction artifact and not a tautology.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14248"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole executable body: accumulate the non-leading
# ---- terms' contributions by walking the sequence backwards and prepending, then
# ---- put the leading term in front. Lies wholly inside the one impl region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). Reshaped
# ---- wholesale by the rivals and the positive controls. ----
_IMPL = (
    "    let mut result : List Char := []\n"
    "    let mut i := terms.length\n"
    "    while i > 1\n"
    "      invariant 1 ≤ i ∧ i ≤ terms.length\n"
    "      invariant result = joinTail (terms.drop i)\n"
    "      done_with i = 1\n"
    "      decreasing i\n"
    "    do\n"
    "      let t := terms[i - 1]!\n"
    "      result := tailPiece t ++ result\n"
    "      i := i - 1\n"
    "    return terms[0]! ++ result\n"
)

# The accumulator initializer (a substring of _IMPL, unique in the file). Anchor
# for the admissibility in-region assert, which is spliced in FRONT of the
# otherwise-verbatim frozen body.
_INIT = "    let mut result : List Char := []\n"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its tactic script without
# ---- touching the spec or dropping the obligation. ----
_PROOF = "prove_correct joinSignedMatrixTerms by\n  loom_solve"


# ---- witness preamble. Appended to BOTH the rival and the frozen file, so the
# ---- names it introduces (`...Exec`, `...Tester`) exist on both sides. ----
def _tester(body):
    return ("extract_program_for joinSignedMatrixTerms\n"
            "prove_precondition_decidable_for joinSignedMatrixTerms\n"
            "prove_postcondition_decidable_for joinSignedMatrixTerms\n"
            "derive_tester_for joinSignedMatrixTerms\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation with its statement intact; only
    # the executable surface (and, where the reshape needs it, the tactic script)
    # moves. No new lemma, no `sorry`, nothing assumed.
    # =====================================================================
    {
        "id": "pos-hoist-head-and-temp",
        "kind": "soundness",
        "expect": "verify",
        # The sibling's own positive control, re-expressed: keep the identical
        # backward walk (same two invariants, same per-step prepend, same
        # `done_with`) and only reshape the executable surface — the leading
        # term's value hoisted into a local BEFORE the loop, and the per-step
        # prepend routed through an explicit named temporary. Statement order and
        # locals differ; the obligations are the same ones, so the frozen tactic
        # script still discharges them unchanged.
        "module": _swap(
            _BASE, _IMPL,
            "    let head := terms[0]!\n"
            "    let mut result : List Char := []\n"
            "    let mut i := terms.length\n"
            "    while i > 1\n"
            "      invariant 1 ≤ i ∧ i ≤ terms.length\n"
            "      invariant result = joinTail (terms.drop i)\n"
            "      done_with i = 1\n"
            "      decreasing i\n"
            "    do\n"
            "      let t := terms[i - 1]!\n"
            "      let piece := tailPiece t\n"
            "      result := piece ++ result\n"
            "      i := i - 1\n"
            "    return head ++ result\n"),
        "rationale": "the sibling's positive control ported: same backward walk, "
                     "same invariants, same per-step prepend — only the leading "
                     "term hoisted into a local before the loop and the prepend "
                     "routed through a named temporary. A structurally-different "
                     "CORRECT impl of `out = joinSignedTerms terms` MUST verify; "
                     "if it cannot => SPEC-TOO-STRONG on the skeleton's exact "
                     "statement order.",
    },
    {
        "id": "pos-return-spec-directly",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different reshape: drop the accumulate-backwards skeleton
        # entirely and return the modeled rendering. Observationally identical
        # (the skeleton's result IS that rendering), so the post-image holds
        # definitionally and the frozen tactic discharges it.
        "module": _swap(_BASE, _IMPL, "    return joinSignedTerms terms\n"),
        "rationale": "returning the modeled rendering directly satisfies "
                     "`out = joinSignedTerms terms` definitionally, so this "
                     "loop-free correct reshape must verify. Guards against a "
                     "SPEC-TOO-STRONG that is specific to the looping skeleton's "
                     "shape rather than to the behaviour.",
    },
    {
        "id": "pos-forward-flatmap",
        "kind": "soundness",
        "expect": "verify",
        # A third correct shape, and the one furthest from the frozen skeleton:
        # emit the leading term, then map each remaining term to its contribution
        # and concatenate FORWARD, with no accumulator and no index at all. The
        # frozen tactic no longer closes this (it is tuned to the backward walk),
        # so the tactic body is retuned inside `prove_correct` — the obligation's
        # statement is untouched and no lemma is added: the induction is done
        # inline over the tail, from the frozen `pure` region's own lemmas.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    return terms[0]! ++ (terms.drop 1).flatMap tailPiece\n"),
            _PROOF,
            "prove_correct joinSignedMatrixTerms by\n"
            "  loom_solve\n"
            "  rw [joinSignedTerms_head terms require_1]\n"
            "  congr 1\n"
            "  induction terms.drop 1 with\n"
            "  | nil => rfl\n"
            "  | cons t ts ih => simp [joinTail_cons, List.flatMap_cons, ih]"),
        "rationale": "a FORWARD, accumulator-free, index-free shape (map each "
                     "non-leading term to its contribution and concatenate) "
                     "computes the same rendering, so it must verify. This is the "
                     "reshape most likely to expose a spec that only accommodates "
                     "the backward walk. The tactic body is retuned (the frozen "
                     "script is tuned to the backward walk); the obligation "
                     "statement is byte-identical and no lemma is introduced.",
    },

    # =====================================================================
    # ADMISSIBILITY. The sibling's admissibility case asserts that the
    # half-permission precondition admits a normal F2P-shaped input and lets a
    # normal return be reached. There is no permission surface here, and the sole
    # `require` (`terms ≠ []`) plainly admits every real input, so that exact
    # reading is thin. It is re-aimed at the residual admissibility risk on this
    # carrier: that the post-image is DEGENERATE at the interesting point — a
    # rendering no impl can produce reads exactly like one every impl produces.
    # The in-region assert pins the modeled rendering's value at the boundary
    # input the failing tests exercise (three terms, the FIRST carrying a leading
    # negative marker and one more in the middle: a negated leading summand kept,
    # each negated non-leading summand folded into a subtraction). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live — a false claim leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-rendering-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _INIT,
                  "    assert (with_name_prefix `assert\n"
                  "      (joinSignedTerms [['-', 'B'], ['-', 'A', '*', 'B'], ['A']] =\n"
                  "         \"-B - A*B + A\".toList))\n" + _INIT),
            _PROOF,
            "prove_correct joinSignedMatrixTerms by\n"
            "  loom_solve <;> first | decide | simp_all"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "boundary input the failing tests exercise: a three-term "
                     "sequence whose first and middle terms carry a leading "
                     "negative marker renders with the leading marker KEPT and "
                     "each subsequent negated term folded into a subtraction "
                     "(`-B - A*B + A`), not as an addition of a negative. The "
                     "in-region assert must discharge — if the modeled rendering "
                     "could not produce this value the obligation would be "
                     "degenerate (PRECOND-TOO-STRONG / unsatisfiable-post) and "
                     "every positive above would be passing for nothing. The impl "
                     "is kept verbatim so the ensures clause still discharges too. "
                     "The assert is LIVE, and that was measured rather than "
                     "asserted: replacing the claimed rendering with the "
                     "added-negative form (`-B + -A*B + A`) and changing nothing "
                     "else makes this same case FAIL to build (exit 1, `error: "
                     "unsolved goals`), so the case's verdict tracks the value it "
                     "pins and it cannot pass by discharging trivially.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, plus the refinement argument that its faithful
    # counterpart would NOT resolve the failing tests. Each rival keeps the frozen
    # `prove_correct` block (which no longer closes for the reshaped impl); the
    # witness is what attributes the rejection to the SPEC rather than to the
    # tactic script.
    # =====================================================================
    {
        "id": "weak-plus-join-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: glue every non-leading term with a fixed
        # " + " separator and emit it VERBATIM, never inspecting its own sign.
        # Correct on every sequence in which no non-leading term carries a
        # leading negative marker; wrong exactly on the sign-bearing inputs.
        "module": _swap(
            _BASE, _IMPL,
            "    return terms[0]! ++ (terms.drop 1).flatMap "
            "(fun t => ' ' :: '+' :: ' ' :: t)\n"),
        "refinement": "this is the unchanged pre-image behaviour, which renders a "
                      "negated summand as an addition of a negative rather than as "
                      "a subtraction — precisely the output the problem statement "
                      "exhibits as wrong. Its faithful counterpart is the code as "
                      "it stands, so it does NOT resolve: every failing assertion "
                      "over a difference of matrix expressions still sees the "
                      "added-negative form. Correct on every sign-free sequence, so "
                      "it is a true partial-domain rival and not a blanket-wrong "
                      "impl.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: the post-image "
                     "requires each non-leading term's contribution to carry that "
                     "TERM'S OWN sign glyph over its marker-stripped body "
                     "(`termSign t` / `termBody t`), while this impl hardcodes the "
                     "glyph and keeps the marker. If it verified the spec would not "
                     "sense the reported defect at all => SPEC-TOO-WEAK. Refuted at "
                     "a two-term sequence whose SECOND term carries the marker.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester [['a'], ['-', 'b']] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-strip-leading-term-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct tail discipline, but the LEADING term is rendered as its BODY:
        # a leading negative marker on term 0 is silently dropped. Correct on
        # every sequence whose first term carries no marker.
        "module": _swap(
            _BASE, _IMPL,
            "    return termBody terms[0]! ++ (terms.drop 1).flatMap tailPiece\n"),
        "refinement": "a counterpart that normalised the FIRST term's sign away "
                      "(dropping its leading marker on the grounds that the leading "
                      "position takes no sign) renders a sequence whose first term "
                      "is negated with the negation lost — the rendered text asserts "
                      "the opposite sign for that summand. The failing assertions "
                      "include exactly this shape (a sum whose first rendered term "
                      "is negative), so it would NOT resolve.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: the post-image "
                     "emits the leading term VERBATIM (`joinSignedTerms (t :: ts) = "
                     "t ++ joinTail ts`), marker included, while this impl strips "
                     "it. Attacks the leading-term arm specifically — the one arm "
                     "the tail-discipline rivals all get right. Refuted at a "
                     "sequence whose FIRST term carries the marker, the mirror of "
                     "the previous rival's point.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester [['-', 'b'], ['a']] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-leading-term-as-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Uniform treatment: run EVERY term through the non-leading contribution,
        # so the leading term gains a separator and a sign glyph of its own.
        # Refuted at the SINGLETON boundary — the one-term sequence where the
        # frozen skeleton's loop body never runs and the leading arm is the whole
        # of the behaviour.
        "module": _swap(_BASE, _IMPL, "    return terms.flatMap tailPiece\n"),
        "refinement": "a counterpart that treated every summand uniformly — "
                      "emitting a separator and an explicit sign before the first "
                      "one too — prefixes the whole rendering with stray leading "
                      "punctuation and whitespace. Every failing assertion pins the "
                      "rendered text exactly, and none of them begins with a "
                      "separator or a leading plus, so it would NOT resolve.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: the post-image "
                     "gives the leading term NO separator and NO sign glyph of its "
                     "own, which this impl adds. Refuted at the SINGLETON sequence "
                     "`[['a']]` — the boundary where `terms.length = 1`, the "
                     "smallest input the `require` admits, and the only witness "
                     "point at which the frozen skeleton's loop body never "
                     "executes, so the leading arm is tested in isolation.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester [['a']] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-sign-emitted-marker-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS. The sign glyph is derived correctly from the term, but the
        # body keeps its own leading marker, so a negated term renders with the
        # marker TWICE. Agrees with the post-image on every marker-free term and
        # gets the sign DECISION right everywhere — it fails only on the body.
        "module": _swap(
            _BASE, _IMPL,
            "    return terms[0]! ++ (terms.drop 1).flatMap\n"
            "      (fun t => ' ' :: termSign t :: ' ' :: t)\n"),
        "refinement": "a counterpart that inserted the subtraction sign but forgot "
                      "to remove the marker already present on the rendered term "
                      "emits the negation twice for every negated summand. The "
                      "failing assertions pin the rendered text exactly and show a "
                      "single subtraction sign per negated summand, so it would NOT "
                      "resolve. This is the most plausible half-fix of the reported "
                      "defect: the sign decision is right and only the body is "
                      "wrong.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: the contribution "
                     "must place the sign glyph over `termBody t` (the marker "
                     "REMOVED), not over `t`. Isolates the BODY decision from the "
                     "SIGN decision — this rival gets the sign right at every "
                     "input, so it is a strictly nearer miss than the plus-join "
                     "rival and is refuted at its own point: a THREE-term sequence "
                     "whose middle term carries the marker, so a correct leading "
                     "arm and a correct final arm surround the single wrong one.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester [['a'], ['-', 'b'], ['c']] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-body-stripped-sign-fixed",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact MIRROR of the previous rival: the body is stripped correctly
        # but the sign glyph is hardcoded to '+'. Together the two show the spec
        # pins the sign decision and the body decision INDEPENDENTLY — neither is
        # a proxy for the other.
        "module": _swap(
            _BASE, _IMPL,
            "    return terms[0]! ++ (terms.drop 1).flatMap\n"
            "      (fun t => ' ' :: '+' :: ' ' :: termBody t)\n"),
        "refinement": "a counterpart that stripped the marker off each rendered "
                      "term but kept joining with an addition sign renders a "
                      "negated summand with its negation deleted outright — the "
                      "rendered text asserts the wrong sign for that summand, which "
                      "is strictly worse than the reported defect. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: the glyph must be "
                     "`termSign t`, not a constant. The exact mirror of "
                     "`weak-sign-emitted-marker-kept` (that rival gets the sign "
                     "right and the body wrong; this one the body right and the "
                     "sign wrong), so the pair demonstrates the two decisions are "
                     "pinned INDEPENDENTLY and neither rival could pass by getting "
                     "the other half right. Refuted at its own two-term point with "
                     "a distinct leading term.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester [['x'], ['-', 'y']] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-single-space-marker-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # CROSS-ALGORITHM rival, ported from the sibling's cross-algorithm case.
        # The sibling site that renders onto a 2-D canvas uses a DIFFERENT
        # discipline for a negated non-leading term: a single separating space
        # with the term kept in full, rather than a spaced sign glyph over the
        # stripped body. This substitutes that discipline here. Correct on every
        # marker-free term; diverges on exactly the negated ones.
        "module": _swap(
            _BASE, _IMPL,
            "    return terms[0]! ++ (terms.drop 1).flatMap\n"
            "      (fun t => if t.head? = some '-' then ' ' :: t "
            "else ' ' :: '+' :: ' ' :: t)\n"),
        "refinement": "the sibling rendering site — the one that draws onto a "
                      "two-dimensional canvas — legitimately uses this other "
                      "discipline for a negated non-leading summand: one separating "
                      "space with the term kept whole. A counterpart that carried "
                      "THAT discipline over to this site would render each negated "
                      "summand with a single space and no spaced sign, where the "
                      "failing assertions for this site pin a spaced subtraction "
                      "sign. The two disciplines are genuinely different and this "
                      "site's assertions demand this one, so it would NOT resolve.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: `tailPiece` is a "
                     "spaced sign glyph over the STRIPPED body for every "
                     "non-leading term, with no special case that keeps the term "
                     "whole. This is the cross-algorithm rival — the one that is a "
                     "CORRECT algorithm for a sibling site and wrong for this one — "
                     "so it is the case that shows the spec pins THIS site's "
                     "discipline and not merely 'some sign handling'. Refuted at a "
                     "three-term sequence carrying the marker on BOTH the leading "
                     "and the final term, a combination no other witness probes.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester "
            "[['-', 'c'], ['a'], ['-', 'b']] = false := by\n  decide\n"),
    },
    {
        "id": "weak-drop-separating-spaces",
        "kind": "uniqueness",
        "expect": "reject",
        # Both content decisions correct — right sign glyph, right stripped body —
        # but the two separating spaces around the glyph are dropped. Isolates the
        # whitespace conjunct of the contribution from its content.
        "module": _swap(
            _BASE, _IMPL,
            "    return terms[0]! ++ (terms.drop 1).flatMap\n"
            "      (fun t => termSign t :: termBody t)\n"),
        "refinement": "a counterpart that folded the sign in without the "
                      "surrounding separators runs each summand together with its "
                      "sign and its neighbour. The failing assertions pin the "
                      "rendered text character for character, including the spacing "
                      "around each operator, so it would NOT resolve even though "
                      "every sign decision it makes is correct.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: `tailPiece` is "
                     "`' ' :: termSign t :: ' ' :: termBody t` — the two separating "
                     "spaces are part of the pinned contribution. Attacks the "
                     "SPACING sub-clause in isolation: this rival's sign and body "
                     "decisions are both right at every input, so a spec that "
                     "pinned only the sign fold would admit it. Refuted at a "
                     "three-term sequence whose FINAL term carries the marker, with "
                     "two marker-free terms before it.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester "
            "[['p'], ['q'], ['-', 'r']] = false := by\n  decide\n"),
    },
    {
        "id": "weak-reverse-tail-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER rival. Every term's contribution is rendered exactly right; only
        # the ORDER of the non-leading contributions is reversed. Attacks the
        # traversal/ordering clause, which no value-level rival above touches: a
        # spec that pinned only the MULTISET of contributions would admit it.
        "module": _swap(
            _BASE, _IMPL,
            "    return terms[0]! ++ ((terms.drop 1).reverse).flatMap tailPiece\n"),
        "refinement": "a counterpart that accumulated the summands' contributions "
                      "in the wrong direction (a plausible slip when the fold is "
                      "rewritten to walk the sequence backwards, which is exactly "
                      "the shape this operation uses) emits the summands in "
                      "reversed order after the first. Every failing assertion pins "
                      "the rendered text exactly, summand order included, so it "
                      "would NOT resolve — even though each individual summand is "
                      "rendered perfectly.",
        "rationale": "REJECT from `out = joinSignedTerms terms`: the post-image is "
                     "a front-recursive concatenation, so it pins the ORDER of the "
                     "contributions and not just their content. This rival renders "
                     "every contribution correctly and is refuted purely on order, "
                     "which is what makes it the case that closes the "
                     "'multiset-only' reading of the clause. Refuted at a "
                     "three-term sequence whose reversal is observable (the two "
                     "non-leading terms differ), with the marker on the LAST term.",
        "witness": _tester(
            "example : joinSignedMatrixTermsTester "
            "[['a'], ['b'], ['-', 'c']] = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery has 11 SPEC cases (2 soundness positives, 1 admissibility,
# 3 mandatory frame-mutation rivals, 5 partial-domain / cross-algorithm rivals)
# and 0 AXIOM_TESTS. This bundle NARROWS the sibling's THREE contracted functions
# to a SINGLE modeled method:
#
#   sibling render_sum        -> joinSignedMatrixTerms   (MODELED here)
#   sibling render_sum_space  -> not modeled: mapping.md §0 records that the
#                                sibling single-space site renders onto a 2-D
#                                canvas, which this backend's value fragment
#                                cannot express. It ships in patch.diff.
#   sibling render_product    -> not modeled: mapping.md §0 records it as an
#                                INDEPENDENT behaviour with its own branch,
#                                deliberately out of scope. It ships in patch.diff.
#
# So every sibling case attached to render_sum_space or render_product has no
# counterpart on this carrier. That is carrier narrowing, not a dropped attack:
# there is no contract here for those rivals to violate, and fabricating one
# would mean specifying a behaviour this bundle does not model.
#
#   sibling case                  -> here                              disposition
#   ----------------------------------------------------------------------------
#   pos-sum-reshape               -> pos-hoist-head-and-temp            PORTED
#   pos-product-reshape           -> (none)                             NOT MODELED
#   (new honest reshapes)         -> pos-return-spec-directly           ADDED
#                                    pos-forward-flatmap                ADDED
#   admiss-sum-readable           -> admiss-rendering-nondegenerate      RE-AIMED
#   frame-sum-write               -> (none)                             VACUOUS
#   frame-sum-space-write         -> (none)                             VACUOUS
#   frame-product-write           -> (none)                             VACUOUS
#   weak-sum-plusjoin             -> weak-plus-join-verbatim             PORTED
#   weak-sum-head-strip           -> weak-strip-leading-term-marker      PORTED
#   weak-space-as-str-discipline  -> weak-single-space-marker-kept       PORTED (inverted)
#   weak-space-text-negativity    -> (none)                             NOT EXPRESSIBLE
#   weak-product-drop-neg         -> (none)                             NOT MODELED
#   weak-product-always-neg       -> (none)                             NOT MODELED
#   (new, this carrier's clauses) -> weak-leading-term-as-tail           ADDED
#                                    weak-sign-emitted-marker-kept       ADDED
#                                    weak-body-stripped-sign-fixed       ADDED
#                                    weak-drop-separating-spaces         ADDED
#                                    weak-reverse-tail-order             ADDED
#
# 3 ported, 1 re-aimed, 7 added, 3 vacuous, 4 without a counterpart. 12 cases.
#
# RE-AIMED (admissibility). The sibling's case asserts that the half-permission
#   precondition admits a normal input and that a normal return is reachable.
#   There is no permission surface here and the sole `require` (`terms ≠ []`)
#   plainly admits every real input, so that reading is thin. It is re-aimed at
#   the residual risk on this carrier — a DEGENERATE post-image, which reads
#   exactly like a satisfiable one — by discharging an in-region assert pinning
#   the modeled rendering's value at the sibling's own discriminating input (the
#   three-term sequence from the problem statement). The sibling's boundary
#   observation is preserved separately and more sharply: the singleton sequence,
#   where the loop body never runs, is now a reject WITNESS POINT
#   (weak-leading-term-as-tail) rather than an assertion.
#
# VACUOUS (all 3 frame-mutation probes). The sibling's MANDATORY probes prepend a
#   write to an input held at half heap permission and are rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: no heap,
#   no aliasing, `terms` is not declared `mut`, so there is no read-only input to
#   overwrite and no substitute probe exists. Not fabricated (spec_guide
#   directive 5: the obligation is discharged here by the ABSENCE of a `mut`,
#   which the frozen spec already encodes).
#
# NOT EXPRESSIBLE (weak-space-text-negativity). The sibling's sharpest rival
#   decides the join on the RENDERED TEXT's leading marker instead of on a
#   STRUCTURAL negativity fact supplied as a separate input, and the sibling can
#   refute it because its contract carries that fact as its own parameter. This
#   bundle's contract has ONE input — the rendered term texts — and mapping.md §1
#   records this site's decision as a test on the leading character of that text.
#   So on this carrier the two are the SAME function and the distinction the
#   sibling maintains does not exist: the rival is not wrong here. Dropped for
#   that reason, not for difficulty. Note this also means the modeled site is the
#   one whose decision genuinely IS textual; the site that consults a structural
#   fact is the unmodeled 2-D one.
#
# DIVERGENCE — CLOSED BY THE CARRIER on this cell (corrected by audit; the
#   earlier text here asserted the opposite and was factually wrong about this
#   bundle's own semantics, so it is replaced rather than softened).
#
#   `Solution.lean` line 4 sets `loom.semantics.termination "total"`, NOT
#   "partial". Under total-correctness semantics the verifier discharges a
#   termination obligation, so a rival whose loop carries no decreasing measure
#   is genuinely REJECTED and there is no vacuous-satisfaction hole to record.
#   The superseded text claimed the reverse ("this bundle sets ... "partial"",
#   and that a diverging variant VERIFIES at exit 0). No bundle in this corpus
#   sets "partial", so that reading describes nothing here, and the internal
#   findings note it once cited has been withdrawn; the mechanism is cited below
#   instead, from the carrier's own source.
#
#   Why the option cannot be inert. The `set_option` elaborator itself opens the
#   matching scope (Loom/MonadAlgebras/WP/Options.lean, `openScope`, where "total"
#   opens `TotalCorrectness`), and Velvet/Syntax.lean:386 opens the same scope by
#   default, so the option and the surrounding `open` cannot disagree. Under
#   `TotalCorrectness` the loop combinator `forWithInvariantLoop` takes
#   `measure : β -> Nat` and emits a per-iteration goal `measure b' < measure b`;
#   the `PartialCorrectness` twin takes `measure : β -> Option Nat` and DISCARDS
#   it. A postcondition is therefore claimed of ALL runs here, not only
#   terminating ones, so a diverging rival cannot satisfy `ensures` vacuously.
#
#   Re-measured on THIS cell, four builds, with the frozen `prove_correct`
#   header kept (keeping the frozen proof TAIL makes a rival look rejected for a
#   tactic reason, which is the trap these builds avoid):
#     * frozen body with a measure-free `while spin = 0` prefix  -> exit 1,
#       `error: Decreasing annotations are required in total correctness
#       semantics` (+ `Failed to prove assertion without names: WPGen`);
#     * the sharper form, diverging and then returning the unambiguously wrong
#       empty rendering                                          -> exit 1,
#       same decreasing-annotation error;
#     * a GUARDED hybrid that is exactly correct for `terms.length ≤ 3` and
#       diverges only above it (so the ONLY thing wrong with it is the missing
#       measure)                                                 -> exit 1,
#       same error;
#     * the DECISIVE form, which carries a measure so it cannot be dismissed as
#       merely un-annotated: `let mut k : Nat := 1` / `while k > 0` with
#       `invariant k > 0`, `done_with k = 0`, `decreasing k`, body `k := k + 1`
#                                                                -> exit 1,
#       and the failure is the measure's OWN descent goal,
#       `case decreasing_1: k ... |- k + 1 < k`, reported as `unsolved goals`.
#   So the annotation is required to be TRUE and not merely PRESENT, the class is
#   closed by the carrier here, on a real proof obligation, and NOT by anything
#   this battery does.
#
#   It is still not shipped as a reject case, for a reason that is about the
#   WITNESS rather than about the spec. A reject case must carry a witness that
#   elaborates against the rival, and the rival's own build is what fails: the
#   missing decreasing annotation is a hard elaboration error, so the tester the
#   witness needs (`joinSignedMatrixTermsTester`) is never derived and `decide`
#   on it reports `did not reduce to isTrue or isFalse` — measured, exit 1
#   against the rival, which is `witness-unproven`, an INCONCLUSIVE outcome that
#   would fail the gate rather than pass it. The rejection here is therefore
#   real but not witness-attributable, which is exactly the shape the gate
#   declines to record. Noted so a later port does not read the absence of a
#   `diverge-*` case as an unmeasured gap: it was measured, three ways, and the
#   carrier rejects it.
#
# BINDER / CLAUSE COVERAGE. The spec has ONE input binder, `terms`, and one
#   top-level clause, `out = joinSignedTerms terms`, whose four independent
#   decisions are each attacked by a rival built for it:
#     leading term verbatim  -> weak-strip-leading-term-marker (marker dropped),
#                               weak-leading-term-as-tail (separator + sign added)
#     sign glyph per term    -> weak-plus-join-verbatim, weak-body-stripped-sign-fixed
#     body marker-stripped   -> weak-sign-emitted-marker-kept
#     separating spaces      -> weak-drop-separating-spaces
#     contribution ORDER     -> weak-reverse-tail-order
#     whole-discipline swap  -> weak-single-space-marker-kept
#   The sole binder is varied across all EIGHT reject witnesses, which sit at
#   eight DISTINCT input points (pts = 8) — no two rivals share a point, so no
#   rival's claimed sub-domain is left undemonstrated:
#     [['a'],['-','b']]                 length 2, marker on the SECOND term
#     [['-','b'],['a']]                 length 2, marker on the FIRST term
#     [['a']]                           length 1, the singleton BOUNDARY (loop
#                                       body never runs; `require`'s smallest input)
#     [['a'],['-','b'],['c']]           length 3, marker in the MIDDLE
#     [['x'],['-','y']]                 length 2, distinct leading term
#     [['-','c'],['a'],['-','b']]       length 3, marker on FIRST and LAST
#     [['p'],['q'],['-','r']]           length 3, marker on the LAST term only
#     [['a'],['b'],['-','c']]           length 3, reversal-observable
#   The binder is varied along every axis the clause can depend on: sequence
#   LENGTH (1, 2, 3 — including the singleton where the loop is skipped entirely),
#   the POSITION of a marked term (first / middle / last / several at once),
#   multi-character bodies, and marker-free sequences as the correct backdrop. The
#   two near-miss pairs are separated: the sign-vs-body mirrors
#   (weak-sign-emitted-marker-kept / weak-body-stripped-sign-fixed) sit at
#   different points and different lengths, and the order rival sits at the only
#   point where a reversal is observable at all.
#
# AUDIT PROBES (attacks D and E), recorded so they are not re-derived. None of
#   these is shipped as a case; they are the independent audit's own rivals and
#   reshapes, built against the frozen spec with the region surgery above.
#
#   D (SPEC-TOO-WEAK probe — a wrong impl that VERIFIED would be a spec hole).
#   Four new wrong impls, aimed at what the shipped eight leave unattacked. All
#   four were REJECTED (exit 1), and each carries a witness that elaborates
#   against it (exit 0), so the spec senses every one:
#     * strip ALL leading markers rather than one — differs only at a term with a
#       DOUBLED marker (`[['a'], ['-','-','b']]`), a shape no shipped point has;
#     * LENGTH-GATED: exactly correct for `terms.length ≤ 3`, wrong only at
#       length ≥ 4. Aimed squarely at the fact that all eight shipped witnesses
#       sit at length ≤ 3, i.e. it probes whether the CLAUSE is universally
#       quantified or only pinned where the battery looks. Refuted at
#       `[['a'],['b'],['c'],['d']]`;
#     * sign taken from the already-stripped BODY instead of the term
#       (`termSign (termBody t)`) — an idempotence slip that looks harmless;
#     * differs only on an EMPTY non-leading term (`[['a'], []]`), where
#       `head? = none`, the one input shape every shipped point avoids.
#   No spec hole found: the `ensures` clause pins the rendering pointwise over
#   the whole domain, not merely at the battery's eight points.
#
#   E (SPEC-TOO-STRONG probe — a faithful correct impl the spec REJECTED would be
#   a soundness hole). Correct reshapes beyond the three shipped positives:
#     * `foldr` over the tail instead of `flatMap`            -> VERIFIES (0);
#     * a direct `match` on the input, no `drop`/index at all -> VERIFIES (0);
#     * `reverse` then `foldl` (accumulating in the opposite
#       direction to both the frozen loop and the shipped
#       forward reshape)                                     -> VERIFIES (0).
#   One reshape is UNRESOLVED rather than a finding: a FORWARD `while` loop that
#   appends (the mirror of the frozen backward walk) could not be closed by the
#   audit. Its `ensures` obligation is fine; the loop INVARIANT needs a
#   take/append step lemma (`joinTail ((terms.take (i+1)).drop 1) = joinTail
#   ((terms.take i).drop 1) ++ tailPiece terms[i]!`) that the frozen `pure`
#   region does not supply and that a variant may not add without leaving
#   variant scope. So this is a limit of what region surgery can prove here, NOT
#   a demonstrated spec-too-strong: the same behaviour DOES verify in three other
#   shapes above, including an accumulator-free forward one
#   (`pos-forward-flatmap`), which is the evidence that the spec does not
#   privilege the backward traversal. Marked uncertain deliberately rather than
#   claimed as a hole.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores them;
# meta.json records `axioms: []` and `deep_model_references: []` (the rendering is
# modeled deeply in the `pure` region and checked by G-CONF and G-AX), so there is
# nothing there to probe.
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for sympy__sympy-11618 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a three-input domain):

  sqSeparation (sameKind : Bool) (a b : List Rat) : Rat
      result = sqSep sameKind a b
    where
      commonLen sameKind a b = if sameKind then min a.length b.length
                                           else max a.length b.length
      sqSep sameKind a b = Σ_{i < commonLen sameKind a b} (a.getD i 0 - b.getD i 0)^2

  Coordinate sequences are modeled as ``List Rat`` (mapping.md: order-preserving
  coordinate lists; the square-root outer wrapper is constant/order-preserving
  and modeled away, so the observable is the radicand). ``sameKind`` is the kind
  discriminator between the two points. The single top-level clause pins the
  radicand to the sum of squared coordinate differences over the COMPARED
  DIMENSION, and that dimension is chosen by three inseparable sub-decisions,
  each pinned to a distinct binder:

    * WHICH dimension the comparison runs in — ``min`` when the two points are
      of the same kind (the trailing coordinates of the longer sequence are
      dropped), ``max`` when they are of different kinds (the shorter sequence
      is zero-embedded into the larger ambient space and its missing trailing
      coordinates contribute nothing extra, while the longer sequence's surplus
      coordinates are NOT dropped). Pinned by ``sameKind``.
    * WHICH coordinates enter each squared difference — position by position up
      to the compared dimension, an out-of-range coordinate reading as ``0``.
      Pinned by ``a`` and ``b``.
    * The full extent of the compared dimension — every position below it
      contributes; none is dropped and none beyond it is added. Pinned by the
      interaction of ``sameKind`` with the two lengths.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — SPLIT. The nagini sibling makes an input-write
    attack MANDATORY because its modeled inputs are held at fractional
    (read-only) permission and a rival that overwrites one is rejected for
    insufficient permission. That MECHANISM is genuinely inexpressible here:
    Lean is referentially transparent, the three inputs are plain immutable
    values (``Bool`` / ``List Rat``), and there is no half-permission to violate
    and no aliasing to exploit — a rival cannot be rejected "for insufficient
    permission" because there is no permission.

    But the frame attack's BEHAVIORAL content is expressible, and is the half
    that carries the soundness question: nagini's own refinement argument for
    that case is that a rival which copies the coordinate sequence and zeroes it
    before summing computes the separation from ALTERED coordinates. On this
    carrier that is a value-level rebinding of a local (``let a := a.map …``),
    which needs no mutation at all, and it IS refuted — see
    ``weak-altered-coordinates``. So the class contributes a real case here; only
    its permission-system reason for rejecting does not carry over.

  * UNGROUNDED-ORACLE ECHO — VACUOUS on the nagini carrier (there the radicand
    is fed to an opaque ``root`` whose value is unpinned, so the discriminating
    content is ``root``'s argument). Here there is no opaque wrapper at all: the
    bundle declares NO ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []) and the radicand is spelled out structurally, so
    there is no answer key an implementation could echo without doing the work.
    The honest analogues are the cheapest-correct POSITIVE CONTROL and the
    degenerate constant rival below.

  * PARTIAL-DOMAIN (min-truncation) — APPLIES, and is the load-bearing rival.
    The pre-fix behavior pairs coordinates via the plain truncating pairing that
    STOPS at the shorter sequence REGARDLESS of kind, i.e. it uses ``min``
    unconditionally. It coincides with gold exactly on the same-kind path and
    diverges on the different-kind unequal-length sub-domain — precisely the F2P
    observable — so it is a direct attack on the ``sameKind`` discriminator and
    is refuted there.

  * PARTIAL-DOMAIN (drop-last-axis) and DEGENERATE CONSTANT — APPLY. An
    off-by-one upper bound that drops the final position of the compared
    dimension, and an impl that returns the constant ``0`` doing no work, each
    violate the one clause on a distinct sub-domain and are refuted with
    witnesses at distinct inputs.

  * CARRIER-NEW rivals, added because the three above leave two of the clause's
    three sub-decisions attacked from only ONE side:

      - ``weak-unconditional-max``: the mirror image of the min-truncation
        rival. Min-truncation ignores the kind discriminator by always using the
        SMALLER dimension (understating); this one ignores it by always using the
        LARGER (overstating, i.e. padding a same-kind pair that must truncate).
        Refuted on the SAME-KIND differing-length sub-domain, which no other
        rival reaches — so the discriminator is now pinned in both directions
        rather than only against collapse-to-min.
      - ``weak-altered-coordinates``: the behavioral half of nagini's frame
        attack (above). The compared dimension is chosen correctly and every
        position below it is summed, so it attacks ONLY the "which coordinates
        enter each squared difference" sub-decision, which the other rivals
        perturb only jointly with the range.
      - ``weak-edge-extend-pad``: the sub-clause NO other rival reaches — the
        VALUE a position within the compared dimension reads when one sequence
        is too short to have a coordinate there. Every other rival either gets
        that read right (so the clause is never perturbed) or perturbs it
        jointly with something else: ``weak-altered-coordinates`` corrupts the
        IN-RANGE reads too, and both dimension rivals leave the reads alone and
        move the range. This one reads the too-short sequence's LAST coordinate
        instead of ``0``, so it is exactly the "missing trailing coordinates
        read as zero" half of the clause and nothing else. Measured over a
        2738-point sweep of the input space: it agrees with the spec on ALL
        1369 same-kind points, on ALL 1058 equal-length points, and on ALL 264
        different-kind unequal-length points whose shorter sequence ends in a
        zero coordinate; it diverges on 560 points, every one of them a
        different-kind unequal-length pair whose shorter sequence ends nonzero.
        That is what makes it the battery's sharpest verify-does-not-imply-
        resolve candidate: the shorter sequence on the F2P observable DOES end
        in a zero coordinate, so this rival reports the F2P value correctly
        (radicand 5, machine-checked) and would pass the whole graded test set
        while getting the zero-embedding wrong everywhere the graded tests do
        not look. It is refuted at a mirror-orientation point whose shorter
        sequence ends nonzero.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input; each was built (against the rival) and rebuilt (against the
frozen solution) to confirm it HOLDS of its rival and FAILS on gold (so it
discriminates rather than asserting a tautology). ``decide`` cannot be used: the
spec predicate is a ``Prop`` over ``Rat`` with no ``Decidable`` instance
(measured: ``failed to synthesize Decidable ¬ problem_spec_sqSeparation …``), so
each witness unfolds the spec + impl and closes the arithmetic with ``norm_num``
after reducing the range fold.

The gold-side failure is a SEMANTIC refutation, not a syntactic accident, and
that was checked rather than assumed. Every reject case's gold-side build fails
with ``unsolved goals ⊢ False`` — the tactic fully reduced the concrete
arithmetic and was left proving ``False``, i.e. gold's value at that input SATISFIES
the spec — never with an unknown identifier, a type error, an unfolding failure,
or a stuck reduction. Note what that signature rules out, since ``⊢ False`` is
also what a hollow case can look like: the goal is ``False`` because the tactic
ALREADY discharged the concrete equation and consumed the ``¬``, so gold's exit
code is a function of the claim. The controls below are what establish that, and
the first is the decisive one — flip the claim and gold's exit code CHANGES:

  * FLIPPED CLAIM vs GOLD. The same witness file with the ``¬`` DROPPED, built
    against the frozen solution, ELABORATES (exit 0) at every one of the six
    refutation points — against exit 1 for the ``¬`` form. Same file, same
    tactic, one character different, opposite exit codes: gold's exit code
    therefore carries information about WHAT IS CLAIMED and not merely about the
    shape of the goal. This is the control that separates a real refutation from
    a gold-side error that would have fired for any claim at all.
  * FLIPPED CLAIM vs RIVAL. The non-``¬`` form applied to each rival at its own
    REFUTATION point FAILS (exit 1, ``⊢ False``), so the two outcomes are not an
    artifact of which claim is easier to close — the tactic tracks truth in both
    directions on both subjects.
  * ``¬`` FORM AT AN AGREEMENT POINT. Applied to a rival at an input where that
    rival coincides with gold, it FAILS, so the tactic does not prove ``¬ spec``
    of anything handed to it. Checked for the min-truncation rival at
    ``sameKind = true`` and for ``weak-edge-extend-pad`` at the F2P input itself,
    where that rival is correct.

None of the witnesses conditions on a hypothesis (all state their refutation at
literal inputs), so there are no assumptions for the gate's consistency probe to
find inconsistent.

BINDER COVERAGE. All three input binders are varied across the reject witnesses:
  * ``sameKind`` — refuted at ``false`` (min-truncation, drop-last-axis) AND at
    ``true`` (degenerate constant, unconditional-max, altered-coordinates), and
    in BOTH directions of getting the discriminator wrong (collapsing it to
    ``min`` and collapsing it to ``max``), so the discriminator is pinned rather
    than merely varied.
  * ``a`` / ``b`` — refuted at differing-length pairs (both different-kind
    orientations) AND at same-kind pairs of equal and of differing length,
    exercising the coordinate reads at several shapes rather than a single point.
  * the PADDING VALUE — the coordinate a position within the compared dimension
    reads when one sequence is too short — is observable ONLY on the
    different-kind unequal-length sub-domain, and only there does
    ``weak-edge-extend-pad`` diverge; it is refuted at a pair whose shorter
    sequence ends NONZERO, since a shorter sequence ending in ``0`` makes the
    zero-embedding and the edge-extension coincide.
``pts`` = 6 distinct input points.

SUB-CLAUSE SEPARATION. The sub-decisions are attacked INDEPENDENTLY, not only
jointly: ``weak-altered-coordinates`` gets the compared dimension exactly right
and still fails (isolating the in-range coordinate reads), ``weak-unconditional-
max`` reads every coordinate correctly and fails only on the dimension choice
(isolating the discriminator), and ``weak-edge-extend-pad`` gets BOTH the
dimension and every in-range read right and fails only on the value a missing
coordinate reads as (isolating the zero-embedding). A rival that perturbs two of
these at once cannot tell which clause is load-bearing, which is why each is
also refuted at a shape where the other two are unambiguous.

OMITTED nagini cases (see assessment): the frame rival's PERMISSION mechanism
(inexpressible — no fractional permission on this carrier; its behavioral content
is ported instead as ``weak-altered-coordinates``) and the AXIOM_TESTS lane (this
bundle declares no axiom / deep-model reference — G-AX skips — and the axiom
lane is not this gate's job).

DIVERGENCE LANE: measured, and NOT shippable as a reject case on this bundle —
recorded here rather than left unstated. The frozen solution sets no
``loom.semantics.termination`` option at all; it is a plain Lean 4 + Mathlib file
whose impl is a bounded ``for i in [0:n]``, so there is no termination obligation
for a rival to fail and no ``partial``-semantics vacuity either. A diverging rival
WAS built to check this rather than argued: ``partial def sepLoop`` recursing
without a decreasing measure, spliced into the impl region. It is admissible
scope (``variant_problems`` = ``[]``) and it IS rejected (module build exit 1,
``unsolved goals … sepLoop a b 0 … = List.foldl …``) — but the rejection is a
TACTIC MISMATCH, not a refutation: ``partial def`` is opaque to the kernel, so no
witness can refute it. Measured both ways. A literal-input witness fails against
the rival itself (exit 1, ``unsolved goals ⊢ ¬sepLoop [5] [1] 0 1 0 = 16``), which
is ``witness-unproven``; and a hypothesis-conditioned witness
(``example (h : implementation_sqSeparation true [5] [1] ≠ 16)``) fails the
DISCRIMINATION half instead — it elaborates against BOTH the rival and the frozen
solution (exit 0 / exit 0), i.e. ``witness-vacuous``, because the hypothesis
alone yields the refutation whatever the impl is. A witness naming ``sepLoop``
directly is refused by ``witness_scope_problems`` (a name the frozen solution does
not declare). So this class is a KNOWN HOLE of the carrier's opacity, not a
vacuous class and not an omission the battery could close: the rejection is real
but unattributable, which is exactly the situation the witness requirement exists
to refuse to count. No case is shipped for it.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
compared-dimension choice and the squared-difference sum are modeled DEEPLY over
the inputs, so there is no axiom-soundness / axiom-containment obligation to
probe here. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-11618"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let n := if sameKind then min a.length b.length else max a.length b.length\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2\n"
    "  return acc"
)

_PROOF_BODY = (
    "  intro sameKind a b\n"
    "  unfold problem_spec_sqSeparation implementation_sqSeparation sqSep commonLen\n"
    "  simp [List.range_eq_range']"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# MIN-TRUNCATION (= the pre-fix bug): the coordinate pairing STOPS at the
# shorter sequence REGARDLESS of kind, i.e. it uses `min` unconditionally,
# dropping the trailing coordinates of the longer sequence even when the two
# points are of different kinds and should be compared in the LARGER dimension.
_MIN_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let n := min a.length b.length\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2\n"
    "  return acc"
)

# DROP-LAST-AXIS: an off-by-one upper bound — the compared dimension is chosen
# correctly but the loop stops one position short (Nat subtraction clamps at 0),
# so the final position of the compared dimension is never summed.
_DROPLAST_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let m := if sameKind then min a.length b.length else max a.length b.length\n"
    "  let n := m - 1\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2\n"
    "  return acc"
)

# DEGENERATE CONSTANT: ignore the inputs entirely and return the constant 0,
# doing no work.
_ZERO_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := 0"
)

# UNCONDITIONAL-MAX: the mirror image of _MIN_IMPL. The comparison always runs in
# the LARGER dimension, so the kind discriminator is ignored in the OPPOSITE
# direction: a pair of the SAME kind whose sequences differ in length is
# zero-embedded and its surplus trailing coordinates are summed, when the
# same-kind path must truncate to the shorter sequence and drop them.
_MAX_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let n := max a.length b.length\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2\n"
    "  return acc"
)

# ALTERED COORDINATES: the compared dimension is selected correctly and every
# position below it is summed — but one sequence's coordinates are zeroed first,
# so the squared differences are taken against ALTERED coordinates rather than
# the ones supplied. Attacks the coordinate-read sub-decision in isolation.
_ALTERED_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let a := a.map (fun _ => 0)\n"
    "  let n := if sameKind then min a.length b.length else max a.length b.length\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2\n"
    "  return acc"
)

# EDGE-EXTEND PAD: the compared dimension is chosen correctly and every position
# below it is summed, and the IN-RANGE coordinate reads are exactly gold's — but a
# position within the compared dimension at which one sequence is too short reads
# that sequence's LAST coordinate instead of `0`. So it perturbs the
# zero-embedding VALUE and nothing else, which no other rival does in isolation.
_EDGEPAD_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let n := if sameKind then min a.length b.length else max a.length b.length\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i (a.getLastD 0) - b.getD i (b.getLastD 0)) ^ 2\n"
    "  return acc"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — the
# compared dimension is computed by lifting from `b.length` instead of
# `a.length` (`min b.length a.length` / `max b.length a.length`), which is equal
# by commutativity of `min`/`max`. Same value on every input; the frozen script
# is retuned to the reshaped `let n` (the extra `min_comm`/`max_comm` rewrite),
# statement byte-identical, no new lemma/axiom.
_POS_IMPL = (
    "def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do\n"
    "  let n := if sameKind then min b.length a.length else max b.length a.length\n"
    "  let mut acc : Rat := 0\n"
    "  for i in [0:n] do\n"
    "    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2\n"
    "  return acc"
)
_POS_PROOF = (
    "  intro sameKind a b\n"
    "  unfold problem_spec_sqSeparation implementation_sqSeparation sqSep commonLen\n"
    "  rw [min_comm b.length a.length, max_comm b.length a.length]\n"
    "  simp [List.range_eq_range']"
)

# ADMISSIBILITY: the frozen impl+proof, with two ground instances discharged
# BEFORE the frozen obligation. Both pin the spec to a LITERAL value rather than
# to `implementation_sqSeparation`'s own output: a ground instance of the form
# `problem_spec … (implementation_sqSeparation …)` is just the frozen theorem
# specialized, so it is provable by `exact correct_sqSeparation …` and attests
# only that the theorem holds — it cannot detect a spec that pins the WRONG
# value. Pinning `5` and `4` makes the case fail if the modeled quantity is not
# the intended one, so the two branch behaviors are checked numerically:
#   * different kind, unequal length -> the shorter sequence is zero-embedded
#     into the larger dimension and the surplus coordinate contributes: 5.
#   * same kind, unequal length -> the comparison truncates to the shorter
#     sequence and the surplus is dropped: 4 (not the padded 8).
_ADMISS_PROOF = (
    "  have _ground : problem_spec_sqSeparation false [1,0,2] [2,0] 5 := by\n"
    "    unfold problem_spec_sqSeparation sqSep commonLen\n"
    "    simp only [List.range_eq_range']\n"
    "    norm_num [List.getD, List.foldl, List.range']\n"
    "  have _truncates : problem_spec_sqSeparation true [1,2] [3] 4 := by\n"
    "    unfold problem_spec_sqSeparation sqSep commonLen\n"
    "    simp only [List.range_eq_range']\n"
    "    norm_num [List.getD, List.foldl, List.range']\n"
    + _PROOF_BODY
)

# Shared witness tactic: unfold spec + impl, reduce the range fold, close the
# concrete Rat (in)equality with norm_num (decide stalls on Rat normalization).
_WIT_TAC = (
    "  unfold problem_spec_sqSeparation implementation_sqSeparation sqSep commonLen\n"
    "  simp only [List.range_eq_range']\n"
    "  norm_num [List.getD, List.foldl, List.range']\n"
)


def _witness(sk, a, b):
    return (
        f"example : ¬ problem_spec_sqSeparation {sk} {a} {b}\n"
        f"    (implementation_sqSeparation {sk} {a} {b}) := by\n"
        + _WIT_TAC
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_sqSeparation`
    # STATEMENT is byte-identical; the tactic body is retuned to the reshaped
    # `let n` (a `min_comm`/`max_comm` rewrite). No helper lemma, axiom, or
    # assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-commuted-dimension",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that computes the compared dimension by lifting "
            "from `b.length` instead of `a.length` (`min b.length a.length` / "
            "`max b.length a.length`, equal by commutativity) must satisfy "
            "`result = sqSep sameKind a b`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Proof: after `unfold`, `rw [min_comm, max_comm]` "
            "restores the frozen form and the range fold closes as in gold — no "
            "new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # behavior is total, so `∀` is unguarded), so nagini's precondition-admission
    # probe has no binder to attack here; the honest analogue is to discharge the
    # spec predicate at the F2P ground input (different-kind, unequal length, so
    # the shorter sequence is zero-embedded into the larger dimension) inside the
    # proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "two ground instances are discharged at LITERAL values by `norm_num` "
            "over the reduced fold, then the frozen obligation is closed "
            "verbatim. Both branch behaviors are pinned numerically: at different "
            "kind `false` with sequences of unequal length `[1,0,2]` vs `[2,0]` "
            "the shorter is zero-embedded into the larger dimension so the "
            "surplus coordinate contributes and the radicand is `5`; at same kind "
            "`true` with `[1,2]` vs `[3]` the comparison truncates to the shorter "
            "sequence and the radicand is `4`, NOT the padded `8`. Pinning "
            "literals rather than `implementation_sqSeparation`'s own output is "
            "what gives this case content — a ground instance stated over the "
            "impl is the frozen theorem specialized (`exact correct_sqSeparation "
            "…` closes it) and would verify even if the spec pinned the wrong "
            "value. Verifies (else the spec is unsatisfiable at the normal input, "
            "the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the theorem "
            "STATEMENT is byte-identical, both ground instances are `have`s inside "
            "the existing tactic body, and no new declaration/axiom/`sorry` is "
            "introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-min-truncation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MIN_IMPL),
        "refinement": (
            "this is the pre-fix behavior: the coordinate pairing STOPS at the "
            "shorter sequence REGARDLESS of the kind of the two points (a plain "
            "truncating pairing), so the trailing coordinates of the longer "
            "sequence are dropped even when the points are of different kinds and "
            "must be compared in the larger dimension. On the F2P observable — a "
            "3-coordinate point against a 2-coordinate point of a different kind, "
            "coordinates `[1,0,2]` vs `[2,0]` — it sums only positions 0,1 "
            "(radicand 1) instead of embedding the shorter sequence and summing "
            "all three (radicand 5), so the reported separation is understated. "
            "It does NOT resolve — this is the literal pre-patch."
        ),
        "rationale": (
            "REJECT from the clause `result = sqSep sameKind a b`: at "
            "`sameKind = false`, `a = [1,0,2]`, `b = [2,0]` the compared "
            "dimension is `max = 3`, so the spec demands the position-2 "
            "coordinate contribute `(2-0)^2 = 4` (radicand 5), but the rival's "
            "unconditional `min = 2` drops it (radicand 1). Refuted on the "
            "different-kind unequal-length sub-domain — a direct attack on the "
            "`sameKind` discriminator (the rival ignores it). If it verifies, the "
            "spec does not force the larger ambient dimension on the "
            "different-kind path (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("false", "[1,0,2]", "[2,0]"),
    },
    {
        "id": "weak-drop-last-axis",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROPLAST_IMPL),
        "refinement": (
            "off-by-one upper bound: the compared dimension is selected correctly "
            "but the loop stops one position short, so the FINAL position of the "
            "compared dimension is never summed. On the F2P observable "
            "(different-kind, coordinates `[1,0,2]` vs `[2,0]`, compared "
            "dimension 3) it sums only positions 0,1 (radicand 1) and drops the "
            "position-2 coordinate `2` (which contributes `+4`), giving 1 instead "
            "of 5. A real patch with an off-by-one bound on the compared "
            "dimension would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = sqSep sameKind a b`: at "
            "`sameKind = false`, `a = [1,2,9]`, `b = [3,4]` the compared "
            "dimension is `max = 3`, so the spec sums positions 0,1,2 including "
            "the position-2 term `(9-0)^2 = 81`, but the rival stops at "
            "`3 - 1 = 2` and omits it. Refuted where a genuine last-position "
            "coordinate contributes, exercising `a` and `b` at a longer "
            "differing-length shape distinct from the other witnesses. If it "
            "verifies, the postcondition leaves the final position unpinned "
            "(partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": _witness("false", "[1,2,9]", "[3,4]"),
    },
    {
        "id": "weak-degenerate-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ZERO_IMPL),
        "refinement": (
            "returns the constant `0` for EVERY input, doing no work. Then the "
            "reported separation is 0 for the F2P observable (and every "
            "positive-separation case), when it must be the sum of squared "
            "coordinate differences over the compared dimension (5 on the F2P "
            "input). A real patch returning a constant separation would not "
            "resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = sqSep sameKind a b`: at "
            "`sameKind = true`, `a = [4]`, `b = [1,1]` the compared dimension is "
            "`min = 1`, so the spec demands `(4-1)^2 = 9`, but the rival returns "
            "`0`. Refuted with `sameKind = true` — varying that binder off the "
            "`false` value the other rivals use — confirming the clause pins the "
            "radicand to the actual squared-difference sum, not merely its sign. "
            "If it verifies, the spec is hollow (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("true", "[4]", "[1,1]"),
    },
    {
        "id": "weak-unconditional-max",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MAX_IMPL),
        "refinement": (
            "the MIRROR IMAGE of the min-truncation rival, and the reason it is "
            "needed: min-truncation gets the kind discriminator wrong by always "
            "comparing in the SMALLER dimension, so refuting it shows only that "
            "the spec forbids collapsing the choice to `min`. This one collapses "
            "the choice to `max` — the comparison always runs in the LARGER "
            "dimension — so a pair of the SAME kind whose sequences differ in "
            "length is zero-embedded and its surplus trailing coordinates are "
            "summed, when the same-kind path must truncate to the shorter "
            "sequence and drop them. It coincides with gold on the whole "
            "different-kind path (including the observable the F2P exercises) and "
            "diverges only on the same-kind differing-length sub-domain, which the "
            "current F2P/P2P set does not reach — so it is exactly a "
            "verify-does-not-imply-resolve candidate: it would pass the graded "
            "tests while overstating the separation for same-kind points of "
            "differing coordinate count, e.g. reporting radicand 8 instead of 4 "
            "for `[1,2]` against `[3]`. Refuting it is what makes the "
            "discriminator pinned in BOTH directions instead of one."
        ),
        "rationale": (
            "REJECT from the clause `result = sqSep sameKind a b`: at "
            "`sameKind = true`, `a = [1,2]`, `b = [3]` the compared dimension is "
            "`min = 1`, so the spec sums position 0 only and demands "
            "`(1-3)^2 = 4`, but the rival's unconditional `max = 2` also sums "
            "position 1, adding `(2-0)^2 = 4` for a radicand of 8. Refuted on the "
            "SAME-KIND differing-length sub-domain, which no other rival in this "
            "battery reaches. If it verifies, the spec does not force the SMALLER "
            "dimension on the same-kind path — i.e. it would admit an impl that "
            "pads unconditionally (SPEC-TOO-WEAK), the exact over-correction a "
            "faithful fix must avoid."
        ),
        "witness": _witness("true", "[1,2]", "[3]"),
    },
    {
        "id": "weak-altered-coordinates",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALTERED_IMPL),
        "refinement": (
            "the behavioral content of the nagini sibling's frame-mutation rival, "
            "ported to a carrier with no mutation: instead of overwriting an input "
            "in place it rebinds a local copy of one coordinate sequence to zeros "
            "and sums against THAT. Nagini's own refinement argument for that case "
            "is this exact behavior — an impl that zeroes the coordinate vector "
            "before summing computes the separation from ALTERED coordinates — so "
            "the class survives the port even though its permission-system "
            "rejection reason does not. It is also the only rival that selects the "
            "compared dimension CORRECTLY on every input and sums every position "
            "below it, so it isolates the coordinate-read sub-decision from the "
            "range sub-decision the other rivals perturb alongside it. A real "
            "patch that normalized a coordinate sequence to zeros before "
            "differencing would report the separation from the origin instead of "
            "between the two points and would not resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = sqSep sameKind a b`: at "
            "`sameKind = true`, `a = [5]`, `b = [1]` the compared dimension is "
            "`min = 1` — which the rival computes correctly — but the spec demands "
            "the squared difference of the coordinates SUPPLIED, `(5-1)^2 = 16`, "
            "while the rival differences the zeroed copy and returns "
            "`(0-1)^2 = 1`. Refuted at an EQUAL-LENGTH same-kind pair, a shape no "
            "other witness uses, which is what makes the attribution clean: the "
            "compared dimension is unambiguous there, so the failure can only be "
            "the coordinate reads. If it verifies, the spec pins the compared "
            "dimension but leaves WHICH coordinates enter each squared difference "
            "free (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("true", "[5]", "[1]"),
    },
    {
        "id": "weak-edge-extend-pad",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EDGEPAD_IMPL),
        "refinement": (
            "the sharpest verify-does-not-imply-resolve candidate in this "
            "battery, and the only rival that isolates the zero-embedding VALUE. "
            "The compared dimension is chosen correctly, every position below it "
            "is summed, and every IN-RANGE coordinate read is exactly the "
            "supplied one — but a position within the compared dimension at "
            "which one sequence is too short reads that sequence's LAST "
            "coordinate instead of `0`, i.e. the shorter sequence is embedded by "
            "extending its final coordinate rather than at the origin. Measured "
            "over a 2738-point sweep of the input space it agrees with the spec "
            "on all 1369 same-kind points, all 1058 equal-length points, and all "
            "264 different-kind unequal-length points whose shorter sequence ends "
            "in a zero coordinate, diverging only on the 560 different-kind "
            "unequal-length points whose shorter sequence ends nonzero. The "
            "shorter sequence on the F2P observable ends in a zero coordinate, so "
            "this rival reports the F2P radicand CORRECTLY as 5 (machine-checked) "
            "and would pass the graded test set unchanged while understating or "
            "overstating the separation for every different-kind pair whose "
            "shorter point does not happen to end at the origin — e.g. a "
            "3-coordinate point against `[2,3]`, where it reports 11 instead of "
            "14. A real patch that extended the shorter point's last coordinate "
            "instead of padding with zeros would resolve the F2P and still be "
            "wrong, which is exactly the break this lane exists to catch."
        ),
        "rationale": (
            "REJECT from the clause `result = sqSep sameKind a b`, specifically "
            "its `getD i 0` — the requirement that a position within the compared "
            "dimension where a sequence has no coordinate read as `0`: at "
            "`sameKind = false`, `a = [1,0,2]`, `b = [2,3]` the compared "
            "dimension is `max = 3` and the spec reads `b`'s missing position-2 "
            "coordinate as `0`, demanding `(1-2)^2 + (0-3)^2 + (2-0)^2 = 14`, but "
            "the rival reads it as `b`'s last coordinate `3` and returns "
            "`1 + 9 + 1 = 11`. Refuted at a shape no other witness uses: a "
            "different-kind unequal-length pair whose SHORTER sequence ends "
            "NONZERO, which is the only region where the padding value is "
            "observable at all. Every other rival either reads `0` out of range "
            "exactly as gold does or corrupts the in-range reads alongside it, so "
            "if this one verifies the spec pins the compared dimension and the "
            "in-range coordinate reads while leaving the PADDING VALUE free "
            "(SPEC-TOO-WEAK) — the one sub-decision the rest of the battery "
            "cannot distinguish."
        ),
        "witness": _witness("false", "[1,0,2]", "[2,3]"),
    },
]


# No consumed axioms and no deep-model references: the compared-dimension choice
# and the squared-difference sum are modeled directly over the inputs, so there
# is no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []

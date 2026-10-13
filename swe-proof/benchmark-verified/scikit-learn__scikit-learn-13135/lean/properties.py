"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13135 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text strictly inside ``-- impl-start`` / ``-- impl-end`` — and, for
a case that legitimately re-proves or exhibits an inhabitant, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the single ``theorem correct_binEdges`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh
invention. The nagini sibling models the same purely-functional core over a
FIXED-ARITY scalar carrier — six ``float`` by-value arguments: four interior
values and the two column bounds — with a ``@ContractOnly`` four-element
ordering stub. It pins seven numbered postcondition clauses (a length, two endpoint equalities,
three ordered-midpoint value equalities, and a monotonicity clause). This Lean
bundle models the SAME behavior over a VARIABLE-LENGTH ``List Rat`` carrier and
folds those seven clauses into a single existential statement, so the port is a
re-expression rather than a translation: each nagini rival is re-aimed at
whichever conjunct of the existential its argument attacks. Two rivals here have
no nagini counterpart precisely because of that carrier widening (see
``assessment``): with a variable-length list, an implementation can change the
MULTISET of interior values, which a four-scalar carrier cannot express.

DEFENDED SURFACE (one modeled behavior, one obligation).

  ``problem_spec_binEdges (colMin colMax : Rat) (centers result : List Rat)``

pins the boundary list produced from a set of cluster centers and a column's
minimum and maximum. It is a single existential with three conjuncts, and all
three are independently load-bearing:

  * (C0 PERM)  ``cs.Perm centers`` — the arrangement the boundaries are derived
    from must contain exactly the input centers, each as many times as it
    occurs. Nothing may be dropped, duplicated, or invented.
  * (C1 SORTED)  ``List.Sorted (· ≤ ·) cs`` — that arrangement must be
    ascending. This is the order-normalization the downstream digitization step
    requires, and the clause the pre-existing behavior violates.
  * (C2 SHAPE)  ``result = colMin :: (midpoints cs ++ [colMax])`` — the result
    is the column minimum, then the CONSECUTIVE pairwise midpoints of that
    ascending arrangement, then the column maximum. This one equation
    simultaneously fixes the length, both brackets and their orientation, the
    pairing of each interior boundary with its two ADJACENT elements, and each
    interior boundary's exact value.

Because C0 and C1 together determine ``cs`` uniquely (antisymmetry of ``≤`` on
``Rat``), the spec is GROUNDED in the inputs: there is no opaque answer key an
implementation could echo, and satisfying C2 requires actually order-normalizing
the centers and forming the adjacent midpoints. That is why the nagini sibling's
"ungrounded-oracle echo" class has no wrong echo THERE and none here either;
both bundles ship honest positive controls in its place, plus the
``weak-flat-interior`` rival below, which exists specifically to show C2's value
content is load-bearing beyond the weaker monotonicity property a reader might
mistake it for.

BINDER STRUCTURE AND POINT SPREAD. The predicate has THREE input binders:
``colMin``, ``colMax``, ``centers``. All three are moved by the reject
witnesses, and no binder is held at one value across the battery:

  * ``colMin`` ∈ {0, 1, 2} (6 witnesses at 0, 3 at 1, 2 at 2);
  * ``colMax`` ∈ {4, 5, 6, 7, 8, 9, 10, 12};
  * ``centers`` ranges over ascending, descending and arbitrary-order lists, of
    length 2 and 3, with and without a repeated element, and with adjacent sums
    both EVEN and ODD (the latter added by the audit — see
    ``weak-truncated-interior``: without it every witness sat at an integer-valued
    interior boundary and a truncating rival agreed with the frozen behavior at
    every point the battery probed).

Two binders are attacked DIRECTLY rather than only carried: ``weak-endpoint-swap``
and ``weak-self-bracket`` are refuted because they mishandle ``colMin`` /
``colMax`` specifically, so neither bracket binder is one that "every witness
holds at the same value" — the failure mode the coverage tooling exists to find.
The twelve reject witnesses probe TWELVE DISTINCT input points (the
audit-added ``weak-nonterminating`` states its refutation over a PAIR of inputs,
which is what an argument-independent body requires; its first point coincides
with ``weak-no-normalization``'s and its second, ``(1, 20, [5])``, is the only
single-center point and the only ``colMax = 20`` in the battery).

CLAUSE COVERAGE. Every conjunct is attacked by at least one rival:

  * C0 PERM — ``weak-collapse-repeats`` (collapses coincident centers, so the
    arrangement its boundaries come from is a strict sub-multiset of the input).
  * C1 SORTED — ``weak-no-normalization`` (the pre-existing behavior: no
    ordering at all) and ``weak-descending`` (normalizes, then reports the
    opposite orientation).
  * C2 SHAPE — ``weak-endpoint-swap`` and ``weak-self-bracket`` (brackets),
    ``weak-short-by-one`` (length), ``weak-head-paired`` and
    ``weak-raw-trailing-pair`` (which pair each interior boundary averages),
    ``weak-flat-interior`` (interior values), ``weak-unhalved-interior``
    (interior values, a scale error that keeps length and brackets intact),
    ``weak-truncated-interior`` (interior values, the FRACTIONAL part — the
    audit-added rival that agrees with the frozen behavior at every point the
    other ten witnesses probe).

CASE CLASSES, read adversarially on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already records
    this class as N/A for itself: all six of its inputs are by-value scalars, so
    it has no read-only mutable input to overwrite. On this carrier it is doubly
    vacuous — Lean is referentially transparent, ``centers`` is an immutable
    value, and there is no aliasing or fractional-permission notion at all. No
    substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — APPLIES, and is SHIPPED as
    ``weak-nonterminating``. The port originally recorded this class as vacuous
    on the ground that "``implementation_binEdges`` is a total Lean ``def``, so a
    diverging implementation cannot be written in the first place". The AUDIT
    measured that claim and it is FALSE as stated. Three builds settle it:

      - a plain ``def spinForever (n : Nat) : List Rat := spinForever (n + 1)``
        is indeed refused, but by the TERMINATION checker
        (``fail to show termination for spinForever / failed to infer structural
        recursion``) — so the original claim is right only for that one spelling;
      - ``partial def spinForever`` is accepted by the elaborator, and a variant
        whose ``implementation_binEdges`` returns ``spinForever 0`` clears
        ``variant_problems`` with an empty list: ``partial`` is not an assumption
        token, adds no ``axiom``/``sorry``, and leaves the ``theorem
        correct_binEdges`` statement byte-identical. So the rival IS expressible
        and IS in scope, which is exactly the ``UNDERPORTED`` disposition rather
        than a vacuous class;
      - it is genuinely REJECTED, because this bundle's carrier makes the
        verifier discharge termination as part of the obligation.

    The witness needed a different shape from the other eleven, and that is the
    part worth recording. A ``partial def`` is compiled through
    ``WellFounded.fix``/opaque recursion, so the rival's result does not REDUCE:
    a witness that tries to evaluate it is stuck, and a witness CONDITIONED on
    the result (``example (h : (implementation_binEdges …).length ≠ 4)``) was
    measured to elaborate against the FROZEN solution too (exit 0 both sides —
    vacuous, since gold's own length is 4 and the hypothesis is simply false
    there, which the closing tactic never has to notice). What discriminates is
    ARGUMENT-INDEPENDENCE, which needs no evaluation of the opaque term at all:
    the rival ignores ``colMin``/``colMax``/``centers`` entirely, so one and the
    same value would have to satisfy the spec at TWO inputs whose demanded
    results differ. The witness states the conjunction of the obligation at
    ``(0, 10, [0, 4, 2])`` and at ``(1, 20, [5])`` and derives ``False`` by
    IDENTIFYING the two results, which holds only for a body that mentions no
    argument.

    HOW that identification is proved is load-bearing, and the first version of
    this witness got it wrong. A term-mode ``rfl`` typechecks it against the
    rival and fails against gold with

        Type mismatch: rfl has type ?m = ?m but is expected to have type
        implementation_binEdges 1 20 [5] = implementation_binEdges 0 10 [0, 4, 2]

    which LOOKS like a refutation and is not one. The deciding measurement is the
    OPPOSITE-CLAIM control: ``implementation_binEdges 0 10 [0, 4, 2] =
    [0, 1, 3, 10]`` is TRUE of gold — ``#eval`` in the same build prints
    ``[mkRat 0 1, mkRat 1 1, mkRat 3 1, mkRat 10 1]`` — and its ``rfl`` fails
    with the byte-identical shape (only the expected type differs), because
    ``List.mergeSort`` and ``Rat`` division do not reduce at default
    transparency. Gold's exit code there did not depend on what was claimed, so
    it attested nothing about whether gold satisfies the spec.

    The identification is now proved by ``simp only [implementation_binEdges,
    Id.run, pure, hms3, hms1, midpoints]``, which unwraps the ``Id.run``/``do``
    carrier and consumes the two pinned ``mergeSort`` equations, so the two
    applications are actually EVALUATED. For the rival both sides become the same
    opaque ``spinForever 0`` and the step closes; on gold it exhibits gold's own
    two boundary lists, reduced and unequal:

        ⊢ 1 :: ([] ++ [20]) = 0 :: ([(0 + 2) / 2, (2 + 4) / 2] ++ [10])

    Measured: rival 0, gold 1. The same tactic at the same two points claiming
    what is TRUE of gold — ``implementation_binEdges 1 20 [5] = 1 :: ([] ++
    [20])`` and ``implementation_binEdges 0 10 [0, 4, 2] = 0 :: ([(0 + 2) / 2,
    (2 + 4) / 2] ++ [10])``, i.e. gold's own reducts — builds against gold
    (exit 0) and fails against the rival (exit 1, ``⊢ spinForever 0 = …``). The
    FORGERY (the same claim with the ``¬`` dropped, so the spec is asserted to
    HOLD at both points, closed by the same evaluation) inverts cleanly as well:
    gold 0, rival 1. So gold's exit code now turns on what is claimed rather than
    on what happens to reduce.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the reason given above (C0 ∧ C1
    determine ``cs``; nothing to echo). Replaced by three positive controls and
    by ``weak-flat-interior``.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the whole battery.
    ``weak-raw-trailing-pair`` is the sharpest: it agrees with the frozen
    solution on every already-ascending input and diverges only where the raw
    trailing pair is not the two largest, so it is a genuine near-miss and is
    given its own witness at an input that distinguishes it (no witness is
    shared between rivals in this battery).

WITNESS MECHANICS. On a tactic-proof backend "did not verify" is the DEFAULT
outcome of reshaping an implementation — the frozen script ends in ``rfl``, which
breaks for a merely-commuted body just as loudly as for a wrong one. So every
reject case carries a refutation ``witness``: a snippet proving the rival
contradicts the spec at one CONCRETE input, checked in a file with the
obligations removed, and required both to hold of the rival and to FAIL on the
frozen solution. Each of the twelve below was run both ways by hand before
shipping.

Two carrier facts shaped how the witnesses are written, and both were measured
rather than assumed:

  1. The ordering operation does NOT reduce under ``decide``/``rfl``/``simp``
     even on integer literals. So each witness first establishes, as a plain
     ``have``, that the literal centers' ascending arrangement is a specific
     list — via permutation, sortedness and antisymmetry of ``≤`` — and hands
     that equation to the closing tactic. The same three-line ``have`` also
     pins the spec's existential ``cs`` to that list, so the refutation is
     stated against the unique arrangement the spec admits, not against an
     arbitrary one.
  2. ``decide`` gets stuck on ``Rat`` arithmetic (it reduces the ``Decidable``
     instance rather than computing, and reduction halts inside ``Rat.mul`` /
     ``Rat.blt``). ``norm_num`` closes the same goals. Hence every witness ends
     in ``norm_num [...]`` and every literal input is chosen so the
     ``Perm``/``Sorted`` side conditions land on integer-valued ``Rat`` literals
     that ``decide`` CAN settle.

No witness binds a hypothesis: every refutation is stated at literal inputs, so
there are no assumptions that could be jointly unsatisfiable and the gate's
consistency probe is not even applicable (``consistency_probe`` returns ``None``
for all twelve). ``sorry``/``admit``/``native_decide`` are banned and unused; no
witness references a name the variant declares and the frozen solution does not.

AUDIT NOTE (independent re-derivation, all builds re-run against the real
verifier). Each of the twelve witnesses was rebuilt BOTH ways: it elaborates
against its rival (exit 0) and fails against the frozen solution (exit 1). Every
gold-side failure was read. Eleven are SEMANTIC in the same way — the rival's
boundary list reduces, the spec's demanded list reduces, ``he`` collapses to
``True`` and the residual goal is an unprovable ``False``; the twelfth
(``weak-nonterminating``) is semantic in a different way, failing on gold with
gold's own two boundary lists reduced and exhibited as unequal
(``⊢ 1 :: ([] ++ [20]) = 0 :: ([(0 + 2) / 2, (2 + 4) / 2] ++ [10])``), which is
exactly the claim's content for an argument-independent body. None is a missing
identifier, a stuck ``decide`` or a timeout. That twelfth gold-side failure USED
to be a term-mode ``Type mismatch … rfl … ?m = ?m``, which a later reducibility
audit measured to be claim-INDEPENDENT (see the DIVERGENCE paragraph above) and
which is why the witness now proves its identification step by evaluation.

Because none of those gold-side errors is a plain evaluation, each was put
through the FORGERY test rather than judged by reading: for every one of the
twelve, a second file differing from the witness ONLY in what it CLAIMS (the
``¬`` dropped, so it asserts the spec HOLDS at that input) was built against both
subjects. All twelve invert cleanly — the flipped claim elaborates against the
frozen solution (exit 0) and FAILS against the rival (exit 1) — so gold's exit
code carries information about the claim and not merely about the file's shape.
The same conclusion was reached a second way for the eleven arithmetic witnesses
by replacing the closing step with a deliberate type error on ``he``: on gold
Lean reports ``he has type True``, i.e. ``norm_num`` PROVED the spec's equation
there, while on each rival the same file reports ``No goals to be solved``,
i.e. ``norm_num`` had already derived ``False``. That pair is a genuine
refutation rather than a coincidence of error text.

The audit additionally established, as a machine-checked ``example`` over
UNIVERSALLY quantified inputs rather than at literals, that C0 ∧ C1 ∧ C2 pin the
result UNIQUELY:

    ∀ lo hi cs r, problem_spec_binEdges lo hi cs r →
      r = lo :: (midpoints (cs.mergeSort (· ≤ ·)) ++ [hi])

That elaborates (exit 0), which settles the SPEC-TOO-WEAK question at the root
rather than one rival at a time: the spec admits exactly one result per input, so
no wrong implementation of the modeled behavior can satisfy it at all, and the
rival lane can only ever be about which wrong shapes are worth exhibiting. The
mirror direction was probed too — two further CORRECT reshapes not shipped here
(order-normalizing via the opposite comparator and reversing, and forming the
interior by a pairwise zip against the tail instead of the ``midpoints`` fold)
were each re-proved and verify, so the spec is not too strong on shape either.

AXIOM lane: DROPPED. The nagini sibling's ``AXIOM_TESTS`` (soundness and
caller-domain containment for its ``@ContractOnly`` ordering stub) belong to
G-AX, not to this gate. They are moot here besides: this bundle consumes NO
axiom — the ordering is modeled deeply in the implementation and discharged from
Mathlib lemmas — so there is no axiom to probe.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13135"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two anchors. Each lies ENTIRELY inside the region it names and is unique
# in the frozen file, so the manifest breaks loudly (AssertionError at import)
# if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The frozen impl-region BODY (the `do` block, marker lines and the `def`/
# `Id.run do` header EXCLUDED so a variant may also restate the header).
_IMPL_BODY = (
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: (midpoints cs ++ [colMax])\n"
)

# The whole impl region including its header, for the variants that change shape.
_IMPL_FULL = (
    "def implementation_binEdges (colMin colMax : Rat) (centers : List Rat) : List Rat :=\n"
    "  Id.run do\n" + _IMPL_BODY
)

# The frozen tactic BODY of `theorem correct_binEdges` (the statement itself is
# never touched — only what follows `:= by`).
_PROOF_BODY = (
    "  intro colMin colMax centers\n"
    "  refine ⟨centers.mergeSort (· ≤ ·), ?_, ?_, ?_⟩\n"
    "  · exact List.mergeSort_perm centers _\n"
    "  · have h := List.sorted_mergeSort (le := (fun a b : Rat => decide (a ≤ b)))\n"
    "      (by intro a b c; simp only [decide_eq_true_eq]; exact le_trans)\n"
    "      (by intro a b; simp only [Bool.or_eq_true, decide_eq_true_eq]; exact le_total a b) centers\n"
    "    simpa using h\n"
    "  · rfl"
)


def _rival(body):
    """A variant whose impl-region body is replaced; proof region untouched."""
    return _swap(_BASE, _IMPL_BODY, body)


# ---------------------------------------------------------------------------
# WITNESS TEMPLATE
#
# `hsm`/`hms` establish the ascending arrangement of the literal centers as an
# equation (the ordering operation does not reduce under decide/rfl/simp, so it
# is derived from permutation + sortedness + antisymmetry instead). `hcs` pins
# the spec's existential witness to that SAME list, which is forced because a
# sorted permutation of a given list is unique up to equality. What remains is a
# closed arithmetic disagreement between the rival's boundary list and the one
# the spec demands, which `norm_num` settles (`decide` cannot: it reduces the
# Decidable instance rather than computing, and halts inside `Rat.mul`).
# ---------------------------------------------------------------------------
def _witness(note, lo, hi, centers, ascending, extra_haves=(),
             extra_simp=()):
    haves = "".join(extra_haves)
    simp = "".join(", " + s for s in extra_simp)
    return (
        f"{note}"
        f"example : ¬ problem_spec_binEdges {lo} {hi} {centers}\n"
        f"    (implementation_binEdges {lo} {hi} {centers}) := by\n"
        f"  have hsm : List.Sorted (α := ℚ) (· ≤ ·) (({centers} : List Rat).mergeSort (· ≤ ·)) := by\n"
        "    have h := List.sorted_mergeSort (le := (fun a b : Rat => decide (a ≤ b)))\n"
        "      (by intro a b c; simp only [decide_eq_true_eq]; exact le_trans)\n"
        "      (by intro a b; simp only [Bool.or_eq_true, decide_eq_true_eq]; exact le_total a b)\n"
        f"      {centers}\n"
        "    simpa using h\n"
        f"  have hms : ({centers} : List Rat).mergeSort (· ≤ ·) = {ascending} :=\n"
        "    List.eq_of_perm_of_sorted ((List.mergeSort_perm _ _).trans (by decide)) hsm (by decide)\n"
        f"{haves}"
        "  rintro ⟨cs, hp, hs, he⟩\n"
        f"  have hcs : cs = {ascending} :=\n"
        "    List.eq_of_perm_of_sorted (hp.trans (by decide)) hs (by decide)\n"
        "  subst hcs\n"
        f"  norm_num [implementation_binEdges, midpoints, Id.run, pure, hms{simp}] at he\n"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
#
# Each is a structurally DIFFERENT but CORRECT implementation, re-proved
# honestly inside the proof region with the `theorem correct_binEdges`
# STATEMENT byte-identical. None weakens the obligation, adds a helper lemma,
# or reaches for sorry/admit/native_decide. A rejection of any of these is
# SPEC-TOO-STRONG.
# ===========================================================================

# Ports the nagini sibling's "reorder the computation" positive: a DIFFERENT
# order-normalizing operation (an insertion-style ordering rather than a
# merge-style one) and a different bracketing shape (cons-then-append rather
# than append-inside-cons). The proof changes accordingly: the two side goals
# are discharged from that operation's own permutation and sortedness lemmas,
# which are single-step, so no new induction is needed.
_POS_INSERTION = _swap(
    _swap(_BASE, _IMPL_BODY,
          "    let mut cs := centers\n"
          "    cs := cs.insertionSort (· ≤ ·)\n"
          "    return (colMin :: midpoints cs) ++ [colMax]\n"),
    _PROOF_BODY,
    "  intro colMin colMax centers\n"
    "  refine ⟨centers.insertionSort (· ≤ ·), ?_, ?_, ?_⟩\n"
    "  · exact List.perm_insertionSort _ _\n"
    "  · exact List.sorted_insertionSort _ _\n"
    "  · rfl")

# A correct implementation that PRE-PERMUTES the centers before normalizing
# their order. Order-normalization is invariant under an input permutation, so
# the result is unchanged; the permutation side goal now needs one extra
# transitivity step. This is the sharpest positive control in the battery: it
# proves the spec does not accidentally pin the INPUT order (which would make it
# too strong, since a clustering routine emits its outputs in no particular
# order), while `weak-no-normalization` proves it does pin the OUTPUT order.
_POS_PREREVERSE = _swap(
    _swap(_BASE, _IMPL_BODY,
          "    let mut cs := centers.reverse\n"
          "    cs := cs.mergeSort (· ≤ ·)\n"
          "    return colMin :: (midpoints cs ++ [colMax])\n"),
    _PROOF_BODY,
    "  intro colMin colMax centers\n"
    "  refine ⟨centers.reverse.mergeSort (· ≤ ·), ?_, ?_, ?_⟩\n"
    "  · exact (List.mergeSort_perm centers.reverse _).trans (List.reverse_perm centers)\n"
    "  · have h := List.sorted_mergeSort (le := (fun a b : Rat => decide (a ≤ b)))\n"
    "      (by intro a b c; simp only [decide_eq_true_eq]; exact le_trans)\n"
    "      (by intro a b; simp only [Bool.or_eq_true, decide_eq_true_eq]; exact le_total a b)\n"
    "      centers.reverse\n"
    "    simpa using h\n"
    "  · rfl")

# Ports the nagini sibling's "build the result a different way" positive: drop
# the mutable-local/do-block shape entirely for a plain functional definition
# with an explicit `List.cons`. Same value, different executable shape; the
# frozen proof body still closes it unchanged, which is itself informative (the
# obligation is about the VALUE, not the shape).
_POS_FUNCTIONAL = _swap(
    _BASE, _IMPL_FULL,
    "def implementation_binEdges (colMin colMax : Rat) (centers : List Rat) : List Rat :=\n"
    "  let cs := centers.mergeSort (fun a b => decide (a ≤ b))\n"
    "  List.cons colMin (midpoints cs ++ [colMax])\n")

# ADMISSIBILITY. Ports the nagini sibling's "the precondition admits a normal
# reported-shape input and is non-vacuous" case. This bundle's obligation is
# unconditional (there is no precondition hypothesis to admit anything), so the
# analogous question is whether the predicate is INHABITED at a reported-shape
# input — five interior values in arbitrary order inside the column range —
# rather than satisfiable only degenerately. The gold implementation and the
# gold proof are kept verbatim and an `example` exhibiting an explicit
# inhabitant is added inside the proof region. If the predicate could not be
# inhabited at such an input, the obligation would be discharged over a domain
# that does not include the case the behavior exists to handle.
_ADMISS = _swap(
    _BASE, _PROOF_BODY,
    _PROOF_BODY + "\n"
    "\n"
    "/-- Non-vacuity of the specification at a reported-shape input: five\n"
    "interior values in arbitrary order inside the column range, and an\n"
    "explicitly written boundary list. The predicate is inhabited there, so the\n"
    "obligation is not discharged over a domain that excludes the case the\n"
    "modeled behavior exists to handle. -/\n"
    "example : problem_spec_binEdges 0 10 [3, 0, 9, 2, 1]\n"
    "    [0, 1/2, 3/2, 5/2, 6, 10] := by\n"
    "  refine ⟨[0, 1, 2, 3, 9], by decide, by decide, by norm_num [midpoints]⟩")


# ===========================================================================
# RIVALS (uniqueness) — must be REJECTED, each with a witness seen to
# discriminate (holds of the rival, fails on the frozen solution).
# ===========================================================================

# C1 SORTED. THE pre-existing behavior: form the boundaries from the centers in
# whatever order they arrived, with no order normalization at all.
_W_NO_NORM = _rival(
    "    let mut cs := centers\n"
    "    return colMin :: (midpoints cs ++ [colMax])\n")

# C1 SORTED. Normalize the order, then report the OPPOSITE orientation.
_W_DESCENDING = _rival(
    "    let mut cs := centers\n"
    "    cs := (cs.mergeSort (· ≤ ·)).reverse\n"
    "    return colMin :: (midpoints cs ++ [colMax])\n")

# C0 PERM. Collapse coincident centers before forming the boundaries, so the
# arrangement the boundaries come from is a strict sub-multiset of the input and
# one interior boundary disappears. Correct on inputs with no repeats; refuted
# wherever a value repeats. Has NO nagini counterpart (see `assessment`).
_W_COLLAPSE = _rival(
    "    let mut cs := centers\n"
    "    cs := (cs.mergeSort (· ≤ ·)).eraseDups\n"
    "    return colMin :: (midpoints cs ++ [colMax])\n")

# C2 SHAPE (brackets). Order-normalize and form every interior boundary
# correctly, but close the list with the two column bounds SWAPPED.
_W_ENDPOINT_SWAP = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMax :: (midpoints cs ++ [colMin])\n")

# C2 SHAPE (brackets). Bracket with the extremes of the CENTERS instead of the
# column bounds. Agrees with the frozen behavior exactly when the smallest and
# largest centers coincide with the column bounds; refuted otherwise. Attacks
# the `colMin`/`colMax` binders specifically.
_W_SELF_BRACKET = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return (cs.headD colMin) :: (midpoints cs ++ [cs.getLastD colMax])\n")

# C2 SHAPE (length). One interior boundary short.
_W_SHORT = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: ((midpoints cs).dropLast ++ [colMax])\n")

# C2 SHAPE (interior values). A degenerate constant interior: as many copies of
# the column minimum as there are interior boundaries. Trivially non-decreasing
# and correct in length and brackets, so it satisfies every structural property
# short of the actual values. This is the case that shows C2's VALUE content is
# load-bearing beyond the monotonicity property a reader might mistake it for.
_W_FLAT = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: (List.replicate (midpoints cs).length colMin ++ [colMax])\n")

# C2 SHAPE (pairing). Order-normalize correctly, but average every element with
# the SMALLEST one rather than with its immediate predecessor. Agrees with the
# frozen behavior on two centers (where the predecessor IS the smallest);
# refuted from three centers on.
_W_HEAD_PAIRED = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: ((cs.drop 1).map (fun x => ((cs.headD 0) + x) / 2) ++ [colMax])\n")

# C2 SHAPE (pairing, near-miss). Order-normalize for every interior boundary
# except the LAST, which is formed from the raw trailing pair of the input.
# Agrees with the frozen behavior on every already-ascending input — the widest
# agreement domain of any rival here — so it gets its own witness at an input
# whose trailing pair is not the two largest.
_W_RAW_TRAILING = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: ((midpoints cs).dropLast\n"
    "      ++ midpoints (centers.drop (centers.length - 2)) ++ [colMax])\n")

# C2 SHAPE (interior values, scale). Order-normalize and pair adjacently, but
# average with the wrong weight — the sum is not halved. Length, brackets and
# pairing are all correct, so this isolates the arithmetic of a single
# boundary. Agrees with the frozen behavior only where every adjacent sum is
# zero.
_W_UNHALVED = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: ((midpoints cs).map (fun x => 2 * x) ++ [colMax])\n")

# C2 SHAPE (interior values, FRACTIONAL part). Order-normalize, pair adjacently
# and halve — then discard each interior boundary's fractional part. Added by the
# AUDIT, not by the port: every one of the ten witnesses above happens to sit at
# centers whose adjacent sums are EVEN, so each required interior boundary is
# integer-valued there and this rival agrees with the frozen behavior at ALL TEN
# of them. It is refuted only at an odd adjacent sum, so it is the narrowest
# partial-domain rival in the battery and the only case whose witness exercises
# the halving at a genuinely non-integer value.
_W_FLOOR = _rival(
    "    let mut cs := centers\n"
    "    cs := cs.mergeSort (· ≤ ·)\n"
    "    return colMin :: ((midpoints cs).map (fun x => ((⌊x⌋ : Int) : Rat))\n"
    "      ++ [colMax])\n")


# DIVERGENCE. A non-terminating implementation: the boundary list is replaced by
# an unbounded self-recursion, written `partial` because that is the ONLY diverging
# spelling this carrier's elaborator accepts (a plain `def` is refused by the
# termination checker, which is what the port mistook for the class being vacuous).
# Added by the AUDIT. Its witness cannot evaluate the rival's result — a `partial
# def` does not reduce — so it refutes by ARGUMENT-INDEPENDENCE instead: the body
# mentions none of the three binders, so a single value would have to satisfy the
# spec at two inputs that demand different results.
_W_NONTERM = _swap(
    _BASE, _IMPL_FULL,
    "partial def spinForever (n : Nat) : List Rat := spinForever (n + 1)\n"
    "\n"
    "def implementation_binEdges (colMin colMax : Rat) (centers : List Rat) : List Rat :=\n"
    "  spinForever 0\n")

def _mergesort_have(name, centers, ascending):
    """`hms<name>`: the literal centers' ascending arrangement, as an equation.

    Same derivation as the `_witness` template (permutation + sortedness +
    antisymmetry, because the ordering operation does not reduce), with the
    sortedness step NESTED inside the `have` so it does not enter the outer
    context. That keeps the goal state gold prints when the identification step
    fails short enough to survive the gate's signature cap, which is the whole
    evidence this case rests on.
    """
    return (
        f"  have hms{name} : ({centers} : List Rat).mergeSort (· ≤ ·) = {ascending} := by\n"
        f"    have hsm : List.Sorted (α := ℚ) (· ≤ ·) (({centers} : List Rat).mergeSort (· ≤ ·)) := by\n"
        "      have h := List.sorted_mergeSort (le := (fun a b : Rat => decide (a ≤ b)))\n"
        "        (by intro a b c; simp only [decide_eq_true_eq]; exact le_trans)\n"
        "        (by intro a b; simp only [Bool.or_eq_true, decide_eq_true_eq]; exact le_total a b)\n"
        f"        {centers}\n"
        "      simpa using h\n"
        "    exact List.eq_of_perm_of_sorted ((List.mergeSort_perm _ _).trans (by decide))\n"
        "      hsm (by decide)\n"
    )


# The divergence witness. Stated at literal inputs (so `consistency_probe`
# returns None, as for the other eleven), but its refutation is structural rather
# than arithmetic: the rival's results at two DIFFERENT inputs are IDENTIFIED,
# which holds only because the body ignores its arguments, and the spec then
# forces two incompatible values for the same term.
#
# The identification is proved by EVALUATION (`simp only` through
# `implementation_binEdges`/`Id.run`/`pure`/`midpoints` with the two pinned
# `mergeSort` equations), not by `rfl`. That is not a style choice: a term-mode
# `rfl` fails on gold with `?m = ?m` against the expected type for ANY claim at
# these points -- including `implementation_binEdges 0 10 [0, 4, 2] =
# [0, 1, 3, 10]`, which `#eval` shows is TRUE of gold -- because `mergeSort` and
# `Rat` division are irreducible at default transparency, so its exit code
# discriminates nothing. Under the evaluating tactic gold instead fails with its
# own two boundary lists reduced and different
# (`1 :: ([] ++ [20]) = 0 :: ([(0 + 2) / 2, (2 + 4) / 2] ++ [10])`), while the
# rival's opaque `spinForever 0` makes both sides the same term and the step
# closes. Measured both ways, plus the opposite claim under the identical tactic:
# gold 0 / rival 1 on gold's own reducts.
_WITNESS_NONTERM = (
    "-- The implementation ignores every argument, so its single value would have\n"
    "-- to be a correct boundary list at TWO inputs demanding different ones. The\n"
    "-- ascending arrangements are pinned as `have`s exactly as in the other\n"
    "-- witnesses; the contradiction is then closed by IDENTIFYING the two results,\n"
    "-- which holds only for an argument-independent body.\n"
    "--\n"
    "-- `hval` is proved by EVALUATION, not by `rfl`. A term-mode `rfl` fails on the\n"
    "-- frozen solution with `?m = ?m` against the expected type no matter WHAT is\n"
    "-- claimed at these points (the true-of-gold `implementation_binEdges 0 10\n"
    "-- [0, 4, 2] = [0, 1, 3, 10]` fails byte-identically), because `mergeSort` and\n"
    "-- `Rat` division do not reduce at default transparency -- so `rfl` here would\n"
    "-- attest nothing. `simp only` through the `Id.run`/`do` carrier with the two\n"
    "-- pinned `mergeSort` equations DOES reduce both applications: the frozen\n"
    "-- solution then fails with its own two boundary lists exhibited and unequal,\n"
    "--   ⊢ 1 :: ([] ++ [20]) = 0 :: ([(0 + 2) / 2, (2 + 4) / 2] ++ [10])\n"
    "-- while for the rival both sides are the same opaque `spinForever 0`.\n"
    "example : ¬ (problem_spec_binEdges 0 10 [0, 4, 2]\n"
    "      (implementation_binEdges 0 10 [0, 4, 2])\n"
    "    ∧ problem_spec_binEdges 1 20 [5] (implementation_binEdges 1 20 [5])) := by\n"
    + _mergesort_have("3", "[0, 4, 2]", "[0, 2, 4]")
    + _mergesort_have("1", "[5]", "[5]")
    + "  have hval : implementation_binEdges 1 20 [5]\n"
      "      = implementation_binEdges 0 10 [0, 4, 2] := by\n"
      "    simp only [implementation_binEdges, Id.run, pure, hms3, hms1, midpoints]\n"
      "  rintro ⟨⟨cs, hp, hs, he⟩, ⟨ds, hq, ht, hf⟩⟩\n"
      "  have hcs : cs = [0, 2, 4] :=\n"
      "    List.eq_of_perm_of_sorted (hp.trans (by decide)) hs (by decide)\n"
      "  have hds : ds = [5] :=\n"
      "    List.eq_of_perm_of_sorted (hq.trans (by decide)) ht (by decide)\n"
      "  subst hcs; subst hds\n"
      "  rw [hval, he] at hf\n"
      "  norm_num [midpoints] at hf\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS — a correct implementation of the modeled behavior
    # must verify, or the specification is TOO STRONG.
    # =====================================================================
    {
        "id": "pos-insertion-ordering",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INSERTION,
        "rationale": "structurally-different CORRECT implementation: a different "
        "order-normalizing operation (insertion-style rather than merge-style) and a "
        "different bracketing shape (cons-then-append rather than append-inside-cons). "
        "Ports the nagini sibling's 'reorder the computation' positive onto this "
        "carrier. Re-proved honestly: the C0/C1 side goals come from that operation's "
        "own permutation and sortedness lemmas (single-step, no new induction), C2 by "
        "`rfl`; the `theorem correct_binEdges` statement is byte-identical and no "
        "helper lemma is added. Must verify; a rejection is SPEC-TOO-STRONG — it would "
        "mean the spec pins the particular ordering operation rather than the ordering.",
    },
    {
        "id": "pos-prepermuted-input",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PREREVERSE,
        "rationale": "CORRECT implementation that permutes the centers before "
        "normalizing their order. Order-normalization is invariant under an input "
        "permutation, so the boundary list is unchanged; the C0 goal needs one extra "
        "transitivity step, which the re-proof supplies. This is the sharpest positive "
        "in the battery: it establishes that the spec does NOT pin the input order — "
        "which would be too strong, since the centers arrive in no particular order — "
        "while `weak-no-normalization` establishes that it DOES pin the order the "
        "boundaries are derived in. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-functional-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNCTIONAL,
        "rationale": "CORRECT implementation with the mutable-local/do-block shape "
        "dropped for a plain functional definition with an explicit list "
        "constructor. Ports the nagini sibling's 'build the result a different way' "
        "positive. Same value, different executable shape, and the frozen proof body "
        "closes it unchanged — which is itself informative: the obligation is about the "
        "VALUE produced, not the shape that produces it. Must verify; else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-reported-shape-inhabited",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "non-vacuity. Ports the nagini sibling's admissibility case, "
        "re-aimed: this obligation is unconditional (no precondition hypothesis), so "
        "the analogous question is whether the predicate is INHABITED at a "
        "reported-shape input rather than satisfiable only degenerately. Keeps the "
        "frozen implementation and proof verbatim and adds an `example` exhibiting an "
        "explicit inhabitant at five interior values in arbitrary order inside the "
        "column range — the very configuration the modeled behavior exists to handle. "
        "If that example could not be closed, the obligation would be discharged over "
        "a domain excluding the interesting case. Must verify.",
    },

    # =====================================================================
    # RIVALS — each is a WRONG implementation of the modeled behavior that
    # shares the frozen spec. Each ships a witness that was run BOTH ways:
    # it holds of the rival and FAILS on the frozen solution, so the
    # rejection is attributable to the spec and not to the frozen tactic
    # script failing to match a reshaped body.
    # =====================================================================
    {
        "id": "weak-no-normalization",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_NO_NORM,
        "rationale": "rejected by C1 (SORTED): the boundaries are derived from the "
        "centers in the order they arrived, so no ascending arrangement can witness "
        "the existential unless the input already happened to be ascending. C2 fails "
        "with it, since the interior values are then the midpoints of the wrong pairs. "
        "This is the pre-existing behavior and the case the whole battery is built "
        "around; a verify here is SPEC-TOO-WEAK.",
        "refinement": "its faithful real patch omits the order normalization of the "
        "cluster centers entirely, forming the interior boundaries directly from the "
        "centers as the clustering routine emitted them. On the reported input the "
        "centers come out in non-ascending order, so the boundary list is not "
        "monotone, the downstream digitization step raises rather than returning bin "
        "indices, and the F2P assertion is never reached. Does NOT resolve. (This is "
        "exactly the shape the bundle's prepatch solution carries, which G-DIFF "
        "records as failing.)",
        "witness": _witness(
            "-- Three centers in non-ascending order. The spec's existential is\n"
            "-- forced to the ascending arrangement, whose adjacent midpoints differ\n"
            "-- from the midpoints of the raw arrival order; the rival produces the\n"
            "-- latter, so no witness for the existential exists at this input.\n",
            "0", "10", "[0, 4, 2]", "[0, 2, 4]"),
    },
    {
        "id": "weak-descending",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_DESCENDING,
        "rationale": "rejected by C1 (SORTED) together with C2 (SHAPE): the "
        "arrangement the boundaries come from is a permutation of the centers but is "
        "DESCENDING, so the only arrangement the spec admits (the ascending one) "
        "yields a different interior sequence. A verify here would mean the spec pins "
        "the arrangement only up to permutation and not its ORIENTATION "
        "(SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch normalizes the order of the centers "
        "and then reverses them, emitting a boundary list that decreases instead of "
        "increases. The downstream digitization step is fed an ascending-expected "
        "edge sequence, so every value is assigned to the wrong interval and the "
        "resulting index vector is not the one the F2P test asserts. Does NOT "
        "resolve.",
        "witness": _witness(
            "-- Three ASCENDING centers, so the input order is already the one the\n"
            "-- spec admits and only the reported orientation can differ. The rival's\n"
            "-- interior sequence is the reverse of the required one, which for three\n"
            "-- distinct centers is a different list.\n",
            "1", "9", "[1, 5, 9]", "[1, 5, 9]"),
    },
    {
        "id": "weak-collapse-repeats",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_COLLAPSE,
        "rationale": "rejected by C0 (PERM): coincident centers are collapsed before "
        "the boundaries are formed, so the arrangement they come from is a strict "
        "sub-multiset of the input rather than a permutation of it, and one interior "
        "boundary is missing. C0 is the ONLY clause this attacks, and this is the only "
        "rival that attacks it — a verify here would mean the spec constrains the "
        "arrangement's ORDER but not its CONTENT (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch de-duplicates the cluster centers "
        "before forming the boundaries. Whenever two centers coincide — which is "
        "precisely what happens when the requested number of intervals approaches the "
        "number of distinct values, the configuration the report describes — the "
        "boundary sequence comes out one edge short, so the number of intervals no "
        "longer matches the number requested and the index vector the F2P test "
        "asserts is the wrong width. Does NOT resolve.",
        "witness": _witness(
            "-- A repeated center. The spec's arrangement must keep BOTH copies, so\n"
            "-- its interior sequence has two entries; the rival keeps one copy and\n"
            "-- produces a single interior entry. `eraseDups` does not reduce under\n"
            "-- norm_num either, so its value at this literal is supplied as a `have`.\n",
            "2", "6", "[2, 2, 6]", "[2, 2, 6]",
            extra_haves=(
                "  have hed : ([2, 2, 6] : List Rat).eraseDups = [2, 6] := by rfl\n",),
            extra_simp=("hed",)),
    },
    {
        "id": "weak-endpoint-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_ENDPOINT_SWAP,
        "rationale": "rejected by C2 (SHAPE), bracket positions: the arrangement and "
        "every interior boundary are correct, but the list opens with the column "
        "MAXIMUM and closes with the column MINIMUM. Attacks the `colMin`/`colMax` "
        "binders directly. A verify here would mean the spec does not pin which "
        "column bound brackets which end (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch brackets the (correctly ordered) "
        "interior boundaries with the two column bounds in the wrong positions. The "
        "boundary sequence then starts above and ends below its own interior values, "
        "so it is not monotone, the downstream digitization step raises, and the F2P "
        "assertion is never reached. Does NOT resolve.",
        "witness": _witness(
            "-- Two ascending centers strictly inside the column range, so the single\n"
            "-- interior boundary is correct in the rival too and only the brackets\n"
            "-- can differ. Both bounds are distinct from each other and from the\n"
            "-- interior value, so the swap is observable.\n",
            "2", "8", "[3, 5]", "[3, 5]"),
    },
    {
        "id": "weak-self-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_SELF_BRACKET,
        "rationale": "rejected by C2 (SHAPE), bracket values: the list is bracketed by "
        "the smallest and largest CENTERS instead of by the column bounds. Agrees with "
        "the frozen behavior exactly when those coincide, so it is a partial-domain "
        "rival, and it is the second case pinning the `colMin`/`colMax` binders — "
        "without it, no witness would demonstrate that either bracket binder is read "
        "at all rather than merely carried. A verify here would mean the spec leaves "
        "the bracket VALUES unconstrained (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch brackets the interior boundaries with "
        "the extreme cluster centers rather than with the column's own minimum and "
        "maximum. The outermost intervals then exclude the column's extreme values, so "
        "those values are assigned to intervals outside the requested range and the "
        "index vector the F2P test asserts differs at its endpoints. Does NOT resolve.",
        "witness": _witness(
            "-- Two centers strictly inside the column range, so both brackets differ\n"
            "-- from the extreme centers and the substitution is observable at both\n"
            "-- ends while the interior boundary itself is correct.\n",
            "0", "12", "[3, 9]", "[3, 9]"),
    },
    {
        "id": "weak-short-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_SHORT,
        "rationale": "rejected by C2 (SHAPE), length: one interior boundary is "
        "dropped, so the result cannot equal the required cons/append shape for ANY "
        "arrangement — the two lists differ in length. A verify here would mean the "
        "number of boundaries is unconstrained (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch emits one interior boundary fewer than "
        "the adjacent-pair count (an off-by-one in the slice that forms them). The "
        "boundary sequence is one edge short, so the number of intervals does not match "
        "the number requested and the index vector the F2P test asserts has the wrong "
        "width. Does NOT resolve.",
        "witness": _witness(
            "-- Three centers in arbitrary order: the required interior sequence has\n"
            "-- two entries, the rival's has one. A length mismatch, so no arrangement\n"
            "-- can witness the existential.\n",
            "0", "6", "[4, 0, 2]", "[0, 2, 4]"),
    },
    {
        "id": "weak-flat-interior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_FLAT,
        "rationale": "rejected by C2 (SHAPE), interior values: the interior entries "
        "are copies of the column minimum rather than the adjacent midpoints. Length, "
        "brackets and non-decreasingness ALL hold, so this is the case that "
        "establishes C2's value content is load-bearing beyond the weaker monotonicity "
        "property a reader might mistake it for — a spec that pinned only monotonicity "
        "would wrongly admit this. A verify here is SPEC-TOO-WEAK.",
        "refinement": "its faithful real patch emits a degenerate boundary sequence "
        "whose interior edges all equal the column minimum. It is trivially monotone, "
        "so the downstream digitization step does not raise — it silently assigns every "
        "value of the reported column to one and the same interval, and the resulting "
        "constant index vector is not the one the F2P test asserts. Does NOT resolve; "
        "note this rival would survive a monotonicity-only specification, which is "
        "precisely why it is here.",
        "witness": _witness(
            "-- Two ascending centers strictly above the column minimum, so the single\n"
            "-- required interior boundary is strictly greater than the constant the\n"
            "-- rival puts there. Length and brackets agree, isolating the values.\n",
            "0", "10", "[2, 4]", "[2, 4]"),
    },
    {
        "id": "weak-head-paired",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_HEAD_PAIRED,
        "rationale": "rejected by C2 (SHAPE), pairing: each interior boundary averages "
        "its element with the SMALLEST element rather than with its immediate "
        "predecessor. Length and brackets are correct and the arrangement is properly "
        "ordered, so this isolates WHICH pair each boundary comes from. Agrees with the "
        "frozen behavior on two centers (there the predecessor is the smallest), so it "
        "is a partial-domain rival, refuted from three on. A verify here would mean C2 "
        "does not pin adjacency (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch averages each center against the "
        "smallest center instead of against its neighbour (an indexing error that "
        "broadcasts one element rather than shifting the sequence by one). Every "
        "interior boundary but the first lands at the wrong value, so values near the "
        "true boundaries are assigned to the wrong intervals and the index vector "
        "diverges from the one the F2P test asserts. Does NOT resolve when there are "
        "three or more centers.",
        "witness": _witness(
            "-- Three ascending centers, needed because with two the rival coincides\n"
            "-- with the frozen behavior. The second interior boundary must average\n"
            "-- the middle and largest centers; the rival averages smallest and\n"
            "-- largest.\n",
            "1", "7", "[1, 3, 7]", "[1, 3, 7]"),
    },
    {
        "id": "weak-raw-trailing-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_RAW_TRAILING,
        "rationale": "rejected by C2 (SHAPE), pairing on a sub-domain: every interior "
        "boundary but the LAST comes from the ordered arrangement; the last comes from "
        "the raw trailing pair of the input. The widest agreement domain of any rival "
        "here — it matches the frozen behavior on EVERY already-ascending input — so it "
        "gets its own witness at an input whose trailing pair is not the two largest, "
        "rather than sharing one with a coarser rival. A verify here would mean C2 does "
        "not pin the last boundary to the ordered pair (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch reads the trailing pair of centers from "
        "a slice taken before the order normalization takes effect, so the final "
        "interior boundary is the midpoint of whichever two centers happened to arrive "
        "last. On the reported input those are not the two largest, so the final "
        "boundary is wrong and can sit out of order relative to its neighbour — the "
        "downstream digitization step then either raises or misassigns, and the index "
        "vector the F2P test asserts is not produced. Does NOT resolve on the "
        "sub-domain where the raw trailing pair is not the two largest centers.",
        "witness": _witness(
            "-- The largest center arrives FIRST, so the raw trailing pair is the two\n"
            "-- SMALLEST centers, not the two largest. Chosen specifically to sit in\n"
            "-- this rival's disagreement sub-domain: on any ascending input it would\n"
            "-- agree with the frozen behavior and no refutation would exist.\n",
            "1", "5", "[5, 1, 3]", "[1, 3, 5]"),
    },
    {
        "id": "weak-unhalved-interior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_UNHALVED,
        "rationale": "rejected by C2 (SHAPE), interior arithmetic: the arrangement, "
        "the adjacency and the brackets are all correct, and each interior entry is "
        "formed from the RIGHT pair — but with the wrong weight, so it is the pair's "
        "sum rather than its midpoint. The narrowest attack in the battery: it changes "
        "one arithmetic operation and nothing else, agreeing with the frozen behavior "
        "only where every adjacent sum is zero. A verify here would mean C2 pins which "
        "elements each boundary depends on but not how (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch forms each interior boundary as the sum "
        "of two adjacent centers without halving it (a dropped scale factor). The "
        "boundaries are still increasing, so nothing raises; they simply sit at roughly "
        "twice their correct positions, so the reported column's values fall into "
        "lower-numbered intervals than they should and the index vector the F2P test "
        "asserts is not produced. Does NOT resolve.",
        "witness": _witness(
            "-- Three ascending centers with non-zero adjacent sums, so doubling each\n"
            "-- interior boundary is observable at both of them while length, brackets\n"
            "-- and pairing all agree with the frozen behavior.\n",
            "0", "8", "[1, 3, 5]", "[1, 3, 5]"),
    },
    {
        "id": "weak-truncated-interior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_FLOOR,
        "rationale": "rejected by C2 (SHAPE), interior values at a FRACTIONAL point: "
        "the arrangement, the adjacency, the brackets, the length and the halving are "
        "all correct, and each interior entry is then truncated to a whole number. "
        "Added by the AUDIT rather than by the port, to close a measured gap: the ten "
        "rivals above are all witnessed at centers whose adjacent sums are EVEN, so "
        "every required interior boundary is integer-valued at all ten points and this "
        "rival AGREES with the frozen behavior at each of them. It is therefore the "
        "narrowest partial-domain rival here, and its witness is the only one in the "
        "battery that exercises the halving where the quotient is not a whole number. "
        "A verify here would mean C2 pins each boundary's integer part but not its "
        "fractional part (SPEC-TOO-WEAK).",
        "refinement": "its faithful real patch forms each interior boundary by an "
        "integer-truncating division rather than an exact one, so every boundary is "
        "pulled down to the whole number below it. On any column whose adjacent "
        "centers sum to an odd value the boundary sits below its correct position, so "
        "values lying between the truncated and the true boundary are assigned to the "
        "next interval down and the index vector the F2P test asserts is not produced. "
        "The boundaries stay non-decreasing, so nothing raises and the divergence is "
        "silent. Does NOT resolve on the sub-domain where some adjacent pair of "
        "order-normalized centers has an odd sum.",
        "witness": _witness(
            "-- Two ascending centers whose adjacent sum is ODD, so the single required\n"
            "-- interior boundary is genuinely fractional (3/2) and the truncation is\n"
            "-- observable. Every other witness in this battery sits at an even\n"
            "-- adjacent sum, where this rival and the frozen behavior coincide.\n",
            "0", "4", "[1, 2]", "[1, 2]"),
    },
    {
        "id": "weak-nonterminating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_NONTERM,
        "rationale": "rejected because the obligation is discharged only for an "
        "implementation that actually PRODUCES a boundary list: the rival's body is "
        "an unbounded self-recursion, so it computes no result and satisfies none of "
        "C0/C1/C2 at any input. Added by the AUDIT, which measured the port's "
        "recorded reason for dropping this class ('a diverging implementation cannot "
        "be written') and found it false as stated — a plain `def` is refused by the "
        "termination checker, but a `partial def` elaborates and clears "
        "`variant_problems` with an empty list, so the rival is both expressible and "
        "in scope on this carrier. A verify here would mean the spec constrains the "
        "boundary list's VALUE without requiring that one be produced at all "
        "(SPEC-TOO-WEAK). Its witness identifies the rival's results at two inputs "
        "by EVALUATION rather than by `rfl`: `rfl` fails on the frozen solution for "
        "every claim at these points (`mergeSort` and `Rat` division are "
        "irreducible at default transparency, so even the true-of-gold value "
        "equation fails identically), while the evaluating step makes gold fail "
        "with its own two boundary lists reduced and unequal — the failure a "
        "reviewer can read as a refutation.",
        "refinement": "its faithful real patch fails to make progress while searching "
        "for the boundary positions — an update step that never moves its loop "
        "variable — so the fit call never returns for the reported column instead of "
        "returning a boundary list. The F2P assertion is never reached because the "
        "call does not terminate, rather than because the value it produces is wrong. "
        "Does NOT resolve.",
        "witness": _WITNESS_NONTERM,
    },
]

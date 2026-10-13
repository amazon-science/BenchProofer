"""properties.py — G-PBT falsification battery for sympy__sympy-19040 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
case is a full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte
(region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds by construction and the ``theorem correct_extFactor`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff the variant is in scope AND the
file elaborates with the obligation closed; ``expect:"reject"`` passes iff it is
in scope AND does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

DEFENDED SURFACE — ONE obligation:

    problem_spec_extFactor (f : ExPoly)
        (result : ExCoeff × List (ExPoly × Nat)) : Prop
      let lc := groundLC f
      let mono := groundMonic f
      result.1 = lc
      ∧ (degreesNonpos (degreeList mono) = true  → result.2 = [])
      ∧ (degreesNonpos (degreeList mono) = false →
          result.2 = trialDivision mono
            (recoverFactors (raiseShift (sqfNorm mono).1) (sqfNorm mono).2.1
              (factorListInclude (sqfNorm mono).2.2) (sqfPart mono)))

THREE INDEPENDENT top-level clauses, each attacked separately:

  * CLAUSE 1 — the coefficient component is the INPUT's ground leading
    coefficient, not the monic form's. Attacked by ``rival-lc-of-monic``.
  * CLAUSE 2 — the degenerate-degree case yields NO factors. Attacked by
    ``rival-no-degenerate-short-circuit``.
  * CLAUSE 3 — the load-bearing one, itself a composite of four independently
    abusable decisions:
      - WHICH POLYNOMIAL the square-free norm is taken of (``mono``, the full
        monic form). Attacked by ``rival-norm-of-square-free-part`` — this is
        the pre-patch routing ``Solution_prepatch.lean`` reverts to.
      - WHICH POLYNOMIAL the multiplicity recovery divides against (``mono``
        again, not the square-free part). Attacked by
        ``rival-divide-against-part``.
      - THE SINGLE-GROUND-FACTOR SELECTOR: the short-circuit fires exactly when
        the ground factor list has length one, and it yields the square-free
        part. Attacked by ``rival-always-short-circuit`` (fires always),
        ``rival-invert-length-guard`` (fires exactly when the length is NOT
        one), ``rival-fallback-is-monic`` (fires correctly but yields the wrong
        polynomial), ``rival-lone-arm-returns-traversal`` (fires correctly but
        yields the TRAVERSAL over the one-entry list, isolating the arm's value
        with every other decision left correct), ``rival-echo-input-as-factor``
        (fires correctly but yields the raw INPUT, no callee applied), and
        ``rival-drop-factor-component`` (the whole component is dropped).
      - THE RECOVERY TRAVERSAL covers EVERY ground factor, in order, threading
        the carrier. Attacked by ``rival-drop-last-ground-factor``.

  * TERMINATION — the impl must produce a value at all. Attacked by
    ``rival-nonterminating-constant``; see the divergence note below for why the
    class is shippable on this carrier and what witness shape it needs.

ADVERSARIAL READ of the nagini classes on this carrier. The nagini sibling is
the design document; see this cell's ``assessment`` for the per-case port
ledger.

  * FRAME / PERMISSION MUTATION — VACUOUS here, and vacuous in the nagini
    sibling too, which says so itself: its own defended-surface note records
    that neither input carries a fractional read-only permission, so there was
    no frame-mutation surface to attack even there. On this backend the class
    additionally cannot be expressed at all: Lean is referentially transparent,
    ``f`` is an immutable value, there is no aliasing and no half-permission to
    violate. No permission-violation substitute is fabricated. The SEMANTIC
    residue — "an input is not silently absorbed into the answer" — survives as
    the spec's pinning of each output component to a named function of ``f``,
    and that IS attacked (``rival-lc-of-monic`` puts a function of the wrong
    polynomial into the coefficient component; ``rival-fallback-is-monic`` puts
    the wrong polynomial into the factor component).
  * DIVERGENCE / NON-TERMINATION — the carrier is TOTAL (no
    ``loom.semantics.termination`` option is set; ``implementation_extFactor``
    is a plain Lean ``def``), so the verifier discharges termination and a
    diverging rival is genuinely REJECTED rather than vacuously accepted. This
    is NOT the velvet ``partial``-semantics spec hole in
    ``the corpus-wide termination-semantics finding``. The class is therefore
    SHIPPABLE, and it is shipped, as ``rival-nonterminating-constant``. An
    earlier reading of this battery recorded it as a KNOWN WITNESS-LANE HOLE on
    the strength of two shapes that genuinely cannot be witnessed; the hole was
    in those two shapes, not in the class, and a third shape closes it.
      - ``partial def implementation_extFactor f := implementation_extFactor f``
        is in variant scope and DOES fail the obligation (``Tactic `unfold`
        failed to unfold `implementation_extFactor```), but ``partial`` makes the
        impl an opaque constant, so the only available witness shape must
        HYPOTHESISE its value — and such a witness then holds of the frozen
        solution too (measured: rival exit 0, gold exit 0 => ``witness-vacuous``,
        not a refutation). Re-measured independently at audit with the narrowest
        available shape, a clause-1 witness assuming only
        ``(implementation_extFactor { val := 81 }).1 ≠ groundLC { val := 81 }``
        and closing by ``exact hlc hs.1``: rival exit 0, GOLD exit 0. The
        hypothesis is stated over ``implementation_extFactor`` itself, the one
        name the rival REPLACES, so on gold it is a hypothesis about gold's own
        (correct) impl and the same two-line script discharges the goal from it.
      - the well-founded shape with no decreasing measure
        (``implementation_extFactor { val := f.val + 1 }``) fails EARLIER, at
        ``fail to show termination for``, which breaks the witness file itself:
        even a trivial ``(1:Nat) + 1 = 2`` witness cannot elaborate against that
        rival (measured exit 1), so the rival build — the half that must SUCCEED
        — can never pass and the case would record ``witness-unproven``.
      - what BOTH of those lack, and what the shipped case has, is a diverging
        term gold and the rival SHARE. Put the divergence in a separate
        ``partial`` constant and route every input through it: the impl becomes a
        CONSTANT FUNCTION, and constancy is expressible over the shared
        vocabulary alone (``implementation_extFactor a = implementation_extFactor
        b := rfl``), with no hypothesis about the replaced name at all. Clause 1
        then refutes it at two inputs at once, since the coefficient component is
        pinned to ``groundLC f`` and cannot take one value at two points whose
        leading coefficients differ. Measured: rival exit 0, gold exit 1 (failing
        on the constancy step itself), consistency probe exit 1, and the opposite
        claim builds on gold while failing against the rival.
    The nagini sibling carries no ``diverge-*`` / ``nonterm-*`` case, so this
    direction is carrier-specific rather than a port.
  * UNGROUNDED-ORACLE ECHO — VACUOUS. Every algebra callee is ``opaque`` with
    NO constraining axiom, so there is no answer key to echo: the only way to
    produce a value equal to the clause-3 right-hand side is to route the same
    values through the same callees in the same order. The nagini sibling's
    ``weak-echo-*`` rivals were echoes of ITS uninterpreted ``factor_list`` /
    ``lone`` axioms, and their content ports as the selector attacks above
    (``rival-always-short-circuit`` is nagini's ``weak-echo-lone``;
    ``rival-invert-length-guard`` covers ``weak-echo-factorlist``). The literal
    input-echo, however, is NOT vacuous and is now landed in its own right as
    ``rival-echo-input-as-factor``: ``f`` and ``sqfPart (groundMonic f)`` are
    distinct opaque terms, so returning the input as its own factor is refutable
    here, and an earlier reading that folded it into
    ``rival-always-short-circuit`` understated the class.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script's ``rfl`` / ``split`` steps are
tuned to the frozen form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at one input; each was checked by two real builds to HOLD of its rival
and to FAIL on the frozen solution.

NO witness can ``decide``: the carrier is nine ``opaque`` callees over three
single-field identity structures with no constraining axiom, so nothing in
clause 3 computes at any literal input — ``decide`` gets stuck on
``sqfNorm (groundMonic { val := k })`` immediately. Every witness therefore
CONDITIONS on the carrier instead: it fixes the input structure to a literal,
assumes only which BRANCH the degenerate-degree test and the ground-factor-list
length selector take there, and assumes that the two answers being compared
differ. That is exactly the sub-domain where each rival is wrong — a carrier
that happened to make the two agree at that point would make the rival agree
with the spec there — and it is a strictly stronger claim than any single
literal input could make. Every hypothesis is about a DISTINCT opaque term, so
the assumptions are jointly satisfiable; the gate's ``False``-derivation probe
was run by hand against all of them and failed on all of them, as required.
``rival-nonterminating-constant`` is the one exception to the shape described in
this paragraph: it conditions on nothing about the selector at all, because its
rival produces no value on any input, and it states its refutation over the
IMPL's own constancy instead (see that case's ``rationale``).

Note the witnesses reach the clauses through the spec's own structure rather
than through arithmetic: clause 1 is projected with ``hs.1``, clause 2 with
``hs.2.1``, clause 3 with ``hs.2.2``, so each rival is refuted against the
clause its ``rationale`` names and not merely against the conjunction.

WHAT THE GOLD-SIDE FAILURE MUST BE, and how it was established. A witness that
fails on the frozen solution for a SYNTACTIC reason discriminates nothing, so
"gold's build exited 1" is not by itself evidence. The admissible evidence is a
type-revealing pair: replace the closing ``exact hdiff h3`` with a deliberate
type error on the hypothesis (``exact ((h3) : Nat)``) and build that on each
side. On gold each of the ELEVEN value-comparison reject cases prints
``h3 has type True`` —
``simp`` PROVED the spec's equation for the frozen impl at that point — while
against the rival the same probe prints the CONCRETE unproven equation
(e.g. ``trialDivision (groundMonic { val := 7 }) [sqfPart ...] = trialDivision
(groundMonic { val := 7 }) [(recoverOne ...).1, (recoverOne ...).1]``). That
asymmetry is the refutation, and it is why every witness here pins BOTH
selector branches concretely: four of these cases originally left one branch
abstract, so gold failed on an unreduced ``if _ then _ else forIn ..`` term
whose exit code carried no information about the claim, and the extra
``Nat.reduceAdd`` / ``reduceIte`` / ``List.forIn_cons`` / ``recoverLoop``
rewrites are what force the spec side to reduce on gold. Independently
cross-checked by asserting the OPPOSITE claim (that the frozen solution IS
correct at each witness's input, discharged by the frozen tactic body): that
builds on gold for all eleven inputs and fails against every rival, so gold's
exit code does track the claim. ``rival-nonterminating-constant`` carries the
same pair in its own idiom: the type-revealing probe on its constancy step
prints the concrete equation ``implementation_extFactor { val := 91 } =
implementation_extFactor { val := 93 }`` against the rival, where ``rfl`` closed
it, while on gold ``rfl`` cannot unify the two sides at all; and the opposite
claim (both points satisfy the spec, closed by the frozen tactic body) builds on
gold and fails against that rival.

BINDER COVERAGE. ``problem_spec_extFactor`` has exactly ONE input binder,
``f``, and it is varied across the reject witnesses: twelve distinct
carriers (``{ val := 3, 5, 7, 9, 21, 23, 27, 41, 43, 63, 67 }`` for the
value-comparison rivals plus ``{ val := 91 }`` / ``{ val := 93 }`` for
``rival-nonterminating-constant``, which is the only witness stating its
refutation at TWO inputs at once, since constancy is not observable at one), so
no two rivals are refuted at the same point; the admissibility positive adds
another (``{ val := 51 }``). Because ``f`` is an opaque identity
carrier, varying its literal alone would be cosmetic — what actually has to be
varied is the CONDITIONED sub-domain each witness pins around it, and that is
varied independently:
  * the degenerate-degree test — ``false`` (ten witnesses) and ``true``
    (``rival-no-degenerate-short-circuit``), so both arms of clause 2 / clause 3
    are probed and a rival mishandling only one arm is reachable;
  * the ground-factor-list length selector — length exactly one (six
    witnesses, the short-circuit arm), explicit one-element lists
    (``rival-invert-length-guard``, ``rival-lone-arm-returns-traversal``), and
    explicit TWO-element lists (``rival-always-short-circuit``,
    ``rival-drop-last-ground-factor``, ``rival-norm-of-square-free-part``, the
    recovery-loop arm), so both arms of the selector and the traversal itself
    are exercised. ``rival-norm-of-square-free-part`` is the one witness that
    pins the selector at DIFFERENT lengths on the two sides it compares — one
    ground factor for the norm of the PART, two for the norm of the MONIC form —
    which is the shape of the routing defect itself and is what makes both sides
    of its comparison reduce;
  * ground factor multiplicities ``1`` and ``2`` and distinct ground carriers
    (``{ val := 11, 13, 17, 31, 37, 71 }``) appear, so neither the traversal nor
    the per-entry projection ``entry.1`` is pinned to one shape.

ADMISSIBILITY lane: PRESENT (`admiss-f2p-two-ground-factors`). The carrier is
total and the obligation carries no precondition, so the class does NOT collapse
— its analogue here is the obligation being unsatisfiable at an F2P-shaped
input, which no uniqueness rival can detect (a rejection cannot distinguish "the
rival is wrong" from "this clause cannot be discharged at all"). The case
discharges the obligation at the F2P shape — the TWO-ground-factor traversal arm
— as a `have` before closing the frozen obligation verbatim.

SPEC-TOO-WEAK PROBES BEYOND THE RIVAL LANE. Eleven further wrong impls were
written and built against the frozen spec, aimed at decisions the shipped
rivals leave unattacked; ALL ELEVEN were rejected, so none is a spec hole and none
is shipped as a case (a rejected probe adds a build without adding a claim). For
the record of what has been probed: the recovery carrier not threaded between
steps (each step re-uses the initial carrier); the traversal run in reverse
order; the shift polynomial built from the norm of the PART's shift count while
everything else routes correctly; the degenerate-degree guard tested on the raw
INPUT's degree list rather than the monic form's; the selector's guard weakened
from ``= 1`` to ``≤ 1``; the degenerate arm returning the MONIC form's leading
coefficient (a clause-1 × clause-2 interaction the shipped clause-1 rival does
not reach, since it is wrong on the non-degenerate arm); the fallback taking the
square-free part of the INPUT rather than of the monic form; and the norm taken
of the doubly-monic form. The last two are the tightest near-misses available
here — ``sqfPart f`` vs ``sqfPart (groundMonic f)``, and ``groundMonic
(groundMonic f)`` vs ``groundMonic f`` — and the carrier keeps them distinct
(``groundMonic`` is opaque and carries no idempotence axiom), so the spec pins
even the doubly-applied form. Three more were added at audit and rejected too:
the recovery step's first two arguments transposed (``recoverOne gCur H entry.1``
— the shift polynomial and the gcd carrier are both ``ExPoly``, so this
type-checks and the spec still catches it); the shift polynomial built from
``s + 1``; and the traversal dropping the FIRST ground factor rather than the
last (``factors0.tail``, the mirror of ``rival-drop-last-ground-factor``).

SPEC-TOO-STRONG PROBES BEYOND THE POSITIVE LANE. Five further correct reshapes
were built, all of which VERIFY, so the spec admits every faithful shape tried.
The single-expression form (the whole answer as one tuple literal with the guard
as a term-level ``if``) is not shipped only because ``pos-functional-fold``
already occupies that direction. The non-monadic ``match`` form verifies too and
IS shipped, as ``pos-match-no-monad``, because it is the one correct shape
neither existing positive reaches. Three more were added at audit and verify
without being shipped: an impl-region helper doing its own front-recursion with
the equality to ``recoverLoop`` proved by induction inside the case (which shows
the spec does not require the frozen ``recoverLoop`` to be the impl's own
traversal, only its extension); a cons-accumulator loop reversed at the end (its
proof needs a different fold lemma, ``(recoverLoop ..).reverse ++ acc``, so it
tests that the spec is not tied to the append-accumulator's fold shape); and the
degenerate-arm split done by ``by_cases`` on the guard rather than by
``split_ifs``.

AXIOM lane: OMITTED. The nagini sibling's five ``AXIOM_TESTS`` belong to G-AX,
which this gate ignores. ``meta.json`` records ``axioms == []`` for this bundle
(every callee enters fully abstract; the proof consumes no callee property), so
there is no consumed-axiom obligation here in any case.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19040"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Every anchor below lies ENTIRELY inside the region it edits
# (the impl region for a rival, impl + proof for a positive that re-proves) and
# is unique in the frozen file — both asserted at load time by _swap, so this
# manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

_IMPL_HEAD = """def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
  let lc := groundLC f
  let mono := groundMonic f
"""

_IMPL_FULL = """def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
  let lc := groundLC f
  let mono := groundMonic f
  if degreesNonpos (degreeList mono) then
    return (lc, [])
  let fSqf := sqfPart mono
  let (s, g, r) := sqfNorm mono
  let factors0 := factorListInclude r
  let mut factors : List ExPoly := []
  if factors0.length = 1 then
    factors := [fSqf]
  else
    let H := raiseShift s
    let mut gCur := g
    for entry in factors0 do
      let (h, g') := recoverOne H gCur entry.1
      gCur := g'
      factors := factors ++ [h]
  return (lc, trialDivision mono factors)
"""

_PROOF_HEAD = """  intro f
  unfold problem_spec_extFactor implementation_extFactor
"""

_NORM_LINE = "  let (s, g, r) := sqfNorm mono\n"
_TRIAL_LINE = "  return (lc, trialDivision mono factors)\n"
_LEN_GUARD = "  if factors0.length = 1 then\n"
_FALLBACK = "    factors := [fSqf]\n"
_FOR_LINE = "    for entry in factors0 do\n"
_DEGEN = "  if degreesNonpos (degreeList mono) then\n    return (lc, [])\n"
_SELECT_BLOCK = """  let mut factors : List ExPoly := []
  if factors0.length = 1 then
    factors := [fSqf]
  else
    let H := raiseShift s
    let mut gCur := g
    for entry in factors0 do
      let (h, g') := recoverOne H gCur entry.1
      gCur := g'
      factors := factors ++ [h]
"""

# The frozen proof body, verbatim (the whole `-- proof-start` / `-- proof-end`
# interior). Only the positives touch it, and only to re-prove the SAME
# statement for a reshaped impl.
_PROOF_FULL = """  intro f
  unfold problem_spec_extFactor implementation_extFactor
  simp only [Id.run, bind, pure]
  refine ⟨by split_ifs <;> rfl, ?_, ?_⟩
  · intro h
    simp [h]
  · intro h
    rw [if_neg (by simp [h])]
    -- key: the forIn accumulates into recoverLoop
    have key : ∀ (H : ExPoly) (l : List (GrPoly × Nat)) (acc : List ExPoly) (g : ExPoly),
        (forIn (m := Id) l (⟨acc, g⟩ : MProd (List ExPoly) ExPoly) (fun entry r =>
          ForInStep.yield
            ⟨r.fst ++ [(recoverOne H r.snd entry.1).1],
              (recoverOne H r.snd entry.1).2⟩)).fst
          = acc ++ recoverLoop H g l := by
      intro H l
      induction l with
      | nil => intro acc g; simp [recoverLoop, pure]
      | cons hd tl ih =>
        intro acc g
        rw [List.forIn_cons]
        simp only [recoverLoop, bind, ih, List.append_assoc, List.singleton_append]
    unfold recoverFactors
    split_ifs with hlen
    · rfl
    · have hkey := key (raiseShift (sqfNorm (groundMonic f)).1)
        (factorListInclude (sqfNorm (groundMonic f)).2.2) [] (sqfNorm (groundMonic f)).2.1
      simp only [List.nil_append] at hkey
      split
      next factors gCur heq =>
        have : factors = recoverLoop (raiseShift (sqfNorm (groundMonic f)).1)
            (sqfNorm (groundMonic f)).2.1 (factorListInclude (sqfNorm (groundMonic f)).2.2) := by
          rw [← hkey, heq]
        rw [this]
"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (P1) Structurally different but CORRECT. Both branch tests are INVERTED: the
# degenerate-degree guard becomes `if !degenerate then <main body>` with the
# empty-factor return moved to a trailing fall-through (so the early return is
# gone and the main body is nested), and the selector becomes `if length ≠ 1
# then <recovery loop> else <short-circuit>` — its two arms swapped. The
# recovery loop also inlines the shift polynomial at its use site instead of
# binding it first, so there is one fewer local. Same routing, different control
# shape and a different number of return points. The obligation is re-proved for
# the new shape (`if_neg` becomes `if_pos`, and the swapped selector needs
# `ite_not` normalization before the loop-equals-fold step applies) with the
# STATEMENT byte-identical. If this failed to verify, the postcondition would be
# over-fit to one branch polarity / one return point => SPEC-TOO-STRONG.
_IMPL_P1 = """def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
  let lc := groundLC f
  let mono := groundMonic f
  if !degreesNonpos (degreeList mono) then
    let (s, g, r) := sqfNorm mono
    let factors0 := factorListInclude r
    let mut factors : List ExPoly := []
    if factors0.length ≠ 1 then
      let mut gCur := g
      for entry in factors0 do
        let (h, g') := recoverOne (raiseShift s) gCur entry.1
        gCur := g'
        factors := factors ++ [h]
    else
      factors := [sqfPart mono]
    return (lc, trialDivision mono factors)
  return (lc, [])
"""
_PROOF_P1 = """  intro f
  unfold problem_spec_extFactor implementation_extFactor
  simp only [Id.run, bind, pure]
  refine ⟨by split_ifs <;> rfl, ?_, ?_⟩
  · intro h
    simp [h]
  · intro h
    rw [if_pos (by simp [h])]
    have key : ∀ (H : ExPoly) (l : List (GrPoly × Nat)) (acc : List ExPoly) (g : ExPoly),
        (forIn (m := Id) l (⟨acc, g⟩ : MProd (List ExPoly) ExPoly) (fun entry r =>
          ForInStep.yield
            ⟨r.fst ++ [(recoverOne H r.snd entry.1).1],
              (recoverOne H r.snd entry.1).2⟩)).fst
          = acc ++ recoverLoop H g l := by
      intro H l
      induction l with
      | nil => intro acc g; simp [recoverLoop, pure]
      | cons hd tl ih =>
        intro acc g
        rw [List.forIn_cons]
        simp only [recoverLoop, bind, ih, List.append_assoc, List.singleton_append]
    unfold recoverFactors
    simp only [ne_eq, ite_not]
    split_ifs with hlen
    · rfl
    · have hkey := key (raiseShift (sqfNorm (groundMonic f)).1)
        (factorListInclude (sqfNorm (groundMonic f)).2.2) [] (sqfNorm (groundMonic f)).2.1
      simp only [List.nil_append] at hkey
      split
      next factors gCur heq =>
        have : factors = recoverLoop (raiseShift (sqfNorm (groundMonic f)).1)
            (sqfNorm (groundMonic f)).2.1 (factorListInclude (sqfNorm (groundMonic f)).2.2) := by
          rw [← hkey, heq]
        rw [this]
"""
_POS_INVERT_BRANCHES = _swap(_swap(_BASE, _IMPL_FULL, _IMPL_P1),
                             _PROOF_FULL, _PROOF_P1)

# (P2) Structurally different but CORRECT: the entire imperative selector — the
# mutable factor accumulator, the length branch, the mutable carrier and the
# `for` loop — is replaced by the purely functional shape, assembling the result
# in one expression. No mutable local, no loop, no early return past the
# degenerate case. Correct because the imperative loop and the front-recursive
# fold compute the same list, which is precisely the fact the frozen proof's
# inductive step establishes; this positive is the honest cheapest correct impl
# and its proof consequently drops that step entirely. If this failed to verify,
# the spec would be over-fit to the imperative accumulator form =>
# SPEC-TOO-STRONG.
_IMPL_P2 = """def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
  let lc := groundLC f
  let mono := groundMonic f
  if degreesNonpos (degreeList mono) then
    return (lc, [])
  let (s, g, r) := sqfNorm mono
  return (lc, trialDivision mono
    (recoverFactors (raiseShift s) g (factorListInclude r) (sqfPart mono)))
"""
_PROOF_P2 = """  intro f
  unfold problem_spec_extFactor implementation_extFactor
  simp only [Id.run, bind, pure]
  refine ⟨by split_ifs <;> rfl, ?_, ?_⟩
  · intro h
    simp [h]
  · intro h
    rw [if_neg (by simp [h])]
"""
_POS_FUNCTIONAL = _swap(_swap(_BASE, _IMPL_FULL, _IMPL_P2),
                        _PROOF_FULL, _PROOF_P2)

# (P3) ADMISSIBILITY. On a total carrier there is no precondition to be too
# strong, so the analogue of PRECOND-TOO-STRONG is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input: a spec whose non-degenerate arm
# could not be discharged at the input the discriminating assertion drives would
# be unusable there while every uniqueness rival still rejected (a reject case
# cannot tell "the rival is wrong" from "the clause is unsatisfiable"), and
# `rival-drop-factor-component` only probes the antecedent's non-vacuity, not
# the consequent's satisfiability at a REACHED point. This case discharges the
# obligation at the F2P shape — a non-degenerate multivariate input whose ground
# factor list has TWO entries, i.e. the recovery-traversal arm the F2P assertion
# exercises, NOT the one-element short-circuit five other witnesses sit on — as
# a `have` in front of the frozen tactic body, which then closes the frozen
# obligation VERBATIM. The concrete part is the input carrier and the
# two-entry list shape; the opaque part is pinned by hypothesis, which is the
# only way to reach a value on this carrier. Verified to be non-vacuous by
# construction: the same `have` with a WRONG claimed value at the same point
# (the factor component `[]` there) does NOT close, so it is not an
# `assumption`-shaped no-op.
_ADMISS = """  have _adm : ∀ (a b : GrPoly),
      degreesNonpos (degreeList (groundMonic { val := 51 })) = false →
      factorListInclude (sqfNorm (groundMonic { val := 51 })).2.2 = [(a, 1), (b, 1)] →
      problem_spec_extFactor { val := 51 }
        (groundLC { val := 51 },
          trialDivision (groundMonic { val := 51 })
            (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 51 })).1)
              (sqfNorm (groundMonic { val := 51 })).2.1 [(a, 1), (b, 1)])) := by
    intro a b hd hfl
    unfold problem_spec_extFactor recoverFactors
    refine ⟨rfl, ?_, ?_⟩
    · intro h
      rw [hd] at h
      exact absurd h (by simp)
    · intro _
      simp only [hfl, List.length_cons, List.length_nil]
      norm_num
"""
_POS_ADMISSIBLE = _swap(_BASE, _PROOF_HEAD, _ADMISS + _PROOF_HEAD)

# (P4) Structurally different but CORRECT, and the shape no other positive
# reaches: the impl leaves the `Id.run do` monad entirely and is a plain
# `match` on the guard Bool with a nested `match` destructuring `sqfNorm`'s
# triple, so there is no `Id.run`, no `do`, no `if`, and no early return
# anywhere. Both other positives keep the monadic wrapper, so a postcondition
# that had been (accidentally) tied to `Id.run`'s unfolding — which is the very
# first step of the frozen proof script — would still pass them both while
# rejecting this. It re-proves the SAME statement by case-splitting on the guard
# with `cases`, which is the honest proof for a `match`-shaped impl. If this
# failed to verify, the spec would be over-fit to the monadic encoding rather
# than to the routing it describes => SPEC-TOO-STRONG.
_IMPL_P4 = """def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) :=
  let mono := groundMonic f
  match degreesNonpos (degreeList mono) with
  | true => (groundLC f, [])
  | false =>
      match sqfNorm mono with
      | (s, g, r) =>
          (groundLC f,
            trialDivision mono (recoverFactors (raiseShift s) g (factorListInclude r) (sqfPart mono)))
"""
_PROOF_P4 = """  intro f
  unfold problem_spec_extFactor implementation_extFactor
  cases hb : degreesNonpos (degreeList (groundMonic f)) with
  | true => simp [hb]
  | false => simp [hb]
"""
_POS_MATCH_NO_MONAD = _swap(_swap(_BASE, _IMPL_FULL, _IMPL_P4),
                            _PROOF_FULL, _PROOF_P4)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (R1) THE DISCRIMINATING DEFECT — the square-free norm is taken of the
# square-free PART rather than of the full monic form. This is the pre-patch
# routing `Solution_prepatch.lean` reverts to.
_RIVAL_NORM_OF_PART = _swap(_BASE, _NORM_LINE, "  let (s, g, r) := sqfNorm fSqf\n")
# Both selector branches are pinned CONCRETELY, which is what makes the
# gold-side build informative rather than merely failing: `hone` says the norm of
# the PART factors into ONE ground factor (so the rival's selector short-circuits
# to `[sqfPart mono]`), and `hmany` gives the norm of the MONIC form as an
# explicit TWO-entry list (so the spec's own `recoverFactors` takes the traversal
# arm and REDUCES). Both are about DISTINCT opaque terms — `sqfNorm (sqfPart
# (groundMonic f))` and `sqfNorm (groundMonic f)` — so they are jointly
# satisfiable, and that is exactly the sub-domain the routing defect is observable
# on. An earlier form of this witness left the spec-side length abstract, so gold
# failed on an UNREDUCED `if _ .length = 1 then _ else _` term whose exit code
# said nothing about the claim; with both branches concrete `simp` reduces the
# spec side on gold, PROVES the equation there (the revealed hypothesis type is
# `True`), and cannot prove it for the rival (the revealed type is the concrete
# `trialDivision mono [sqfPart mono] = trialDivision mono [recoverOne .., ..]`
# equation). That pair is the refutation.
_W_NORM_OF_PART = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 3 })) = false)
    (hone : (factorListInclude (sqfNorm (sqfPart (groundMonic { val := 3 }))).2.2).length = 1)
    (hmany : factorListInclude (sqfNorm (groundMonic { val := 3 })).2.2
        = [({ val := 11 }, 1), ({ val := 13 }, 1)])
    (hdiff : trialDivision (groundMonic { val := 3 }) [sqfPart (groundMonic { val := 3 })]
      ≠ trialDivision (groundMonic { val := 3 })
          (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 3 })).1)
            (sqfNorm (groundMonic { val := 3 })).2.1
            [({ val := 11 }, 1), ({ val := 13 }, 1)])) :
    ¬ problem_spec_extFactor { val := 3 }
        (implementation_extFactor { val := 3 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hone, hmany, Bool.false_eq_true, if_false,
    if_pos, List.length_cons, List.length_nil, Nat.reduceAdd, Nat.reduceEqDiff,
    reduceIte, List.forIn_cons, List.forIn_nil, recoverLoop, List.nil_append,
    List.append_assoc, List.singleton_append, List.cons_append] at h3
  exact hdiff h3
"""

# (R2) THE OTHER ROUTING EDGE — the norm is taken of the right polynomial, but
# the multiplicity recovery divides against the square-free PART instead of the
# full monic form.
_RIVAL_DIVIDE_AGAINST_PART = _swap(_BASE, _TRIAL_LINE,
                                   "  return (lc, trialDivision fSqf factors)\n")
_W_DIVIDE_AGAINST_PART = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 5 })) = false)
    (hone : (factorListInclude (sqfNorm (groundMonic { val := 5 })).2.2).length = 1)
    (hdiff : trialDivision (sqfPart (groundMonic { val := 5 }))
          [sqfPart (groundMonic { val := 5 })]
        ≠ trialDivision (groundMonic { val := 5 }) [sqfPart (groundMonic { val := 5 })]) :
    ¬ problem_spec_extFactor { val := 5 }
        (implementation_extFactor { val := 5 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hone, if_pos, Bool.false_eq_true, if_false] at h3
  exact hdiff h3
"""

# (R3) THE SELECTOR IS REMOVED — the single-ground-factor short-circuit fires
# UNCONDITIONALLY, so the recovery traversal never runs and the factor component
# is always the one-element square-free part.
_RIVAL_ALWAYS_SHORT_CIRCUIT = _swap(_BASE, _SELECT_BLOCK,
                                    "  let factors : List ExPoly := [fSqf]\n")
_W_ALWAYS_SHORT_CIRCUIT = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 7 })) = false)
    (hfl : factorListInclude (sqfNorm (groundMonic { val := 7 })).2.2
        = [({ val := 11 }, 1), ({ val := 13 }, 1)])
    (hdiff : trialDivision (groundMonic { val := 7 }) [sqfPart (groundMonic { val := 7 })]
        ≠ trialDivision (groundMonic { val := 7 })
            (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 7 })).1)
              (sqfNorm (groundMonic { val := 7 })).2.1
              [({ val := 11 }, 1), ({ val := 13 }, 1)])) :
    ¬ problem_spec_extFactor { val := 7 }
        (implementation_extFactor { val := 7 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hfl, Bool.false_eq_true, if_false,
    List.length_cons, List.length_nil, Nat.reduceAdd, Nat.reduceEqDiff,
    reduceIte, List.forIn_cons, List.forIn_nil, recoverLoop, List.nil_append,
    List.append_assoc, List.singleton_append, List.cons_append] at h3
  exact hdiff h3
"""

# (R4) THE SELECTOR'S GUARD IS INVERTED — the short-circuit fires exactly when
# the ground factor list does NOT have length one, so a single ground factor is
# pushed through the recovery traversal and a multi-factor list gets the
# one-element fallback. Wrong on BOTH arms.
_RIVAL_INVERT_LENGTH_GUARD = _swap(_BASE, _LEN_GUARD,
                                   "  if factors0.length ≠ 1 then\n")
_W_INVERT_LENGTH_GUARD = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 9 })) = false)
    (hfl : factorListInclude (sqfNorm (groundMonic { val := 9 })).2.2 = [({ val := 17 }, 2)])
    (hdiff : trialDivision (groundMonic { val := 9 })
          (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 9 })).1)
            (sqfNorm (groundMonic { val := 9 })).2.1 [({ val := 17 }, 2)])
        ≠ trialDivision (groundMonic { val := 9 }) [sqfPart (groundMonic { val := 9 })]) :
    ¬ problem_spec_extFactor { val := 9 }
        (implementation_extFactor { val := 9 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hfl, Bool.false_eq_true, if_false,
    List.length_cons, List.length_nil, ne_eq, reduceIte, not_true_eq_false] at h3
  exact hdiff h3
"""

# (R5) THE TRAVERSAL IS INCOMPLETE — the recovery loop stops one ground factor
# short, so the final component is never recovered.
_RIVAL_DROP_LAST = _swap(_BASE, _FOR_LINE, "    for entry in factors0.dropLast do\n")
_W_DROP_LAST = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 21 })) = false)
    (hfl : factorListInclude (sqfNorm (groundMonic { val := 21 })).2.2
        = [({ val := 31 }, 1), ({ val := 37 }, 1)])
    (hdiff : trialDivision (groundMonic { val := 21 })
          (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 21 })).1)
            (sqfNorm (groundMonic { val := 21 })).2.1 [({ val := 31 }, 1)])
        ≠ trialDivision (groundMonic { val := 21 })
            (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 21 })).1)
              (sqfNorm (groundMonic { val := 21 })).2.1
              [({ val := 31 }, 1), ({ val := 37 }, 1)])) :
    ¬ problem_spec_extFactor { val := 21 }
        (implementation_extFactor { val := 21 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hfl, Bool.false_eq_true, if_false,
    List.length_cons, List.length_nil, List.dropLast_cons₂, List.dropLast_single,
    recoverLoop, Nat.reduceAdd, Nat.reduceEqDiff, reduceIte, List.forIn_cons,
    List.forIn_nil, List.nil_append, List.append_assoc, List.singleton_append,
    List.cons_append] at h3
  exact hdiff h3
"""

# (R6) THE FALLBACK'S VALUE IS WRONG — the selector fires on the right
# condition but yields the monic form itself instead of its square-free part.
_RIVAL_FALLBACK_IS_MONIC = _swap(_BASE, _FALLBACK, "    factors := [mono]\n")
_W_FALLBACK_IS_MONIC = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 23 })) = false)
    (hone : (factorListInclude (sqfNorm (groundMonic { val := 23 })).2.2).length = 1)
    (hdiff : trialDivision (groundMonic { val := 23 }) [groundMonic { val := 23 }]
        ≠ trialDivision (groundMonic { val := 23 }) [sqfPart (groundMonic { val := 23 })]) :
    ¬ problem_spec_extFactor { val := 23 }
        (implementation_extFactor { val := 23 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hone, Bool.false_eq_true, if_false, if_pos] at h3
  exact hdiff h3
"""

# (R7) THE FACTOR COMPONENT IS DROPPED — the non-degenerate case returns an
# empty factor component, i.e. the degenerate case's answer everywhere.
_RIVAL_DROP_RESULT = _swap(_BASE, _TRIAL_LINE, "  return (lc, [])\n")
_W_DROP_RESULT = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 27 })) = false)
    (hone : (factorListInclude (sqfNorm (groundMonic { val := 27 })).2.2).length = 1)
    (hne : trialDivision (groundMonic { val := 27 }) [sqfPart (groundMonic { val := 27 })] ≠ []) :
    ¬ problem_spec_extFactor { val := 27 }
        (implementation_extFactor { val := 27 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hone, Bool.false_eq_true, if_false, if_pos] at h3
  exact hne h3.symm
"""

# (R8) THE COEFFICIENT COMPONENT IS TAKEN OF THE WRONG POLYNOMIAL — the ground
# leading coefficient is read off the MONIC form rather than the input.
_RIVAL_LC_OF_MONIC = _swap(
    _BASE, _IMPL_HEAD,
    """def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
  let mono := groundMonic f
  let lc := groundLC mono
""")
_W_LC_OF_MONIC = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 41 })) = false)
    (hone : (factorListInclude (sqfNorm (groundMonic { val := 41 })).2.2).length = 1)
    (hlc : groundLC (groundMonic { val := 41 }) ≠ groundLC { val := 41 }) :
    ¬ problem_spec_extFactor { val := 41 }
        (implementation_extFactor { val := 41 }) := by
  intro hs
  have h1 := hs.1
  unfold implementation_extFactor at h1
  simp only [Id.run, bind, pure, hd, hone, Bool.false_eq_true, if_false, if_pos] at h1
  exact hlc h1
"""

# (R10) THE LENGTH-ONE ARM RETURNS THE TRAVERSAL'S OUTPUT — the selector fires
# on the RIGHT condition, and the multi-factor arm is untouched and correct, but
# the one-ground-factor arm hands back the recovery traversal over that
# single-entry list instead of the square-free part. Strictly NARROWER than
# `rival-invert-length-guard` (which is also wrong on the multi arm) and than
# `rival-fallback-is-monic` (which substitutes a polynomial, not a traversal), so
# it isolates the fallback's VALUE on the arm the guard selects.
_RIVAL_LONE_ARM_TRAVERSAL = _swap(
    _BASE, _FALLBACK, "    factors := recoverLoop (raiseShift s) g factors0\n")
_W_LONE_ARM_TRAVERSAL = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 63 })) = false)
    (hfl : factorListInclude (sqfNorm (groundMonic { val := 63 })).2.2 = [({ val := 71 }, 1)])
    (hdiff : trialDivision (groundMonic { val := 63 })
          (recoverLoop (raiseShift (sqfNorm (groundMonic { val := 63 })).1)
            (sqfNorm (groundMonic { val := 63 })).2.1 [({ val := 71 }, 1)])
        ≠ trialDivision (groundMonic { val := 63 }) [sqfPart (groundMonic { val := 63 })]) :
    ¬ problem_spec_extFactor { val := 63 }
        (implementation_extFactor { val := 63 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hfl, Bool.false_eq_true, if_false,
    List.length_cons, List.length_nil, if_pos] at h3
  exact hdiff h3
"""

# (R11) THE INPUT IS ECHOED AS ITS OWN FACTOR — the length-one arm returns the
# raw INPUT polynomial as a lone factor. On this carrier the input `f` and its
# monic form's square-free part are distinct opaque terms, so this is an
# un-factored blob rather than a factorization. Distinct from
# `rival-fallback-is-monic`, which returns the MONIC form: this one never applies
# any algebra callee at all to what it hands back.
_RIVAL_ECHO_INPUT = _swap(_BASE, _FALLBACK, "    factors := [f]\n")
_W_ECHO_INPUT = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 67 })) = false)
    (hone : (factorListInclude (sqfNorm (groundMonic { val := 67 })).2.2).length = 1)
    (hdiff : trialDivision (groundMonic { val := 67 }) [{ val := 67 }]
        ≠ trialDivision (groundMonic { val := 67 }) [sqfPart (groundMonic { val := 67 })]) :
    ¬ problem_spec_extFactor { val := 67 }
        (implementation_extFactor { val := 67 }) := by
  intro hs
  have h3 := hs.2.2 hd
  unfold implementation_extFactor at h3
  unfold recoverFactors at h3
  simp only [Id.run, bind, pure, hd, hone, Bool.false_eq_true, if_false, if_pos] at h3
  exact hdiff h3
"""

# (R9) THE DEGENERATE CASE IS NOT SHORT-CIRCUITED — the guard is removed
# outright, so a degenerate-degree input is pushed through the whole recovery
# pipeline instead of returning no factors.
_RIVAL_NO_DEGENERATE = _swap(_BASE, _DEGEN, "")
_W_NO_DEGENERATE = """
example
    (hd : degreesNonpos (degreeList (groundMonic { val := 43 })) = true)
    (hone : (factorListInclude (sqfNorm (groundMonic { val := 43 })).2.2).length = 1)
    (hne : trialDivision (groundMonic { val := 43 }) [sqfPart (groundMonic { val := 43 })] ≠ []) :
    ¬ problem_spec_extFactor { val := 43 }
        (implementation_extFactor { val := 43 }) := by
  intro hs
  have h2 := hs.2.1 hd
  unfold implementation_extFactor at h2
  simp only [Id.run, bind, pure, hd, hone, if_true, if_pos] at h2
  exact hne h2
"""

# (R12) THE COMPUTATION NEVER TERMINATES — the whole body is replaced by a
# `partial` self-call, so no answer is ever produced on any input. The carrier is
# TOTAL (no `loom.semantics.termination` option is set and the frozen impl is a
# plain `def`), so the verifier owes a termination obligation here and this rival
# is genuinely rejected rather than vacuously accepted.
#
# What makes the class SHIPPABLE — an earlier reading of this battery recorded it
# as a witness-lane hole — is that the diverging value must be reached through a
# term gold and the rival SHARE. A `partial def implementation_extFactor f :=
# implementation_extFactor f` cannot be witnessed: `partial` makes the impl an
# opaque constant, so every hypothesis must be stated over
# `implementation_extFactor` itself, which is the one name the rival REPLACES —
# on gold the same hypothesis is a hypothesis about gold's own correct impl and
# the identical script discharges the goal from it (measured: rival exit 0, GOLD
# exit 0 => witness-vacuous). The repair is to make the divergence
# INPUT-INDEPENDENT: routing every input through one `partial` constant makes the
# impl a CONSTANT FUNCTION, and constancy is expressible over the shared
# vocabulary as `implementation_extFactor a = implementation_extFactor b := rfl`.
# The refutation is then clause 1 applied at two inputs at once: the coefficient
# component is pinned to `groundLC f`, which varies with `f`, so no single value
# can satisfy it at two points whose leading coefficients differ. Gold's build
# fails on exactly that constancy step (it is not a constant function), which is
# a SEMANTIC failure of the claim rather than a syntactic one — the type-revealing
# probe prints `implementation_extFactor { val := 91 } = implementation_extFactor
# { val := 93 }` for the rival, where `rfl` closed it, and on gold `rfl` itself
# fails to unify. Measured: rival exit 0, gold exit 1, consistency probe exit 1;
# the opposite claim (both points satisfy the spec, closed by the frozen tactic
# body) builds on gold (exit 0) and fails against the rival (exit 1), so gold's
# exit code tracks the claim.
_RIVAL_NONTERMINATING = _swap(
    _BASE, _IMPL_FULL,
    """/-- A computation whose only reduct is itself: it never terminates. -/
partial def spinForever (_u : Unit) : ExCoeff × List (ExPoly × Nat) := spinForever ()

def implementation_extFactor (_f : ExPoly) : ExCoeff × List (ExPoly × Nat) :=
  spinForever ()
""")
_W_NONTERMINATING = """
example
    (hne : groundLC { val := 91 } ≠ groundLC { val := 93 }) :
    ¬ (problem_spec_extFactor { val := 91 } (implementation_extFactor { val := 91 })
        ∧ problem_spec_extFactor { val := 93 } (implementation_extFactor { val := 93 })) := by
  intro hs
  have e1 := hs.1.1
  have e2 := hs.2.1
  have hsame : implementation_extFactor { val := 91 } = implementation_extFactor { val := 93 } :=
    rfl
  rw [hsame] at e1
  exact hne (e1.symm.trans e2)
"""


# ---------------------------------------------------------------------------
# Shared refinement grounding. The F2P assertion is a ROUND TRIP: it re-expands
# the factorization of an expanded two-factor product over an extension and
# requires the original expression back. So any rival whose faithful real patch
# returns a factor component that is not the input's complete factorization
# fails it, because the product of what it returns is not the input.
# ---------------------------------------------------------------------------

_REF_INCOMPLETE = (
    "its faithful real patch returns a factor component whose product is NOT "
    "the input polynomial, so the F2P assertion — which re-expands the "
    "extension factorization of an expanded two-factor product and requires "
    "the original expression back — reads back a different expression and "
    "fails. It would NOT resolve.")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-invert-branches", "kind": "soundness", "expect": "verify",
     "module": _POS_INVERT_BRANCHES,
     "rationale": "a CORRECT impl with a different control shape: BOTH branch "
                  "tests are inverted — the degenerate-degree guard becomes a "
                  "positive test wrapping the main body with the empty-factor "
                  "answer as a trailing fall-through (no early return), and the "
                  "single-ground-factor selector's two arms are swapped — plus "
                  "the shift polynomial is inlined at its use site rather than "
                  "bound to a local. Identical routing of identical values "
                  "through identical callees; only the executable shape "
                  "differs. The obligation is re-proved for the new shape (the "
                  "frozen `if_neg` step becomes `if_pos`, and the swapped "
                  "selector needs `ite_not` normalization before the "
                  "loop-equals-fold induction applies) with its STATEMENT "
                  "byte-identical, and no new lemma, axiom or assumption is "
                  "introduced. Must verify; if not, the postcondition is "
                  "over-fit to one branch polarity / one return point => "
                  "SPEC-TOO-STRONG. Ports nagini's `pos-control-reorder`, whose "
                  "content is exactly this branch-order flip."},
    {"id": "pos-functional-fold", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a CORRECT impl that replaces the whole imperative selector — "
                  "the mutable factor accumulator, the length branch, the "
                  "mutable carrier and the `for` loop — with the purely "
                  "functional shape, assembling the result in a single "
                  "expression. Correct because the accumulator loop and the "
                  "front-recursive fold compute the same list, which is exactly "
                  "the fact the frozen proof's inductive step establishes; this "
                  "positive therefore closes with that step DROPPED, which is "
                  "the honest cheapest correct impl here and needs no new "
                  "lemma. Must verify; if not, the spec is over-fit to the "
                  "imperative accumulator form => SPEC-TOO-STRONG. Ports "
                  "nagini's `pos-control-shared-loop` (its single shared "
                  "materialisation loop in place of the frozen two)."},
    {"id": "admiss-f2p-two-ground-factors", "kind": "admissibility",
     "expect": "verify",
     "module": _POS_ADMISSIBLE,
     "rationale": "ADMISSIBILITY on a total carrier. There is no precondition "
                  "here, so the PRECOND-TOO-STRONG analogue is the obligation "
                  "being UNSATISFIABLE at an F2P-shaped input — which every "
                  "uniqueness rival is blind to, since a reject case cannot "
                  "distinguish `the rival is wrong` from `the clause cannot be "
                  "discharged at all` there. This discharges the obligation at "
                  "the F2P shape (a non-degenerate multivariate input whose "
                  "ground factor list has TWO entries, i.e. the "
                  "recovery-traversal arm the discriminating assertion drives, "
                  "not the one-element short-circuit the other positives and "
                  "five witnesses sit on) as a `have`, then closes the frozen "
                  "obligation VERBATIM after it. The input carrier and the "
                  "two-entry list shape are concrete; the opaque callees' values "
                  "are pinned by hypothesis, which is the only way to reach a "
                  "value on this carrier, and the entries' multiplicities are "
                  "left universally quantified so nothing about them is assumed. "
                  "Nothing else is assumed: no new declaration, no axiom, no "
                  "`sorry`, STATEMENT byte-identical. Must verify; if not, the "
                  "obligation is unsatisfiable at exactly the input the bundle "
                  "exists to fix => PRECOND-TOO-STRONG / SPEC-UNUSABLE. Checked "
                  "non-vacuous rather than assumed: the same `have` asserting a "
                  "WRONG value at the same point (an empty factor component on "
                  "the non-degenerate arm) does NOT close, so this is not an "
                  "`assumption`-shaped no-op. Ports nagini's `admiss-f2p-input`, "
                  "whose recursive self-call discharges the callee `Requires` at "
                  "the concrete F2P value."},
    {"id": "pos-match-no-monad", "kind": "soundness", "expect": "verify",
     "module": _POS_MATCH_NO_MONAD,
     "rationale": "a CORRECT impl that leaves the `Id.run do` monad ENTIRELY: a "
                  "plain `match` on the guard Bool with a nested `match` "
                  "destructuring the square-free norm's triple, so there is no "
                  "`Id.run`, no `do` block, no `if`, no mutable local and no "
                  "return statement anywhere. Identical routing of identical "
                  "values through identical callees. This reaches the one shape "
                  "the other two positives cannot: both of those keep the "
                  "monadic wrapper, and `simp only [Id.run, bind, pure]` is the "
                  "frozen proof's FIRST step — so a postcondition that had been "
                  "tied to the monadic encoding rather than to the routing would "
                  "pass both of them while rejecting every non-monadic impl of "
                  "the same function. The obligation is re-proved by case "
                  "analysis on the guard (`cases hb : degreesNonpos ..`), which "
                  "is the honest proof for a match-shaped impl, with the "
                  "STATEMENT byte-identical and no new lemma, axiom or "
                  "assumption. Must verify; if not, the spec is over-fit to the "
                  "executable encoding => SPEC-TOO-STRONG. Not a nagini port: "
                  "the nagini carrier has no monadic-vs-pure distinction to "
                  "make, so this is a carrier-specific soundness direction that "
                  "the design document could not have contained."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-norm-of-square-free-part", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_NORM_OF_PART,
     "refinement": "this IS the pre-patch routing: the square-free norm is "
                   "built from the square-free part rather than from the full "
                   "monic form. The part is taken with respect to the principal "
                   "variable, so it omits irreducible components that do not "
                   "involve that variable; the ground factor list it yields is "
                   "then missing those components, and on the reported input "
                   "the norm of the part factors into a SINGLE ground factor, "
                   "so the short-circuit fires and the answer collapses to one "
                   "component. That is precisely the reported symptom (a "
                   "co-factor silently absent from the factorization). Its "
                   "faithful real patch is the pre-patch source, which is what "
                   "the F2P assertion was marked expected-failure against; it "
                   "does NOT resolve.",
     "rationale": "the DISCRIMINATING defect, and the rival "
                  "`Solution_prepatch.lean` reverts to. Rejection source: "
                  "CLAUSE 3, which pins the factor component to trial division "
                  "against factors recovered from `sqfNorm mono` — the norm of "
                  "the full monic form — while this variant recovers from "
                  "`sqfNorm (sqfPart mono)`. `sqfNorm` is opaque with no "
                  "constraining axiom, so those two are not provably equal and "
                  "the clause cannot be discharged. If it verified => "
                  "SPEC-TOO-WEAK: the spec would admit the very defect the "
                  "bundle exists to pin. Ports nagini's "
                  "`weak-prepatch-apply-to-other`. The witness conditions on "
                  "the carrier at the sub-domain where the defect is observable "
                  "— non-degenerate degrees; the norm OF THE PART factoring into "
                  "one ground factor, which is what makes the rival collapse to "
                  "the square-free part; and the norm OF THE MONIC FORM "
                  "factoring into TWO, which is the traversal the spec requires "
                  "instead — and assumes only that the collapsed answer differs "
                  "from the spec's. Pinning BOTH lengths is what makes the "
                  "gold-side build informative rather than merely failing: with "
                  "the spec side's length left abstract, gold failed on an "
                  "unreduced selector `if` term, so its exit code attested to a "
                  "reduction limit rather than to the claim. With both concrete, "
                  "`simp` PROVES the spec's equation on the frozen solution (the "
                  "type-revealing probe prints `True` there) and cannot for the "
                  "rival (it prints the concrete unproven equation), which is "
                  "the discrimination the case the bundle exists to pin has to "
                  "carry.",
     "witness": _W_NORM_OF_PART},
    {"id": "rival-divide-against-part", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVIDE_AGAINST_PART,
     "refinement": "its faithful real patch recovers multiplicities by trial "
                   "division against the square-free part instead of against "
                   "the full monic form. Dividing against a square-free "
                   "polynomial can only ever report multiplicity one, so any "
                   "input with a repeated component comes back with its "
                   "exponents flattened and the re-expanded product is not the "
                   "original. " + _REF_INCOMPLETE,
     "rationale": "the OTHER routing edge of clause 3, and the near-miss of the "
                  "prepatch rival: this variant takes the norm of the RIGHT "
                  "polynomial and recovers the right factors, differing from "
                  "gold only in which polynomial the multiplicity recovery "
                  "divides against. It therefore gets its own witness at its "
                  "own input, since it agrees with gold wherever the two "
                  "polynomials' trial divisions agree — a strictly different "
                  "sub-domain from the prepatch rival's. Rejection source: "
                  "CLAUSE 3's outer application, pinned to `trialDivision mono`; "
                  "`trialDivision` is opaque, so `trialDivision (sqfPart mono)` "
                  "is not provably equal to it. If it verified => "
                  "SPEC-TOO-WEAK: the spec would leave the recovery's own "
                  "argument unconstrained, so half the routing this bundle pins "
                  "would be free.",
     "witness": _W_DIVIDE_AGAINST_PART},
    {"id": "rival-always-short-circuit", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_SHORT_CIRCUIT,
     "refinement": "its faithful real patch always returns the single "
                   "square-free representative and never runs the recovery "
                   "traversal, so every input — however many components it has "
                   "— comes back as one factor. That is the reported symptom in "
                   "its most extreme form. " + _REF_INCOMPLETE,
     "rationale": "the selector is removed outright: the one-element "
                  "short-circuit fires unconditionally, so the recovery "
                  "traversal is dead code. Rejection source: CLAUSE 3 on the "
                  "arm where the ground factor list does NOT have length one — "
                  "the clause requires `recoverLoop` over the whole list there, "
                  "and a one-element list of the square-free part is not "
                  "provably that. If it verified => SPEC-TOO-WEAK (the "
                  "multi-factor arm would be vacuous). Ports nagini's "
                  "`weak-echo-lone-unconditional` — its unconditional "
                  "materialisation of the length-one fallback — and covers "
                  "`weak-input-as-singleton` and `weak-truncate-last`'s "
                  "collapse-to-one behaviour on the same clause. The witness "
                  "pins a TWO-element ground factor list, the shape on which "
                  "the discarded traversal is observable.",
     "witness": _W_ALWAYS_SHORT_CIRCUIT},
    {"id": "rival-invert-length-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT_LENGTH_GUARD,
     "refinement": "its faithful real patch inverts the single-factor test, so "
                   "an input whose norm yields ONE ground factor is pushed "
                   "through the recovery traversal (which composes and "
                   "gcd-refines a factor that needed neither) while a "
                   "multi-component input is collapsed to one representative. "
                   "Wrong in both directions. " + _REF_INCOMPLETE,
     "rationale": "the selector's GUARD DIRECTION, attacked independently of "
                  "whether the selector exists at all. Rejection source: CLAUSE "
                  "3 via `recoverFactors`, violated on BOTH arms — the "
                  "one-ground-factor case gets the traversal's output where the "
                  "square-free part is required, and the multi-factor case gets "
                  "the square-free part where the traversal's output is "
                  "required. If it verified => SPEC-TOO-WEAK (the guard's "
                  "direction would be unconstrained). Ports nagini's "
                  "`weak-echo-factorlist-unconditional` and "
                  "`weak-lone-branch-returns-factorlist`, both of which attack "
                  "the length-one fallback's non-vacuity; this rival attacks it "
                  "from the other side than `rival-always-short-circuit` does, "
                  "so the two demonstrate the guard is pinned in both "
                  "directions. The witness probes the ONE-ground-factor "
                  "sub-domain, where this rival is wrong and "
                  "`rival-always-short-circuit` is right — the input that "
                  "separates their sub-domain claims.",
     "witness": _W_INVERT_LENGTH_GUARD},
    {"id": "rival-drop-last-ground-factor", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_DROP_LAST,
     "refinement": "its faithful real patch stops the recovery traversal one "
                   "ground factor short, so the final component is never "
                   "recovered and the returned factorization is missing a "
                   "co-factor — the reported symptom exactly. " + _REF_INCOMPLETE,
     "rationale": "PARTIAL-DOMAIN on the traversal: correct on the degenerate "
                  "case, correct on the one-ground-factor short-circuit, and "
                  "correct on the FIRST components of a multi-factor list — "
                  "wrong only in that the last entry is dropped. It agrees with "
                  "gold over strictly more of the domain than "
                  "`rival-always-short-circuit`, so it carries its own witness "
                  "at its own two-element list rather than sharing that one's. "
                  "Rejection source: CLAUSE 3's `recoverLoop` over the WHOLE "
                  "ground factor list — the fold's front-recursive shape covers "
                  "every entry, and a traversal over `dropLast` produces the "
                  "proper prefix instead. If it verified => SPEC-TOO-WEAK (the "
                  "traversal's completeness would be unconstrained, which is "
                  "the off-by-one a real recovery loop is most likely to have). "
                  "Ports nagini's `weak-truncate-last-factor`.",
     "witness": _W_DROP_LAST},
    {"id": "rival-fallback-is-monic", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FALLBACK_IS_MONIC,
     "refinement": "its faithful real patch takes the single-factor "
                   "short-circuit on the right condition but returns the monic "
                   "polynomial itself rather than its square-free part, so a "
                   "repeated component is reported once with the wrong "
                   "representative and the recovered multiplicities do not "
                   "reconstruct the input. " + _REF_INCOMPLETE,
     "rationale": "attacks the fallback's VALUE rather than the condition that "
                  "selects it: the guard, the traversal and both routing edges "
                  "are untouched and correct, so this rival is refutable only "
                  "by the clause pinning WHICH polynomial the short-circuit "
                  "yields. It is the case that would survive a spec stating "
                  "merely that the fallback returns some one-element list. "
                  "Rejection source: CLAUSE 3 via `recoverFactors`'s `[fSqf]` "
                  "arm; `sqfPart` is opaque, so `[mono]` is not provably "
                  "`[sqfPart mono]`. If it verified => SPEC-TOO-WEAK (the "
                  "fallback's content would be free). Ports the same nagini "
                  "obligation as `weak-lone-branch-returns-factorlist` — that "
                  "the length-one branch is pinned to a specific value — but at "
                  "the value level rather than the branch level.",
     "witness": _W_FALLBACK_IS_MONIC},
    {"id": "rival-drop-factor-component", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_DROP_RESULT,
     "refinement": "its faithful real patch returns no factors at all on the "
                   "non-degenerate path, so nothing is ever factored and the "
                   "re-expanded product of an empty factorization cannot be the "
                   "input. " + _REF_INCOMPLETE,
     "rationale": "supporting near-miss / floor case: the factor component is "
                  "dropped entirely, i.e. the degenerate case's answer is given "
                  "everywhere. Rejection source: CLAUSE 3 — `[]` is not "
                  "provably the trial division's result, and since "
                  "`trialDivision` is opaque it cannot be shown empty. If it "
                  "verified => SPEC-TOO-WEAK, and specifically it is the case "
                  "that detects a clause-3 antecedent so strong it is never "
                  "satisfiable: were the non-degenerate arm vacuous, this "
                  "variant would verify while computing nothing. Ports nagini's "
                  "`weak-empty-factorisation`.",
     "witness": _W_DROP_RESULT},
    {"id": "rival-lc-of-monic", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LC_OF_MONIC,
     "refinement": "its faithful real patch reads the ground leading "
                   "coefficient off the polynomial AFTER it has been made "
                   "monic. Making a polynomial monic is exactly what divides "
                   "that coefficient out, so the returned coefficient is the "
                   "unit rather than the input's own; the coefficient and the "
                   "factors then no longer multiply back to the input and the "
                   "F2P round trip returns a differently-scaled expression. It "
                   "would NOT resolve.",
     "rationale": "the only rival attacking CLAUSE 1, and the reason it must "
                  "exist: clauses 1 and 3 are independent conjuncts, so a "
                  "battery aimed only at the factor component would leave the "
                  "coefficient component untested and a spec that omitted "
                  "clause 1 entirely would still pass every other case here. "
                  "Rejection source: CLAUSE 1 `result.1 = groundLC f`, pinned "
                  "to the INPUT; `groundLC` and `groundMonic` are opaque, so "
                  "`groundLC (groundMonic f)` is not provably `groundLC f`. If "
                  "it verified => SPEC-TOO-WEAK. This also carries the semantic "
                  "residue of nagini's frame class on a referentially "
                  "transparent carrier: the output component must be a function "
                  "of the named input and not of a derived value.",
     "witness": _W_LC_OF_MONIC},
    {"id": "rival-no-degenerate-short-circuit", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_NO_DEGENERATE,
     "refinement": "its faithful real patch drops the degenerate-degree guard, "
                   "so an input with no positive per-variable degree is pushed "
                   "into the norm-and-recovery pipeline instead of returning no "
                   "factors. Those callees are not defined on a degenerate "
                   "input — the pipeline needs a principal variable to take a "
                   "norm with respect to — so the real patch raises rather than "
                   "returning, and every assertion that reaches it errors out. "
                   "It would NOT resolve.",
     "rationale": "the only rival attacking CLAUSE 2, and the only witness on "
                  "the degenerate side of the degree test — without it every "
                  "witness would hold the degenerate-degree binder at `false` "
                  "and clause 2 would be a conjunct no rival was built to "
                  "abuse. Rejection source: CLAUSE 2 `degreesNonpos (degreeList "
                  "mono) = true → result.2 = []`; this variant returns the "
                  "recovery pipeline's output there, which is opaque and not "
                  "provably `[]`. If it verified => SPEC-TOO-WEAK (the "
                  "degenerate case's answer would be unconstrained). Ports the "
                  "branch-completeness content of nagini's two-branch "
                  "`weak-lone-branch-returns-factorlist` at the outer "
                  "(degenerate vs non-degenerate) split rather than the inner "
                  "one.",
     "witness": _W_NO_DEGENERATE},
    {"id": "rival-lone-arm-returns-traversal", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_LONE_ARM_TRAVERSAL,
     "refinement": "its faithful real patch hands back the recovery traversal's "
                   "output on the single-ground-factor arm instead of the "
                   "square-free representative, so an input that does not split "
                   "comes back composed and gcd-refined by a recovery step it "
                   "never needed — a non-canonical representative rather than "
                   "the expected one. " + _REF_INCOMPLETE,
     "rationale": "isolates the fallback's VALUE on the arm the guard actually "
                  "selects, which no other case here does: "
                  "`rival-invert-length-guard` is wrong on the multi-factor arm "
                  "too (so it cannot show the one-factor arm is independently "
                  "pinned), and `rival-fallback-is-monic` substitutes another "
                  "POLYNOMIAL rather than the traversal. This variant leaves the "
                  "guard direction, the multi-factor arm and both routing edges "
                  "correct, so it is refutable only by the clause pinning the "
                  "length-one arm to `[sqfPart mono]` specifically. Rejection "
                  "source: CLAUSE 3 via `recoverFactors`'s `[fSqf]` arm; "
                  "`recoverLoop` over a one-entry list is not provably "
                  "`[sqfPart mono]`, both being opaque. If it verified => "
                  "SPEC-TOO-WEAK. Ports nagini's "
                  "`weak-lone-branch-returns-factorlist` directly — its "
                  "`len<=1` arm returning the raw recovery list — which the "
                  "earlier port folded into two other cases rather than landing.",
     "witness": _W_LONE_ARM_TRAVERSAL},
    {"id": "rival-echo-input-as-factor", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_ECHO_INPUT,
     "refinement": "its faithful real patch returns the input polynomial itself "
                   "as its own lone factor, so nothing is ever factored and the "
                   "answer is an un-factored blob; the leading coefficient has "
                   "not even been divided out of it. " + _REF_INCOMPLETE,
     "rationale": "the ECHO floor case on the factor component: the answer is "
                  "the INPUT, with no algebra callee applied to it at all. "
                  "Distinct from `rival-fallback-is-monic` (which returns the "
                  "monic form, i.e. one callee deep) and from "
                  "`rival-drop-factor-component` (which returns nothing): this "
                  "one tests that the spec pins the factor component to a "
                  "DERIVED value rather than merely to something non-empty. "
                  "Rejection source: CLAUSE 3 via `recoverFactors`'s `[fSqf]` "
                  "arm; `f` and `sqfPart (groundMonic f)` are distinct opaque "
                  "terms, so `[f]` is not provably `[sqfPart mono]`. If it "
                  "verified => SPEC-TOO-WEAK. Ports nagini's "
                  "`weak-input-as-singleton`, which the earlier port recorded as "
                  "covered by `rival-always-short-circuit`'s collapse-to-one "
                  "behaviour rather than landing as its own case.",
     "witness": _W_ECHO_INPUT},
    {"id": "rival-nonterminating-constant", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_NONTERMINATING,
     "refinement": "its faithful real patch never returns on any input: the "
                   "procedure loops without making progress, so every assertion "
                   "that reaches it hangs rather than producing a value. Nothing "
                   "is read back at all, so the F2P assertion — which re-expands "
                   "the extension factorization of an expanded two-factor "
                   "product and requires the original expression back — cannot "
                   "complete. It would NOT resolve.",
     "rationale": "the DIVERGENCE class, on a carrier where it is a real reject "
                  "case rather than a vacuous one: no "
                  "`loom.semantics.termination` option is set and the frozen "
                  "impl is a plain `def`, so the verifier discharges a "
                  "termination obligation and a non-terminating impl is "
                  "genuinely rejected (this is NOT the `partial`-semantics "
                  "vacuity hole other backends have). Rejection source: the "
                  "obligation cannot be closed for an impl that produces no "
                  "value — every clause is stated of `result`, and the frozen "
                  "script's `unfold` / `split_ifs` steps have no body to reduce. "
                  "If it verified => SPEC-TOO-WEAK, and specifically the whole "
                  "spec would be discharged by a program that computes nothing. "
                  "The witness is what makes the class shippable, and it is why "
                  "the class needed its own shape rather than a copy of the "
                  "uniqueness witnesses: a self-referential "
                  "`implementation_extFactor` is an opaque constant whose only "
                  "available hypothesis is stated over the very name the rival "
                  "replaces, so on gold that hypothesis describes gold's own "
                  "correct impl and the same script discharges the goal from it "
                  "(measured: rival 0, gold 0 — vacuous). Making the divergence "
                  "INPUT-INDEPENDENT fixes that: routing every input through one "
                  "`partial` constant makes the impl a CONSTANT FUNCTION, and "
                  "constancy is stateable over shared vocabulary alone "
                  "(`implementation_extFactor a = implementation_extFactor b := "
                  "rfl`). CLAUSE 1 then refutes it at two inputs at once — the "
                  "coefficient component is pinned to `groundLC f`, which varies "
                  "with `f`, so one value cannot satisfy it at two points whose "
                  "leading coefficients differ. Gold fails on precisely the "
                  "constancy step, a semantic failure of the claim: the "
                  "type-revealing probe prints the concrete equation "
                  "`implementation_extFactor { val := 91 } = "
                  "implementation_extFactor { val := 93 }` against the rival "
                  "(where `rfl` closes it) while on gold `rfl` cannot unify the "
                  "two sides at all. Not a nagini port — the nagini sibling "
                  "carries no `diverge-*` / `nonterm-*` case, so this is a "
                  "carrier-specific direction the design document does not "
                  "contain.",
     "witness": _W_NONTERMINATING},
]

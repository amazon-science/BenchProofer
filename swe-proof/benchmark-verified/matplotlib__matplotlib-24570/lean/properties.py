"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24570 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each SPEC
case is a full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte
(region surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a
case that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_alignedOffsets``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``): it
carries that battery's adversarial ARGUMENT over and re-expresses it against this
backend's carrier. It is not a translation of the nagini text.

DEFENDED SURFACE (one total function, four anchor rules)
--------------------------------------------------------
A single modeled function distributes a list of boxes, each given by its
``(height, descent)`` pair, within an intended total extent along one axis:

  alignedOffsets (hdList : List (Rat × Rat)) (height : Rat) (align : String)
      : Rat × Rat × List Rat        -- (resolvedHeight, descent, offsets)

with the precondition ``validAlign align`` (the anchor keyword is one of the six
the surface accepts) carried as a binder hypothesis. The postcondition
``problem_spec_alignedOffsets`` is a conjunction of FOUR independent
anchor-guarded clauses, and each clause pins all THREE output components:

  (BASE)  align = "baseline"          → resolvedHeight = maxExtent + maxDescent
                                      ∧ descent = maxDescent
                                      ∧ offsets = every box at zero
  (LOW)   align ∈ {"left","bottom"}   → resolvedHeight = height ∧ descent = 0
                                      ∧ offsets = each box's OWN descent
  (HIGH)  align ∈ {"right","top"}     → resolvedHeight = height ∧ descent = 0
                                      ∧ offsets = each box flush against the FAR
                                        edge (height - boxHeight + descent)
  (CTR)   align = "center"            → resolvedHeight = height ∧ descent = 0
                                      ∧ offsets = each box centered
                                        ((height - boxHeight)/2 + descent)

WHAT DRIVES THE REJECTS. The discriminating content of the modeled change is the
ANCHOR→RULE GROUPING: which anchor keywords select the own-descent offset rule
(LOW) versus the far-edge rule (HIGH). The two vertical anchors exchange rules;
the horizontal anchors, ``baseline`` and ``center`` are unaffected. So (LOW) and
(HIGH) are the load-bearing clauses the anchor-parameterized layout assertions
pin, while (BASE) and (CTR) are the must-not-regress clauses that the anchors
already behaving correctly exercise. Because every clause also pins
``resolvedHeight`` and ``descent``, the battery attacks those two components
separately from the offsets list — an offsets-only battery would leave both
unconstrained in practice, which is the read-only-frame analogue on a
referentially transparent carrier (spec_guide §0.5: an output component the
rivals never probe is the full-permission hole).

The ten rivals partition the surface as follows, each named by the clause it
violates and the component it corrupts:

  * ``rival-anchor-group-swap`` — (LOW)+(HIGH), offsets. The two vertical anchors
    select each other's offset rule. This is the pre-change grouping.
  * ``rival-splits-low-group-left`` — (LOW), offsets, at the group's HORIZONTAL
    anchor. Splits the own-descent group instead of moving it as a unit, so it is
    the only case that evaluates the spec at ``left``; added by audit (see the
    AUDIT REPAIRS note below).
  * ``rival-splits-high-group-right`` — (HIGH), offsets, at the group's HORIZONTAL
    anchor. The mirror of the previous case on the far-edge group, and the only
    case that evaluates the spec at ``right``; added by the second audit (see
    AUDIT REPAIRS note 3).
  * ``rival-high-edge-halves-slack`` — (HIGH), offsets. A near-miss: the far-edge
    anchors use the CENTERED rule, halving the leftover extent. Agrees with the
    frozen behavior on every box that already fills the extent.
  * ``rival-low-edge-drops-descent`` — (LOW), offsets. The own-descent anchors emit
    zero, collapsing each box's descent contribution.
  * ``rival-partial-domain-first-box`` — (LOW), offsets. Correct on every box but
    the FIRST, where it emits zero. The classic pins-all-but-one attack.
  * ``rival-center-full-slack`` — (CTR), offsets. The centered anchor uses the
    far-edge rule, so a box is flushed instead of centered.
  * ``rival-baseline-descent-component`` — (BASE), descent. The recomputed packing
    descent reduces over each box's ABOVE-baseline extent rather than its descent.
  * ``rival-recomputes-resolved-height`` — (LOW), resolvedHeight. The intended
    total is discarded and recomputed from the box extents for EVERY anchor, not
    just the one clause that specifies a recomputation.
  * ``rival-leaks-descent-component`` — (HIGH), descent. The three anchors that
    must report a zero packing descent instead leak the maximal box descent.

BINDER COVERAGE. All three input binders are varied across the ten refutation
witnesses, and no witness holds one at a value the others share by accident:

  * ``align`` takes all SIX legal values (``bottom``, ``top``, ``center``,
    ``baseline``, ``left``, ``right``), so every one of the four clauses is entered
    by some witness — a rival mishandling only ``center`` or only ``baseline`` is
    caught by its own rival rather than slipping past a battery aimed only at the
    two clauses the change touches. The two HORIZONTAL anchors matter separately:
    (LOW) and (HIGH) are DISJUNCTIVE guards over two anchors each, and a witness
    only ever discharges ONE disjunct, so a battery whose witnesses all enter via
    the vertical anchor never evaluates the horizontal half of either guard.
    ``left`` covers that half of (LOW) and ``right`` covers it for (HIGH); both
    halves of both guards are therefore evaluated by some witness, which is what
    makes a group-SPLITTING rival visible on either group.
  * ``height`` takes four distinct values (60, 72, 84, 100). This binder matters
    because two rules (HIGH, CTR) are functions of the leftover extent
    ``height - boxHeight``: a witness that held ``height`` equal to the tallest
    box would zero that slack and make the far-edge, centered and own-descent
    rules AGREE, so those rivals would verify at the probed point. Each witness
    is therefore stated at a slack-bearing input.
  * ``hdList`` takes three distinct shapes, deliberately chosen so no witness
    relies on an accidental coincidence: ``[(30,5),(60,10)]`` (both boxes carry a
    descent, and box 2 already fills the 60-extent so the two rules differ only
    via the descent), ``[(40,7),(60,0)]`` (a nonzero descent at index 0 ONLY,
    which is what makes the first-box rival's zero detectable — with descents
    ``[0,_]`` the rival would agree with the frozen behavior at index 0), and
    ``[(30,0),(60,9)]`` (a nonzero descent at index 1 only, which is what makes
    the drops-descent rival detectable — the layout geometry the F2P assertions
    themselves use has ZERO descents throughout, so a witness copied from it
    would NOT discriminate this rival at all).

That last point is the substantive one: the shipped F2P geometry has zero
descents, so a rival that drops the descent contribution passes those assertions
narrowly. The spec pins ALL boxes, and the witness for that rival is stated at a
nonzero-descent input precisely so the manifest demonstrates the sub-domain its
``refinement`` argument claims.

Ten distinct input points in total, so no rival is refuted at a point another
rival already covers, and each near-miss is separated from the frozen behavior at
an input where the two genuinely differ.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen tactic script is tuned to the frozen
impl's exact elaboration — so a rejection alone attributes nothing to the spec.
Each ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input: it selects the violated clause's
implication arm by supplying the anchor equality, projects the corrupted output
component, and closes by ``norm_num``. Six of the ten reach the arithmetic by
rewriting the rival's application to its own reduced tuple with a kernel ``rfl``
(``_wit``); the other four NORMALISE the clause instead (``_wit_eval``), because at
their inputs the two tuples differ in a rational sum and a kernel ``rfl`` cannot
reduce ``Rat`` arithmetic — so its gold-side failure was decided by reducibility
rather than by value. That was measured, not assumed; see AUDIT REPAIR 4, which is
also where the split between the two helpers is justified. Every witness was
checked with two real builds: it ELABORATES
against its rival and FAILS against the frozen solution. All ten state their
refutation at literal inputs and bind NO hypothesis, so there is no consistency
obligation to discharge — nothing is assumed about a carrier term.

A carrier note worth recording, because it cost a probe round and the guide flags
this exact trap: ``decide`` does NOT close these goals. The offsets are exact
rationals, and ``decide`` reduces the ``Decidable`` instance rather than the
value, so it gets stuck at ``(… .add …).num`` on every literal — as do ``simp``,
``rfl`` and ``ring_nf`` on the same subterms. ``norm_num`` closes them. For the
same reason the ``show … from rfl`` step that reduces a rival's application must
leave the ARITHMETIC unevaluated (``[60 - 30 + 5, 60 - 60 + 10]``, not
``[35, 10]``): kernel ``rfl`` will reduce the branch dispatch and the ``List.map``
but not the rational additions, so pre-evaluating them makes the ``rfl`` fail
against the rival too and the witness discriminates nothing.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models an imperative accumulate-into-a-list loop over two
parallel integer lists held at HALF permission, with the anchor encoded as an
integer code and the per-box offset pinned by a deep-model pure function. This
lean carrier models the same offset selection as a total function over exact
rationals, returning the whole three-component tuple. The correspondence:

  * nagini ``rival-anchor-group-swap`` (the pre-change grouping) ↦
    ``rival-anchor-group-swap`` here, unchanged in argument; the integer anchor
    codes become the anchor keyword strings the spec's clauses guard on.
  * nagini ``rival-upper-halves-slack`` ↦ ``rival-high-edge-halves-slack``.
  * nagini ``rival-lower-drops-descent`` ↦ ``rival-low-edge-drops-descent``.
  * nagini ``rival-partial-domain-first-box`` ↦ ``rival-partial-domain-first-box``.
    On nagini the rival tests the loop counter; here the loop is a ``List.map``,
    so the faithful re-expression destructures the list and zeroes the head. Same
    attack (correct everywhere but index 0), re-expressed for a mapped carrier.
  * nagini ``pos-control-reorder-branches`` ↦ ``pos-reorder-branches``, and nagini
    ``pos-control-named-slack`` ↦ ``pos-named-slack``. The
    ``correct_alignedOffsets`` statement is byte-identical and the frozen tactic
    body closes each new shape unchanged (no helper lemma, no axiom, no
    assumption token). But note WHY it closes them unchanged, because the port's
    original claim that these two carry nagini's argument over does not survive
    measurement: on this carrier both are DEFINITIONALLY EQUAL to the frozen impl.
    ``rfl`` alone proves the named-slack impl EQUAL to the frozen one as a
    function (pure zeta reduction of the ``let``), and the reordered cascade
    reduces to the frozen one at every anchor by iota. On nagini the same two
    reshapes are real work — Viper re-discharges the postcondition through the
    loop invariant either way — but here the frozen script closes them for free
    and neither touches the spec's arithmetic. They are kept (a definitional
    reshape is still a true soundness statement, and it pins that the dispatch
    ORDER and the ``let`` are not load-bearing) but they are NOT sufficient on
    their own, which is why ``pos-reassociated-arithmetic`` was added.
  * nagini ``admiss-f2p-shaped`` ↦ ``admiss-ground-instance``. Nagini's version
    asserts its four ``Requires`` clauses are usable; here the only precondition
    is the anchor-membership hypothesis, so the honest analogue discharges BOTH
    that hypothesis at a concrete anchor AND the full spec predicate at a
    layout-shaped ground input, inside the proof region, before closing the
    frozen obligation verbatim.
  * nagini ``echo-honest`` — NO COUNTERPART NEEDED, same disposition as nagini's.
    There is no opaque oracle on either carrier: nagini's per-box offset helper is
    a fully-unfolded pure function, and here the spec is written directly over the
    input carrier in arithmetic and ``List.map``, with an empty axioms region and
    no ``opaque`` declaration anywhere. So there is nothing to echo — satisfying a
    clause IS computing its rule — and the UNGROUNDED-ORACLE ECHO class is
    genuinely N/A rather than untested. Nagini shipped an honest positive control
    in lieu of a fake wrong-echo; here the two soundness positives already play
    that role, so no third positive is added for it.
  * nagini ``frame-mutation-write-heights`` (MANDATORY there — the two input lists
    are held at half permission, and a value-neutral element write is rejected for
    insufficient permission) — VACUOUS here. Lean is referentially transparent:
    ``hdList`` is an immutable ``List``, there is no fractional permission, no
    aliasing and no in-place write to express, so the class has no counterpart and
    no substitute is fabricated. The nearest honest analogue on this carrier is
    "an output component left unconstrained", and that IS attacked — by
    ``rival-recomputes-resolved-height`` and ``rival-leaks-descent-component``,
    which corrupt the two components a purely offsets-focused battery would leave
    unprobed.
  * DIVERGENCE / NON-TERMINATION — the nagini sibling carries no ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case, so there is nothing to port. Had it
    carried one, the class would be genuinely VACUOUS on this backend (not a spec
    hole): ``implementation_alignedOffsets`` is a total Lean ``def``, so a
    diverging implementation cannot be written at all. This is the lean
    disposition of the class described in ``the corpus-wide termination-semantics finding``, which
    applies to velvet under partial termination semantics, not here.

AUDIT REPAIRS (independent adversarial re-derivation of the recorded SOUND)
--------------------------------------------------------------------------
The battery was re-audited case-by-case against the real verifier. Two defects
were found and fixed here; both were the kind a recorded SOUND cannot see.

1. THE SOUNDNESS LANE TESTED REDUCTION, NOT THE SPEC. Both shipped positives are
   definitionally equal to the frozen impl on this carrier — measured, not
   argued: ``example : implNamedSlack = implementation_alignedOffsets := rfl``
   elaborates (exit 0), and the reordered cascade reduces to the frozen impl at
   each of the four anchors by ``rfl`` as well. So the frozen tactic script closed
   both for free and the spec's arithmetic was never re-proven for a new shape.
   Two genuinely non-definitional correct reshapes were then tried: the far-edge
   rule reassociated to ``height + descent - boxHeight``, and the centered rule
   spelled ``* (1/2)`` instead of ``/ 2``. Both FAIL the frozen script (exit 1,
   ``rfl ... expected to have type (…).2.2 = List.map (fun hd => height - hd.1 +
   hd.2) hdList``) and both VERIFY (exit 0) once the offsets conjunct is closed by
   ``List.map_congr_left`` + ``ring``. So the spec is NOT over-fit to its
   arithmetic spelling — no SPEC-TOO-STRONG hole — but the lane needed a case that
   demonstrates it. Shipped as ``pos-reassociated-arithmetic``.

2. NO CASE EVER EVALUATED THE SPEC AT A HORIZONTAL ANCHOR. (LOW) and (HIGH) are
   disjunctive guards over two anchors each, and a witness discharges exactly one
   disjunct; all eight witnesses then present entered via ``Or.inr`` (the vertical
   anchor), ``center`` or ``baseline``. So a rival that SPLITS a group — moving
   only the horizontal anchor — was unattacked, and it is not a hypothetical: the
   grouping is the entire discriminating content of the modeled change, so a
   battery that only probes the anchors that moved licenses breaking the ones that
   stayed. Shipped as ``rival-splits-low-group-left`` (witness at ``left``,
   ``Or.inl``; rival build exit 0, frozen-solution build exit 1).

3. THE MIRROR HALF OF THE SAME GAP WAS STILL OPEN, and the manifest's own prose
   claimed otherwise. Repair 2 landed a witness at ``left``, closing the (LOW)
   guard's horizontal disjunct — but ``right`` remained the one legal anchor no
   witness reached, so the (HIGH) guard's ``Or.inl`` half was still never
   evaluated, while the binder-coverage note asserted the horizontal halves of
   BOTH guards were covered and the ``left`` case's rationale claimed it closed
   "the `left` and `right` halves". A false claim about coverage the manifest did
   not demonstrate, and a live gap behind it: measured, a rival splitting the
   far-edge group at ``right`` (vertical anchor keeps the far-edge rule, the
   horizontal one gets the own-descent rule) fails the frozen script (exit 1) and
   its refutation at ``right`` elaborates against the rival (exit 0) while failing
   against the frozen solution (exit 1) — with the flipped claim (the spec HOLDS
   there) elaborating on gold (exit 0), so gold's exit code tracks the claim.
   Shipped as ``rival-splits-high-group-right``; the two overstated prose passages
   were corrected to say which case covers which half.

   The same re-audit also machine-checked what the reject lane rests on, rather
   than arguing it. All nine original witnesses were rebuilt: nine elaborate
   against their rival (exit 0) and nine fail against the frozen solution (exit
   1); the tenth, shipped by this audit, was built the same way. Because every gold-side failure is a ``rfl`` type mismatch — a shape an
   audit must distrust, since a syntactic failure is not a refutation — each was
   also put through the FORGERY test: a file differing only in what it CLAIMS,
   asserting the spec HOLDS at the same input. All ten forgeries elaborate
   against the frozen solution (exit 0) and fail against their rival (exit 1). So
   gold's exit code carries information about the claim and the rejections are
   semantic, not tactic artifacts. — CORRECTED by AUDIT REPAIR 4: that last
   inference does not follow. The forgery flips the claim but replaces the TACTIC
   too, so it never runs the witness's own ``show … from rfl`` step; four of the
   ten witnesses fail on gold at that step for an irreducible ``Rat`` sum, and
   for them gold's exit code carried nothing. See FOURTH AUDIT. Independently, the frozen solution provably
   satisfies the spec at all witness inputs (one file, exit 0).

   Two further facts worth recording because they bound the whole SPEC-TOO-WEAK
   lane. First, the spec is FUNCTIONAL under its precondition: ``validAlign align``
   implies any two results satisfying ``problem_spec_alignedOffsets`` at the same
   input are EQUAL, proven and machine-checked (exit 0). All three output
   components are pinned uniquely at every legal anchor, so no wrong impl can
   verify at all and no spec hole of the SPEC-TOO-WEAK kind exists to find — which
   is why every rival probe below is rejected. Second, the admissibility case's
   two ground facts are load-bearing, not decoration: forging the precondition at
   an illegal keyword fails (exit 1), and forging the ground instance to claim the
   spec holds of a WRONG tuple at the same input also fails (exit 1).

Four further wrong impls were written and all four were REJECTED as they should
be, so they are not shipped: the baseline resolved-height dropping its descent
term; the baseline offsets emitting each descent instead of zero; the far-edge
rule clamping negative slack via ``max 0 (height - boxHeight)`` (a rival that
agrees with the frozen behavior at every input any other witness uses, and is
separated only where the intended total is SMALLER than a box); and the low-edge
offsets list reversed — right multiset, wrong order. No new wrong impl verified,
so no spec hole was found.

The second audit added five more wrong impls beyond those, all REJECTED with a
discriminating witness (impl exit 1; witness rival exit 0 / gold exit 1): the
baseline resolved height reduced over each box's full extent rather than the
above-baseline extent plus the max descent (a near-miss coinciding with the frozen
behavior whenever the tallest box carries the max descent); the far-edge rule
SUBTRACTING the descent instead of adding it (invisible at zero descent); the
resolved height recomputed for the CENTERED anchor only, probing the ``(CTR)``
resolved-height conjunct that the shipped recompute rival demonstrates only for
``(LOW)``; the own-descent offsets list carrying an extra trailing entry — right
per-box values, wrong LENGTH, probing whether the clause pins length and not just
contents (it does, being a ``List.map`` equation); and the baseline offsets
emitting each descent instead of zero, the ``(BASE)`` offsets conjunct. Three more
correct RESHAPES were tried and all three VERIFY (exit 0): the whole dispatch
rewritten as a ``match`` on the anchor keyword with alternative patterns (under the
frozen tactic body AND under the ring-based one), and the far-edge rule spelled
``descent - (boxHeight - height)`` with the centered rule put over a common
denominator ``(height + 2*descent - boxHeight)/2``. So on every axis probed the
spec is neither too weak nor over-fit to its arithmetic spelling.

The witnesses were also re-derived rather than trusted. Each was rebuilt twice:
all elaborate against their rival (exit 0) and all fail against the
frozen solution (exit 1). Every gold-side failure is a ``rfl`` type mismatch at
the reduction step, which is the shape an audit must distrust — a syntactic
failure is not a refutation. It was therefore checked SEMANTICALLY: the frozen
solution provably SATISFIES the spec at every witness input (each discharged
by ``correct_alignedOffsets _ _ _ (by unfold validAlign; decide)``, one file,
exit 0). Since gold satisfies the spec at every witness's input, each witness's
``¬ problem_spec_alignedOffsets …`` is FALSE of gold, so gold's build failure is
semantically forced and cannot be a tactic artifact. — CORRECTED by AUDIT REPAIR
4: the second half of that sentence is a non sequitur. That gold's build MUST fail
does not mean its exit code was produced by the claim; a witness can be false of
gold and still fail for a stuck ``rfl``, and four of the ten did. What licenses the
inference is the exit code INVERTING when the claim does, which is what the fourth
audit measured and what the four re-authored witnesses now have. The carrier note's tactic
claims were re-measured too and all hold: on ``(60 : Rat) - 30 + 5 = 5``,
``decide`` fails (``instDecidableNot did not reduce to isTrue or isFalse``),
``simp`` and ``ring_nf`` leave unsolved goals, ``rfl`` errors on the goal shape,
and ``norm_num`` closes it.

THIRD AUDIT (independent re-derivation; no case changed, one prose claim fixed)
------------------------------------------------------------------------------
A third adversarial pass re-ran every build from scratch rather than trusting the
notes above. All 14 cases behaved as declared (4 verify exit 0, 10 reject exit 1),
and the spec view + ``theorem correct_alignedOffsets`` statement were confirmed
BYTE-IDENTICAL to the frozen file for all 14 modules, so no case reformats or
weakens the obligation it is supposed to discharge.

The reject lane's 2x2 was rebuilt in full: all ten witnesses elaborate against
their rival (exit 0) and all ten fail against the frozen solution (exit 1), and
because every gold-side failure is a ``rfl``/``Type mismatch`` — a shape an audit
must distrust — each was put through the FORGERY test with a self-contained
flipped claim (the spec HOLDS at that same input, proved from the four clause
slots directly, NOT via ``correct_alignedOffsets``, which the witness harness
strips). All ten forgeries elaborate on gold (exit 0) and FAIL on their rival
(exit 1, ``Application type mismatch``). Gold's exit code therefore tracks what is
claimed, so the rejections are semantic and not tactic artifacts. — CORRECTED by
AUDIT REPAIR 4: it tracks what is claimed under the FORGERY's tactic, which is not
the witness's. Under the witness's own ``show … from rfl`` step, four of the ten
fail on gold identically for gold's TRUE value and for the rival's; those four were
re-authored over ``norm_num``. See FOURTH AUDIT. No witness binds
a hypothesis, so ``consistency_probe`` is ``None`` for all ten — there is no
satisfiability obligation to forge (re-measured after the repair: ``None`` for the
four re-authored witnesses too).

Three structural facts behind the manifest's own claims were re-measured, since
each is load-bearing and none is mechanically checked:

  * ``pos-reassociated-arithmetic`` genuinely re-proves: its impl under the FROZEN
    tactic body FAILS (exit 1, ``rfl ... expected to have type
    (implementation_alignedOffsets hdList height "right").2.2 = List.map (fun hd
    => height - hd.1 + hd.2) hdList``). So the ring-based re-proof is doing real
    work and the soundness lane is not just testing reduction.
  * the other two positives ARE definitionally free, as the manifest admits:
    the named-slack impl equals the frozen one by ``rfl`` (exit 0), and the
    reordered cascade reduces to the frozen tuple at all SIX anchors by a single
    ``rfl`` (exit 0). Their honest value is pinning that dispatch order and the
    ``let`` are not load-bearing — not testing the spec's arithmetic.
  * ``admiss-ground-instance``'s two ground facts are both load-bearing: forging
    the precondition at an illegal keyword fails (exit 1, ``decide`` proves the
    proposition false) and forging the ground instance to a WRONG tuple at the
    same input fails (exit 1).

SPEC-TOO-WEAK is bounded by proof, not by sampling. The spec is FUNCTIONAL under
its precondition: ``validAlign align`` implies any two results satisfying
``problem_spec_alignedOffsets`` at the same input are EQUAL (re-proven from
scratch, one file, exit 0, discharging all six anchors including both disjuncts of
(LOW) and (HIGH)). All three output components are pinned uniquely at every legal
anchor, so NO wrong impl can verify and the SPEC-TOO-WEAK lane is closed as a
theorem. Consistent with that, nine further wrong impls beyond the shipped ten
were written and all nine were REJECTED (exit 1): an empty-list corner returning
the caller's total; a single-box corner emitting ``[0]``; the centered anchor given
the own-descent rule; the far-edge rule doubling the descent; the baseline descent
hard-wired to zero; the centered rule halving the descent too; the baseline offsets
emitting each descent; the baseline total dropping its descent term; and the
far-edge rule clamping negative slack via ``max 0 (height - boxHeight)`` — the last
being wrong only where the intended total is SMALLER than a box, a sub-domain no
shipped witness probes. Nothing verified; no spec hole.

SPEC-TOO-STRONG was probed with three NEW correct reshapes: the own-descent rule
via ``List.map Prod.snd`` (verifies, exit 0, under the frozen script); the far-edge
rule as ``descent - (boxHeight - height)`` with the centered rule over a common
denominator (verifies, exit 0); and the offsets built by EXPLICIT RECURSION over
the list instead of ``List.map`` — the most distant reshape tried, since it needs
induction rather than reduction. That one verifies (exit 0) once the list equation
is proven as an inline ``have`` induction inside the proof region. Worth recording
that the same reshape FAILS (exit 1, ``unsolved goals``) if the induction is run
after ``rcases`` on the anchor guard, because the ``if``-cascade is then already
specialized and the inductive hypothesis is stated about the wrong term — a proof
artifact, NOT a spec hole, which is exactly the confusion an audit has to resolve
by building both. No faithful correct reshape was rejected.

DIVERGENCE is vacuous here by demonstration rather than by argument. The frozen
solution sets no ``loom.semantics.termination`` option (it is a plain Lean ``def``,
not a loom bundle), and a diverging impl written the only way ``variant_scope``
permits — a non-``partial`` recursive ``def`` with no decreasing measure — is
rejected by Lean's own elaborator (exit 1, ``fail to show termination for``). So
the class cannot be expressed on this carrier at all; it is not a spec hole and
not a shippable reject case.

The carrier note's tactic claims were re-measured in the position that actually
matters — a FALSE hypothesis to be refuted, not a bare goal. On ``([5, 10] :
List Rat) = [60 - 30 + 5, 60 - 60 + 10] ⊢ False``: ``simp``, ``rfl``, ``ring_nf``
and ``omega`` all fail, and ``norm_num`` closes it (exit 0). ``decide`` is the
interesting one: as a bare goal it fails to reduce, and ``decide at`` is not even
syntax. So the note is right that ``norm_num`` is the tactic these witnesses need.

One PROSE defect was found and fixed, the only change this audit made.
``rival-high-edge-halves-slack``'s rationale claimed its slack-bearing sub-domain
is one "no other rival's witness probes". That was true when written, but AUDIT
REPAIRS 2 and 3 later landed witnesses at total 100 (``left``) and 84 (``right``),
both slack-bearing, so the claim had gone stale — the same class of
coverage-overclaim that repair 3 corrected. It now states what the manifest
actually demonstrates: the witness is the only one at (``top``, total 100), and no
other witness enters (HIGH) via ``Or.inr`` where this rival is wrong. The case's
own discrimination was unaffected (rival exit 0 / gold exit 1 / forgery inverted).

Also confirmed against the frozen artifact rather than assumed: the
``rival-anchor-group-swap`` impl is BYTE-IDENTICAL (comments aside) to
``Solution_prepatch.lean``'s impl region, so its ``refinement`` claim to be the
unresolved starting state is exact; the axioms region really is empty with no
``opaque``/``axiom``/``partial`` declaration anywhere, so the ECHO class is N/A as
recorded; and the ten witness inputs are ten DISTINCT points covering all six
anchors, four totals and three list shapes, matching the binder-coverage note.
Finally, the precondition boundary was characterized: an impl correct at all six
legal anchors but returning garbage at an ILLEGAL keyword VERIFIES (exit 0), which
is the correct consequence of carrying anchor validation as a binder hypothesis and
locates exactly where the spec's authority stops.

FOURTH AUDIT (four witnesses re-authored: the gold-side failure was HOLLOW)
--------------------------------------------------------------------------
The two audits above both noticed that every gold-side failure was a ``rfl``
``Type mismatch`` and both said the right thing about it — a syntactic failure is
not a refutation — and both then cleared it with the WRONG test. The FORGERY test
they ran flips the CLAIM but also changes the TACTIC: the forgery proves the spec
from the four clause slots with ``norm_num``, so it never executes the witness's
own ``show … from rfl`` step. It therefore could not see that for four of the ten
witnesses that step is decided by REDUCIBILITY and not by value.

The deciding test is the one the forgery skipped: keep the witness's tactic and
write GOLD'S OWN VALUE as the claim. Kernel ``rfl`` cannot reduce ``Rat``
``+``/``-``/``/`` at all — ``Rat.normalize`` goes through the well-founded
``Nat.gcd`` — so at any input where the two tuples differ in a rational sum, the
``rfl`` fails because one side is STUCK. Measured, one build, gold, all ten
witness points, each asserting gold's value as ``#eval`` prints it:

  * SIX build (exit 0): ``60 "bottom" = (60, 0, [5, 10])``, ``100 "left" =
    (100, 0, [5, 10])``, ``[(30,0),(60,9)] 60 "bottom" = (60, 0, [0, 9])``,
    ``[(40,7),(60,0)] 60 "bottom" = (60, 0, [7, 0])``, ``100 "bottom" =
    (100, 0, [5, 10])``, and — for ``rival-leaks-descent-component``, whose
    witness differs from gold in the DESCENT slot only — ``60 "top" = (60, 0,
    List.map (fun hd => 60 - hd.1 + hd.2) …)``. For these the exit code flips with
    the claim, so gold's failure is a real refutation and the cases are unchanged.
  * FOUR FAIL with byte-identical ``Type mismatch … rfl … ?m.35 = ?m.35``:
    ``84 "right" = (84, 0, [59, 34])``, ``100 "top" = (100, 0, [75, 50])``,
    ``72 "center" = (72, 0, [26, 16])`` and ``84 "baseline" = (60, 10, [0, 0])`` —
    every one of them TRUE of gold, ``#eval`` printing exactly ``(mkRat 84 1,
    mkRat 0 1, [mkRat 59 1, mkRat 34 1])``, ``(mkRat 100 1, mkRat 0 1, [mkRat 75
    1, mkRat 50 1])`` and ``(mkRat 60 1, mkRat 10 1, [mkRat 0 1, mkRat 0 1])``.
    Isolated: ``((84 : Rat) - 30) + 5 = 59`` and ``((72 : Rat) - 30) / 2 + 5 = 26``
    both fail by ``rfl``, while ``(26 : Rat) = mkRat 26 1`` and ``maxList
    [(5 : Rat), 10] = 10`` succeed — so it is the arithmetic, not the literal
    representation or ``maxList``, that is irreducible.

So for ``rival-splits-high-group-right``, ``rival-high-edge-halves-slack``,
``rival-center-full-slack`` and ``rival-baseline-descent-component`` gold's exit
code did not depend on what was claimed and the recorded rejection attested
nothing about whether gold satisfies the spec there. Two of those four were not in
scope of any earlier check at all: the ``100 "top"`` and ``60 "top"`` points had
never had gold's own value asserted, and it is why the sixth bullet above matters —
the two ``top`` witnesses look identical in shape and only one of them is sound.

REPAIR. Those four now use ``_wit_eval``: the clause instance is normalised by
``norm_num +decide [implementation_alignedOffsets, maxList]`` instead of being
rewritten by ``rfl``. ``+decide`` is required — the default simp set leaves
``if "right" = "baseline" then …`` standing on a String literal, measured — and
``norm_num`` then evaluates the rationals on both sides. New 2x2, one build each,
every build reaching a verdict (5.8-8.1 s, no timeout):

  * against the rival, all four ELABORATE (exit 0): the clause normalises to a
    false numeric equation and the refutation closes;
  * against the frozen solution, all four FAIL (exit 1) with

        error: unsolved goals
        h : problem_spec_alignedOffsets [(30, 5), (60, 10)] 84 "right" (…)
        hx : True
        ⊢ False

    — ``hx : True`` is the whole point: ``norm_num`` PROVED the spec's clause of
    gold at that input, so the assumed violation collapsed and ``False`` is
    unreachable. The failure now reports that gold satisfies the spec, which is
    what a reject case's gold-side build is supposed to report.

OPPOSITE-CLAIM CONTROL for the repair, same input and the same tactic, asserting
that the clause the witness says is violated is SATISFIED — e.g.
``(implementation_alignedOffsets [(30, 5), (60, 10)] 84 "right").2.2 =
List.map (fun hd => 84 - hd.1 + hd.2) [(30, 5), (60, 10)]`` by ``norm_num
+decide [implementation_alignedOffsets, maxList]``. All four build against the
frozen solution (exit 0) and all four FAIL against their own rival (exit 1,
``unsolved goals ⊢ False``). Gold's exit code now inverts with the claim under the
witness's own script, which is exactly what the old ``rfl`` step could not do. The
stronger flipped claim was rebuilt too — the full ``problem_spec_alignedOffsets``
predicate at all four inputs, discharged from the four clause slots — and it
verifies against gold in one build (exit 0), so gold provably satisfies the spec at
every repaired point and each witness's ``¬ …`` is FALSE of gold by proof and not
only by exit code.

No rival was touched: all four are genuinely wrong impls (each fails the frozen
tactic script and each is refuted by its repaired witness), so the defect was in
the witnesses' evidence, not in the attacks. Nothing in the accept lane, the six
sound witnesses or ``Solution.lean`` changed. The carrier note above still holds
for ``_wit``'s six users and is now the reason the two helpers differ: leaving the
arithmetic UNEVALUATED is what makes a ``rfl`` rewrite work against the rival, and
it is also what makes the same rewrite uninformative against gold whenever the two
tuples differ in a rational sum — so the six cases whose gold value reduces to
literals keep ``rfl``, and the four whose value does not are stated over ``norm_num``.

AXIOM lane: the nagini ``AXIOM_TESTS`` (``ax-deepmodel-sound``,
``ax-deepmodel-containment``) are DROPPED — the axiom lane is G-AX's job and this
gate ignores it. This bundle has no axiom to validate in any case: the axioms
region is empty, the extent reduction is reproduced concretely, and G-AX is a skip
stub.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24570"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Every one lies ENTIRELY inside the impl region (or, for
# `_PROOF_HEAD`, the proof region) and is unique in the file — asserted by
# `_swap` at import, so any drift in the frozen solution breaks this manifest
# loudly rather than silently retargeting a case.
# ---------------------------------------------------------------------------

# The whole frozen dispatch cascade, used by cases that restructure it wholesale.
_BODY = (
    '  if align == "baseline" then\n'
    '    let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))\n'
    '    let descent := maxList (hdList.map (fun hd => hd.2))\n'
    '    let h := heightDescent + descent\n'
    '    return (h, descent, hdList.map (fun _ => (0 : Rat)))\n'
    '  else if align == "left" || align == "bottom" then\n'
    '    return (height, 0, hdList.map (fun hd => hd.2))\n'
    '  else if align == "right" || align == "top" then\n'
    '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))\n'
    '  else\n'
    '    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))'
)

# The three individual non-baseline arms, and the baseline arm's descent binding.
_LOW = ('  else if align == "left" || align == "bottom" then\n'
        '    return (height, 0, hdList.map (fun hd => hd.2))')
_HIGH = ('  else if align == "right" || align == "top" then\n'
         '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))')
_CENTER = ('  else\n'
           '    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))')
_BASE_DESCENT = '    let descent := maxList (hdList.map (fun hd => hd.2))'

# The impl signature line + first dispatch test, for a case that prepends a
# binding ahead of the whole cascade.
_IMPL_HEAD = (
    'def implementation_alignedOffsets\n'
    '    (hdList : List (Rat × Rat)) (height : Rat) (align : String) :\n'
    '    Rat × Rat × List Rat := Id.run do\n'
    '  if align == "baseline" then'
)

# The frozen proof body's opening `intro`, for the admissibility ground instance.
_PROOF_HEAD = '  intro hdList height align _hv'

# The WHOLE frozen proof body, for the two positives whose reshaped arithmetic is
# only PROPOSITIONALLY equal to the frozen spelling. The frozen script closes
# every clause by `rfl`, which reduces the branch dispatch, the `let` and the
# `List.map` but NOT a reassociated or `*(1/2)`-spelled rational sum; those need
# a congruence step under the map plus `ring`. Re-proving inside the proof region
# is admissible (`variant_scope` permits it, the theorem STATEMENT stays
# byte-identical, and no axiom / `sorry` / assumption token is introduced), and it
# is the honest thing to do: the obligation is discharged for the new impl shape
# rather than inherited from the frozen one.
_PROOF_BODY = (
    '  intro hdList height align _hv\n'
    '  refine ⟨fun hc => ?_, fun hc => ?_, fun hc => ?_, fun hc => ?_⟩\n'
    '  · subst hc; exact ⟨rfl, rfl, rfl⟩\n'
    '  · rcases hc with hc | hc <;> subst hc <;> exact ⟨rfl, rfl, rfl⟩\n'
    '  · rcases hc with hc | hc <;> subst hc <;> exact ⟨rfl, rfl, rfl⟩\n'
    '  · subst hc; exact ⟨rfl, rfl, rfl⟩'
)

# The re-proof: same four-clause skeleton, but the offsets conjunct of the two
# slack-bearing clauses is closed by `List.map_congr_left` + `ring` instead of by
# definitional `rfl`.
_PROOF_RING = (
    '  intro hdList height align _hv\n'
    '  refine ⟨fun hc => ?_, fun hc => ?_, fun hc => ?_, fun hc => ?_⟩\n'
    '  · subst hc; exact ⟨rfl, rfl, rfl⟩\n'
    '  · rcases hc with hc | hc <;> subst hc <;>\n'
    '      exact ⟨rfl, rfl, by simp [implementation_alignedOffsets]⟩\n'
    '  · rcases hc with hc | hc <;> subst hc <;>\n'
    '      refine ⟨rfl, rfl, ?_⟩ <;>\n'
    '      simp only [implementation_alignedOffsets, Id.run] <;>\n'
    '      exact List.map_congr_left (fun hd _ => by ring)\n'
    '  · subst hc\n'
    '    refine ⟨rfl, rfl, ?_⟩\n'
    '    simp only [implementation_alignedOffsets, Id.run]\n'
    '    exact List.map_congr_left (fun hd _ => by ring)'
)


# ---------------------------------------------------------------------------
# Witness helper.
#
# A reject witness states the spec predicate at ONE concrete input and refutes
# it. Mechanics, in order:
#
#   * `intro h` assumes the spec holds of the rival at that input;
#   * `clause` supplies the anchor equality that opens the violated clause's
#     implication arm, and `proj` selects the corrupted output component
#     (`.1` resolvedHeight, `.2.1` descent, `.2.2` offsets);
#   * the `show … from rfl` rewrite replaces the rival's application by its own
#     reduced tuple. Kernel `rfl` reduces the branch dispatch and the `List.map`
#     but NOT the rational arithmetic, so `offs` must carry the arithmetic
#     UNEVALUATED — pre-evaluating it makes this step fail against the rival too,
#     and the witness would then discriminate nothing;
#   * `norm_num` closes. `decide` cannot: it reduces the `Decidable` instance
#     rather than the value and gets stuck on `Rat`'s `.num` projection.
#
# No witness binds a hypothesis — every one is stated at literal inputs — so
# nothing is assumed about a carrier term and there is no consistency obligation.
#
# This helper is used by the SIX witnesses whose gold-side exit code was measured
# to turn on gold's VALUE (see AUDIT REPAIR 4). The other four use `_wit_eval`
# below, because for them the `show … from rfl` step is decided by reducibility
# rather than by value and its failure attests nothing.
# ---------------------------------------------------------------------------

def _wit(hd, height, align, clause, reduced, proj=".2.2", simp=""):
    return (
        f'example : ¬ problem_spec_alignedOffsets {hd} {height} "{align}"\n'
        f'    (implementation_alignedOffsets {hd} {height} "{align}") := by\n'
        f'  intro h\n'
        f'  have hx := ({clause}){proj}\n'
        f'  rw [show implementation_alignedOffsets {hd} {height} "{align}"\n'
        f'      = ({reduced}) from rfl] at hx\n'
        f'  norm_num{simp} at hx\n'
    )


# ---------------------------------------------------------------------------
# Witness helper, EVALUATING form (AUDIT REPAIR 4).
#
# Same argument as `_wit` — assume the spec of the rival at one concrete input,
# open the violated clause's arm, project the corrupted component — but the
# rival's application is NOT rewritten by a kernel `rfl`. Instead the clause
# instance itself is normalised by `norm_num +decide`, which decides the string
# dispatch (`+decide`; the default simp set does NOT reduce `align == "baseline"`
# on a String literal, measured) and then EVALUATES the rational arithmetic on
# both sides of the equation.
#
# Why the arithmetic has to be evaluated rather than left symbolic, which is the
# opposite of what `_wit`'s note prescribes: kernel `rfl` cannot reduce `Rat`
# `+`/`-`/`/` at all (`Rat.normalize` goes through `Nat.gcd`, which is
# well-founded), so at an input where the rival's tuple and gold's differ only in
# a rational SUM, `rfl` fails on gold because one side is STUCK, not because the
# values differ — measured directly: with `_wit`'s script the true-of-gold claim
# `implementation_alignedOffsets [(30, 5), (60, 10)] 84 "right" = (84, 0, [59, 34])`
# fails by `rfl` with the same `Type mismatch … ?m.35 = ?m.35` bytes as the
# rival's claim, although `#eval` prints exactly `(mkRat 84 1, mkRat 0 1,
# [mkRat 59 1, mkRat 34 1])`. `norm_num` does evaluate those sums (the carrier
# note's own measurement), so under this helper gold's build fails with
#
#     unsolved goals … hx : True ⊢ False
#
# i.e. the spec's clause was DISCHARGED for gold at that input and the refutation
# collapsed — the failure now says what it is supposed to say. Against the rival
# the same script normalises the clause to a false numeric equation and closes.
# ---------------------------------------------------------------------------

def _wit_eval(hd, height, align, clause, proj=".2.2"):
    return (
        f'example : ¬ problem_spec_alignedOffsets {hd} {height} "{align}"\n'
        f'    (implementation_alignedOffsets {hd} {height} "{align}") := by\n'
        f'  intro h\n'
        f'  have hx := ({clause}){proj}\n'
        f'  norm_num +decide [implementation_alignedOffsets, maxList] at hx\n'
    )


# The two reductions that stay symbolic because they reduce over the list rather
# than to a literal; `norm_num [maxList]` finishes them.
def _max_over(f, hd):
    return f'maxList (List.map (fun hd => {f}) {hd})'


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # implementations that MUST verify; if one cannot, the postcondition is
    # over-fit to the frozen spelling (SPEC-TOO-STRONG). Each keeps the
    # `theorem correct_alignedOffsets` statement byte-identical and closes with
    # the frozen tactic body unchanged — no helper lemma, no axiom, no
    # assumption token. Both were confirmed to elaborate with a real build.
    # =====================================================================
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        # The four-way dispatch is reordered to center / baseline / low-edge /
        # high-edge, so the anchor tested FIRST and the anchor reached by the
        # final `else` both change. Each arm still returns the same tuple for
        # its own anchor, and the anchor→rule assignment is a function of the
        # keyword, not of the arm's position in the cascade.
        "module": _swap(
            _BASE, _BODY,
            '  if align == "center" then\n'
            '    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))\n'
            '  else if align == "baseline" then\n'
            '    let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))\n'
            '    let descent := maxList (hdList.map (fun hd => hd.2))\n'
            '    let h := heightDescent + descent\n'
            '    return (h, descent, hdList.map (fun _ => (0 : Rat)))\n'
            '  else if align == "left" || align == "bottom" then\n'
            '    return (height, 0, hdList.map (fun hd => hd.2))\n'
            '  else\n'
            '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))',
        ),
        "rationale": "a correct impl whose dispatch cascade is REORDERED (the centered "
                     "anchor tested first, the far-edge rule moved into the final "
                     "`else`) must satisfy all four clauses (BASE)/(LOW)/(HIGH)/(CTR): "
                     "each anchor keyword still selects the same offset rule, resolved "
                     "height and descent, because the spec guards its clauses on the "
                     "keyword and not on cascade position. If it failed to verify the "
                     "postcondition would be over-fit to the frozen branch ORDER => "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body closes it "
                     "unchanged — the per-clause `subst`/`rcases` on the anchor still "
                     "reduces each arm to `rfl`.",
    },
    {
        "id": "pos-named-slack",
        "kind": "soundness",
        "expect": "verify",
        # The two slack-bearing rules compute the leftover extent through a named
        # local inside the mapped function rather than inline. Identical
        # arithmetic, a different code shape for exactly the two rules whose
        # value depends on the leftover extent.
        "module": _swap(
            _swap(
                _BASE, _HIGH,
                '  else if align == "right" || align == "top" then\n'
                '    return (height, 0, hdList.map (fun hd =>\n'
                '      let slack := height - hd.1\n'
                '      slack + hd.2))',
            ),
            _CENTER,
            '  else\n'
            '    return (height, 0, hdList.map (fun hd =>\n'
            '      let slack := height - hd.1\n'
            '      slack / 2 + hd.2))',
        ),
        "rationale": "a correct impl that binds the leftover extent to a named local "
                     "inside the mapped function and reuses it in the far-edge "
                     "(`slack + descent`) and centered (`slack / 2 + descent`) rules — "
                     "identical arithmetic, a different shape for precisely the two "
                     "clauses (HIGH) and (CTR) whose value depends on that extent. If "
                     "it failed the spec would be over-fit to the inline "
                     "`height - boxHeight` spelling => SPEC-TOO-STRONG. Proof: the "
                     "frozen tactic body closes it unchanged (the `let` is definitional, "
                     "so each arm still reduces to `rfl`).",
    },

    {
        "id": "pos-reassociated-arithmetic",
        "kind": "soundness",
        "expect": "verify",
        # The two positives above are, on this carrier, DEFINITIONALLY equal to
        # the frozen impl: `rfl` alone closes `implNamedSlack =
        # implementation_alignedOffsets` and the reordered dispatch reduces to the
        # frozen one at every anchor by iota. So each is closed by the frozen
        # script for free, and neither exercises the spec's arithmetic at all.
        # This positive is deliberately NOT definitional: the far-edge rule is
        # reassociated to `height + descent - boxHeight` and the centered rule
        # multiplies by `1/2` rather than dividing by 2 (which is how the modeled
        # surface spells the halving). Both are ring-equal to the frozen
        # arithmetic but not reducible to it, so the offsets conjunct genuinely
        # has to be RE-PROVEN under the map.
        "module": _swap(
            _swap(
                _swap(
                    _BASE, _HIGH,
                    '  else if align == "right" || align == "top" then\n'
                    '    return (height, 0, hdList.map (fun hd => height + hd.2 - hd.1))',
                ),
                _CENTER,
                '  else\n'
                '    return (height, 0, hdList.map (fun hd => (height - hd.1) * (1/2) + hd.2))',
            ),
            _PROOF_BODY, _PROOF_RING,
        ),
        "rationale": "a correct impl whose two slack-bearing rules are spelled with "
                     "REASSOCIATED arithmetic — far edge as `height + descent - "
                     "boxHeight`, centered as `(height - boxHeight) * (1/2) + descent` "
                     "— must satisfy (HIGH) and (CTR), because the spec pins the offset "
                     "VALUE and both spellings are ring-equal to it. Unlike the two "
                     "positives above (each definitionally equal to the frozen impl, so "
                     "the frozen `rfl` script closes them for free) this one is NOT "
                     "reducible to the frozen spelling: measured, the frozen tactic body "
                     "fails on it with `rfl ... expected to have type (…).2.2 = "
                     "List.map (fun hd => height - hd.1 + hd.2) hdList`. It therefore "
                     "RE-PROVES the obligation in the proof region — same four-clause "
                     "skeleton, the offsets conjunct closed by `List.map_congr_left` + "
                     "`ring` — with the theorem statement byte-identical and no axiom, "
                     "`sorry` or assumption token. Verifies. If a faithful ring-equal "
                     "reshape could NOT be proven, the spec would be over-fit to the "
                     "frozen ARITHMETIC SPELLING rather than to the offset value => "
                     "SPEC-TOO-STRONG. This is the positive that makes the soundness "
                     "lane test the spec instead of testing zeta/iota reduction.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, layout-shaped
    # input rather than only provable in the abstract, and its one precondition
    # is ESTABLISHABLE at a concrete anchor. Nagini's version asserts its four
    # `Requires` clauses are usable; the only precondition here is the
    # anchor-membership hypothesis, so this discharges that hypothesis AND the
    # full spec predicate at a ground input, then closes the frozen obligation
    # verbatim. Nothing is assumed: no new declaration, the theorem statement is
    # byte-identical, and both ground facts are `have`s inside the existing
    # tactic body.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_HEAD,
            '  have _anchor : validAlign "top" := by\n'
            '    unfold validAlign; decide\n'
            '  have _ground : problem_spec_alignedOffsets [(30, 5), (60, 10)] 60 "top"\n'
            '      (implementation_alignedOffsets [(30, 5), (60, 10)] 60 "top") := by\n'
            '    refine ⟨fun hc => absurd hc (by decide), fun hc => ?_, fun _ => ⟨rfl, rfl, rfl⟩,\n'
            '            fun hc => absurd hc (by decide)⟩\n'
            '    rcases hc with hc | hc <;> exact absurd hc (by decide)\n'
            '  intro hdList height align _hv',
        ),
        "rationale": "the precondition is DISCHARGED at a concrete anchor (`validAlign` "
                     "holds of a far-edge keyword) and the whole spec predicate is then "
                     "discharged at a ground layout-shaped input — two boxes of "
                     "differing extent, both carrying a descent, inside an intended "
                     "total equal to the taller box — before the frozen obligation is "
                     "closed verbatim. Verifies. If the precondition could not be "
                     "established for a legal anchor, or the predicate were "
                     "unsatisfiable at a normal input, that is PRECOND-TOO-STRONG "
                     "(a spec no admissible input reaches proves nothing).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real change would NOT resolve, so a verifying
    # rival is a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation `witness` pinning the violation at one
    # concrete input, each SEEN to elaborate against its rival and fail against
    # the frozen solution.
    #
    # Ordered: the four that attack the offsets list of a specific clause, then
    # the two that attack the descent and resolved-height components — the
    # output positions a purely offsets-focused battery would leave unprobed.
    # =====================================================================
    {
        "id": "rival-anchor-group-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # The two vertical anchors select each other's offset rule: the anchor
        # that must sit flush with the low edge gets the far-edge rule and vice
        # versa. This IS the pre-change grouping.
        "module": _swap(
            _BASE, _LOW + "\n" + _HIGH,
            '  else if align == "left" || align == "top" then\n'
            '    return (height, 0, hdList.map (fun hd => hd.2))\n'
            '  else if align == "right" || align == "bottom" then\n'
            '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))',
        ),
        "refinement": "this is exactly the pre-change anchor→rule grouping (the shape "
                      "`Solution_prepatch.lean` carries). The anchor-parameterized "
                      "layout assertions require the low-edge vertical anchor to place "
                      "each box at its own descent and the high-edge vertical anchor to "
                      "place it against the far edge; this rival gives each the OTHER "
                      "value, so BOTH of the two currently-failing assertions still "
                      "fail — with the offsets not merely wrong but swapped, which is "
                      "the observable the reported defect describes. It does NOT "
                      "resolve; it is the unresolved starting state.",
        "rationale": "REJECT from clause (LOW) (align ∈ {left,bottom} → offsets = each "
                     "box's own descent) and, symmetrically, clause (HIGH). At a "
                     "low-edge anchor the rival returns the far-edge value "
                     "`height - boxHeight + descent` where the spec requires `descent`; "
                     "the two differ whenever the box does not already fill the extent. "
                     "If it verified => SPEC-TOO-WEAK (the spec would admit the "
                     "pre-change grouping and could not see the defect at all).",
        "witness": _wit("[(30, 5), (60, 10)]", "60", "bottom",
                        "h.2.1 (Or.inr rfl)",
                        "60, 0, [60 - 30 + 5, 60 - 60 + 10]"),
    },
    {
        "id": "rival-splits-low-group-left",
        "kind": "uniqueness",
        "expect": "reject",
        # The (LOW) group is SPLIT: the vertical anchor keeps the own-descent rule
        # and the HORIZONTAL one is given the far-edge rule. Every other rival
        # treats each anchor group as an atom, and every other witness enters at a
        # vertical anchor (`bottom`/`top`), `center` or `baseline` — so before this
        # case nothing in the battery ever evaluated the spec at `left` or
        # `right`, and a rival corrupting only a horizontal anchor would verify.
        "module": _swap(
            _BASE, _LOW,
            '  else if align == "bottom" then\n'
            '    return (height, 0, hdList.map (fun hd => hd.2))\n'
            '  else if align == "left" then\n'
            '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))',
        ),
        "refinement": "a faithful change that keeps the two anchors of the own-descent "
                      "group on DIFFERENT rules — the vertical one offset by its own "
                      "descent, the horizontal one flushed against the far edge — is a "
                      "regression on an anchor the accepted change leaves alone, and one "
                      "the anchor-parameterized layout assertions cannot see: they "
                      "exercise the two VERTICAL anchors, which this rival gets right. "
                      "The horizontal anchor's own assertion is currently passing and "
                      "expects the own-descent value, so it would start failing: the "
                      "change does NOT resolve. It matters because the grouping is the "
                      "whole discriminating content of the modeled change, and a battery "
                      "that only ever probes the two anchors that moved would license "
                      "silently breaking the two that stayed.",
        "rationale": "REJECT from clause (LOW) (align ∈ {left,bottom} → offsets = each "
                     "box's own descent), entered at its FIRST disjunct. The clause is a "
                     "disjunctive guard, so it must hold of BOTH anchors; the witnesses "
                     "that enter (LOW)/(HIGH) via `Or.inr` reach only the vertical "
                     "anchor, and this case is the one that discharges (LOW) via "
                     "`Or.inl`. Its witness is stated at the horizontal anchor `left`, at "
                     "a slack-bearing total (100) where the own-descent and far-edge "
                     "rules genuinely differ. Without it the `left` half of the (LOW) "
                     "guard is never evaluated by any case => a rival splitting THAT "
                     "group would be SPEC-TOO-WEAK-invisible. The mirror half of (HIGH) "
                     "is covered by `rival-splits-high-group-right`, not by this case.",
        "witness": _wit("[(30, 5), (60, 10)]", "100", "left",
                        "h.2.1 (Or.inl rfl)",
                        "100, 0, [100 - 30 + 5, 100 - 60 + 10]"),
    },
    {
        "id": "rival-splits-high-group-right",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR of the case above, on the other group: (HIGH) is SPLIT, its
        # vertical anchor keeping the far-edge rule while the HORIZONTAL one is
        # given the own-descent rule. Added by audit: with the low group's split
        # covered but not the high group's, `right` was still the one legal anchor
        # no witness ever reached, so the `Or.inl` half of the (HIGH) guard was
        # never evaluated and a rival corrupting only `right` would have verified.
        "module": _swap(
            _BASE, _HIGH,
            '  else if align == "top" then\n'
            '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))\n'
            '  else if align == "right" then\n'
            '    return (height, 0, hdList.map (fun hd => hd.2))',
        ),
        "refinement": "a faithful change that keeps the two anchors of the far-edge group "
                      "on DIFFERENT rules — the vertical one flushed against the far edge, "
                      "the horizontal one offset by its own descent — is a regression on an "
                      "anchor the accepted change leaves alone, and the mirror image of "
                      "`rival-splits-low-group-left`. The anchor-parameterized layout "
                      "assertions exercise the two VERTICAL anchors, which this rival gets "
                      "right, so they cannot see it; the horizontal anchor's own assertion "
                      "is currently passing and expects the far-edge value, so it would "
                      "start failing and the change does NOT resolve. Both group splits "
                      "have to be attacked, not just one: the grouping is the whole "
                      "discriminating content of the modeled change, and covering only the "
                      "own-descent group's horizontal anchor would still license silently "
                      "breaking the far-edge group's.",
        "rationale": "REJECT from clause (HIGH) (align ∈ {right,top} → offsets = "
                     "height - boxHeight + descent), entered at its FIRST disjunct. This "
                     "is the only case that discharges the (HIGH) guard via `Or.inl`, and "
                     "its witness is the only one stated at `right` — the one legal anchor "
                     "no other witness reaches. Its total (84) is slack-bearing for both "
                     "boxes, so the own-descent value the rival emits and the far-edge "
                     "value the clause requires genuinely differ. Without it the `right` "
                     "half of the (HIGH) guard is an unevaluated disjunct => a rival "
                     "splitting the far-edge group would be SPEC-TOO-WEAK-invisible.",
        # `_wit_eval`, not `_wit`: at total 84 the far-edge offsets are rational
        # SUMS, which kernel `rfl` cannot reduce, so `_wit`'s `show … from rfl`
        # failed on gold for being stuck rather than for differing — measured, the
        # true-of-gold claim `= (84, 0, [59, 34])` failed with the same bytes.
        "witness": _wit_eval("[(30, 5), (60, 10)]", "84", "right",
                             "h.2.2.1 (Or.inl rfl)"),
    },
    {
        "id": "rival-high-edge-halves-slack",
        "kind": "uniqueness",
        "expect": "reject",
        # The far-edge anchors use the CENTERED rule, halving the leftover
        # extent — as if those anchors centered the box rather than flushing it
        # against the far edge.
        "module": _swap(
            _BASE, _HIGH,
            '  else if align == "right" || align == "top" then\n'
            '    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))',
        ),
        "refinement": "a faithful change computing the high-edge offset as half the "
                      "leftover extent plus the descent, rather than the full leftover "
                      "extent, places the box at the track MIDPOINT instead of flush "
                      "against the far edge. The layout assertion for that anchor "
                      "expects the full extent difference, so its per-box closeness "
                      "check fails on the shorter box — it does NOT resolve. Note it "
                      "would also make the far-edge anchor indistinguishable from the "
                      "centered one, collapsing two documented behaviors into one.",
        "rationale": "REJECT from clause (HIGH) (align ∈ {right,top} → offsets = "
                     "height - boxHeight + descent): this rival gives "
                     "(height - boxHeight)/2 + descent, differing by half the leftover "
                     "extent. A deliberate NEAR-MISS — it agrees with the frozen "
                     "behavior on every box that already fills the extent (zero slack) "
                     "and on the descent contribution — so its witness is stated at a "
                     "slack-bearing input (intended total 100, boxes of extent 30 and "
                     "60), which is the sub-domain where it is actually wrong — at a "
                     "total equal to the taller box the halved and full slack rules "
                     "AGREE and the witness would discriminate nothing. It is the only "
                     "witness at the pair (`top`, total 100); other witnesses are also "
                     "slack-bearing, but each at a different anchor, so none of them "
                     "enters (HIGH) via `Or.inr` where this rival is wrong. If it "
                     "verified => SPEC-TOO-WEAK.",
        # `_wit_eval`, not `_wit`: gold's far-edge offsets at total 100 are the
        # rational sums `[100 - 30 + 5, 100 - 60 + 10]`, which kernel `rfl` cannot
        # reduce, so `_wit`'s gold-side failure was stuck rather than differing —
        # measured, the true-of-gold claim `= (100, 0, [75, 50])` failed with the
        # same bytes as the rival's halved-slack claim.
        "witness": _wit_eval("[(30, 5), (60, 10)]", "100", "top",
                             "h.2.2.1 (Or.inr rfl)"),
    },
    {
        "id": "rival-low-edge-drops-descent",
        "kind": "uniqueness",
        "expect": "reject",
        # The own-descent anchors emit zero for every box, collapsing each box's
        # descent contribution.
        "module": _swap(
            _BASE, _LOW,
            '  else if align == "left" || align == "bottom" then\n'
            '    return (height, 0, hdList.map (fun _ => (0 : Rat)))',
        ),
        "refinement": "a faithful change emitting a flat zero for the own-descent "
                      "anchor group instead of each box's descent would NARROWLY pass "
                      "the currently-failing assertions, because the geometry those "
                      "assertions construct has ZERO descents on every box — so zero "
                      "and the descent coincide there. It is still not the accepted "
                      "behavior: the surface is documented to offset each box by its "
                      "own descent, the already-passing assertion for the horizontal "
                      "anchor in the same group pins the same rule, and every layout "
                      "that drives boxes with real descenders (text) would be "
                      "misplaced. This is the rival whose faithful patch is closest to "
                      "passing while being wrong, which is exactly why the spec must "
                      "pin ALL boxes rather than only the zero-descent ones.",
        "rationale": "REJECT from clause (LOW) (align ∈ {left,bottom} → offsets = each "
                     "box's own descent): the rival returns zero, violating the clause "
                     "whenever any box has a nonzero descent. The value-domain attack "
                     "hiding behind the shipped geometry's zero descents, so its "
                     "witness is deliberately stated at a nonzero-descent input — "
                     "boxes `[(30,0),(60,9)]`, with the descent on the SECOND box only, "
                     "a shape no other witness uses. A witness copied from the layout "
                     "geometry would not discriminate this rival at all. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _wit("[(30, 0), (60, 9)]", "60", "bottom",
                        "h.2.1 (Or.inr rfl)", "60, 0, [0, 0]"),
    },
    {
        "id": "rival-partial-domain-first-box",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every box EXCEPT the first, where it emits zero. The frozen
        # impl maps uniformly over the list, so the faithful re-expression of
        # nagini's index-0 attack destructures the list and zeroes the head.
        "module": _swap(
            _BASE, _LOW,
            '  else if align == "left" || align == "bottom" then\n'
            '    match hdList with\n'
            '    | []           => return (height, 0, [])\n'
            '    | _ :: rest    => return (height, 0, 0 :: rest.map (fun hd => hd.2))',
        ),
        "refinement": "a faithful change correct on every box but the FIRST, which it "
                      "offsets by zero — a fence-post slip treating the leading box as "
                      "the reference. For the low-edge anchor the first box's required "
                      "offset is its own descent, so any layout whose leading box "
                      "carries a descent places it wrongly while every following box is "
                      "correct; the per-box closeness check fails on element 0 and the "
                      "change does NOT resolve. It also silently mis-sizes any "
                      "single-box layout, where element 0 is the whole result.",
        "rationale": "the PARTIAL-DOMAIN attack: pins every element but index 0. "
                     "REJECT from clause (LOW), whose equation `offsets = hdList.map "
                     "(fun hd => hd.2)` covers the head as much as the tail — a clause "
                     "stated over the tail only would be too weak here. The witness "
                     "input `[(40,7),(60,0)]` is chosen so the descent is nonzero at "
                     "index 0 ONLY: with the shipped geometry's `[0,_]` descents the "
                     "rival's zero would AGREE with the frozen behavior at index 0 and "
                     "the witness would not discriminate. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit("[(40, 7), (60, 0)]", "60", "bottom",
                        "h.2.1 (Or.inr rfl)", "60, 0, [0, 0]"),
    },
    {
        "id": "rival-center-full-slack",
        "kind": "uniqueness",
        "expect": "reject",
        # The centered anchor uses the far-edge rule, flushing the box instead of
        # centering it. Attacks the clause the modeled change does NOT touch.
        "module": _swap(
            _BASE, _CENTER,
            '  else\n'
            '    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))',
        ),
        "refinement": "a faithful change that gives the centered anchor the far-edge "
                      "rule — the full leftover extent instead of half of it — is a "
                      "REGRESSION on an anchor the accepted change leaves alone. Its "
                      "layout assertion is currently passing and expects half the "
                      "extent difference, so it would start failing: the change does "
                      "not resolve, it breaks a behavior that already worked. This is "
                      "the mirror image of `rival-high-edge-halves-slack` and matters "
                      "because a spec that pinned only the two clauses the change "
                      "touches would license exactly this collateral damage.",
        "rationale": "REJECT from clause (CTR) (align = center → offsets = "
                     "(height - boxHeight)/2 + descent): the rival returns the full "
                     "`height - boxHeight + descent`. Attacks the clause guarding the "
                     "one anchor no other rival enters, so it is the case that makes "
                     "(CTR) a tested clause rather than an unexercised conjunct. Its "
                     "witness is the only one at the centered anchor, and uses a fourth "
                     "intended total (72) so the halving is visible. If it verified => "
                     "SPEC-TOO-WEAK on the anchors outside the change's blast radius.",
        # `_wit_eval`, not `_wit`: the centered rule DIVIDES, and `Rat` division is
        # the one operation the gate's own stuck-reduction note calls out as
        # kernel-irreducible, so `_wit`'s `show … from rfl` failed on gold for being
        # stuck — measured, `((72 : Rat) - 30) / 2 + 5 = 26` itself fails by `rfl`.
        "witness": _wit_eval("[(30, 5), (60, 10)]", "72", "center",
                             "h.2.2.2 rfl"),
    },
    {
        "id": "rival-baseline-descent-component",
        "kind": "uniqueness",
        "expect": "reject",
        # The recomputed packing descent reduces over each box's ABOVE-baseline
        # extent rather than its descent. Attacks the DESCENT component of the
        # one clause that recomputes anything.
        "module": _swap(
            _BASE, _BASE_DESCENT,
            '    let descent := maxList (hdList.map (fun hd => hd.1 - hd.2))',
        ),
        "refinement": "a faithful change reducing the recomputed packing descent over "
                      "each box's above-baseline extent instead of its descent reports "
                      "the wrong descent for the baseline anchor, and — because that "
                      "same value also feeds the recomputed total — the wrong total "
                      "extent too. The baseline anchor's layout assertion checks the "
                      "reported extents directly and is currently PASSING, so this "
                      "change makes it fail: it does not resolve. Baseline is also the "
                      "default anchor, so the misreport propagates to every layout that "
                      "never names an anchor at all.",
        "rationale": "REJECT from clause (BASE) (align = baseline → descent = the "
                     "maximal box descent). The only rival attacking the DESCENT "
                     "component of the baseline clause, and the only one entering that "
                     "clause at all — without it (BASE) is an unexercised conjunct and "
                     "a rival corrupting the recomputation would verify. The witness "
                     "reduction stays symbolic over `maxList` (the reduction is over "
                     "the list, not to a literal) and `norm_num [maxList]` closes it. "
                     "If it verified => SPEC-TOO-WEAK on the recomputed components.",
        # `_wit_eval`, not the hand-written `show … from rfl` this case used to
        # carry: the recomputed descent reduces over `hd.1 - hd.2`, a rational
        # DIFFERENCE, so `maxList` gets stuck on `Rat`'s comparison and the
        # rewrite failed on gold for being stuck rather than for differing —
        # measured, the true-of-gold claim `84 "baseline" = (60, 10, [0, 0])`
        # failed with the same bytes although `#eval` prints exactly
        # `(mkRat 60 1, mkRat 10 1, [mkRat 0 1, mkRat 0 1])`. Under `_wit_eval`
        # `norm_num +decide` evaluates both maxima and gold's build reports
        # `hx : True ⊢ False`.
        "witness": _wit_eval("[(30, 5), (60, 10)]", "84", "baseline",
                             "h.1 rfl", ".2.1"),
    },
    {
        "id": "rival-recomputes-resolved-height",
        "kind": "uniqueness",
        "expect": "reject",
        # The intended total is discarded and recomputed from the box extents for
        # EVERY anchor, not only the one clause that specifies a recomputation.
        # Attacks the resolvedHeight component.
        "module": _swap(
            _BASE, _IMPL_HEAD,
            'def implementation_alignedOffsets\n'
            '    (hdList : List (Rat × Rat)) (height : Rat) (align : String) :\n'
            '    Rat × Rat × List Rat := Id.run do\n'
            '  let height := maxList (hdList.map (fun hd => hd.1 - hd.2))\n'
            '                  + maxList (hdList.map (fun hd => hd.2))\n'
            '  if align == "baseline" then',
        ),
        "refinement": "a faithful change hoisting the extent recomputation ahead of the "
                      "anchor dispatch discards the intended total the caller passed "
                      "in, for every anchor. The surface is documented to return a "
                      "caller-supplied total unchanged (it is returned without checking "
                      "that it is large enough), and the callers depend on that: a "
                      "container given an explicit extent would silently shrink it to "
                      "the boxes' own, changing the reported extents of every nested "
                      "layout and the offsets that derive from them. Currently-passing "
                      "extent assertions would fail, so the change does NOT resolve — "
                      "and because the recomputed value coincides with the intended one "
                      "whenever the caller passes exactly the boxes' extent, the "
                      "breakage is invisible on the simplest layouts.",
        "rationale": "REJECT from the resolvedHeight conjunct of clause (LOW) "
                     "(align ∈ {left,bottom} → resolvedHeight = height), and equally of "
                     "(HIGH) and (CTR). This is the frame-discipline case on a "
                     "referentially transparent carrier (spec_guide §0.5): the spec "
                     "pins an output component to an INPUT, and this rival overwrites "
                     "it. Without this case that conjunct is never probed and any rival "
                     "reporting a plausible-but-wrong total would verify. The witness "
                     "is stated at an intended total (100) that exceeds the recomputed "
                     "one, since at a total equal to the boxes' extent the two agree. "
                     "If it verified => SPEC-TOO-WEAK on the resolved extent.",
        "witness": (
            'example : ¬ problem_spec_alignedOffsets [(30, 5), (60, 10)] 100 "bottom"\n'
            '    (implementation_alignedOffsets [(30, 5), (60, 10)] 100 "bottom") := by\n'
            '  intro h\n'
            '  have hx := (h.2.1 (Or.inr rfl)).1\n'
            '  rw [show implementation_alignedOffsets [(30, 5), (60, 10)] 100 "bottom"\n'
            f'      = ({_max_over("hd.1 - hd.2", "[(30, 5), (60, 10)]")}\n'
            f'           + {_max_over("hd.2", "[(30, 5), (60, 10)]")},\n'
            '         0, List.map (fun hd => hd.2) [(30, 5), (60, 10)]) from rfl] at hx\n'
            '  norm_num [maxList] at hx\n'
        ),
    },
    {
        "id": "rival-leaks-descent-component",
        "kind": "uniqueness",
        "expect": "reject",
        # The three non-baseline anchors report the maximal box descent instead of
        # the zero packing descent the spec requires. Attacks the descent
        # component of the three clauses that pin it to zero.
        "module": _swap(
            _swap(
                _swap(
                    _BASE, _LOW,
                    _LOW.replace(
                        '(height, 0,',
                        '(height, maxList (hdList.map (fun hd => hd.2)),'),
                ),
                _HIGH,
                _HIGH.replace(
                    '(height, 0,',
                    '(height, maxList (hdList.map (fun hd => hd.2)),'),
            ),
            _CENTER,
            _CENTER.replace(
                '(height, 0,',
                '(height, maxList (hdList.map (fun hd => hd.2)),'),
        ),
        "refinement": "a faithful change reporting the maximal box descent from the "
                      "three anchors that must report none leaks a baseline-only "
                      "quantity into the anchored modes. The reported descent is what "
                      "the enclosing layout uses to position the whole group, so every "
                      "nested container using an anchored mode would be shifted by that "
                      "amount; the extent assertions for those anchors are currently "
                      "PASSING and check the reported descent directly, so they would "
                      "start failing and the change does NOT resolve. It is invisible "
                      "on any layout whose boxes all have zero descent — which is "
                      "precisely the geometry the anchor assertions construct — so the "
                      "spec's zero-descent conjunct is what rules it out, not the tests.",
        "rationale": "REJECT from the descent conjunct `result.2.1 = 0` of clause "
                     "(HIGH) (align ∈ {right,top}), and equally of the identical "
                     "conjunct `result.2.1 = 0` in clauses (LOW) and (CTR) — this one "
                     "rival violates all three, since it leaks the maximal box descent "
                     "from every non-baseline anchor. The second frame-discipline "
                     "case: an output component the "
                     "spec pins to a constant, which an offsets-only battery would "
                     "leave unprobed — and unlike the resolved-height rival this one "
                     "corrupts a value with no input to trace it to, so it is the "
                     "shape a wrong impl can most easily hide in. Refuted at a "
                     "nonzero-descent input, since with all-zero descents the leaked "
                     "maximum IS zero and the rival agrees with the frozen behavior. "
                     "If it verified => SPEC-TOO-WEAK on the reported descent.",
        "witness": (
            'example : ¬ problem_spec_alignedOffsets [(30, 5), (60, 10)] 60 "top"\n'
            '    (implementation_alignedOffsets [(30, 5), (60, 10)] 60 "top") := by\n'
            '  intro h\n'
            '  have hx := (h.2.2.1 (Or.inr rfl)).2.1\n'
            '  rw [show implementation_alignedOffsets [(30, 5), (60, 10)] 60 "top"\n'
            f'      = (60, {_max_over("hd.2", "[(30, 5), (60, 10)]")},\n'
            '         List.map (fun hd => 60 - hd.1 + hd.2) [(30, 5), (60, 10)]) from rfl] at hx\n'
            '  norm_num [maxList] at hx\n'
        ),
    },
]

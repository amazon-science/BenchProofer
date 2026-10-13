"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24149 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant sharing the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the single ``theorem correct_safeRepresentative`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts TWO structurally-identical functions with fractional-permission
contracts (``select_position_x0`` / ``select_position_xconv``) over a
``List[int]`` finiteness-FLAG abstraction, with three separate postcondition
clauses (P1 identity, P2 totality, F frame) plus a ``MustTerminate`` clause
(P3) and two ``@ContractOnly`` callee axioms. This Lean bundle models the SAME
single behavior — both nagini functions were already "one modeled behavior" —
but on a DEEPER carrier: the values themselves (``List Float``, not flags), the
finiteness test as a real predicate, the SHAPE of the coordinate argument
(``CoordArg``), and the selection spelled out rather than axiomatized. So the
nagini clauses collapse into ONE grounded equation, and several nagini cases
lose their target entirely. Every nagini case's disposition is recorded in the
module ``assessment``.

DEFENDED SURFACE (one modeled obligation). The result is exactly the
representative chosen for the coordinate argument, pinned by a single grounded
equation ``result = chooseRepresentative arg``. The argument's SHAPE is part of
the carrier, so the equation has these independent input-selected clauses:

  * the LONE-VALUE clause — when the argument is a single coordinate value
    rather than a sequence, that value stands for itself UNCONDITIONALLY, and
    in particular no finiteness test is applied to it and a representative is
    always available;
  * the FINITE-SEARCH clause — when the argument is a sequence some of whose
    values COUNTS AS FINITE, the representative is the FIRST such value
    (positionally leftmost), not merely some counting value and not the
    sequence's leading value. Counting as finite is settled per REGIME and not by
    arithmetic alone: a value the test can weigh as a quantity counts exactly
    when it is finite; a value the test CANNOT weigh counts REGARDLESS, so the
    search does not pass it over; a MISSING value never counts;
  * the FALL-BACK clause (the clause under repair) — when the argument is a
    sequence in which NO value counts as finite but which is non-empty, a
    representative is still produced, and it is the sequence's OWN first value,
    whatever regime that value belongs to;
  * the UNSEARCHED-SEQUENCE clause — when the argument is a sequence of the
    kind the search does NOT run over, the representative is its LEADING value,
    taken directly and unconditionally: no finiteness test bears on that value,
    so it is taken even when it does not count and even when some later value
    would have counted. Which of the two sequence shapes an argument has is
    settled by WHAT KIND of thing it is and never by which values it holds;
  * the EMPTY clause — no representative at all exactly when there is a
    sequence with nothing to select from, of whichever of the two sequence
    shapes.

The BEHAVIOURAL DISCRIMINATOR (the change): the non-empty SEQUENCE in which no
value counts as finite must yield a representative rather than none. Pre-change, the
finite search exhausted the sequence and no representative was produced, which
propagated out of the surrounding conversion step as a failure instead of a
value. The ``weak-no-fallback`` rival below IS that pre-change behavior.

WHY THE KIND OF SEQUENCE IS PART OF THE CARRIER (the third repair). Both earlier
revisions carried ONE sequence shape, i.e. modeled the step as though every
coordinate sequence were searched value by value for the first one that counts.
That was measured to be too strong. The selection the step performs dispatches on
WHAT KIND of argument it received, and one of the kinds it recognises is a
sequence it does NOT search: for such a sequence it reads the LEADING position
directly and the per-value test is not consulted at all — the unchanged helper
carries a standing note that the filtering remains to be done for that kind. A
carrier with a single sequence shape has no image of that kind, so it forces the
search onto it, and the resulting equation PREDICTS a value the real step does not
produce: where the real step yields the leading value, the model demands a later
one. MEASURED (the real helpers reconstructed from the base worktree at the
recorded commit, and independently through the public plotting entry point): for a
sequence of that kind whose leading value does not count and whose next value is
an ordinary finite number, the step selects the LEADING one and the extent that
the coordinate-plus-offset arithmetic computes is non-finite, whereas the
list-shaped sequence with the same values selects the finite one and the extent is
finite. The two shapes are therefore observably different behaviors of the same
step, and the argument reaches the step in that shape verbatim: the entry point
hands the argument through unaltered, and the guard that precedes the selection
constrains a DIFFERENT one of the step's two arguments, so it does not exclude
this kind. An existing test of the unchanged helper drives exactly this kind of
argument and asserts the unfiltered leading value, so the kind is deliberately
supported rather than incidental. Carrying the KIND in the carrier is what lets
the equation state what the step guarantees for each kind instead of over-claiming
on one of them; the `weak-unsearched-searched` rival below probes that clause, and
it is the rival the previous carrier could not even express.

WHY EACH VALUE'S REGIME IS PART OF THE CARRIER (the second repair). A previous
revision carried the argument's SHAPE (see the next section) but modeled every
value inside a sequence as a NUMBER, i.e. as though the finiteness test were bare
arithmetic finiteness. That was measured to be too coarse in the same way the
shape had been. The test the step actually applies has THREE rulings, not one: it
weighs a value it can weigh as a quantity, it COUNTS a value it cannot weigh at
all rather than passing it over, and it refuses a value that is missing outright.
A carrier in which every sequence value is a number has no image of the second
and third regimes, so an implementation that substitutes bare arithmetic
finiteness for the real test is indistinguishable from the correct one on every
input the carrier can express — while diverging on exactly the sequences whose
values cannot be weighed, where the arithmetic test errors, the surrounding
handler absorbs that error, and the WHOLE SEQUENCE is left standing as its own
representative so that the coordinate-plus-offset arithmetic is discarded.
MEASURED (the test reconstructed verbatim from the unchanged helper): the two
tests agree on every plain number and disagree on a point in time, an elapsed
duration, an exactly-represented quantity, a text value, a whole vector in one
position, and an absent value. An existing regression test drives a sequence of
two time-valued coordinates directly into the search, which is why such an
implementation regresses the suite while still passing the F2P. Giving each value
a REGIME turns that divergence into a value the equation pins, which is what the
`weak-unweighable-skipped` and `weak-missing-counted` rivals below probe.

WHY THE ARGUMENT'S SHAPE IS PART OF THE CARRIER (the first repair). An earlier
revision of this bundle modeled the argument as a bare ``List Float``, i.e. as
though a coordinate argument were always a sequence. That carrier was measured
to be too coarse, and the measurement is the reason this manifest now carries a
LONE-VALUE clause and the ``weak-single-filtered`` rival. The surrounding
conversion step accepts a coordinate argument that is EITHER a sequence of
coordinates OR one lone coordinate, and the two shapes take different routes
through it: for a lone value the finiteness search over "the elements" does not
apply at all, and the lone value itself is what the arithmetic proceeds with,
whatever that value is — including when it is non-finite, and including when it
is not even a number (a date, say). Modeling only the sequence shape left that
whole regime unobserved, and a rival could therefore relocate WHEN the
fall-back selection happens — performing it up front for every argument rather
than only upon an exhausted search — while remaining indistinguishable on every
sequence. Measured: such a rival agrees with the correct behavior on every
sequence shape (all-non-finite, leading-non-finite, all-finite, empty) and
diverges on exactly and only the lone-value shape, where the correct behavior
yields that value and the rival yields no representative at all. Carrying the
shape in the carrier is what makes that divergence a VALUE the equation can
pin, which is why the two shapes are distinguished here rather than the
sequence case being generalised.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini U1, its "#1 weakness class") — VACUOUS
    here. Lean is referentially transparent: an input carries no heap
    permission, there is no read-only half-permission to overwrite, and no
    aliasing to exploit. The nagini rival (write into the read-only input before
    returning) has no expressible instance. No substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION (nagini U5) — NOT SHIPPABLE here, and the
    reason is narrower than "cannot be written". MEASURED (audit): a diverging
    rival IS expressible on this carrier — a ``partial def`` whose no-finite-value
    arm self-calls passes the variant scope check unchanged (``variant_problems``
    returns ``[]``) — so the claim that a total Lean ``def`` forbids one is FALSE
    and is not the reason. What blocks the case is ATTRIBUTION, not
    expressibility: ``partial def`` generates no equation lemmas (``.eq_def`` is
    an unknown constant), so the impl is irreducible, and BOTH the case's own
    build AND a witness stated against it fail identically with ``Tactic
    `unfold` failed to unfold `implementation_safeRepresentative```. That
    rejection is a tooling artifact rather than the spec speaking, and no
    witness can discriminate rival from gold through it. Nor is there a
    soundness hole to record: a diverging impl does not verify VACUOUSLY here,
    it does not verify at all — unlike the ``partial``-semantics hole in
    the corpus-wide termination-semantics finding, which is real on velvet where a
    non-terminating impl satisfies every ``ensures`` vacuously. So: no shippable
    case and no gap, but for the attribution reason above, not the
    expressibility one.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason nagini gave and more
    strongly. ``result`` is pinned to a term built only from the input; there is
    no opaque answer key to echo. Nagini kept an honest positive control in its
    place (returning the pure fold directly, which IS the correct selection);
    that control ports directly as ``pos-grounded-fold``.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries all the adversarial pressure:
    dropping the fall-back (the pre-change behavior), ignoring finiteness
    altogether, inverting which regime each selection rule serves, and applying
    the sequence regime's finiteness filter to a lone coordinate value that no
    filter bears on.

CARRIER NOTE (why every float-sensitive witness conditions rather than computes).
The finiteness test on this carrier is a compiler-``extern`` primitive, so it is
OPAQUE to the kernel: re-measured during the audit, ``example : (1.0 :
Float).isFinite = true`` fails under ``rfl``, ``decide``, ``decide +kernel``,
``simp``, ``simp [Float.isFinite, Float.isNaN, Float.isInf]`` AND ``norm_num
[Float.isFinite]`` (six builds, all exit 1; only ``native_decide`` closes it,
which is banned and would in any case make a witness hold of gold too). So no
float LITERAL decides anything here, and a witness that must inspect a concrete
float's finiteness cannot exist. NARROWED (audit): this does NOT extend to every
literal input — the EMPTY sequence is a literal whose verdict needs no finiteness
test at all, and a witness stated at ``.sequence []`` with NO hypotheses does
reduce by plain evaluation (measured against a rival that invents a
representative there: rival exit 0, gold exit 1 ``unsolved goals ⊢ False``). See
the EMPTY-clause disposition below for why that literal nonetheless yields no
shippable rival. Every witness for the float-sensitive clauses therefore
conditions on the carrier instead of computing it — quantifying over abstract
values and assuming only each one's finiteness flag, which is exactly enough to
separate rival from gold. The claim each witness makes is consequently STRONGER
than any single literal could make: it refutes the rival across the whole
sub-domain its hypotheses describe. Each witness's binders were checked JOINTLY
SATISFIABLE (the gate's ``consistency_probe`` shape, run by hand: the probe could
not derive ``False`` from any of them) — no witness carries two hypotheses about
the same value, and the disequality binders relate DISTINCT abstract values,
which is realisable.

EMPTY-clause disposition (audit): NO RIVAL, and the reason is REFINEMENT, not
expressibility — the earlier honest gap in this manifest was that the EMPTY
clause was listed as a defended clause with nothing probing it. A rival that
invents a representative for the empty sequence is expressible, in scope
(``variant_problems`` returns ``[]``), IS rejected by the frozen spec (measured:
exit 1), and carries the corpus's most desirable witness shape — a plain
evaluation at a literal with no hypotheses at all, ``¬ problem_spec …
(.sequence []) (impl (.sequence []))``, measured rival exit 0 / gold exit 1
``unsolved goals ⊢ False``, with the flipped claim separating cleanly (gold exit
0, rival exit 1). It is deliberately NOT shipped, because it could not carry an
honest ``refinement``: the step surrounding this selection short-circuits an
empty coordinate sequence before any representative is ever requested, so the
empty case is unreachable under the refinement and a faithful patch differing
ONLY there would still resolve every F2P and P2P test. Shipping it would buy a
green case whose refinement argument is false — the precise defect this audit
lane exists to catch — so the clause is recorded here as
DEFENDED-BUT-UNREACHABLE rather than probed. The three clauses that ARE
reachable carry the seven rivals below.

BINDER / POINT SPREAD. The spec's one input binder is the coordinate argument,
so the witnesses vary it along every axis the spec's clauses turn on rather than
probing one convenient point: the argument's SHAPE (lone value vs sequence),
LENGTH (1, 2, 3), each value's REGIME (weighable / unweighable / missing), the
counting PATTERN (nothing counts; leading-non-counting-then-counting;
two-non-counting-then-counting; leading-unweighable-then-number;
leading-missing-then-number), and WHICH clause fires (the lone-value clause, the
fall-back clause, the finite-search clause at a non-leading position, the
finite-search clause at each regime boundary). The seven reject witnesses probe seven
distinct input shapes, and no two rivals share a point: ``weak-single-filtered`` is the only
one stated at the lone-value shape; ``weak-ignores-finiteness`` and
``weak-inverted-guard`` both attack the finite-search clause but the latter is
the NEAR-MISS (it is correct wherever the leading value is finite, and correct
about which VALUE to take when it takes one), so it is refuted at its own
distinguishing shape — two leading non-finite values before the finite one —
rather than sharing the former's length-2 point. The two regime rivals are
likewise near-misses of each other — `weak-unweighable-skipped` gets the missing
ruling right and the unweighable one wrong, `weak-missing-counted` the converse —
so each is refuted at its own regime boundary rather than at a shared point, and
neither shares a point with the three all-weighable rivals. ``weak-unsearched-searched``
is the only one stated at the unsearched-sequence shape, which no other witness in
the battery can even mention, and it is refuted at the one counting PATTERN that
separates the two sequence kinds — leading value does not count, trailing value is
a finite number — where the searched kind takes the trailing value and the
unsearched kind takes the leading one.

SPEC-STRENGTH PROBES RUN BY THE AUDIT (recorded so the next reader does not
re-spend the builds). Wrong impls beyond the seven shipped rivals were built
against the frozen spec; NONE verified, so no spec hole was found: selecting the
LAST finite value instead of the first; guarding on not-a-NaN instead of on
finiteness (so infinities are wrongly accepted); falling back to the sequence's
LAST value instead of its first; inventing a representative for the empty
sequence; and routing a lone coordinate value through the sequence rule. Most
are not SHIPPED, and the reason is the same for the first three: their
refinements would be false. The width/offset arithmetic that consumes the
representative is translation-invariant on plain numeric coordinates
(``convert(x0 + ddx) - x`` cancels the representative's magnitude), so a patch
that picks a DIFFERENT FINITE value still computes the same extent and still
resolves every F2P and P2P test. What the real tests are sensitive to is whether
a representative is produced AT ALL for each argument shape, and whether the
selected one is FINITE when a finite one exists — a non-finite one propagates
through that subtraction and yields a non-finite extent, and a MISSING one
diverts the whole conversion onto a different route. That is exactly the axis
the seven shipped rivals attack, and it is why they are the right seven rather
than an arbitrary seven. Correct RESHAPES were also built and all verified
(arms reordered; the fall-back hoisted into a named local; returning the pure
selection directly), so the spec is not over-fit to the frozen traversal shape
either.

AXIOM lane: DROPPED. The nagini bundle carried four ``AXIOM_TESTS`` for its two
``@ContractOnly`` callee axioms; this bundle axiomatizes NOTHING (the selection
is modeled deeply, and the two callees are A-references validated executably by
G-AX). The axiom lane belongs to G-AX; this gate ignores it.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24149"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The impl anchor is the WHOLE impl-region definition; the proof anchor is the
# whole frozen tactic body. Both lie entirely inside their region, so same_spec
# stays byte-identical and the obligation STATEMENT is never touched.

_I_GOLD = """def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do
  match arg with
  | .single v => return (some v)
  | .sequence vs =>
    for v in vs do
      if v.countsAsFinite then
        return (some v)
    return vs.head?
  | .unsearched vs => return vs.head?"""

_P_GOLD = """  intro arg
  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative
  cases arg with
  | single v => rfl
  | sequence vs =>
    simp only [Id.run, bind, forIn_firstFinite_helper]
    cases h : vs.find? (fun v => v.countsAsFinite) with
    | none => rfl
    | some v => rfl
  | unsearched vs => rfl"""

# Every rival/control below replaces the WHOLE impl definition, so each must
# carry an arm for each of the carrier's three argument shapes. The
# UNSEARCHED-SEQUENCE arm is written CORRECTLY in every rival whose target is a
# different clause, so each rival's wrongness stays confined to the clause its
# rationale names; the one rival that attacks this arm names it explicitly.
_A_US = "  | .unsearched vs => return vs.head?"
_A_US_PURE = "  | .unsearched vs => vs.head?"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical; nothing is assumed (no new
    # axiom / lemma / assumption token), and each proof below was CLOSED for its
    # own reshaped implementation rather than weakened.
    # =====================================================================

    # Ports nagini case pos-control-reordered: the nagini positive inverted the
    # guard so the no-representative-available regime is handled FIRST. Here the
    # equivalent reshape swaps the two match ARMS of the sequence case (the
    # fall-back arm written first), which is the same "test the fall-back regime
    # first" restructuring on a carrier that selects by pattern match rather
    # than by an if/else.
    {
        "id": "pos-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_GOLD,
                "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal :=\n"
                "  match arg with\n"
                "  | .single v => some v\n"
                "  | .sequence vs =>\n"
                "    match vs.find? (fun v => v.countsAsFinite) with\n"
                "    | none   => vs.head?\n"
                "    | some v => some v\n"
                + _A_US_PURE,
            ),
            _P_GOLD,
            "  intro arg\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  cases arg with\n"
            "  | single v => rfl\n"
            "  | sequence vs =>\n"
            "    show (match vs.find? (fun v => v.countsAsFinite) with\n"
            "          | none => vs.head? | some v => some v)\n"
            "        = (match vs.find? (fun v => v.countsAsFinite) with\n"
            "          | some v => some v | none => vs.head?)\n"
            "    cases h : vs.find? (fun v => v.countsAsFinite) with\n"
            "    | none => rfl\n"
            "    | some v => rfl\n"
            "  | unsearched vs => rfl",
        ),
        "rationale": "a structurally DIFFERENT but correct selection — the "
                     "fall-back regime handled first, and the search expressed as "
                     "a direct pattern match rather than an accumulating traversal "
                     "— must verify: it agrees with the spec's grounded equation on "
                     "every input of both shapes. If it failed, the obligation would "
                     "be over-fit to one branch ordering / one traversal shape "
                     "(SPEC-TOO-STRONG). Proof: re-closed for the new shape by "
                     "stating the reordered match and case-splitting on the search "
                     "result directly (the traversal helper is no longer needed, so "
                     "its rewrite is dropped); no new lemma, no assumption token. "
                     "Ports nagini's pos-control-reordered.",
    },

    # Ports nagini case pos-control-local: the nagini positive hoisted the guard
    # predicate into a named local and branched on it. Here the analogous reshape
    # hoists the FALL-BACK value into a named local computed BEFORE the traversal.
    # NOTE this control is deliberately retained after the carrier repair, and it
    # is the sharpest one in the file: it shows the spec still admits computing
    # the fall-back VALUE early for a sequence (which is harmless — the value does
    # not depend on the traversal having run) while the `weak-single-filtered`
    # rival below shows the spec does NOT admit letting that relocation change
    # what a LONE coordinate value selects. The repair separates those two, where
    # the previous `List Float` carrier conflated them.
    {
        "id": "pos-fallback-hoisted",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (some v)\n"
            "  | .sequence vs =>\n"
            "    let fallback := vs.head?\n"
            "    for v in vs do\n"
            "      if v.countsAsFinite then\n"
            "        return (some v)\n"
            "    return fallback\n"
            + _A_US,
        ),
        "rationale": "a correct implementation that binds the sequence's fall-back "
                     "representative to a named local BEFORE the search, then "
                     "returns that local when the search finds nothing — a "
                     "different code shape for the same behavior — must verify. If "
                     "it failed, the obligation would be over-fit to computing the "
                     "fall-back inline at the exit (SPEC-TOO-STRONG). Note what it "
                     "does NOT license: it leaves the lone-value clause untouched, "
                     "which is the clause `weak-single-filtered` attacks. Proof: the "
                     "frozen tactic body is retained (the local zeta-reduces). "
                     "Ports nagini's pos-control-local named-intermediate reshape.",
    },

    # Ports nagini case pos-fold-grounded verbatim in spirit: the anti-echo
    # control. The nagini bundle argued there is no WRONG echo of its oracle
    # because the oracle is grounded in the input; the same holds here, so the
    # honest control returns the spec's own pure selection directly.
    {
        "id": "pos-grounded-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_GOLD,
                "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal :=\n"
                "  chooseRepresentative arg",
            ),
            _P_GOLD, "  intro arg\n  rfl",
        ),
        "rationale": "the anti-echo control. The postcondition is GROUNDED — it "
                     "pins the result to a selection computed from the input alone "
                     "— so there is no opaque answer key an implementation could "
                     "echo without doing the work, and returning that selection "
                     "DIRECTLY is not a cheat but the correct behavior. It must "
                     "verify; if it failed, the equation would be self-inconsistent "
                     "(SPEC-TOO-STRONG). Its adversarial content is the converse: "
                     "it demonstrates that the ONLY thing satisfying the "
                     "postcondition is the actual selection, which is what the "
                     "seven rivals below then fail to be. Proof: `rfl` (the impl is "
                     "definitionally the pinned selection). Ports nagini's "
                     "pos-fold-grounded.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at the exact input
    # shapes the regression is about, not merely in the abstract. The frozen
    # theorem carries NO precondition hypothesis (the modeled behavior is
    # total, so the `∀` is unguarded), so nagini's permission/length/termination
    # precondition probe has no binder to attack here; the honest analogue is to
    # discharge the spec predicate at those input shapes alongside the frozen
    # obligation. Ports nagini case admiss-f2p-all-nan.
    # =====================================================================
    {
        "id": "admiss-all-nonfinite-singleton",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the regression's own input shape — a
        # single-element SEQUENCE whose only value is non-finite, i.e. the
        # fall-back regime under repair — as a `have` inside the existing tactic
        # body, then close the frozen obligation verbatim. Nothing is assumed:
        # no new declaration, statement byte-identical, and the `have` is PROVED
        # (from the value's finiteness flag alone) rather than posited.
        "module": _swap(
            _BASE, _P_GOLD,
            "  have _ground : ∀ v : Float, v.isFinite = false →\n"
            "      problem_spec_safeRepresentative (.sequence [.numeric v])\n"
            "        (implementation_safeRepresentative (.sequence [.numeric v])) := by\n"
            "    intro v hv\n"
            "    unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "    simp [CoordVal.countsAsFinite, hv]\n"
            + _P_GOLD,
        ),
        "rationale": "the obligation is discharged at the exact input shape the "
                     "regression exercises — a one-element sequence whose single "
                     "value is non-finite, which is precisely the fall-back regime "
                     "the change repairs — and then the frozen obligation is closed "
                     "verbatim. Verifies, else the modeled behavior would be "
                     "unsatisfiable at the very input the fix targets (the analogue "
                     "of PRECOND-TOO-STRONG). Note this is a real proof over an "
                     "OPAQUE carrier: it is established from the value's finiteness "
                     "flag alone, for EVERY non-finite value, not posited at a "
                     "literal. Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical. Ports nagini's "
                     "admiss-f2p-all-nan in-domain probe.",
    },

    # The companion admissibility probe for the OTHER argument shape, added with
    # the carrier repair: the obligation must also be satisfiable for a LONE
    # coordinate value that is non-finite — the shape on which the previous
    # carrier was silent and on which the wrong-placement rivals diverge.
    {
        "id": "admiss-single-nonfinite",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_GOLD,
            "  have _ground : ∀ v : Float, v.isFinite = false →\n"
            "      problem_spec_safeRepresentative (.single (.numeric v))\n"
            "        (implementation_safeRepresentative (.single (.numeric v))) := by\n"
            "    intro v _\n"
            "    rfl\n"
            + _P_GOLD,
        ),
        "rationale": "the obligation is discharged at the OTHER reachable input "
                     "shape — one lone coordinate value that is NON-finite — and "
                     "then the frozen obligation is closed verbatim. This must "
                     "verify: a lone coordinate value stands for itself whatever it "
                     "is, so the spec must be satisfiable there, and satisfiable "
                     "WITHOUT the finiteness flag being consulted (note the proof "
                     "discharges it by `rfl` while DISCARDING the finiteness "
                     "hypothesis — the flag is genuinely irrelevant to this clause, "
                     "which is exactly what the clause claims). If it failed, the "
                     "spec would demand a finiteness filter on a value no filter "
                     "bears on (PRECOND-TOO-STRONG on the lone-value regime). New "
                     "with the carrier repair; nagini had no analogue because its "
                     "flag abstraction modeled only sequences.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a machine-checked refutation witness. Because the
    # carrier's finiteness test is opaque (see CARRIER NOTE), each witness
    # conditions on finiteness flags instead of using literals; each was checked
    # to ELABORATE against its rival, to FAIL on the frozen solution, and to
    # have jointly-satisfiable hypotheses.
    # =====================================================================

    # ---- the change itself: no fall-back at all (nagini U2, the prepatch
    # witness / G-DIFF shape) ----
    {
        "id": "weak-no-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-change behavior: search a sequence for a finite value and, finding
        # none, produce NO representative even though the sequence is non-empty.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (some v)\n"
            "  | .sequence vs =>\n"
            "    for v in vs do\n"
            "      if v.countsAsFinite then\n"
            "        return (some v)\n"
            "    return none\n"
            + _A_US,
        ),
        "refinement": "this IS the pre-change behavior, and it is the one rival "
                      "whose faithful patch fails the F2P for a NON-value reason: "
                      "the surrounding conversion step has no representative to "
                      "continue with, so the exhausted search propagates out as a "
                      "failure rather than a value, and plotting an all-non-finite "
                      "coordinate raises instead of producing a (non-finite) "
                      "geometry. The F2P compares the figure produced for such a "
                      "coordinate against a reference figure, so there is no figure "
                      "to compare and it does NOT resolve. Independently confirmed "
                      "by the bundle's own prepatch artifact, whose obligation is "
                      "unclosable.",
        "rationale": "REJECT from the FALL-BACK clause: on a non-empty sequence "
                     "with no finite value the spec pins the result to the "
                     "sequence's first value (`some`), while the rival yields none, "
                     "so `result` differs — the two disagree even in the option's "
                     "CONSTRUCTOR, the coarsest possible disagreement. This is the "
                     "clause under repair, so if it verified the spec would not see "
                     "the bug at all (SPEC-TOO-WEAK). Witness point: the shortest "
                     "and most direct shape — a one-element all-non-finite sequence "
                     "(the regression's own shape), stated for EVERY non-finite "
                     "value. Ports nagini's rival-prepatch-no-fallback.",
        "witness": (
            "-- Refuted at the regression's own shape: a sequence of one non-finite\n"
            "-- value. The finiteness test is an opaque primitive on this carrier, so\n"
            "-- the point is described by hypothesis rather than by a literal — which\n"
            "-- makes the claim universal over non-finite values. One hypothesis,\n"
            "-- about one value, so it is trivially satisfiable.\n"
            "example (v : Float) (hv : v.isFinite = false) :\n"
            "    ¬ problem_spec_safeRepresentative (.sequence [.numeric v])\n"
            "        (implementation_safeRepresentative (.sequence [.numeric v])) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, hv]\n"
        ),
    },

    # ---- ignore finiteness entirely (nagini U3, the identity attack on P1) ----
    {
        "id": "weak-ignores-finiteness",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the sequence's leading value unconditionally, never testing
        # finiteness — so a leading non-finite value is selected even though a
        # finite one is present later.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (some v)\n"
            "  | .sequence vs =>\n"
            "    for v in vs do\n"
            "      return (some v)\n"
            "    return vs.head?\n"
            + _A_US,
        ),
        "refinement": "a faithful patch of this shape selects the leading "
                      "coordinate unconditionally instead of the leading FINITE "
                      "one, so for a sequence whose first coordinate is non-finite "
                      "the representative is non-finite. Measured on the real "
                      "arithmetic that consumes it: the derived extent for the "
                      "leading-non-finite sequence comes out non-finite for EVERY "
                      "bar, where the correct selection yields a finite extent. A "
                      "value-sensitive regression test asserts exactly that — that "
                      "only the leading item carries the non-finite position while "
                      "every remaining item has a finite position AND a finite "
                      "extent — so it breaks, and the patch does NOT resolve. Note "
                      "this rival also still resolves nothing about the all-non-"
                      "finite case it appears to handle: it reaches a representative "
                      "there only by accident of the leading value being the answer.",
        "rationale": "REJECT from the FINITE-SEARCH clause: when a finite value is "
                     "present the spec pins the result to the FIRST finite value, "
                     "while the rival returns the sequence's leading value, so on a "
                     "leading-non-finite sequence `result` differs. This is the "
                     "identity pin — the clause that makes the spec unsatisfiable "
                     "by 'some plausible representative' — so if it verified the "
                     "spec would admit an implementation that never tests "
                     "finiteness at all (SPEC-TOO-WEAK). Witness point: length 2, "
                     "pattern non-finite-then-finite — a DIFFERENT length and a "
                     "different finiteness pattern from the fall-back rival's "
                     "point, and the first point at which the search clause is "
                     "live. Ports nagini's "
                     "rival-wrong-selector-leading-nan.",
        "witness": (
            "-- Refuted where the finite value is not the leading one: the spec\n"
            "-- must reach past the non-finite head, the rival stops at it. Two\n"
            "-- hypotheses about two DISTINCT values with OPPOSITE flags — jointly\n"
            "-- satisfiable (any non-finite value paired with any finite one).\n"
            "-- The closing steps derive the contradiction: were the rival's answer\n"
            "-- the spec's, the non-finite head would carry the finite value's flag.\n"
            "example (a b : Float) (ha : a.isFinite = false) (hb : b.isFinite = true) :\n"
            "    ¬ problem_spec_safeRepresentative (.sequence [.numeric a, .numeric b])\n"
            "        (implementation_safeRepresentative (.sequence [.numeric a, .numeric b])) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, ha, hb]\n"
            "  intro h\n"
            "  rw [h] at ha\n"
            "  simp [hb] at ha\n"
        ),
    },

    # ---- invert which regime each rule serves (nagini U4) ----
    {
        "id": "weak-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverted: when a finite value EXISTS take the sequence's leading value
        # instead, and when none exists fall back to the (empty) search result —
        # so the fall-back regime produces no representative and the search
        # regime produces the wrong one. Both sequence clauses attacked at once,
        # which is exactly the nagini rival's shape.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal :=\n"
            "  match arg with\n"
            "  | .single v => some v\n"
            "  | .sequence vs =>\n"
            "    match vs.find? (fun v => v.countsAsFinite) with\n"
            "    | some _ => vs.head?\n"
            "    | none   => vs.find? (fun v => v.countsAsFinite)\n"
            + _A_US_PURE,
        ),
        "refinement": "a faithful patch of this shape inverts which regime each "
                      "selection rule serves: it takes the leading coordinate on "
                      "the COMMON path where a finite coordinate exists (the wrong "
                      "representative, giving a non-finite extent for the "
                      "leading-non-finite sequence and so breaking the "
                      "value-sensitive regression exactly as the previous rival "
                      "does) AND produces no representative on the all-non-finite "
                      "path (re-introducing the failure the F2P checks). Both the "
                      "value regression and the F2P break, so it does NOT resolve. "
                      "It is strictly worse than either single-clause rival, which "
                      "is why it is kept as its own case rather than folded in: it "
                      "shows the spec catches a simultaneous mis-assignment and not "
                      "merely one clause at a time.",
        "rationale": "REJECT from BOTH sequence clauses at once — the FINITE-SEARCH "
                     "clause (the leading value is returned where the first FINITE "
                     "value is pinned) and the FALL-BACK clause (no representative "
                     "where one is pinned). If it verified, the spec would place no "
                     "constraint on which regime each rule serves (SPEC-TOO-WEAK). "
                     "Witness point: this rival is the NEAR-MISS of the "
                     "ignores-finiteness rival — it agrees with gold on every "
                     "sequence whose leading value is finite, and unlike that rival "
                     "it does consult finiteness — so it is refuted at its OWN "
                     "distinguishing shape rather than sharing a point: length 3, "
                     "pattern non-finite / non-finite / finite, where the pinned "
                     "answer lies two positions past the head. That moves the "
                     "length binder to 3 and probes a third distinct finiteness "
                     "pattern. Ports nagini's rival-inverted-guard.",
        "witness": (
            "-- Refuted at a length-3 shape with TWO non-finite values before the\n"
            "-- finite one — this rival's own sub-domain, distinct from the\n"
            "-- length-2 point of the ignores-finiteness rival (which it does not\n"
            "-- share, being correct wherever the head is finite). Three\n"
            "-- hypotheses about three DISTINCT values; jointly satisfiable.\n"
            "example (a b c : Float) (ha : a.isFinite = false) (hb : b.isFinite = false)\n"
            "    (hc : c.isFinite = true) :\n"
            "    ¬ problem_spec_safeRepresentative (.sequence [.numeric a, .numeric b, .numeric c])\n"
            "        (implementation_safeRepresentative (.sequence [.numeric a, .numeric b, .numeric c])) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, ha, hb, hc]\n"
            "  intro h\n"
            "  rw [h] at ha\n"
            "  simp [hc] at ha\n"
        ),
    },

    # ---- NEW with the carrier repair: apply the sequence regime's finiteness
    # filter to a LONE coordinate value that no filter bears on. This is the
    # rival class the previous `List Float` carrier could not express at all,
    # and it is the class the audited counterexample belonged to. ----
    {
        "id": "weak-single-filtered",
        "kind": "uniqueness",
        "expect": "reject",
        # The sequence clauses are exactly right; the LONE-VALUE clause is wrong —
        # a lone coordinate value is admitted only if it happens to be finite, and
        # a non-finite lone value yields no representative at all.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (if v.countsAsFinite then some v else none)\n"
            "  | .sequence vs =>\n"
            "    for v in vs do\n"
            "      if v.countsAsFinite then\n"
            "        return (some v)\n"
            "    return vs.head?\n"
            + _A_US,
        ),
        "refinement": "a faithful patch of this shape subjects a LONE coordinate "
                      "argument to the finiteness screening that only the sequence "
                      "regime calls for, so a lone coordinate that is not a finite "
                      "number yields no representative and the conversion step is "
                      "diverted off its normal route onto the fall-back route that "
                      "discards the coordinate-plus-offset arithmetic entirely. "
                      "MEASURED against the real conversion step: for a lone "
                      "coordinate argument the correct behavior proceeds with that "
                      "coordinate itself (a plain number, a date, a 0-d array — "
                      "whatever it is), whereas this shape abandons it, and the "
                      "difference is observable in the resulting geometry for every "
                      "lone-coordinate call. Two existing regression tests drive "
                      "exactly that configuration — a lone date-valued coordinate "
                      "with an offset in elapsed-time units, in both the "
                      "single-item-bar and the item-range forms — and both break "
                      "while the F2P all-non-finite-sequence case still passes, so "
                      "the patch does NOT resolve. This is precisely the shape of "
                      "the counterexample that motivated widening the carrier: it "
                      "is invisible to any equation stated over sequences alone.",
        "rationale": "REJECT from the LONE-VALUE clause: the spec pins a lone "
                     "coordinate value to stand for ITSELF unconditionally, with no "
                     "finiteness test bearing on it, while the rival withholds a "
                     "representative whenever that value is not finite — so on a "
                     "non-finite lone value `result` differs in the option's "
                     "CONSTRUCTOR. This is the clause that makes the argument's "
                     "SHAPE observable, and it is the clause whose absence let a "
                     "wrong implementation verify: without it, an implementation may "
                     "relocate the fall-back selection so that it runs for every "
                     "argument rather than only upon an exhausted search, which is "
                     "indistinguishable on sequences and wrong on lone values "
                     "(SPEC-TOO-WEAK). Witness point: the lone-value shape, which no "
                     "other rival in this battery probes, stated for EVERY "
                     "non-finite value. New with the carrier repair.",
        "witness": (
            "-- Refuted at the shape no sequence-shaped witness can reach: ONE lone\n"
            "-- coordinate value that is non-finite. The spec says it stands for\n"
            "-- itself; the rival withholds it. The finiteness test is opaque on this\n"
            "-- carrier, so the point is described by hypothesis rather than by a\n"
            "-- literal, which makes the claim universal over non-finite values. One\n"
            "-- hypothesis about one value, so it is trivially satisfiable.\n"
            "example (v : Float) (hv : v.isFinite = false) :\n"
            "    ¬ problem_spec_safeRepresentative (.single (.numeric v))\n"
            "        (implementation_safeRepresentative (.single (.numeric v))) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, hv]\n"
        ),
    },
    # ---- NEW with the REGIME repair: apply the arithmetic finiteness test to a
    # value it cannot weigh as a quantity. This is the rival class the previous
    # all-numeric element carrier could not express at all, and it is the class
    # the audited counterexample belonged to. ----
    {
        "id": "weak-unweighable-skipped",
        "kind": "uniqueness",
        "expect": "reject",
        # Every clause about the argument's SHAPE and about the fall-back is
        # exactly right; what is wrong is WHICH VALUES the search counts. A value
        # the test cannot weigh is treated as though it failed the test, so the
        # search passes it over instead of stopping at it.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (some v)\n"
            "  | .sequence vs =>\n"
            "    for v in vs do\n"
            "      match v with\n"
            "      | .numeric w => if w.isFinite then return (some v)\n"
            "      | _          => pure ()\n"
            "    return vs.head?\n"
            + _A_US,
        ),
        "refinement": "a faithful patch of this shape screens each value of a "
                      "coordinate sequence by the ARITHMETIC finiteness test alone, "
                      "rather than by the test the step actually applies, which "
                      "counts a value it cannot weigh as a quantity instead of "
                      "passing it over. MEASURED against the real conversion step "
                      "(the test reconstructed verbatim from the unchanged helper): "
                      "for a sequence whose leading values are points in time, the "
                      "correct behavior stops at the FIRST of them and proceeds with "
                      "it, whereas the arithmetic test cannot weigh such a value at "
                      "all -- it errors on it, and that error is absorbed by the "
                      "surrounding handler so the WHOLE SEQUENCE is left standing as "
                      "its own representative, after which the coordinate-plus-offset "
                      "arithmetic on a sequence rather than a value fails and the "
                      "step falls off its normal route, discarding that arithmetic "
                      "entirely. An existing regression test drives exactly that "
                      "configuration -- a sequence of two time-valued coordinates "
                      "with an offset in elapsed-time units -- so it breaks while the "
                      "F2P all-non-counting-sequence case still passes, and the patch "
                      "does NOT resolve. Substituting the real regime-aware test for "
                      "the arithmetic one, changing nothing else, restores it.",
        "rationale": "REJECT from the FINITE-SEARCH clause read at the REGIME level: "
                     "the spec pins the representative to the first value that COUNTS "
                     "AS FINITE, and a value the test cannot weigh COUNTS, so the "
                     "search must stop at it; the rival passes it over and takes a "
                     "later weighable value instead, so `result` differs. If it "
                     "verified, the spec would place no constraint on which values a "
                     "search for a finite value is entitled to skip, and would admit "
                     "an implementation that substitutes bare arithmetic finiteness "
                     "for the real test (SPEC-TOO-WEAK). Witness point: a length-2 "
                     "sequence whose leading value is unweighable and whose trailing "
                     "value is a finite number -- a shape no other rival in this "
                     "battery probes, since every other witness is stated at all-"
                     "weighable values. New with the regime repair.",
        "witness": (
            "-- Refuted at the shape no all-numeric witness can reach: a sequence\n"
            "-- whose LEADING value is one the finiteness test cannot weigh and whose\n"
            "-- trailing value is a finite number. The spec must stop at the leading\n"
            "-- value; the rival skips it. No hypothesis is needed about the\n"
            "-- unweighable value (its counting is settled by its regime), and one\n"
            "-- hypothesis about one distinct number, so it is trivially satisfiable.\n"
            "example (t : Nat) (b : Float) (hb : b.isFinite = true) :\n"
            "    ¬ problem_spec_safeRepresentative (.sequence [.unweighable t, .numeric b])\n"
            "        (implementation_safeRepresentative (.sequence [.unweighable t, .numeric b])) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, hb]\n"
        ),
    },

    # ---- NEW with the REGIME repair: the converse mis-ruling -- count a MISSING
    # value, which the real test never counts. ----
    {
        "id": "weak-missing-counted",
        "kind": "uniqueness",
        "expect": "reject",
        # The search counts EVERY value that is not a non-finite number, so a
        # missing value -- a hole where a coordinate should be -- is taken as the
        # representative instead of being passed over.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (some v)\n"
            "  | .sequence vs =>\n"
            "    for v in vs do\n"
            "      match v with\n"
            "      | .numeric w => if w.isFinite then return (some v)\n"
            "      | _          => return (some v)\n"
            "    return vs.head?\n"
            + _A_US,
        ),
        "refinement": "a faithful patch of this shape rules that a value it cannot "
                      "weigh as a quantity always counts WITHOUT first excluding a "
                      "value that is missing outright, so a sequence whose leading "
                      "coordinate is absent has that absence selected as its "
                      "representative rather than being passed over for the first "
                      "real coordinate behind it. MEASURED against the real test "
                      "reconstructed verbatim from the unchanged helper: an absent "
                      "value is the ONE case ruled out before any other "
                      "consideration, so a sequence of an absence followed by a "
                      "finite number selects that number, whereas this shape selects "
                      "the absence and the subsequent coordinate-plus-offset "
                      "arithmetic on an absent coordinate fails, diverting the step "
                      "off its normal route and discarding that arithmetic. The F2P "
                      "all-non-counting-sequence case is untouched, so the fix is in "
                      "place and the patch still does NOT resolve.",
        "rationale": "REJECT from the FINITE-SEARCH clause at the OTHER regime "
                     "boundary: the spec pins a missing value to NEVER count, "
                     "however much it resembles a value that cannot be weighed, so "
                     "the search must pass it over; the rival stops at it, and "
                     "`result` differs. This is the near-miss of the previous rival "
                     "-- it gets the unweighable regime right and only the missing "
                     "regime wrong -- so if it verified the spec would pin only two "
                     "of the test's three rulings (SPEC-TOO-WEAK). Witness point: a "
                     "length-2 sequence, leading value MISSING, trailing value a "
                     "finite number: a fourth distinct shape, and the only one in the "
                     "battery stated at the missing regime. New with the regime "
                     "repair.",
        "witness": (
            "-- Refuted where the leading value is absent and a real coordinate\n"
            "-- stands behind it: the spec reaches past the absence, the rival stops\n"
            "-- at it. The absence's counting is settled by its regime so it needs no\n"
            "-- hypothesis; one hypothesis about one number, trivially satisfiable.\n"
            "example (b : Float) (hb : b.isFinite = true) :\n"
            "    ¬ problem_spec_safeRepresentative (.sequence [.missing, .numeric b])\n"
            "        (implementation_safeRepresentative (.sequence [.missing, .numeric b])) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, hb]\n"
        ),
    },

    # ---- NEW with the SHAPE-OF-SEQUENCE repair: run the finiteness search over a
    # kind of sequence the search does not run over. The carrier distinguishes the
    # two sequence shapes precisely so this rival is expressible; an earlier
    # revision had ONE sequence shape and so applied the search to both, which is
    # the clause this rival now pins. ----
    {
        "id": "weak-unsearched-searched",
        "kind": "uniqueness",
        "expect": "reject",
        # Every clause about the LONE value and about the searched sequence is
        # exactly right; what is wrong is that the OTHER kind of sequence -- the one
        # read at its leading position -- is subjected to the finiteness search too,
        # so a non-counting leading value is passed over for a later counting one.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do\n"
            "  match arg with\n"
            "  | .single v => return (some v)\n"
            "  | .sequence vs =>\n"
            "    for v in vs do\n"
            "      if v.countsAsFinite then\n"
            "        return (some v)\n"
            "    return vs.head?\n"
            "  | .unsearched vs =>\n"
            "    for v in vs do\n"
            "      if v.countsAsFinite then\n"
            "        return (some v)\n"
            "    return vs.head?",
        ),
        "refinement": "a faithful patch of this shape applies the per-value "
                      "finiteness screening to EVERY kind of coordinate sequence, "
                      "including the kind the step reads at its leading position "
                      "instead of searching. MEASURED against the real conversion "
                      "step: for that kind of sequence the correct behavior takes the "
                      "LEADING value whatever it is -- the screening is not performed "
                      "on it at all -- whereas this shape reaches past a leading "
                      "non-counting value to a later counting one, so the "
                      "representative differs and the coordinate-plus-offset "
                      "arithmetic is done about the wrong position, yielding a finite "
                      "extent where the correct behavior yields a non-finite one. The "
                      "F2P all-non-counting-sequence case is untouched (the fix is in "
                      "place) and every searched-sequence call site is untouched too, "
                      "so this rival is invisible to both and the patch still does NOT "
                      "faithfully reproduce the step. It is the converse of the "
                      "previous carrier's defect, which had no image of this kind of "
                      "sequence at all and therefore could not tell the two apart.",
        "rationale": "REJECT from the UNSEARCHED-SEQUENCE clause: the spec pins the "
                     "leading value of such a sequence unconditionally, with no "
                     "finiteness test bearing on it, while the rival searches it and "
                     "so returns a later value whenever the leading one does not "
                     "count -- `result` differs. If it verified, the spec would place "
                     "no constraint on WHICH kinds of sequence the search is entitled "
                     "to run over, and would admit an implementation that screens a "
                     "sequence the step reads positionally (SPEC-TOO-WEAK). Witness "
                     "point: the unsearched-sequence shape at length 2, leading value "
                     "non-counting and trailing value a finite number -- a shape no "
                     "other rival in this battery probes, since every other witness is "
                     "stated at the lone-value or the searched-sequence shape. New "
                     "with the shape-of-sequence repair.",
        "witness": (
            "-- Refuted at the shape no searched-sequence witness can reach: a\n"
            "-- sequence of the kind that is read at its leading position, whose\n"
            "-- leading value does NOT count and whose trailing value is a finite\n"
            "-- number. The spec stops at the leading value; the rival reaches past\n"
            "-- it. Two hypotheses about two DISTINCT values with OPPOSITE flags --\n"
            "-- jointly satisfiable (any non-finite value paired with any finite one).\n"
            "example (a b : Float) (ha : a.isFinite = false) (hb : b.isFinite = true) :\n"
            "    ¬ problem_spec_safeRepresentative (.unsearched [.numeric a, .numeric b])\n"
            "        (implementation_safeRepresentative (.unsearched [.numeric a, .numeric b])) := by\n"
            "  unfold problem_spec_safeRepresentative implementation_safeRepresentative chooseRepresentative\n"
            "  simp [CoordVal.countsAsFinite, ha, hb]\n"
            "  intro h\n"
            "  rw [h] at hb\n"
            "  simp [ha] at hb\n"
        ),
    },
]

# No AXIOM lane here: this bundle consumes no `axiom` (the selection is modeled
# deeply; the two unchanged callees are A-references validated executably by
# G-AX, not assumed contracts). The nagini sibling's four AXIOM_TESTS are
# dropped per the porting contract — that lane belongs to G-AX.
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13142 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the single ``theorem correct_fit_predict`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff the variant is in scope AND the
file elaborates with the obligation closed; ``expect="reject"`` passes iff the
variant is in scope AND it does NOT verify AND the case's refutation ``witness``
holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the routine as a STATEFUL procedure over a mutable estimator object with
fractional-permission contracts: the held parameter state is writable, the two
trial-input lists are read-only halves, and the postcondition splits into (P1)
"the persisted state is the selected trial" and (P2) "the returned labels are
those of the state the object holds ON RETURN". This Lean bundle models the
purely-functional core instead — one total function from the trial sequence to
the reported labels — so the object identity that carried nagini's (P1) is not
part of the carrier at all. (P1) and (P2) FUSE here into a single clause: the
reported labels are those of the SELECTED trial's configuration. Every nagini
value-level rival therefore lands on that one clause, and the frame /
permission class has no expressible instance. The per-case mapping (or the
principled omission) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior). Several independent fitting trials are
run; each yields a candidate parameter configuration together with an
order-only quality score. The procedure must report the label assignment
produced by the configuration of the highest-scoring trial, with the EARLIEST
such trial winning a tie.

The postcondition is written as two top-level conjuncts, but only ONE of them
is an obligation, and the battery says so rather than claiming clause coverage
it does not have. The obligation is quantified over NON-EMPTY trial lists
(``trials ≠ []``, the modeled analogue of "at least one trial is always run"),
and on a non-empty list the selection always yields some trial. That is a
machine-checked fact about the carrier, not a reading:

    example (t : Int × Int) (ts : List (Int × Int)) : bestParam (t :: ts) ≠ none

elaborates (audit build, exit 0). So:

  * the TRIALS-PRESENT conjunct is the whole live obligation: whenever a best
    trial exists, the result equals the label assignment of THAT trial's
    configuration. Every rival below lands here, because there is nowhere else
    to land;
  * the NO-TRIALS conjunct is DEAD under the obligation's own hypothesis — its
    antecedent is unsatisfiable there, so it constrains no implementation. It
    is honest defensive text in the spec (the excluded input is one the modeled
    routine never sees), but it pins NOTHING, and an earlier draft of this
    manifest was wrong to describe it as a second independent clause and as
    "frame discipline". Measured: a variant that returns an arbitrary label
    assignment on the empty list, and is gold elsewhere, VERIFIES (audit build,
    exit 0). No case here claims otherwise, and no case can be refuted on that
    conjunct.

The BEHAVIOURAL DISCRIMINATOR (the fix): the reported labels must be derived
from the SELECTED configuration, not from whichever configuration the run
happens to leave behind after the final trial. With a single trial the two
coincide, which is why the discriminating inputs all carry several trials whose
best is not the last.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    an input carries no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini frame-mutation rival
    (write into the read-only trial list) has no expressible instance here, and
    no substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — REJECTED BY THE CARRIER, but NOT SHIPPABLE
    under the witness requirement. An earlier draft of this manifest said a
    non-terminating rival "cannot be written at all" because the modeled routine
    is a total Lean ``def``. That is FALSE and the audit measured it: declaring
    the routine ``partial`` and having it call itself

        partial def implementation_fit_predict (trials : List (Int × Int))
            : List Nat := implementation_fit_predict trials

    is an admissible variant (``variant_problems`` returns ``[]`` — ``partial``
    is not an assumption-bearing token, the statement stays byte-identical, no
    axiom or ``sorry`` is added) and the verifier REJECTS it (audit build, exit
    1: ``Tactic `unfold` failed to unfold `implementation_fit_predict```). So
    this carrier does discharge the obligation against a diverging impl, and the
    class is NOT a spec hole — nothing here verifies vacuously.

    What blocks shipping it is the WITNESS half, not the rival. A ``partial
    def`` is kernel-IRREDUCIBLE (it elaborates through the ``Inhabited``
    default), so no refutation can evaluate the rival's result and the only
    statable shape conditions on that result:

        example (h : implementation_fit_predict [((40 : Int), (3 : Int))]
            ≠ labelsOf 40) : ¬ problem_spec_fit_predict [(40, 3)] ...

    Measured on both sides: it elaborates against the rival (exit 0) AND
    against the frozen solution (exit 0), because the conclusion follows from
    the hypothesis for ANY implementation. That is ``witness-vacuous`` — an
    inconclusive outcome, not a pass — so the case is not shippable, and
    fabricating it would attest to nothing. Recorded as a measured
    non-shippable class rather than as "no rival exists".

  * UNGROUNDED-ORACLE ECHO — NO WRONG ECHO EXISTS, as in nagini. The label
    computation is an ``opaque`` unchanged downstream callee, but the
    postcondition applies it to a configuration that is itself pinned by the
    selection over the INPUT trials. So the result is a function of the inputs
    and there is no free answer-key to echo with a wrong value. What replaces
    the echo attack is the argument-level attack: a rival that applies the
    label computation to the WRONG configuration (see below).

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the whole battery. Six
    rivals: report the last trial's configuration; report the first trial's
    configuration; let a later equally-scoring trial displace the earlier one;
    leave the final trial out of the selection entirely; report the selected
    trial's SCORE component instead of its configuration component; and seed the
    running best with a zero sentinel instead of the absent accumulator. The
    last two were added by the audit — the original four all vary WHICH TRIAL is
    reported and all keep the frozen seed, so the pair's projection and the
    non-positive score sub-domain were unattacked.

  * CORRECT-RESHAPE (SPEC-TOO-STRONG) HEADROOM — measured wider than the
    shipped positives show. Besides the three positives below, the audit closed
    two further faithful reshapes against the frozen spec and reports them here
    so the next reader does not re-derive them: the decision tail extracted into
    a named helper ``reportOf`` fed by the fold (exit 0), and — the one a prior
    audit round left as an open uncertainty it could NOT close — the selection
    rewritten with three SCALAR accumulators (``seen : Bool``, ``bp``, ``bs :
    Int``) in place of the ``Option``, which needs its own invariant lemma
    relating the flag-carrying recursion to ``stepBest`` and then closes (exit 0,
    axioms ``[propext, Quot.sound]``, no ``sorryAx``). That reshape abandons the
    frozen accumulator TYPE, not merely its traversal shape, so its closing is
    the strongest available evidence that the spec is not over-fitted to the
    frozen impl's surface form. Neither is shipped as a case: they would add
    build cost without probing a clause the three shipped positives leave
    unprobed. No faithful correct impl was found that the spec rejects.

  * ADMISSIBILITY — APPLIES, contrary to an earlier draft of this manifest,
    which dropped the nagini admissibility case as having no instance here.
    There is no precondition to admit and no self-call on this carrier, but the
    case's CONTENT (the modeled behavior is satisfiable at a normal F2P-shaped
    input, so the positives are not discharging a vacuous obligation) is
    expressible as a ground instance of the postcondition and is now shipped as
    ``admiss-ground-tie-nonlast-best``.

WITNESSES, and how an OPAQUE carrier is attacked. On a tactic-proof backend
"did not verify" is the DEFAULT outcome of reshaping an implementation — the
frozen script is tuned to the frozen form — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet refuting the spec predicate at one concrete input.

The label computation is ``opaque``, so no witness can COMPUTE the reported
labels and ``decide`` is useless on them. The refutations instead CONDITION on
the carrier: each states, under the single hypothesis that the callee
distinguishes the two configurations at issue, that the rival's result differs
from the one the spec pins. That is a strictly stronger claim than any literal
input could make — it says the rival is wrong on the whole sub-domain where the
two configurations are distinguishable — and it is exactly the sub-domain the
rival is wrong on. The transparent parts (which trial the selection picks, and
which configuration the result is derived from) are what carry each proof:
``bestParam`` at the concrete trial list evaluates by ``rfl``, and so does the
rival's own result, so the two sides reduce to two applications of the callee
that the hypothesis separates. One hypothesis per witness, about one callee
application pair, so the assumptions stay jointly satisfiable (the gate probes
this: an inconsistent binder set would prove anything).

The no-trials rival needs no hypothesis of that shape and gets the weaker,
honest one it actually needs (the callee's result is non-empty at the probed
configuration), since there the spec pins the result to the callee's value
while the rival returns the empty list.

BINDER / POINT SPREAD. ``trials`` is the spec's only input binder, so the
spread that matters is over its SHAPE and over the two coordinates of its
elements. The witnesses move it rather than sharing one convenient point: the
best trial sits LAST at a strict maximum (``[(30,4),(31,8)]``), FIRST at a
strict maximum (``[(10,9),(11,7)]``), FIRST on a TIE (``[(20,5),(21,5)]``), a
single-trial list (``[(40,3)]``) where the best is simultaneously the first and
the last, a single trial at a NEGATIVE score (``[(50,-2)]``), LAST at a strict
maximum with the selected pair's two coordinates BOTH distinct and both small
(``[(70,3),(71,6)]``), and — in the admissibility case, which exhibits the spec
holding rather than refuting — a three-trial list whose maximum is attained
twice with the winner neither first nor last (``[(10,7),(11,9),(12,9)]``).

Six rivals, SIX distinct refutation points, no two sharing one — and that is
now true rather than merely asserted. An earlier draft of this manifest claimed
it while the score-projection rival and the final-trial rival were BOTH refuted
at ``[(10,9),(11,7)]``; ``scripts/pbt_coverage.py`` had been reporting the
discrepancy all along as ``pts=5-5`` on six rivals, and the audit moved the
projection rival to its own point (``[(70,3),(71,6)]``, selected pair ``(71,6)``)
rather than weakening the sentence to match the defect. The two rivals were
never redundant — they fail for different reasons at that shared input — but a
shared point cannot DEMONSTRATE that, which is the whole job of the spread.

The tie point is what separates the near-miss tie rival from the others — it
agrees with the frozen solution wherever the maximum is strict, so refuting it
anywhere else would claim a sub-domain the manifest never demonstrates. The
list-shape spread is also what distinguishes the first-trial and last-trial
rivals from each other: each is refuted at the point where the OTHER one is
correct. The negative-score point is the only one that moves the SCORE
coordinate off the positives, which is the sub-domain the sentinel-seed rival is
wrong on and no other point reaches; and the score-projection rival is the only
one that varies which COMPONENT of the selected pair is read, a distinction that
is invisible in the list shape.

NAGINI ACCOUNTING (per sibling case; audited, no case folded into a summary).
The sibling battery has 7 SPEC cases. Each is either ported, re-expressed, or
recorded as having no expressible instance WITH the reason demonstrated:

  frame-mutate-readonly-run_config -> NO INSTANCE. Not "hard": the distinction
    does not exist on this carrier. The sibling rival's rejection comes from
    fractional permissions on a heap-allocated input; a Lean input is a value,
    there is no permission to hold a half of and no aliasing to exploit, so no
    variant can be written whose defect is the write. Nothing is fabricated in
    its place.
  drop-selection-keep-final-trial -> COLLAPSES ONTO report-final-trial-config.
    Demonstrated, not assumed: a variant that keeps the frozen tail but destroys
    the selection (accept every incoming trial unconditionally) denotes exactly
    "the labels of the last trial's configuration" — the SAME total function as
    the shipped case-1 rival. Built during the audit and refuted by case 1's own
    witness verbatim (rival exit 0), which is what makes them one rival on this
    carrier rather than two. Shipping both would double-count one defect: the
    sibling could tell them apart only because its (P1) observed the PERSISTED
    state separately from the returned value, and that object identity is not
    part of this carrier.
  weak-order-swap-prepatch      -> report-final-trial-config    PORTED
  strict-tiebreak-wrong-earliest-> tie-displaces-earliest       PORTED (mirrored:
    the sibling's backward scan needs `>=` where this forward fold needs `>`, so
    the rival is the NON-strict guard here and the strict one there; same
    defect, same tie-only sub-domain)
  pos-control-branch-reorder    -> pos-control-tail-branch-reorder  RE-EXPRESSED
  pos-control-tail-local-reshape-> pos-control-functional-fold      RE-EXPRESSED
  admissibility-multitrial-self-call -> admiss-ground-tie-nonlast-best
    RE-EXPRESSED (added by the audit; an earlier draft dropped it as having no
    instance, which was wrong — see the ADMISSIBILITY note above).

The sibling has no ``diverge-*`` / ``nonterm-*`` case, so nothing was dropped
from that lane; the DIVERGENCE note above records what this carrier does with
one anyway, because "no sibling case" is not by itself a reason the class is
empty here. The measured result: the rival is writable and IS rejected, but its
only statable witness is vacuous (holds of gold too), so the class is
non-shippable rather than either a spec hole or a fabricable case.

Cases this bundle ADDS beyond the sibling, because this carrier admits defects
the sibling's typed object state did not: report-first-trial-config,
final-trial-never-offered, report-score-not-config,
sentinel-seed-swallows-low-scores, pos-control-named-recursive-selection.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` belong to G-AX, which this gate
ignores. (Here the bundle consumes no ``axiom`` at all: the label computation is
declared ``opaque`` with signature only, an A-reference, so the axiom lane is a
documented skip in the bundle's own ``axiom_check.py``.)
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13142"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region, except _P_* which lie
# entirely inside the proof region (a variant may re-prove), so the spec view
# stays byte-identical either way.

# The whole loop + decision tail of the impl.
_I_LOOP_TAIL = (
    "  for t in trials do\n"
    "    match best with\n"
    "    | none => best := some t\n"
    "    | some (_, bs) => if t.2 > bs then best := some t\n"
    "  match best with\n"
    "  | none => return []\n"
    "  | some (bp, _) => return labelsOf bp"
)

# The impl's running-best update guard.
_I_UPDATE = "    | some (_, bs) => if t.2 > bs then best := some t"

# The impl's loop header.
_I_FOR = "  for t in trials do\n"

# The impl's whole body (loop + tail), from the accumulator declaration on.
_I_BODY = "  let mut best : Option (Int × Int) := none\n" + _I_LOOP_TAIL

# The impl's decision tail alone.
_I_TAIL = (
    "  match best with\n"
    "  | none => return []\n"
    "  | some (bp, _) => return labelsOf bp"
)

# The proof's opening rewrite (the step that reduces the loop to the fold) plus
# the over-precise closing step that a functional variant no longer needs.
_P_OPEN = (
    "  intro trials _\n"
    "  unfold implementation_fit_predict\n"
    "  simp only [Id.run, bind]\n"
    "  rw [loop_helper trials none]\n"
    "  constructor"
)
_P_CLOSE = (
    "    | some p => rw [hf] at hb; obtain ⟨bp, bs⟩ := p; simp at hb; "
    "simp only [hb]; rfl"
)


# ===========================================================================
# 1. UNIQUENESS / report the configuration left behind by the FINAL trial.
#    Selects correctly (the running best is computed exactly as frozen) but
#    derives the reported labels from the configuration the run ends on. This
#    is the pre-change position, restated as a rival: correct only when the
#    last trial is the best (in particular whenever there is one trial), wrong
#    on every input whose highest-scoring trial is not the last.
# ===========================================================================
_last_trial = _swap(
    _BASE,
    _I_LOOP_TAIL,
    "  let mut reported : Option Int := none\n"
    "  for t in trials do\n"
    "    reported := some t.1\n"
    "    match best with\n"
    "    | none => best := some t\n"
    "    | some (_, bs) => if t.2 > bs then best := some t\n"
    "  match reported with\n"
    "  | none => return []\n"
    "  | some c => return labelsOf c",
)

# Refuted where the best trial is FIRST at a strict maximum: the spec pins the
# result to the first configuration's labels, the rival reports the last's.
_W_LAST = """example (h : labelsOf 10 ≠ labelsOf 11) :
    ¬ problem_spec_fit_predict [(10, 9), (11, 7)]
        (implementation_fit_predict [(10, 9), (11, 7)]) := by
  intro hs
  have hb : bestParam [((10 : Int), (9 : Int)), ((11 : Int), (7 : Int))] = some 10 := by rfl
  have he := hs.1 10 hb
  have hr : implementation_fit_predict [((10 : Int), (9 : Int)), ((11 : Int), (7 : Int))]
      = labelsOf 11 := by rfl
  rw [hr] at he
  exact h he.symm"""


# ===========================================================================
# 2. UNIQUENESS / near-miss tie-break — a NON-STRICT update guard, so a later
#    trial that merely MATCHES the running best score displaces it. Agrees
#    with the frozen solution on every input whose maximum score is attained
#    once; diverges exactly on the tie sub-domain, where the selection must
#    keep the EARLIEST trial attaining the maximum. Refuted AT a tie, since
#    that is the only place it is wrong — refuting it anywhere else would
#    claim a sub-domain it does not actually get wrong.
# ===========================================================================
_tie_displaces = _swap(
    _BASE,
    _I_UPDATE,
    "    | some (_, bs) => if t.2 >= bs then best := some t",
)

_W_TIE = """example (h : labelsOf 20 ≠ labelsOf 21) :
    ¬ problem_spec_fit_predict [(20, 5), (21, 5)]
        (implementation_fit_predict [(20, 5), (21, 5)]) := by
  intro hs
  have hb : bestParam [((20 : Int), (5 : Int)), ((21 : Int), (5 : Int))] = some 20 := by rfl
  have he := hs.1 20 hb
  have hr : implementation_fit_predict [((20 : Int), (5 : Int)), ((21 : Int), (5 : Int))]
      = labelsOf 21 := by rfl
  rw [hr] at he
  exact h he.symm"""


# ===========================================================================
# 3. UNIQUENESS / report the FIRST trial's configuration. The mirror image of
#    case 1: it also selects correctly and also derives the labels from the
#    wrong configuration, but it is correct precisely where case 1 is wrong.
#    Shipped separately (not sharing case 1's witness) because it fails at a
#    DIFFERENT input for a different reason, and refuting it at case 1's point
#    would attribute a failure it does not have there.
# ===========================================================================
_first_trial = _swap(
    _BASE,
    _I_LOOP_TAIL,
    "  let mut reported : Option Int := none\n"
    "  for t in trials do\n"
    "    if reported.isNone then reported := some t.1\n"
    "    match best with\n"
    "    | none => best := some t\n"
    "    | some (_, bs) => if t.2 > bs then best := some t\n"
    "  match reported with\n"
    "  | none => return []\n"
    "  | some c => return labelsOf c",
)

# Refuted where the best trial is LAST at a strict maximum — the point at which
# case 1's rival happens to be RIGHT.
_W_FIRST = """example (h : labelsOf 30 ≠ labelsOf 31) :
    ¬ problem_spec_fit_predict [(30, 4), (31, 8)]
        (implementation_fit_predict [(30, 4), (31, 8)]) := by
  intro hs
  have hb : bestParam [((30 : Int), (4 : Int)), ((31 : Int), (8 : Int))] = some 31 := by rfl
  have he := hs.1 31 hb
  have hr : implementation_fit_predict [((30 : Int), (4 : Int)), ((31 : Int), (8 : Int))]
      = labelsOf 30 := by rfl
  rw [hr] at he
  exact h he"""


# ===========================================================================
# 4. UNIQUENESS / OFF-BY-ONE over the trial sequence — the final trial is never
#    offered to the selection, so it can neither win nor be reported. Wrong
#    whenever the best trial is the last, and (the point it is refuted at)
#    degenerate on a single-trial input, where it selects nothing and reports
#    the empty assignment while a trial plainly exists.
#
#    It is refuted on the TRIALS-PRESENT clause, like every other rival: the
#    selection at [(40,3)] plainly yields that trial, so that clause pins the
#    result to the callee's value there and the rival returns []. What is
#    DISTINCT about this rival is not the clause but the FAILURE MODE — it
#    returns the wrong OUTPUT SHAPE (the empty assignment, the value the dead
#    no-trials conjunct mentions) rather than the labels of the wrong
#    configuration, so its witness needs no two-configuration separation
#    hypothesis. It does NOT attest to the no-trials conjunct: that conjunct is
#    dead under the obligation's hypothesis (see the header) and nothing can be
#    refuted on it.
# ===========================================================================
_drop_last = _swap(_BASE, _I_FOR, "  for t in trials.dropLast do\n")

_W_DROP_LAST = """example (h : labelsOf 40 ≠ []) :
    ¬ problem_spec_fit_predict [(40, 3)]
        (implementation_fit_predict [(40, 3)]) := by
  intro hs
  have hb : bestParam [((40 : Int), (3 : Int))] = some 40 := by rfl
  have he := hs.1 40 hb
  have hr : implementation_fit_predict [((40 : Int), (3 : Int))] = [] := by rfl
  rw [hr] at he
  exact h he.symm"""


# ===========================================================================
# 4b. UNIQUENESS / WRONG PROJECTION of the selected pair — the selection is
#    exactly the frozen one, but the reported labels are derived from the
#    selected trial's SCORE component instead of its CONFIGURATION component.
#    Added by the audit: the four rivals above all vary WHICH TRIAL is reported,
#    so a rival that reports the right trial through the wrong field of the pair
#    was unattacked, and the pair's two components are the same type here
#    (`Int × Int`), which is exactly the carrier condition that makes such a
#    confusion type-correct and therefore expressible. Wrong on every input
#    whose selected trial has score ≠ config.
#
#    Refuted at its OWN point, [(70,3),(71,6)] — not, as an earlier draft had
#    it, at case 1's point [(10,9),(11,7)]. Sharing that input made the
#    manifest's "six distinct refutation points, no two share one" claim false
#    and left the projection sub-domain demonstrated only by argument: two
#    rivals refuted at one input cannot exhibit that they fail for different
#    reasons there. This point keeps the best trial LAST at a strict maximum
#    (so the final-trial rival is CORRECT here and only the projection is
#    wrong) with a selected pair (71, 6) whose coordinates are distinct.
# ===========================================================================
_score_projection = _swap(
    _BASE,
    "  | some (bp, _) => return labelsOf bp",
    "  | some (_, bscore) => return labelsOf bscore",
)

_W_PROJ = """example (h : labelsOf 71 ≠ labelsOf 6) :
    ¬ problem_spec_fit_predict [(70, 3), (71, 6)]
        (implementation_fit_predict [(70, 3), (71, 6)]) := by
  intro hs
  have hb : bestParam [((70 : Int), (3 : Int)), ((71 : Int), (6 : Int))] = some 71 := by rfl
  have he := hs.1 71 hb
  have hr : implementation_fit_predict [((70 : Int), (3 : Int)), ((71 : Int), (6 : Int))]
      = labelsOf 6 := by rfl
  rw [hr] at he
  exact h he.symm"""


# ===========================================================================
# 4c. UNIQUENESS / SENTINEL SEED instead of the "nothing selected yet" seed —
#    the running best is seeded with a concrete zero score rather than the
#    absent-accumulator the frozen selection uses, so a trial is accepted only
#    if it beats that sentinel. Added by the audit: every rival above keeps the
#    frozen `none` seed, so the SEED — the one modeled point where an unbounded
#    initial score is represented by an absent value rather than by a magic
#    number — was unattacked. Correct wherever some trial scores above the
#    sentinel; wrong on the whole sub-domain where every score is at or below
#    it, so it is refuted THERE (a single trial at a negative score), where the
#    selection plainly picks that trial and the rival reports the sentinel's
#    labels instead. This is the value-level rival the SCORE binder needs: it
#    moves the score coordinate off the positives every other point uses.
# ===========================================================================
_sentinel_seed = _swap(
    _BASE,
    "def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do\n"
    + _I_BODY,
    "def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do\n"
    "  let mut bestp : Int := 0\n"
    "  let mut bests : Int := 0\n"
    "  for t in trials do\n"
    "    if t.2 > bests then\n"
    "      bestp := t.1\n"
    "      bests := t.2\n"
    "  return labelsOf bestp",
)

_W_SENTINEL = """example (h : labelsOf 50 ≠ labelsOf 0) :
    ¬ problem_spec_fit_predict [(50, -2)]
        (implementation_fit_predict [(50, -2)]) := by
  intro hs
  have hb : bestParam [((50 : Int), (-2 : Int))] = some 50 := by rfl
  have he := hs.1 50 hb
  have hr : implementation_fit_predict [((50 : Int), (-2 : Int))]
      = labelsOf 0 := by rfl
  rw [hr] at he
  exact h he.symm"""


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — FUNCTIONAL RESHAPE. The imperative
#    accumulate-then-decide loop is replaced by a direct fold of the shared
#    selection step over the trials, with the same decision tail. Behaviourally
#    identical by the definition of the fold, and structurally different enough
#    that the frozen proof's loop-reduction step becomes unnecessary rather
#    than merely re-derivable: the re-proof DROPS that rewrite (and the closing
#    step that was tuned to it) and closes on the same obligation. MUST VERIFY,
#    else SPEC-TOO-STRONG.
# ===========================================================================
_pos_functional = _swap(
    _BASE,
    "def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do\n"
    + _I_BODY,
    "def implementation_fit_predict (trials : List (Int × Int)) : List Nat :=\n"
    "  match trials.foldl stepBest none with\n"
    "  | none => []\n"
    "  | some (bp, _) => labelsOf bp",
)
_pos_functional = _swap(
    _pos_functional,
    _P_OPEN,
    "  intro trials _\n"
    "  unfold implementation_fit_predict\n"
    "  constructor",
)
_pos_functional = _swap(
    _pos_functional,
    _P_CLOSE,
    "    | some p => rw [hf] at hb; obtain ⟨bp, bs⟩ := p; simp at hb; simp only [hb]",
)


# ===========================================================================
# 6. POSITIVE CONTROL (soundness) — BRANCH REORDER in the decision tail: the
#    trials-present arm is written before the no-trials arm. A `match` on the
#    same scrutinee denotes the same function whichever order its arms are
#    written in, so behaviour is unchanged and the frozen proof body still
#    closes verbatim; only the surface shape of the tail changes. This is the
#    cheapest honest reshape of the clause the rivals above attack, so it is the
#    control that says those rejections come from the spec and not from the tail
#    merely looking different. MUST VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================
_pos_tail_reorder = _swap(
    _BASE,
    _I_TAIL,
    "  match best with\n"
    "  | some (bp, _) => return labelsOf bp\n"
    "  | none => return []",
)


# ===========================================================================
# 7. POSITIVE CONTROL (soundness) — NAMED TAIL-RECURSIVE SELECTION. Added by the
#    audit: the two positives above both keep the frozen selection term itself
#    (`foldl stepBest`, reached either through the loop or directly), so neither
#    shows that the spec accepts an impl whose SELECTION is a differently-shaped
#    recursion. This one replaces it with an explicitly recursive helper over the
#    trial list and closes the obligation by proving that helper equal to the
#    fold — real re-proof work (an induction the frozen script does not contain),
#    on the byte-identical statement. MUST VERIFY, else SPEC-TOO-STRONG: an impl
#    that selects by structural recursion instead of by folding is a faithful
#    correct impl, and a spec that rejected it would be over-fitted to the
#    frozen selection's surface form.
# ===========================================================================
_pos_named_rec = _swap(
    _BASE,
    "def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do\n"
    + _I_BODY,
    "def bestGo : Option (Int × Int) → List (Int × Int) → Option (Int × Int)\n"
    "  | acc, [] => acc\n"
    "  | acc, t :: ts => bestGo (stepBest acc t) ts\n"
    "\n"
    "def implementation_fit_predict (trials : List (Int × Int)) : List Nat :=\n"
    "  match bestGo none trials with\n"
    "  | none => []\n"
    "  | some (bp, _) => labelsOf bp",
)
_pos_named_rec = _swap(
    _pos_named_rec,
    _P_OPEN,
    "  intro trials _\n"
    "  have hgo : ∀ (l : List (Int × Int)) (a : Option (Int × Int)),\n"
    "      bestGo a l = l.foldl stepBest a := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro a; rfl\n"
    "    | cons x xs ih => intro a; simp only [bestGo, List.foldl_cons, ih]\n"
    "  unfold implementation_fit_predict\n"
    "  rw [hgo]\n"
    "  constructor",
)
_pos_named_rec = _swap(
    _pos_named_rec,
    _P_CLOSE,
    "    | some p => rw [hf] at hb; obtain ⟨bp, bs⟩ := p; simp at hb; simp only [hb]",
)


# ===========================================================================
# 8. ADMISSIBILITY. Added by the audit: the nagini battery carried an
#    admissibility case (a self-call on an F2P-shaped multi-trial input, proving
#    the precondition admits it and the postcondition is usable), and this port
#    dropped it as having no instance. It HAS one. Lean has no precondition to
#    admit and no self-call, but the same content — "the modeled behavior is
#    SATISFIABLE at a normal F2P-shaped input, so the obligation the positives
#    discharge is not vacuous" — is expressible as a GROUND instance of the
#    postcondition, discharged before the frozen proof runs verbatim.
#
#    The input is the nagini case's own shape carried over: three trials, a TIE
#    for the maximum, and the best NOT last (scores 7, 9, 9 -> the second trial
#    wins). This is the one case in the battery that exercises tie-breaking and
#    non-last-best TOGETHER, and it is discharged by exhibiting the spec holding
#    rather than by refuting anything. MUST VERIFY, else PRECOND-TOO-STRONG /
#    unsatisfiable-at-a-normal-input.
# ===========================================================================
_L3 = "[((10 : Int), (7 : Int)), ((11 : Int), (9 : Int)), ((12 : Int), (9 : Int))]"

_admiss = _swap(
    _BASE,
    "  intro trials _\n",
    f"  have _ground : problem_spec_fit_predict {_L3}\n"
    f"      (implementation_fit_predict {_L3}) := by\n"
    f"    have hbp : bestParam {_L3} = some 11 := by rfl\n"
    "    constructor\n"
    "    · intro b hb\n"
    "      rw [hbp] at hb\n"
    "      have hb2 : (11 : Int) = b := by simpa using hb\n"
    "      subst hb2\n"
    "      rfl\n"
    "    · intro hb\n"
    "      rw [hbp] at hb\n"
    "      simp at hb\n"
    "  intro trials _\n",
)


SPEC_TESTS = [
    {
        "id": "report-final-trial-config",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _last_trial,
        "witness": _W_LAST,
        "refinement": (
            "The faithful real analogue derives the reported labels from the "
            "parameter state the run is left in after the final trial, while the "
            "estimator ends up holding the selected best trial's parameters. A "
            "later query of the same fitted estimator answers from the HELD "
            "(selected) parameters, so the two disagree on every multi-trial run "
            "whose best trial is not the last — which is precisely the reported "
            "defect. The F2P checks agreement between the labels returned by the "
            "fitting call and a subsequent query on a multi-trial configuration, "
            "so it FAILS -> would NOT resolve."
        ),
        "rationale": (
            "Rejection comes from the trials-present clause: the result must equal "
            "the label assignment of the SELECTED trial's configuration. The rival "
            "selects correctly but applies the label computation to the "
            "configuration of the last trial. The witness fixes a two-trial input "
            "whose best is FIRST at a strict maximum, where the selection "
            "evaluates to the first configuration and the rival's result "
            "evaluates to the last's; under the single hypothesis that the label "
            "computation separates those two configurations, the clause is "
            "refuted. Both sides of that inequality are one application of the "
            "callee, so the hypothesis is satisfiable."
        ),
    },
    {
        "id": "tie-displaces-earliest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tie_displaces,
        "witness": _W_TIE,
        "refinement": (
            "The real selection replaces its running best only on a STRICT "
            "improvement in the quality score, so the EARLIEST trial attaining "
            "the maximum is the one retained. A rival that also replaces on an "
            "exact match retains a different trial's parameters whenever the "
            "maximum is attained more than once; the fitted estimator then holds "
            "— and the fitting call reports — a different trial's answer than the "
            "canonical earliest-maximum selection. On a run with a repeated "
            "maximum the resulting labels differ from the gold ones, so a "
            "tie-bearing run would NOT resolve. (It also leaves the retained "
            "quality score attached to the wrong trial, which the surrounding "
            "selection assertions in the existing suite observe.)"
        ),
        "rationale": (
            "Also the trials-present clause, but attacked through the SELECTION "
            "rather than through the argument: the spec's selection keeps the "
            "earliest trial attaining the maximum, so on a tie the rival's "
            "running best is the later trial. This is a NEAR-MISS — it agrees "
            "with the frozen solution wherever the maximum is attained once — so "
            "its witness is stated AT a tie (two trials, equal scores), the only "
            "sub-domain where it is wrong. Under the single hypothesis that the "
            "label computation separates the two tied configurations, the clause "
            "is refuted."
        ),
    },
    {
        "id": "report-first-trial-config",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _first_trial,
        "witness": _W_FIRST,
        "refinement": (
            "The faithful real analogue reports the labels of the FIRST trial's "
            "parameters regardless of which trial scored best — the same class of "
            "defect as reporting the final trial's, and equally observable: the "
            "fitted estimator holds the selected best parameters, so a subsequent "
            "query disagrees with the returned labels on any multi-trial run whose "
            "best trial is not the first. The F2P compares exactly those two, on a "
            "multi-trial configuration, so it FAILS -> would NOT resolve. It also "
            "loses the standing guarantee that more trials cannot give a worse "
            "reported answer."
        ),
        "rationale": (
            "The trials-present clause again, at the MIRROR input: this rival is "
            "correct wherever the best trial is first, so it is refuted where the "
            "best trial is LAST at a strict maximum — the very point at which the "
            "final-trial rival above is correct. Giving it its own witness is what "
            "keeps each rival's claimed sub-domain demonstrated rather than "
            "asserted. Under the single hypothesis that the label computation "
            "separates the two configurations, the clause is refuted."
        ),
    },
    {
        "id": "final-trial-never-offered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop_last,
        "witness": _W_DROP_LAST,
        "refinement": (
            "The faithful real analogue runs the trial loop one short, so the last "
            "trial's parameters are never a selection candidate. Whenever that "
            "trial is the best one the estimator retains a worse trial's "
            "parameters, and with only one trial configured nothing is selected at "
            "all — the fitting call reports an answer produced by no trial while a "
            "trial demonstrably ran. That breaks the single-trial agreement the "
            "existing suite already relies on as well as the multi-trial F2P, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "The trials-present clause, attacked through the OUTPUT SHAPE rather "
            "than through the selection or the argument — which is why it is "
            "shipped alongside the argument-level rivals. On a single-trial input "
            "the rival returns the empty assignment although the selection "
            "plainly yields that trial, so the clause that pins the result to the "
            "callee's value at that trial is violated. It is NOT a second-clause "
            "case: the no-trials conjunct is dead under the obligation's "
            "hypothesis (machine-checked in the header) and nothing can be "
            "refuted on it. Its witness needs no separation hypothesis about two "
            "configurations, only that the label computation is non-empty at the "
            "one probed configuration — the weakest assumption the refutation "
            "needs, and satisfiable."
        ),
    },
    {
        "id": "report-score-not-config",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _score_projection,
        "witness": _W_PROJ,
        "refinement": (
            "The faithful real analogue derives the reported labels from the "
            "selected trial's QUALITY SCORE rather than from its parameter "
            "configuration — the right trial, read out through the wrong field of "
            "the record the selection carries. The estimator still holds the "
            "selected trial's parameters, so a subsequent query answers from those "
            "while the fitting call reports an assignment produced by an unrelated "
            "quantity; the two agree only in the degenerate case where the score "
            "and the configuration coincide. The F2P compares exactly those two on "
            "a multi-trial configuration, so it FAILS -> would NOT resolve."
        ),
        "rationale": (
            "The trials-present clause, attacked at the PROJECTION rather than at "
            "the selection or at which trial is reported: the spec pins the result "
            "to the label assignment of the selected trial's CONFIGURATION, and "
            "this rival applies the label computation to its score instead. Added "
            "by the audit because the other rivals all vary which trial is "
            "reported and none varies which COMPONENT of the selected trial is "
            "used — a confusion this carrier makes type-correct, since both "
            "components are the same type. The witness fixes the two-trial input "
            "[(70,3),(71,6)], whose selected pair is (71, 6): the selection "
            "evaluates to the configuration 71 and the rival's result to the "
            "labels of 6, so under the single hypothesis that the label "
            "computation separates those two the clause is refuted. Both sides "
            "are one application of the callee, so the hypothesis is satisfiable. "
            "The point is this rival's OWN — the best trial is LAST at a strict "
            "maximum here, so the final-trial rival is correct at this input and "
            "only the projection is wrong, which is what makes the projection "
            "sub-domain demonstrated rather than asserted. A prior draft refuted "
            "it at the final-trial rival's point instead, which made the "
            "manifest's distinct-points claim false."
        ),
    },
    {
        "id": "sentinel-seed-swallows-low-scores",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _sentinel_seed,
        "witness": _W_SENTINEL,
        "refinement": (
            "The faithful real analogue initialises the running best quality at a "
            "concrete zero rather than at an unbounded-below value, so a trial "
            "whose quality never rises above zero is never accepted and the "
            "estimator is left holding no fitted trial's parameters at all — it "
            "reports an assignment produced by the initial placeholder while real "
            "trials demonstrably ran. Quality scores in the real routine are "
            "log-likelihood-shaped and routinely non-positive, so this is not a "
            "corner: on such a run the reported labels are those of no trial, "
            "which disagrees with a subsequent query on the fitted estimator and "
            "with the single-trial agreement the existing suite relies on -> would "
            "NOT resolve."
        ),
        "rationale": (
            "The trials-present clause, attacked at the SEED. The frozen selection "
            "represents 'no trial accepted yet' by an absent accumulator, so the "
            "first trial is always accepted whatever its score; this rival "
            "represents it by a zero sentinel, so a trial is accepted only if it "
            "beats zero. It is a NEAR-MISS on the score coordinate — it agrees "
            "with the frozen solution on every input where some trial scores above "
            "the sentinel — so it is refuted where it is actually wrong: a single "
            "trial at a NEGATIVE score, where the selection plainly picks that "
            "trial and the rival reports the sentinel's labels. Added by the audit "
            "because every other rival keeps the frozen seed and states its "
            "refutation at positive scores, leaving the sentinel and the "
            "non-positive score sub-domain unprobed. Under the single hypothesis "
            "that the label computation separates the trial's configuration from "
            "the sentinel, the clause is refuted; both sides are one application "
            "of the callee, so the hypothesis is satisfiable."
        ),
    },
    {
        "id": "pos-control-functional-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_functional,
        "rationale": (
            "Structurally different, behaviourally identical: the imperative "
            "accumulate-then-decide loop is replaced by a direct fold of the "
            "shared selection step, with the same decision tail. Equal by the "
            "definition of the fold, so both postcondition clauses still hold. The "
            "re-proof is honest work on the SAME obligation — the statement is "
            "byte-identical and the loop-reduction rewrite the frozen script "
            "needed is dropped because the reshaped impl no longer has a loop to "
            "reduce (as is the closing step that was tuned to it). MUST verify, "
            "else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-tail-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_tail_reorder,
        "rationale": (
            "Cheapest honest reshape of the exact clause the rivals attack: the "
            "decision tail decides its two output branches in the opposite order. "
            "A `match` on one scrutinee denotes the same function whichever order "
            "its arms are written in, so the order is free; behaviour is "
            "unchanged and the frozen proof body closes verbatim. "
            "This is the control that makes the four rejections attributable to "
            "the spec rather than to a reshaped tail: it shows a merely "
            "RESHAPED tail still verifies, so the rivals' rejections are about "
            "which configuration is reported, not about the tail's surface form. "
            "MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-named-recursive-selection",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_named_rec,
        "rationale": (
            "Added by the audit. The other two positives both keep the frozen "
            "SELECTION term itself, so neither shows the spec accepts an impl that "
            "selects by a differently-shaped recursion; this one replaces the fold "
            "with an explicitly recursive helper over the trial list. "
            "Behaviourally identical, and the re-proof is genuine work on the "
            "byte-identical statement: it proves the helper equal to the frozen "
            "selection by an induction the frozen script does not contain, then "
            "closes the same obligation. Selecting by structural recursion instead "
            "of by folding is a faithful correct impl, so MUST verify, else "
            "SPEC-TOO-STRONG (the spec would be over-fitted to the frozen "
            "selection's surface form)."
        ),
    },
    {
        "id": "admiss-ground-tie-nonlast-best",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Added by the audit; the nagini battery's admissibility case, "
            "re-expressed rather than dropped. There is no precondition to admit "
            "and no self-call on this carrier, but the case's content carries over "
            "exactly: the modeled behavior must be SATISFIABLE at a normal "
            "F2P-shaped input, else every positive in this battery discharges a "
            "vacuous obligation. It is discharged as a GROUND instance of the "
            "postcondition at the sibling case's own input shape — three trials, "
            "the maximum score attained TWICE, and the winning trial neither first "
            "nor last — proven before the frozen proof body then runs verbatim. "
            "This is also the only case in the battery that exercises "
            "tie-breaking and a non-last best together, and the only one that "
            "establishes the spec by exhibiting it holding rather than by "
            "refuting a rival. MUST verify, else the modeled behavior would be "
            "unsatisfiable at exactly a normal multi-trial input."
        ),
    },
]

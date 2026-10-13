"""properties.py — G-PBT falsification battery for sympy__sympy-19954 (lean).

NOT a Lean file: a manifest the G-PBT gate executes. Every SPEC case is a
complete ``Solution.lean`` variant built by REGION SURGERY (``_swap``) that edits
only text inside ``-- impl-start``/``-- impl-end`` and — for the positives that
legitimately re-prove — inside ``-- proof-start``/``-- proof-end``. So
``markers.same_spec`` holds by construction, the single
``theorem correct_pruneSystems`` STATEMENT stays byte-identical, and any
rejection is attributable to the postcondition rather than to a tampered spec.
No case adds an ``axiom``, a helper ``theorem``/``lemma``, ``sorry``, ``admit``
or ``native_decide``.

``expect="verify"`` passes iff the variant is in scope AND elaborates with the
obligation genuinely closed. ``expect="reject"`` passes iff the variant is in
scope AND does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

PORT NOTE — this is a PORT of the nagini battery (``../nagini/properties.py``)
onto this backend's carrier, not a fresh invention and not a translation of its
text. The nagini sibling models the pruning step as
``prune_parallel(blocks, nums, reps, flag)``: three parallel lists filtered by
ONE externally-supplied boolean mask, pinned against the ``@Pure`` folds
``filtered``/``kept``. This Lean bundle models the SAME behavior but ONE LEVEL
WIDER: the mask is not an input here, it is COMPUTED by the modeled routine from
the candidate's representative cell against the retained cells, and the routine
also decides the candidate's own viability and the conditional append. So every
nagini rival ports as an attack on the aligned-prune half of this spec, and the
extra surface this carrier exposes (the scan predicates, the early exit, the
viability flag, the dedup membership test, the append) carries additional rivals
that nagini's narrower carrier could not express. See ``ASSESSMENT`` below for
the case-by-case correspondence and the omissions.

DEFENDED SURFACE (one modeled routine, one obligation).
``problem_spec_pruneSystems blocks numBlocks repBlocks block numBlock rep result``
pins ``result`` to a single grounded functional term, so the postcondition is an
EXACT equation rather than a list of independent conjuncts. Its independently
attackable sub-behaviors — each one an anchor some rival must be caught by — are:

  * (S1) the SCAN PREDICATES: a retained cell is flagged only when it is
    strictly larger than the candidate's cell AND contains it; the candidate is
    rejected only when a retained cell is strictly smaller AND contained in it.
    Both comparisons are strict in cardinality, and BOTH strictnesses are
    probed independently (``scan-nonstrict-supersession`` drops the first,
    ``scan-nonstrict-domination`` the second).
  * (S2) the EARLY EXIT: on rejecting the candidate the scan stops and every
    remaining index is left unflagged.
  * (S3) the ALIGNED PRUNE — the load-bearing clause, and the one the nagini
    battery is entirely about: all THREE collections are filtered by the SAME
    single mask, so they keep exactly the same surviving indices in the same
    order. Never one collection by position while another goes by value, and
    never one collection under a different mask than the others.
  * (S4) the VIABILITY GUARD: the candidate is appended only if it survived the
    scan.
  * (S5) the DEDUP TEST: membership of the candidate's numbering is tested
    against the SURVIVING numberings, i.e. AFTER the prune — a numbering sitting
    at a removed index must not block the append.
  * (S6) the APPEND: the candidate's three pieces of data go to all three
    collections together, preserving alignment.

BINDER STRUCTURE. The spec predicate has SIX input binders — ``blocks``,
``numBlocks``, ``repBlocks``, ``block``, ``numBlock``, ``rep``. Every one is
load-bearing and every one is VARIED across the reject witnesses: the twelve
rivals are refuted at DISTINCT input tuples, spanning the zero-flag, one-flag
and two-flag mask domains, the candidate-rejected domain, BOTH equal-cell
boundaries (the flagging comparison's and the rejecting comparison's), the
duplicate-numbering-at-a-removed-index corner, the flag value AT the rejecting
index and the mask's PAD DEFAULT over the tail the scan never reached. No binder
is held constant across the witnesses, so no rival that mishandled exactly one
input could slip through unprobed.

POSITIVES AND DEFINITIONAL EQUALITY — read this before trusting the soundness
lane. The obligation is an EXACT equation ``result = pruneSystems ...``, and the
frozen script closes its tail with ``rfl``. So a reshape that is definitionally
equal to the frozen impl is closed by the frozen script UNCHANGED, and such a
positive verifies without testing whether the postcondition is over-fit — it only
re-confirms that Lean's ``rfl`` sees through a ``let``. Three of the positives
here (``pos-prune-through-triple``, ``pos-guard-through-local``,
``pos-named-scan-predicates``) are of exactly that kind: measured, each one's
impl edit alone is closed by the FROZEN proof region with no proof authoring at
all. They are kept as cheap regression controls, but they are not evidence
against SPEC-TOO-STRONG. ``pos-scan-arms-reordered`` is the one that is: swapping
the scan's two decision arms is behavior-preserving (the guards are mutually
exclusive on cardinality) yet NOT definitional, the frozen ``rfl`` fails on it,
and the case has to re-derive all three branches of the reification lemma under a
reversed ``split_ifs`` binding — including obtaining ``supersededBy rep r =
false`` from ``r.card < rep.card`` arithmetically. That is the positive lane's
actual load.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate's NEGATION at one
concrete input. This carrier computes: the collections are list literals and the
cells are ``Finset Nat`` literals, so ``decide`` reduces both sides in full and
each witness is three lines. Each binds NOTHING in its head (all inputs are
ground literals), so there are no hypotheses whose joint satisfiability could be
in question and no conditioning on an opaque term is needed anywhere. Each of
the twelve was checked with two real ``lake env lean`` builds: it HOLDS of its
rival and FAILS on the frozen solution, so it discriminates rather than
asserting a tautology. Each was additionally checked with the FORGERY pair (the
same statement with the ``¬`` dropped): the flipped claim ELABORATES against the
frozen solution and FAILS against the rival, byte-inverting both exit codes, so
each gold-side exit code demonstrably tracks the claim rather than a syntactic
accident. Every gold-side failure is a plain evaluation — ``Tactic `decide`
proved that the proposition ... is false`` — with no stuck reduction, no missing
``Decidable`` instance and no unification failure anywhere in the battery.

AXIOM lane: the ``axioms`` region declares no ``opaque`` callee and the bundle
consumes no ``axiom`` (the changed operation is modeled deeply), so nagini's
``AXIOM_TESTS`` — empty there too — are dropped; that lane is G-AX's job.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19954"
BACKEND = "lean"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence of a region substring; assert it matched,
    so silent drift (Solution.lean edited) fails loudly at manifest load."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ===========================================================================
# REGION ANCHORS — each verified unique inside Solution.lean at load time.
# ===========================================================================

# --- impl region ---
def _scan_branch(indent, named):
    """The scan's three-way decision, at a given indentation. `named=False` is
    the frozen spelling (comparisons written out); `named=True` spells the same
    two decisions through the pure predicates the spec region already defines."""
    p = " " * indent
    hi = "supersededBy rep r" if named else "r.card > rep.card && rep ⊆ r"
    lo = "dominates rep r" if named else "r.card < rep.card && r ⊆ rep"
    return (f"{p}if {hi} then\n"
            f"{p}  mask := mask ++ [true]\n"
            f"{p}else if {lo} then\n"
            f"{p}  minimal := false\n"
            f"{p}  break\n"
            f"{p}else\n"
            f"{p}  mask := mask ++ [false]")


# the mask-driven filter of all three collections (the aligned prune, S3)
_I_PRUNE3 = """  let blocks' := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask
  let repBlocks' := dropFlagged repBlocks mask"""

# the accumulate-then-pad prologue that precedes the prune
_I_SCAN_ALL = """  let mut minimal := true
  let mut mask : List Bool := []
  for r in repBlocks do
""" + _scan_branch(4, named=False) + """
  mask := mask ++ List.replicate (repBlocks.length - mask.length) false
""" + _I_PRUNE3

# the append guard (S4 + S5) and the append itself (S6)
_I_GUARD = "  if minimal && !(numBlocks'.contains numBlock) then"
_I_APPEND = ("    return (blocks' ++ [block], numBlocks' ++ [numBlock], "
             "repBlocks' ++ [rep])")

# --- proof region (touched ONLY by the positives that re-prove) ---
_P_INTRO = "  intro blocks numBlocks repBlocks block numBlock rep"

# The scan block is restated three more times inside the proof region (once in
# the reification lemma, once in each of the two lemmas that consume it). Each
# restatement is anchored together with enough of its own head to be unique.
_P_REIFY_SCAN = """      (Id.run do
        let mut minimal := true
        let mut mask : List Bool := acc
        for r in L do
""" + _scan_branch(10, named=False)

_P_LOOPEQ_SCAN = """theorem loop_scan_eq (rep : Finset Nat) (repBlocks : List (Finset Nat)) :
    (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
""" + _scan_branch(8, named=False)

_P_TAILEQ_SCAN = """    (hloop : (Id.run do
      let mut minimal := true
      let mut mask : List Bool := []
      for r in repBlocks do
""" + _scan_branch(8, named=False)

# the reification lemma's first branch re-derives the flagging decision from the
# raw `split_ifs` hypothesis; with the decision spelled through the named
# predicate that step needs its own unfolding.
_P_HS_DIRECT = "      have hs : supersededBy rep r = true := h1"


def _named_scan_everywhere(src):
    """Spell BOTH scan decisions through the pure predicates, in the impl and in
    all three proof-region restatements (which must agree with the impl for the
    reification lemma to still apply)."""
    return _swaps(
        src,
        (_scan_branch(4, named=False), _scan_branch(4, named=True)),
        (_P_REIFY_SCAN,
         _P_REIFY_SCAN.replace(_scan_branch(10, named=False),
                               _scan_branch(10, named=True))),
        (_P_LOOPEQ_SCAN,
         _P_LOOPEQ_SCAN.replace(_scan_branch(8, named=False),
                                _scan_branch(8, named=True))),
        (_P_TAILEQ_SCAN,
         _P_TAILEQ_SCAN.replace(_scan_branch(8, named=False),
                                _scan_branch(8, named=True))),
        (_P_HS_DIRECT,
         "      have hs : supersededBy rep r = true := by\n"
         "        simpa [supersededBy] using h1"),
    )


# --- the ARM-REORDERED scan (the positive that is NOT definitional) ---
# The frozen scan tests the flagging comparison first; this tests the REJECTING
# one first. The two guards are mutually exclusive (one needs `r.card > rep.card`,
# the other `r.card < rep.card`), so the decision is unchanged on every input —
# but the `if`-trees are NOT definitionally equal, so the frozen `rfl` no longer
# closes the tail and the branch order has to be reproven from the cardinality
# antisymmetry. That is what makes this positive load-bearing where a
# defeq-preserving reshape is not.
def _reordered_scan(indent):
    p = " " * indent
    return (f"{p}if r.card < rep.card && r ⊆ rep then\n"
            f"{p}  minimal := false\n"
            f"{p}  break\n"
            f"{p}else if r.card > rep.card && rep ⊆ r then\n"
            f"{p}  mask := mask ++ [true]\n"
            f"{p}else\n"
            f"{p}  mask := mask ++ [false]")


# The reification lemma's `split_ifs` now binds the hypotheses in the OPPOSITE
# order: `h1` is the domination test, `h2` the supersession test. So each of the
# three branches has to be re-derived, and the first branch additionally needs
# `supersededBy rep r = false` — which does NOT follow syntactically any more
# (the frozen file got it from the failed first `if`) and must come from
# `r.card < rep.card` by arithmetic.
_P_CONS_FROZEN = """    simp only [List.forIn_cons, bind, pure, Id.run]
    split_ifs with h1 h2
    · -- superseded: mask ++ [true], continue
      have hs : supersededBy rep r = true := h1
      rw [scanReps_cons_super rep r rs hs]
      have hih := ih (acc ++ [true])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]
    · -- dominated: break
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hd : dominates rep r = true := by
        simpa [dominates] using h2
      rw [scanReps_cons_dom rep r rs hs hd]
      dsimp only
      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
      rw [List.replicate_succ]
    · -- neither: mask ++ [false], continue
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h1
      have hnd : dominates rep r = false := by
        simpa [dominates] using h2
      rw [scanReps_cons_neither rep r rs hs hnd]
      have hih := ih (acc ++ [false])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]"""

_P_CONS_REORDERED = """    simp only [List.forIn_cons, bind, pure, Id.run]
    split_ifs with h1 h2
    · -- dominated (tested FIRST in this shape): break
      have hd : dominates rep r = true := by
        simpa [dominates] using h1
      have hs : supersededBy rep r = false := by
        have hlt : r.card < rep.card := by
          simp only [Bool.and_eq_true, decide_eq_true_eq] at h1
          exact h1.1
        simp only [supersededBy, gt_iff_lt, Bool.and_eq_false_iff,
                   decide_eq_false_iff_not, not_lt]
        exact Or.inl (by omega)
      rw [scanReps_cons_dom rep r rs hs hd]
      dsimp only
      rw [show acc.length + (r::rs).length - acc.length = rs.length + 1 by simp]
      rw [List.replicate_succ]
    · -- superseded: mask ++ [true], continue
      have hs : supersededBy rep r = true := by
        simpa [supersededBy] using h2
      rw [scanReps_cons_super rep r rs hs]
      have hih := ih (acc ++ [true])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[true]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]
    · -- neither: mask ++ [false], continue
      have hs : supersededBy rep r = false := by
        simpa [supersededBy] using h2
      have hnd : dominates rep r = false := by
        simpa [dominates] using h1
      rw [scanReps_cons_neither rep r rs hs hnd]
      have hih := ih (acc ++ [false])
      simp only [bind, pure, Id.run] at hih
      dsimp only
      rw [show acc.length + (r::rs).length = (acc++[false]).length + rs.length by simp; omega]
      rw [hih]; simp [List.append_assoc]"""


def _reordered_scan_everywhere(src):
    """Swap the scan's two decision arms in the impl and in all three
    proof-region restatements, and re-derive the reification lemma's three
    branches under the reversed `split_ifs` binding."""
    return _swaps(
        src,
        (_scan_branch(4, named=False), _reordered_scan(4)),
        (_P_REIFY_SCAN,
         _P_REIFY_SCAN.replace(_scan_branch(10, named=False),
                               _reordered_scan(10))),
        (_P_LOOPEQ_SCAN,
         _P_LOOPEQ_SCAN.replace(_scan_branch(8, named=False),
                                _reordered_scan(8))),
        (_P_TAILEQ_SCAN,
         _P_TAILEQ_SCAN.replace(_scan_branch(8, named=False),
                                _reordered_scan(8))),
        (_P_CONS_FROZEN, _P_CONS_REORDERED),
    )


# ===========================================================================
# WITNESS helper — the spec predicate's negation at one ground input.
# ===========================================================================
_F = "Finset Nat"


def _w(blocks, numBlocks, repBlocks, block, numBlock, rep):
    a = f"{blocks} {numBlocks} {repBlocks} {block} {numBlock} {rep}"
    return (f"example : ¬ problem_spec_pruneSystems {a}\n"
            f"    (implementation_pruneSystems {a}) := by\n"
            "  unfold problem_spec_pruneSystems\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else the spec is over-fit to the frozen
    # shape (SPEC-TOO-STRONG). Each keeps the `correct_pruneSystems` STATEMENT
    # byte-identical and adds no declaration. All three were confirmed by a real
    # build to elaborate with the obligation closed.
    # =====================================================================
    {
        "id": "pos-prune-through-triple",
        "kind": "soundness",
        "expect": "verify",
        # Build the three pruned collections as ONE tuple and project the
        # components out, instead of three sibling bindings. Same values, one
        # more level of structure between the filter and the append.
        "module": _swap(_BASE, _I_PRUNE3, """  let pruned := (dropFlagged blocks mask, dropFlagged numBlocks mask,
    dropFlagged repBlocks mask)
  let blocks' := pruned.1
  let numBlocks' := pruned.2.1
  let repBlocks' := pruned.2.2"""),
        "rationale": "CORRECT reshape of the aligned prune (S3): the three "
                     "filtered collections are produced as one tuple and then "
                     "projected, rather than bound side by side. Every "
                     "collection is still filtered by the SAME mask, so the "
                     "result is unchanged on every input and the obligation "
                     "must still close — if it does not, the postcondition is "
                     "over-fit to the frozen spelling of the prune rather than "
                     "to its behavior (SPEC-TOO-STRONG). The frozen tactic "
                     "script closes it unchanged (the projections are "
                     "definitionally the bindings), so no proof authoring, no "
                     "helper lemma, no assumption token. Ports the nagini "
                     "pos-control-local-reshape positive, whose point was the "
                     "same: the spec must not pin the executable spelling of "
                     "the per-position survivor bookkeeping.",
    },
    {
        "id": "pos-named-scan-predicates",
        "kind": "soundness",
        "expect": "verify",
        # The scan's two decisions are spelled through the pure predicates the
        # spec region already defines, instead of written out inline. This is the
        # positive that actually RE-PROVES: the reification lemma's statement
        # must be restated in the same shape for it to apply, and its first
        # branch then needs the predicate unfolded to recover the flagging
        # hypothesis.
        "module": _named_scan_everywhere(_BASE),
        "rationale": "CORRECT reshape of the scan predicates (S1/S2): both "
                     "comparisons are spelled through the named pure predicates "
                     "instead of inline, so the SAME mask and the SAME viability "
                     "flag are computed on every input, with the same early "
                     "exit. Must verify, else the spec is over-fit to the inline "
                     "spelling of the comparisons (SPEC-TOO-STRONG). Re-proved "
                     "honestly inside the proof region: the loop-reification "
                     "lemma's own statement is restated in the reshaped form "
                     "(otherwise it no longer applies to the reshaped loop) and "
                     "its flagged branch unfolds the predicate to recover the "
                     "decision hypothesis. Statement byte-identical, no new "
                     "declaration, no assumption token. Ports nagini's "
                     "pos-control-branch-reorder, which likewise re-expressed "
                     "the removal decision without changing it.",
    },
    {
        "id": "pos-guard-through-local",
        "kind": "soundness",
        "expect": "verify",
        # The append guard (S4 && S5) is bound to a named local and then tested.
        "module": _swap(_BASE, _I_GUARD,
                        "  let keepCandidate := minimal && "
                        "!(numBlocks'.contains numBlock)\n"
                        "  if keepCandidate then"),
        "rationale": "CORRECT reshape of the append guard (S4+S5): the "
                     "conjunction of viability and not-already-present is bound "
                     "to a named local and then tested, rather than tested "
                     "inline. Identical decision on every input, so it must "
                     "verify; if it does not, the spec is over-fit to the "
                     "guard's spelling (SPEC-TOO-STRONG). Closed by the frozen "
                     "script (the local is definitionally the guard). Covers the "
                     "same 'the spec must not pin the executable form' concern "
                     "the nagini positives raise, at the one decision point "
                     "nagini's carrier does not have (its mask is an input, so "
                     "it has no viability guard to reshape).",
    },

    {
        "id": "pos-scan-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # The scan tests the REJECTING comparison before the flagging one. The
        # two guards are mutually exclusive on cardinality, so the computed mask
        # and viability flag are unchanged — but the `if`-trees are NOT
        # definitionally equal, so this positive cannot be closed by the frozen
        # `rfl` and has to be genuinely reproven.
        "module": _reordered_scan_everywhere(_BASE),
        "rationale": "CORRECT reshape of the scan (S1/S2) that is NOT "
                     "definitional, which is what distinguishes it from the "
                     "other three positives here. The two decision arms are "
                     "swapped: the rejecting comparison is tested before the "
                     "flagging one. Because one guard requires "
                     "`r.card > rep.card` and the other `r.card < rep.card`, at "
                     "most one can hold, so the same mask, the same viability "
                     "flag and the same early exit are computed at every input "
                     "and the obligation must still close. It is the "
                     "load-bearing positive precisely because the frozen tactic "
                     "script does NOT close it: swapping the arms changes the "
                     "`if`-tree, `rfl` fails on the reshaped tail, and the "
                     "reification lemma's `split_ifs` binds its two hypotheses "
                     "in the OPPOSITE order — so all three branches are "
                     "re-derived, and the flagged branch must additionally "
                     "obtain `supersededBy rep r = false` from "
                     "`r.card < rep.card` by arithmetic rather than reading it "
                     "off a failed first `if`. That is the mutual exclusion of "
                     "the two comparisons being reproven for a new impl shape, "
                     "not restated. Statement byte-identical, no new "
                     "declaration, no assumption token. This is the faithful "
                     "port of nagini's pos-control-branch-reorder, which swapped "
                     "the arms of the removal decision; the previously shipped "
                     "port of that case (pos-named-scan-predicates) turned out "
                     "to be definitionally equal to the frozen impl, so it could "
                     "not have detected an over-fit postcondition.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE, non-vacuously, at a normal
    # in-domain input. nagini's admissibility case self-calls to show the
    # Requires can be ESTABLISHED; the frozen obligation here carries no
    # precondition binder at all, so the corresponding question is whether the
    # modeled behavior is actually inhabited at a load-bearing input rather than
    # only at a degenerate one. Discharged by evaluation at a TWO-REMOVAL input
    # (the domain the reported failure lives in) as a `have`, then the frozen
    # obligation is closed verbatim.
    # =====================================================================
    {
        "id": "admiss-ground-two-removals",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, """  have _ground : problem_spec_pruneSystems [[7], [8]] [[1], [2]]
      [({0, 1} : Finset Nat), ({0, 2} : Finset Nat)] [9] [3] ({0} : Finset Nat)
      (implementation_pruneSystems [[7], [8]] [[1], [2]]
        [({0, 1} : Finset Nat), ({0, 2} : Finset Nat)] [9] [3] ({0} : Finset Nat)) := by
    unfold problem_spec_pruneSystems
    decide
""" + _P_INTRO),
        "rationale": "the obligation is discharged BY EVALUATION at a concrete "
                     "in-domain input with TWO retained systems both flagged for "
                     "removal — precisely the >=2-removal domain the reported "
                     "failure occupies — as a `have`, and the frozen obligation "
                     "is then closed verbatim. Must verify: if the spec were "
                     "unsatisfiable at exactly a normal, load-bearing input, "
                     "every positive would be passing over a vacuous "
                     "obligation, the analogue of nagini's PRECOND-TOO-STRONG. "
                     "Ports nagini's admiss-selfcall-empty-parallel, but at the "
                     "two-removal point rather than the empty one: with no "
                     "precondition to establish, the degenerate input would "
                     "demonstrate nothing about the domain that matters.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P, and
    # (b) a witness, checked by two real builds, pinning the violation at one
    # concrete input.
    # =====================================================================

    # ---- the headline rival: the pre-fix desynchronisation (nagini's #2) ----
    {
        "id": "desync-running-index-prune",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: two of the three collections are shortened by the
        # RUNNING INDEX while the scan is still in progress, and the third is
        # pruned afterwards by VALUE. The counter then no longer addresses the
        # intended entries.
        "module": _swap(_BASE, _I_SCAN_ALL, """  let mut blocks' := blocks
  let mut numBlocks' := numBlocks
  let mut toRemove : List (Finset Nat) := []
  let mut minimal := true
  let mut i := 0
  for r in repBlocks do
    if supersededBy rep r then
      blocks' := blocks'.eraseIdx i
      numBlocks' := numBlocks'.eraseIdx i
      toRemove := toRemove ++ [r]
    else if dominates rep r then
      minimal := false
      break
    i := i + 1
  let repBlocks' := repBlocks.filter (fun r => !(toRemove.contains r))"""),
        "refinement": "this IS the reported defect. The faithful real "
                      "counterpart shortens two of the three parallel "
                      "collections in place, by the scan's own running index, "
                      "while that scan is still walking the third; the third is "
                      "then pruned separately by value. As soon as a second "
                      "system is flagged the counter addresses an entry that "
                      "has already shifted, so the wrong row is discarded — or, "
                      "in the real code, the index has run past the end of the "
                      "already-shortened collection and the routine raises "
                      "instead of returning, which is exactly the crash in the "
                      "report. Either way the F2P group-order assertions are "
                      "never reached or are computed from misaligned "
                      "collections, so the faithful patch definitively does NOT "
                      "resolve.",
        "rationale": "REJECT from S3 (the aligned prune): the spec pins all "
                     "three collections to the SAME mask filter, but this rival "
                     "prunes two by shifting position and one by value. Refuted "
                     "at a TWO-removal input (both retained cells strictly "
                     "contain the candidate's cell): the shifted counter leaves "
                     "the second flagged entry in place, so two collections "
                     "retain a system the mask removed while the third does not "
                     "— the three results no longer describe the same surviving "
                     "systems and their lengths disagree.",
        "witness": _w("[[7], [8]]", "[[1], [2]]",
                      f"[({{0, 1}} : {_F}), ({{0, 2}} : {_F})]",
                      "[9]", "[3]", f"({{0}} : {_F})"),
    },

    # ---- one collection under a DIFFERENT mask than the other two (nagini #3) ----
    {
        "id": "wrong-mask-one-collection",
        "kind": "uniqueness",
        "expect": "reject",
        # The numbering collection is filtered by the COMPLEMENT of the shared
        # mask; the other two use the mask itself.
        "module": _swap(
            _BASE,
            """  let blocks' := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks mask""",
            """  let blocks' := dropFlagged blocks mask
  let numBlocks' := dropFlagged numBlocks (mask.map (fun m => !m))"""),
        "refinement": "the faithful real counterpart applies an inverted (or "
                      "simply different) removal condition to one of the three "
                      "parallel collections than to the other two. The k-th "
                      "surviving numbering then no longer belongs to the k-th "
                      "surviving system: the numbering collection keeps exactly "
                      "the entries that were supposed to go and drops the "
                      "survivors. Every downstream consumer that reads a "
                      "numbering positionally — including the duplicate check on "
                      "the very next candidate — is then reading another "
                      "system's data, so the set of retained systems is wrong "
                      "and the F2P subgroup-order assertions fail. NOT "
                      "resolving.",
        "rationale": "REJECT from S3: the spec filters all three collections by "
                     "ONE mask; this rival filters one by the complement. "
                     "Refuted at a MIXED-mask input (index 0 flagged, index 1 "
                     "untouched, candidate viable and appended), where the "
                     "numbering collection retains the flagged system's "
                     "numbering and loses the survivor's — a distinct sub-domain "
                     "from the two-removal witness above, since here the mask is "
                     "neither all-true nor all-false.",
        "witness": _w("[[7], [8]]", "[[1], [2]]",
                      f"[({{0, 1}} : {_F}), ({{5}} : {_F})]",
                      "[4]", "[6]", f"({{0}} : {_F})"),
    },

    # ---- ignore the mask entirely (nagini #4, partial-domain keep-all) ----
    {
        "id": "partial-never-prune",
        "kind": "uniqueness",
        "expect": "reject",
        # The mask is computed but never applied: nothing is ever removed.
        "module": _swap(_BASE, _I_PRUNE3, """  let blocks' := blocks
  let numBlocks' := numBlocks
  let repBlocks' := repBlocks"""),
        "refinement": "the faithful real counterpart computes the removal "
                      "decision and then never acts on it, leaving all three "
                      "collections unpruned. Superseded systems — the ones the "
                      "arriving candidate has just shown to be non-coarsest — "
                      "are all retained, so the routine accumulates strictly "
                      "more systems than it should and the F2P assertions on the "
                      "resulting subgroup orders read the wrong count. Correct "
                      "only on the sub-domain where nothing is ever flagged, "
                      "which is not the sub-domain the report is about. NOT "
                      "resolving.",
        "rationale": "REJECT from S3: whenever any index is flagged, the spec's "
                     "filtered collections are strictly shorter than the inputs "
                     "while the rival returns them untouched. Refuted at a "
                     "ONE-removal input with a single retained system that the "
                     "candidate supersedes — the smallest point at which "
                     "ignoring the mask is observable, and a third distinct mask "
                     "shape (all-true over a length-1 collection).",
        "witness": _w("[[6]]", "[[8]]", f"[({{0, 3}} : {_F})]",
                      "[1]", "[2]", f"({{0}} : {_F})"),
    },

    # ---- over-prune (nagini #5, partial-domain drop-all) ----
    {
        "id": "partial-prune-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # Every retained system is discarded regardless of the mask.
        "module": _swap(_BASE, _I_PRUNE3, """  let blocks' : List (List Int) := []
  let numBlocks' : List (List Nat) := []
  let repBlocks' : List (Finset Nat) := []"""),
        "refinement": "the faithful real counterpart over-prunes: it clears the "
                      "retained collections instead of removing only the flagged "
                      "entries. Coarsest systems that must survive are thrown "
                      "away, so the routine ends up reporting far fewer systems "
                      "than it should and the F2P subgroup-order assertions "
                      "again read the wrong value. Correct only on the "
                      "sub-domain where every retained system happens to be "
                      "flagged. NOT resolving.",
        "rationale": "REJECT from S3: the spec keeps every unflagged entry; this "
                     "rival keeps none. Refuted at a NO-removal input — one "
                     "retained system whose cell neither contains nor is "
                     "contained in the candidate's, so the mask is all-false and "
                     "the spec must keep the entry the rival drops. A fourth "
                     "distinct mask shape, and the one that separates this rival "
                     "from the never-prune rival above (they agree wherever the "
                     "mask is all-true).",
        "witness": _w("[[7]]", "[[1]]", f"[({{5}} : {_F})]",
                      "[9]", "[3]", f"({{0}} : {_F})"),
    },

    # ---- rivals against surface nagini's carrier does not expose ----
    # nagini receives the mask and the survivor decision as INPUTS, so it cannot
    # express a rival that computes them wrongly. This carrier can, and each of
    # these attacks a distinct sub-behavior (S2, S5, S4, S1, S6).
    {
        "id": "scan-no-early-exit",
        "kind": "uniqueness",
        "expect": "reject",
        # The scan keeps going after the candidate has been rejected, so later
        # indices are still flagged for removal.
        "module": _swap(_BASE, _scan_branch(4, named=False), """    if r.card > rep.card && rep ⊆ r then
      mask := mask ++ [true]
    else if r.card < rep.card && r ⊆ rep then
      minimal := false
      mask := mask ++ [false]
    else
      mask := mask ++ [false]"""),
        "refinement": "the faithful real counterpart drops the early exit, "
                      "continuing the comparison after the arriving candidate has "
                      "already been found non-coarsest. Retained systems further "
                      "along are then removed on behalf of a candidate that is "
                      "itself discarded: the routine loses systems that nothing "
                      "in the retained set supersedes, and nothing is added in "
                      "their place. The surviving set is strictly too small, so "
                      "the F2P subgroup-order assertions fail. NOT resolving.",
        "rationale": "REJECT from S2 (the early exit): the spec leaves every "
                     "index after the rejecting one unflagged; this rival "
                     "continues flagging. Refuted at an input where the FIRST "
                     "retained cell rejects the candidate and the SECOND would "
                     "otherwise be flagged — so the rival deletes the second "
                     "system while the spec keeps both and appends nothing. A "
                     "candidate-rejected point, a sub-domain none of the "
                     "mask-shape witnesses above reaches.",
        "witness": _w("[[7], [8]]", "[[1], [2]]",
                      f"[({{0}} : {_F}), ({{0, 1, 2}} : {_F})]",
                      "[5]", "[8]", f"({{0, 1}} : {_F})"),
    },
    {
        "id": "dedup-against-unpruned",
        "kind": "uniqueness",
        "expect": "reject",
        # The duplicate check consults the numberings from BEFORE the prune.
        "module": _swap(_BASE, _I_GUARD,
                        "  if minimal && !(numBlocks.contains numBlock) then"),
        "refinement": "the faithful real counterpart performs the "
                      "already-present check against the collection as it stood "
                      "BEFORE the removal instead of after it. A candidate whose "
                      "numbering matches a system that the same step has just "
                      "removed is then wrongly treated as a duplicate and is not "
                      "recorded — so that step removes a system and adds nothing, "
                      "and a coarsest system is permanently lost. This is a "
                      "NEAR-MISS: it agrees with the correct behavior everywhere "
                      "except when the duplicate numbering sits at a removed "
                      "index, which is exactly why it needs its own witness at "
                      "that input rather than sharing one. On the F2P inputs the "
                      "arriving candidate is precisely the coarser system "
                      "replacing the one being removed, so the lost system "
                      "changes the retained count and the asserted subgroup "
                      "orders. NOT resolving.",
        "rationale": "REJECT from S5 (dedup against the SURVIVORS): the spec "
                     "tests membership after the prune. Refuted at the corner "
                     "that isolates the difference — one retained system, "
                     "flagged for removal, whose numbering EQUALS the "
                     "candidate's. The spec removes it and appends the "
                     "candidate; the rival sees the stale numbering, suppresses "
                     "the append, and returns all three collections empty. No "
                     "other witness in this battery visits that point.",
        "witness": _w("[[7]]", "[[1]]", f"[({{0, 1}} : {_F})]",
                      "[9]", "[1]", f"({{0}} : {_F})"),
    },
    {
        "id": "append-ignores-viability",
        "kind": "uniqueness",
        "expect": "reject",
        # The candidate is appended even when the scan rejected it.
        "module": _swap(_BASE, _I_GUARD,
                        "  if !(numBlocks'.contains numBlock) then"),
        "refinement": "the faithful real counterpart records the arriving "
                      "candidate unconditionally, ignoring the flag that says a "
                      "retained system already supersedes it. A system known to "
                      "be non-coarsest is then kept alongside the coarser one "
                      "that dominates it, so the retained set is strictly too "
                      "large and, being order-dependent, also feeds the next "
                      "candidate's comparisons with an entry that should not be "
                      "there. The F2P subgroup-order assertions read the "
                      "inflated count. NOT resolving.",
        "rationale": "REJECT from S4 (the viability guard): the spec appends "
                     "only if the candidate survived the scan. Refuted at an "
                     "input where the single retained cell is strictly smaller "
                     "than and contained in the candidate's cell, so the "
                     "candidate is rejected: the spec returns the collections "
                     "unchanged, the rival appends anyway. Distinct from the "
                     "no-early-exit witness (there the rejection point is "
                     "followed by a floggable index; here it is not, so only the "
                     "append differs).",
        "witness": _w("[[3]]", "[[4]]", f"[({{2}} : {_F})]",
                      "[6]", "[7]", f"({{1, 2}} : {_F})"),
    },
    {
        "id": "scan-nonstrict-supersession",
        "kind": "uniqueness",
        "expect": "reject",
        # The flagging test drops its strictness in cardinality: a retained cell
        # merely containing the candidate's — including an EQUAL one — is flagged.
        "module": _swap(_BASE, _scan_branch(4, named=False), """    if rep ⊆ r then
      mask := mask ++ [true]
    else if r.card < rep.card && r ⊆ rep then
      minimal := false
      break
    else
      mask := mask ++ [false]"""),
        "refinement": "the faithful real counterpart tests containment without "
                      "requiring the retained cell to be strictly larger, so a "
                      "retained system whose representative cell EQUALS the "
                      "candidate's is treated as superseded. An equal system is "
                      "removed and the candidate put in its place: where the "
                      "two carry the same numbering the retained set churns "
                      "without settling, and where they differ the same "
                      "partition is recorded twice under different data. Either "
                      "way the retained collection no longer holds one entry per "
                      "distinct coarsest system, and the F2P subgroup-order "
                      "assertions fail. NOT resolving.",
        "rationale": "REJECT from S1 (strictness of the flagging comparison): "
                     "the spec flags only strictly larger containing cells. "
                     "Refuted at the EQUAL-cell boundary — one retained cell "
                     "identical to the candidate's, with the same numbering. The "
                     "spec flags nothing and suppresses the append (the "
                     "numbering is already present), so the input is returned "
                     "unchanged; the rival flags the entry, prunes it, then "
                     "appends the candidate's own data in its place. That "
                     "boundary point is reached by no other witness here.",
        "witness": _w("[[7]]", "[[1]]", f"[({{0}} : {_F})]",
                      "[9]", "[1]", f"({{0}} : {_F})"),
    },
    {
        "id": "scan-nonstrict-domination",
        "kind": "uniqueness",
        "expect": "reject",
        # The REJECTING test drops its strictness in cardinality: a retained
        # cell merely contained in the candidate's — including an EQUAL one —
        # rejects the candidate. The mirror image of the case above, which drops
        # the strictness of the FLAGGING test; each comparison has its own
        # cardinality strictness and one rival can only pin one of them.
        "module": _swap(_BASE, _scan_branch(4, named=False), """    if r.card > rep.card && rep ⊆ r then
      mask := mask ++ [true]
    else if r.card <= rep.card && r ⊆ rep then
      minimal := false
      break
    else
      mask := mask ++ [false]"""),
        "refinement": "the faithful real counterpart tests the reverse "
                      "containment without requiring the retained cell to be "
                      "strictly smaller, so a retained system whose "
                      "representative cell EQUALS the candidate's is treated as "
                      "already superseding it and the candidate is discarded. A "
                      "genuinely new coarsest system that merely happens to "
                      "share a representative cell with a retained one — same "
                      "cell, different numbering, hence a DIFFERENT system — is "
                      "then never recorded, so the retained collection is "
                      "permanently short one entry. The F2P subgroup-order "
                      "assertions read the deficient count. NOT resolving.",
        "rationale": "REJECT from S1, at the strictness the "
                     "scan-nonstrict-supersession rival leaves untouched: that "
                     "rival weakens the FLAGGING comparison, this one weakens "
                     "the REJECTING comparison, and the spec makes both strict. "
                     "Refuted at the equal-cell boundary approached from the "
                     "other side — one retained cell identical to the "
                     "candidate's but with a DIFFERENT numbering, so the spec "
                     "flags nothing, finds the numbering absent and appends "
                     "(two retained systems out), while the rival treats the "
                     "equal cell as dominating and returns the input unchanged. "
                     "The equal-cell input with a differing numbering is "
                     "reached by no other witness here.",
        "witness": _w("[[7]]", "[[1]]", f"[({{0}} : {_F})]",
                      "[9]", "[3]", f"({{0}} : {_F})"),
    },
    {
        "id": "append-skips-one-collection",
        "kind": "uniqueness",
        "expect": "reject",
        # The candidate is appended to two of the three collections only.
        "module": _swap(_BASE, _I_APPEND,
                        "    return (blocks', numBlocks' ++ [numBlock], "
                        "repBlocks' ++ [rep])"),
        "refinement": "the faithful real counterpart records the accepted "
                      "candidate in two of the three parallel collections and "
                      "forgets the third. From that step onward the collections "
                      "have different lengths and the k-th entry of one no longer "
                      "corresponds to the k-th of another, so every later "
                      "positional read — and the final result the F2P assertions "
                      "are computed from — is off by one for at least one "
                      "system. NOT resolving.",
        "rationale": "REJECT from S6 (the aligned append): the spec extends all "
                     "three collections together, which is what makes the "
                     "alignment guarantee hold across steps as well as within "
                     "one. Refuted at a plain append input — two retained "
                     "systems, neither comparable to the candidate's cell, so "
                     "nothing is flagged and the candidate is accepted: the spec "
                     "returns three collections of length 3, the rival one of "
                     "length 2 and two of length 3. Attacks the append rather "
                     "than the prune, so it shares no witness with any rival "
                     "above.",
        "witness": _w("[[2], [3]]", "[[5], [6]]",
                      f"[({{7}} : {_F}), ({{8}} : {_F})]",
                      "[4]", "[9]", f"({{0}} : {_F})"),
    },
    {
        "id": "scan-flags-rejecting-index",
        "kind": "uniqueness",
        "expect": "reject",
        # The index that REJECTS the candidate is itself flagged for removal.
        # Distinct from scan-no-early-exit: there the exit is dropped and LATER
        # indices are flagged; here the exit is kept and the flag lands on the
        # rejecting index itself.
        "module": _swap(_BASE, _scan_branch(4, named=False), """    if r.card > rep.card && rep ⊆ r then
      mask := mask ++ [true]
    else if r.card < rep.card && r ⊆ rep then
      minimal := false
      mask := mask ++ [true]
      break
    else
      mask := mask ++ [false]"""),
        "refinement": "the faithful real counterpart marks for removal the very "
                      "retained system whose representative cell showed the "
                      "arriving candidate to be non-coarsest. That system is a "
                      "genuine coarsest one — it is the reason the candidate is "
                      "being discarded — so the step both drops it and refuses "
                      "the candidate, losing a system and recording nothing in "
                      "its place. The retained set is then permanently short the "
                      "coarsest system at that position, so the F2P "
                      "subgroup-order assertions read the deficient count. NOT "
                      "resolving.",
        "rationale": "REJECT from S1/S2 read together: the spec leaves the "
                     "rejecting index UNFLAGGED (the scan stops there and every "
                     "remaining index, that one included, stays false), so the "
                     "retained collections come back untouched. Refuted at a "
                     "single-retained-system input whose cell is strictly "
                     "smaller than and contained in the candidate's: the spec "
                     "returns the input unchanged, the rival returns all three "
                     "collections empty. Distinct from scan-no-early-exit, which "
                     "keeps the rejecting index unflagged and instead flags the "
                     "indices AFTER it; no other witness here pins the flag "
                     "value AT the rejecting index.",
        "witness": _w("[[3]]", "[[4]]", f"[({{2}} : {_F})]",
                      "[6]", "[7]", f"({{1, 2}} : {_F})"),
    },
    {
        "id": "scan-pad-rejecting-tail-true",
        "kind": "uniqueness",
        "expect": "reject",
        # After the early exit the mask is padded out to full length with `true`
        # instead of `false`, so every index the scan never reached is removed.
        "module": _swap(
            _BASE,
            "  mask := mask ++ List.replicate (repBlocks.length - mask.length) false\n"
            + _I_PRUNE3,
            "  mask := mask ++ List.replicate (repBlocks.length - mask.length) true\n"
            + _I_PRUNE3),
        "refinement": "the faithful real counterpart pads the removal mask to "
                      "full length with the WRONG default after the comparison "
                      "loop breaks early, so every retained system the scan never "
                      "examined is discarded. Those systems were never compared "
                      "against the candidate at all — nothing has shown them "
                      "non-coarsest — so the step throws away an arbitrary tail "
                      "of the retained collection while also refusing the "
                      "candidate. The retained set collapses to the prefix the "
                      "scan happened to reach, and the F2P subgroup-order "
                      "assertions read that truncated count. NOT resolving.",
        "rationale": "REJECT from S2 (the early exit): the spec leaves every "
                     "index after the rejecting one UNFLAGGED, i.e. the tail is "
                     "padded with false. This rival pads with true and so prunes "
                     "the unexamined tail. Refuted at an input whose FIRST "
                     "retained cell rejects the candidate and which has a SECOND "
                     "retained system after it: the spec keeps both and appends "
                     "nothing, the rival keeps only the first. It attacks the "
                     "PAD DEFAULT rather than the loop body, so it is not caught "
                     "by scan-no-early-exit (which removes the break and reaches "
                     "every index in the loop itself, never exercising the pad).",
        "witness": _w("[[7], [8]]", "[[1], [2]]",
                      f"[({{0}} : {_F}), ({{0, 1, 2}} : {_F})]",
                      "[5]", "[8]", f"({{0, 1}} : {_F})"),
    },
]


# ===========================================================================
# ASSESSMENT — per-nagini-case disposition. Every case in the nagini battery is
# accounted for here. The docstring's PORT NOTE references this ledger; an
# earlier revision promised it without supplying it (an audit repair).
# ===========================================================================
ASSESSMENT = """\
  nagini case                    disposition
  -----------------------------  ---------------------------------------------
  pos-control-branch-reorder     PORTED as pos-scan-arms-reordered — the LITERAL
                                 analogue, swapping the two arms of the removal
                                 decision exactly as nagini does. This is the
                                 only positive here that is not definitionally
                                 equal to the frozen impl, so it is the only one
                                 that can detect an over-fit postcondition: the
                                 frozen `rfl` fails on it and the reification
                                 lemma's three branches are re-derived under a
                                 reversed `split_ifs` binding.
                                 An earlier revision ported this case as
                                 pos-named-scan-predicates (both decisions spelled
                                 through the named pure predicates). That case is
                                 RETAINED but reclassified: measured, its impl
                                 edit alone is closed by the FROZEN proof region
                                 unchanged, so `supersededBy`/`dominates` are
                                 definitionally their inline bodies and the case
                                 tests nothing about over-fitting. Its proof-region
                                 edit was cosmetic, not a re-proof (an audit
                                 repair).
  pos-control-local-reshape      PORTED as pos-prune-through-triple, plus
                                 pos-guard-through-local at the decision point
                                 nagini's carrier does not have. Both are
                                 DEFINITIONAL reshapes (measured: the frozen
                                 script closes each unchanged), so they are cheap
                                 regression controls rather than SPEC-TOO-STRONG
                                 probes; pos-scan-arms-reordered carries that
                                 load.
  admiss-selfcall-empty-parallel PORTED as admiss-ground-two-removals, NOT
                                 dropped. The frozen obligation here has no
                                 precondition binder, so there is no Requires to
                                 establish by a self-call; the analogue on a
                                 total carrier is the obligation being
                                 SATISFIABLE at a load-bearing input, which the
                                 case discharges BY EVALUATION at a two-removal
                                 point (the domain the reported failure occupies)
                                 as a `have`, before closing the frozen
                                 obligation verbatim. Nagini's empty-list point
                                 is deliberately NOT reused: with no precondition
                                 to establish, the degenerate input would
                                 demonstrate nothing about the domain that
                                 matters. Verified that the `have` really
                                 evaluates rather than passing vacuously — the
                                 same case with the ground claim NEGATED fails to
                                 build, so the evaluation carries information.
  frame-mutate-append-blocks     VACUOUS on this carrier, demonstrated rather
  frame-mutate-store-flag        than asserted. Both nagini cases are rejected by
                                 the PERMISSION SYSTEM: the inputs are held at
                                 `Acc(list_pred(x), 1/2)`, so writing through one
                                 is insufficient-permission regardless of the
                                 value clauses. This carrier is referentially
                                 transparent and has no fractional permissions,
                                 so "write to a read-only input" is not
                                 expressible: the nearest expressible analogues
                                 (rebinding `blocks` to a longer list, or
                                 normalising the mask with `mask.set 0 false`
                                 before the prune) are not FRAME violations at
                                 all — they are ordinary VALUE errors, already
                                 caught by S3 and indistinguishable from the
                                 prune rivals this battery carries. Nothing the
                                 permission lane detects survives the
                                 translation, so the lane has no content here
                                 rather than being skipped for difficulty.
  prepatch-desync-blocks-nums    PORTED as desync-running-index-prune (the
                                 headline rival).
  wrong-mask-nums-inverted       PORTED as wrong-mask-one-collection.
  partial-keep-all               PORTED as partial-never-prune.
  partial-drop-all               PORTED as partial-prune-everything.
  AXIOM_TESTS (empty)            G-AX's lane; empty there for the same reason it
                                 is empty here (no `opaque` callee consumed).

Added beyond the nagini battery, because this carrier COMPUTES the mask and the
viability flag that nagini receives as inputs, exposing surface nagini cannot
attack: scan-no-early-exit (S2), dedup-against-unpruned (S5),
append-ignores-viability (S4), scan-nonstrict-supersession and
scan-nonstrict-domination (S1, one per cardinality strictness),
append-skips-one-collection (S6), scan-flags-rejecting-index (the flag value AT
the rejecting index, S1/S2 together) and scan-pad-rejecting-tail-true (the
mask's PAD DEFAULT over the tail the early exit never reaches, S2).

DIVERGENCE LANE (F') — KNOWN HOLE, not a vacuous class, and measured rather than
argued. This bundle sets no `loom.semantics.termination` option at all, so the
verifier discharges no termination obligation for the modeled routine and the
`partial` keyword is available. A rival whose body is
`partial def spinPrune ... := spinPrune ...`, with
`implementation_pruneSystems` delegating to it, passes variant_scope cleanly
(same_spec holds, no banned assumption token — `partial` is not in
`_ASSUMPTION_TOKENS`) and is REJECTED by the verifier: the frozen `rfl` fails
against the opaque `spinPrune`. But it cannot be SHIPPED, because no witness
discriminates it. `partial def` compiles to an opaque constant with no reduction
behavior, so a `decide` witness against it does not evaluate
(`Tactic \\`decide\\` failed for proposition`, exit 1) and a
`simp [implementation_pruneSystems, spinPrune]` witness leaves unsolved goals
(exit 1) — both measured. The rival's rejection is therefore attributable to the
opacity of `spinPrune` rather than to the postcondition, which is precisely the
tactic-mismatch failure the witness requirement exists to exclude. So the class
is recorded as a HOLE in what this battery can attest, not as vacuous: a
diverging impl of this routine exists and this spec does not demonstrably
exclude it. Nagini carries no diverge case either, so nothing is dropped in the
port.
"""

# ===========================================================================
# AXIOM LANE — NONE. The `axioms` region declares no `opaque` callee and the
# bundle consumes no `axiom`: the changed behavior is modeled deeply over lists
# and finite sets, so there is no external callee to run against a contract.
# The nagini sibling's AXIOM_TESTS is empty for the same reason, and that lane
# belongs to G-AX regardless.
# ===========================================================================
AXIOM_TESTS = []

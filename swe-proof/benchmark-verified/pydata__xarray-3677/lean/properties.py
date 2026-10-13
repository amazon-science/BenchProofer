# properties.py — G-PBT falsification battery for pydata__xarray-3677 (lean).
#
# PORT of the nagini sibling's battery to this bundle's carrier. Each SPEC_TESTS
# case is a full Solution.lean variant that shares the FROZEN spec exactly
# (markers.same_spec) and edits ONLY the `-- impl-start`/`-- impl-end` region
# and, where a reshaped impl needs reproving, the `-- proof-start`/`-- proof-end`
# body. The `theorem correct_merge` STATEMENT is byte-identical in every case,
# and no case introduces an axiom, a helper lemma, `sorry`, `admit`, or
# `native_decide` — so a rejection is attributable to the postcondition and a
# verification to a real discharge of the real obligation.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE of this bundle (read Solution.lean + mapping.md + refinement.md)
# ---------------------------------------------------------------------------
#   ONE obligation:
#     theorem correct_merge :
#       ∀ (self : Dataset) (other : MergeOther),
#         problem_spec_merge self other (implementation_merge self other)
#
#   problem_spec_merge (self : Dataset) (other : MergeOther)
#                      (result : Except OpErr Dataset) : Prop :=
#     result = (asDataset other).bind (mergeDatasets self)
#
#   ONE top-level clause, no conjunction and no implication arm — a single
#   equation pinning the whole outcome. There is no precondition: the obligation
#   quantifies over every `self` and every `other` unconditionally, so the
#   nagini sibling's read-permission and distinct-object hypotheses have no
#   counterpart to admit or to over-restrict here.
#
#   The equation is a COMPOSITION OF TWO STAGES, and that is what makes the
#   clause load-bearing in six independent ways rather than four. `asDataset` is
#   itself `Except OpErr Dataset`-valued — reading the second operand as a
#   dataset can RAISE — and `bind` short-circuits on that raise, so the modeled
#   outcome has three regions, not two: the reading raises (no merge happens and
#   the reading's own error is the whole answer), the reading succeeds and the
#   merge raises, the reading succeeds and the merge succeeds.
#
#   INPUT BINDERS the reject witnesses must vary:
#     * self  : Dataset       — the receiving dataset value
#     * other : MergeOther    — the second operand, `.ds d` (already a dataset)
#                               or `.da a` (a single named array)
#   `result` is not an input: it is what a rival produces.
#
#   Both binders are attacked, and each is attacked at BOTH levels the carrier
#   gives it. `other` is varied by SHAPE across the rivals below (`.ds` and `.da`
#   both carry witnesses). `self` is UNIVERSALLY quantified, and a third audit
#   measured that the nine clause-level witnesses all probe it at one pinned point
#   — so it carries its own rival, uniq-receiver-special-case (C7), whose witness
#   binds `self` instead of pinning it. A FOURTH audit then measured that the same
#   hole remained one binder over: `other`'s two CONSTRUCTORS vary, but the ARRAY
#   the `.da` constructor carries is the single term `Classical.arbitrary DataArray`
#   in all six `.da` witnesses, which the coverage reporter reads as "varies". So
#   the array PAYLOAD carries its own rival too, uniq-operand-special-case (C8),
#   whose witness binds `a`. A FIFTH audit measured that the hole then remained on
#   the OTHER constructor's payload — the DATASET the `.ds` shape carries is pinned
#   in every witness the battery had — so that payload carries its own rival as
#   well, uniq-dataset-operand-special-case (C9), whose witness binds `d`. All
#   three dependences were measured with real builds, not argued: the ten witnesses
#   shipped before C8 all fail to refute the C8 rival, and the eleven shipped
#   before C9 all fail to refute the C9 rival (11/11 exit 1).
#
#   The clause is load-bearing in SIX independent ways, and each gets its own
#   rival below (plus C7 on the receiver binder and C8/C9 on the two constructors'
#   payloads):
#     (C1) the second operand is READ AS A DATASET before the merge —
#          `asDataset (.da a) = datasetOfArray a`, so the single-named-array
#          shape is absorbed as its equivalent one-variable dataset rather than
#          handed to the merge unread;                    -> uniq-drop-reading
#     (C2) the already-dataset shape is read AS ITSELF — `asDataset (.ds d)` is
#          `Except.ok d`, so no substitute dataset may stand in for it;
#                                                 -> uniq-substitute-noop-operand
#     (C3) the two merge operands appear in THAT ORDER (`self` first, the read
#          operand second), which is what fixes merge precedence;
#                                                  -> uniq-reverse-operand-order
#     (C4) the outcome is the underlying merge's outcome VERBATIM — the equation
#          is over `Except OpErr Dataset`, so both channels are pinned down to
#          their payloads. Four independent halves, one rival each:
#            * the merge may not be skipped altogether  -> uniq-unmerged-operand
#            * a raised failure may not be swallowed    -> uniq-swallow-failure
#            * a raised failure's own payload is pinned -> uniq-relabel-failure
#            * a merged dataset's value is pinned too   -> uniq-substitute-
#              success-payload (the narrowest near-miss on the merge stage: it
#              runs the merge, branches on its outcome, and propagates the error
#              arm verbatim WITH its payload, replacing only the merged value)
#     (C5) a READING failure short-circuits: where reading the second operand as
#          a dataset raises, that error is the WHOLE outcome and the merge does
#          not run, so the failure may not be converted into any answer the merge
#          would have produced;             -> uniq-swallow-reading-failure
#     (C6) a reading failure's own payload is pinned too, exactly as the merge
#          stage's is: `bind` propagates the reading's error verbatim, so a rival
#          that raises a constant in its place violates the equation.
#                                           -> uniq-relabel-reading-failure
#     (C7) the equation holds at EVERY receiver, not merely at the one point the
#          clause-level witnesses probe — the obligation quantifies over `self`
#          universally.                     -> uniq-receiver-special-case
#     (C8) and it holds at EVERY ARRAY the `.da` shape can carry, not merely at
#          the one array every `.da` witness probes — the quantification over
#          `other` reaches the constructor's PAYLOAD, not just its tag.
#                                           -> uniq-operand-special-case
#     (C9) and the same for the OTHER constructor: it holds at EVERY DATASET the
#          `.ds` shape can carry, not merely at the one dataset the `.ds`
#          witnesses probe.            -> uniq-dataset-operand-special-case
#
#   C5 and C6 are the two clauses the SHORT-CIRCUIT introduces, and they are
#   attackable independently of C1: a rival can read the operand through the very
#   same partial reading the spec names (so C1 is satisfied on every input where
#   the reading succeeds) and still be wrong on the region where it raises. They
#   are also the two halves that distinguish this postcondition from one asserting
#   a total reading: under a total reading there is no error region for the first
#   stage at all, so no rival could be built for either, and the two rivals below
#   are the machine-checked evidence that the region is real and pinned.
#
# ---------------------------------------------------------------------------
# CARRIER NARROWING vs the nagini sibling (read `assessment` for the full map)
# ---------------------------------------------------------------------------
# The nagini sibling contracts a function whose carrier is the OPERAND LIST the
# receiving object hands onward: its postcondition pins that list's length, the
# object identity of each element, a mapping-shaped flag on each, and field
# equality against the second operand's own fields. This bundle models the
# OUTCOME instead — `Except OpErr Dataset`, the merged value or the failure —
# so every nagini clause about the operand LIST (length, positional identity,
# per-element flags) has no counterpart to attack, while both stages' failure
# channels and the merge invocation itself are newly attackable. The cases below
# therefore do not line up one-for-one with nagini's, and case-count parity is
# not the target.
#
# CONDITIONING ON THE CARRIER. `Dataset`, `DataArray`, `datasetOfArray` and
# `mergeDatasets` are all `opaque`, so no literal input decides anything and
# `decide` gets stuck on the opaque term. Every reject witness therefore states
# its refutation at a point described by HYPOTHESIS: it assumes only what it
# needs about the opaque outcomes at that point, and derives that the rival
# contradicts the spec there.
#
# Because the modeled reading is PARTIAL, a witness that wants to reach the merge
# stage at all must say so: `(datasetOfArray a).bind (mergeDatasets self)` sits
# in the reading's error region unless the reading is assumed to succeed. So the
# merge-stage witnesses (uniq-swallow-failure, uniq-relabel-failure,
# uniq-substitute-success-payload, and the two operand-handling witnesses) carry a
# `hread : datasetOfArray … = Except.ok dRead` hypothesis that NAMES the dataset
# the reading yields. That is a binder plus one assumption about one opaque term,
# and it is what puts the witness in a region the modeled behavior actually has
# rather than in a formally-consistent but empty one — the same discipline the
# degenerate-point note below describes, applied to the new first stage.
#
# DEGENERATE-POINT DISCIPLINE (an independent audit of this battery corrected one
# case for this and it is the trap to watch on this carrier). A witness that
# conditions on an opaque term is only as good as the sub-domain its hypothesis
# describes. Because no tactic can derive `False` from a statement about an opaque
# term, the gate's consistency probe passes ANY such hypothesis — including one
# describing a sub-domain the referent does not have. Concretely: assuming
# `mergeDatasets X X = Except.error e` is formally consistent here, but a merge of
# a dataset with ITSELF has nothing to disagree about and does not raise, so a
# rejection conditioned on it attaches to an empty sub-domain. Every hypothesis
# below that assumes a RAISE therefore places it on two DISTINCT operand terms.
# The same care is why uniq-substitute-noop-operand's hypothesis is an
# INEQUALITY between a self-merge and a genuine two-operand merge (which is what
# the rival's own wrongness is) rather than an assumption that the self-merge
# raises.
#
# `Classical.arbitrary` supplies the input points: the carriers are `opaque` and
# only `Nonempty`, so there is no literal to write, and it is already in the
# frozen file's dependency closure (G-VERIFY records `Classical.choice` for
# `correct_merge`). Two DISTINCT dataset points are used — an arbitrary dataset,
# and the dataset a successful reading of an arbitrary single named array yields
# (`dRead`, a binder rather than a term, since the reading is partial) — so the
# `self` and operand binders are genuinely varied across the rivals rather than
# held fixed.
#
# `Except.bind` is named in the witnesses' `simp` sets. The spec's `bind` is
# `Except.bind`, which reduces by `rfl` but is not a `simp` lemma, so `simp [h]`
# alone leaves the goal untouched (`simp made no progress`) and the witness would
# fail against the RIVAL — recorded as `witness-unproven`, an inconclusive
# outcome, rather than as the refutation it is. Measured with real builds on both
# sides before it was added.
from pathlib import Path

INSTANCE = "pydata__xarray-3677"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact frozen impl and proof bodies. Every variant is produced by swapping
# one or both of these, so the spec view — and the `theorem correct_merge`
# statement — is untouched by construction.
# ---------------------------------------------------------------------------
_IMPL_OLD = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  -- Read the second operand as a dataset: a single named array is read as its
  -- equivalent one-variable dataset (a reading that may raise); a dataset is
  -- used unchanged.
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  -- Delegate to the underlying dataset-to-dataset merge only where the reading
  -- succeeded; a reading error is the whole outcome.
  return read.bind (mergeDatasets self)"""

_PROOF_OLD = """  intro self other
  unfold problem_spec_merge implementation_merge asDataset
  cases other <;> rfl"""

assert _BASE.count(_IMPL_OLD) == 1
assert _BASE.count(_PROOF_OLD) == 1

# The input points the witnesses probe, and the operand shapes over them.
_S0 = "(Classical.arbitrary Dataset)"
_A0 = "(Classical.arbitrary DataArray)"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each reads the second operand exactly as the
# spec's own reading does, short-circuits on a reading failure exactly as `bind`
# does, and hands the underlying merge the same two operands in the same order;
# only the control flow / data flow around that changes.
# ===========================================================================

# pos-branch-outward: lift the case analysis OUT of the local binding — instead
# of selecting the read operand into a `let` and then binding once, each branch
# performs its own reading and merge and returns directly, with the reading's
# error region spelled out as an explicit match instead of left to `bind`. Two
# exit points where the frozen shape has one; the same two operands in the same
# order on each path, and the same short-circuit.
_POS_BRANCH_OUTWARD = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  -- Each operand shape takes its own path: a single named array is first read as
  -- its equivalent one-variable dataset, and a failed reading is returned as-is;
  -- a dataset is used unchanged.
  match other with
  | .ds d => return mergeDatasets self d
  | .da a =>
      match datasetOfArray a with
      | .error e => return Except.error e
      | .ok d => return mergeDatasets self d"""

_PROOF_BRANCH_OUTWARD = """  intro self other
  unfold problem_spec_merge implementation_merge asDataset
  cases other with
  | ds d => rfl
  | da a =>
      simp only [Id.run]
      cases datasetOfArray a <;> rfl"""

# pos-accumulator: a mutable local, seeded and then overwritten per branch,
# instead of a single-assignment `let`. A different local/data shape (the
# imperative accumulator idiom) reaching the same reading of the operand.
_POS_ACCUMULATOR = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  -- Read the second operand into a mutable local: a single named array becomes
  -- its equivalent one-variable dataset (or the reading's error); a dataset is
  -- used unchanged.
  let mut read : Except OpErr Dataset := Except.ok self
  match other with
  | .ds d => read := Except.ok d
  | .da a => read := datasetOfArray a
  return read.bind (mergeDatasets self)"""

# pos-outcome-rebound: reshape the OUTCOME path rather than the operand path —
# take the composed answer apart and put it back together channel by channel (a
# failure from EITHER stage is re-raised as itself, a merged dataset is returned
# as itself). Observationally the identity on `Except OpErr Dataset`, so the
# postcondition still holds, but the frozen tactic body no longer closes it: this
# positive needs a genuine reprove (a case split on the reading AND on the merge's
# outcome), which is what makes it a real defence of the obligation rather than a
# reshape the frozen script happens to survive.
_POS_OUTCOME_REBOUND = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  -- Read the second operand as a dataset, exactly as above.
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  -- Delegate, then rebind the outcome channel by channel.
  return (read.bind (mergeDatasets self)).bind (fun merged => Except.ok merged)"""

_PROOF_OUTCOME_REBOUND = """  intro self other
  unfold problem_spec_merge implementation_merge asDataset
  cases other with
  | ds d =>
      simp only [Id.run, Except.bind]
      cases mergeDatasets self d <;> rfl
  | da a =>
      simp only [Id.run, Except.bind]
      cases datasetOfArray a with
      | error e => rfl
      | ok d =>
          simp only [Except.bind]
          cases mergeDatasets self d <;> rfl"""


# ===========================================================================
# ADMISSIBILITY (verify) — the obligation is not merely closable in the abstract;
# it is SATISFIABLE at each concrete operand shape the modeled behavior must
# handle. The frozen impl is kept verbatim and two GROUND instances of the
# postcondition are established inside the tactic body (one per operand shape,
# including the shape the F2P scenario exercises) before the frozen obligation is
# closed verbatim. Nothing is assumed: no new declaration, the theorem statement
# is byte-identical, and the ground instances are `have`s in the existing body.
# If either could not be established, the modeled behavior would be
# unsatisfiable at exactly an input the tests exercise — the analogue of
# PRECOND-TOO-STRONG on a carrier that states no precondition at all.
# ===========================================================================
_PROOF_ADMISS = """  -- Ground the postcondition at each operand shape the behavior must handle:
  -- a second operand that is a single named array (the scenario the added
  -- coverage exercises), and one that is already a dataset.
  have _ground_named_array :
      problem_spec_merge (Classical.arbitrary Dataset)
        (MergeOther.da (Classical.arbitrary DataArray))
        (implementation_merge (Classical.arbitrary Dataset)
          (MergeOther.da (Classical.arbitrary DataArray))) := by
    unfold problem_spec_merge implementation_merge asDataset
    rfl
  have _ground_dataset :
      problem_spec_merge (Classical.arbitrary Dataset)
        (MergeOther.ds (Classical.arbitrary Dataset))
        (implementation_merge (Classical.arbitrary Dataset)
          (MergeOther.ds (Classical.arbitrary Dataset))) := by
    unfold problem_spec_merge implementation_merge asDataset
    rfl
  intro self other
  unfold problem_spec_merge implementation_merge asDataset
  cases other <;> rfl"""


# ===========================================================================
# UNIQUENESS (reject) — rivals sharing the spec exactly, each attacking one of
# the six independent ways the single postcondition clause is load-bearing. A
# rival that VERIFIED would be a true verify-does-not-imply-resolve break, so
# each carries the argument that its faithful real patch does NOT resolve.
#
# Every rival also carries a `witness` that has been SEEN to discriminate: it
# elaborates against the rival and fails against the frozen solution.
# ===========================================================================

# uniq-drop-reading (C1) — the central rival: the behavior
# Solution_prepatch.lean reproduces. The already-dataset shape merges normally,
# but the single-named-array shape is never read as its equivalent one-variable
# dataset. It is treated as an operand the underlying merge cannot consume, so
# the branch yields a failure instead of the composed outcome.
_UNIQ_DROP_READING = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  match other with
  | .ds d => return mergeDatasets self d
  | .da _ => return Except.error { reason := "operand has no items" }"""

_W_DROP_READING = f"""-- Wherever reading the array as a dataset and merging that into `self` is not
-- that very failure, the rival's answer differs from the spec's. Stated over the
-- whole composition, so it needs no assumption about whether the reading
-- succeeds: the rival is wrong on BOTH regions of the reading.
example (h : (datasetOfArray {_A0}).bind (mergeDatasets {_S0})
      ≠ Except.error {{ reason := "operand has no items" }}) :
    ¬ problem_spec_merge {_S0} (MergeOther.da {_A0})
        (implementation_merge {_S0} (MergeOther.da {_A0})) := by
  unfold problem_spec_merge implementation_merge asDataset
  intro hc
  exact h hc.symm"""

# uniq-substitute-noop-operand (C2): the single-named-array shape is read
# correctly, but on the already-dataset shape the operand is DISCARDED and the
# receiver is merged with itself instead. The near-miss that keeps the whole
# reading of the array shape and abuses only the pass-through shape.
_UNIQ_SUBSTITUTE_NOOP = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  match other with
  | .ds _ => return mergeDatasets self self
  | .da a => return (datasetOfArray a).bind (mergeDatasets self)"""

_W_SUBSTITUTE_NOOP = f"""-- Wherever merging the receiver with itself differs from merging it with the
-- operand it was actually given, the rival's answer differs from the spec's. The
-- probed operand is the dataset a SUCCESSFUL reading of an arbitrary named array
-- yields (`dRead`, named by `hread`), which is a dataset the modeled behavior
-- genuinely produces — the reading is partial, so it must be assumed to succeed
-- to name its result at all.
example (dRead : Dataset) (hread : datasetOfArray {_A0} = Except.ok dRead)
    (h : mergeDatasets {_S0} {_S0} ≠ mergeDatasets {_S0} dRead) :
    ¬ problem_spec_merge {_S0} (MergeOther.ds dRead)
        (implementation_merge {_S0} (MergeOther.ds dRead)) := by
  unfold problem_spec_merge implementation_merge asDataset
  simpa [Except.bind] using h"""

# uniq-reverse-operand-order (C3): the operand is read exactly as the spec reads
# it, the short-circuit is preserved, and both operands reach the underlying
# merge — but in the opposite order, so the receiver is the one absorbed rather
# than the one absorbing.
_UNIQ_REVERSE_ORDER = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  return read.bind (fun other' => mergeDatasets other' self)"""

_W_REVERSE_ORDER = f"""-- Wherever the underlying merge is not symmetric in its two operands, the
-- rival's answer differs from the spec's. Probed at the mirror image of the
-- substitute-noop point.
example (dRead : Dataset) (hread : datasetOfArray {_A0} = Except.ok dRead)
    (h : mergeDatasets dRead {_S0} ≠ mergeDatasets {_S0} dRead) :
    ¬ problem_spec_merge {_S0} (MergeOther.ds dRead)
        (implementation_merge {_S0} (MergeOther.ds dRead)) := by
  unfold problem_spec_merge implementation_merge asDataset
  simpa [Except.bind] using h"""

# uniq-swallow-failure (C4, merge failure channel): the operand is read
# correctly, a reading failure short-circuits correctly, the merge runs on the
# right two operands in the right order, and a successful outcome is propagated
# verbatim — but the FAILURE the MERGE raises is swallowed and the receiver is
# handed back as a success instead. Attacks only the merge stage's error arm; a
# rival that agreed with the spec everywhere the merge succeeds.
_UNIQ_SWALLOW_FAILURE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  match read with
  | .error e => return Except.error e
  | .ok other' =>
      match mergeDatasets self other' with
      | .ok merged => return Except.ok merged
      | .error _ => return Except.ok self"""

_W_SWALLOW_FAILURE = f"""-- At a point where the MERGE does raise, the rival reports success and so
-- differs from the spec. `e` is the raised failure, a binder rather than a second
-- assumption about the same term.
--
-- The two merge operands here are DISTINCT terms (an arbitrary receiver, against
-- the dataset a successful reading of a named array yields). That matters: a
-- hypothesis placed on `mergeDatasets X X` — a merge of a dataset with ITSELF —
-- would be consistent on this opaque carrier yet describe a sub-domain the
-- modeled behavior does not have, since merging a dataset with itself has
-- nothing to disagree about and does not raise. `hread` plays the same role for
-- the first stage: without it the probed point sits in the reading's error
-- region, where this rival is CORRECT, and the witness would say nothing.
example (dRead : Dataset) (hread : datasetOfArray {_A0} = Except.ok dRead)
    (e : OpErr) (h : mergeDatasets {_S0} dRead = Except.error e) :
    ¬ problem_spec_merge {_S0} (MergeOther.ds dRead)
        (implementation_merge {_S0} (MergeOther.ds dRead)) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, h]"""

# uniq-unmerged-operand (C4, merge skipped): the reading of the second operand is
# entirely CORRECT, short-circuit included — and the read operand is then
# returned as the outcome without the underlying merge ever running. The
# receiver's own content never reaches the answer.
_UNIQ_UNMERGED_OPERAND = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  return read"""

_W_UNMERGED_OPERAND = f"""-- Wherever reading the array as a dataset and merging that into `self` is not
-- just the reading handed back, the rival's answer differs from the spec's.
-- Stated over the whole composition, so no assumption about the reading is
-- needed: on the reading's error region the two agree, and this says they differ
-- somewhere, which is all the refutation needs.
example (h : (datasetOfArray {_A0}).bind (mergeDatasets {_S0})
      ≠ datasetOfArray {_A0}) :
    ¬ problem_spec_merge {_S0} (MergeOther.da {_A0})
        (implementation_merge {_S0} (MergeOther.da {_A0})) := by
  unfold problem_spec_merge implementation_merge asDataset
  intro hc
  exact h hc.symm"""

# uniq-relabel-failure (C4, merge failure PAYLOAD): the operand is read
# correctly, the short-circuit is preserved, the merge runs on the right two
# operands in the right order, the success channel is propagated verbatim, AND
# the merge's failure CHANNEL is preserved as a failure — only the raised
# failure's own content is replaced by a constant. uniq-swallow-failure attacks
# whether a raise survives at all; nothing else establishes that the raise's
# PAYLOAD is pinned too.
_UNIQ_RELABEL_FAILURE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  match read with
  | .error e => return Except.error e
  | .ok other' =>
      match mergeDatasets self other' with
      | .ok merged => return Except.ok merged
      | .error _ => return Except.error { reason := "merge conflict" }"""

_W_RELABEL_FAILURE = f"""-- At a point where the MERGE raises a failure carrying its OWN reason, the rival
-- raises one carrying a constant reason instead, so its answer differs from the
-- spec's. `hread` puts the point in the region where the merge runs at all; the
-- two merge operands there are distinct.
example (dRead : Dataset) (hread : datasetOfArray {_A0} = Except.ok dRead)
    (h : mergeDatasets {_S0} dRead
      = Except.error {{ reason := "conflicting values for variable" }}) :
    ¬ problem_spec_merge {_S0} (MergeOther.da {_A0})
        (implementation_merge {_S0} (MergeOther.da {_A0})) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, hread, h]"""

# uniq-substitute-success-payload (C4, success PAYLOAD): the mirror of
# uniq-relabel-failure on the OTHER channel of the merge stage. The operand is
# read correctly, the short-circuit is preserved, the merge runs on the right two
# operands in the right order, its outcome is CONSULTED, and a raised failure is
# re-raised with its own payload intact — only the SUCCESS payload is replaced,
# by the receiver.
_UNIQ_SUBSTITUTE_SUCCESS = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  match read with
  | .error e => return Except.error e
  | .ok other' =>
      match mergeDatasets self other' with
      | .ok _ => return Except.ok self
      | .error e => return Except.error e"""

_W_SUBSTITUTE_SUCCESS = f"""-- At a point where the MERGE succeeds with a merged dataset that is not the
-- receiver itself, the rival hands back the receiver and so differs from the
-- spec. `merged` is the merge's own answer, a binder rather than an extra
-- assumption about the same term.
--
-- `hm` is what keeps the assumed sub-domain a REAL one rather than merely a
-- consistent one. Assuming only that the merge succeeds would describe a
-- sub-domain on which the rival is not necessarily wrong — where the merged
-- answer happens to BE the receiver (merging in nothing new), the rival agrees
-- with the spec. `hread` plays the analogous role for the reading stage.
example (dRead merged : Dataset)
    (hread : datasetOfArray {_A0} = Except.ok dRead)
    (h : mergeDatasets {_S0} dRead = Except.ok merged) (hm : merged ≠ {_S0}) :
    ¬ problem_spec_merge {_S0} (MergeOther.da {_A0})
        (implementation_merge {_S0} (MergeOther.da {_A0})) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, hread, h, Ne.symm hm]"""

# uniq-swallow-reading-failure (C5): the READING is the very one the spec names —
# on every input where reading the array as a dataset succeeds this rival is
# byte-for-byte the frozen behavior, so C1 does not touch it — but where the
# reading RAISES, the rival swallows that failure and hands the receiver back as
# a success instead of short-circuiting. Attacks the region the composition
# introduces, and it is the region the modeled behavior would not have at all
# under a total reading.
_UNIQ_SWALLOW_READING_FAILURE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  match other with
  | .ds d => return mergeDatasets self d
  | .da a =>
      match datasetOfArray a with
      | .ok d => return mergeDatasets self d
      | .error _ => return Except.ok self"""

_W_SWALLOW_READING_FAILURE = f"""-- At a point where READING the array as a dataset raises, the spec's answer is
-- that raised failure (the merge does not run), and the rival reports success —
-- so the two differ. `e` is the raised failure, a binder; the single hypothesis
-- names the reading's outcome once. This is the only region where this rival is
-- wrong, so no witness at a succeeding reading could discriminate it.
example (e : OpErr) (h : datasetOfArray {_A0} = Except.error e) :
    ¬ problem_spec_merge {_S0} (MergeOther.da {_A0})
        (implementation_merge {_S0} (MergeOther.da {_A0})) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, h]"""

# uniq-relabel-reading-failure (C6): the narrowest near-miss in the battery. The
# reading is the spec's own, the merge stage is untouched, a reading failure DOES
# short-circuit and IS still a failure — only the reading failure's own content is
# replaced by a constant. It agrees with the spec on every input where the reading
# succeeds, and on the failing region it agrees about the channel; it differs only
# in what that failure carries. The mirror of uniq-relabel-failure, one stage
# earlier.
_UNIQ_RELABEL_READING_FAILURE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  match other with
  | .ds d => return mergeDatasets self d
  | .da a =>
      match datasetOfArray a with
      | .ok d => return mergeDatasets self d
      | .error _ => return Except.error { reason := "operand cannot be read" }"""

_W_RELABEL_READING_FAILURE = f"""-- At a point where READING the array as a dataset raises a failure carrying its
-- OWN reason, the rival raises one carrying a constant reason instead, so its
-- answer differs from the spec's. The equation is over `Except OpErr Dataset` and
-- `OpErr` carries a reason, so `bind`'s verbatim propagation of the reading's
-- error pins that reason.
example (h : datasetOfArray {_A0}
      = Except.error {{ reason := "operand cannot be read as a dataset" }}) :
    ¬ problem_spec_merge {_S0} (MergeOther.da {_A0})
        (implementation_merge {_S0} (MergeOther.da {_A0})) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, h]"""

# uniq-receiver-special-case (the `self` BINDER) — ADDED BY A THIRD AUDIT, which
# measured that every rival above is witnessed at a receiver PINNED to
# `Classical.arbitrary Dataset`, and that the pin is load-bearing rather than
# cosmetic. This rival is the frozen behavior EXACTLY at that one receiver and a
# constant failure at every other, so it agrees with all nine witnesses above at
# the only point they look. Measured, with real builds: a witness in the shipped
# style (receiver pinned, the operand hypothesized) does NOT refute it (exit 1,
# `unsolved goals … ⊢ False`), while the witness below — which binds `self` and
# hypothesizes only that it is a DIFFERENT receiver — does (exit 0 on the rival,
# exit 1 on the frozen solution). So the `self` binder needed its own rival: the
# obligation quantifies over EVERY receiver, and nothing else here tests that.
_UNIQ_RECEIVER_SPECIAL_CASE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset :=
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  @ite _ (self = Classical.arbitrary Dataset) (Classical.propDecidable _)
    (read.bind (mergeDatasets self))
    (Except.error { reason := "unsupported receiver" })"""

_W_RECEIVER_SPECIAL_CASE = f"""-- At a receiver OTHER than the one every other witness here probes, the rival
-- yields a constant failure while the spec demands the composition — so wherever
-- that composition is not that very failure, the two differ. `self` is a BINDER,
-- not the pinned point, and `hself` places it off that point; this is the only
-- witness in the battery whose refutation would break if the receiver were held
-- fixed, which is exactly the reach this case exists to add.
example (self : Dataset) (hself : self ≠ {_S0}) (d : Dataset)
    (h : mergeDatasets self d ≠ Except.error {{ reason := "unsupported receiver" }}) :
    ¬ problem_spec_merge self (MergeOther.ds d)
        (implementation_merge self (MergeOther.ds d)) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, hself]
  exact fun hc => h hc.symm"""


# uniq-operand-special-case (the `other` PAYLOAD binder) — ADDED BY A FOURTH
# AUDIT, which measured that uniq-receiver-special-case closed the receiver
# binder and left the SAME hole one binder over. Every `.da` witness in the
# battery states its refutation at the single array term `Classical.arbitrary
# DataArray`; the coverage reporter cannot see that pin, because it reads `other`
# as varying (the two CONSTRUCTORS `.ds`/`.da` do vary) while the array the `.da`
# constructor carries is the same term in all six. So this rival is the frozen
# behavior EXACTLY at that one array — the reading, the short-circuit, the merge,
# both payloads, verbatim — and a constant failure at every other array. Measured,
# with real builds: ALL TEN shipped witnesses fail to refute it (10/10 exit 1,
# with the reading-region witnesses landing on `unsolved goals … ⊢ False`),
# because each looks only at the point where the rival IS gold; the witness below,
# which binds `a` and hypothesizes only that it is a DIFFERENT array, refutes it
# (exit 0 on the rival, exit 1 on the frozen solution, probe exit 1).
_UNIQ_OPERAND_SPECIAL_CASE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset :=
  match other with
  | .ds d => (Except.ok d).bind (mergeDatasets self)
  | .da a =>
      @ite _ (a = Classical.arbitrary DataArray) (Classical.propDecidable _)
        ((datasetOfArray a).bind (mergeDatasets self))
        (Except.error { reason := "unsupported operand" })"""

_W_OPERAND_SPECIAL_CASE = f"""-- At an ARRAY other than the one every `.da` witness in this battery probes, the
-- rival yields a constant failure while the spec demands the composition — so
-- wherever that composition is not that very failure, the two differ. `a` is a
-- BINDER, not the pinned point, and `ha` places it off that point; `self` is
-- bound too. This is the only witness here whose refutation would break if the
-- ARRAY operand were held fixed, which is exactly the reach this case adds:
-- uniq-receiver-special-case did this for the receiver and left the array pinned.
example (self : Dataset) (a : DataArray) (ha : a ≠ {_A0})
    (h : (datasetOfArray a).bind (mergeDatasets self)
      ≠ Except.error {{ reason := "unsupported operand" }}) :
    ¬ problem_spec_merge self (MergeOther.da a)
        (implementation_merge self (MergeOther.da a)) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, ha]
  exact fun hc => h hc.symm"""


# uniq-dataset-operand-special-case (the OTHER constructor's PAYLOAD binder) —
# ADDED BY A FIFTH AUDIT, which measured that uniq-operand-special-case closed
# the `.da` constructor's payload and left the IDENTICAL hole on the `.ds`
# constructor's payload. The dataset the `.ds` shape carries is a pinned term in
# every clause-level witness: five of them probe `MergeOther.ds dRead`, where
# `dRead` is bound but constrained by `hread` to be the reading of the single
# pinned array, and the rest probe the `.da` shape. So this rival is the frozen
# behavior EXACTLY at the one dataset operand term `Classical.arbitrary Dataset`
# — the pass-through reading, the merge, both payloads, verbatim — and a constant
# failure at every other dataset operand. Measured, with real builds: ALL ELEVEN
# previously shipped witnesses fail to refute it (11/11 exit 1), because each
# looks only where the rival IS gold; the witness below, which binds `d` and
# hypothesizes only that it is a DIFFERENT dataset, refutes it (exit 0 on the
# rival, exit 1 on the frozen solution, probe exit 1). This is the `.ds` mirror
# of uniq-operand-special-case, and like it the coverage reporter cannot see the
# gap: it reads `other` as varying because the two CONSTRUCTORS vary, while the
# payload each constructor carries is pinned.
_UNIQ_DS_OPERAND_SPECIAL_CASE = """noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset :=
  match other with
  | .ds d =>
      @ite _ (d = Classical.arbitrary Dataset) (Classical.propDecidable _)
        ((Except.ok d).bind (mergeDatasets self))
        (Except.error { reason := "unsupported dataset operand" })
  | .da a => (datasetOfArray a).bind (mergeDatasets self)"""

_W_DS_OPERAND_SPECIAL_CASE = f"""-- At a DATASET OPERAND other than the one the `.ds` witnesses in this battery
-- probe, the rival yields a constant failure while the spec demands the merge —
-- so wherever that merge is not that very failure, the two differ. `d` is a
-- BINDER, not the pinned point, and `hd` places it off that point; `self` is
-- bound too. The `.ds` mirror of uniq-operand-special-case: that case freed the
-- ARRAY the `.da` constructor carries, this one frees the DATASET the `.ds`
-- constructor carries, which every other witness here pins.
example (self : Dataset) (d : Dataset) (hd : d ≠ {_S0})
    (h : mergeDatasets self d
      ≠ Except.error {{ reason := "unsupported dataset operand" }}) :
    ¬ problem_spec_merge self (MergeOther.ds d)
        (implementation_merge self (MergeOther.ds d)) := by
  unfold problem_spec_merge implementation_merge asDataset
  simp [Except.bind, hd]
  exact fun hc => h hc.symm"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-branch-outward",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_OLD, _POS_BRANCH_OUTWARD),
            _PROOF_OLD, _PROOF_BRANCH_OUTWARD),
        "rationale": "structurally-different CORRECT impl: the case analysis on "
                     "the second operand's shape is lifted out of the local "
                     "binding, so each shape takes its own path and returns "
                     "directly (two exit points where the frozen shape has one), "
                     "and the reading's error region is spelled out as an explicit "
                     "match instead of being left to `bind`. Both paths hand the "
                     "underlying merge the same two operands in the same order as "
                     "the spec's reading — the array shape read as its equivalent "
                     "one-variable dataset, the dataset shape unchanged — and "
                     "short-circuit on a failed reading exactly as `bind` does, so "
                     "`result = (asDataset other).bind (mergeDatasets self)` still "
                     "holds pointwise. Reproved with a case split on the reading, "
                     "since the frozen `cases other <;> rfl` no longer sees a "
                     "single `bind` to reduce; the theorem statement is "
                     "byte-identical and nothing is assumed. Ports nagini's "
                     "single-if/else positive control. If a faithful correct impl "
                     "cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_ACCUMULATOR),
        "rationale": "local/data-shape reshape: the read operand is seeded into a "
                     "MUTABLE local and then overwritten per operand shape, "
                     "instead of being bound once by a single-assignment `let`. "
                     "The imperative-accumulator idiom reaching the same reading, "
                     "so the single postcondition clause holds unchanged. Ports "
                     "nagini's build-then-assign positive control (its list "
                     "append has no counterpart on this carrier, which returns "
                     "the merge OUTCOME rather than an operand list). If it "
                     "cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-outcome-rebound",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_OLD, _POS_OUTCOME_REBOUND),
            _PROOF_OLD, _PROOF_OUTCOME_REBOUND),
        "rationale": "the strongest positive here, because it reshapes the OUTCOME "
                     "path rather than the operand path: the composed answer is "
                     "taken apart and reassembled channel by channel (a failure "
                     "from EITHER stage re-raised as itself, a merged dataset "
                     "returned as itself). Observationally the identity on "
                     "`Except OpErr Dataset`, so the postcondition holds — but "
                     "the frozen tactic body no longer closes it, so this case "
                     "REPROVES the obligation with a case split on the reading "
                     "AND on the merge outcome. The `theorem correct_merge` "
                     "statement is byte-identical and nothing is assumed (no "
                     "lemma, no axiom, no `sorry`), so the verification is a real "
                     "discharge of the real obligation for a different impl "
                     "shape. If a correct impl whose proof must be redone cannot "
                     "verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-both-operand-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_OLD, _PROOF_ADMISS),
        "rationale": "the frozen impl is kept VERBATIM and two GROUND instances of "
                     "the postcondition are established inside the tactic body — "
                     "one per operand shape the modeled behavior must handle: a "
                     "second operand that is a single named array (the shape the "
                     "added test coverage exercises) and one that is already a "
                     "dataset — before the frozen obligation is closed verbatim. "
                     "This bundle's obligation states NO precondition (it "
                     "quantifies over every receiver and every operand shape "
                     "unconditionally, including the operands the reading raises "
                     "on), so nagini's read-permission / distinct-object / "
                     "named-array admissibility clauses have no counterpart to "
                     "admit; what remains portable is the satisfiability "
                     "question, and this asks it at each shape. If either ground "
                     "instance could not be established the behavior would be "
                     "unsatisfiable at exactly an input the tests exercise — the "
                     "analogue of PRECOND-TOO-STRONG. Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, the "
                     "instances are `have`s in the existing body.",
    },

    # ---- uniqueness (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-drop-reading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_READING),
        "refinement": "this IS the behavior Solution_prepatch.lean reproduces and "
                      "G-DIFF flags: the second operand is handed onward without "
                      "first being read as a dataset when it arrives as a single "
                      "named array. The sole F2P test, "
                      "TestMergeMethod::test_merge_dataarray, does exactly that — "
                      "it asks a dataset to merge a single named array and "
                      "asserts the answer is identical to the top-level merge of "
                      "the two. With the reading absent the array shape is not "
                      "something the underlying dataset-to-dataset merge can "
                      "consume: it fails, raising rather than returning the "
                      "merged dataset, which is precisely the traceback quoted in "
                      "the problem statement. Its faithful real patch is the "
                      "un-patched code, so it is exactly what does NOT resolve.",
        "rationale": "rejected by clause C1 of `result = (asDataset other).bind "
                     "(mergeDatasets self)`: on the `.da a` operand shape the spec "
                     "demands the reading of `a` bound into the merge with `self` "
                     "(`asDataset (.da a)` reduces to `datasetOfArray a`), while "
                     "the rival yields a constant failure, which is neither the "
                     "merge outcome where the reading succeeds nor the reading's "
                     "own error where it raises. Attributed by a witness at the "
                     "`.da` shape over an arbitrary receiver, stated over the "
                     "whole composition so it needs no assumption about which "
                     "region the point is in. Direct port of nagini's "
                     "drop-the-conversion rival, re-expressed against the merge "
                     "OUTCOME (this carrier) rather than against a mapping-shaped "
                     "flag on an operand-list element (nagini's).",
        "witness": _W_DROP_READING,
    },
    {
        "id": "uniq-substitute-noop-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SUBSTITUTE_NOOP),
        "refinement": "a NEAR-MISS that reads the single-named-array shape "
                      "correctly — so the F2P scenario itself is unaffected — and "
                      "abuses only the pass-through shape, where it discards the "
                      "operand and merges the receiver with itself. Its faithful "
                      "real patch would replace an already-dataset second operand "
                      "by the receiver before merging, so any merge of two "
                      "DIFFERENT datasets would silently return the receiver's "
                      "own content and drop the operand's. The P2P suite pins "
                      "that directly: TestMergeMethod::test_merge merges a "
                      "one-variable dataset with a different one-variable dataset "
                      "and asserts the answer carries BOTH variables, and "
                      "test_merge_auto_align / test_merge_fill_value assert "
                      "merged answers combining two disjoint variables. All would "
                      "get the receiver back and fail their identity assertions, "
                      "so the patch does NOT resolve (resolution requires the "
                      "P2P set to keep passing).",
        "rationale": "rejected by clause C2: `asDataset (.ds d)` is `Except.ok d`, "
                     "so the spec demands the merge of `self` with the operand it "
                     "was given, while the rival merges `self` with `self`. "
                     "Witnessed at a DIFFERENT input point from the other rivals "
                     "— the `.ds` shape, over the dataset a SUCCESSFUL reading of "
                     "an arbitrary named array yields — so the operand binder is "
                     "genuinely varied, and `hread` keeps that operand one the "
                     "modeled behavior actually produces (the reading is partial, "
                     "so its result cannot be named without assuming it "
                     "succeeds). Re-expresses nagini's lossy-rebuild rival: "
                     "nagini killed that one on OBJECT IDENTITY (a freshly built "
                     "operand is not the same object as the one passed in), which "
                     "a referentially-transparent value carrier has no "
                     "counterpart for; the portable half of the argument is that "
                     "the pass-through shape must be used AS GIVEN, and that is "
                     "what this attacks.",
        "witness": _W_SUBSTITUTE_NOOP,
    },
    {
        "id": "uniq-reverse-operand-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REVERSE_ORDER),
        "refinement": "the operand is read exactly as the spec reads it, the "
                      "short-circuit on a failed reading is preserved, and both "
                      "operands do reach the underlying merge — only their order "
                      "is swapped, so the receiver becomes the absorbed operand "
                      "rather than the absorbing one. Merge is order-dependent in "
                      "precisely the ways the P2P suite pins: "
                      "TestMergeMethod::test_merge_compat asserts that merging "
                      "with the overriding compatibility setting returns the "
                      "RECEIVER's value for a conflicting variable — reversed, "
                      "the operand's value wins and the identity assertion fails; "
                      "test_merge_auto_align and test_merge_no_conflicts assert "
                      "left- and right-joined answers, which are aligned to the "
                      "FIRST operand's index and so come out different when the "
                      "order flips. Does NOT resolve.",
        "rationale": "rejected by clause C3: the spec fixes the two merge operands "
                     "in order — `(asDataset other).bind (mergeDatasets self)` "
                     "merges `self` with the read operand — and the rival binds "
                     "the reading into `fun other' => mergeDatasets other' self`. "
                     "The witness assumes only that the underlying merge is not "
                     "symmetric at the probed pair and derives the "
                     "contradiction; it probes the mirror image of the "
                     "substitute-noop witness's point, so the two rivals are "
                     "refuted at genuinely different places. Direct port of "
                     "nagini's swap-the-operand-order rival.",
        "witness": _W_REVERSE_ORDER,
    },
    {
        "id": "uniq-swallow-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWALLOW_FAILURE),
        "refinement": "NEW to this carrier (nagini's abstraction has no failure "
                      "channel to attack): the operand is read correctly, a failed "
                      "reading short-circuits correctly, the merge runs on the "
                      "right operands in the right order, and a successful outcome "
                      "is propagated verbatim — but the failure the MERGE raises "
                      "is SWALLOWED and the receiver handed back as a success. A "
                      "rival that agrees with the spec everywhere the merge "
                      "succeeds, so it is the most dangerous kind of near-miss. "
                      "Its faithful real patch would catch the conflict the merge "
                      "raises and return the receiver instead, and the P2P suite "
                      "asserts that raise explicitly and repeatedly: "
                      "TestMergeMethod::test_merge_compat expects a raised merge "
                      "conflict for four different compatibility settings and for "
                      "a conflicting-attribute operand, and "
                      "test_merge_no_conflicts expects one for two different "
                      "conflicting operands. Swallowed, nothing raises and every "
                      "one of those expectations fails. Does NOT resolve.",
        "rationale": "rejected by clause C4 on the MERGE stage's ERROR arm: the "
                     "spec's equation is over `Except OpErr Dataset`, so it pins "
                     "BOTH channels of the outcome verbatim, not just the "
                     "successful one. The witness conditions on the carrier at a "
                     "point where the merge does raise — that is the only "
                     "sub-domain where the rival is wrong, so no witness at a "
                     "succeeding point could discriminate it — and it places that "
                     "raise on TWO DISTINCT operands (an arbitrary receiver "
                     "against the dataset a successful reading yields). The "
                     "distinctness is load-bearing rather than cosmetic: an "
                     "assumed raise on `mergeDatasets X X` would be CONSISTENT on "
                     "this opaque carrier — no tactic can derive `False` from it, "
                     "so the gate's probe passes it — while describing a "
                     "sub-domain the modeled behavior does not have, since merging "
                     "a dataset with itself has nothing to disagree about. "
                     "`hread` is the same discipline one stage earlier: without "
                     "it the probed point could sit in the reading's error "
                     "region, where this rival is CORRECT.",
        "witness": _W_SWALLOW_FAILURE,
    },
    {
        "id": "uniq-unmerged-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_UNMERGED_OPERAND),
        "refinement": "NEW to this carrier: the reading of the second operand is "
                      "entirely CORRECT — the single named array is absorbed as "
                      "its equivalent one-variable dataset and a failed reading is "
                      "propagated, exactly as the spec says — and the reading is "
                      "then returned as the outcome without the underlying merge "
                      "ever running. The receiver's own content never reaches the "
                      "answer. This is the rival that shows reading the operand "
                      "right is not sufficient, and it is refuted by the F2P test "
                      "directly: TestMergeMethod::test_merge_dataarray asks a "
                      "one-variable dataset to merge a single named array and "
                      "asserts the answer is identical to the top-level merge of "
                      "the two, which carries BOTH variables; this rival's answer "
                      "carries only the array's. Does NOT resolve.",
        "rationale": "rejected by clause C4 on the SUCCESS arm: the spec demands "
                     "the underlying merge's own outcome bound onto the reading, "
                     "and the rival returns the reading itself without invoking "
                     "the merge. The witness assumes only that merging the "
                     "receiver with the reading is not just the reading handed "
                     "back — i.e. that the merge does something — and derives the "
                     "contradiction; stated over the whole composition, so it "
                     "needs no assumption about which region the point is in. It "
                     "shares the drop-reading witness's input point (`.da` shape, "
                     "arbitrary receiver) legitimately: both rivals fail there "
                     "for the same reason, namely that the answer at that point "
                     "is not the composition the spec names.",
        "witness": _W_UNMERGED_OPERAND,
    },
    {
        "id": "uniq-relabel-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RELABEL_FAILURE),
        "refinement": "ADDED BY AUDIT to close a gap the battery left: the "
                      "narrowest near-miss on the MERGE stage. The operand is read "
                      "correctly, the short-circuit is preserved, the merge runs "
                      "on the right operands in the right order, the success arm "
                      "is propagated verbatim, and the merge's failure arm is "
                      "still a FAILURE — only the raised failure's own content is "
                      "replaced by a constant. uniq-swallow-failure establishes "
                      "that a raise may not be converted into a success; nothing "
                      "established that the raise's PAYLOAD is pinned, which is a "
                      "separate half of the same clause. Its faithful real patch "
                      "would catch the conflict the merge raises and re-raise a "
                      "generic one in its place, discarding the diagnostic the "
                      "merge computed. That is a real behavior change: the "
                      "operation would still raise the right exception type, so "
                      "the P2P expectations that only assert a raise still pass, "
                      "but every caller reading the message gets a constant "
                      "string. Weaker refutation evidence than the other rivals "
                      "(the P2P suite pins the raise, not its text — checked: no "
                      "TestMergeMethod case matches on the message), so this case "
                      "is carried on the spec's own terms: the postcondition is an "
                      "equation over `Except OpErr Dataset` and `OpErr` carries a "
                      "reason, so the reason is inside what the equation pins.",
        "rationale": "rejected by clause C4 on the merge stage's error arm PAYLOAD "
                     "rather than its channel: `result = (asDataset other).bind "
                     "(mergeDatasets self)` is an equation between `Except OpErr "
                     "Dataset` values, and `OpErr` is a structure carrying "
                     "`reason`, so equality of the two sides requires the reason "
                     "to agree too — a rival that raises `{ reason := \"merge "
                     "conflict\" }` where the merge raised something else violates "
                     "it. Witnessed at a point where the merge raises a NAMED "
                     "failure the rival discards; `hread` puts that point in the "
                     "region where the merge runs at all, and the two merge "
                     "operands there are distinct, so the assumed raising "
                     "sub-domain is one the modeled behavior actually has. "
                     "Verified by rebuild: witness elaborates against the rival "
                     "(exit 0) and fails on the frozen solution (exit 1) — a "
                     "semantic refutation, not a name or type error.",
        "witness": _W_RELABEL_FAILURE,
    },
    {
        "id": "uniq-substitute-success-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SUBSTITUTE_SUCCESS),
        "refinement": "ADDED BY A SECOND AUDIT to close the mirror of the gap "
                      "uniq-relabel-failure closed. That rival established that "
                      "the MERGE's ERROR arm payload is pinned; this one "
                      "establishes it for its SUCCESS arm. The operand is read "
                      "correctly, the short-circuit is preserved, the merge runs "
                      "on the right two operands in the right order, its outcome "
                      "is consulted, and a raised failure is re-raised with its "
                      "own payload intact — only the merged dataset is replaced, "
                      "by the receiver. Its faithful real patch would consult the "
                      "merge for whether it conflicts and then return the receiver "
                      "unchanged instead of the merged result, so every successful "
                      "merge would silently discard the second operand's "
                      "contribution while still raising on conflict. The F2P "
                      "scenario refutes it directly: "
                      "TestMergeMethod::test_merge_dataarray asks a one-variable "
                      "dataset to merge a single named array and asserts the "
                      "answer is identical to the top-level merge of the two, "
                      "which carries BOTH variables; this rival's answer carries "
                      "only the receiver's. The P2P suite pins it repeatedly too: "
                      "TestMergeMethod::test_merge asserts a merge of two "
                      "different one-variable datasets carries both variables, "
                      "and test_merge_auto_align / test_merge_fill_value assert "
                      "answers combining two disjoint variables on a widened "
                      "index. All would get the receiver back. Does NOT resolve. "
                      "Distinct from uniq-unmerged-operand, which never invokes "
                      "the merge at all and returns the OPERAND: this one invokes "
                      "it, branches on it, and returns the RECEIVER, so it agrees "
                      "with the spec on the whole error arm where that rival does "
                      "not.",
        "rationale": "rejected by clause C4 on the SUCCESS arm's PAYLOAD: "
                     "`result = (asDataset other).bind (mergeDatasets self)` is an "
                     "equation over `Except OpErr Dataset`, so the value inside "
                     "`.ok` is pinned as tightly as the channel is. A rival "
                     "returning `Except.ok self` where the merge returned "
                     "`Except.ok merged` violates it exactly when `merged ≠ "
                     "self`. Witnessed at that sub-domain by naming the merge's "
                     "own answer as a binder and assuming it differs from the "
                     "receiver — which is what makes the assumed sub-domain a "
                     "real one and not merely a consistent one: assuming only "
                     "that the merge SUCCEEDS would include points where the "
                     "merged answer IS the receiver (merging in nothing new), "
                     "and the rival is right there. `hread` does the same for the "
                     "reading stage, and the two merge operands in the hypothesis "
                     "are distinct. Verified by rebuild: witness elaborates "
                     "against the rival (exit 0) and fails on the frozen solution "
                     "(exit 1), a semantic refutation.",
        "witness": _W_SUBSTITUTE_SUCCESS,
    },
    {
        "id": "uniq-swallow-reading-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWALLOW_READING_FAILURE),
        "refinement": "ADDED BY THE FAITHFULNESS PANEL, which found the modeled "
                      "reading has an error region the battery had no rival for. "
                      "The reading here is the very one the spec names, so on "
                      "every operand where it succeeds this rival is "
                      "byte-for-byte the frozen behavior and the F2P scenario "
                      "passes; where the reading RAISES, it swallows the failure "
                      "and hands the receiver back as a success. Its faithful "
                      "real patch would guard the coercion of a DataArray operand "
                      "and fall back to returning the receiver when the coercion "
                      "will not go through — so an operand the one-variable "
                      "reading does not apply to would silently produce the "
                      "receiver unchanged instead of raising. The P2P suite pins "
                      "the raise on the top-level path that shares this reading: "
                      "TestMergeFunction::test_merge_dataarray_unnamed asserts "
                      "that an unnamed array operand raises, and "
                      "test_merge_wrong_input_error asserts a raise for an "
                      "operand that cannot be read at all. A fallback that "
                      "returns the receiver satisfies neither. Does NOT resolve.",
        "rationale": "rejected by clause C5, the short-circuit `bind` performs: "
                     "where `asDataset other` is `Except.error e`, `(asDataset "
                     "other).bind (mergeDatasets self)` IS `Except.error e` — the "
                     "merge does not run and the reading's failure is the whole "
                     "answer — while the rival returns `Except.ok self` there. "
                     "The witness conditions on exactly that region (`h : "
                     "datasetOfArray … = Except.error e`, the raised failure a "
                     "binder), which is the only sub-domain where this rival is "
                     "wrong; a witness at a succeeding reading could not "
                     "discriminate it, since the rival and the frozen impl agree "
                     "there. This clause exists only because the modeled reading "
                     "is PARTIAL: under a total reading there would be no error "
                     "region for the first stage and this rival could not be "
                     "built, so its rejection is the machine-checked evidence "
                     "that the region is real and pinned.",
        "witness": _W_SWALLOW_READING_FAILURE,
    },
    {
        "id": "uniq-relabel-reading-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RELABEL_READING_FAILURE),
        "refinement": "ADDED BY THE FAITHFULNESS PANEL as the mirror of "
                      "uniq-relabel-failure one stage earlier, and the narrowest "
                      "near-miss in the whole battery. The reading is the spec's "
                      "own, the merge stage is untouched, a failed reading DOES "
                      "short-circuit and IS still a failure — only that failure's "
                      "own content is replaced by a constant. It agrees with the "
                      "spec on every operand where the reading succeeds (so both "
                      "the F2P scenario and every P2P merge assertion pass) and, "
                      "on the failing region, it agrees about the channel too. "
                      "Its faithful real patch would catch the error the coercion "
                      "raises and re-raise a generic one in its place, discarding "
                      "the diagnostic that says WHICH way the array could not be "
                      "read — an unnamed array and an array colliding with its "
                      "own coordinate would report the same constant message. "
                      "Weaker refutation evidence than the other rivals (the P2P "
                      "cases pin the raise, and test_merge_dataarray_unnamed "
                      "matches on the message via raises_regex, but the constant "
                      "could be chosen to match it), so this case is carried on "
                      "the spec's own terms, exactly as uniq-relabel-failure is: "
                      "the postcondition is an equation over `Except OpErr "
                      "Dataset` and `OpErr` carries a reason, so `bind`'s "
                      "verbatim propagation of the reading's error pins that "
                      "reason.",
        "rationale": "rejected by clause C6: `bind` propagates the reading's error "
                     "VERBATIM, payload included, so where `asDataset other` is "
                     "`Except.error e` the spec demands exactly `Except.error e` "
                     "and not a failure carrying some other reason. `OpErr` is a "
                     "structure with a `reason` field, so equality of the two "
                     "sides of the equation requires the reasons to agree. "
                     "Witnessed at a point where the reading raises a NAMED "
                     "failure the rival discards; the hypothesis names the "
                     "reading's outcome once. Like C5, this clause exists only "
                     "because the modeled reading is partial, and this rival is "
                     "what establishes that the first stage's payload is pinned "
                     "as tightly as the merge stage's.",
        "witness": _W_RELABEL_READING_FAILURE,
    },
    {
        "id": "uniq-receiver-special-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RECEIVER_SPECIAL_CASE),
        "refinement": "ADDED BY A THIRD AUDIT to close the one binder the battery "
                      "left unprobed. Every rival above is witnessed at a receiver "
                      "PINNED to a single arbitrary dataset; this rival is the frozen "
                      "behavior EXACTLY at that receiver — the reading, the "
                      "short-circuit, the merge, both payloads, all verbatim — and a "
                      "constant failure at every other receiver. Its faithful real "
                      "patch would guard the whole method on the receiver being one "
                      "particular dataset and refuse the operation for all others, so "
                      "every merge whose receiver is not that one raises instead of "
                      "merging. The F2P scenario and the whole P2P suite refute it "
                      "directly, since they build their own receivers: "
                      "TestMergeMethod::test_merge_dataarray asks a one-variable "
                      "dataset to merge a single named array and asserts the answer is "
                      "identical to the top-level merge of the two, and "
                      "TestMergeMethod::test_merge / test_merge_auto_align / "
                      "test_merge_compat / test_merge_fill_value each merge into a "
                      "receiver they construct themselves. All would raise. Does NOT "
                      "resolve.",
        "rationale": "rejected by the obligation's UNIVERSAL quantification over the "
                     "receiver: `correct_merge` reads `∀ (self : Dataset) (other : "
                     "MergeOther), problem_spec_merge self other (implementation_merge "
                     "self other)`, so `result = (asDataset other).bind (mergeDatasets "
                     "self)` must hold at EVERY receiver, not merely at one. This is "
                     "the only case here whose witness binds `self` rather than "
                     "pinning it, and the distinction is MEASURED rather than argued: "
                     "a witness in the shipped pinned-receiver style fails to refute "
                     "this rival (exit 1, `unsolved goals … ⊢ False`), because the "
                     "rival IS the frozen behavior at that pinned point; the witness "
                     "below, whose `hself` places the receiver off that point, "
                     "elaborates against the rival (exit 0) and fails on the frozen "
                     "solution (exit 1). The forgery control was run too: the FLIPPED "
                     "claim (the postcondition HOLDS at that hypothesized point) "
                     "builds on the frozen solution (exit 0) and fails on the rival "
                     "(exit 1), so gold's exit code tracks the claim and the "
                     "refutation is semantic rather than syntactic. No nagini "
                     "counterpart: nagini's receiver is pinned by its permission "
                     "preconditions, so the universally-quantified receiver is new to "
                     "this carrier.",
        "witness": _W_RECEIVER_SPECIAL_CASE,
    },
    {
        "id": "uniq-operand-special-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OPERAND_SPECIAL_CASE),
        "refinement": "ADDED BY A FOURTH AUDIT, which found that "
                      "uniq-receiver-special-case closed the receiver binder and "
                      "left the identical hole one binder over: every `.da` witness "
                      "in this battery probes the single array term "
                      "`Classical.arbitrary DataArray`. This rival is the frozen "
                      "behavior EXACTLY at that one array — the reading of the array "
                      "as its equivalent one-variable dataset, the short-circuit, "
                      "the merge, both payloads, all verbatim — and a constant "
                      "failure at every other array. Its faithful real patch would "
                      "guard the array-shaped branch on the operand being one "
                      "particular array and refuse the operation for all others, so "
                      "every merge of a named array the guard does not admit raises "
                      "instead of merging. The F2P scenario refutes it directly: "
                      "TestMergeMethod::test_merge_dataarray builds its own named "
                      "array operand and asserts the answer is identical to the "
                      "top-level merge of the two, and "
                      "TestMergeFunction::test_merge_dataarray_unnamed asserts a "
                      "specific raise for an operand the reading rejects — a "
                      "constant refusal for every other array satisfies neither. "
                      "Does NOT resolve.",
        "rationale": "rejected by the obligation's UNIVERSAL quantification over the "
                     "second operand's PAYLOAD, not merely over its two "
                     "constructors: `correct_merge` reads `∀ (self : Dataset) "
                     "(other : MergeOther), problem_spec_merge self other "
                     "(implementation_merge self other)`, and `asDataset (.da a) = "
                     "datasetOfArray a` must hold at EVERY array `a`, not at one. "
                     "The gap this closes was MEASURED rather than argued, and it is "
                     "a gap the coverage reporter cannot see: it reads `other` as "
                     "varying because the `.ds`/`.da` CONSTRUCTORS vary, while the "
                     "array the `.da` constructor carries is the same term in all "
                     "six `.da` witnesses. All TEN previously shipped witnesses fail "
                     "to refute this rival (10/10 exit 1 — the reading-region ones "
                     "landing on `unsolved goals … ⊢ False`), because each looks "
                     "only where the rival IS the frozen behavior. The witness "
                     "below binds `a` and `self` and hypothesizes only that the "
                     "array is a DIFFERENT one: it elaborates against the rival "
                     "(exit 0), fails on the frozen solution (exit 1), and its "
                     "consistency probe cannot derive `False` (exit 1). The forgery "
                     "controls were run both ways: the FLIPPED claim (the "
                     "postcondition HOLDS at that hypothesized point) builds on the "
                     "frozen solution (exit 0) and fails on the rival (exit 1), and "
                     "the TYPE-REVEALING build shows gold's goal reduced to `⊢ "
                     "False` (the simp set PROVED the equation for the frozen impl) "
                     "while the rival's is left as the concrete `¬ Except.error "
                     "{ reason := \"unsupported operand\" } = match datasetOfArray a "
                     "with …`. So gold's exit code tracks the claim and the "
                     "refutation is semantic. No nagini counterpart: nagini's "
                     "operand is pinned by its permission preconditions.",
        "witness": _W_OPERAND_SPECIAL_CASE,
    },
    {
        "id": "uniq-dataset-operand-special-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DS_OPERAND_SPECIAL_CASE),
        "refinement": "ADDED BY A FIFTH AUDIT, which found that "
                      "uniq-operand-special-case closed the `.da` constructor's "
                      "PAYLOAD and left the identical hole on the OTHER "
                      "constructor: the dataset the `.ds` shape carries is a "
                      "pinned term in every witness the battery shipped. This "
                      "rival is the frozen behavior EXACTLY at that one dataset "
                      "operand — the pass-through reading, the merge, both "
                      "payloads, all verbatim — and a constant failure at every "
                      "other dataset operand. Its faithful real patch would guard "
                      "the already-a-dataset branch on the operand being one "
                      "particular dataset and refuse the operation for all others, "
                      "so every merge whose second argument is a dataset the guard "
                      "does not admit raises instead of merging. The P2P suite "
                      "refutes it wholesale, since every one of those cases builds "
                      "its own dataset operand: "
                      "TestMergeMethod::test_merge merges a one-variable dataset "
                      "into another and asserts the answer carries both variables, "
                      "test_merge_broadcast_equals / test_merge_auto_align / "
                      "test_merge_fill_value / test_merge_no_conflicts each assert "
                      "a merged answer for a dataset operand they construct, and "
                      "test_merge_compat asserts specific raises for its own "
                      "constructed operands. All would get the constant refusal "
                      "instead. Does NOT resolve.",
        "rationale": "rejected by the obligation's UNIVERSAL quantification over "
                     "the `.ds` constructor's PAYLOAD: `correct_merge` reads `∀ "
                     "(self : Dataset) (other : MergeOther), problem_spec_merge "
                     "self other (implementation_merge self other)`, and `asDataset "
                     "(.ds d) = Except.ok d` must hold at EVERY dataset `d`, not at "
                     "one. The gap this closes was MEASURED, not argued, and it is "
                     "invisible to the coverage reporter for the same reason "
                     "uniq-operand-special-case's was: the reporter reads `other` as "
                     "varying because the two CONSTRUCTORS vary, while the payload "
                     "each constructor carries is pinned. All ELEVEN previously "
                     "shipped witnesses fail to refute this rival (11/11 exit 1), "
                     "because each looks only where the rival IS the frozen "
                     "behavior. The witness below binds `d` and `self` and "
                     "hypothesizes only that the dataset operand is a DIFFERENT "
                     "one: it elaborates against the rival (exit 0), fails on the "
                     "frozen solution (exit 1), and its consistency probe cannot "
                     "derive `False` (exit 1). Both forgery controls were run: the "
                     "FLIPPED claim (the postcondition HOLDS at that hypothesized "
                     "point) builds on the frozen solution (exit 0) and fails on the "
                     "rival (exit 1), and the TYPE-REVEALING build shows gold's goal "
                     "reduced to `⊢ False` (the simp set PROVED the equation for the "
                     "frozen impl) while the rival's is left as the concrete `¬ "
                     "Except.error { reason := \"unsupported dataset operand\" } = "
                     "mergeDatasets self d`. So gold's exit code tracks the claim "
                     "and the refutation is semantic. No nagini counterpart: "
                     "nagini's operand is pinned by its permission preconditions.",
        "witness": _W_DS_OPERAND_SPECIAL_CASE,
    },
]

# ===========================================================================
# DIVERGENCE LANE — VACUOUS on this carrier, and MEASURED rather than asserted
# (recorded by the second audit; the port carried no disposition for this class).
#
# This bundle's frozen file sets no `loom.semantics.termination` option at all —
# it is a plain Lean file over a total `noncomputable def`, so neither the
# "total" nor the "partial" disposition applies verbatim. What decides the class
# here is that `implementation_merge` inhabits `Id`, and `Id.bind x f` reduces to
# `f x` WITHOUT evaluating `x`. A diverging prefix's value is discarded by the
# continuation, so the prefix is erased for definitional equality and denotes
# nothing the logic can see. Measured, with real builds:
#
#   * the frozen impl with `while true do pure ()` spliced in front of it and the
#     frozen proof unchanged VERIFIES (exit 0) — but that is not a hole, because
#     it is the same claim the frozen impl makes: the prefix is dead code, so the
#     variant is definitionally the frozen impl and the case would be VACUOUS
#     under attack C rather than a spec break;
#   * the decisive control — the same diverging prefix in front of a WRONG answer
#     (`return Except.error { reason := "diverged" }`) — is REJECTED (exit 1,
#     `Tactic 'rfl' failed`, and the goal printed shows the `forIn Lean.Loop.mk`
#     term still standing next to the spec's demand). So divergence buys a rival
#     NOTHING: the postcondition is not vacuously satisfied and the value
#     obligation is discharged in full;
#   * `example (v w : Nat) : prefixed v = w := by rfl` FAILS while
#     `example (v : Nat) : prefixed v = v := by rfl` succeeds, which is the
#     direct demonstration that the loop is erased dead code and not an opaque
#     term that unifies with any answer;
#   * a genuinely non-terminating shape — `partial def implementation_merge ... :=
#     implementation_merge self other` — cannot discharge the obligation at all
#     (four proof attempts, all exit 1: `unfold` refuses a `partial def`'s
#     equations, `simp` makes no progress, `rfl` fails). It is REJECTED, so it is
#     not shippable as a hole either.
#
# So there is no diverging rival to ship: the weak form is vacuous (it IS the
# frozen impl) and every form that changes the answer is already rejected by the
# clauses the uniqueness lane carries. This is a vacuous CLASS, not a known hole
# — the spec pins the value on every path.
# ===========================================================================
#
# ===========================================================================
# AXIOM LANE — deliberately absent. The nagini sibling carries two AXIOM_TESTS
# (a soundness probe and a containment probe for its deep-model conversion
# reference). Those belong to G-AX, which this gate ignores, and this bundle's
# meta.json already records G-AX=pass over 601 scenarios for both A-reference
# callees. Dropped by the porting map, not by omission.
# ===========================================================================

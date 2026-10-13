# properties.py — G-PBT falsification battery for django__django-16116 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against
# the frozen spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier (a total Lean `def` over three Boolean inputs).
#
# Defended surface (read from Solution.lean):
#   problem_spec_processChanges
#     (hasChanges checkOnly mergeIntoLast : Bool) (result : CommandEffect) : Prop
#   implementation_processChanges
#     (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect
#   with `CommandEffect := { wroteToLast : Bool, wroteNew : Bool, exitCode : Option Nat }`.
#
#   The spec pins EVERY output field for EVERY combination of the three inputs,
#   in three independent top-level clauses selected by the input guards:
#     (C1) !hasChanges →
#            wroteToLast = false ∧ wroteNew = false ∧ exitCode = none
#          — nothing detected: emit nothing, complete normally.
#     (C2) hasChanges ∧ checkOnly →
#            wroteToLast = false ∧ wroteNew = false ∧ exitCode = some 1
#          — verification-only mode: request an immediate non-zero exit and emit
#            NOTHING (this is the discriminating clause the change establishes).
#     (C3) hasChanges ∧ !checkOnly →
#            wroteToLast = mergeIntoLast ∧ wroteNew = (!mergeIntoLast) ∧
#            exitCode = none
#          — otherwise emit exactly one form of output (merged-into-latest iff
#            mergeIntoLast, a fresh file otherwise) and complete normally.
#
# What each nagini ingredient becomes on this carrier
# ----------------------------------------------------
# The nagini sibling contracts a single side-effecting procedure whose store is a
# produced-file list and whose control-flow effect (raise vs return) is pinned by
# an Exsures/Ensures pair. This bundle models the SAME decision purely: the
# store-grew Exsures conjunct and the raise-vs-return guard both collapse onto the
# fully-determined `CommandEffect` fields, so the nagini reasoning ports as
# clause-level attacks on those fields.
#
#   * nagini EXIT-FIRST Exsures (store unchanged on the check-mode raise) →
#     this bundle's C2 emit-nothing conjuncts (wroteToLast = false ∧ wroteNew =
#     false) TOGETHER with exitCode = some 1. A rival that emits before exiting
#     grows an emit-flag and is caught by C2, exactly as the nagini store-growth
#     conjunct catches a writer that ran before the raise.
#   * nagini NORMAL-RETURN guard `Ensures(not check_mode)` → this bundle's C2
#     exitCode = some 1 conjunct. Returning normally in check mode (exitCode =
#     none) is the analogue of returning instead of raising.
#   * nagini GROWTH pin `len(store) >= len(Old)+1` → this bundle's C3 emit
#     conjuncts (exactly one of wroteToLast / wroteNew is true on the normal
#     path). A rival that emits nothing on the normal path fails C3.
#
# Carrier narrowing vs the nagini sibling
# ---------------------------------------
#   * The nagini GROWTH pin is grounded in real writer axioms (len >= +1). Here
#     the writers' file-content behaviour is unmodeled and irrelevant to the fix;
#     only WHICH form of output ran is observable, recorded by two Boolean flags.
#     So there is no echoable oracle and no A-consumed axiom — the axiom lane is
#     empty (AXIOM_TESTS = []) and G-AX's job, not this gate's.
#   * The three-input carrier gives an attack surface the nagini single-store
#     model did not name explicitly: WRITER SELECTION on the normal path (the
#     mergeIntoLast dependence of C3) and the no-changes branch (C1). Two rivals
#     with no direct nagini counterpart are added so every input binder is abused
#     by some reject witness and every clause is attacked.
#
# Vacuous / dropped classes (stated per directive, not silently omitted)
# ----------------------------------------------------------------------
#   * nagini `rival-no-raise-in-check` — PORTED (as rival-emit-in-check-no-exit).
#     The nagini rival keeps a check-mode branch but emits a FRESH artefact there
#     and returns instead of raising. That is observably DISTINCT on this carrier
#     from rival-check-returns-normally (which deletes the guard and dispatches by
#     mergeIntoLast): at (true, true, true) the no-raise shape yields
#     wroteNew = true while the guard-deleted shape yields wroteToLast = true. An
#     earlier revision of this manifest dropped it with no recorded reason; it is
#     expressible and is now shipped.
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. The nagini file itself
#     records this class as inapplicable (the store is full-permission, so the
#     relevant store attack is value-level, not a permission violation). Lean is
#     referentially transparent: no aliasable read-only input exists. The nagini
#     value-level "mutate-then-exit-in-check" rival is NOT a frame case; it ports
#     as an emit-then-exit rival and is subsumed by rival-write-then-exit on this
#     carrier (setting an emit flag true before the check-mode exit is exactly
#     what the pre-patch order does), so it is not shipped as a separate case —
#     see `assessment`.
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean. The nagini sibling
#     carries no such case, and `implementation_processChanges` is a total Lean
#     `def`: a diverging implementation cannot be written, so the class does not
#     exist on this carrier (contrast velvet's `partial` semantics, a known spec
#     hole — not relevant to lean; see the corpus-wide termination-semantics finding).
#   * ADMISSIBILITY (nagini admiss-self-call) — PORTED (as admiss-f2p-input).
#     An earlier revision dropped this lane on the ground that
#     `correct_processChanges` carries NO precondition hypothesis, so "there is
#     nothing for an admissibility positive to establish". That reason is wrong:
#     it describes the nagini FORM of the case, not its JOB. On a total carrier
#     the analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
#     exactly an F2P-shaped input — a spec whose clauses cannot be jointly
#     discharged there is vacuously "proven" by a `False`-deriving script and
#     admits anything. That is tested directly by discharging the obligation at
#     the concrete F2P input BY EVALUATION as a `have`, and only then closing the
#     frozen obligation verbatim. Shipped; see admiss-f2p-input.
#   * AXIOM lane — DROPPED (meta.axioms == []; no opaque callee). AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-16116"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl-region body and the proof tactic body (after the byte-identical
# `theorem correct_processChanges` STATEMENT) are the ONLY regions a variant may
# edit. The spec, the structure, the signatures, and the theorem statement are
# never touched, so same_spec holds by construction.

_IMPL_OLD = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro hasChanges checkOnly mergeIntoLast
  unfold problem_spec_processChanges implementation_processChanges
  cases hasChanges <;> cases checkOnly <;> cases mergeIntoLast <;>
    simp [Id.run, bind, pure]"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl body, and (for
    soundness positives whose reshaped impl needs a matching proof) the proof
    tactic body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Each is a structurally different
# but behaviourally identical correct impl, shipped WITH a proof that closes for
# the new shape (the theorem statement is byte-identical; only the tactic body
# changes). No new lemma / axiom / sorry. The frozen proof case-splits on all
# three Bools and `simp`s each leaf, so any impl that reduces to the same
# CommandEffect on every leaf is closed by the SAME tactic.
# ---------------------------------------------------------------------------

# pos-reorder-writers: keep the check-mode exit FIRST, but rewrite the writer
# dispatch in the OPPOSITE branch order (test `!mergeIntoLast` first, fresh writer
# in the then-branch, merge writer in the else). Semantically identical; a
# different control-flow source. Mirrors nagini pos-control-reorder-writers. If it
# fails to verify the spec is over-fit to one writer-branch order => SPEC-TOO-STRONG.
_POS_REORDER = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if !mergeIntoLast then
    eff := { eff with wroteNew := true }
  else
    eff := { eff with wroteToLast := true }
  return eff"""

# pos-pure-functional: the same decision as a pure functional nested match (no
# Id.run / no `let mut`), the shape the underlying branch actually has. Same
# semantics, different block structure. Mirrors nagini pos-control-nested-else. If
# it fails the spec is over-fit to the imperative `Id.run do` encoding =>
# SPEC-TOO-STRONG.
_POS_PURE = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect :=
  if !hasChanges then
    { wroteToLast := false, wroteNew := false, exitCode := none }
  else if checkOnly then
    { wroteToLast := false, wroteNew := false, exitCode := some 1 }
  else
    { wroteToLast := mergeIntoLast, wroteNew := !mergeIntoLast, exitCode := none }"""

# pos-boolean-algebra: no branching at all — every output field is a single
# Boolean / Option expression over the three inputs, so the impl shares NO
# control-flow structure with the frozen one (which the two positives above both
# still do: `_POS_PURE`'s three arms are the frozen guards in the frozen order,
# and its else-arm is the spec's C3 RHS verbatim). This is the strongest
# available soundness probe on this carrier: if the spec admitted only the
# guard-shaped encoding, a branchless impl computing the same function would be
# rejected. Verified to close under the FROZEN proof tactic unchanged.
_POS_BOOL_ALGEBRA = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect :=
  { wroteToLast := hasChanges && !checkOnly && mergeIntoLast,
    wroteNew := hasChanges && !checkOnly && !mergeIntoLast,
    exitCode := if hasChanges && checkOnly then some 1 else none }"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region; every one ships a `witness` proving it violates the spec at a
# concrete Boolean input (elaborates against the rival, fails against the frozen
# solution). All inputs are concrete Bools, so `decide` discharges the negation.
# ---------------------------------------------------------------------------

# rival-write-then-exit: THE BUG ITSELF — the pre-change order. Emit output FIRST,
# then request the check-mode exit. In verification-only mode an emit-flag is set
# before the exit, so C2's emit-nothing conjuncts are violated while exitCode is
# still some 1. Ports nagini rival-write-then-exit (the G-DIFF defect). Witness at
# (hasChanges=true, checkOnly=true, mergeIntoLast=true): the merge writer runs, so
# wroteToLast = true where C2 demands false.
_RIVAL_WRITE_THEN_EXIT = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  if checkOnly then
    eff := { eff with exitCode := some 1 }
  return eff"""

# rival-check-returns-normally: omit the check-mode guard entirely — always
# dispatch a writer and complete normally, even in verification-only mode. Returns
# with exitCode = none in check mode. Ports nagini rival-check-returns-normally
# (control-flow-effect). Witness at (true, true, true): emits merged output and
# exitCode = none where C2 demands some 1 (and emit-nothing).
_RIVAL_CHECK_RETURNS = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""

# rival-skip-writer: raise correctly in check mode, but on the normal (not-check)
# path do NOTHING — never emit. Ports nagini rival-skip-writer (the GROWTH pin: an
# artefact must be produced on the normal path). Witness at (true, false, false):
# C3 requires wroteNew = true (fresh output) but the rival emits nothing.
_RIVAL_SKIP_WRITER = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  return eff"""

# rival-partial-domain: gate the check-mode exit on mergeIntoLast too
# (`if checkOnly && mergeIntoLast: exit`). Correct on (check & merge) and on every
# non-check input, but for (checkOnly=true, mergeIntoLast=false) it falls through,
# emits a fresh file and completes normally. Ports nagini
# rival-partial-domain-update-gated-exit. Witness at (true, true, false): the exact
# sub-domain where it returns exitCode = none and wroteNew = true, both violating C2.
_RIVAL_PARTIAL = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly && mergeIntoLast then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""

# rival-emit-without-changes: NO direct nagini counterpart — attacks C1 and the
# hasChanges binder, which no other rival varies. Ignores the no-changes guard and
# proceeds as if changes were present, emitting output when nothing was detected.
# Witness at (false, false, false): C1 demands wroteNew = false but the rival emits
# a fresh file. Without this rival the hasChanges binder would be held true by
# every reject witness — a binder no rival abuses.
_RIVAL_EMIT_NO_CHANGES = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""

# rival-swap-writers: NO direct nagini counterpart — attacks C3's writer SELECTION
# and the mergeIntoLast dependence at mergeIntoLast=true, distinct from
# rival-skip-writer's mergeIntoLast=false witness. On the normal path it picks the
# WRONG output form (merge writer when a fresh file is asked for and vice versa).
# Witness at (true, false, true): C3 requires wroteToLast = true ∧ wroteNew = false,
# but the rival swaps them.
_RIVAL_SWAP_WRITERS = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteNew := true }
  else
    eff := { eff with wroteToLast := true }
  return eff"""


# rival-emit-in-check-no-exit: the ported nagini `rival-no-raise-in-check`. Keeps a
# check-mode branch but EMITS a fresh migration there and completes normally
# instead of requesting the exit. Observably distinct from
# rival-check-returns-normally: at (true, true, true) this sets wroteNew while the
# guard-deleted rival sets wroteToLast, so the two break DIFFERENT C2 conjuncts.
# Witness at (true, true, true): C2 demands wroteNew = false ∧ exitCode = some 1,
# the rival gives wroteNew = true ∧ exitCode = none.
_RIVAL_EMIT_IN_CHECK = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    eff := { eff with wroteNew := true }
    return eff
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""

# rival-exit-without-changes: hoists the verification-only exit ABOVE the
# no-changes guard, so a verification-only run on a project with NOTHING pending
# still requests a non-zero exit. Attacks C1's exitCode conjunct, which NO other
# rival breaks (every other C1-side rival attacks an emit flag). Witness at
# (false, true, false): C1 demands exitCode = none, the rival gives some 1.
_RIVAL_EXIT_NO_CHANGES = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if checkOnly then
    return { eff with exitCode := some 1 }
  if !hasChanges then
    return eff
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""

# rival-exit-on-normal-path: emits the correct output form, but then ALSO requests
# a process exit on the ordinary (not verification-only) path. Attacks C3's
# exitCode = none conjunct, the last conjunct no other rival breaks: every other
# C3 rival attacks an emit flag and leaves the exit status agreeing with gold.
# Witness at (true, false, false): C3 demands exitCode = none, the rival gives
# some 0.
_RIVAL_EXIT_ON_NORMAL = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return eff
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return { eff with exitCode := some 0 }"""


# rival-merge-without-changes: emits MERGED output on the no-changes branch.
# Attacks (C1, wroteToLast) — the last of the 9 pinned conjuncts left unprobed
# after the previous revision (which nonetheless recorded all 9 as covered).
# rival-emit-without-changes breaks C1's OTHER emit flag (wroteNew) and
# rival-exit-without-changes breaks C1's exitCode, so nothing tested the pin that
# the no-changes branch must not merge into the latest migration either. Witness
# at (false, false, false): C1 demands wroteToLast = false, the rival gives true.
_RIVAL_MERGE_NO_CHANGES = """\
def implementation_processChanges
    (hasChanges checkOnly mergeIntoLast : Bool) : CommandEffect := Id.run do
  let mut eff : CommandEffect := { wroteToLast := false, wroteNew := false, exitCode := none }
  if !hasChanges then
    return { eff with wroteToLast := true }
  if checkOnly then
    return { eff with exitCode := some 1 }
  if mergeIntoLast then
    eff := { eff with wroteToLast := true }
  else
    eff := { eff with wroteNew := true }
  return eff"""


# --- ADMISSIBILITY. On this total carrier the obligation carries no precondition
# hypothesis, so the PRECOND-TOO-STRONG analogue is the obligation being
# UNSATISFIABLE at an F2P-shaped input: a spec whose three clauses could not be
# jointly discharged at the input the F2P test actually exercises would admit
# anything, since the frozen script would be closing a goal that reduces to
# `False`. This positive discharges the obligation AT that concrete input, by
# evaluation, as a `have` — then closes the frozen obligation verbatim. Only the
# proof region is touched; the impl stays the frozen one, which is the point: the
# case tests the SPEC's satisfiability at the F2P point, not any impl reshape.
# (true, true, false) is the F2P configuration: changes pending, verification-only
# mode, no merge requested — the run must request a non-zero exit and emit
# NOTHING. If the `have` cannot be closed by evaluation the spec is unsatisfiable
# exactly where the bug lives => PRECOND-TOO-STRONG / vacuous obligation.
_PROOF_ADMISS = """\
  have _ground : problem_spec_processChanges true true false
      (implementation_processChanges true true false) := by
    unfold problem_spec_processChanges implementation_processChanges
    decide
""" + _PROOF_OLD


# --- Witness helper. Each reject case states the spec predicate directly at a
# concrete, `decide`-able Boolean triple; the negation elaborates iff the rival's
# output contradicts the spec there. Checked in a file with the frozen obligation
# removed, so no tactic script can interfere.
def _witness(args):
    return f"""\
example : ¬ problem_spec_processChanges {args}
    (implementation_processChanges {args}) := by
  unfold problem_spec_processChanges implementation_processChanges
  decide"""


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder-writers",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but behaviourally-identical impl: the "
            "check-mode exit stays FIRST, the writer dispatch is rewritten in the "
            "opposite branch order (test `!mergeIntoLast` first). Both output "
            "forms satisfy the same C3 conjuncts, so C1/C2/C3 still hold. The "
            "frozen `cases … <;> simp` proof closes unchanged because each leaf "
            "reduces to the same CommandEffect. If it fails => SPEC-TOO-STRONG "
            "(over-fit to one writer-branch order)."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE),
        "rationale": (
            "the same decision as a pure functional `if/else if/else` (no Id.run / "
            "no `let mut`), the block structure the underlying branch actually "
            "has. Result is definitionally the spec RHS on every leaf, so the "
            "frozen case-split + simp proof still closes. Confirms the spec does "
            "not secretly depend on the imperative encoding. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-boolean-algebra",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_BOOL_ALGEBRA),
        "rationale": (
            "branchless reshape: every output field is one Boolean / Option "
            "expression over the three inputs, so the impl shares NO control-flow "
            "structure with the frozen one — unlike the two positives above, "
            "whose arms are still the frozen guards in the frozen order. Computes "
            "the same function on all 8 inputs, and closes under the FROZEN proof "
            "tactic unchanged. The strongest soundness probe available here: if it "
            "failed, the spec would be admitting only the guard-shaped encoding "
            "rather than the behaviour => SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_OLD, _PROOF_ADMISS),
        "rationale": (
            "the obligation is DISCHARGED at the F2P-shaped input "
            "(hasChanges=true, checkOnly=true, mergeIntoLast=false — changes "
            "pending, verification-only mode, no merge requested) by evaluation "
            "as a `have`, before the frozen obligation is closed verbatim. On a "
            "total carrier with no precondition hypothesis, this is the "
            "PRECOND-TOO-STRONG analogue: what could go wrong is not an "
            "unsatisfiable Requires but an obligation that is UNSATISFIABLE at "
            "exactly the input the F2P test exercises, which would let the frozen "
            "script close a goal reducing to `False` and admit anything. The impl "
            "is the frozen one unchanged — deliberately, since the claim under "
            "test is the spec's joint satisfiability at that point, not an impl "
            "reshape. If the `have` cannot be closed by evaluation => the three "
            "clauses conflict where the change lives and the whole obligation is "
            "vacuous."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "rival-write-then-exit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_WRITE_THEN_EXIT),
        "witness": _witness("true true true"),
        "refinement": (
            "this is the PRE-CHANGE order verbatim (emit output first, request the "
            "check-mode exit after). Its faithful real patch is the unchanged "
            "pre-change command, which in verification-only mode writes the "
            "migration output and THEN exits non-zero. That is precisely what the "
            "F2P test asserts against: it requires that after a verification-only "
            "run raises, the migration module directory does NOT exist (no output "
            "was produced). The pre-change order leaves output on disk, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "the DISCRIMINATING bug this change fixes. Rejection source: C2's "
            "emit-nothing conjunct — a writer ran before the exit so wroteToLast = "
            "true where C2 demands false (exitCode is still some 1). Witness at "
            "(hasChanges=true, checkOnly=true, mergeIntoLast=true). If it verified "
            "=> SPEC-TOO-WEAK (admits the very bug)."
        ),
    },
    {
        "id": "rival-check-returns-normally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_CHECK_RETURNS),
        "witness": _witness("true true true"),
        "refinement": (
            "omits the check-mode guard entirely: ALWAYS emits output and "
            "completes normally, even in verification-only mode. A faithful real "
            "patch with the check-mode exit deleted would make a verification-only "
            "run emit migrations and exit 0 even when migrations are missing — the "
            "F2P test requires a non-zero exit (SystemExit) on pending changes, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "control-flow-effect rival: completes normally in check mode. "
            "Rejection source: C2's exitCode = some 1 conjunct — with the guard "
            "gone the run emits merged output and exitCode = none. Witness at "
            "(true, true, true): both the exitCode and emit-nothing conjuncts of "
            "C2 fail. If it verified => SPEC-TOO-WEAK (raise-vs-return "
            "unconstrained)."
        ),
    },
    {
        "id": "rival-skip-writer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_SKIP_WRITER),
        "witness": _witness("true false false"),
        "refinement": (
            "exits correctly in check mode but on the normal (not-check) path does "
            "NOTHING — never emits. A faithful real patch that skipped the writer "
            "dispatch would make an ordinary run produce no migration output, "
            "failing the P2P behaviour that the command must actually write "
            "migrations — would NOT resolve."
        ),
        "rationale": (
            "the normal-return path must emit output. Rejection source: C3 — with "
            "no writer run, wroteNew = false where (mergeIntoLast=false) demands "
            "true. Witness at (true, false, false). If it verified => "
            "SPEC-TOO-WEAK (output-production on the normal path not enforced)."
        ),
    },
    {
        "id": "rival-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_PARTIAL),
        "witness": _witness("true true false"),
        "refinement": (
            "gates the check-mode exit on mergeIntoLast too (exit only when BOTH "
            "checkOnly and mergeIntoLast). Correct on (check & merge) and every "
            "non-check input, but for (checkOnly=true, mergeIntoLast=false) it "
            "falls through, emits a fresh file and completes normally — i.e. a "
            "verification-only run without merge mode writes a file and exits 0. "
            "That is the pre-change bug on the fresh-output sub-domain (the exact "
            "F2P configuration), so it would NOT resolve."
        ),
        "rationale": (
            "partial-domain rival: correct on most of the flag domain, wrong on "
            "the (check, not-merge) sub-domain. Rejection source: C2 — for "
            "(true, true, false) the rival emits (wroteNew = true) and completes "
            "normally (exitCode = none), violating both C2 conjuncts. Witness at "
            "(true, true, false) — the sub-domain where partial gating breaks, "
            "distinct from the (…, true) inputs the other check-mode rivals probe. "
            "If it verified => SPEC-TOO-WEAK (domain-incomplete check-mode exit)."
        ),
    },
    {
        "id": "rival-emit-without-changes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_EMIT_NO_CHANGES),
        "witness": _witness("false false false"),
        "refinement": (
            "NO direct nagini counterpart — attacks the no-changes branch. Drops "
            "the no-changes guard and proceeds as if changes were present. A real "
            "patch that emitted output when the autodetector reported NO changes "
            "would write a spurious migration on a clean project, failing the "
            "unchanged 'no changes detected' behaviour (P2P) — would NOT resolve."
        ),
        "rationale": (
            "rejection source: C1 — for hasChanges = false the run must emit "
            "nothing (wroteToLast = false ∧ wroteNew = false), but the rival emits "
            "a fresh file (wroteNew = true). Witness at (false, false, false) — the "
            "only reject witness holding hasChanges = false, so this binder is "
            "abused by a rival. If it verified => SPEC-TOO-WEAK on the no-changes "
            "branch."
        ),
    },
    {
        "id": "rival-swap-writers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_SWAP_WRITERS),
        "witness": _witness("true false true"),
        "refinement": (
            "NO direct nagini counterpart — attacks the writer SELECTION on the "
            "normal path. Emits the WRONG output form (merges into the latest "
            "migration when a fresh file is requested, and vice versa). A real "
            "patch that inverted the merge/fresh dispatch would emit the wrong "
            "kind of migration output, failing the P2P tests that pin which form "
            "is produced (e.g. the --update merge behaviour) — would NOT resolve."
        ),
        "rationale": (
            "rejection source: C3's writer-selection conjuncts — for "
            "(hasChanges=true, checkOnly=false, mergeIntoLast=true) C3 requires "
            "wroteToLast = true ∧ wroteNew = false, but the rival swaps them. "
            "Witness at (true, false, true): exercises the mergeIntoLast = true "
            "leg of C3, distinct from rival-skip-writer's mergeIntoLast = false "
            "witness, so the mergeIntoLast binder is abused on both values. If it "
            "verified => SPEC-TOO-WEAK on writer selection."
        ),
    },
    {
        "id": "rival-emit-in-check-no-exit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_EMIT_IN_CHECK),
        "witness": _witness("true true true"),
        "refinement": (
            "the ported nagini `rival-no-raise-in-check`. Keeps a "
            "verification-only branch but EMITS a fresh migration there and "
            "completes normally instead of requesting the exit. A faithful real "
            "patch of this shape would make a verification-only run both leave "
            "migration output on disk AND report success: it fails the F2P "
            "requirement of a non-zero exit on pending changes, and also the F2P "
            "requirement that no migration output survives the run — would NOT "
            "resolve."
        ),
        "rationale": (
            "rejection source: C2 — at (true, true, true) the rival gives "
            "wroteNew = true where C2 demands false and exitCode = none where C2 "
            "demands some 1. Distinct from rival-check-returns-normally at the "
            "SAME input: that rival dispatches by mergeIntoLast and so breaks the "
            "wroteToLast conjunct, this one breaks the wroteNew conjunct, so the "
            "two emit flags of C2 are each attacked by some rival. If it verified "
            "=> SPEC-TOO-WEAK (emitting the wrong form before completing normally "
            "in verification-only mode is admitted)."
        ),
    },
    {
        "id": "rival-merge-without-changes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_MERGE_NO_CHANGES),
        "witness": _witness("false false false"),
        "refinement": (
            "emits MERGED output on the no-changes branch: a run that detects "
            "nothing pending still merges into the latest existing migration. A "
            "real patch of this shape would rewrite an already-committed "
            "migration on a project whose models are fully migrated — the "
            "unchanged 'no changes detected' behaviour (emit nothing, complete "
            "normally) is asserted by the surrounding P2P suite, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "rejection source: C1's wroteToLast conjunct — for hasChanges = false "
            "the run must emit nothing, but the rival merges into the latest "
            "migration. This is the LAST of the 9 pinned conjuncts to be "
            "attacked: rival-emit-without-changes breaks C1's other emit flag "
            "(wroteNew) and rival-exit-without-changes breaks C1's exitCode, so "
            "before this case the no-changes merge pin was recorded as covered "
            "while no witness touched it. Witness at (false, false, false). If it "
            "verified => SPEC-TOO-WEAK (the no-changes branch would constrain the "
            "fresh-output flag but not the merge one)."
        ),
    },
    {
        "id": "rival-exit-without-changes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_EXIT_NO_CHANGES),
        "witness": _witness("false true false"),
        "refinement": (
            "hoists the verification-only exit ABOVE the no-changes guard, so a "
            "verification-only run on a project with nothing pending still "
            "requests a non-zero exit. A real patch of this shape would make a "
            "verification-only run fail on a project whose models are fully "
            "migrated — the unchanged behaviour that such a run completes "
            "successfully when no changes are detected is asserted by the "
            "surrounding P2P suite, so it would NOT resolve."
        ),
        "rationale": (
            "rejection source: C1's exitCode conjunct — for hasChanges = false the "
            "run must complete normally (exitCode = none), but the rival requests "
            "some 1. This is the ONLY rival that breaks C1's exit conjunct: every "
            "other no-changes-side rival attacks an emit flag and leaves the exit "
            "status agreeing with the frozen impl. Witness at (false, true, "
            "false). If it verified => SPEC-TOO-WEAK (the no-changes branch would "
            "constrain only what is emitted, not whether the run succeeds)."
        ),
    },
    {
        "id": "rival-exit-on-normal-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_EXIT_ON_NORMAL),
        "witness": _witness("true false false"),
        "refinement": (
            "emits the correct output form on the ordinary path, but then ALSO "
            "requests a process exit. A real patch of this shape would make an "
            "ordinary run terminate via an exit request after writing its "
            "migrations rather than returning to its caller; the P2P suite calls "
            "the command in-process and asserts it returns normally, so an exit "
            "request would surface as a raised SystemExit and it would NOT "
            "resolve."
        ),
        "rationale": (
            "rejection source: C3's exitCode = none conjunct — the last conjunct "
            "no other rival breaks: every other C3 rival attacks an emit flag and "
            "leaves the exit status matching gold. Pins that the ordinary path "
            "must complete normally, not merely emit the right thing. Witness at "
            "(true, false, false): C3 demands exitCode = none, the rival gives "
            "some 0. If it verified => SPEC-TOO-WEAK (a run could emit correctly "
            "and still refuse to complete normally)."
        ),
    },
]

# Conjunct coverage after this battery (3 clauses x 3 pinned fields = 9): every
# one of the 9 is broken at the WITNESS POINT of at least one reject case above.
# Derived by computing, for each rival, the full 8-input truth table and the
# conjunct set that actually fails at its own witness input — not by reading the
# rationales, which is how the two errors below survived a revision each:
#   * (C1, exitCode) and (C3, exitCode) were once unattacked; closed by
#     rival-exit-without-changes and rival-exit-on-normal-path.
#   * (C1, wroteToLast) was then STILL unattacked while this comment claimed all
#     nine were covered. Every hasChanges=false rival either set wroteNew or
#     touched only exitCode, so the merge-emit pin on the no-changes branch was
#     asserted and never probed. Closed by rival-merge-without-changes, whose
#     witness input (false, false, false) breaks exactly (C1, wroteToLast).
# The claim above is a checkable one: it holds iff the union of the
# conjunct-sets-broken-at-witness-point over the nine reject cases is all 9.

# No @ContractOnly axioms and no opaque callee on this path (meta.axioms == []).
# Only the observable "which output form ran / what exit was requested" matters;
# it is modeled directly by the impl's control flow, so there is no callee for the
# axiom lane to execute.
AXIOM_TESTS = []

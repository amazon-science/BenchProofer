# properties.py — G-PBT falsification battery for django__django-13410 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive would reprove, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json). Two modeled
# functions turn a lower-level primitive's two-channel result (`outcome`) into a
# boolean status, each pinned by one postcondition GROUNDED in the argument:
#
#   acquire (outcome : Outcome) : Except FlockErr Bool
#     result = (match outcome with
#               | .ok _              => .ok true       <-- a completed operation is
#                                                          reported as success
#               | .error .wouldBlock => .ok false      <-- a not-granted-right-now
#                                                          non-blocking request is
#                                                          reported as failure
#               | .error (.other c)  => .error (.other c))  <-- any OTHER out-of-band
#                                                          signal is PROPAGATED unchanged
#
#   release (outcome : Outcome) : Except FlockErr Bool
#     result = outcome.map (fun _ => true)             <-- a completed operation is
#                                                          reported as success; an
#                                                          out-of-band signal is
#                                                          propagated unchanged
#
# CARRIER NOTE. The nagini sibling abstracted the same decision behind a plain
# boolean plus an unforgeable capability token (lock_held / lock_freed) minted only
# by actually invoking the primitive fcntl.flock, and grounded acquire on
# Result()==available / release on Result() is True. This backend does NOT model the
# primitive's side-effect at all: its result is the pure `outcome` argument, and the
# only logic modeled is the pure two-channel→bool transformation. So the two carriers
# defend the SAME F2P behaviour by different means — see the lane notes below for
# which nagini cases port, which are vacuous here, and why.
#
# The oracle is a total, transparent match/`Except.map` over the input (no opaque
# callee, no answer-key), so a witness can state its refutation at any literal input;
# no conditioning on the carrier is needed.
#
# WITNESS DISCIPLINE — why the witnesses refute through the HYPOTHESIS (`intro h; unfold
# problem_spec_… at h; cases h`) rather than by computing the impl with `simp`. The two
# impl SHAPES available on this carrier are not equally reducible by `simp`: a direct
# `match` normalises, but the imperative `do`/`try`/`catch` skeleton elaborates through
# `tryCatch`/`DoResultPR` and `simp` does NOT see through it — it leaves the goal
# untouched. A witness of the form `unfold …; simp` therefore ELABORATES against a
# match-shaped rival and FAILS against a do-shaped impl for a reason that has nothing to
# do with behaviour, which makes it a discriminator of syntactic FORM rather than of the
# spec. Measured on this bundle: a `unfold …; simp` acquire witness at `.ok ()` failed to
# refute a rival that is genuinely WRONG at `.ok ()` (reports a completed acquisition as
# failure) but written in the frozen do/try/catch shape — the goal came back unreduced,
# exit 1, exactly as it does on gold. That witness would have attested to a reshape, not
# to the spec.
#   The form used below is shape-INDEPENDENT: `cases h` refutes the equation the spec
# ASSERTS by constructor clash on the spec's own right-hand side, so it never needs to
# reduce the impl at all. Re-derived on every rival, on gold, on both positives, and on
# do-shaped WRONG confounders for all five channels — it elaborates against every wrong
# impl in EITHER shape and fails on gold/the positives with a semantic `⊢ False`
# (constructor clash / `case refl`), never an unfolding failure or an unknown identifier.
#
# ADMISSIBILITY, ON A TOTAL CARRIER (nagini case 3). This lane is NOT vacuous here and
# is carried below as `admiss-ground-f2p-channels`. The tempting reason to drop it —
# "the frozen obligation has no precondition hypothesis, so nothing can be
# PRECOND-TOO-STRONG" — is the wrong test. The analogue of an over-strong precondition
# on a total carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input: the `∀ outcome` obligation could be closed for a reason that never actually
# holds at the concrete channels the F2P tests drive, and a battery of pure negatives
# plus whole-domain positives would not notice. So the case discharges the spec at each
# concrete F2P channel BY EVALUATION, as a `have` prepended to the frozen tactic body,
# before closing the frozen obligation verbatim. Measured load-bearing: the same shape
# with the ground instance asserting the WRONG status at the completion channel FAILS
# (`Tactic 'rfl' failed: Except.ok false is not definitionally equal to …`), so the
# `have` is kernel-evaluated rather than decorative.
#
# LANES THAT DO NOT PORT (each a deliberate, documented omission — see 'assessment'):
#   * CONTROL-FLOW-EFFECT / capability-token (nagini cases 4-5, the acquire/release
#     "no-op that never invokes the primitive" rivals). Nagini closed the value flank
#     with an unforgeable lock_held()/lock_freed() token whose sole producer is the
#     real primitive. This backend is referentially transparent and does NOT model
#     the primitive as a side-effecting callee: `implementation_acquire` /
#     `implementation_release` are TOTAL pure functions of `outcome` (the primitive's
#     already-observed result). There is no side-effect to bypass and no token to
#     forge, so the class is VACUOUS here — not fabricated a substitute. (VACUOUS.)
#     NUANCE (audited): what does port is the no-op rivals' VALUE shape, and it is
#     already carried. Nagini's release no-op is literally `return True`, which is
#     `weak-swallow-error-release` here (`.ok true` on every channel) — rejected, with a
#     rebuilt witness. Nagini's acquire no-op echoes the argument; the closest value-level
#     analogue on this carrier is an impl that ignores a channel distinction, which
#     `weak-contention-blind-acquire` and `weak-overhandled-acquire` cover at the two
#     error channels. So only the unforgeable-TOKEN mechanism is vacuous, not the
#     behaviour those cases were pointing at.
#   * FRAME-MUTATION. Nagini itself marks this N/A (acquire takes a plain bool, release
#     takes no inputs — no half-permission input to over-write). Vacuous here too.
#   * DIVERGENCE / non-termination. On lean `implementation_*` is a TOTAL Lean `def`;
#     a diverging implementation cannot be written at all, so the class is genuinely
#     VACUOUS (contrast velvet's `partial` semantics, where it is a known spec hole).
#     The nagini sibling carries no diverge-* case anyway.
#   * AXIOM_TESTS. No UNCHANGED callee is consumed as an opaque axiom (the primitive
#     is abstracted as `outcome`, not axiomatized); mapping.md records axioms=[]. The
#     axiom lane is G-AX's job and this gate ignores it regardless.
from pathlib import Path

INSTANCE = "django__django-13410"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl-region bodies (the full `def` between an impl-start / impl-end pair).
# Editing only inside one of these keeps the spec view — hence same_spec — byte
# identical. Each block is UNIQUE in _BASE so _swap targets it unambiguously. The
# frozen proof bodies are NOT touched (the positive reshapes below happen to close
# under the frozen proof scripts, so the proof region also stays byte-identical).
# ---------------------------------------------------------------------------

_ACQ_GOLD = """def implementation_acquire (outcome : Outcome) : Except FlockErr Bool := do
  try
    let _ ← outcome
    return true
  catch e =>
    match e with
    | .wouldBlock => return false
    | .other c    => throw (.other c)"""

_REL_GOLD = """def implementation_release (outcome : Outcome) : Except FlockErr Bool := do
  let _ ← outcome
  return true"""

assert _BASE.count(_ACQ_GOLD) == 1, "anchor drift: acquire gold impl not found verbatim"
assert _BASE.count(_REL_GOLD) == 1, "anchor drift: release gold impl not found verbatim"

# The head of each frozen PROOF body. The admissibility case below prepends a ground
# `have` here, leaving the frozen `theorem correct_…` STATEMENT byte-identical and the
# frozen tactic script intact after it (only the tactic body may differ, per
# variant_scope; the statement may not).
_ACQ_PROOF_INTRO = """  intro outcome
  match outcome with"""

_REL_PROOF_INTRO = """  intro outcome
  rcases outcome with u | e <;> rfl"""

assert _BASE.count(_ACQ_PROOF_INTRO) == 1, "anchor drift: acquire proof intro"
assert _BASE.count(_REL_PROOF_INTRO) == 1, "anchor drift: release proof intro"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-acquire-match: acquire reshaped from the imperative do/try/catch skeleton into a
# single direct `match` expression over `outcome` — structurally DIFFERENT but
# behaviourally identical (the two shapes agree on every channel). This is the shape a
# faithful patch could equally take. The frozen `theorem correct_acquire` statement is
# kept byte-identical and its match-per-channel `rfl` proof body still closes for the
# reshaped impl (no new axiom/lemma/sorry, no proof weakening). If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to the do-notation branch form).
_ACQ_POS = """def implementation_acquire (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _              => .ok true
  | .error .wouldBlock => .ok false
  | .error (.other c)  => .error (.other c)"""

# pos-release-match: release reshaped from the do-bind skeleton into an explicit
# `match` that preserves the error channel and maps a completion to `.ok true` — the
# cheapest HONEST correct impl (it IS `outcome.map (fun _ => true)` written out). The
# frozen `rcases … <;> rfl` proof body still closes. Must verify, else SPEC-TOO-STRONG
# on release.
_REL_POS = """def implementation_release (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _     => .ok true
  | .error e  => .error e"""


# ===========================================================================
# ADMISSIBILITY — must VERIFY (else the obligation is unsatisfiable at an
# F2P-shaped input, this carrier's analogue of PRECOND-TOO-STRONG).
# ===========================================================================

# admiss-ground-f2p-channels: discharge the acquire obligation AT THE CONCRETE CHANNELS
# the F2P tests drive, by evaluation, before closing the frozen `∀ outcome` obligation
# verbatim. Both `have`s are GROUND instances (no binder, no hypothesis): the completion
# channel — the status a caller reads when the operation was carried out — and the
# not-granted-right-now channel, which is the pair the F2P assertions exercise. The
# frozen statement is untouched and the frozen match-per-channel script still runs after
# the `have`s. If either ground instance did NOT hold, the whole-domain obligation would
# be closing for a reason that fails at exactly the inputs the tests use.
_ACQ_ADMISS = """  have _f2p_completed : problem_spec_acquire (Except.ok ())
      (implementation_acquire (Except.ok ())) := by
    unfold problem_spec_acquire
    rfl
  have _f2p_contended : problem_spec_acquire (Except.error FlockErr.wouldBlock)
      (implementation_acquire (Except.error FlockErr.wouldBlock)) := by
    unfold problem_spec_acquire
    rfl
  intro outcome
  match outcome with"""

# The release sibling: the completion channel is the only one the F2P tests drive for a
# release (it does not block and is asserted to report success).
_REL_ADMISS = """  have _f2p_released : problem_spec_release (Except.ok ())
      (implementation_release (Except.ok ())) := by
    unfold problem_spec_release
    rfl
  intro outcome
  rcases outcome with u | e <;> rfl"""


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# elaborates against the rival and FAILS on the frozen solution. Every rival attacks
# an F2P-OBSERVABLE clause (so a verifying rival would be a true
# verify-does-not-imply-resolve break, not merely a stronger-than-F2P artifact).
# ===========================================================================

# always-false-acquire: the headline pre-patch bug (Solution_prepatch_1.lean). The
# pre-patch read `ret == 0` off the discarded return value; the primitive reports a
# completion through the no-value channel (never the integer 0), so a completed
# acquisition was ALWAYS reported as failure. Modelled as the constant `.ok false` on
# the completion channel (error channels unchanged, so it is wrong ONLY at `.ok`).
_ACQ_ALWAYS_FALSE = """def implementation_acquire (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _              => .ok false
  | .error .wouldBlock => .ok false
  | .error (.other c)  => .error (.other c)"""

# contention-blind-acquire: reports a not-granted-right-now non-blocking request as
# SUCCESS (`.ok true` on the wouldBlock channel). This is the exact defect the issue
# names — a non-blocking caller cannot tell it FAILED to acquire the lock. Wrong ONLY
# at `.error .wouldBlock` (completion + other channels unchanged), so its witness
# probes the wouldBlock channel of the binder.
_ACQ_CONTENTION_BLIND = """def implementation_acquire (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _              => .ok true
  | .error .wouldBlock => .ok true
  | .error (.other c)  => .error (.other c)"""

# inverted-acquire: swaps the two status channels — a completion reported as failure
# and a not-granted request reported as success. The inverse of the faithful
# translation; wrong on BOTH the completion and the wouldBlock channels.
_ACQ_INVERT = """def implementation_acquire (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _              => .ok false
  | .error .wouldBlock => .ok true
  | .error (.other c)  => .error (.other c)"""

# overhandled-acquire: turns an out-of-band signal that is NOT the not-granted-right-now
# one into a `.ok false` status instead of propagating it. This is the ONLY acquire channel
# no other rival varies (always-false / contention-blind / inverted all leave `.error
# (.other c)` at gold), and it is the channel the spec's third clause exists for: the
# operation handles ONLY the not-granted signal, and turning every other failure into a
# plain "did not get the lock" status hides a genuine error from the caller. Wrong ONLY at
# `.error (.other c)`.
_ACQ_OVERHANDLE = """def implementation_acquire (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _              => .ok true
  | .error .wouldBlock => .ok false
  | .error (.other _)  => .ok false"""

# always-false-release: the pre-patch release bug (Solution_prepatch_2.lean). `ret == 0`
# is always the failure verdict because a completed release reports through the
# no-value channel, so a successful release was reported as failure. Modelled as
# `.ok false` on the completion channel (error channel preserved).
_REL_ALWAYS_FALSE = """def implementation_release (outcome : Outcome) : Except FlockErr Bool :=
  match outcome with
  | .ok _    => .ok false
  | .error e => .error e"""

# swallow-error-release: collapses the error channel — reports `.ok true` on EVERY
# input, discarding an out-of-band signal instead of propagating it. Wrong ONLY on the
# `.error _` sub-domain of the binder (the completion channel is unchanged), so it is
# the rival that varies the release binder to a second distinct point. NOTE (honest
# framing, see refinement): this attacks a MODELED clause (release's error-propagation)
# that is spec-strengthening beyond the F2P-observable behaviour.
_REL_SWALLOW_ERR = """def implementation_release (outcome : Outcome) : Except FlockErr Bool :=
  .ok true"""


def _wit(fn, inp, note):
    """A SHAPE-INDEPENDENT refutation witness at a concrete literal input `inp`.

    Refutes through the hypothesis rather than by computing the impl: assume the spec
    holds at `inp` (`intro h`), unfold ONLY the spec predicate (never the impl), and let
    `cases h` derive `False` from the constructor clash between the two sides of the
    equation the spec asserts. Because the impl is never reduced, the witness is blind to
    whether the impl is written as a direct `match` or as the imperative `do`/`try`/`catch`
    skeleton — see WITNESS DISCIPLINE in the header for the measurement showing why a
    `simp`-over-the-impl witness discriminates FORM instead of behaviour here.

    Elaborates against any rival whose verdict at `inp` differs from the frozen one, in
    either shape; fails on gold and on the correct reshapes with a semantic `⊢ False`.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_{fn} ({inp})\n"
        f"    (implementation_{fn} ({inp})) := by\n"
        f"  intro h\n"
        f"  unfold problem_spec_{fn} at h\n"
        f"  cases h"
    )


def _wit_acq(inp, note):
    return _wit("acquire", inp, note)


def _wit_rel(inp, note):
    return _wit("release", inp, note)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-acquire-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_POS),
        "rationale": (
            "structurally-different but CORRECT acquire: the imperative do/try/catch "
            "skeleton is reshaped into a single direct `match` over the binder, "
            "agreeing with gold on every channel (.ok/.wouldBlock/.other). Only the "
            "branch FORM changes — the shape a faithful patch could equally take. The "
            "frozen `theorem correct_acquire` STATEMENT is kept byte-identical and its "
            "match-per-channel `rfl` proof body still closes (no new axiom/lemma/sorry). "
            "If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to the do-notation "
            "branch form)."
        ),
    },
    {
        "id": "pos-release-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _REL_GOLD, _REL_POS),
        "rationale": (
            "release reshaped from the do-bind skeleton into an explicit `match` that "
            "preserves the error channel and maps a completion to `.ok true` — the "
            "honest cheapest CORRECT impl (it is `outcome.map (fun _ => true)` written "
            "out). The frozen `rcases … <;> rfl` proof body still closes. Must verify, "
            "else SPEC-TOO-STRONG on release."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-f2p-channels",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _ACQ_PROOF_INTRO, _ACQ_ADMISS),
        "rationale": (
            "ADMISSIBILITY on a TOTAL carrier. The frozen obligation is `∀ (outcome : "
            "Outcome), problem_spec_acquire outcome (implementation_acquire outcome)` "
            "with no precondition hypothesis, so the classical PRECOND-TOO-STRONG shape "
            "cannot arise — but the analogue here can: the whole-domain obligation could "
            "be closing for a reason that does NOT hold at the concrete channels the "
            "F2P assertions actually drive. This case discharges the spec BY EVALUATION "
            "at both of those channels — a completed operation and a not-granted "
            "non-blocking request — as ground `have`s (no binder, no hypothesis, so "
            "nothing is assumed) prepended to the frozen tactic body, then closes the "
            "frozen obligation verbatim. The `theorem correct_acquire` STATEMENT is "
            "byte-identical and no new axiom/lemma/sorry appears. Load-bearing, not "
            "decorative: the same shape with the ground instance asserting the WRONG "
            "status at the completion channel FAILS to build (`Tactic 'rfl' failed`), so "
            "the kernel really evaluates these. If this case FAILED, the obligation "
            "would be unsatisfiable at an F2P-shaped input."
        ),
    },
    {
        "id": "admiss-ground-release-channel",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _REL_PROOF_INTRO, _REL_ADMISS),
        "rationale": (
            "The release sibling of the above. Discharges `problem_spec_release` BY "
            "EVALUATION at the completion channel — the one channel the F2P assertions "
            "drive for a release, which does not block and is asserted to report success "
            "— as a ground `have` before closing the frozen `rcases … <;> rfl` obligation "
            "verbatim. Statement byte-identical, no new assumption-bearing declaration. "
            "Confirms the release obligation is satisfiable at exactly the concrete input "
            "the tests use, rather than only in the aggregate over the binder."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-always-false-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_ALWAYS_FALSE),
        "refinement": (
            "This IS the pre-patch behaviour (Solution_prepatch_1.lean): reading the "
            "verdict off the discarded return value always yields the failure branch "
            "because a completed operation is reported through the no-value channel, "
            "never the compared code. A helper that reports every completed acquisition "
            "as failure fails the F2P success assertion — test_exclusive_lock asserts "
            "the completion is reported as True (assertIs(lock(f1, LOCK_EX), True)); a "
            "constant-failure helper reports False and does NOT resolve. So a verifying "
            "rival here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the acquire postcondition, which pins the completion channel "
            "to `.ok true`; the rival returns `.ok false` there, so the equality fails. "
            "Attacks the `.ok _ => .ok true` clause / the `.ok ()` sub-domain of the "
            "binder `outcome`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # .ok (): gold => .ok true, rival => .ok false.
        "witness": _wit_acq(
            "Except.ok ()",
            "completed operation: gold reports success, rival reports failure"),
    },
    {
        "id": "weak-contention-blind-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_CONTENTION_BLIND),
        "refinement": (
            "Reporting a not-granted-right-now non-blocking request as SUCCESS is the "
            "exact defect the issue names: a non-blocking caller can no longer tell it "
            "FAILED to acquire the lock. test_exclusive_lock asserts a contended "
            "non-blocking request is reported as False (assertIs(lock(f2, LOCK_EX | "
            "LOCK_NB), False)); a helper that reports it True FAILS that assertion and "
            "does NOT resolve — a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the acquire postcondition, which pins the not-granted channel "
            "to `.ok false`; the rival returns `.ok true` there. Attacks the "
            "`.error .wouldBlock => .ok false` clause / the `.error .wouldBlock` "
            "sub-domain of the binder `outcome` — the second distinct binder value the "
            "battery probes. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # .error .wouldBlock: gold => .ok false, rival => .ok true.
        "witness": _wit_acq(
            "Except.error FlockErr.wouldBlock",
            "not-granted non-blocking request: gold reports failure, rival reports success"),
    },
    {
        "id": "weak-inverted-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_INVERT),
        "refinement": (
            "Swapping the two status channels (completion -> False, not-granted -> True) "
            "inverts the contract the issue demands: a completion must never be reported "
            "as failure, and a contended request must never be reported as success. "
            "test_exclusive_lock asserts BOTH the completion=True and the "
            "contention=False directions; an inverted helper fails both and does NOT "
            "resolve — a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the acquire postcondition on the completion channel: gold pins "
            "`.ok true`, the inverted rival returns `.ok false`. Attacks the "
            "`.ok _ => .ok true` clause (a distinct rival SHAPE from always-false — it "
            "additionally mishandles the wouldBlock channel). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # .ok (): gold => .ok true, inverted rival => .ok false.
        "witness": _wit_acq(
            "Except.ok ()",
            "completed operation: gold reports success, inverted rival reports failure"),
    },
    {
        "id": "weak-overhandled-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_OVERHANDLE),
        "refinement": (
            "Varies the ONE acquire channel no other rival touches: the propagation of an "
            "out-of-band signal that is NOT the not-granted-right-now one. The operation is "
            "specified to handle only the not-granted signal and to propagate every other "
            "failure unchanged; this rival converts them all into a plain `.ok false`. "
            "HONEST SCOPE: like the release error-propagation guard, this clause is "
            "spec-strengthening beyond what the F2P tests observe — those tests exercise "
            "only a completion and a genuine contention, so a helper that also absorbed "
            "unrelated failures would still pass them. It is a spec-fidelity guard "
            "(spec_guide §5): the modeled behaviour distinguishes the handled signal from "
            "the propagated ones, and a rival that collapses that distinction must be "
            "rejected or the third clause of the acquire postcondition is hollow. Reporting "
            "an unrelated failure as an ordinary 'lock not acquired' would also hide a real "
            "fault from the caller rather than surfacing it."
        ),
        "rationale": (
            "REJECTED by the acquire postcondition's third clause, which pins "
            "`.error (.other c)` to `.error (.other c)` (propagated); the rival returns "
            "`.ok false` on that channel. Attacks the `.error (.other c)` sub-domain of the "
            "binder `outcome` — a THIRD distinct binder point, which no other acquire rival "
            "probes. If it VERIFIES => SPEC-TOO-WEAK (the propagation clause unenforced)."
        ),
        # .error (.other 9): gold => .error (.other 9), rival => .ok false.
        "witness": _wit_acq(
            "Except.error (FlockErr.other 9)",
            "unrelated out-of-band signal: gold propagates it, rival reports it as an "
            "ordinary not-acquired status"),
    },
    {
        "id": "weak-always-false-release",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_ALWAYS_FALSE),
        "refinement": (
            "This IS the pre-patch release behaviour (Solution_prepatch_2.lean): the "
            "verdict off the discarded return value always yields failure, so a "
            "completed release was reported as failure. test_exclusive_lock / "
            "test_shared_lock assert the release is reported as True (assertIs("
            "unlock(f1), True)); a constant-failure release FAILS that assertion and "
            "does NOT resolve — a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the release postcondition `result = outcome.map (fun _ => true)`, "
            "which pins a completion to `.ok true`; the rival returns `.ok false` there. "
            "Attacks the completion clause of release / the `.ok ()` sub-domain of the "
            "binder `outcome`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # .ok (): gold => .ok true, rival => .ok false.
        "witness": _wit_rel(
            "Except.ok ()",
            "completed release: gold reports success, rival reports failure"),
    },
    {
        "id": "weak-swallow-error-release",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_SWALLOW_ERR),
        "refinement": (
            "This rival varies the SECOND binder value of release (the error channel), "
            "which the always-false rival leaves at gold. HONEST SCOPE: the release "
            "error-propagation clause is a MODELED, spec-strengthening property — it "
            "mirrors gold's `unlock`, which has NO `except`, so any out-of-band signal "
            "propagates out unchanged. It is NOT F2P-observable: LOCK_UN does not block "
            "and never raises in the F2P tests, so a catch-all release that swallowed an "
            "error and returned True would still pass test_exclusive_lock / "
            "test_shared_lock. So this is NOT a verify-does-not-imply-resolve "
            "demonstrator; it is a spec-fidelity / frame-discipline guard (spec_guide "
            "§5): the spec pins the UNCHANGED error channel, and a rival that overwrites "
            "it with `.ok true` must be rejected or the propagation clause would be "
            "hollow. Included to exercise the release binder's error sub-domain, which "
            "no other release rival probes."
        ),
        "rationale": (
            "REJECTED by the release postcondition `result = outcome.map (fun _ => true)`, "
            "which pins `.error e` to `.error e` (propagated); the rival returns "
            "`.ok true` on that channel. Attacks the error-propagation clause of release "
            "/ the `.error .wouldBlock` sub-domain of the binder `outcome` — the second "
            "distinct release binder value the battery probes. If it VERIFIES => "
            "SPEC-TOO-WEAK (the propagation clause would be unenforced)."
        ),
        # .error .wouldBlock: gold => .error .wouldBlock, rival => .ok true.
        "witness": _wit_rel(
            "Except.error FlockErr.wouldBlock",
            "out-of-band signal on release: gold propagates it, rival swallows it as success"),
    },
]


# No @ContractOnly axioms and no opaque callees: the lower-level primitive is
# abstracted as the `outcome` argument (mapping.md: axioms=[], deep_model_references=[]),
# and the two-channel->bool transformation is modeled DEEPLY over the transparent
# `Except FlockErr _` carrier. The axiom lane is therefore vacuous here and belongs to
# G-AX regardless.
AXIOM_TESTS = []

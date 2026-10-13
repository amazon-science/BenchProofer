# properties.py — G-PBT falsification battery for django__django-15252 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl region
# — and, where a positive reproves, the proof body — differs), checked by
# variant_scope before the verifier runs. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the postcondition rather than
# to a tactic script that merely stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
# ---------------------------------------------------------------------------
#   implementation_provisionRecordsTable
#       (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome
#   theorem correct_provisionRecordsTable :
#       ∀ plannedOps tableExists, problem_spec_provisionRecordsTable …
#
# ONE obligation, NO precondition hypothesis, TWO input binders, and an `Outcome`
# with TWO observable components (`provisionedTable`, `state`). The postcondition is
# a total three-arm decision, each arm pinning BOTH components:
#
#   (A) plannedOps = some []  ∧ tableExists         ⇒ { false, continuationResult (some []) }
#   (B) plannedOps = some []  ∧ ¬tableExists        ⇒ { false, projectState false }
#   (C) plannedOps ≠ some []  (none, or non-empty)  ⇒ { true,  continuationResult plannedOps }
#
# Load-bearing content, clause by clause — this is the nagini argument re-expressed
# over this carrier:
#   * the `provisionedTable` component of (A)/(B) vs (C) is nagini's clause (1)
#     `schema_ensured == (not no_pending_records(pending))`: the provisioning step
#     occurs iff the caller did NOT explicitly state there is nothing to record.
#     Dropping the guard is exactly the pre-fix behavior (Solution_prepatch.lean).
#   * the `state` component of (B) vs (A) is nagini's clause (2)
#     `records_read == not (no_pending and not table_present)`: the short-circuit —
#     returning the no-applied state INSTEAD OF reaching the unchanged remainder —
#     happens on EXACTLY the (explicitly-empty, table-absent) point. This is what
#     the zero-query assertion in the failing tests measures; nagini's refinement
#     calls it load-bearing, because an impl that skips the provisioning step but
#     still reaches the remainder satisfies the first component and violates this one.
#   * (A)'s pairing of `provisionedTable := false` with `continuationResult` is
#     nagini's clause (3) read positively: the two effects are independent, and on
#     the table-PRESENT empty batch the remainder is still reached with nothing
#     provisioned.
#   * `tableExists` is consulted ONLY inside the empty-batch arm; on (C) the outcome
#     is independent of it, which is why the (C)-attacking rivals below are refuted
#     at both of its values across the battery rather than at one fixed value:
#     weak-never-provision at (some [7], false), weak-empty-truthiness at
#     (none, true), and weak-provision-only-when-present at (some [7], true) — the
#     last of which exists precisely because a rival that conditions the provisioning
#     guard on table presence is refutable ONLY at a non-empty batch with the table
#     already there, a point no ported case reached.
#   * the `includesApplied` PAYLOAD of the short-circuit state in arm (B) is pinned
#     too, and weak-shortcircuit-payload is the only case that attacks it: it takes
#     the right branch and skips provisioning, differing from gold ONLY in that
#     payload. Without it the spec could have pinned `State.projectState _` with the
#     payload free and every other case would still have been refuted.
#
# WITNESS-POINT COVERAGE (all six (batch-shape x table-presence) points, and which
# component each witness turns on — recomputed against the spec, not asserted):
#   (some [], true)  arm (A): weak-unconditional-provision [provisionedTable],
#                             weak-ignore-table [state]
#   (some [], false) arm (B): weak-no-short-circuit [state],
#                             weak-provision-on-short-circuit [provisionedTable],
#                             weak-flip-table-presence [state],
#                             weak-shortcircuit-payload [state payload]
#   (some [7], false) arm (C): weak-never-provision [provisionedTable]
#   (some [7], true)  arm (C): weak-provision-only-when-present [provisionedTable]
#   (none, true)      arm (C): weak-empty-truthiness [provisionedTable]
#   (none, false)     arm (C): reached by no witness. Deliberate, not a gap: it is
#     refutable (a rival short-circuiting on an ABSENT batch diverges there in the
#     `state` component alone), but every clause that point exercises — that `none`
#     is not the explicit empty batch, and that arm (C) returns the remainder's state
#     — is already pinned by weak-empty-truthiness at (none, true) and by the two
#     non-empty-batch witnesses. A rival for it would restate the `none` distinction
#     weak-empty-truthiness already certifies.
#
# CARRIER NOTE. Nagini modeled the same decision as two mutating boolean flags on an
# `Executor` object behind fractional read permission on the table-presence flag.
# Here both inputs enter as plain data and both effects are components of a returned
# `Outcome`, so every nagini clause has a direct counterpart and each is refutable at
# a CONCRETE literal input: the carrier is fully transparent (`Option (List Nat)`,
# `Bool`, two `deriving DecidableEq` inductives), so `decide` computes the spec at
# any literal point and no witness needs to condition on an opaque term.
#
# ---------------------------------------------------------------------------
# NAGINI CASES THAT DO NOT PORT (see also the `assessment` field of the payload)
# ---------------------------------------------------------------------------
#   * FRAME-MUTATION (nagini's frame-mutate-readonly-table / frame-flip-readonly-
#     table, its MANDATORY class). The literal MECHANISM does not port: those rivals
#     write the table-presence flag, held at half permission, and are rejected by the
#     PERMISSION SYSTEM before any value reasoning. Lean is referentially transparent
#     — no aliasing, no fractional permission, and `tableExists : Bool` is an
#     immutable argument — so a "store into a read-only input" rival is not
#     expressible, and a rejection for insufficient permission has no counterpart.
#     The INTENT, however, IS expressible and is now carried by a rival of its own:
#     weak-flip-table-presence below CORRUPTS the presence observation at the value
#     level (it consults it with the opposite polarity), which is exactly what
#     nagini's frame-flip rival would have achieved had it been permitted to write.
#     (An earlier revision of this file assigned that intent to
#     weak-empty-truthiness; that was wrong — the truthiness rival misreads the
#     BATCH observation, `plannedOps`, and agrees with gold on `tableExists`
#     everywhere, so it cannot stand in for a presence-corrupting rival.)
#   * ADMISSIBILITY — NOT omitted any more. An earlier revision of this file
#     recorded the lane as N/A on the ground that the lean obligation carries NO
#     precondition hypothesis, so "there is nothing that could be
#     PRECOND-TOO-STRONG" and a probe "would attest to nothing". That reasoning was
#     WRONG, and the case it rejected is now shipped below as
#     admiss-f2p-shaped-input. The absence of a precondition is not the absence of
#     the failure mode: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
#     modeled obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#     positive that discharges the obligation at that concrete input — by
#     EVALUATION, as a `have`, before closing the frozen obligation verbatim —
#     tests directly. That is a strictly stronger claim than the ∀-obligation makes
#     on its own, because the frozen theorem could in principle be closed while the
#     modeled decision evaluated to something the F2P scenario contradicts; the
#     second `have` pins the outcome at that point to a CONCRETE `Outcome` value
#     rather than leaving it to a term over the same inputs. Ports nagini's
#     admiss-f2p-shaped-input (which defended the half-permission precondition and
#     the two "starts False" requirements) to the shape this carrier admits.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries no `diverge-*` /
#     `nonterm-*` / `weak-diverge` case, and on lean the class is vacuous here — not
#     merely hard. This bundle sets NO `loom.semantics.termination` option at all, so
#     the impl is a plain Lean `def` and Lean's own elaborator enforces totality;
#     that is the "total" disposition, under which a measureless loop is genuinely
#     rejected. What makes the class VACUOUS rather than shippable is that such a
#     rival cannot carry a witness, which is what a reject case must have here. Both
#     halves were measured, not argued:
#       - a rival whose impl opens `let rec spin (n : Nat) : Bool := spin (n + 1)`
#         passes variant_scope and then fails to elaborate with `fail to show
#         termination for implementation_provisionRecordsTable.spin … ⊢ False`;
#       - the refutation witness built AGAINST that same rival — the half that must
#         SUCCEED for a reject case to attribute anything — also fails, because the
#         impl it must reduce never elaborates (`Tactic `decide` failed for
#         proposition ¬if some [7] = some [] then …`). A reject case here would
#         therefore record `witness-unproven`, an inconclusive outcome, not a
#         rejection attributable to the postcondition.
#       - spelling it `partial def` instead is accepted by variant_scope and then
#         fails to compile: `failed to compile 'partial' definition
#         `implementation_provisionRecordsTable`, could not prove that the type
#         Option (List PlannedOp) → Bool → Outcome is nonempty` (`Outcome` carries no
#         `Inhabited`/`Nonempty` instance), so it cannot mint a vacuous pass either.
#     (Contrast velvet under `loom.semantics.termination "partial"`, where a
#     non-terminating impl verifies vacuously and the disposition is a KNOWN HOLE
#     rather than a vacuous class; the corpus-wide termination-semantics finding.)
#   * AXIOM_TESTS. Empty in the nagini sibling and out of scope for this gate
#     anyway — the axiom lane is G-AX's job. There is no `opaque` callee and no
#     consumed axiom in this bundle, so it is vacuous on both sides.
from pathlib import Path

INSTANCE = "django__django-15252"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. `_IMPL_OLD` is the whole impl region body (between
# # impl-start / # impl-end) and `_PROOF_OLD` the whole tactic body (between
# # proof-start / # proof-end, theorem STATEMENT excluded and never touched).
# Both lie ENTIRELY inside the region they name and are unique in the file, so
# every variant differs from the frozen source only where variant_scope permits.
# ---------------------------------------------------------------------------
_IMPL_OLD = """def implementation_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
  -- The bookkeeping table must be present to record applied migrations, but it
  -- must not be provisioned when there is nothing to record.
  let mut provisioned := false
  if plannedOps = some [] then
    if !tableExists then
      -- nothing to record and no table: short-circuit with a no-applied state.
      return { provisionedTable := false, state := State.projectState false }
    -- table already present: leave it untouched and proceed.
  else
    -- there is work to record (or the batch is computed): provision the table.
    provisioned := true
  -- the routine's unchanged remainder produces the project state.
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }"""

_PROOF_OLD = """  intro plannedOps tableExists
  unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
  by_cases h : plannedOps = some []
  · subst h
    cases tableExists <;> rfl
  · simp only [Id.run, h, if_false]
    rfl"""

assert _BASE.count(_IMPL_OLD) == 1, "impl anchor drifted"
assert _BASE.count(_PROOF_OLD) == 1, "proof anchor drifted"

# The signature line every variant keeps verbatim (only the BODY is reshaped).
_HEAD = """def implementation_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
"""


def _variant(body, proof=_PROOF_OLD):
    """A full Solution.lean with the impl body (and optionally the tactic body)
    replaced. The `theorem correct_provisionRecordsTable` STATEMENT, the spec, the
    docstring and the pure region are all untouched."""
    return _swap(_swap(_BASE, _IMPL_OLD, _HEAD + body), _PROOF_OLD, proof)


def _reproof(proof):
    """A full Solution.lean with ONLY the tactic body replaced — the impl region is
    the FROZEN one, byte-for-byte. Used by the admissibility case, whose whole point
    is to add a ground discharge to the proof of the unmodified implementation."""
    return _swap(_BASE, _PROOF_OLD, proof)


# ===========================================================================
# ADMISSIBILITY (soundness direction: the obligation must be SATISFIABLE at the
# F2P-shaped input). Impl region is the frozen one; the tactic body gains two
# `have`s that discharge the obligation at that concrete input BY EVALUATION
# before the frozen script closes the ∀-obligation verbatim.
# ===========================================================================
_ADMISS = _reproof(
    """  -- The F2P-shaped input: the caller explicitly states there is nothing to
  -- record (`some []`) and the bookkeeping table is absent (`false`). Discharge
  -- the obligation THERE, by evaluation, before proving it in general.
  have _f2p : problem_spec_provisionRecordsTable (some []) false
      (implementation_provisionRecordsTable (some []) false) := by
    unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
    decide
  -- ... and pin the outcome at that point to a CONCRETE value, so the discharge
  -- above cannot be satisfied by an unspecified branch: no provisioning, and the
  -- short-circuit no-applied state.
  have _noProvision : implementation_provisionRecordsTable (some []) false
      = { provisionedTable := false, state := State.projectState false } := by
    unfold implementation_provisionRecordsTable
    decide
""" + _PROOF_OLD)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG. Ported from
# nagini's pos-control-flat / pos-control-reorder: same DECISION on all six
# (batch-shape × table-presence) points, different executable shape. Each needs a
# genuine reproof here, since the frozen script's `rfl`/`simp only` steps are tuned
# to the frozen branch tree; the theorem statement stays byte-identical and no
# lemma / axiom / sorry / native_decide is introduced.
# ===========================================================================

# pos-flat — nagini's pos-control-flat. Both observable components are computed
# STRAIGHT-LINE from the same two observations the frozen impl branches on: the
# provisioning component is the negation of "the caller explicitly stated there is
# nothing to record", and the state component short-circuits exactly on the
# conjunction of that with the table being absent. No nested `if`, no early return.
_POS_FLAT = _variant(
    """  -- Decide both observable components up front, then return them together.
  let emptyBatch : Bool := decide (plannedOps = some [])
  let provisioned : Bool := !emptyBatch
  let st : State :=
    if emptyBatch && !tableExists then State.projectState false
    else State.continuationResult plannedOps
  return { provisionedTable := provisioned, state := st }""",
    """  intro plannedOps tableExists
  unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
  by_cases h : plannedOps = some []
  · subst h
    cases tableExists <;> rfl
  · simp only [Id.run, h, if_false]
    simp
    rfl""",
)

# pos-reorder — nagini's pos-control-reorder. The arms are handled in the opposite
# order: the work-to-record case first with an early return, then the empty batch
# split on table presence. Behaviourally identical on all six points; a branch
# reorder, not a different algorithm.
_POS_REORDER = _variant(
    """  -- Handle the work-to-record case first, then split the explicitly-empty
  -- batch on whether the table is already there.
  if plannedOps ≠ some [] then
    return { provisionedTable := true, state := State.continuationResult plannedOps }
  if tableExists then
    return { provisionedTable := false, state := State.continuationResult plannedOps }
  return { provisionedTable := false, state := State.projectState false }""",
    """  intro plannedOps tableExists
  unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
  by_cases h : plannedOps = some []
  · subst h
    cases tableExists <;> rfl
  · simp only [Id.run, h, if_false]
    simp [h]
    rfl""",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly, edits only the impl region, leaves the frozen tactic body in place
# (it will not close for the reshaped impl — which is precisely why the gate reads
# the WITNESS, not the rival's build, to attribute the rejection).
# ===========================================================================

# weak-unconditional-provision — nagini's uniq-unconditional-schema, THE pre-fix
# behaviour (byte-equal to Solution_prepatch.lean's impl body up to comments).
_RIV_UNCOND = _variant(
    """  let mut provisioned := false
  provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")

# weak-no-short-circuit — nagini's uniq-always-read. Gets the provisioning
# component right on every point and NEVER short-circuits: the remainder is always
# reached. Attacks the `state` component of arm (B) in isolation.
_RIV_ALWAYS_CONT = _variant(
    """  let mut provisioned := false
  if plannedOps ≠ some [] then
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")

# weak-ignore-table — nagini's uniq-ignore-table. Short-circuits on EVERY
# explicitly-empty batch, ignoring `tableExists` entirely. Correct on arm (B) and on
# arm (C); wrong on arm (A) only. The near-miss that pins the `tableExists` binder.
_RIV_IGNORE_TABLE = _variant(
    """  let mut provisioned := false
  if plannedOps = some [] then
    return { provisionedTable := false, state := State.projectState false }
  else
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")

# weak-provision-on-short-circuit — nagini's uniq-write-on-notouch. Short-circuits
# correctly (the `state` component of (B) is right) but reports the provisioning
# step as HAVING BEEN PERFORMED on that very point.
_RIV_PROVISION_NOTOUCH = _variant(
    """  let mut provisioned := false
  if plannedOps = some [] then
    if !tableExists then
      return { provisionedTable := true, state := State.projectState false }
  else
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")

# weak-never-provision — nagini's uniq-skip-all, the supporting mechanical
# near-miss: the provisioning step never occurs on any point and the remainder is
# always reached. Correct on arm (A) alone.
_RIV_NEVER = _variant(
    """  let provisioned : Bool := false
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")

# weak-empty-truthiness — NO direct nagini counterpart; this is the carrier's own
# rival, added because it is the ONLY case that moves `plannedOps` off `some [] /
# some (_ :: _)` onto `none`. It conflates "the caller supplied an empty batch" with
# "the caller left the batch for the routine to compute" by testing emptiness of
# `plannedOps.getD []`, which is `[]` for BOTH. Nagini's `no_pending_records` pins
# `pending is not None and len(pending) == 0`, so the distinction is present in the
# nagini spec too; its battery just never built a rival for it, and without one the
# `plannedOps = none` sub-domain of arm (C) would be attacked by nothing.
_RIV_TRUTHY = _variant(
    """  let mut provisioned := false
  if plannedOps.getD [] = [] then
    if !tableExists then
      return { provisionedTable := false, state := State.projectState false }
  else
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")


# weak-flip-table-presence — the value-level carrier of nagini's FRAME-FLIP intent
# (frame-flip-readonly-table). Nagini corrupted the presence observation by WRITING
# the read-only flag; on this carrier the input cannot be written, so the rival
# corrupts it the only way a referentially transparent impl can — by consulting it
# with the OPPOSITE polarity. It short-circuits on the explicitly-empty batch when
# the table is PRESENT and provisions nothing when it is absent, i.e. it takes the
# no-touch path on exactly the wrong half of the presence domain. Wrong on BOTH
# empty-batch arms while leaving arm (C) untouched.
_RIV_FLIP_PRESENCE = _variant(
    """  let mut provisioned := false
  if plannedOps = some [] then
    if tableExists then
      return { provisionedTable := false, state := State.projectState false }
  else
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")

# weak-provision-only-when-present — closes the one coverage gap the ported battery
# left: NO shipped rival diverges from gold on arm (C) at `tableExists = true`, so
# nothing certified that the provisioning decision on a non-empty batch is
# INDEPENDENT of table presence. This rival hoists the presence test outermost, so
# on a non-empty batch with the table already there it provisions nothing and the
# guard collapses into a presence check.
_RIV_PROVISION_IF_ABSENT = _variant(
    """  let mut provisioned := false
  if !tableExists then
    if plannedOps = some [] then
      return { provisionedTable := false, state := State.projectState false }
    else
      provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")


# weak-shortcircuit-payload — closes the last unattacked sub-clause: NO shipped
# rival varied the `includesApplied` PAYLOAD of the short-circuit state. Every other
# rival that touches arm (B) either reaches the remainder or flips the provisioning
# component, so all of them would still be refuted if the spec had pinned the state
# to `State.projectState _` with the payload left free. This rival short-circuits on
# exactly the right point, provisions nothing there — both correct — and returns
# `projectState true`, a state that DOES carry the already-applied migrations.
_RIV_PAYLOAD = _variant(
    """  let mut provisioned := false
  if plannedOps = some [] then
    if !tableExists then
      return { provisionedTable := false, state := State.projectState true }
  else
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }""")


def _wit(ops, tbl, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at ONE concrete
    literal point, closed by `decide`. The carrier is fully transparent, so the
    statement binds NOTHING (no hypothesis, hence no consistency question) — it
    elaborates against a rival whose outcome differs from the pinned one at that
    point, and fails on the frozen solution, which satisfies the spec everywhere.
    Each of the six witnesses below was built against its rival (must succeed) and
    against the frozen solution (must fail) before shipping."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_provisionRecordsTable {ops} {tbl}\n"
        f"    (implementation_provisionRecordsTable {ops} {tbl}) := by\n"
        f"  unfold problem_spec_provisionRecordsTable"
        f" implementation_provisionRecordsTable\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-flat",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLAT,
        "rationale": (
            "PORT of nagini pos-control-flat. Structurally-different but CORRECT: "
            "both observable components are computed straight-line from the same two "
            "observations the frozen impl branches on — the provisioning component is "
            "the negation of the explicitly-empty-batch test, and the state component "
            "short-circuits exactly on that test conjoined with the table being "
            "absent. Identical outcome on all six (batch-shape x table-presence) "
            "points; no nested branch, no early return, no loop or fold (so no new "
            "induction). The `theorem correct_provisionRecordsTable` STATEMENT is "
            "byte-identical and the tactic body is honestly re-closed (`simp; rfl` on "
            "the non-empty arm) — no lemma, axiom, sorry or native_decide. If a "
            "faithful correct impl of this shape were REJECTED => SPEC-TOO-STRONG "
            "(the postcondition would be over-fit to the frozen branch tree rather "
            "than pinning the decision)."
        ),
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "PORT of nagini pos-control-reorder. Branch reorder: the "
            "work-to-record arm (C) is handled FIRST with an early return, then the "
            "explicitly-empty batch is split on table presence — arm (A) returning "
            "the remainder's state with nothing provisioned, arm (B) short-circuiting. "
            "Same outcome on all six points; a control-shape reshape, not a different "
            "algorithm. Theorem statement byte-identical, tactic body honestly "
            "re-closed. Must verify, else SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "PORT of nagini admiss-f2p-shaped-input, re-expressed for a TOTAL "
            "carrier. The impl region is the FROZEN one byte-for-byte; only the "
            "tactic body gains content, and the theorem STATEMENT is byte-identical. "
            "The frozen obligation has no precondition hypothesis, so the analogue of "
            "PRECOND-TOO-STRONG here is the modeled obligation being UNSATISFIABLE at "
            "exactly an F2P-shaped input. The first `have` discharges "
            "`problem_spec …` at (some [], false) — the caller explicitly stating "
            "there is nothing to record, with the bookkeeping table absent, which is "
            "the shape both FAIL_TO_PASS tests exercise — by EVALUATION (`decide` "
            "after `unfold`), not by appeal to the general theorem. The second `have` "
            "pins the outcome at that point to the concrete value "
            "`{ provisionedTable := false, state := State.projectState false }`, "
            "which is what makes the probe attest to the F2P branch specifically "
            "rather than to some unspecified branch: without it, the discharge would "
            "read identically if the input landed anywhere, since the spec pins "
            "`result` to a term over the same inputs. Then the frozen script closes "
            "the ∀-obligation verbatim. Nothing is assumed — no new declaration, no "
            "lemma, axiom, sorry or native_decide. If either `have` failed, the "
            "modeled decision would be contradicted at the very input the F2P tests "
            "measure => the total-carrier analogue of PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-unconditional-provision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNCOND,
        "refinement": (
            "This is the PRE-FIX behavior itself (the same impl body "
            "Solution_prepatch.lean carries): the provisioning step is performed up "
            "front on every call, unconditionally, and the remainder is always "
            "reached. Its faithful real counterpart is the un-patched routine — "
            "literally the code at base_commit. Both FAIL_TO_PASS tests exercise a "
            "caller that explicitly states there is nothing to record while the table "
            "is absent, and each asserts that no provisioning happens there (one via "
            "'the provisioning step was not invoked', one via 'zero queries were "
            "issued'). With the step unconditional, the table is created and both "
            "assertions fail. So a verifying rival here would be a genuine "
            "verify-does-not-imply-resolve break: it is exactly the code the F2P "
            "tests were written to reject."
        ),
        "rationale": (
            "REJECTED by the `provisionedTable` component of arms (A) and (B): on an "
            "explicitly-empty batch the spec pins it to false, and the rival reports "
            "true. (It violates the `state` component of (B) too, since it reaches "
            "the remainder instead of short-circuiting.) Attacks the "
            "provisioning-guard clause; witnessed at (some [], true), which varies "
            "`tableExists` away from the value the other empty-batch witnesses use, "
            "so the refutation rests on the provisioning component alone and not on "
            "the short-circuit."
        ),
        "witness": _wit("(some [])", "true",
                        "explicitly-empty batch, table present: the spec pins "
                        "provisioning to false; the rival performs it"),
    },
    {
        "id": "weak-no-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_CONT,
        "refinement": (
            "The PARTIAL fix, and the case nagini's refinement singles out as "
            "load-bearing (uniq-always-read). It gets the provisioning guard entirely "
            "right — nothing is provisioned on an explicitly-empty batch — but never "
            "short-circuits: the routine's unchanged remainder is entered on every "
            "path. Its faithful real counterpart is a patch that guards the "
            "provisioning step on a non-empty batch but omits the early return. That "
            "patch satisfies the 'provisioning step not invoked' half of the F2P pair, "
            "and still fails the other half: entering the remainder reads the "
            "already-applied records, issuing queries, so the zero-query assertion "
            "fails. It therefore does NOT resolve — the discriminator is the "
            "short-circuit, not the guard."
        ),
        "rationale": (
            "REJECTED by the `state` component of arm (B): at (some [], false) the "
            "spec pins the result to the no-applied short-circuit state, and the rival "
            "returns the remainder's state. The `provisionedTable` component agrees "
            "with gold at EVERY point, so this case isolates the second, independent "
            "component of the postcondition — if it VERIFIED, the spec would be "
            "pinning only the provisioning effect and the short-circuit clause would "
            "be hollow => SPEC-TOO-WEAK."
        ),
        "witness": _wit("(some [])", "false",
                        "explicitly-empty batch, table absent: the spec pins the "
                        "short-circuit state; the rival reaches the remainder"),
    },
    {
        "id": "weak-ignore-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_TABLE,
        "refinement": (
            "PORT of nagini uniq-ignore-table. Short-circuits on EVERY explicitly-"
            "empty batch, never consulting whether the table is already present. Its "
            "faithful real counterpart is the fix WITHOUT its inner presence guard — "
            "an unconditional early return on the empty batch. It resolves both F2P "
            "tests (they both mock the table as absent, where this rival agrees with "
            "gold), but it changes behavior on the table-PRESENT empty batch: the "
            "routine returns a state with no already-applied migrations instead of "
            "proceeding through the remainder, which is where the applied-record state "
            "is assembled. The PASS_TO_PASS migration-executor tests run against an "
            "existing bookkeeping table and observe that assembly, so this patch "
            "breaks them and does not resolve the instance. A NEAR-MISS: it agrees "
            "with gold on the whole F2P sub-domain, which is why its witness is placed "
            "at the one point that distinguishes it."
        ),
        "rationale": (
            "REJECTED by the `state` component of arm (A): at (some [], true) the "
            "spec pins the remainder's state, and the rival returns the short-circuit "
            "state. This is the ONLY point in the domain where it differs from gold, "
            "so the witness must sit exactly there — it is the case that certifies the "
            "spec genuinely DEPENDS on the `tableExists` binder inside the empty-batch "
            "arm. If it VERIFIED, `tableExists` would be doing no work in the spec => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit("(some [])", "true",
                        "explicitly-empty batch, table PRESENT: the spec pins the "
                        "remainder's state; the rival short-circuits"),
    },
    {
        "id": "weak-provision-on-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PROVISION_NOTOUCH,
        "refinement": (
            "PORT of nagini uniq-write-on-notouch. Short-circuits on exactly the "
            "right point — the `state` component of arm (B) is correct — but performs "
            "the provisioning step on that very point before returning. Its faithful "
            "real counterpart is a patch that adds the early return yet still "
            "provisions the table first: the single side effect the fix exists to "
            "remove. Both F2P tests assert that no provisioning happens on precisely "
            "this input, so this patch fails both and does NOT resolve. It is the "
            "mirror image of weak-no-short-circuit: right half, wrong half, and the "
            "pair together shows the two components are independently pinned."
        ),
        "rationale": (
            "REJECTED by the `provisionedTable` component of arm (B): at "
            "(some [], false) the spec pins it to false while the rival reports true, "
            "with the `state` component agreeing. Attacks the provisioning-guard "
            "clause at the short-circuit point specifically — the nagini clause (3) "
            "reading, that on the short-circuit path NEITHER effect occurs. If it "
            "VERIFIED, the spec would permit provisioning on the no-touch path => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit("(some [])", "false",
                        "explicitly-empty batch, table absent: the spec pins "
                        "provisioning to false on the short-circuit point; the rival "
                        "performs it"),
    },
    {
        "id": "weak-never-provision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEVER,
        "refinement": (
            "PORT of nagini uniq-skip-all, the supporting mechanical near-miss. The "
            "provisioning step never occurs on any input and the remainder is always "
            "reached; only arm (A) is correct. Its faithful real counterpart is a "
            "patch that DELETES the provisioning step outright instead of guarding it. "
            "That resolves nothing: the bookkeeping table would never be provisioned "
            "even when there is migration work to record, so the applied migrations "
            "could not be recorded at all and the PASS_TO_PASS suites that apply "
            "migrations against a fresh database fail. Deleting an effect is not the "
            "same edit as conditioning it, and only the latter resolves."
        ),
        "rationale": (
            "REJECTED by the `provisionedTable` component of arm (C): at "
            "(some [7], false) — a NON-EMPTY batch with the table ABSENT — the spec "
            "pins provisioning to true and the rival reports false. It is the "
            "UNDER-provisioning direction, which only one other rival "
            "(weak-provision-only-when-present) attacks, and this is the only case "
            "that takes it at the table-absent point: every other rival "
            "over-provisions or mis-short-circuits, so without this case an impl that "
            "simply never provisions on a table-absent non-empty batch would satisfy "
            "the battery. Its violation set is also the widest here — it is wrong at "
            "five of the six points, correct on arm (A) alone — so it doubles as the "
            "supporting mechanical near-miss. Varies `plannedOps` off `some []`, so "
            "arm (C) is attacked rather than assumed."
        ),
        "witness": _wit("(some [7])", "false",
                        "non-empty batch: the spec pins provisioning to true; the "
                        "rival never provisions"),
    },
    {
        "id": "weak-empty-truthiness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRUTHY,
        "refinement": (
            "NEW on this carrier (no nagini counterpart shipped, though nagini's "
            "oracle draws the same distinction). It conflates the two ways a batch can "
            "look empty: the caller EXPLICITLY stating there is nothing to do, and the "
            "caller leaving the batch for the routine to compute. Its faithful real "
            "counterpart is the fix written with a truthiness test on the batch "
            "parameter rather than an equality test against the empty batch — a "
            "textbook near-miss, and idiomatic enough in the source language that it "
            "is the most plausible wrong patch here. It resolves both F2P tests, which "
            "pass an explicitly-empty batch. But when the caller leaves the batch to "
            "be computed, the routine must still provision and proceed; under the "
            "truthiness test it instead skips provisioning and, with the table absent, "
            "returns a no-applied state WITHOUT ever computing the batch — so no "
            "migration work is performed. The PASS_TO_PASS executor tests that invoke "
            "the routine without supplying a batch (running a simple set of "
            "migrations, running a squashed migration, and the rollback/replacement "
            "cases) all fail, and the instance does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the `provisionedTable` component of arm (C) at "
            "`plannedOps = none`: the spec pins the outcome to { provisioned, "
            "remainder's state } for ANY batch that is not the explicit empty one, "
            "`none` included, and at the witness point (none, true) the rival reports "
            "NO provisioning while agreeing on the `state` component — so the "
            "refutation there rests on the provisioning component alone. (At "
            "(none, false) the rival diverges in BOTH components, additionally "
            "returning the short-circuit state; the witness is deliberately placed at "
            "the table-PRESENT point instead, because that is the only place the "
            "battery varies `tableExists` to true on arm (C).) This is the ONLY case "
            "whose witness moves the "
            "`plannedOps` binder onto `none`, i.e. the only one that certifies the "
            "spec's `plannedOps = some []` test is an equality on the OPTION and not "
            "merely on the list. If it VERIFIED, the spec would not distinguish an "
            "absent batch from an explicitly empty one => SPEC-TOO-WEAK. It also "
            "carries the INTENT of nagini's frame-mutation class over: the rival "
            "corrupts the observation the whole decision branches on — by reading it "
            "at the wrong shape, since on this carrier it cannot be written to."
        ),
        "witness": _wit("none", "true",
                        "absent batch (left for the routine to compute): the spec "
                        "pins provisioning and the remainder's state; the rival "
                        "treats it as an empty batch"),
    },
    {
        "id": "weak-flip-table-presence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLIP_PRESENCE,
        "refinement": (
            "The value-level PORT of nagini's frame-flip-readonly-table intent, which "
            "the mechanism-level omission note above explains cannot port literally. "
            "Its faithful real counterpart is the fix with the inner presence guard "
            "written at the wrong polarity — short-circuiting when the bookkeeping "
            "table IS already present and provisioning nothing when it is absent. "
            "Both FAIL_TO_PASS tests exercise the explicitly-empty batch with the "
            "table mocked ABSENT: there this rival falls through to the remainder "
            "instead of short-circuiting, so the zero-query assertion fails and it "
            "does NOT resolve. It simultaneously breaks the table-present empty-batch "
            "sub-domain the PASS_TO_PASS executor suites cover. A patch that consults "
            "the presence observation with inverted sense is a plausible off-by-a-"
            "negation edit, and it is wrong in both directions at once."
        ),
        "rationale": (
            "REJECTED by the `state` component of BOTH empty-batch arms, and the "
            "witness is placed at (some [], false) — arm (B) — where the spec pins the "
            "short-circuit no-applied state and the rival returns the remainder's "
            "state. (It is symmetrically wrong on arm (A) at (some [], true), where it "
            "short-circuits and the spec pins the remainder; both points were built "
            "and both discriminate.) Distinct from weak-ignore-table, which DROPS the "
            "presence test and so is wrong on arm (A) only: this one INVERTS it and is "
            "wrong on both. If it VERIFIED, the spec would be pinning that the "
            "presence observation is consulted without pinning its SENSE => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit("(some [])", "false",
                        "explicitly-empty batch, table absent: the spec pins the "
                        "short-circuit state; the rival, reading presence at the "
                        "opposite polarity, reaches the remainder"),
    },
    {
        "id": "weak-provision-only-when-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PROVISION_IF_ABSENT,
        "refinement": (
            "NEW on this carrier, and it closes a genuine hole in the ported battery: "
            "every other rival that attacks arm (C) does so with the table ABSENT, so "
            "none of them tested that the provisioning decision on a batch with work "
            "to record is INDEPENDENT of whether the table happens to be there. Its "
            "faithful real counterpart is the fix written with the presence check "
            "hoisted above the batch check, so that provisioning is attempted only on "
            "connections whose table is missing. It resolves both F2P tests (they mock "
            "the table absent and pass an explicitly-empty batch, where it agrees with "
            "gold), which is exactly what makes it dangerous. But on a non-empty batch "
            "against an EXISTING bookkeeping table it skips the provisioning step, so "
            "the routine no longer guarantees the table is present and correctly "
            "shaped before the remainder records applied migrations — the invariant "
            "the step exists to establish. The PASS_TO_PASS executor suites that apply "
            "and record migrations against an already-provisioned database observe "
            "that, so this patch does NOT resolve the instance."
        ),
        "rationale": (
            "REJECTED by the `provisionedTable` component of arm (C) at "
            "(some [7], true): the spec pins provisioning to true for ANY batch that "
            "is not the explicit empty one, at BOTH values of `tableExists`, and the "
            "rival reports false. This is the ONLY witness in the battery that sits on "
            "arm (C) with the table PRESENT — the (non-empty batch, table present) "
            "point no other case reaches — so it is what certifies that `tableExists` "
            "does NO work outside the empty-batch arm. If it VERIFIED, the spec would "
            "permit the provisioning guard to be conditioned on table presence => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit("(some [7])", "true",
                        "non-empty batch with the table already present: the spec "
                        "pins provisioning to true regardless of presence; the rival "
                        "provisions only when the table is absent"),
    },
    {
        "id": "weak-shortcircuit-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PAYLOAD,
        "refinement": (
            "NEW on this carrier, and it closes the last sub-clause nothing else "
            "probed: the PAYLOAD of the short-circuit state. Its faithful real "
            "counterpart is the fix written with the short-circuit's project-state "
            "constructed to INCLUDE the already-applied migrations rather than "
            "excluding them — the same early return, the same skipped provisioning, "
            "the wrong flag on the state it hands back. That is a plausible edit "
            "precisely because the routine's other project-state construction, the "
            "one the unchanged remainder performs on an empty batch, does include "
            "them, so copying that call is the natural mistake. It resolves the half "
            "of the F2P pair that counts queries only by accident and fails the "
            "instance regardless: assembling a state that claims applied migrations "
            "are included, on a connection whose bookkeeping table does not even "
            "exist, means the returned state misreports what has been applied, and "
            "the applied-migration set it would have to read is unavailable. The "
            "PASS_TO_PASS suites that inspect the returned state's applied-migration "
            "content on the short-circuit path observe that, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the `state` component of arm (B) at (some [], false): the "
            "spec pins the result to `State.projectState false` — the no-applied "
            "state — and the rival returns `State.projectState true`. This is the "
            "ONLY case that varies the `includesApplied` payload while getting BOTH "
            "the short-circuit decision and the provisioning component right; every "
            "other arm-(B) rival diverges in the branch taken or in "
            "`provisionedTable`, so all of them would still be refuted if the spec "
            "had pinned the state to `State.projectState _` with the payload left "
            "free. If it VERIFIED, the spec would pin THAT a no-applied state is "
            "returned without pinning WHICH => SPEC-TOO-WEAK."
        ),
        "witness": _wit("(some [])", "false",
                        "explicitly-empty batch, table absent: the spec pins the "
                        "short-circuit state to the one with NO applied migrations; "
                        "the rival returns one that claims to include them"),
    },
]


# The axiom lane is G-AX's job and is vacuous here regardless: there is no `opaque`
# callee and no consumed axiom in this bundle (both inputs enter as plain data and
# the two returned state shapes are structural carriers in the `pure` region).
AXIOM_TESTS = []

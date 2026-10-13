# properties.py — G-PBT falsification battery for sympy__sympy-20154 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only
# the impl region — and, where the positive reproves, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries
# a refutation `witness`: a self-contained snippet that ELABORATES against the
# rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   implementation_partitions : List PartMap → List PartMap
#   Materializes a produced sequence of intermediate states `states` into a list
#   `result`. The single postcondition pins two independent clauses:
#     (C1) result.length = states.length          — one entry per produced state;
#     (C2) ∀ i < states.length, result.getD i [] = states.getD i []
#          — the entry at each position is the state produced at THAT position, in
#            order.
#   (C2) is the LOAD-BEARING discriminator: every materialized entry must equal the
#   GROUNDED per-position state of its OWN position. This is exactly the per-step
#   history that a materialization collapsing every entry onto the final produced
#   state (the modeled defect) cannot reproduce.
#
# CARRIER NOTE. The nagini sibling modeled the walk over an INTEGER abstraction
# (each produced state == its 1-based step index; the by-value snapshot fix modeled
# as `snap = work`, and total correctness pinned by a MustTerminate obligation).
# This backend models the FULL position-wise materialization over a transparent
# `List PartMap` carrier: `states` is the produced sequence taken as the input, and
# the fix is the position-wise identity relating `result` to `states`. So the
# nagini rivals that attack the per-step value / order / cardinality all port
# directly, re-expressed as list-shaped rivals over `states`.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION. Nagini's aliasing/permission machinery (Acc(x,1/2)) does not
#     exist here: Lean is referentially transparent, the sole input `states` is
#     immutable, and the ownership predicate on the fresh output is not a thing to
#     mutate. The class is VACUOUS — the aliasing-COLLAPSE DEFECT (the pre-patch
#     "every record reads back as the final state") still ports as a value rival,
#     since on this carrier it is a value divergence, not a permission trick.
#   * NON-TERMINATION (nagini's uniq-nonterminating, rejected by the MustTerminate
#     obligation). An earlier revision of this file recorded the class as "genuinely
#     vacuous — a diverging implementation cannot be written at all". That is FALSE
#     as stated and was corrected by audit, with builds. A diverging impl IS
#     writable inside the impl region without any banned token: an unbounded
#     `while` whose loop state is the returned value,
#         let mut i : Nat := 0
#         while i < 1 do
#           out := out
#         return out
#     elaborates (the `def` alone builds, exit 0) because `Lean.Loop.forIn`'s
#     recursion is compiled, not structural — so `def` totality is NOT what blocks
#     it. What blocks it is that the resulting term never REDUCES: `#eval` of that
#     impl times out (exit 124 at 150s), `rfl` cannot equate it to any value ("is
#     not definitionally equal"), and no Mathlib lemma equates the loop term to its
#     input (`simp` "made no progress"; `unfold Lean.Loop.forIn` fails; `decide
#     +kernel` cannot even form the goal).
#     So the correct DISPOSITION is a KNOWN HOLE, not a vacuous class:
#       - the rival is not shippable as a reject case. It fails to build (exit 1),
#         but only because the frozen proof's `show` no longer matches — a tactic
#         mismatch, exactly what the witness requirement exists to disallow. And no
#         witness can refute it: a `decide` witness cannot reduce the loop term
#         ("Tactic `decide` failed", exit 1 on the RIVAL — the half that must
#         succeed), and a hypothesis-conditioned witness fares no better, since its
#         own consistency probe cannot be discharged either (`⊢ False` unsolved on
#         BOTH sides), which is the forgery shape the gate screens for.
#       - nor is it a demonstrated SPEC hole: the diverging rival was NOT shown to
#         verify. A serious reproof attempt fails with unsolved goals over the
#         irreducible loop term, and the non-reducibility above is what stops the
#         obligation being discharged in either direction. The honest reading is
#         UNDECIDED-BY-THIS-CARRIER, and it is recorded here rather than silently
#         dropped.
#     One weaker probe DOES verify and must not be mistaken for the above: a
#     `while True do pure ()` prefix spliced ahead of the frozen body verifies
#     (exit 0) — but that is not a divergence at all. Its loop state is `PUnit`,
#     the frozen body still computes the answer, and `Id`'s bind discards the dead
#     loop, so the impl still `#eval`s to gold's value. It is a correct impl with
#     unreachable garbage, so its verifying is right, not a hole.
#   * FRAME-MUTATION's partner class, CONTROL-FLOW-EFFECT: N/A for the same reason
#     nagini gave — the modeled function is pure-functional over the value domain,
#     with no raise path and no effect on any input.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them.
#
# ADMISSIBILITY IS *NOT* IN THAT LIST — it ports, as adm-f2p-ground below. An
# earlier revision of this file recorded the lane as N/A on the ground that the
# lean obligation `∀ (states : List PartMap), problem_spec …` carries NO
# precondition hypothesis, so nothing could be PRECOND-TOO-STRONG. That reasoning
# is wrong, and dropping the lane removed one of the three directions this gate
# exists to test. The analogue of PRECOND-TOO-STRONG on a TOTAL carrier is not an
# unsatisfiable `require`; it is the OBLIGATION being unsatisfiable at exactly an
# F2P-shaped input — a spec vacuously or contradictorily strong at the very inputs
# the consumer actually uses. That is directly testable here: discharge the
# obligation at a concrete F2P-shaped produced sequence BY EVALUATION, as a
# `have`, before closing the frozen obligation verbatim. See adm-f2p-ground.
from pathlib import Path

INSTANCE = "sympy__sympy-20154"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchor (lies ENTIRELY inside impl-start/impl-end, unique in file).
# The accumulating materialization loop body, verbatim: ---------------------------
_IMPL = (
    "  let mut out : List PartMap := []\n"
    "  for s in states do\n"
    "    -- emit the state current at this step as its own entry\n"
    "    out := out ++ [s]\n"
    "  return out"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# --- proof-region body (between the proof markers), verbatim. Only the positive
# control (a structurally-different CORRECT impl) reshapes this, keeping the
# `theorem correct_partitions` STATEMENT byte-identical. ---------------------------
_PROOF = (
    "/-- The append-accumulating `forIn` loop over `states`, generalized over the\n"
    "accumulator, is just `init ++ states`. -/\n"
    "theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :\n"
    "    (Id.run (forIn states init (fun s r =>\n"
    "        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap))))))\n"
    "    = init ++ states := by\n"
    "  induction states generalizing init with\n"
    "  | nil => simp [Id.run, List.forIn_nil, pure]\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    rw [ih]\n"
    "    simp\n"
    "\n"
    "theorem partitions_eq (states : List PartMap) :\n"
    "    implementation_partitions states = states := by\n"
    "  unfold implementation_partitions\n"
    "  have h2 : (forIn states ([] : List PartMap) fun s r =>\n"
    "        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))\n"
    "          : Id (ForInStep (List PartMap))))\n"
    "      = (forIn states ([] : List PartMap) fun s r =>\n"
    "        (ForInStep.yield (r ++ [s]) : Id (ForInStep (List PartMap)))) := rfl\n"
    "  show Id.run (forIn states ([] : List PartMap) fun s r =>\n"
    "        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [s]))\n"
    "          : Id (ForInStep (List PartMap)))) = states\n"
    "  rw [h2, forIn_append_eq]\n"
    "  simp\n"
    "\n"
    "theorem correct_partitions :\n"
    "    ∀ (states : List PartMap),\n"
    "      problem_spec_partitions states (implementation_partitions states) := by\n"
    "  intro states\n"
    "  unfold problem_spec_partitions\n"
    "  rw [partitions_eq]\n"
    "  exact ⟨rfl, fun i _ => rfl⟩"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------
# pos-identity-return: returns the produced sequence directly (no accumulator, no
# loop) — the shape a faithful patch could equally take, since materialization is
# position-wise identity. The result is identical on every input, and the frozen
# `theorem correct_partitions` STATEMENT is kept byte-identical.
#
# HONEST LIMIT OF THIS CONTROL (recorded by audit, not by the port). `let mut out
# := states; return out` is DEFINITIONALLY the identity on this carrier, so the
# reproof closes both clauses by bare `rfl` and the case exercises no real proof
# obligation. It is a genuine soundness control — a spec that had become
# unsatisfiable, or that pinned something other than position-wise identity, would
# still fail here — but it is the WEAKEST form of the soundness probe, and on its
# own it would leave SPEC-TOO-STRONG barely tested: any spec that admits gold at
# all admits a term that is definitionally gold's answer. So it is kept as the
# cheap control and pos-cons-reverse below carries the load.
_POS_IMPL = (
    "  let mut out : List PartMap := states\n"
    "  return out"
)

# pos-cons-reverse: the LOAD-BEARING soundness control. A structurally different
# loop that is NOT definitionally the frozen one: each produced state is PREPENDED
# (`out := s :: out`), so the accumulator holds the reversed prefix at every step
# and the produced order is restored once at the end by `.reverse`. Behaviourally
# identical on every input, but nothing here reduces by `rfl` — the reproof has to
# re-establish the loop lemma with a genuinely different statement
# (`states.reverse ++ init` in place of `init ++ states`) and then discharge the
# double reversal. This is the reshape that would actually catch a spec too tightly
# coupled to the frozen impl's append-accumulate SHAPE rather than to its VALUE:
# a spec pinning the accumulator's intermediate contents, or stated so that only a
# left-to-right append could satisfy it, verifies pos-identity-return and fails
# here. Verified end-to-end at /tmp (exit 0) before shipping.
# If it FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected).
_POS2_IMPL = (
    "  let mut out : List PartMap := []\n"
    "  for s in states do\n"
    "    -- prepend each produced state, then restore the produced order at the end\n"
    "    out := s :: out\n"
    "  return out.reverse"
)
_POS2_PROOF = (
    "/-- The cons-accumulating `forIn` loop over `states`, generalized over the\n"
    "accumulator, is `states.reverse ++ init`. -/\n"
    "theorem forIn_append_eq (states : List PartMap) (init : List PartMap) :\n"
    "    (Id.run (forIn states init (fun s r =>\n"
    "        (ForInStep.yield (s :: r) : Id (ForInStep (List PartMap))))))\n"
    "    = states.reverse ++ init := by\n"
    "  induction states generalizing init with\n"
    "  | nil => simp [Id.run, List.forIn_nil, pure]\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    rw [ih]\n"
    "    simp\n"
    "\n"
    "theorem partitions_eq (states : List PartMap) :\n"
    "    implementation_partitions states = states := by\n"
    "  unfold implementation_partitions\n"
    "  have h2 : (forIn states ([] : List PartMap) fun s r =>\n"
    "        (do pure PUnit.unit; pure (ForInStep.yield (s :: r))\n"
    "          : Id (ForInStep (List PartMap))))\n"
    "      = (forIn states ([] : List PartMap) fun s r =>\n"
    "        (ForInStep.yield (s :: r) : Id (ForInStep (List PartMap)))) := rfl\n"
    "  show (Id.run (forIn states ([] : List PartMap) fun s r =>\n"
    "        (do pure PUnit.unit; pure (ForInStep.yield (s :: r))\n"
    "          : Id (ForInStep (List PartMap))))).reverse = states\n"
    "  rw [h2, forIn_append_eq]\n"
    "  simp\n"
    "\n"
    "theorem correct_partitions :\n"
    "    ∀ (states : List PartMap),\n"
    "      problem_spec_partitions states (implementation_partitions states) := by\n"
    "  intro states\n"
    "  unfold problem_spec_partitions\n"
    "  rw [partitions_eq]\n"
    "  exact ⟨rfl, fun i _ => rfl⟩"
)
_POS_PROOF = (
    "theorem correct_partitions :\n"
    "    ∀ (states : List PartMap),\n"
    "      problem_spec_partitions states (implementation_partitions states) := by\n"
    "  intro states\n"
    "  unfold problem_spec_partitions implementation_partitions\n"
    "  refine ⟨rfl, fun i _ => rfl⟩"
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly, edits only the impl region, and carries a witness proving
# it violates the spec at one concrete input (elaborates against the rival, fails
# on gold).
# ---------------------------------------------------------------------------

# uniq-aliasing-collapse: the pre-patch defect. Every materialized entry reads back
# as the FINAL produced state instead of the state of its own position.
_REJ_COLLAPSE = (
    "  let mut out : List PartMap := states.map (fun _ => states.getLastD [])\n"
    "  return out"
)

# uniq-off-by-one-snapshot: materializes the state one position EARLY — every entry
# lags one position (a prepended empty state, the last produced state dropped).
_REJ_SHIFT = (
    "  let mut out : List PartMap := ([] : PartMap) :: states.dropLast\n"
    "  return out"
)

# uniq-partial-first-element: correct on every position EXCEPT the first, which is
# overwritten with the stale initial (empty) state.
_REJ_FIRST = (
    "  let mut out : List PartMap := states.set 0 []\n"
    "  return out"
)

# uniq-length-divergence: correct per-position values but one EXTRA (duplicate)
# entry appended, so the list is one longer than the produced sequence.
_REJ_LEN = (
    "  let mut out : List PartMap := states ++ [[]]\n"
    "  return out"
)

# uniq-reversed-order: same multiset of produced states but in REVERSED position
# order — the k-th entry is the (len-1-k)-th produced state.
_REJ_REVERSED = (
    "  let mut out : List PartMap := states.reverse\n"
    "  return out"
)

# uniq-truncated-drop-last: materializes one entry too FEW (the last produced state
# is never emitted). The mirror of uniq-length-divergence on the (C1) clause: the
# shipped battery only ever probed length being too LONG, so a spec that bounded
# `result.length` from above but not below would have survived the whole battery.
_REJ_SHORT = (
    "  let mut out : List PartMap := states.dropLast\n"
    "  return out"
)

# uniq-last-position: correct on every position EXCEPT the LAST, which is
# overwritten with the empty state. The upper-boundary partner of
# uniq-partial-first-element: it probes (C2) exactly at i == states.length - 1, the
# largest index the clause's `i < states.length` guard admits. An off-by-one in the
# guard (`i < states.length - 1`, or `i + 1 < states.length`) would leave the final
# position unpinned and is invisible to every other rival here.
_REJ_LAST = (
    "  let mut out : List PartMap := states.set (states.length - 1) []\n"
    "  return out"
)

# uniq-middle-position: correct on every position EXCEPT an INTERIOR one, which is
# overwritten with the empty state. Added by audit: the shipped battery pinned (C2)
# only at the two BOUNDARY indices (i==0 via uniq-partial-first-element, and
# i==length-1 via uniq-last-position). A guard weakened to admit only the endpoints
# — `i = 0 ∨ i = states.length - 1`, the shape a hand-written boundary check takes —
# satisfies every other case in this battery and fails only here.
_REJ_MIDDLE = (
    "  let mut out : List PartMap := states.set 1 []\n"
    "  return out"
)

# uniq-intra-partition-key-order: every position holds the RIGHT partition, in the
# right order, with the right multiset of (part, count) pairs — but the pairs INSIDE
# each partition are reversed. Added by audit: every other rival in this battery
# permutes or replaces WHOLE entries, so all of them are caught by a spec comparing
# entries as multisets/sets of pairs. mapping.md declares the association list's key
# order (the generator's largest→smallest `keys`) part of the modeled value, so this
# is a real divergence, and it is the only case that pins the entry's INTERNAL shape.
_REJ_KEYORDER = (
    "  let mut out : List PartMap := states.map (fun p => p.reverse)\n"
    "  return out"
)

# uniq-dedup-repeated-states: collapses ADJACENT EQUAL produced states into one.
# Added by audit: it agrees with the frozen impl on every sequence of pairwise
# DISTINCT states — which is every input the rest of the battery uses, since each
# other witness is stated at distinct states. So a spec quantified only over
# distinct-state sequences, or one pinning entries up to deduplication, satisfies
# the whole rest of the battery and fails only here. The repeated-state sub-domain
# is reachable for the consumer: nothing in the modeled carrier makes consecutive
# produced states distinct, and the (C1) count clause is exactly what forbids
# silently merging them.
_REJ_DEDUP = (
    "  let mut out : List PartMap := states.eraseDups\n"
    "  return out"
)

# uniq-empty-sequence-only: behaves EXACTLY like the frozen impl on every non-empty
# produced sequence, and emits one spurious entry when the generator produced
# nothing at all. Probes the degenerate `states = []` sub-domain, which every other
# case in this battery leaves untouched (their witnesses all use length >= 1): a
# spec quantifying only over non-empty carriers would admit this.
_REJ_EMPTY = (
    "  let mut out : List PartMap :=\n"
    "    if states.isEmpty then [([] : PartMap)] else states\n"
    "  return out"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (soundness-at-an-F2P-input) — must VERIFY.
# ---------------------------------------------------------------------------
# adm-f2p-ground: the frozen obligation, discharged at a CONCRETE F2P-shaped
# produced sequence by EVALUATION (`decide`) as a leading `have`, before the frozen
# obligation is then closed verbatim by the unmodified frozen proof. The impl region
# is the FROZEN one, byte-for-byte — this case changes only the proof body, adding a
# `have` in front of it, so `theorem correct_partitions`'s statement stays
# byte-identical and no new declaration is introduced.
#
# What it tests that no other case here does: that the modeled obligation is
# actually SATISFIABLE — by kernel evaluation, not by a tactic script — at exactly
# the shape of input the consumer uses. A spec that had become vacuously or
# contradictorily strong at F2P-shaped inputs (the total-carrier analogue of
# PRECOND-TOO-STRONG) would fail here while every uniqueness rival still rejected
# and the positive control still verified. The four-state sequence is F2P-shaped:
# a multi-yield produced run of pairwise-DISTINCT partitions, which is what makes
# the per-position clause (C2) non-trivial at every index.
# If it FAILS => the obligation is unsatisfiable at a normal input.
_ADM_STATES = "([[(2,3)], [(1,2),(2,2)], [(1,4),(2,1)], [(1,6)]] : List PartMap)"
_ADM_HAVE = (
    "  have _ground : problem_spec_partitions " + _ADM_STATES + "\n"
    "      (implementation_partitions " + _ADM_STATES + ") := by\n"
    "    unfold problem_spec_partitions implementation_partitions\n"
    "    decide\n"
    "  intro states\n"
    "  unfold problem_spec_partitions\n"
)
_ADM_PROOF = _PROOF.replace(
    "  intro states\n  unfold problem_spec_partitions\n", _ADM_HAVE, 1)
assert _ADM_PROOF != _PROOF, "admissibility proof anchor drifted"


def _wit(states):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    `states` input, closed by `decide`. Elaborates against a rival that diverges
    from the frozen result there, and fails on gold (which satisfies the spec
    everywhere)."""
    return (
        f"example : ¬ problem_spec_partitions {states}\n"
        f"    (implementation_partitions {states}) := by\n"
        f"  unfold problem_spec_partitions implementation_partitions\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "pos-identity-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _POS_IMPL), _PROOF, _POS_PROOF),
        "rationale": (
            "A structurally-different but behaviourally-identical impl: no "
            "accumulator and no per-position append loop — the produced sequence is "
            "returned directly, since materialization is position-wise identity. "
            "Produces the identical list on every input. The frozen `theorem "
            "correct_partitions` statement is kept byte-identical; the reproof "
            "discharges both the length clause (C1) and the position-wise clause "
            "(C2) directly by `rfl`. Verified end-to-end at /tmp before shipping. "
            "If it FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-cons-reverse",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _POS2_IMPL), _PROOF, _POS2_PROOF),
        "rationale": (
            "The LOAD-BEARING soundness control, added by audit because "
            "pos-identity-return is definitionally the frozen impl and so closes by "
            "bare `rfl` without exercising any real obligation. This one PREPENDS "
            "each produced state and restores the produced order with a final "
            "`.reverse`: behaviourally identical on every input, but nothing reduces "
            "by `rfl`, so the reproof must re-establish the loop lemma with a "
            "different statement (`states.reverse ++ init` for `init ++ states`) and "
            "then discharge the double reversal. The frozen `theorem "
            "correct_partitions` statement is kept byte-identical and no new "
            "declaration is introduced (the loop lemma reuses the frozen lemma's "
            "name). A spec coupled to the frozen impl's append-accumulate SHAPE "
            "rather than to its VALUE — one pinning the accumulator's intermediate "
            "contents, or satisfiable only left-to-right — verifies "
            "pos-identity-return and fails HERE. Verified end-to-end at /tmp (exit 0) "
            "before shipping. If it FAILS => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected)."
        ),
    },
    {
        "id": "adm-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _ADM_PROOF),
        "rationale": (
            "The frozen obligation is SATISFIABLE at a concrete F2P-shaped produced "
            "sequence — a multi-yield run of four pairwise-distinct partitions — and "
            "is discharged there by EVALUATION (`decide`) as a leading `have`, after "
            "which the frozen obligation is closed verbatim by the unmodified frozen "
            "proof. The impl region is the frozen one byte-for-byte; nothing is "
            "assumed (no new declaration, `theorem correct_partitions`'s statement "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body). This is the total-carrier analogue of the nagini "
            "sibling's admiss-3-step-walk: on lean the obligation carries no "
            "precondition hypothesis to re-derive, so what PRECOND-TOO-STRONG "
            "becomes is the obligation being unsatisfiable at exactly the inputs the "
            "consumer uses, which kernel evaluation at that input tests directly. If "
            "it FAILS => the modeled obligation is vacuous/contradictory at a normal "
            "F2P-shaped input. Verified end-to-end at /tmp before shipping."
        ),
    },
    {
        "id": "uniq-aliasing-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_COLLAPSE),
        "refinement": (
            "This is the pre-patch behaviour: every materialized entry reads back as "
            "the FINAL produced state (the live-alias collapse). Its faithful real "
            "counterpart is the unchanged repo, under which materializing the "
            "generator yields the same object at every position (all equal to the "
            "last produced state) instead of the genuine per-position history. The "
            "FAIL_TO_PASS tests assert the exact ordered list of distinct per-step "
            "partitions, so it does NOT resolve — a verifying rival here would be a "
            "true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (C2): for a sequence of length >= 2 with distinct "
            "produced states, the collapse makes the entry at position 0 equal the "
            "final state, not the state produced at position 0. Attacks the "
            "per-position-history clause — the exact discriminator the fix installs. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # 3 distinct states; collapse puts the last state at position 0.
        "witness": _wit("([[(2,3)], [(1,2),(2,2)], [(1,6)]] : List PartMap)"),
    },
    {
        "id": "uniq-off-by-one-snapshot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_SHIFT),
        "refinement": (
            "Materializes each state one position EARLY (an empty state prepended, "
            "the last produced state dropped), so the entries are a shifted history. "
            "A faithful real analogue snapshots the working state at the wrong point "
            "in the generation loop; the materialized list is off by one position "
            "everywhere, so the F2P element-by-element comparison fails and it does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C2): the entry at position 0 is the empty state, not "
            "the state produced at position 0. Targets the per-position VALUE facet "
            "(snapshot timing), distinct from the collapse defect. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # 2 distinct states; the shift puts [] at position 0.
        "witness": _wit("([[(1,1),(3,1),(4,1)], [(2,2),(4,1)]] : List PartMap)"),
    },
    {
        "id": "uniq-partial-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_FIRST),
        "refinement": (
            "Correct on every position EXCEPT the first, which is overwritten with a "
            "stale initial (empty) state. A monotonicity/distinctness proxy would "
            "accept it (the rest of the sequence is untouched); only the exact "
            "per-position pin catches it. The faithful real analogue mis-records the "
            "FIRST produced state, so the first entry of every materialized list is "
            "wrong and the F2P first-row comparison fails — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C2) on the single sub-domain i==0 (entry is the empty "
            "state, not the state produced at position 0), while satisfying it for "
            "every i>=1. The partial-domain attack the per-position clause defends. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # first produced state non-empty so `set 0 []` changes position 0 only.
        "witness": _wit("([[(4,2)], [(2,1),(3,2)]] : List PartMap)"),
    },
    {
        "id": "uniq-length-divergence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_LEN),
        "refinement": (
            "Per-position values are all correct, but one EXTRA (duplicate) entry is "
            "appended, so the list is one longer than the produced sequence. The "
            "faithful real analogue is a materialization with a spurious trailing "
            "entry / off-by-one loop bound: every F2P test asserting the exact list "
            "(length and contents) fails because there is one extra entry — does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause (C1) result.length = states.length (length is "
            "states.length + 1). Targets the cardinality facet the per-element clause "
            "alone would not catch. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # a single-state sequence; the rival returns length 2.
        "witness": _wit("([[(3,2)]] : List PartMap)"),
    },
    {
        "id": "uniq-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_REVERSED),
        "refinement": (
            "Materializes the SAME multiset of produced states but in REVERSED "
            "position order. A value proxy keyed on the set/multiset of entries would "
            "accept it; only the per-position clause catches that the k-th entry must "
            "be the k-th produced state. The faithful real analogue materializes the "
            "generator's output in the wrong order, so the F2P ordered comparison "
            "fails — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C2) at position 0 for a length >= 2 sequence with "
            "distinct endpoints (entry is the last produced state, not the first). "
            "Targets the index/order facet. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # 2 distinct states; reversal swaps positions 0 and 1.
        "witness": _wit("([[(2,3)], [(1,4),(2,1)]] : List PartMap)"),
    },
    {
        "id": "uniq-truncated-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_SHORT),
        "refinement": (
            "Materializes one entry too FEW: the last produced state is never "
            "emitted. The faithful real analogue is a materialization whose loop "
            "bound stops one short / drops the final produced state, so every F2P "
            "assertion on the exact list fails for missing its last entry — does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause (C1) result.length = states.length (length is "
            "states.length - 1). This is the MIRROR of uniq-length-divergence, which "
            "only ever probed the list being too LONG: a spec that bounded "
            "result.length from above but not from below would satisfy every other "
            "case in this battery and fail only here. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # 2 states; the rival returns length 1.
        "witness": _wit("([[(3,2)], [(1,1),(2,1)]] : List PartMap)"),
    },
    {
        "id": "uniq-last-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_LAST),
        "refinement": (
            "Correct on every position EXCEPT the LAST, which is overwritten with the "
            "empty state. The faithful real analogue mis-records the FINAL produced "
            "state, so the last row of every materialized list is wrong and the F2P "
            "element-by-element comparison fails there — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C2) at the single sub-domain i == states.length - 1, "
            "the LARGEST index the clause's `i < states.length` guard admits, while "
            "satisfying it at every smaller i. The upper-boundary partner of "
            "uniq-partial-first-element (which pins i == 0): an off-by-one weakening "
            "of the guard itself — `i < states.length - 1`, or `i + 1 < "
            "states.length` — would leave the final position entirely unpinned and is "
            "invisible to every other rival here. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # last produced state non-empty, so `set (length-1) []` changes it.
        "witness": _wit("([[(4,2)], [(2,1),(3,2)]] : List PartMap)"),
    },
    {
        "id": "uniq-middle-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_MIDDLE),
        "refinement": (
            "Correct on the first and last positions but wrong at an INTERIOR one, "
            "which is overwritten with the empty state. The faithful real analogue "
            "mis-records a produced state in the MIDDLE of a run, so the materialized "
            "list is right at both ends and wrong in between; the F2P "
            "element-by-element comparison fails at that row — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C2) at an INTERIOR index. Added by audit: the shipped "
            "battery pinned (C2) only at the two BOUNDARY indices (i==0 via "
            "uniq-partial-first-element, i==states.length-1 via uniq-last-position), so "
            "a guard weakened to admit only the endpoints — `i = 0 ∨ i = "
            "states.length - 1`, the shape a hand-written boundary check takes — would "
            "satisfy every other case in this battery and fail only here. Witness "
            "rebuilt by audit: elaborates against the rival (exit 0), fails on the "
            "frozen solution (exit 1) with `decide` DECIDING the claim false, and the "
            "flipped-claim forgery inverts both exits. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # 3 states, all distinct; `set 1 []` changes ONLY the interior position.
        "witness": _wit("([[(4,2)], [(2,1),(3,2)], [(1,6)]] : List PartMap)"),
    },
    {
        "id": "uniq-intra-partition-key-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_KEYORDER),
        "refinement": (
            "Every position holds the right partition with the right multiset of "
            "(part-value, multiplicity) pairs, but the pairs INSIDE each entry are "
            "reversed. The faithful real analogue materializes each produced partition "
            "with its key order rebuilt the wrong way round; since mapping.md binds the "
            "generator's key order (largest→smallest) into the modeled value, the F2P "
            "comparison against the expected partitions fails — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C2): the entry at position 0 is the produced "
            "partition's pair list REVERSED, not the produced partition. Added by "
            "audit: every other rival in this battery permutes, drops or replaces WHOLE "
            "entries, so all of them are caught by a spec that compared entries as "
            "SETS/MULTISETS of pairs; this is the only case pinning the entry's "
            "INTERNAL order, which mapping.md declares part of the modeled value. "
            "Witness rebuilt by audit: exit 0 on the rival, exit 1 on the frozen "
            "solution with `decide` deciding it false, forgery inverts both. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # a single 2-pair partition: reversal changes the entry and nothing else.
        "witness": _wit("([[(1,2),(2,2)]] : List PartMap)"),
    },
    {
        "id": "uniq-dedup-repeated-states",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_DEDUP),
        "refinement": (
            "Collapses ADJACENT EQUAL produced states into a single entry. Agrees with "
            "the frozen impl on every sequence of pairwise-distinct states. The "
            "faithful real analogue silently merges consecutive equal produced states, "
            "so a consumer draining a run that repeats a state gets one entry where it "
            "should get two and the F2P count/list assertion fails — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C1) result.length = states.length on the REPEATED-STATE "
            "sub-domain (length 1, not 2). Added by audit: every other witness in this "
            "battery is stated at pairwise-DISTINCT states, so this rival agrees with "
            "the frozen impl on every input the rest of the battery uses — a spec "
            "quantified only over distinct-state sequences, or one pinning entries only "
            "up to deduplication, would satisfy the whole rest of the battery and fail "
            "only here. Nothing in the modeled carrier makes consecutive produced "
            "states distinct, so the sub-domain is consumer-reachable. Witness rebuilt "
            "by audit: exit 0 on the rival, exit 1 on the frozen solution with `decide` "
            "deciding it false, forgery inverts both. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # two EQUAL produced states: the one sub-domain this rival diverges on.
        "witness": _wit("([[(1,6)], [(1,6)]] : List PartMap)"),
    },
    {
        "id": "uniq-empty-sequence-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _REJ_EMPTY),
        "refinement": (
            "Agrees with the frozen impl on every non-empty produced sequence, and "
            "emits one spurious entry when the generator produced nothing at all. The "
            "faithful real analogue is a materialization that manufactures a bogus "
            "entry for an empty run, so a consumer draining a generator that yields "
            "nothing gets a one-element list instead of an empty one — the F2P "
            "assertion on that shape fails, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (C1) at the DEGENERATE sub-domain states == [] "
            "(length 1, not 0), while agreeing with the frozen impl everywhere else. "
            "Every other case in this battery states its refutation at length >= 1, "
            "so a spec quantifying only over non-empty carriers — or one whose length "
            "clause was stated as an inequality that happens to hold at 0 — would "
            "satisfy the entire rest of the battery and fail only here. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # the empty produced sequence: the one input this rival diverges on.
        "witness": _wit("([] : List PartMap)"),
    },
]


# No @ContractOnly axioms and no opaque callees: the materialization is modeled
# DEEPLY (position-wise) over the transparent `List PartMap` carrier, so the axiom
# lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []

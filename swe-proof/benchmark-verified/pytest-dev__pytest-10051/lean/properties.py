# properties.py — G-PBT falsification battery for pytest-dev__pytest-10051 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a positive that reproves, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   clear(s) : empty a collector TOTALLY — its backing list AND the rendered account
#   it feeds — WITHOUT detaching the views already coupled to it. The model is a tiny
#   heap: `cells` is the set of live backing-list objects, `records` is the reference
#   (an index) the collector reads, `callView` is the reference a previously-taken
#   view reads, and `transcript` is the rendered account, a sink read directly rather
#   than through any reference. The precondition of
#   the obligation is that the collector's reference is live (records < cells.length)
#   AND the view was taken onto the collector's current cell (callView = records).
#   The single postcondition `problem_spec_clear` pins the resulting state exactly,
#   over the four input binders (cells / records / callView / transcript), with SEVEN
#   top-level clauses (seven clauses, but NOT seven independent ones — see the
#   REDUNDANCY note below, which is machine-checked):
#     (1) result.records  = s.records          — the collector's reference is unchanged
#         (the emptying is IN PLACE, not a reallocation that repoints it);
#     (2) result.callView = s.callView         — the view reference is untouched;
#     (3) result.cells.length = s.cells.length — no cell is allocated or discarded;
#     (4) result.cells[result.records]? = some []   — the referenced cell is PRESENT
#         and empty (addressed by identity via getElem?, so a present-empty cell is
#         never confused with an absent one);
#     (5) result.cells[result.callView]? = some []  — a coupled view still observes
#         that present, empty cell (the load-bearing behaviour the system relies on);
#     (6) ∀ i ≠ s.records, result.cells[i]? = s.cells[i]?  — every OTHER cell is
#         unchanged, identity-for-identity (frame);
#     (7) result.transcript = []                     — the rendered account reads
#         empty afterwards, so a reader consulting the transcript DIRECTLY observes
#         nothing the collector had recorded. Only the sink's CONTENTS are pinned,
#         never its identity or the route by which it comes to read empty (nothing
#         holds a reference into it, so identity is not observable) — which is why
#         pos-takedrop-reshape may empty it by truncation instead of by installing a
#         fresh sink and must still verify.
#   Every clause is a total transparent function of the inputs (List / Nat, no opaque
#   callee, no answer-key oracle), so a witness can state the spec at a concrete
#   literal heap and needs no conditioning on the carrier.
#
# REDUNDANCY / DETERMINACY (measured, not argued — an audit re-derived both as
# real Lean proofs against the frozen preamble, exit 0):
#   * The spec is FUNCTIONALLY DETERMINATE on its precondition domain: from
#     `problem_spec_clear s r` plus (records < cells.length, callView = records) it
#     follows that `r = { s with cells := s.cells.set s.records [], transcript := [] }`
#     — proved by
#     `List.ext_getElem?` on clauses (1)+(4)+(6) and clause (7) for the sink, then
#     destructuring `r`. So the
#     postcondition admits EXACTLY ONE result state per legal input. The practical
#     consequence for this battery: SPEC-TOO-WEAK is unreachable here. No rival, of
#     any shape, can verify — the spec pins the answer rather than merely
#     constraining it. The reject lane therefore certifies witness DISCRIMINATION
#     (each rival provably violates the spec at a stated input), which is the honest
#     claim, and not "the spec was strong enough to notice", which determinacy
#     already settles a priori.
#   * Clause (3) is IMPLIED by (1)+(4)+(6) (same ext_getElem? argument, then
#     `List.length_set`). Clause (5) is IMPLIED by (1)+(2)+(4) under the
#     precondition callView = records. So neither (3) nor (5) can be violated in
#     isolation, and no rival can be written that isolates them. An earlier draft of
#     this header claimed `grow` "isolates clause (3)"; that claim was false and is
#     corrected below.
#
# BINDER / CLAUSE COVERAGE (what the reject lane exercises). The failure sets below
# were MEASURED by evaluating the six clauses at each rival's own witness input
# (a decidable #eval table, exit 0), not inferred from the impl's shape:
#   * `noop` (does nothing) fails (4)+(5) at ⟨[[7]],0,0⟩ — the referenced cell is
#     not emptied, and the coupled view therefore observes the un-emptied cell.
#   * `rebind` — the PRE-PATCH shape (reallocate a fresh empty cell and repoint
#     `records` at it) — fails (1)+(3)+(5)+(6) at ⟨[[3],[9]],1,1⟩: the reference
#     changes, the heap grows, the coupled view is orphaned on the old populated
#     cell, and the frame leg fails too because the reallocation makes a previously
#     ABSENT index present.
#   * `grow` (empty the right cell BUT also allocate a spurious cell) fails (3)+(6)
#     at ⟨[[7]],0,0⟩ — NOT (3) alone: the appended cell makes index 1 present where
#     it was absent, so the frame leg fails with it. (3) cannot be isolated at all;
#     see the REDUNDANCY note.
#   * `callview-touch` (empty correctly but bump the view reference) fails (2)
#     ALONE at ⟨[[7],[]],0,0⟩ — the bump lands on a PRESENT-EMPTY bystander cell, so
#     clause (5) still holds and clause (2) is the single failing leg. This is a
#     genuine isolation of the view-reference leg, and it is why the witness point
#     carries that trailing empty cell rather than the length-1 heap an earlier
#     draft used (at ⟨[[7]],0,0⟩ the bump runs off the end and (5) fails too).
#   * `frame` (empty the referenced cell AND clobber a DIFFERENT cell) fails (6)
#     ALONE at ⟨[[1],[4]],0,0⟩ — the only true single-clause isolation besides
#     callview-touch, and the one the frame leg needs.
#   * `clear-then-rebind` (do the real in-place empty, THEN reallocate/repoint)
#     fails (1)+(3)+(6) at ⟨[[5],[8]],0,0⟩. Note clause (5) HOLDS here, unlike in
#     `rebind`: the in-place empty happened first, so the orphaned view observes a
#     present-empty cell. An earlier draft claimed (5) among its failures; corrected.
#   * `reseat-reference` (empty the referenced cell in place — contents correct —
#     but re-seat `records` onto the heap's last cell) fails (1) ALONE at
#     ⟨[[7],[]],0,0⟩. Added by the audit: no shipped rival isolated clause (1), the
#     load-bearing reference-preservation leg, and (1) is the one clause the
#     determinacy proof consumes that a single-clause rival can actually reach.
#   * `tail-reseat` (empty the referenced cell in place BUT re-seat `records` DOWN
#     onto index 0) fails (1) ALONE at ⟨[[],[4],[7]],2,2⟩ — see its own note.
#   * `tail-reseat` (empty the referenced cell in place BUT re-seat `records` onto
#     index 0) fails (1) ALONE at ⟨[[1],[2],[9]],2,2⟩. Added by the second audit to
#     supply the probe point the header previously CLAIMED but did not carry: it is
#     the only reject case at heap length 3, and the only one at records = 2 (an
#     INTERIOR-to-last index rather than 0 or 1). It also witnesses the clause-(1)
#     break in the opposite direction from reseat-reference (downward re-seat onto a
#     POPULATED cell, not upward onto an empty one), so the isolation of clause (1)
#     no longer rests on a single re-seat direction or a single heap shape.
#   The reject witnesses vary `records` (0, 1 and 2) and `cells` (input heaps of
#   length 1, 2 and 3, with distinct contents) across SIX distinct input points, so
#   no binder is pinned at one value by every rival. (Corrected by the second audit:
#   the header previously claimed input heaps of "length 1, 2, 3" when every shipped
#   witness probed a length-1 or length-2 heap and records was only ever 0 or 1 — a
#   coverage claim the manifest did not carry. `tail-reseat` was added to make the
#   claim true rather than the claim weakened to match.) The `callView` binder is NOT
#   independently varied: the obligation's precondition FORCES callView = records
#   (the view is taken onto the collector's current cell — the setup aliasing), so
#   within the modeled domain clause (5) is implied by (1)+(2)+(4) and callView
#   cannot range free of records. That is a genuine domain constraint, not a
#   coverage gap — see 'assessment'.
#
# NAGINI CASES AND HOW THEY PORT (see 'assessment' in the submitted payload):
#   * S1/S5 positive controls → pos-closed-form / pos-do-selfrebind, KEPT as cheap
#     controls, plus `pos-takedrop-reshape` added by the audit. The first two are
#     honest but WEAK: an audit checked `fun _ => rfl` and both are DEFINITIONALLY
#     EQUAL to the frozen impl (a `do`-block over one `List.set` reduces to the
#     closed form, and a self-rebind `records := records` is the identity), so
#     neither can detect a postcondition over-fit to the frozen impl's syntactic
#     form — the very thing a soundness positive exists to detect. The added
#     take/drop positive is NOT definitionally equal (the same `rfl` check FAILS on
#     it) and needs a real rewrite step to close, so it is the case that actually
#     bears the SPEC-TOO-STRONG weight.
#   * S2 rebind-orphans → `rebind` (the prepatch shape; here it is exactly
#     Solution_prepatch.lean's impl).
#   * S3 clear-then-rebind → `clear-then-rebind`.
#   * S4 no-op → `noop`.
#   * S6 wrongval-append / S7 rebind-append → the append-then-visible function is NOT
#     modeled in this bundle (carrier narrowing: the lean bundle contracts only the
#     purely functional `clear` core, one `theorem correct_*`). No counterpart; OMITTED.
#   * S8 self-recursion / S9 empty-then-recurse (divergence) → nothing to ship, but
#     an earlier draft's REASON ("a diverging implementation cannot be written at
#     all") is wrong and is corrected here. An audit wrote one: `partial def
#     implementation_clear s := implementation_clear s` elaborates fine and passes
#     variant_scope. It does not verify, and not for a termination reason — a
#     `partial def` is compiled to an opaque constant, so the frozen proof's
#     `unfold implementation_clear` fails ("Tactic `unfold` failed to unfold"), i.e.
#     the obligation becomes unprovable rather than vacuously true. Lean's total
#     `def` elaborator is what forecloses the vacuous-verify shape that
#     `loom.semantics.termination "partial"` would otherwise admit on the velvet
#     carrier, which is why those bundles carry an explicit total-semantics
#     obligation. Disposition unchanged (nothing to ship); the reason is now the
#     measured one.
#   * Frame/permission mutation (nagini's fractional-permission class) → nagini calls
#     it non-applicable there (no half-permission input). Lean is referentially
#     transparent, so "store into a read-only alias" is not expressible EITHER — but
#     the lean spec carries its OWN explicit frame clause (6), which IS attackable by a
#     value-level rival, so this port ADDS the `frame` reject that nagini could not.
#   * AXIOM_TESTS → dropped; the axiom lane is G-AX's job and this gate ignores them.
#     (The operation is modeled DEEPLY over the heap carrier, so there is no consumed
#     axiom anyway — mapping.md: G-AX skips.)
#   * ADMISSIBILITY LANE → the port shipped none and recorded no reason, and the first
#     audit's omission review did not raise it either. That is an UNDERPORT, not a
#     vacuous class: the nagini sibling carries the admissibility assertion embedded in
#     both of its positive controls (`Assert(view is buf.items)`, explicitly labelled
#     "admissibility: precond delivered the alias"), and the frozen obligation here is
#     GUARDED by two hypotheses, so the direction is live. Landed by the second audit as
#     `admiss-f2p-shaped-input`, which discharges both preconditions AND the six-clause
#     postcondition at a concrete F2P-shaped state by evaluation, ahead of the frozen
#     obligation, and verifies. Note the reason "the frozen obligation has no
#     precondition" would not have applied here in any case — this one has two.
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10051"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------
# The single in-place-empty line of the gold impl body. It lies ENTIRELY inside
# the impl region and is unique in the file. Rivals that keep the do-block shape
# swap this line; rivals/positives that reshape the whole impl swap _IMPL_DEF.
_SET_LINE = "  st := { st with cells := st.cells.set st.records [] }"
assert _BASE.count(_SET_LINE) == 1, "set-line anchor drifted"

# The transcript-discarding line of the gold impl body. Also entirely inside the
# impl region and unique. Rivals that attack the transcript clause swap THIS line
# (or drop it); rivals attacking the heap clauses swap _SET_LINE and leave it, so
# the two attack surfaces stay independently addressable.
_TRANSCRIPT_LINE = "  st := { st with transcript := [] }"
assert _BASE.count(_TRANSCRIPT_LINE) == 1, "transcript-line anchor drifted"

# The full frozen impl def — swapped by variants that reshape the whole body.
_IMPL_DEF = (
    "def implementation_clear (s : HandlerState) : HandlerState := Id.run do\n"
    "  let mut st := s\n"
    "  -- Empty the contents of the collector's current backing list in place,\n"
    "  -- keeping the same reference; views onto it stay coupled.\n"
    "  st := { st with cells := st.cells.set st.records [] }\n"
    "  -- Discard the rendered account as well, so nothing the collector recorded\n"
    "  -- stays readable through the transcript either.\n"
    "  st := { st with transcript := [] }\n"
    "  return st"
)
assert _BASE.count(_IMPL_DEF) == 1, "impl-def anchor drifted"

# The full frozen proof body — swapped only by the positive that reproves with a
# non-do impl (no `show` normalization needed there).
_PROOF_BODY = (
    "  intro s hlt hview\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  show s.records = s.records ∧ s.callView = s.callView ∧\n"
    "    (s.cells.set s.records []).length = s.cells.length ∧\n"
    "    (s.cells.set s.records [])[s.records]? = some [] ∧\n"
    "    (s.cells.set s.records [])[s.callView]? = some [] ∧\n"
    "    (∀ i, i ≠ s.records → (s.cells.set s.records [])[i]? = s.cells[i]?) ∧\n"
    "    ([] : List Nat) = []\n"
    "  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩\n"
    "  · exact List.length_set\n"
    "  · rw [List.getElem?_set_self]\n"
    "    simp [hlt]\n"
    "  · rw [hview, List.getElem?_set_self]\n"
    "    simp [hlt]\n"
    "  · intro i hi\n"
    "    rw [List.getElem?_set_ne (Ne.symm hi)]"
)
assert _BASE.count(_PROOF_BODY) == 1, "proof-body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-closed-form: the cheapest HONEST impl — a non-`do` closed form that empties
# the referenced cell in place with the same List.set, so the output equals the
# frozen impl's on every input. The obligation statement is byte-identical; the
# reproof drops the `show` (no do-block to normalize) and closes the six legs with
# the same lemmas. MUST verify; else SPEC-TOO-STRONG (postcondition over-fit to the
# do-block syntactic shape).
_POS_CLOSED = _swap(
    _swap(
        _BASE,
        _IMPL_DEF,
        "def implementation_clear (s : HandlerState) : HandlerState :=\n"
        "  { s with cells := s.cells.set s.records [], transcript := [] }",
    ),
    _PROOF_BODY,
    "  intro s hlt hview\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩\n"
    "  · exact List.length_set\n"
    "  · rw [List.getElem?_set_self]\n"
    "    simp [hlt]\n"
    "  · rw [hview, List.getElem?_set_self]\n"
    "    simp [hlt]\n"
    "  · intro i hi\n"
    "    rw [List.getElem?_set_ne (Ne.symm hi)]",
)

# pos-do-selfrebind: a do-block variant with a harmless intermediate rebind of the
# local state to itself (records := records) before the in-place empty. Reduces to
# the same List.set, so it is correct on every input; the frozen proof body (with
# its `show` normalization) still closes on the byte-identical obligation. A faithful
# restructure — no reproof needed, no new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG.
#
# CAVEAT (audit, machine-checked): like pos-closed-form, this impl is
# DEFINITIONALLY EQUAL to the frozen one — `example : ∀ s, implSelfRebind s =
# implGold s := fun _ => rfl` elaborates. Both are kept as cheap controls (they do
# confirm the obligation is not tied to the literal frozen TEXT), but neither can
# detect a spec over-fit to the frozen impl's reduction behaviour, because there is
# nothing for the spec to be over-fit AGAINST. _POS_TAKEDROP below is the positive
# that carries real SPEC-TOO-STRONG weight.
_POS_SELFREBIND = _swap(
    _BASE,
    "  let mut st := s\n"
    "  -- Empty the contents of the collector's current backing list in place,\n"
    "  -- keeping the same reference; views onto it stay coupled.\n"
    "  st := { st with cells := st.cells.set st.records [] }\n",
    "  let mut st := s\n"
    "  st := { st with records := st.records }\n"
    "  st := { st with cells := st.cells.set st.records [] }\n",
)
assert _TRANSCRIPT_LINE in _POS_SELFREBIND, "selfrebind lost the transcript discard"

# pos-takedrop-reshape (ADDED by the audit): a genuinely non-definitionally-equal
# correct impl. It rebuilds the heap as `take records ++ [] :: drop (records+1)`
# instead of calling List.set. Same result on every precondition-legal input, but
# `fun _ => rfl` does NOT close the equality with the frozen impl (checked: the
# `rfl` build FAILS), so the frozen proof body cannot survive either — the reproof
# must first bridge the shapes with `List.set_eq_take_cons_drop`, then close the six
# legs with the SAME lemmas the frozen proof uses (length_set, getElem?_set_self,
# getElem?_set_ne). No new axiom/lemma/sorry, obligation statement byte-identical.
# This is the case that actually tests SPEC-TOO-STRONG: if a postcondition were
# over-fit to `List.set`'s reduction behaviour rather than to the STATE it produces,
# this faithful reshape would be rejected. It verifies (measured, exit 0).
_POS_TAKEDROP = _swap(
    _swap(
        _BASE,
        _IMPL_DEF,
        "def implementation_clear (s : HandlerState) : HandlerState :=\n"
        "  { s with\n"
        "      cells := s.cells.take s.records ++ [] :: s.cells.drop (s.records + 1),\n"
        "      transcript := s.transcript.take 0 }",
    ),
    _PROOF_BODY,
    "  intro s hlt hview\n"
    "  unfold problem_spec_clear implementation_clear\n"
    "  rw [← List.set_eq_take_cons_drop _ hlt]\n"
    "  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, ?_⟩\n"
    "  · exact List.length_set\n"
    "  · rw [List.getElem?_set_self hlt]\n"
    "  · rw [hview, List.getElem?_set_self hlt]\n"
    "  · intro i hi\n"
    "    rw [List.getElem?_set_ne (Ne.symm hi)]\n"
    "  · simp",
)


# ===========================================================================
# ADMISSIBILITY (PRECOND-TOO-STRONG) — must VERIFY.
# ===========================================================================
# admiss-f2p-shaped-input (ADDED by the second audit): the lane the port dropped
# ENTIRELY and recorded no reason for. The frozen obligation is guarded by two
# hypotheses (records < cells.length, callView = records), so on this total carrier
# the PRECOND-TOO-STRONG failure mode is the obligation being UNSATISFIABLE — or
# satisfiable only vacuously — at exactly the input shape the reported behaviour is
# about. This case tests that directly and by EVALUATION, not by argument: keeping
# the frozen impl AND the entire frozen proof body verbatim, it inserts two `have`s
# ahead of the frozen proof, at the concrete state ⟨[[7],[4]], 0, 0⟩ —
#
#   * hadm_pre  : the two preconditions HOLD at that state, discharged by `decide`
#                 (so the guard actually ADMITS the input rather than excluding it);
#   * hadm_post : the postcondition HOLDS there of the frozen impl's own output,
#                 discharged by reduction (`rfl` on the five positional legs and a
#                 case split on the index for the universally-quantified frame leg).
#
# The input is F2P-shaped in every modeled respect: a collector whose backing list is
# NON-EMPTY (one recorded entry) with a view coupled to it (callView = records = 0),
# alongside a POPULATED BYSTANDER cell that must survive untouched — that bystander is
# the modeled counterpart of the other phase's view, which the behaviour under test
# asserts is unaffected by the clear. If the precondition were over-strong at that
# point, `decide` on hadm_pre would fail; if the postcondition were unsatisfiable
# there, hadm_post would not reduce. Neither is a consequence of the frozen proof
# closing: the frozen proof establishes an IMPLICATION, which holds vacuously at any
# input the guard excludes, so this case is the only one in the battery that shows the
# guarded domain is non-empty at a behaviourally relevant point. Adds no
# axiom/lemma/sorry and leaves the obligation statement byte-identical.
_ADMISS_STATE = "{ cells := [[7], [4]], records := 0, callView := 0, transcript := [7] }"
_ADMISS_HAVES = (
    "  -- ADMISSIBILITY at an F2P-shaped input, discharged BEFORE the general\n"
    "  -- obligation: a view coupled to a NON-EMPTY collector (cell 0 holds one\n"
    "  -- recorded entry) alongside a POPULATED bystander cell that must survive,\n"
    "  -- and a NON-EMPTY transcript standing for an account already rendered.\n"
    f"  have hadm_pre :\n"
    f"      ({_ADMISS_STATE} : HandlerState).records <\n"
    f"        ({_ADMISS_STATE} : HandlerState).cells.length ∧\n"
    f"      ({_ADMISS_STATE} : HandlerState).callView =\n"
    f"        ({_ADMISS_STATE} : HandlerState).records := by\n"
    "    decide\n"
    f"  have hadm_post :\n"
    f"      problem_spec_clear {_ADMISS_STATE}\n"
    f"        (implementation_clear {_ADMISS_STATE}) := by\n"
    "    unfold problem_spec_clear implementation_clear\n"
    "    refine ⟨rfl, rfl, rfl, rfl, rfl, ?_, rfl⟩\n"
    "    intro i hi\n"
    "    match i, hi with\n"
    "    | 0, hi => exact absurd rfl hi\n"
    "    | (n + 1), _ => rfl\n"
)
_POS_ADMISS = _swap(
    _BASE,
    "  intro s hlt hview\n",
    "  intro s hlt hview\n" + _ADMISS_HAVES,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for a reshaped impl, but the gate reads the WITNESS — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# noop: does nothing — leaves the collector's cell holding its pre-existing records.
# Attacks clause (4): the referenced cell is not emptied.
_RIV_NOOP = _swap(_BASE, _SET_LINE, "  st := st")

# rebind: the PRE-PATCH bug verbatim — reallocate a fresh empty cell and repoint the
# collector's reference at it, leaving every view naming the old (still-populated)
# cell. Attacks clauses (1) records changed, (3) heap grew, (5) view orphaned.
_RIV_REBIND = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := st.cells ++ [[]], records := st.cells.length }")

# grow: empty the RIGHT cell in place (references intact) but also allocate a
# spurious extra cell. Attacks the ALLOCATION legs: clauses (3) and (6) fail together
# (the appended cell makes a previously ABSENT index present), while (1)/(2)/(4)/(5)
# hold. It does NOT "isolate clause (3)" — that is impossible, since (3) is a
# consequence of (1)+(4)+(6); see the REDUNDANCY note. (Stale comment corrected by
# the second audit: it still asserted the isolation the case's own rationale
# explicitly retracts.)
_RIV_GROW = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := (st.cells.set st.records []) ++ [[]] }")

# callview-touch: empty the referenced cell correctly but bump the view reference.
# Attacks clause (2): the operation must not touch the views.
_RIV_CALLVIEW = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := st.cells.set st.records [], callView := st.callView + 1 }")

# frame: empty the referenced cell AND clobber a DIFFERENT cell to empty. Does the
# work but disturbs a bystander backing-list object. Attacks clause (6) (frame).
_RIV_FRAME = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := (st.cells.set st.records []).set (st.records + 1) [] }")

# clear-then-rebind: empty in place (the real work) and THEN reallocate/repoint —
# observationally identical to `rebind` from the collector's side. Fails clauses
# (1)+(3)+(6) at its witness point (measured); clause (5) HOLDS here, because the
# in-place empty ran first, so the stranded view observes a present-empty cell.
_RIV_CTR = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := (st.cells.set st.records []) ++ [[]], records := st.cells.length }")

# reseat-reference (ADDED by the audit): empty the referenced cell IN PLACE — so the
# CONTENTS are right on every input and the heap keeps its exact size — but re-seat
# the collector's reference onto the heap's last cell. Fails clause (1) ALONE at
# ⟨[[7],[]],0,0⟩ (measured), which no shipped rival did: every other reference-leg
# rival (`rebind`, `clear-then-rebind`) also grows the heap, so clauses (3) and (6)
# fail alongside (1) and the rejection could be attributed to allocation rather than
# to reference preservation. Clause (1) is the load-bearing leg for this bundle's
# behaviour, and it is one of only three clauses a single-clause rival can reach
# (see the REDUNDANCY note), so it deserves an isolating rival.
_RIV_RESEAT = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := st.cells.set st.records [],\n"
    "                  records := st.cells.length - 1 }")

# tail-reseat (ADDED by the second audit): the same clause-(1) break as
# reseat-reference but in the opposite DIRECTION — empty the referenced cell in place
# (contents right, heap size exact) and re-seat the collector's reference DOWN onto
# index 0 instead of up onto the last cell. Its witness is the battery's only probe at
# heap length 3 and its only probe at records = 2, which is the input variation the
# header claimed and no shipped witness supplied. Witness point ⟨[[],[4],[7]],2,2⟩:
# index 0 is PRESENT-EMPTY there, so clause (4) still holds of the re-seated reference
# and MEASURED FAILS=[1] ALONE. (Measured, not assumed: at a populated index 0 —
# e.g. ⟨[[1],[2],[9]],2,2⟩ — the re-seated reference names a non-empty cell and the
# failure set is (1)+(4), which would NOT isolate the reference leg.)
_RIV_TAILRESEAT = _swap(
    _BASE, _SET_LINE,
    "  st := { st with cells := st.cells.set st.records [], records := 0 }")

# retain-transcript (ADDED by the spec repair): does the records-side work
# PERFECTLY — the referenced cell is emptied in place, every reference is
# preserved, the heap keeps its exact size, no bystander is touched — but leaves
# the rendered account standing. Clauses (1)-(6) all hold; only clause (7) fails.
#
# This is the rival the previous spec ADMITTED, and admitting it is what made the
# cell a verify⇏correct counterexample: the collector's own contents and all the
# aliasing are right, so every heap-side clause is satisfied, yet a reader that
# consults the transcript directly still observes everything recorded before the
# clear. Emptying a collector has to be TOTAL — no surviving route to the
# discarded entries — and clause (7) is what says so.
_RIV_RETAIN = _swap(_BASE, _TRANSCRIPT_LINE, "  st := st")


def _wit_simp(cells, records, callView, note, transcript="[5]"):
    """Witness that refutes a rival by `simp` at a concrete literal heap. Elaborates
    against a rival that violates the spec there and FAILS on gold (which satisfies
    the spec at every precondition-legal input). No head binders → no consistency
    probe needed.

    Every witness point carries a NON-EMPTY `transcript`. That is load-bearing for
    the transcript clause (7) — at an already-empty transcript a rival that never
    touches the sink satisfies (7) vacuously (MEASURED: failure set is empty at
    ⟨[[7]],0,0,[]⟩) — and inert for the heap clauses, whose measured failure sets
    are unchanged by it."""
    st = (f"{{ cells := {cells}, records := {records}, callView := {callView},"
          f" transcript := {transcript} }}")
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_clear\n"
        f"    {st}\n"
        f"    (implementation_clear {st}) := by\n"
        f"  unfold problem_spec_clear implementation_clear\n"
        f"  simp"
    )


# frame needs to attack clause (6) at a specific bystander index; `simp` alone
# leaves an existential, so extract clause 6 at i = records+1 and refute it there.
# NOTE the projection path: with SEVEN clauses, `h.2.2.2.2.2` is the (6 ∧ 7) pair,
# so clause (6) — the universally-quantified frame leg — is reached by a trailing
# `.1`. Getting this wrong would refute the TRANSCRIPT leg instead and silently
# stop attributing the rejection to the frame.
def _wit_frame(cells, records, callView, idx, note, transcript="[5]"):
    st = (f"{{ cells := {cells}, records := {records}, callView := {callView},"
          f" transcript := {transcript} }}")
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_clear\n"
        f"    {st}\n"
        f"    (implementation_clear {st}) := by\n"
        f"  unfold problem_spec_clear implementation_clear\n"
        f"  intro h\n"
        f"  have h6 := h.2.2.2.2.2.1 {idx} (by decide)\n"
        f"  simp at h6"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CLOSED,
        "rationale": (
            "structurally-different but CORRECT impl: a non-`do` closed form that "
            "empties the referenced cell with the same in-place List.set, equal to the "
            "frozen impl on every input. The `theorem correct_clear` statement is "
            "byte-identical; the reproof drops the do-block `show` normalization and "
            "closes the six legs with the same lemmas (length_set, getElem?_set_self, "
            "getElem?_set_ne) — no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to the do-block syntactic shape)."
        ),
    },
    {
        "id": "pos-do-selfrebind",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SELFREBIND,
        "rationale": (
            "a do-block variant with a harmless intermediate rebind of the local state "
            "to itself (records := records) before the in-place empty; it reduces to the "
            "same List.set so it is correct on every input, and the FROZEN proof body "
            "still closes on the byte-identical obligation (the extra self-rebind is "
            "definitionally transparent). A faithful restructure, no reproof/axiom/lemma/"
            "sorry. If it FAILS => SPEC-TOO-STRONG. WEAK CONTROL, stated honestly: an "
            "audit checked `fun _ => rfl` and this impl is DEFINITIONALLY EQUAL to the "
            "frozen one, as is pos-closed-form, so neither can detect a spec over-fit "
            "to the frozen impl's reduction behaviour. pos-takedrop-reshape is the "
            "positive that carries the SPEC-TOO-STRONG weight."
        ),
    },
    {
        "id": "pos-takedrop-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TAKEDROP,
        "rationale": (
            "the SPEC-TOO-STRONG control that is not definitionally equal to gold: it "
            "rebuilds the heap as `take records ++ [] :: drop (records+1)` instead of "
            "calling List.set. Correct on every precondition-legal input (the resulting "
            "STATE is identical), but `fun _ => rfl` does NOT close the equality with the "
            "frozen impl — measured, that build fails — so the frozen proof body cannot "
            "close either: the reproof must bridge the two shapes with "
            "List.set_eq_take_cons_drop and only then discharge the six legs with the "
            "SAME lemmas the frozen proof uses. Obligation statement byte-identical, no "
            "new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the postcondition "
            "would be constraining HOW the cell is emptied rather than the state that "
            "results). It verifies (measured, exit 0)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADDED by the second audit: the battery shipped with NO admissibility "
            "case and no recorded reason, which silently removes the "
            "PRECOND-TOO-STRONG direction this gate exists to test (457 of the lean "
            "batteries in this corpus carry the lane). The frozen obligation IS "
            "guarded — records < cells.length and callView = records — so the lane is "
            "not vacuous here: the analogue of PRECOND-TOO-STRONG on a total carrier "
            "is the obligation being unsatisfiable, or satisfiable only vacuously, at "
            "exactly the input shape the reported behaviour is about. Keeping the "
            "frozen impl and the WHOLE frozen proof body verbatim, this variant adds "
            "two `have`s ahead of it at the concrete state ⟨[[7],[4]], 0, 0⟩: "
            "hadm_pre discharges BOTH preconditions by `decide` (the guard admits the "
            "input rather than excluding it), and hadm_post discharges the six-clause "
            "postcondition of the frozen impl's own output there by reduction (`rfl` "
            "on the five positional legs, an index case-split on the frame leg). That "
            "state is F2P-shaped in every modeled respect: a NON-EMPTY collector, a "
            "view coupled to it, and a POPULATED bystander cell standing for the "
            "other phase's view, which must survive the clear untouched. This is not "
            "implied by the frozen proof closing: the obligation is an IMPLICATION "
            "and holds vacuously at every input the guard excludes, so this is the "
            "only case in the battery that shows the guarded domain is inhabited at a "
            "behaviourally relevant point. If `decide` on hadm_pre FAILED => "
            "PRECOND-TOO-STRONG; if hadm_post did not reduce => the postcondition is "
            "unsatisfiable at the F2P shape. It verifies (measured, exit 0)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOOP,
        "refinement": (
            "a clear that does nothing keeps every reference intact but leaves the "
            "captured records in place. The F2P logs an entry before clearing and asserts "
            "the view observes NO records afterwards; a no-op clear leaves the pre-clear "
            "entry visible, so the faithful real patch does NOT resolve. A verifying no-op "
            "would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (4) result.cells[result.records]? = some [] on the "
            "non-empty sub-domain the F2P exercises: doing nothing leaves the pre-existing "
            "records in the referenced cell. Witness probes a length-1 heap with a "
            "non-empty cell at records = 0; MEASURED failure set there is (4)+(5) — the "
            "view leg fails with it, since the view is coupled to the same un-emptied "
            "cell. A verifying no-op would be SPEC-TOO-WEAK, though note the spec is "
            "provably determinate on its domain (see REDUNDANCY above), so what this "
            "case certifies is that the witness genuinely discriminates the no-op."
        ),
        "witness": _wit_simp("[[7]]", "0", "0",
                             "non-empty referenced cell: gold empties it, the no-op "
                             "leaves record 7 in place"),
    },
    {
        "id": "rebind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REBIND,
        "refinement": (
            "this is the PRE-PATCH shape: the collector is rebound to a freshly allocated "
            "empty backing list, so the per-phase view (bound to the collector's cell at "
            "setup) is orphaned — it keeps naming the OLD, still-populated list. The F2P "
            "asserts the view observes NO records after the clear AND observes a record "
            "logged AFTER the clear; with the reallocation the orphaned view still shows "
            "the pre-clear records and never sees the post-clear one, so the F2P FAILS. A "
            "verifying rebind is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (1) result.records = s.records (the reference changes), "
            "clause (3) result.cells.length = s.cells.length (a cell is allocated), and "
            "clause (5) the coupled view still observes some [] (the view is orphaned on "
            "the old populated cell). Witness probes a length-2 heap at records = 1 with a "
            "non-empty cell — a distinct input point from noop (varies records and cells). "
            "MEASURED failure set there is (1)+(3)+(5)+(6): clause (6) fails too, because "
            "the allocation makes a previously ABSENT index present, so the frame leg is "
            "violated as well. All four are genuine; the rejection is over-determined "
            "rather than attributable to any one leg, which is why the audit added "
            "reseat-reference to isolate clause (1)."
        ),
        "witness": _wit_simp("[[3], [9]]", "1", "1",
                             "reallocate + repoint: gold keeps reference 1 and empties it "
                             "in place; the rebind moves records to a fresh cell (length 3) "
                             "and leaves the view on the old populated cell"),
    },
    {
        "id": "grow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_GROW,
        "refinement": (
            "empties the right cell in place (references intact) but also allocates a "
            "spurious extra backing-list object. A patch that leaks an extra live list "
            "object per clear disturbs the heap invariant the surrounding system relies on "
            "(cells are addressed by identity); the count of live objects must be "
            "preserved, so the faithful real patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (3) result.cells.length = s.cells.length (the heap grows) "
            "AND clause (6), the frame leg. Clauses (1)/(2)/(4)/(5) do still hold "
            "(correct references, referenced cell empty, view coupled), so this separates "
            "the allocation legs from the reference legs — a rival mishandling only "
            "allocation. Witness probes a length-1 heap at records = 0; MEASURED failure "
            "set there is (3)+(6). CORRECTION: an earlier draft claimed clause (3) failed "
            "\"in isolation\" here. That is impossible — clause (3) is a LOGICAL "
            "CONSEQUENCE of (1)+(4)+(6) (proof re-derived by the audit, exit 0), so no "
            "rival can violate (3) while satisfying the other five, and in fact the "
            "spurious cell makes an absent index present, violating (6) too."
        ),
        "witness": _wit_simp("[[7]]", "0", "0",
                             "spurious allocation: gold keeps the heap at length 1, grow "
                             "leaves it at length 2"),
    },
    {
        "id": "callview-touch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CALLVIEW,
        "refinement": (
            "empties the referenced cell correctly but mutates the view reference itself. "
            "The clear operation must not touch the views it is meant to keep coupled; "
            "repointing a view to a different backing-list object detaches it from the "
            "collector, so a reader through that view no longer observes the collector's "
            "state. The faithful real patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2) result.callView = s.callView: the view reference is "
            "bumped. Witness probes a length-2 heap ⟨[[7],[]], 0, 0⟩ whose SECOND cell is "
            "present-and-empty, so the bumped view (0 → 1) lands on a present-empty cell "
            "and clause (5) still holds: MEASURED failure set is (2) ALONE, a genuine "
            "isolation of the view-reference leg. The audit CHANGED this witness point: "
            "the earlier ⟨[[7]],0,0⟩ length-1 heap bumped the view off the end of the "
            "heap, so clause (5) failed too (measured (2)+(5)) and the rationale's "
            "isolation claim was false — the rejection could have been read as 'the view "
            "now names no live object' rather than 'the view reference was touched'. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit_simp("[[7], []]", "0", "0",
                             "view reference bumped onto a PRESENT-EMPTY bystander cell: "
                             "gold leaves callView = 0, the rival moves it to 1, and that "
                             "is the only clause that fails"),
    },
    {
        "id": "frame",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FRAME,
        "refinement": (
            "empties the referenced cell (the real work) but ALSO clobbers a different, "
            "unrelated backing-list object. Emptying a bystander collector that a "
            "different view is coupled to silently strands that view's data; the clear "
            "must disturb only the target, so the faithful real patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (6) ∀ i ≠ s.records, result.cells[i]? = s.cells[i]? "
            "(frame): the cell at index records+1 is altered. Witness probes a length-2 "
            "heap at records = 0 with a non-empty bystander cell at index 1, and refutes "
            "clause (6) at that index (extracted directly, since the clause is universally "
            "quantified). MEASURED failure set at that point is (6) ALONE — a true "
            "single-clause isolation of the frame leg. If it VERIFIES => SPEC-TOO-WEAK "
            "(spec would tolerate collateral damage to bystander objects)."
        ),
        "witness": _wit_frame("[[1], [4]]", "0", "0", "1",
                              "bystander clobbered: gold leaves cell 1 = [4], the frame "
                              "rival empties it to []"),
    },
    {
        "id": "clear-then-rebind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CTR,
        "refinement": (
            "empties in place (the real work) but THEN reallocates and repoints the "
            "collector's reference at a fresh cell — observationally identical to the "
            "prepatch rebind: the live reference names a NEW object, so the "
            "previously-taken view is orphaned exactly as in `rebind` and the F2P FAILS "
            "(the post-clear record is never visible through the stale view). Doing the "
            "work and then discarding identity does not resolve the F2P."
        ),
        "rationale": (
            "REJECTED by clause (1) result.records = s.records, clause (3) "
            "result.cells.length = s.cells.length, and clause (6) the frame leg: the final "
            "reference is a fresh cell distinct from the original, the heap grew, and the "
            "allocation makes a previously absent index present. Witness probes a length-2 "
            "heap at records = 0 — a distinct input point from rebind (records = 1). "
            "MEASURED failure set is (1)+(3)+(6). CORRECTION: an earlier draft listed "
            "clause (5) among the failures. It does NOT fail here, and that is exactly "
            "what distinguishes this rival from `rebind`: because the in-place empty ran "
            "FIRST, the stranded view observes a present-EMPTY cell, so (5) holds while "
            "the reference identity is still lost. The behavioural break is real "
            "(the view is decoupled from the collector and never sees later entries) and "
            "the spec catches it on the reference/frame legs, not on the view-contents "
            "leg. Checked over records = 0..3 on a length-4 heap: the failure set is "
            "(1)+(3)+(6) at every point. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit_simp("[[5], [8]]", "0", "0",
                             "work-then-reallocate: gold keeps reference 0 and empties it; "
                             "the rival empties then moves records to a fresh cell (length "
                             "3), decoupling the view from the collector"),
    },
    {
        "id": "reseat-reference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RESEAT,
        "refinement": (
            "empties the collector's backing list IN PLACE — so the contents are right on "
            "every input and no object is allocated or discarded — but then re-seats the "
            "collector's own reference onto a DIFFERENT existing backing list. Every view "
            "already taken onto the collector is thereby decoupled from it: a reader "
            "through the view no longer observes what the collector observes, and entries "
            "recorded afterwards land on the newly-named object rather than the one the "
            "view holds. That is the same behavioural break the F2P asserts against (the "
            "view must still track the collector after the clear, including for entries "
            "recorded later), so a patch of this shape does NOT resolve it, even though "
            "it emptied the right list and leaked no objects."
        ),
        "rationale": (
            "ADDED by the audit to isolate clause (1) result.records = s.records — the "
            "reference-preservation leg, which is the load-bearing property of this "
            "bundle and which NO shipped rival isolated. `rebind` and `clear-then-rebind` "
            "both also grow the heap, so clauses (3) and (6) fail alongside (1) and their "
            "rejection is attributable to allocation as much as to reference identity. "
            "This rival keeps the heap length exactly, empties the referenced cell's "
            "contents, and touches nothing else: MEASURED failure set at ⟨[[7],[]],0,0⟩ "
            "is (1) ALONE. Witness probes that length-2 heap at records = 0. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec would permit the emptying to silently "
            "re-point the collector, which is the whole behaviour under test)."
        ),
        "witness": _wit_simp("[[7], []]", "0", "0",
                             "reference re-seated onto a different, already-empty cell: "
                             "gold keeps reference 0, the rival moves it to 1 while the "
                             "heap size and all cell contents are otherwise correct"),
    },
    {
        "id": "tail-reseat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TAILRESEAT,
        "refinement": (
            "empties the collector's backing list IN PLACE — contents right, no object "
            "allocated or discarded — but then re-seats the collector's own reference "
            "onto a DIFFERENT existing backing list, the first one in the heap. Every "
            "view already taken onto the collector is thereby decoupled: a reader "
            "through the view no longer observes what the collector observes, and "
            "entries recorded after the clear land on the newly-named object instead of "
            "the one the view holds. That is the behavioural break the F2P asserts "
            "against (the view must still track the collector across the clear, "
            "including for entries recorded afterwards), so a patch of this shape does "
            "NOT resolve it, even though it emptied the right list and leaked nothing."
        ),
        "rationale": (
            "ADDED by the second audit for INPUT COVERAGE, not for a new clause: the "
            "header claimed the reject witnesses ranged over heaps of length 1, 2 and 3 "
            "and over several `records` values, while every shipped witness in fact "
            "probed a length-1 or length-2 heap at records = 0 or 1. This case is the "
            "battery's only probe at heap length 3 and its only probe at records = 2, "
            "so the claim is now carried rather than asserted. It attacks clause (1) "
            "result.records = s.records in the OPPOSITE direction from "
            "reseat-reference (re-seat DOWN onto index 0 rather than UP onto the last "
            "cell), so the isolation of the reference-preservation leg no longer rests "
            "on one re-seat direction or one heap shape. Witness point "
            "⟨[[],[4],[7]],2,2⟩, where index 0 is PRESENT-EMPTY so the re-seated "
            "reference still names an empty cell and clause (4) holds: MEASURED "
            "failure set is (1) ALONE. Measured, not assumed — at a POPULATED index 0 "
            "(⟨[[1],[2],[9]],2,2⟩) the failure set is (1)+(4) and the isolation would "
            "be lost, which is why the witness carries the leading empty cell. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit_simp("[[], [4], [7]]", "2", "2",
                             "reference re-seated DOWN onto a different, already-empty "
                             "cell at a length-3 heap: gold keeps reference 2 and "
                             "empties it; the rival moves records to 0 while heap size "
                             "and every cell's contents are otherwise correct"),
    },
    {
        "id": "retain-transcript",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RETAIN,
        "refinement": (
            "does the records-side work PERFECTLY — empties the collector's backing "
            "list in place, preserves the collector's and the view's references, "
            "allocates and discards nothing, disturbs no bystander — but leaves the "
            "rendered account of what was recorded standing. A reader that consults "
            "the collector, or any view coupled to it, sees an empty collector; a "
            "reader that consults the running transcript directly still sees "
            "everything recorded before the clear. Emptying a collector is supposed "
            "to leave NO surviving route to the discarded entries, so a patch of this "
            "shape does NOT resolve the instance: it satisfies the aliasing behaviour "
            "the F2P asserts while a P2P reader of the transcript still observes the "
            "stale account."
        ),
        "rationale": (
            "ADDED by the spec repair, and it is the rival the previous spec "
            "ADMITTED — the recorded G-EQ / G-PANEL-1 counterexample. The earlier "
            "model carried no transcript component at all, so an impl that emptied "
            "the records store and nothing else satisfied every clause; its faithful "
            "refinement omits the captured-text reset and does not resolve the "
            "instance (F2P passes, a P2P reader of the captured text fails), which is "
            "exactly verify⇏correct. Clause (7) result.transcript = [] closes it: this "
            "rival satisfies clauses (1)-(6) in full and fails (7) ALONE — MEASURED at "
            "⟨[[7]],0,0,[5]⟩ and again at ⟨[[3],[9]],1,1,[2,4]⟩, so the isolation does "
            "not rest on one heap shape or one `records` value. The witness point must "
            "carry a NON-EMPTY transcript: MEASURED at ⟨[[7]],0,0,[]⟩ the failure set "
            "is EMPTY, because a rival that never touches an already-empty sink "
            "satisfies (7) vacuously. Clause (7) constrains only the sink's CONTENTS, "
            "never its identity or how it comes to read empty — pos-takedrop-reshape "
            "empties it by truncation rather than by installing a fresh sink and still "
            "verifies — so this rejection is attributable to the surviving account, "
            "not to a pinned implementation route. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit_simp("[[7]]", "0", "0",
                            "the collector is emptied in place and every reference is "
                            "preserved, but the rendered account survives: gold leaves "
                            "the transcript reading empty, the rival leaves entry 5 "
                            "readable through it",
                            transcript="[5]"),
    },
]


# No consumed @ContractOnly axioms and no opaque callees: the in-place empty and its
# reference-preserving semantics are modeled DEEPLY over the transparent heap carrier
# (List (List Nat) + Nat references), so the axiom lane is vacuous here and belongs to
# G-AX regardless.
AXIOM_TESTS = []

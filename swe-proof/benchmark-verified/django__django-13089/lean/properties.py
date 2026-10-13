"""properties.py — G-PBT falsification battery for django__django-13089 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant sharing the FROZEN spec byte-for-byte: region surgery
touches only text inside ``-- impl-start``/``-- impl-end`` and (for a case that
legitimately re-proves) inside ``-- proof-start``/``-- proof-end``, so
``markers.same_spec`` holds by construction and the ``theorem correct_cull``
STATEMENT stays byte-identical. ``expect:"verify"`` passes iff the case is in
scope AND the file elaborates with the obligation closed; ``expect:"reject"``
passes iff the case is in scope AND it does NOT verify AND its refutation
``witness`` holds of the rival while FAILING on the frozen solution.

DEFENDED SURFACE (one total function; one obligation, ``correct_cull``):

    cull (frequency : Nat) (capacity now : Int) (entries : List Entry)
        : Option (List Entry)

The spec pins the result for EVERY configuration, as a conjunction of clauses
guarded by disjoint conditions on the inputs. Writing ``remaining`` for
``keepUnexpired now entries`` (the records that have not expired at ``now``):

    (1) frequency = 0                     -> result = some []
    (2) frequency ≠ 0, |remaining| ≤ cap   -> result = some remaining
    (3) frequency ≠ 0, |remaining| > cap   -> result = some (
            match cullBoundary remaining (|remaining| / frequency) with
            | some k => keepAboveKey k remaining     -- (3a) boundary addressed
            | none   => remaining)                  -- (3b) no such position

Four INDEPENDENTLY ATTACKABLE decisions are folded into those clauses, and the
battery attacks each one separately:

  * WHETHER the whole store is discarded — clause (1), selected by ``frequency``
    alone. Attacked by ``weak-no-zero-frequency-case``.
  * WHICH records survive the first stage — ``remaining`` is pinned to the
    not-yet-expired records, so ``now`` and each record's ``expires`` are
    load-bearing in clauses (2) and (3) alike. Attacked by
    ``weak-skip-expiry-stage``.
  * WHETHER any culling happens at all — the ``|remaining| ≤ cap`` vs ``>``
    split between (2) and (3), selected by ``capacity``. Attacked by
    ``weak-cull-regardless-of-capacity``.
  * WHICH records the culling drops — inside (3), the boundary POSITION
    (``|remaining| / frequency``, so ``frequency`` is load-bearing a second
    time) and, decisively, the (3a)/(3b) SPLIT on whether the ordering has a
    record at that position. Attacked by ``weak-boundary-at-front-of-ordering``
    (wrong position), by ``weak-boundary-from-descending-order`` (right position,
    wrong ORDER — added by audit, because every other rival leaves the ascending
    ordering itself gold-shaped) and by the two (3b) rivals below.

Clause (3b) is the load-bearing one for this instance: when the boundary offset
lies at or beyond the number of survivors the ordering yields no key, and the
spec demands the store be left EXACTLY as it is. Two distinct wrong things an
implementation can do there are attacked separately —
``weak-absent-boundary-aborts`` (the pass does not complete) and
``weak-absent-boundary-empties-store`` (the pass completes but discards
everything). A third rival, ``weak-cull-arms-swapped``, attacks the (3a)/(3b)
SELECTOR rather than either arm's value: it is wrong on both arms at once, so
only a spec that pins WHICH arm applies refutes it. Added by audit, because every
other rival leaves one arm gold-shaped and so is individually refutable by a spec
that pinned only the arm under attack.

ADVERSARIAL READ of the nagini classes on this carrier. The nagini sibling
models a NARROWER surface: one function deciding only "is a prune issued, and
with what key" from an optional boundary row. Here the modeled surface is the
whole maintenance pass, so nagini's optional-row present/absent split appears as
the (3a)/(3b) split of clause (3) — nested inside the frequency and capacity
decisions, which nagini does not model at all and which are attacked here by
rivals that have no nagini counterpart.

  * PRECONDITION ADMISSION (nagini's ``admiss-present-and-absent``) — PORTED, not
    dropped, as ``admiss-ground-f2p-empty-store``. The frozen obligation is total
    and carries no precondition, so there is no ``Requires`` to establish; the
    analogue on a total carrier is that the obligation be SATISFIABLE at exactly
    an F2P-shaped input rather than vacuous or unreachable, which a positive that
    discharges the whole conjunction BY EVALUATION at that concrete point — as a
    ``have``, before closing the frozen obligation verbatim — tests directly. An
    earlier revision of this battery omitted the lane entirely; that omission was
    a real gap (it removes the PRECOND-TOO-STRONG direction from a gate that
    exists to test three), not an inexpressibility, and is repaired.

  * FRAME / PERMISSION MUTATION (nagini's mandatory class, because its input row
    is held read-only at fractional permission) — VACUOUS here. Lean is
    referentially transparent: ``entries`` is an immutable value, there is no
    half-permission to violate and no aliasing to overwrite, so a
    write-to-the-input rival cannot be written at all. No permission-violation
    substitute is fabricated. The SEMANTIC content of that obligation — "the
    read-only input is not silently rewritten into the answer" — survives as the
    spec's own pinning of ``remaining`` and of the (3b) leave-as-is clause, and
    both ARE attacked (``weak-skip-expiry-stage``,
    ``weak-absent-boundary-empties-store``).

  * DIVERGENCE / NON-TERMINATION — genuinely VACUOUS on lean, not a spec hole:
    ``implementation_cull`` is a total Lean ``def``, so a diverging rival cannot
    be expressed. (On velvet under partial termination semantics this class is a
    real spec hole; see the corpus-wide termination-semantics finding. That disposition does not
    transfer here.) The nagini sibling carries no divergence case either.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason nagini gives. The
    postcondition is GROUNDED: an equality against terms built only from the
    inputs (``keepUnexpired`` / ``cullBoundary`` / ``keepAboveKey`` over
    ``entries``, ``now``, ``frequency``, ``capacity``), all structural. The
    bundle declares no ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []), so there is no answer key an implementation
    could echo without doing the work — an "echo" of a grounded oracle IS the
    correct implementation. The honest analogue is the positive control below.

  * CONTROL-FLOW-EFFECT — VACUOUS, as in nagini. The only observable is the
    returned ``Option (List Entry)``: "does the pass complete, and with which
    survivors". There is no side-effect channel distinct from that value, so a
    capability-token rival would add no discrimination.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script's ``simp only [...]``/``rfl`` is
tuned to the frozen form), so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet that instantiates
the spec at ONE concrete input, projects out the clause the rival violates
(``h.1`` for (1), ``(h.2 _).1`` for (2), ``(h.2 _).2`` for (3)) and reduces the
resulting ground equation to a contradiction. Each was built against the rival
AND against the frozen solution: every witness below was SEEN to elaborate on
its rival and to FAIL on gold, so it discriminates rather than asserting a
tautology, and an independent audit re-derived both builds plus the
claim-tracking checks recorded under AUDIT RECORD below. No witness binds a hypothesis, so none can be vacuously true — every
refutation is stated at literal inputs, and the gate's consistency probe has
nothing to check.

Two mechanical notes on this carrier, both measured:
  * ``decide`` cannot be applied to the spec directly — ``problem_spec_cull`` is
    an implication-shaped ``Prop`` over ``Int`` and has no ``Decidable``
    instance, so the witnesses project a clause first and discharge the ground
    equation with ``simp``/``decide`` on the residue.
  * the ``Id`` carrier must be reduced by ``decide``, not by ``simp``: the impl
    is ``Id.run do``, and ``simp`` (even with ``Id.run`` in the set) leaves the
    returned value wrapped as ``pure v = v`` — TRUE but not closed. Such a
    residue is a DEAD END for evidence, because it stalls identically whichever
    claim is made about it, so a witness that ends there records an exit code
    that attributes nothing to the spec. ``decide`` does reduce ``pure v`` (the
    kernel unfolds ``Id``), so every witness here ends by deciding the ground
    equation: on the frozen solution ``decide`` then reports the negated
    equation FALSE, which is the spec being satisfied at that input, and on the
    rival it proves it. Conversely ``decide`` CANNOT be pointed at an
    unsimplified ``implementation_cull`` application or at a ``simp only``
    residue that still contains the ``do`` block: measured, both report
    "reduction got stuck at the `Decidable` instance". The order — full ``simp``
    to collapse the branches, then ``decide`` — is load-bearing in both
    directions.
  * ``String`` order does not reduce: ``decide`` gets stuck on ``String.ltb``'s
    iterators. Where a witness needs the ordering, ``String.le_iff_toList_le`` /
    ``String.lt_iff_toList_lt`` rewrite it to ``List Char`` comparisons, which
    DO decide. Witnesses that turn only on clause (3b) or on record COUNTS avoid
    the ordering entirely and reduce with ``simp [cullBoundary, keepUnexpired]``.

BINDER COVERAGE. Every input binder of ``problem_spec_cull`` is varied across
the reject witnesses, so no rival could mishandle a binder the battery holds
fixed:
  * ``frequency`` — 0 (weak-no-zero-frequency-case, the only value selecting
    clause (1)), 1 (absent-boundary rivals, skip-expiry), 2
    (boundary-at-front, cull-regardless, boundary-from-descending-order), and 3
    at the F2P-shaped empty-store point (the aborting rival and the
    admissibility positive). It is load-bearing twice (the clause-(1) selector and the boundary
    offset divisor) and both roles are probed.
  * ``capacity`` — negative (-1, the F2P shape: capacity forced below any
    survivor count so culling is entered immediately), 0, and 10 (large enough
    that clause (2) is selected). So the ``≤``/``>`` split is exercised on BOTH
    sides, and the value is not pinned.
  * ``now`` — 0 where no record is expired, and 5 where one record IS expired
    (weak-skip-expiry-stage). Both sides of the expiry filter are probed; a
    rival mishandling ``now`` alone is caught.
  * ``entries`` — varied in length (0, 1, 2) and in shape: all-unexpired,
    mixed expired/unexpired, and multi-key so the ordering matters. The empty
    list is included, which is the exact F2P store state. Length 3 is NOT
    reached by any witness: an audit measured that at three or more records the
    ground residue no longer decides — ``List.merge``'s recursion leaves the
    ordering as an unreduced ``if ['a'] ≤ ['b'] then … else …`` guard nested
    under a second ``merge``, and ``decide`` reports "reduction got stuck at the
    Decidable instance". Two records is therefore the largest store on which the
    ordering position is observable AND the residue reduces; since the boundary
    offset and the (3a)/(3b) split are already discriminated at lengths 0-2, the
    extra length buys no clause, only a bigger term.
``pts`` = 8 distinct input points across 8 rivals; no two rivals share a witness
point, so each rival's claimed sub-domain is separately demonstrated rather than
inherited from a sibling.

AUDIT RECORD (independent re-derivation, real builds). Every reject witness was
rebuilt on BOTH subjects: all 8 elaborate against their rival (exit 0) and all 8
FAIL against the frozen solution (exit 1). The gold-side failures were then shown
to track the CLAIM rather than the tactic, two ways: (a) replaying each witness's
own tactic prefix and forcing Lean to print the projected hypothesis's real type
shows a TRUE ground equation on gold (`pure (some [{key := "b", ...}]) = some
[{key := "b", ...}]`) against a FALSE one on the rival (`pure (some [{key := "a",
...}, {key := "b", ...}]) = some [{key := "b", ...}]`); (b) a FORGERY asserting
the OPPOSITE claim — that the spec HOLDS at the witness point — is DISCHARGED on
gold and leaves `False` or a false ground equation on the rival, so gold's exit
code tracks the claim rather than the tactic.

That control was re-run per witness and it CONDEMNED the original
`weak-absent-boundary-aborts` witness — the only one in the battery whose
gold-side error was an `unsolved goals` dump rather than a `decide` verdict. The
opposite claim, carrying the same simp set, failed on gold with the SAME open
`pure (some []) = some []` (the `Id` carrier, never evaluated), so gold's exit 1
there did not depend on what the witness claimed and the case attested to
nothing. It is re-authored to revert the projected clause and close it with
`decide` (see the witness comment and the second mechanical note): gold now
fails with `decide` proving `¬pure (some []) = some []` FALSE — its value there
IS `some []` — and the opposite claim now VERIFIES against gold (exit 0), which
is the claim-dependence this control exists to establish. The rival build is
unchanged (exit 0). The other seven witnesses already ended in a `decide`
verdict and their controls behave as described above. No witness binds a
hypothesis, so no consistency probe is required. Independently, all 7 rivals were
differentially model-checked against the frozen semantics over 3840 input points
(frequency 0-3 × capacity ∈ {-1,0,1,2,10} × now ∈ {0,5,10} × every store of ≤ 2
records over 3 keys × 3 expiries): each disagrees with the frozen function on
168-1233 of them, and each disagrees at its OWN witness point — so none is a
merely reshaped correct impl.

Five FURTHER wrong implementations the battery does not contain were written and
built against the frozen spec, aimed at the least-probed components: a strict
(`<`) expiry comparison, a `≤` cull predicate that drops the boundary record
itself, a `≥` capacity guard, an off-by-one boundary offset, and a descending
ordering. All five were REJECTED (exit 1); the descending one was judged the most
valuable gap and is now shipped as ``weak-boundary-from-descending-order``. Two
correct RESHAPES were also built: the expiry filter written with a negated strict
comparison (`!(e.expires < now)` rather than `now ≤ e.expires`) is extensionally
identical to the frozen one over all 16272 points and its obligation was CLOSED
(exit 0, via a `filter`-congruence `have`), so the spec admits it; the branch
reorder ships as a positive control. No spec hole was found in either direction.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
boundary lookup is modeled structurally (ascending order + indexed access) and
the stage filters are plain ``List.filter``, so there is no in-model axiom
obligation for this lane to re-discharge (that lane is G-AX's job regardless).
"""
from pathlib import Path

INSTANCE = "django__django-13089"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of the region it names and is unique in
# Solution.lean (asserted at import), so every _swap lands entirely inside the
# region it means to edit and the manifest breaks loudly on any drift.
# ---------------------------------------------------------------------------
_IMPL_BODY = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
"""

_PROOF_BODY = """  intro frequency capacity now entries
  unfold problem_spec_cull implementation_cull
  simp only [Id.run]
  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
  intro hne
  simp only [hne, if_false]
  refine ⟨?_, ?_⟩
  · intro hle
    have hgt : ¬ (↑(keepUnexpired now entries).length > capacity) := by
      simp only [not_lt]; exact hle
    simp only [hgt, if_false]
    rfl
  · intro hgt
    simp only [hgt, if_true]
    cases h : cullBoundary (keepUnexpired now entries)
        ((keepUnexpired now entries).length / frequency) with
    | none => rfl
    | some k => rfl
"""

assert _BASE.count(_IMPL_BODY) == 1, "impl region drifted; update _IMPL_BODY"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean with the impl-region body replaced (proof unchanged)."""
    return _swap(_BASE, _IMPL_BODY, body)


def _impl_proof(body, proof):
    """Full Solution.lean with BOTH the impl body and the tactic body replaced.

    Used only by the positive controls, which reshape the implementation and so
    must re-prove the SAME obligation: the `theorem correct_cull` statement is
    untouched, and no helper lemma, axiom, or assumption token is introduced.
    """
    return _swap(_swap(_BASE, _IMPL_BODY, body), _PROOF_BODY, proof)


# ===========================================================================
# RIVAL IMPLEMENTATIONS (uniqueness; expect reject)
# Each changes exactly one modeled decision and leaves the rest gold-shaped, so
# its rejection is attributable to the clause named in its rationale.
# ===========================================================================

# (3b) -> the pass does not complete when the ordering has no record at the
# boundary position. This is the pre-fix behavior for this instance.
_ABSENT_ABORTS = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return none
  return some remaining
"""

# (3b) -> the pass completes but discards every record, instead of leaving the
# store exactly as it is. A near-miss: it agrees with gold everywhere else,
# including on the whole of (3a).
_ABSENT_CLEARS = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some []
  return some remaining
"""

# (3a) -> the boundary is taken at the FRONT of the ascending ordering rather
# than at the configured offset, so the wrong records are dropped. Also collapses
# (3b) into unreachability: position 0 always addresses a record when any
# survivor exists.
_BOUNDARY_FRONT = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    match cullBoundary remaining 0 with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
"""

# `remaining` -> the expiry stage is skipped, so already-expired records are
# counted against capacity, drive the boundary offset, and survive the pass.
_SKIP_EXPIRY = """  if frequency = 0 then
    return some []
  let remaining := entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
"""

# (2)/(3) split -> the capacity comparison is dropped, so culling runs even when
# the survivors are within capacity.
_ALWAYS_CULL = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  let cullNum := remaining.length / frequency
  match cullBoundary remaining cullNum with
  | some k => return some (keepAboveKey k remaining)
  | none   => return some remaining
"""

# (3a)/(3b) SWAPPED -> the two culling outcomes are exchanged: when the ordering
# DOES address a record the store is left alone (the cull that is due is skipped),
# and when it does NOT the store is emptied (a cull that is not due is performed
# maximally). Added by audit: every other rival gets exactly one of the two arms
# wrong, so each could in principle be met by a spec that pinned only the arm it
# attacks. This one is wrong on BOTH arms simultaneously, so it is refuted only by
# a spec that pins the (3a)/(3b) SELECTOR — the presence of a record at the
# boundary position — and not merely the two arm values independently.
_CULL_ARMS_SWAPPED = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some remaining
    | none   => return some []
  return some remaining
"""

# The boundary is located in the WRONG ORDER: the surviving keys are ordered
# DESCENDING and the offset is taken into that ordering, so the boundary is
# counted from the high end. Added by audit: every other rival leaves the
# ordering DIRECTION gold-shaped (they change the offset, the arm, the stage or
# the guard), so the spec's commitment to an ASCENDING order was the one
# component of clause (3a) no case attacked. Same offset, same arm selector, same
# stages — only the order is reversed.
_BOUNDARY_DESCENDING = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match ((remaining.map (·.key)).mergeSort (fun a b => b ≤ a))[cullNum]? with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
"""

# (1) -> the zero-frequency case is dropped, so a store configured to be emptied
# is instead treated as an ordinary capacity check.
_NO_ZERO = """  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
  return some remaining
"""

# ===========================================================================
# POSITIVE CONTROLS (soundness; expect verify) — structurally DIFFERENT but
# CORRECT. Each re-proves the SAME obligation; the statement is byte-identical.
# ===========================================================================

# Test the within-capacity case FIRST, with the comparison negated, and reach the
# culling stage by fall-through. Same value on every input; the frozen script's
# `simp only [hgt, if_false]` no longer matches, so the branch order is swapped
# in the tactic body too.
_POS_REORDER = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) ≤ capacity then
    return some remaining
  else
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some remaining
"""
_POS_REORDER_PROOF = """  intro frequency capacity now entries
  unfold problem_spec_cull implementation_cull
  simp only [Id.run]
  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
  intro hne
  simp only [hne, if_false]
  refine ⟨?_, ?_⟩
  · intro hle
    simp only [hle, if_true]
    rfl
  · intro hgt
    have hle : ¬ (↑(keepUnexpired now entries).length ≤ capacity) := by
      simp only [not_le]; exact hgt
    simp only [hle, if_false]
    cases h : cullBoundary (keepUnexpired now entries)
        ((keepUnexpired now entries).length / frequency) with
    | none => rfl
    | some k => rfl
"""

# Cull against the EMPTY key in the absent-boundary arm instead of returning the
# survivors untouched. This is correct but not obviously so, and it is the only
# positive control here whose correctness is a THEOREM rather than a reduction:
# no key sorts strictly below "", so `keepAboveKey "" remaining = remaining`
# extensionally — but NOT definitionally, since `String.<` does not reduce on an
# opaque `remaining`. Measured: this impl under the FROZEN proof script fails
# (`rfl` cannot close the none-arm), so the reshape is genuinely load-bearing and
# the case is not a defeq no-op. The proof discharges the arm by proving the
# filter is the identity via `List.filter_eq_self` + `String.lt_iff_toList_lt`.
#
# This replaces an earlier `Option.map`/`getD` eliminator reshape, DROPPED by
# audit as VACUOUS: `(x.map f).getD d` is definitionally the `match` it was meant
# to differ from, so that impl verified under the UNCHANGED frozen proof script
# (measured exit 0). Its bespoke `Option.map_none`/`getD_none` proof therefore
# demonstrated nothing the frozen `rfl` did not already do — a positive control
# that passes without exercising the spec.
_POS_EMPTY_KEY_CULL = """  if frequency = 0 then
    return some []
  let remaining := keepUnexpired now entries
  if (remaining.length : Int) > capacity then
    let cullNum := remaining.length / frequency
    match cullBoundary remaining cullNum with
    | some k => return some (keepAboveKey k remaining)
    | none   => return some (keepAboveKey "" remaining)
  return some remaining
"""
_POS_EMPTY_KEY_CULL_PROOF = """  intro frequency capacity now entries
  have hnil : ∀ xs : List Entry, keepAboveKey "" xs = xs := by
    intro xs
    unfold keepAboveKey
    apply List.filter_eq_self.mpr
    intro e _
    simp only [Bool.not_eq_true', decide_eq_false_iff_not]
    simp [String.lt_iff_toList_lt]
  unfold problem_spec_cull implementation_cull
  simp only [Id.run]
  refine ⟨fun h0 => by simp only [h0, if_true]; rfl, ?_⟩
  intro hne
  simp only [hne, if_false]
  refine ⟨?_, ?_⟩
  · intro hle
    have hgt : ¬ (↑(keepUnexpired now entries).length > capacity) := by
      simp only [not_lt]; exact hle
    simp only [hgt, if_false]
    rfl
  · intro hgt
    simp only [hgt, if_true]
    cases h : cullBoundary (keepUnexpired now entries)
        ((keepUnexpired now entries).length / frequency) with
    | none =>
      show some (keepAboveKey "" (keepUnexpired now entries)) = _
      rw [hnil]
    | some k => rfl
"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS — a faithful correct implementation MUST satisfy the
    # frozen obligation. If one cannot, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-within-capacity-branch-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_REORDER, _POS_REORDER_PROOF),
        "rationale": (
            "branch REORDER: test `|remaining| ≤ capacity` first and return the "
            "survivors, reaching the culling stage by fall-through, instead of "
            "testing `> capacity` first. `≤` and `>` are complementary on Int, so "
            "the two shapes agree on every input — every clause of the spec, "
            "including the (3a)/(3b) split, is computed identically. A "
            "structurally different CORRECT implementation MUST verify. The proof "
            "re-derives the frozen argument with the two branches swapped: the "
            "`≤` case closes directly and the culling case recovers `¬ (… ≤ "
            "capacity)` from `hgt` via `not_le` before casing the boundary. Same "
            "theorem statement, no helper lemma, no axiom, no assumption token."
        ),
    },
    {
        "id": "pos-absent-boundary-culls-empty-key",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_EMPTY_KEY_CULL, _POS_EMPTY_KEY_CULL_PROOF),
        "rationale": (
            "in the absent-boundary arm, cull against the EMPTY key rather than "
            "returning the survivors untouched. This is EXTENSIONALLY the same "
            "function — no key sorts strictly below \"\", so `keepAboveKey \"\" "
            "remaining` retains every record — but it is NOT definitionally the "
            "frozen shape: `String.<` does not reduce on an abstract `remaining`, "
            "so the equality is a theorem, proven here from "
            "`List.filter_eq_self` plus `String.lt_iff_toList_lt`. That makes it "
            "the strongest positive control available on this carrier: it shows "
            "the spec accepts a correct impl whose agreement with the frozen one "
            "needs a PROOF rather than a reduction, so clause (3b) is pinned "
            "semantically (to the SET of survivors) and not merely syntactically. "
            "It also doubles as the ungrounded-oracle lane's positive control: "
            "the oracle being grounded, the cheapest faithful 'echo' is simply a "
            "correct implementation and MUST verify. Same theorem statement, no "
            "helper lemma declaration, no axiom, no assumption token (`hnil` is a "
            "`have` inside the tactic body, not a new top-level declaration — "
            "checked by variant_scope). Replaces an `Option.map`/`getD` "
            "eliminator reshape that the audit measured as a defeq no-op: it "
            "verified under the UNCHANGED frozen proof script, so it exercised "
            "nothing."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem is total and carries no
    # precondition, so the nagini precondition-admission self-call re-expresses
    # on this carrier as: discharge the spec predicate BY EVALUATION at the exact
    # F2P-shaped configuration, as a `have`, before closing the frozen obligation
    # verbatim. If the conjunction were unsatisfiable at that concrete point the
    # `have` could not be closed — the total-carrier analogue of
    # PRECOND-TOO-STRONG. Added by audit: the port carried no admissibility case,
    # which silently dropped one of the three directions this gate tests.
    # (Measured: real build, exit 0.)
    # =====================================================================
    {
        "id": "admiss-ground-f2p-empty-store",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "  intro frequency capacity now entries\n"
            "  unfold problem_spec_cull implementation_cull\n",
            "  intro frequency capacity now entries\n"
            "  have _ground : problem_spec_cull 3 (-1) 0 ([] : List Entry)\n"
            "      (implementation_cull 3 (-1) 0 ([] : List Entry)) := by\n"
            "    simp [problem_spec_cull, implementation_cull, Id.run,"
            " cullBoundary, keepUnexpired]\n"
            "      <;> rfl\n"
            "  unfold problem_spec_cull implementation_cull\n"),
        "rationale": (
            "ADMISSIBILITY at the F2P-shaped configuration: `frequency = 3` (the "
            "configuration default), `capacity = -1` (forced below any survivor "
            "count, so the culling stage is entered immediately) and an EMPTY "
            "store — exactly the state the F2P observable constructs. The whole "
            "spec conjunction is discharged there BY EVALUATION as a `have` "
            "(`simp [...] <;> rfl` reduces every clause to a ground identity), "
            "then the frozen obligation is closed verbatim. This is the total-"
            "carrier analogue of nagini's precondition-admission self-call: the "
            "frozen theorem has no precondition to establish, so what the lane "
            "tests here is that the obligation is SATISFIABLE at a normal input "
            "rather than vacuously true or unreachable. Had the conjunction been "
            "contradictory at that concrete point — the shape of "
            "PRECOND-TOO-STRONG on a total carrier — the `have` could not close, "
            "and the case would fail. Nothing is assumed: statement "
            "byte-identical, no new top-level declaration, no axiom and no "
            "assumption token (`_ground` is a `have` inside the existing tactic "
            "body — checked by variant_scope). Ports nagini's "
            "admiss-present-and-absent, whose present/absent split appears here "
            "as the (3a)/(3b) arms of clause (3); the absent arm is the one this "
            "point lands in."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong implementations sharing the frozen spec, which
    # MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve, and (b) a witness pinning the
    # violation at one concrete input, SEEN to hold of the rival and to fail on
    # the frozen solution.
    # =====================================================================
    {
        "id": "weak-absent-boundary-aborts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABSENT_ABORTS),
        "refinement": (
            "this is the pre-fix behavior: the boundary position is read "
            "unconditionally, so when the ordering yields no record at that "
            "position the pass aborts instead of completing. Its faithful real "
            "patch is the pre-patch code itself, which the F2P observable "
            "defeats directly: with capacity configured below any survivor count, "
            "storing the very first record enters the culling stage on a store "
            "whose ordering has no record at the boundary position, the pass "
            "raises instead of returning, and the record the test then asserts to "
            "be present was never retained. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (3b): when `cullBoundary remaining (|remaining| / "
            "frequency)` is `none` the spec demands `result = some remaining` — "
            "the pass COMPLETES and leaves the store as it is. At `frequency = 3`, "
            "`capacity = -1`, `now = 0` and an EMPTY store (the exact F2P state: "
            "capacity forced negative so culling is entered on a store with no "
            "survivors, offset 0 addressing nothing) the spec demands `some []` "
            "while the rival returns the abort marker. Probed at the empty-store "
            "point no other witness uses, and at `frequency = 3` — the "
            "configuration default — so the load-bearing clause is refuted at the "
            "very shape the F2P constructs. If it verified, the spec would admit "
            "the pre-fix crash => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Clause (3b) at the F2P store state: an empty store with capacity\n"
            "-- forced below the survivor count. Culling is entered, the ordering\n"
            "-- has no record at the boundary position, so the pass must complete\n"
            "-- with the store unchanged (`some []`). The rival aborts instead.\n"
            "--\n"
            "-- The projected clause is REVERTED and DECIDED rather than simped in\n"
            "-- place, and the difference is not cosmetic. Measured: `simp` alone\n"
            "-- leaves the `Id` carrier as the unreduced `pure (some []) = some []`\n"
            "-- on the frozen solution, and that residue stalls for EITHER claim --\n"
            "-- the OPPOSITE claim (that the spec HOLDS at this point), carrying\n"
            "-- the same simp set, failed on the frozen solution with the same open\n"
            "-- equation -- so an exit code obtained that way did not depend on\n"
            "-- what was claimed and attested to nothing. The closing `decide`\n"
            "-- forces the ground equation through the kernel instead: the frozen\n"
            "-- solution now reports that `decide` proved `¬pure (some []) = some\n"
            "-- []` FALSE -- its value at this input IS `some []`, i.e. clause (3b)\n"
            "-- genuinely holds of it -- while the rival's `none = some []` is\n"
            "-- discharged by the simp itself, which is why the decide runs under\n"
            "-- `all_goals`. With the decide in place the opposite claim VERIFIES\n"
            "-- against the frozen solution (exit 0), so the rejection is\n"
            "-- claim-dependent rather than a carrier artifact.\n"
            "example : ¬ problem_spec_cull 3 (-1) 0 ([] : List Entry)\n"
            "    (implementation_cull 3 (-1) 0 ([] : List Entry)) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).2 (by decide)\n"
            "  revert hx\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired]\n"
            "  all_goals decide\n"
        ),
    },
    {
        "id": "weak-absent-boundary-empties-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABSENT_CLEARS),
        "refinement": (
            "a NEAR-MISS of the previous rival: the pass completes (so it never "
            "raises) but discards every record when the ordering has no record at "
            "the boundary position. Its faithful real patch guards the boundary "
            "read and then, finding no boundary, deletes unconditionally rather "
            "than skipping the delete. That is exactly what the F2P forbids: with "
            "capacity forced below the survivor count, the record just stored is "
            "removed by the very pass that was meant to leave the store alone, so "
            "the assertion that it is still present fails. It does NOT resolve — "
            "and unlike the aborting rival it fails silently, with no exception "
            "to attribute the loss to."
        ),
        "rationale": (
            "REJECT from clause (3b), the same clause as the aborting rival but "
            "at a DIFFERENT wrong value and a different input point, since this "
            "rival agrees with gold over strictly more of the domain (it completes "
            "everywhere, and is correct on the whole of (3a)): the spec demands "
            "`some remaining`, the rival returns `some []`. Refuted at `frequency "
            "= 1`, `capacity = -1`, `now = 0` with ONE unexpired record — a store "
            "that is NON-empty, so `some remaining ≠ some []` is a real "
            "disagreement rather than the coincidence it would be on the empty "
            "store the sibling rival uses. Its own point, so its narrower "
            "sub-domain is demonstrated and not inherited. If it verified, the "
            "spec would not pin what survives when no boundary is addressed => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Clause (3b) on a NON-empty store: one unexpired record, capacity\n"
            "-- below the survivor count, offset 1 addressing nothing in a\n"
            "-- one-record ordering. The store must survive unchanged; the rival\n"
            "-- empties it. Non-empty on purpose, so `some remaining ≠ some []`.\n"
            "example : ¬ problem_spec_cull 1 (-1) 0 [⟨\"a\", 10⟩]\n"
            "    (implementation_cull 1 (-1) 0 [⟨\"a\", 10⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).2 (by decide)\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired] at hx\n"
            "  exact absurd hx (by decide)\n"
        ),
    },
    {
        "id": "weak-boundary-at-front-of-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BOUNDARY_FRONT),
        "refinement": (
            "taking the boundary at the front of the ascending ordering instead "
            "of at the configured offset corresponds to requesting the ordering "
            "without skipping the leading records. Its faithful real patch culls "
            "against the lowest surviving key, and since no record sorts strictly "
            "below the lowest, NOTHING is ever dropped: the store grows without "
            "bound past its capacity, and the pre-existing culling tests — which "
            "assert an exact surviving count after deliberately overflowing the "
            "store — see every record retained instead. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (3a): the spec pins the boundary to the record at "
            "position `|remaining| / frequency` of the ascending ordering, so both "
            "`frequency` (as the divisor) and the ordering itself are load-bearing. "
            "At `frequency = 2`, `capacity = 0`, `now = 0` with two unexpired "
            "records the offset is 1, so the spec drops the lower record and keeps "
            "one; the rival takes offset 0 and keeps both. Probed with TWO "
            "distinct keys — the smallest store on which the ordering position is "
            "observable at all — at a `frequency`/`capacity` pair no other witness "
            "uses. If it verified, the spec would not pin WHICH records culling "
            "drops => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Clause (3a): two unexpired records, offset |remaining|/frequency\n"
            "-- = 1, so the boundary is the SECOND key ascending and the first must\n"
            "-- be dropped. The rival takes the front of the ordering and drops\n"
            "-- nothing. String order is rewritten to List Char, which decides.\n"
            "example : ¬ problem_spec_cull 2 0 0 [⟨\"a\", 10⟩, ⟨\"b\", 10⟩]\n"
            "    (implementation_cull 2 0 0 [⟨\"a\", 10⟩, ⟨\"b\", 10⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).2 (by decide)\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired,\n"
            "    keepAboveKey, List.mergeSort, List.merge, String.le_iff_toList_le,\n"
            "    String.lt_iff_toList_lt] at hx\n"
            "  exact absurd hx (by decide)\n"
        ),
    },
    {
        "id": "weak-boundary-from-descending-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BOUNDARY_DESCENDING),
        "refinement": (
            "ordering the surviving keys the other way corresponds to requesting "
            "the boundary from a descending rather than an ascending ordering, "
            "while keeping the same offset. Its faithful real patch culls against "
            "a boundary counted from the HIGH end of the key range, so on a "
            "deliberately overflowed store it drops a different — and generally "
            "much larger — set of records than the configured fraction: the "
            "pre-existing culling tests, which assert an exact surviving count "
            "after overflowing the store, see the wrong count. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the ORDER inside clause (3a), the one component of the "
            "boundary computation no other rival attacks: the sibling rivals "
            "change the offset (boundary-at-front), the arm (arms-swapped, "
            "absent-*), the stage (skip-expiry) or the guard "
            "(cull-regardless), all of which leave the ascending ordering itself "
            "gold-shaped — so a spec that pinned only 'the key at offset n of SOME "
            "canonical ordering' would still refute every one of them. This rival "
            "keeps the offset, both arms and every stage identical and reverses "
            "only the direction, so refuting it requires the spec to pin the "
            "ordering as ASCENDING. At `frequency = 2`, `capacity = -1`, `now = 0` "
            "with two unexpired records the offset is 1: ascending that addresses "
            "the HIGHER key and the lower record must be dropped, while descending "
            "it addresses the LOWER key and nothing is dropped. Its own input "
            "point (a `capacity`/`expires` pair no other witness uses). If it "
            "verified, the spec would pin the boundary's position without pinning "
            "the ordering it is a position in => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Clause (3a), ordering DIRECTION: two unexpired records, offset\n"
            "-- |remaining|/frequency = 1. Ascending, offset 1 is the SECOND key,\n"
            "-- so the first must be dropped; descending, offset 1 is the FIRST\n"
            "-- key and nothing sorts strictly below it, so the rival drops\n"
            "-- nothing. String order is rewritten to List Char, which decides.\n"
            "example : ¬ problem_spec_cull 2 (-1) 0 [⟨\"a\", 0⟩, ⟨\"b\", 0⟩]\n"
            "    (implementation_cull 2 (-1) 0 [⟨\"a\", 0⟩, ⟨\"b\", 0⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).2 (by decide)\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired,\n"
            "    keepAboveKey, List.mergeSort, List.merge, String.le_iff_toList_le,\n"
            "    String.lt_iff_toList_lt] at hx\n"
            "  exact absurd hx (by decide)\n"
        ),
    },
    {
        "id": "weak-skip-expiry-stage",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SKIP_EXPIRY),
        "refinement": (
            "skipping the first stage corresponds to omitting the removal of "
            "already-expired records before the capacity check. Its faithful real "
            "patch leaves expired records in the store, so they are counted "
            "against capacity, shift the boundary position, and survive a pass "
            "that was supposed to remove them. The pre-existing culling tests "
            "assert an exact surviving count after overflowing the store, and a "
            "pass that both retains dead records and culls against a boundary "
            "computed from an inflated count returns a different count. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the definition of `remaining`, which every one of clauses "
            "(2) and (3) is stated against: the spec pins it to the records whose "
            "expiry is at or after `now`, making `now` and each record's `expires` "
            "load-bearing. At `now = 5` with one record expired at 0 and one live "
            "at 10, `frequency = 1`, `capacity = 0`, the spec's `remaining` is the "
            "single live record while the rival's is both. This is the ONLY witness "
            "with `now` off the value at which the expiry filter is a no-op, so it "
            "is what stops a rival that ignores expiry from verifying => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- The expiry stage: at now = 5 the record expiring at 0 is already\n"
            "-- expired and must be dropped before anything else happens, leaving\n"
            "-- one survivor. The rival keeps both. The only witness at which the\n"
            "-- expiry filter is not the identity.\n"
            "example : ¬ problem_spec_cull 1 0 5 [⟨\"a\", 0⟩, ⟨\"b\", 10⟩]\n"
            "    (implementation_cull 1 0 5 [⟨\"a\", 0⟩, ⟨\"b\", 10⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).2 (by decide)\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired] at hx\n"
            "  exact absurd hx (by decide)\n"
        ),
    },
    {
        "id": "weak-cull-regardless-of-capacity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_CULL),
        "refinement": (
            "dropping the capacity comparison corresponds to culling on every "
            "pass rather than only when the store has outgrown its capacity. Its "
            "faithful real patch prunes records from a store that is comfortably "
            "within capacity, so ordinary stores silently lose entries on each "
            "write: the pre-existing tests that store a record and then read it "
            "back find it missing whenever an earlier-sorting key was present. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (2), the only clause no other rival attacks: when "
            "`|remaining| ≤ capacity` the spec demands `result = some remaining` "
            "with NO culling at all, so `capacity` is load-bearing as the "
            "selector between (2) and (3). At `frequency = 2`, `capacity = 10`, "
            "`now = 0` with two unexpired records the survivors are well within "
            "capacity and must be returned untouched; the rival culls anyway and "
            "drops the lower key. This is the only witness on the `≤` side of the "
            "capacity split — it exercises `capacity` at a large positive value "
            "against the negative and zero values the other witnesses use, so the "
            "spec's dependence on that binder is demonstrated on both sides. If it "
            "verified, the spec would not pin WHETHER culling happens => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Clause (2): two survivors against a capacity of 10 is within\n"
            "-- capacity, so the store must be returned exactly as it is. The\n"
            "-- rival culls regardless and drops the lower key.\n"
            "example : ¬ problem_spec_cull 2 10 0 [⟨\"a\", 0⟩, ⟨\"b\", 0⟩]\n"
            "    (implementation_cull 2 10 0 [⟨\"a\", 0⟩, ⟨\"b\", 0⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).1 (by decide)\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired,\n"
            "    keepAboveKey, List.mergeSort, List.merge, String.le_iff_toList_le,\n"
            "    String.lt_iff_toList_lt] at hx\n"
            "  exact absurd hx (by decide)\n"
        ),
    },
    {
        "id": "weak-cull-arms-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CULL_ARMS_SWAPPED),
        "refinement": (
            "exchanging the two culling outcomes corresponds to inverting the "
            "presence guard on the boundary lookup: the prune is issued exactly "
            "when no boundary was found and skipped exactly when one was. Its "
            "faithful real patch fails BOTH sides of the observable behavior. On "
            "the F2P shape — capacity forced below the survivor count, the "
            "ordering addressing nothing — it prunes the whole store, so the "
            "record just stored is gone and the assertion that it is still "
            "present fails. On a deliberately overflowed store, where the "
            "ordering DOES address a boundary, it prunes nothing, so the "
            "pre-existing tests asserting an exact reduced surviving count see "
            "every record retained. It does NOT resolve on either sub-domain."
        ),
        "rationale": (
            "REJECT from the (3a)/(3b) SELECTOR of clause (3), which no other "
            "rival attacks as a selector: the sibling rivals each get exactly one "
            "arm wrong while leaving the other gold-shaped, so each is refutable "
            "by a spec that pinned only the arm under attack. This rival is wrong "
            "on both arms at once, so refuting it requires the spec to pin WHICH "
            "arm applies — i.e. that the outcome is selected by whether the "
            "ascending ordering has a record at the boundary position. Refuted at "
            "`frequency = 2`, `capacity = 1`, `now = 0` with two unexpired records "
            "at expiry 7: the survivor count 2 exceeds capacity 1, the offset is "
            "2/2 = 1, so the ordering DOES address the second key and the spec "
            "demands the lower record be dropped; the rival takes the (3a) arm and "
            "returns both. Its own input point — a `capacity`/`expires` pair no "
            "other witness uses — so its sub-domain is demonstrated, not "
            "inherited. If it verified, the spec would pin the two arm VALUES "
            "without pinning which one applies => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- The (3a)/(3b) selector: two survivors against capacity 1 enters\n"
            "-- culling, and offset |remaining|/frequency = 1 DOES address the\n"
            "-- second key ascending, so the (3a) arm applies and the lower record\n"
            "-- must be dropped. The rival swaps the arms and returns both.\n"
            "example : ¬ problem_spec_cull 2 1 0 [⟨\"a\", 7⟩, ⟨\"b\", 7⟩]\n"
            "    (implementation_cull 2 1 0 [⟨\"a\", 7⟩, ⟨\"b\", 7⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := (h.2 (by decide)).2 (by decide)\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired,\n"
            "    keepAboveKey, List.mergeSort, List.merge, String.le_iff_toList_le,\n"
            "    String.lt_iff_toList_lt] at hx\n"
            "  exact absurd hx (by decide)\n"
        ),
    },
    {
        "id": "weak-no-zero-frequency-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_ZERO),
        "refinement": (
            "dropping the zero-frequency case corresponds to removing the "
            "short-circuit that empties the store when the maintenance frequency "
            "is configured as zero, and instead running the ordinary capacity "
            "path. Its faithful real patch computes the boundary position by "
            "dividing by that zero frequency, so a store configured this way "
            "either fails outright or prunes against a boundary derived from a "
            "division by zero rather than being emptied. The pre-existing test "
            "for the zero-frequency configuration asserts the exact surviving "
            "count produced by emptying, which this does not produce. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (1), which no other rival attacks: `frequency = 0` "
            "demands `result = some []` unconditionally, independent of capacity, "
            "`now` and the records. At `frequency = 0`, `capacity = 10`, `now = 0` "
            "with one unexpired record the spec demands the store be emptied; the "
            "rival takes the capacity path, finds one record within capacity, and "
            "returns it. This is the only witness at `frequency = 0` — the single "
            "value selecting clause (1) — so it is what stops a rival that ignores "
            "the frequency configuration from verifying => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Clause (1): frequency configured as zero empties the store\n"
            "-- unconditionally. The rival runs the capacity path instead and, the\n"
            "-- single record being within capacity, returns it.\n"
            "example : ¬ problem_spec_cull 0 10 0 [⟨\"a\", 10⟩]\n"
            "    (implementation_cull 0 10 0 [⟨\"a\", 10⟩]) := by\n"
            "  unfold problem_spec_cull\n"
            "  intro h\n"
            "  have hx := h.1 (by decide)\n"
            "  revert hx\n"
            "  simp [implementation_cull, Id.run, cullBoundary, keepUnexpired]\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references (meta.json axioms == [],
# deep_model_references == []): the boundary lookup is modeled structurally as
# an ascending ordering plus an indexed access, and both stage filters are plain
# list filters, so there is no in-model axiom obligation for this lane to
# re-discharge. The axiom lane belongs to G-AX regardless.
AXIOM_TESTS = []

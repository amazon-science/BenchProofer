"""properties.py — PBT falsification manifest for django__django-16631 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the two positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition rather than to a tampered spec.

DEFENDED SURFACE
----------------
One modeled function, one obligation:

    implementation_validateToken
        (storedToken currentToken : List Char)
        (alternateTokens : List (List Char)) : VerifyDecision

pinned by `problem_spec_validateToken`, a conjunction of FOUR independent
implications that partition the input space and pin the decision to a single
value in each cell:

  1. `storedToken = [] → result = .rejected`
     — absence of a stored token is decided on its own, before any comparison.
  2. `storedToken ≠ [] → storedToken = currentToken → result = .acceptedCurrent`
     — a stored token equal to the currently-valid one is accepted against the
     current token, and NOT against an alternate. This clause is what makes the
     current token take PRIORITY over the alternates.
  3. `storedToken ≠ [] → storedToken ≠ currentToken →
      (∃ t ∈ alternateTokens, t = storedToken) → result = .acceptedAlternate`
     — a present token that differs from the current one but appears among the
     additionally-accepted tokens is accepted against an alternate. Acceptance is
     TOTAL over such tokens: it may not be conditioned on their shape.
  4. `storedToken ≠ [] → storedToken ≠ currentToken →
      (¬ ∃ t ∈ alternateTokens, t = storedToken) → result = .rejected`
     — a present token matching neither is rejected. This is the clause that
     stops the acceptance paths from over-firing.

The carrier is FULLY TRANSPARENT: `List Char`, list equality, an inductive
three-valued decision, and no `opaque` callee anywhere (the axioms region is
empty — the token values are INPUTS, produced elsewhere and opaque to this
decision). So every rival is refutable by `decide` at a concrete input and no
witness needs to condition on the carrier; correspondingly, no witness binds a
hypothesis, so none can be `witness-inconsistent`.

The battery attacks all four clauses and varies all three input binders:
`storedToken` ranges over `[]`, a one-character, a two-character and a
three-character token; `currentToken` over `[]`, a token equal to `storedToken`
and several distinct tokens; `alternateTokens` over `[]`, a singleton holding
`storedToken`, a singleton holding some OTHER token, and a TWO-entry list whose
match sits at the tail. Eight distinct probe points.

The spec is a TOTAL FUNCTION, and that is machine-checked rather than argued: the
audit pass proved

    ∀ st ct alts r1 r2, problem_spec_… st ct alts r1 →
                        problem_spec_… st ct alts r2 → r1 = r2

by case-splitting the same four conditions the clauses split on (exit 0), and then
composed it with the frozen `correct_validateToken` to get the sharper statement

    ∀ st ct alts r, problem_spec_… st ct alts r →
                    r = implementation_validateToken st ct alts

also exit 0. That is the whole SPEC-TOO-WEAK question settled mechanically rather
than by enumerating rivals: any impl satisfying this spec agrees with gold on
EVERY input, so no wrong impl can verify and no tuned rival can be a spec hole.
(Re-derived independently by a later audit pass, which then wrote three NEW wrong
impls the battery does not contain — prefix-matching the alternates instead of
comparing them, scanning only the LAST entry, and dropping the absence guard
outright — and confirmed all three are rejected, as the theorem above requires.)
So the
four clauses genuinely partition the input space and pin one decision per cell,
and no implementation can satisfy the spec while computing any decision function
other than gold's. That is the strongest available answer to SPEC-TOO-WEAK: a
rival verifies only if it agrees with gold on every input, so the reject lane
below is testing witness discrimination, not hunting a residual spec hole.

PORTING NOTES (which nagini cases port, which are omitted and why)
------------------------------------------------------------------
The nagini sibling contracts TWO functions — the three-way decision and the
producer of the additionally-accepted token list (a fold over the configured
alternate keys). This bundle models only the DECISION; the token values are its
inputs, since their derivation is not part of the modeled control flow
(mapping.md, "Callee provenance"). So every nagini case attached to the producer
has no counterpart on this carrier. That is carrier narrowing, not a gap:

  * `pos-control-A` -> `pos-early-return` — the structurally-different CORRECT
    decision impl; reshaped into early returns with the two membership facts
    computed in a different order. Proof re-closed for the new shape.
  * added `pos-functional-form` — a second correct impl in a genuinely different
    form (pure functional if/else cascade, no `Id.run do` / `for` / `let mut`,
    the alternate scan expressed as `List.any`). Proof re-closed. Guards against
    a spec over-fit to the imperative skeleton.
  * `reject-all-A` -> `no-alternate-path` — never produces the alternate-
    acceptance decision; attacks clause 3.
  * `swap-1-2-A` -> `prior-before-current` — priority inversion: consults the
    alternates FIRST, so a token equal to the current token is accepted against
    an alternate. Attacks clause 2.
  * `partial-A` -> `partial-wrong-width` — correct except it refuses the
    alternate path for every stored token WIDER than one character; attacks
    clause 3 on a value sub-domain. Kept as a distinct case from
    `no-alternate-path` because it is a NEAR-MISS (it agrees with gold
    everywhere else), so it carries its own witness at the sub-domain point
    rather than sharing one. The refused class is deliberately the one that
    contains the real token's fixed width — see the case comment for why the
    mirror direction makes the `refinement` argument false.
  * `miskey-B` -> `alternates-vs-current` — the site-B mis-keying defect
    re-expressed on THIS carrier: the producer is not modeled here, but the same
    error is observable as comparing each alternate against the CURRENT token
    instead of the stored one, which is exactly what a uniformly mis-keyed
    alternate list would make the decision do. Attacks clause 3.
  * `drop-token-B` — OMITTED as such: it empties the alternate list, which on
    this carrier is not an impl at all but an INPUT value (`alternateTokens =
    []`), a legitimate configuration the spec already covers. Its adversarial
    content (the acceptance path never firing) is exactly `no-alternate-path`.
  * added `accept-any-present` — accepts every present mismatching token,
    over-firing the alternate path. The ONLY rival attacking clause 4, and the
    only one probing an EMPTY alternate list. Without it a rival that accepted
    unconditionally would verify against a battery that only ever attacked the
    under-acceptance direction.
  * added `absent-token-verified` — decides the absent-token guard the WRONG WAY,
    so an absent stored token is treated as verified and accepted. The ONLY rival
    attacking clause 1, and the only one varying `storedToken` to `[]`. This is
    the clause the pre-patch code already had right, so nagini had no rival for
    it; on this carrier it is an independent top-level clause and an unattacked
    clause is an untested one. (The audit pass replaced an earlier form that
    merely DELETED the guard: that form's only divergence from gold was at
    `storedToken = [] ∧ currentToken = []`, so its refined patch would have
    resolved — see the case comment.)
  * added `alternate-decided-as-current` (audit) — takes the alternate branch on
    exactly the right inputs but returns the current-token decision there. The
    only rival attacking the decision VALUE rather than the branch taken, i.e.
    the only one that tests the two ACCEPTANCE decisions are distinguished from
    each other.
  * added `scan-head-only` (audit) — scans only the first entry of the accepted-
    alternates list. The only rival attacking the TOTALITY of clause 3's
    existential, and the only case whose `alternateTokens` has more than one
    entry.
  * `frame-mut-A` / `frame-mut-A2` / `frame-mut-B` / `frame-mut-B2` — OMITTED as
    VACUOUS on this backend. They are fractional-permission cases: nagini grants
    the read-only inputs half permission and a rival writes to one. Lean is
    referentially transparent, so there is no aliasing, no permission and no
    in-place write to express; the inputs cannot be mutated. Nor is there a
    structural substitute here: unlike bundles whose result CARRIES an input
    component (where the frame obligation reappears as an equality in the
    payload), this result is a bare three-valued decision, so no input is an
    observable component of the output. No substitute is fabricated.
  * `admiss-A` / `admiss-B` -> `admiss-ground-alternate` (audit). An earlier pass
    recorded this lane as VACUOUS because the obligation is
    `∀ storedToken currentToken alternateTokens, problem_spec_… (implementation_…)`
    with NO precondition hypothesis, so nothing could be over-strong. That reason
    is wrong, and the audit pass landed the case rather than agreeing with it:
    the analogue of PRECOND-TOO-STRONG on a TOTAL carrier is the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input, which a positive that discharges
    the spec predicate at that concrete input — by evaluation, as a `have`, before
    closing the frozen obligation verbatim — tests directly. It is measured
    load-bearing rather than assumed: the same two `have`s spliced onto the
    `no-alternate-path` rival FAIL (exit 1, `decide` proved the proposition
    false), and so do they on `alternate-decided-as-current`, so the case pins
    the ground input to the alternate-acceptance branch AND to the decision value
    that branch must report. See the case comment.
  * No `diverge-*` / `nonterm-*` case exists in the nagini sibling, and the class
    is genuinely vacuous here — but the audit pass re-derived the reason with real
    builds rather than accepting the original one, because the original was stated
    in a form that is not what the carrier actually enforces. This bundle carries
    NO `set_option loom.semantics.termination` line at all: it is plain Lean, not
    the velvet/loom carrier, so there is no termination-semantics setting to invert
    the disposition and every `def` the kernel accepts is total BY CONSTRUCTION.
    Three probes, all built:
      - the generic `while true do pure ()` prefix spliced ahead of the frozen body
        VERIFIES (exit 0) — but it is not a diverging impl at all. Its `Id`-monad
        loop value is dead, `#print` shows the frozen decision term untouched, and
        `#eval implementation_validateToken [] [] []` RETURNS `.rejected` rather
        than hanging. So the probe measures nothing and is not a rival;
      - a probe whose spin value is genuinely DEMANDED (`while spin do spin := true`
        feeding the returned decision) is REJECTED (exit 1, `unsolved goals` on
        `forIn Lean.Loop.mk … = false`) — the obligation is unsatisfiable, which is
        the correct disposition;
      - `partial def` — the honest way to write a non-terminating Lean impl —
        does not elaborate here at all (exit 1, `could not prove that the type …
        is nonempty`; `VerifyDecision` derives no `Nonempty`/`Inhabited`), so the
        escape hatch is closed on this carrier too.
    Hence vacuous, and demonstrated so. (Contrast the velvet twin, which DOES set
    `loom.semantics.termination "total"`; under `"partial"` this would be a KNOWN
    SPEC HOLE rather than a vacuous class — see the corpus-wide termination-semantics finding.)
  * `AXIOM_TESTS` — dropped; the axiom lane is G-AX's job and this gate ignores
    it. (Here it is a skip stub anyway: the axioms region is empty.)

WITNESSES
---------
Every reject case carries a `witness`: a Lean `example` negating the spec
predicate at ONE concrete input, checked in a file where the frozen obligation
has been removed so no tactic script can interfere. Each must (1) ELABORATE
against the rival and (2) FAIL against the frozen solution, so it is a real
discriminator and not a tautology. All eight below were built BOTH ways with
scripts/lean_verify.sh: exit 0 against the rival, exit 1 against gold, where the
gold-side failure is `Tactic 'decide' proved that the proposition … is false`
— i.e. gold demonstrably SATISFIES the spec at the probed point, so the failure
is a SEMANTIC refutation and not a missing identifier, a type error, a stuck
unfolding or a timeout. No witness binds a hypothesis, so there are no
assumptions to be jointly unsatisfiable and no consistency probe is owed.

A later audit pass re-derived all eight discriminations from scratch (rival exit 0,
gold exit 1 in every case) and additionally ran the FORGERY test on each, since
"the error looks semantic" is not evidence by itself: for every witness it built a
second file differing ONLY in what it claims — the same statement with the `¬`
dropped, i.e. asserting the spec HOLDS at that point — and built that on both
sides. The exit codes invert cleanly (forged-on-gold 0, forged-on-rival 1) against
the real witness's (gold 1, rival 0), so gold's exit code demonstrably tracks the
CLAIM and not the file's shape. No case here is hollow.

Two further CORRECT reshapes were written by that pass and both verify (exit 0),
beyond the two positives shipped below: one that tests the current-token equality
BEFORE the absence guard (re-nesting the absence case inside the equality branch,
so the clause order of the impl no longer mirrors the spec's), and one that scans
`alternateTokens.reverse` with the operands of the comparison FLIPPED
(`storedToken == t`). So the spec is not over-fit to the frozen scan direction,
comparison orientation, or guard order either.

Each rival is additionally OBSERVABLY different from gold, checked directly
rather than inferred from the rival's build failing: for every reject case the
audit pass elaborated `rival <args> ≠ goldImpl <args> := by decide` at that
case's own witness point, with gold's impl and every rival's impl renamed into a
single file (exit 0). So no case here is a merely-reshaped correct impl whose
rejection would attest to a tactic mismatch. Witness non-redundancy was spot-
checked the same way: `partial-wrong-width`'s rival survives
`no-alternate-path`'s witness (exit 1), so the two are not interchangeable and
each case needs the witness it carries.
"""
from pathlib import Path

INSTANCE = "django__django-16631"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence; assert it matched so that silent drift
    (Solution.lean edited underneath this manifest) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Every anchor below lies STRICTLY inside the impl region
# (or, for the positives, the proof region) and is unique across the file.
# ---------------------------------------------------------------------------

# The whole gold impl (used by variants that restructure the entire body).
_IMPL = """def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision := Id.run do
  let mut tokenVerified := false
  if storedToken = [] then
    tokenVerified := false
  else
    tokenVerified := (storedToken == currentToken)
  if !tokenVerified then
    let mut alternateMatched := false
    for t in alternateTokens do
      if t == storedToken then
        alternateMatched := true
    if storedToken != [] && alternateMatched then
      return .acceptedAlternate
    else
      return .rejected
  return .acceptedCurrent
"""

# The absence guard + current-token comparison.
_GUARD = """  if storedToken = [] then
    tokenVerified := false
  else
    tokenVerified := (storedToken == currentToken)"""

# The alternate-scan comparison.
_CMP = "      if t == storedToken then"

# The whole alternate scan (loop header + comparison + flag set).
_SCAN = """    for t in alternateTokens do
      if t == storedToken then
        alternateMatched := true
"""

# The alternate-acceptance dispatch.
_DISPATCH = """    if storedToken != [] && alternateMatched then
      return .acceptedAlternate
    else
      return .rejected"""

_DISPATCH_GUARD = "    if storedToken != [] && alternateMatched then"

# The gold proof body (swapped only by the positives, which must re-close the
# byte-identical `theorem correct_validateToken` statement for a new impl).
_PROOF = """  intro st ct alts
  have loop_lemma :
      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
        = (alts.any (fun t => t == st)) := by
    have gen : ∀ (b : Bool),
        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
          = (b || alts.any (fun t => t == st)) := by
      intro b
      induction alts generalizing b with
      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
      | cons h tl ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, Id.instMonad] at *
        by_cases hh : (h == st) = true
        · simp only [hh, if_pos, ih]
          simp [hh, List.any_cons]
        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
          simp [hh, List.any_cons]
    have := gen false
    simpa using this
  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
    constructor
    · intro h
      rw [List.any_eq_true] at h
      obtain ⟨x, hx, hxeq⟩ := h
      exact ⟨x, hx, by simpa using hxeq⟩
    · rintro ⟨x, hx, hxeq⟩
      rw [List.any_eq_true]
      exact ⟨x, hx, by simp [hxeq]⟩
  unfold implementation_validateToken
  simp only [Id.run, bind, pure, Id.instMonad]
  rw [loop_lemma]
  unfold problem_spec_validateToken
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2
    simp only [h1] at *
    have hbeq : (st == ct) = true := by simp [h2]
    simp [hbeq]
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hne : (st != ([] : List Char)) = true := by simp [h1]
    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
    split <;> rfl
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hany : (alts.any (fun t => t == st)) = false := by
      by_contra hc
      have : (alts.any (fun t => t == st)) = true := by
        cases h : (alts.any (fun t => t == st)) with
        | false => exact absurd h hc
        | true => rfl
      exact h3 (any_char.mp this)
    simp only [h1, hbeq]
    simp [hany]
"""

# The shared `List.any`-vs-existential bridge, reused by both positive proofs.
_ANY_BRIDGE = """  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
    constructor
    · intro h
      rw [List.any_eq_true] at h
      obtain ⟨x, hx, hxeq⟩ := h
      exact ⟨x, hx, by simpa using hxeq⟩
    · rintro ⟨x, hx, hxeq⟩
      rw [List.any_eq_true]
      exact ⟨x, hx, by simp [hxeq]⟩
"""


# ===========================================================================
# POSITIVE CONTROLS (must VERIFY, else SPEC-TOO-STRONG)
# ===========================================================================

# --- pos-functional-form ---------------------------------------------------
# A CORRECT impl in a genuinely different form: a pure functional if/else
# cascade with no `Id.run do`, no `let mut` and no `for`, with the alternate
# scan expressed as `List.any`. Same decision on every input. The proof is
# re-closed for the new shape (no loop lemma is needed, since there is no loop);
# the `theorem correct_validateToken` STATEMENT is byte-identical.
_POS_FUNCTIONAL = _swap(
    _swap(_BASE, _IMPL, """def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision :=
  if storedToken = [] then .rejected
  else if storedToken = currentToken then .acceptedCurrent
  else if alternateTokens.any (fun t => t == storedToken) then .acceptedAlternate
  else .rejected
"""),
    _PROOF,
    "  intro st ct alts\n" + _ANY_BRIDGE + """  unfold implementation_validateToken problem_spec_validateToken
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2; subst h2; simp [h1]
  · intro h1 h2 h3
    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
    simp [h1, h2, hany]
  · intro h1 h2 h3
    have hany : (alts.any (fun t => t == st)) ≠ true := fun hc => h3 (any_char.mp hc)
    simp [h1, h2, hany]
""")

# --- pos-early-return ------------------------------------------------------
# The nagini `pos-control-A` reshape, on this carrier: keep the imperative
# skeleton but decide each case with an EARLY RETURN instead of threading a
# `tokenVerified` flag, and compute the two membership facts in a different
# order (the absence and current-token cases are settled and returned BEFORE
# the alternate scan is entered at all, where gold computes the flag first and
# dispatches once). Same decision on every input; the absence re-check on the
# alternate path is dropped as redundant, which it provably is once the absent
# case has already returned. Proof re-closed for the new shape.
_POS_EARLY = _swap(
    _swap(_BASE, _IMPL, """def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision := Id.run do
  if storedToken = [] then
    return .rejected
  if storedToken == currentToken then
    return .acceptedCurrent
  let mut alternateMatched := false
  for t in alternateTokens do
    if t == storedToken then
      alternateMatched := true
  if alternateMatched then
    return .acceptedAlternate
  return .rejected
"""),
    _PROOF,
    """  intro st ct alts
  have loop_lemma :
      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
        = (alts.any (fun t => t == st)) := by
    have gen : ∀ (b : Bool),
        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
          = (b || alts.any (fun t => t == st)) := by
      intro b
      induction alts generalizing b with
      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
      | cons h tl ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, Id.instMonad] at *
        by_cases hh : (h == st) = true
        · simp only [hh, if_pos, ih]
          simp [hh, List.any_cons]
        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
          simp [hh, List.any_cons]
    have := gen false
    simpa using this
""" + _ANY_BRIDGE + """  unfold implementation_validateToken
  simp only [Id.run, bind, pure, Id.instMonad]
  rw [loop_lemma]
  unfold problem_spec_validateToken
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2
    have hbeq : (st == ct) = true := by simp [h2]
    simp [h1, hbeq]
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
    simp [h1, hbeq, hany]
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hany : (alts.any (fun t => t == st)) ≠ true := fun hc => h3 (any_char.mp hc)
    simp [h1, hbeq, hany]
""")


# ===========================================================================
# ADMISSIBILITY (must VERIFY, else PRECOND-TOO-STRONG)
# ===========================================================================

# --- admiss-ground-alternate -----------------------------------------------
# Landed by audit; the port had recorded this whole lane as vacuous "because the
# frozen obligation has no precondition hypothesis". That is not the right test on
# a TOTAL carrier. With an unguarded `∀` there is no precondition to be
# over-strong, but the same failure is still observable as the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input — a spec that pinned an impossible
# decision there would be discharged by no impl at all, and the reject lane cannot
# see that (every rival "fails" a spec nothing can satisfy). So the analogue is a
# positive that discharges the spec predicate at that concrete input BY EVALUATION,
# as a `have`, before closing the frozen obligation verbatim.
#
# The ground input is the F2P-shaped one: a PRESENT stored token that does NOT
# verify against the currently-valid token but DOES appear among the
# additionally-accepted tokens — the configuration the F2P test sets up, and the
# only cell in which the fix is observable at all.
#
# Two `have`s, because the first alone would be too weak: `_ground` says the spec
# holds of whatever the impl returns there, which `decide` would also close if that
# input landed in a rejecting branch. `_fires` EVALUATES the decision at that input
# down to `.acceptedAlternate`, pinning the admission to the alternate-acceptance
# branch and to the decision value that branch must report.
#
# Measured load-bearing rather than assumed: spliced onto the `no-alternate-path`
# rival both `have`s FAIL (exit 1, "`decide` proved that the proposition … is
# false"), and likewise on `alternate-decided-as-current` (which takes the right
# branch but reports the wrong value). Nothing is assumed: no new declaration, no
# axiom or assumption token, the `theorem correct_validateToken` statement stays
# byte-identical, and the frozen tactic body follows unchanged.
_ADMISS_GROUND = _swap(
    _BASE, "  intro st ct alts\n",
    """  have _ground : problem_spec_validateToken
      ['a'] ['b'] [['a']]
      (implementation_validateToken ['a'] ['b'] [['a']]) := by
    unfold problem_spec_validateToken implementation_validateToken
    decide
  have _fires : implementation_validateToken ['a'] ['b'] [['a']]
      = VerifyDecision.acceptedAlternate := by
    unfold implementation_validateToken
    decide
  intro st ct alts
""")


# ===========================================================================
# UNIQUENESS RIVALS (must be REJECTED). The gold proof body is carried over
# VERBATIM in every rival, so nothing is weakened and the rejection is the
# spec's, not a deleted obligation's.
# ===========================================================================

# --- no-alternate-path : the alternate-acceptance decision is never produced.
_RIVAL_NO_ALT = _swap(_BASE, _DISPATCH, "    return .rejected")

# --- prior-before-current : priority inversion. The alternate scan runs FIRST
# and wins, so a present token equal to the current token is accepted against
# an alternate whenever it also appears in the alternate list.
_RIVAL_PRIOR_FIRST = _swap(_BASE, _IMPL, """def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision := Id.run do
  let mut alternateMatched := false
  for t in alternateTokens do
    if t == storedToken then
      alternateMatched := true
  if storedToken != [] && alternateMatched then
    return .acceptedAlternate
  if storedToken = [] then
    return .rejected
  if storedToken == currentToken then
    return .acceptedCurrent
  return .rejected
""")

# --- partial-wrong-width : correct EXCEPT that the alternate path is refused
# for every stored token whose width is not one character (a value sub-domain).
# A near-miss. The REFUSED class is deliberately the one that contains the real
# token's shape: the real token is a fixed-width digest many characters wide, so
# a refined patch of this rival refuses the alternate path on exactly the tokens
# the system actually produces. (An earlier form of this case accepted every
# width EXCEPT one character, which inverted that: its refused class was a width
# the real fixed-width token never has, so its refined patch would have honored
# every real token and RESOLVED, making the non-resolution argument false. The
# spec-probe half was sound either way — the rival violates clause 3 on its
# refused class and its witness discriminates — but a reject case's `refinement`
# has to be true, so the class was flipped to the reachable one.)
_RIVAL_PARTIAL = _swap(
    _BASE, _DISPATCH_GUARD,
    "    if storedToken != [] && storedToken.length == 1 && alternateMatched then")

# --- alternates-vs-current : each alternate is compared against the CURRENT
# token instead of the stored one, so the scan reports whether the current
# token is among the alternates — a fact independent of the stored token.
_RIVAL_MISCOMPARE = _swap(_BASE, _CMP, "      if t == currentToken then")

# --- accept-any-present : over-fires. Every present mismatching token is
# accepted against an alternate, whether or not any alternate matches.
_RIVAL_ACCEPT_ANY = _swap(_BASE, _DISPATCH, """    let _ := alternateMatched
    if storedToken != [] then
      return .acceptedAlternate
    else
      return .rejected""")

# --- absent-token-verified : the absent-token guard decides the WRONG way — an
# absent stored token is marked verified instead of unverified, so a request
# carrying no token at all is accepted against the current token.
#
# The obvious spelling of this attack is to DELETE the guard and let the absent
# token fall through to the comparison
# (`tokenVerified := (storedToken == currentToken)` alone). That rival does
# violate clause 1 on this carrier and its witness discriminates — but its ONLY
# divergence from gold is at `storedToken = [] ∧ currentToken = []`, machine-
# enumerated over the small domain: 13 divergence points, every one of them with
# BOTH tokens empty. The current token is a fixed-width digest that is never
# empty, so a refined patch of that rival agrees with gold on every input the
# system can present and WOULD resolve — the non-resolution argument would be
# false and the case would attest to a tactic mismatch rather than to the spec.
# Deciding the guard the wrong way instead makes the divergence reachable: it
# fires whenever the stored token is absent, whatever the current token is.
_RIVAL_DROP_GUARD = _swap(_BASE, _GUARD, """  if storedToken = [] then
    tokenVerified := true
  else
    tokenVerified := (storedToken == currentToken)""")

# --- alternate-decided-as-current : the alternate path fires on exactly the
# right inputs, but reports the CURRENT-token decision instead of the alternate
# one. Added by audit: every other rival attacks WHICH BRANCH is taken, so all of
# them are refutable by a witness that only has to see the accept/reject split.
# This one takes the correct branch and returns the wrong VALUE, which is the
# distinction between the two acceptance decisions — clause 3 pinning
# `.acceptedAlternate` specifically, rather than merely "accepted".
_RIVAL_ALT_AS_CURRENT = _swap(_BASE, _DISPATCH, """    if storedToken != [] && alternateMatched then
      return .acceptedCurrent
    else
      return .rejected""")

# --- scan-head-only : the alternate scan inspects only the FIRST entry of the
# accepted-alternates list instead of every entry. Added by audit: the existing
# rivals either never fire the alternate path, always fire it, or key it on the
# wrong operand — none of them keys it correctly but scans an incomplete PORTION
# of the list, which is the totality half of clause 3 (acceptance must hold for
# `∃ t ∈ alternateTokens`, not for the head alone).
_RIVAL_SCAN_HEAD = _swap(_BASE, _SCAN, """    if alternateTokens.headI == storedToken then
      alternateMatched := true
""")


# ---------------------------------------------------------------------------
# Witnesses. Each negates the spec predicate at one concrete input. The carrier
# is transparent, so `decide` closes and no witness binds a hypothesis (nothing
# to be jointly unsatisfiable). Verified BOTH ways with scripts/lean_verify.sh.
# ---------------------------------------------------------------------------

def _wit(stored: str, current: str, alternates: str) -> str:
    args = f"{stored} {current} {alternates}"
    return (
        "example : ¬ problem_spec_validateToken\n"
        f"    {args}\n"
        f"    (implementation_validateToken {args}) := by\n"
        "  unfold problem_spec_validateToken implementation_validateToken\n"
        "  decide"
    )


# Present two-character token, differs from current, IS among the alternates.
# Clause 3: gold => .acceptedAlternate, rival => .rejected.
_WIT_NO_ALT = _wit("['a', 'b']", "['x', 'y']", "[['a', 'b']]")

# Present token EQUAL to the current token that also appears among the
# alternates — the exact overlap where priority is observable. Clause 2:
# gold => .acceptedCurrent, rival => .acceptedAlternate.
_WIT_PRIOR_FIRST = _wit("['a']", "['a']", "[['a']]")

# A stored token WIDER than one character, present in the alternate list — the
# sub-domain this near-miss abandons, and the width class the real fixed-width
# token actually inhabits. Clause 3: gold => .acceptedAlternate, rival =>
# .rejected. Three characters rather than two so it is not the same probe point
# as `no-alternate-path`'s witness.
_WIT_PARTIAL = _wit("['p', 'q', 'r']", "['x', 'y', 'z']", "[['p', 'q', 'r']]")

# The stored token is absent from the alternate list, but the CURRENT token is
# present in it — so a scan keyed on the wrong operand reports a match where
# none exists. Clause 4: gold => .rejected, rival => .acceptedAlternate.
_WIT_MISCOMPARE = _wit("['a']", "['b']", "[['b']]")

# Present token, differs from current, EMPTY alternate list (the configuration
# in which no alternate can possibly match — the only witness varying
# `alternateTokens` to `[]`). Clause 4: gold => .rejected, rival =>
# .acceptedAlternate.
_WIT_ACCEPT_ANY = _wit("['a']", "['b']", "[]")

# ABSENT stored token against a PRESENT current token — the only witness varying
# `storedToken` to `[]`, and a point the rival reaches on a realistic current
# token rather than only on an empty one. Clause 1: gold => .rejected, rival =>
# .acceptedCurrent.
_WIT_DROP_GUARD = _wit("[]", "['a']", "[]")

# Present token, differs from current, IS among the alternates — the cell where
# clause 3 pins `.acceptedAlternate` specifically. Discriminates on the DECISION
# VALUE rather than on the accept/reject split: gold => .acceptedAlternate,
# rival => .acceptedCurrent (both "accepted", so a witness that only distinguished
# acceptance from rejection would NOT catch this rival).
_WIT_ALT_AS_CURRENT = _wit("['a']", "['b']", "[['a']]")

# The stored token sits at the TAIL of a two-entry alternate list, so a scan that
# inspects only the head misses it. The only witness giving `alternateTokens` more
# than one entry. Clause 3: gold => .acceptedAlternate, rival => .rejected.
_WIT_SCAN_HEAD = _wit("['a']", "['b']", "[['c'], ['a']]")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a CORRECT impl in a genuinely different form: a pure functional "
                  "if/else cascade (no `Id.run do`, no `let mut`, no `for`; the "
                  "alternate scan as `List.any`). Every one of the four clauses still "
                  "holds, and the proof is re-closed for the new shape with the "
                  "`theorem correct_validateToken` statement byte-identical (no loop "
                  "lemma is needed since there is no loop). If it fails to verify, the "
                  "spec is over-fit to the imperative skeleton => SPEC-TOO-STRONG."},
    {"id": "pos-early-return", "kind": "soundness", "expect": "verify",
     "module": _POS_EARLY,
     "rationale": "the nagini pos-control-A reshape on this carrier: the imperative "
                  "skeleton is kept but each case is settled by an EARLY RETURN rather "
                  "than by threading a verification flag, and the two membership facts "
                  "are computed in a different order (absence and the current-token "
                  "case return before the alternate scan is entered). Semantically "
                  "identical; the redundant absence re-check on the alternate path is "
                  "dropped. Proof re-closed. If it fails to verify, the spec is "
                  "over-fit to one control-flow order => SPEC-TOO-STRONG."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-ground-alternate", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_GROUND,
     "rationale": "confirms the obligation is SATISFIABLE (non-vacuous) at the "
                  "F2P-shaped input rather than only in the abstract: a PRESENT "
                  "stored token that does not verify against the currently-valid "
                  "token but DOES appear among the additionally-accepted tokens — "
                  "the configuration the F2P test sets up, and the only cell in "
                  "which the fix is observable. The frozen `∀` carries no "
                  "precondition hypothesis, so the nagini precondition-admission "
                  "probes (admiss-A / admiss-B) have no binder to attack; on a "
                  "total carrier the honest analogue is to discharge the spec "
                  "predicate at that concrete input by evaluation, as a `have`, "
                  "then close the frozen obligation verbatim. Two `have`s, because "
                  "`_ground` alone would also close if the input landed in a "
                  "rejecting branch: `_fires` evaluates the decision there to "
                  "`.acceptedAlternate`, pinning the admission to the "
                  "alternate-acceptance branch and to the value it must report. "
                  "Measured load-bearing — both `have`s FAIL on the "
                  "`no-alternate-path` and `alternate-decided-as-current` rivals. "
                  "If it fails to verify, the modeled behavior is unsatisfiable at "
                  "exactly a normal F2P input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "no-alternate-path", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_ALT, "witness": _WIT_NO_ALT,
     "refinement": "its faithful real patch is the UNFIXED behavior: a stored token "
                   "that does not verify against the currently-valid token drops the "
                   "principal outright, with the additionally-accepted tokens never "
                   "consulted. That is precisely the state the F2P test was written to "
                   "detect — its first phase asserts the principal SURVIVES when the "
                   "token verifies only under an additionally-configured key. The patch "
                   "would leave that assertion failing and would NOT resolve, so a "
                   "verifying rival here is a true verify-does-not-imply-resolve break.",
     "rationale": "attacks clause 3 (present, differs from current, matches an "
                  "alternate => .acceptedAlternate): the rival can never return "
                  "`.acceptedAlternate` at all. Witness varies `storedToken` to a "
                  "two-character token present in `alternateTokens`; gold gives "
                  "`.acceptedAlternate`, the rival `.rejected`."},
    {"id": "prior-before-current", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PRIOR_FIRST, "witness": _WIT_PRIOR_FIRST,
     "refinement": "its faithful real patch consults the additionally-accepted tokens "
                   "BEFORE the currently-valid one, so a token that is already valid "
                   "under the current configuration takes the alternate-acceptance path "
                   "whenever it also appears among the alternates. The spec pins that "
                   "case to the current-token decision, and the two decisions carry "
                   "DIFFERENT glue (mapping.md 'Effect glue'): the alternate path "
                   "rotates the request's session state, the current path leaves it "
                   "untouched. The F2P's second phase re-checks the principal after "
                   "the additional key is withdrawn and requires the already-valid "
                   "token to be honored on the untouched path, and a P2P test asserts "
                   "the ordinary verification case changes no state; the patch would "
                   "rotate state where none should change and would NOT resolve.",
     "rationale": "attacks clause 2 (present and equal to current => "
                  "`.acceptedCurrent`), which is what makes the current token take "
                  "PRIORITY. Witness probes the overlap where priority is observable: "
                  "`storedToken = currentToken` AND that token also in "
                  "`alternateTokens`; gold gives `.acceptedCurrent`, the rival "
                  "`.acceptedAlternate`."},
    {"id": "partial-wrong-width", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL, "witness": _WIT_PARTIAL,
     "refinement": "its faithful real patch conditions the alternate-acceptance path "
                   "on the WIDTH of the stored token, honoring it only for tokens of a "
                   "single character. Acceptance must be total over present mismatching "
                   "tokens, and the real token is a fixed-width digest many characters "
                   "wide — so the refused class is the class every real token falls in. "
                   "The refined patch therefore never takes the alternate-acceptance "
                   "path on any input the system can actually present: it drops the F2P "
                   "principal on the very configuration the test sets up, and would NOT "
                   "resolve. Note the direction is load-bearing: the mirror rival "
                   "(refuse only single-character tokens) violates the same clause on "
                   "the same carrier, but its refused class is a width no real digest "
                   "has, so its refined patch WOULD resolve and the non-resolution "
                   "argument would be false.",
     "rationale": "attacks clause 3 on a VALUE SUB-DOMAIN. A near-miss: it agrees with "
                  "gold on single-character stored tokens and diverges on every wider "
                  "one, so it gets its OWN witness inside the refused class rather than "
                  "sharing `no-alternate-path`'s. Machine-checked non-redundancy: this "
                  "rival's own witness point is where it and gold disagree, and the two "
                  "witnesses are not interchangeable. Gold gives `.acceptedAlternate`, "
                  "the rival `.rejected`."},
    {"id": "alternates-vs-current", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MISCOMPARE, "witness": _WIT_MISCOMPARE,
     "refinement": "this is the nagini site-B mis-keying defect as it becomes "
                   "observable HERE. The producer of the additionally-accepted tokens "
                   "is not modeled in this bundle, but a producer that derived every "
                   "alternate under the CURRENT configuration instead of each "
                   "additional one yields a list whose entries track the current token "
                   "rather than the stored one — making the scan answer a question "
                   "independent of the stored token, which is what this rival does. On "
                   "the F2P the stored token was derived under the WITHDRAWN key, so it "
                   "would match no such entry, the acceptance path would never fire, "
                   "and the principal would be dropped: it would NOT resolve.",
     "rationale": "attacks clause 4 (present, differs from current, matches NO "
                  "alternate => .rejected) by keying the scan on the wrong operand. "
                  "Witness varies `alternateTokens` to a singleton holding the CURRENT "
                  "token while `storedToken` is absent from it: gold gives `.rejected`, "
                  "the rival `.acceptedAlternate`."},
    {"id": "accept-any-present", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ACCEPT_ANY, "witness": _WIT_ACCEPT_ANY,
     "refinement": "its faithful real patch accepts ANY present stored token on the "
                   "alternate path without checking it against the additionally-"
                   "accepted tokens at all — an authentication bypass, since an "
                   "arbitrary non-empty token would be honored. A P2P test asserts that "
                   "a stored token matching neither the current nor any additional key "
                   "drops the principal; the patch would keep it and would NOT resolve.",
     "rationale": "the ONLY rival attacking clause 4 in the OVER-acceptance direction "
                  "(every other rival under-accepts), and the only one probing an EMPTY "
                  "`alternateTokens`. Without it a spec that failed to bound the "
                  "acceptance path would go untested. Witness: present token, differs "
                  "from current, no alternates at all; gold gives `.rejected`, the "
                  "rival `.acceptedAlternate`."},
    {"id": "absent-token-verified", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_GUARD, "witness": _WIT_DROP_GUARD,
     "refinement": "its faithful real patch decides the no-stored-token case the wrong "
                   "way: a request carrying NO token is treated as having verified "
                   "against the current token, so it is accepted and the principal is "
                   "kept instead of being dropped — an authentication bypass on the "
                   "anonymous path, reached on EVERY tokenless request rather than only "
                   "on a degenerate configuration. A P2P test asserts that a request "
                   "with no stored token yields the anonymous principal; the patch would "
                   "return a real one and would NOT resolve.",
     "rationale": "the ONLY rival attacking clause 1 (`storedToken = []` => "
                  ".rejected), and the only witness varying `storedToken` to `[]`. "
                  "Clause 1 is an independent top-level clause of the postcondition, "
                  "and the pre-patch code already had it right, so nagini carried no "
                  "rival for it — an unattacked clause is an untested one. Gold gives "
                  "`.rejected`, the rival `.acceptedCurrent`."},
    {"id": "alternate-decided-as-current", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALT_AS_CURRENT, "witness": _WIT_ALT_AS_CURRENT,
     "refinement": "its faithful real patch takes the additionally-accepted-token path "
                   "on exactly the right inputs but wires it to the CURRENT-token "
                   "decision's glue, so the request's session state is left untouched "
                   "where the accepted-alternate path must refresh it (mapping.md "
                   "'Effect glue': the alternate decision cycles the session key and "
                   "rewrites the stored token; the current decision changes nothing). "
                   "The F2P asserts the session key CHANGES on the first phase, and its "
                   "second phase then re-checks the principal after the additional key "
                   "is withdrawn — which only succeeds because the stored token was "
                   "refreshed under the current configuration. Leaving the state "
                   "untouched fails the first assertion outright and strands the stored "
                   "token under the withdrawn key for the second, so it would NOT "
                   "resolve.",
     "rationale": "added by audit. Attacks clause 3's pinning of the decision VALUE, "
                  "not the branch: this rival takes the correct branch on the correct "
                  "inputs and returns `.acceptedCurrent` there. Every pre-existing "
                  "rival changes which branch fires, so all of them are refutable by a "
                  "witness that only sees the accept-vs-reject split; none of them "
                  "tests that the two ACCEPTANCE decisions are distinguished from each "
                  "other. Gold gives `.acceptedAlternate`, the rival "
                  "`.acceptedCurrent`."},
    {"id": "scan-head-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SCAN_HEAD, "witness": _WIT_SCAN_HEAD,
     "refinement": "its faithful real patch consults only the FIRST of the "
                   "additionally-accepted tokens instead of iterating all of them, so a "
                   "stored token accepted under any but the first additional key is "
                   "dropped. The additional keys are a configured sequence of arbitrary "
                   "length and the matching one need not be first; a patch that stops "
                   "after one entry honors the configuration only by luck of ordering "
                   "and would NOT reliably resolve.",
     "rationale": "added by audit. Attacks the TOTALITY half of clause 3 — acceptance "
                  "is pinned for `∃ t ∈ alternateTokens, t = storedToken`, not for the "
                  "head alone. No pre-existing rival keys the scan correctly while "
                  "scanning an incomplete portion of the list (they never fire, always "
                  "fire, or compare the wrong operand), and no pre-existing witness "
                  "gives `alternateTokens` more than ONE entry, so the quantifier's "
                  "range was never probed. Witness puts the match at the tail: gold "
                  "gives `.acceptedAlternate`, the rival `.rejected`."},
]

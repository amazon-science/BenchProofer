# properties.py — G-PBT falsification battery for sympy__sympy-19637 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region is edited — the theorem STATEMENT and the frozen proof body are left
# untouched), checked by variant_scope + the Lean verifier. Every expect="reject"
# case carries a refutation `witness`: a self-contained snippet that ELABORATES
# against the rival and FAILS on the frozen solution, so the rejection is
# attributable to the spec and not to a tactic script that merely stopped matching a
# reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   implementation_kernSHit (parenBranch : Bool) (s : List Char) : Except Unit Bool
#   models the flag computation inside a string-preprocessing helper's optional
#   bracket-handling branch. `parenBranch` is the outer branch gate; `s` is the
#   post-transform character sequence, of which only whether a space is present is
#   observed. The SINGLE postcondition pins the whole result to ONE equation:
#     (P) result = Except.ok (parenBranch && s.contains ' ')
#   which bundles two independent obligations:
#     (P-well)  the result is ALWAYS `Except.ok _` — the routine never aborts
#               (the failure the fix removes: reading a marker before it is bound).
#     (P-val)   the flag equals the conjunction `parenBranch && s.contains ' '`:
#               set exactly when the branch is active AND a space was present (a
#               fresh marker is then substituted for the spaces and is necessarily
#               a member); unset in every other case.
#   The carrier is FULLY TRANSPARENT: `parenBranch : Bool` and the observed
#   `s.contains ' '` are both decidable at concrete inputs, so no conditioning on an
#   opaque callee is needed — every reject witness states `¬ P …` at a literal
#   input and closes by `simp`. (`decide` is NOT usable: `Except Unit Bool` carries
#   no `DecidableEq` instance, so `simp` — which reduces the `Except.ok`/`&&`/
#   `List.contains` and discharges the residual boolean disequality — is the tactic
#   that closes both halves.)
#
# CARRIER NARROWING vs nagini. The nagini sibling modeled the substitution key as a
# three-valued `Optional[bool]`: None (no marker created), True (marker created and
# a member), False (marker created but NOT a member) — and split the entered/
# key-present domain into FOUR input classes. This backend folds that key into the
# single decidable observable `s.contains ' '`: post-substitution a freshly-chosen
# marker is NECESSARILY present whenever a space was present, so the "created but
# not a member" class (nagini's (True, False)) does not exist on this carrier. Two
# consequences for the port:
#   * nagini's NARROW (True,False)-only rival has an EMPTY sub-domain on this
#     folded carrier, so it cannot be ported as-is; `flag-as-agreement` is its
#     lean counterpart (a rival wrong at exactly one corner). nagini's VALUE-SWAP
#     rival, by contrast, DOES port and is now shipped as `negate-membership` —
#     an earlier revision of this file dropped it as a "duplicate of
#     always-false", which is measurably WRONG: negating the observable gives
#     `parenBranch && !s.contains ' '`, which returns `true` at (true, ['a'])
#     where always-false returns `false`, so it is wrong at a DIFFERENT corner
#     and additionally violates the spec at (true, [' ']). Measured by
#     evaluation: at (true,['a']) spec/always-false/value-swap are
#     false/false/TRUE. The two rivals disagree, so the collapse claim was false.
#   * conversely, nagini's precondition `Implies(not entered, key is None)` (a
#     marker only exists inside the branch) has NO counterpart here — the lean
#     obligation is `∀ parenBranch s, P …` with no precondition hypothesis — so the
#     input `(parenBranch = false, space present)` is REACHABLE and lets us attack
#     the `parenBranch` conjunct of (P-val) independently (rival `ignore-branch-
#     gate`), a distinction nagini's carrier could not probe.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION. nagini's directive-5 probe is VACUOUS for this
#     instance even in nagini (both inputs are value types, no Acc(x,1/2) heap); on
#     lean it is doubly vacuous — referential transparency admits no aliasing or
#     write-back into a read-only input. See 'assessment'. No substitute fabricated.
#   * DIVERGENCE / NON-TERMINATION. Re-measured with real builds rather than
#     asserted. This bundle sets NO `loom.semantics.termination` option (it is a
#     plain lean `def` carrier), so the total-carrier disposition applies: the
#     verifier discharges termination as part of accepting the file. Measured two
#     ways. (a) A plain `def spin : Nat → Bool | n => spin (n+1)` inside the impl
#     region makes the whole variant fail to elaborate — `fail to show
#     termination for spin / failed to infer structural recursion` — so a
#     measure-less loop is rejected by the carrier before the spec is ever
#     consulted; the rejection attributes nothing to THIS spec, which is why no
#     such case is shipped. (b) A `partial def spin` DOES elaborate, and the
#     resulting rival `Except.ok (parenBranch && s.contains ' ' && spin 0)` is
#     rejected — but `partial` is a banned witness token (pbt_witness
#     _WITNESS_BANNED) and, measured, the refutation witness at (true, [' '])
#     fails on the RIVAL with `unsolved goals ⊢ spin 0 = false`: `spin` is opaque,
#     so no witness can refute it and the case would land `witness-unproven`.
#     So the class is genuinely unshippable here, and the honest label is that a
#     divergent impl is either carrier-rejected (a) or witness-irrefutable (b) —
#     not that the concept is vacuous. The nagini sibling carries no divergence
#     case either.
#   * AXIOM_TESTS. nagini's axiom lane is empty (no @ContractOnly axiom); the marker
#     step is modeled deeply. The axiom lane is G-AX's job; this gate ignores it.
#
# THE LOOP-SHAPED POSITIVE IS NOW SHIPPED (`pos-for-loop-scan`). An earlier
# revision of this file recorded the `for c in s do if c == ' ' then hit := true`
# scan as UNCERTAIN — behaviourally identical to the frozen impl, the strongest
# available soundness positive (spec_guide §0.3's faithful imperative skeleton),
# but "no proof closed here" after five scripted attempts that died on `maximum
# recursion depth` inside `simp`. That was a proof-engineering gap, correctly not
# claimed as SPEC-TOO-STRONG — and it has now been CLOSED, so the honest
# disposition is to ship the case rather than to keep the gap on record.
# What the earlier attempts were missing is that the `Id.run do let mut … for …`
# elaborate to a `forIn` whose body is wrapped in `do pure PUnit.unit; pure
# (ForInStep.yield …)` — NOT the bare `ForInStep.yield (f c r)` shape that
# `List.forIn_yield_eq_foldl` is stated over — so the rewrite silently does not
# fire and unguided `simp` then loops on the un-normalised term. The proof that
# closes does the normalisation explicitly, in two `have`s inside the tactic body:
# `body_norm` proves the elaborated body equal to the bare `ForInStep.yield
# (decide (c = ' ') || r)` form by `congr 1; funext c r` and a `by_cases` on
# `c = ' '` (unfolding `Id.instMonad`/`Bind.bind` to discharge the `pure`
# wrapper), and `loop_gen` then rewrites by `List.forIn_yield_eq_foldl` and does
# a `cons`/`nil` induction generalising the accumulator. No new axiom/lemma/sorry
# (both are `have`s, not top-level declarations), statement byte-identical.
#
# LANES THAT DO PORT, CONTRARY TO AN EARLIER READING OF THIS FILE:
#   * ADMISSIBILITY. An earlier revision of this battery recorded the lane as N/A
#     on the ground that "the lean obligation carries NO precondition hypothesis,
#     so nothing could be PRECOND-TOO-STRONG". That reason is wrong, and the lane
#     is now carried (`admiss-f2p-shaped-ground`). The analogue of
#     PRECOND-TOO-STRONG on a TOTAL carrier is not a precondition to instantiate:
#     it is the obligation being UNSATISFIABLE at exactly an F2P-shaped input,
#     which a positive that discharges the obligation AT that concrete input — by
#     evaluation, as a `have`, before closing the frozen obligation verbatim —
#     tests directly. nagini's `admissibility-f2p-shaped` defended the value
#     precondition `Implies(not entered, key is None)` at (entered=True,
#     key=None); the lean counterpart discharges `problem_spec_kernSHit true ['a']
#     (implementation_kernSHit true ['a'])` by `rfl`, i.e. it shows the modeled
#     behaviour is satisfiable at the branch-active/no-space point rather than
#     only in the abstract. Measured expressible: `rfl` closes it (exit 0), so the
#     omission was a gap, not a carrier limit.
#
# SPEC-STRENGTH PROBES RUN AND NOT SHIPPED (no case needed; recorded so the next
# reader does not re-run them). Six further WRONG impls were built against the
# frozen spec, aimed at what the shipped rivals leave alone — a length side
# condition (`… && s.length < 3`), an exactly-one-space count (`s.count ' ' == 1`),
# a widened whitespace notion (`… || s.contains '\t'`), an abort on the empty
# sequence, a head-only test (`s.head? == some ' '`), and the DISJUNCTION
# (`parenBranch || s.contains ' '`). All six were REJECTED by the frozen spec
# (exit 1 each), and each one's disagreement with the spec was independently
# confirmed by evaluation at a concrete input rather than inferred from the build
# failure. No spec hole was found: the single equation (P) pins the result totally,
# so any deviation at any input is caught. Three further CORRECT reshapes were
# also built: space-presence via `s.reverse.contains ' '` (verifies, closed by
# `List.contains_reverse`), via a recursive impl-region helper `scanSpace`
# (verifies, closed by a `cons`/`nil` induction using `BEq.comm`), and via
# `!(s.filter (· == ' ')).isEmpty` (NOT closed — `simp` hits `maximum recursion
# depth`; a proof-engineering gap, recorded as uncertain, NOT a soundness hole,
# since the `reverse` and `scanSpace` reshapes already establish the spec admits a
# different computation of the observable and the loop positive establishes it for a
# different control shape).
from pathlib import Path

INSTANCE = "sympy__sympy-19637"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every variant (positives and rivals) swaps THIS block and nothing else,
# so the frozen spec AND the frozen proof body are shared byte-for-byte.
_IMPL = (
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do\n"
    "  let mut hit : Bool := false\n"
    "  if parenBranch then\n"
    "    if s.contains ' ' then\n"
    "      -- a fresh marker is substituted for the spaces, so it now occurs in the\n"
    "      -- string: the membership test yields `true`\n"
    "      hit := true\n"
    "    else\n"
    "      -- no space was present, so the flag stays unset\n"
    "      hit := false\n"
    "  return Except.ok hit"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen PROOF body, lying entirely inside proof-start/proof-end and unique in
# the file. Two cases below re-prove for a reshaped impl / prepend a ground `have`;
# both edit only this block, so the theorem STATEMENT and the spec view are
# untouched (variant_scope compares the statement, not the tactic body).
_PROOF = (
    "  intro parenBranch s\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  cases parenBranch <;> cases s.contains ' ' <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-flat-and: structurally different but CORRECT. The nested branch/space guards
# are collapsed into a single conjunction `parenBranch && s.contains ' '` guarding
# one assignment, default flag unset. Output equals the frozen impl's on every
# input. The theorem STATEMENT is byte-identical and the FROZEN proof body still
# closes (both forms reduce to the same `parenBranch && s.contains ' '` after the
# same `cases parenBranch <;> cases s.contains ' ' <;> rfl`). No reproof, no new
# axiom/lemma/sorry. Ports nagini's (F) flat short-circuit positive. If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to the nested-branch impl shape).
_POS_FLAT = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do\n"
    "  let mut hit : Bool := false\n"
    "  if parenBranch && s.contains ' ' then\n"
    "    hit := true\n"
    "  return Except.ok hit",
)

# pos-direct-return: a structurally different CORRECT impl that returns the flag
# value directly (no `Id.run do`, no `let mut`, no branch), i.e. the grounded
# result `Except.ok (parenBranch && s.contains ' ')`. Semantics identical on every
# input. This ports nagini's (G) grounded-oracle-delegate positive: the flag is
# defined by the transparent conjunction (not an opaque answer-key), so returning
# it directly IS the modeled behaviour, not a wrong echo. The theorem STATEMENT is
# byte-identical and the FROZEN proof body still closes (`unfold` then
# `cases … <;> rfl` reduce both sides to the same term). No reproof, no new
# axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition bound to the
# monadic impl shape rather than the behaviour).
_POS_DIRECT = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
    "  Except.ok (parenBranch && s.contains ' ')",
)

# pos-any-scan: a CORRECT reshape that computes space-presence by a DIFFERENT
# function than the spec names — `List.any` with a pointwise `BEq` test, in place
# of the spec's `List.contains`. This is the only positive here whose obligation is
# genuinely RE-PROVEN rather than closed by the frozen script: measured, the frozen
# proof body FAILS on it (`Tactic 'rfl' failed: ... Except.ok (true && s.any fun c
# => ' ' == c) is not definitionally equal to Except.ok (true && false)`), because
# `s.any` does not reduce against the un-instantiated `s` the way `s.contains ' '`
# does under the frozen `cases`. It is closed by one rewrite with the library
# bridge `List.any_beq : (l.any fun x => a == x) = l.contains a` — no case split,
# no new axiom/lemma/sorry, statement byte-identical. That is what distinguishes
# this positive from the two above: they are re-spellings the frozen `cases … <;>
# rfl` happens to absorb, whereas this one requires the proof to move, so its
# verification is evidence that the spec admits a genuinely different COMPUTATION
# of the observable and not merely a re-spelling of the frozen term. If it FAILS =>
# SPEC-TOO-STRONG (the postcondition would be pinning `List.contains` as the
# syntactic route to space-presence rather than the behaviour).
_POS_ANY = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_kernSHit\n"
        "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
        "  Except.ok (parenBranch && s.any (fun c => ' ' == c))",
    ),
    _PROOF,
    "  intro parenBranch s\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  rw [List.any_beq]",
)


# pos-for-loop-scan: the faithful IMPERATIVE skeleton — space-presence computed by
# an explicit `for c in s do if c == ' ' then hit := true` scan over the character
# sequence instead of by any library call, with the branch gate kept as the outer
# `if`. Behaviourally identical to the frozen impl on every input. This is the
# strongest soundness positive in the battery: the frozen proof script does NOT
# close it (measured — the `forIn` term does not reduce against an
# un-instantiated `s`), so the obligation is genuinely RE-PROVEN, and unlike
# `pos-any-scan` the reshape changes the impl's CONTROL SHAPE (a monadic fold with
# a mutable accumulator) rather than swapping one library predicate for another.
# The proof normalises the elaborated loop body and then folds; see the module
# header for why the naive `List.forIn_yield_eq_foldl` rewrite does not fire. No
# new axiom/lemma/sorry — both steps are `have`s inside the tactic body — and the
# theorem STATEMENT is byte-identical. If it FAILS => SPEC-TOO-STRONG (the
# postcondition would be admitting only impls that compute the observable by a
# library call, rejecting the loop that the modeled routine actually is).
_POS_FOR_LOOP = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_kernSHit\n"
        "    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do\n"
        "  let mut hit : Bool := false\n"
        "  if parenBranch then\n"
        "    for c in s do\n"
        "      if c == ' ' then\n"
        "        hit := true\n"
        "  return Except.ok hit",
    ),
    _PROOF,
    "  have body_norm : ∀ (l : List Char) (b : Bool),\n"
    "      (forIn (m := Id) l b fun c r =>\n"
    "          if c = ' ' then (do pure PUnit.unit; pure (ForInStep.yield true))\n"
    "          else (do pure PUnit.unit; pure (ForInStep.yield r)))\n"
    "        = (forIn (m := Id) l b fun c r =>"
    " ForInStep.yield (decide (c = ' ') || r)) := by\n"
    "    intro l b\n"
    "    congr 1\n"
    "    funext c r\n"
    "    by_cases hc : c = ' ' <;> simp [hc, Id.instMonad, Bind.bind]\n"
    "  have loop_gen : ∀ (l : List Char) (b : Bool),\n"
    "      (forIn (m := Id) l b fun c r => ForInStep.yield (decide (c = ' ') || r))\n"
    "        = (b || l.contains ' ') := by\n"
    "    intro l b\n"
    "    rw [List.forIn_yield_eq_foldl]\n"
    "    induction l generalizing b with\n"
    "    | nil => simp\n"
    "    | cons c t ih =>\n"
    "      rw [List.foldl_cons, ih, List.contains_cons]\n"
    "      by_cases hc : c = ' '\n"
    "      · subst hc; simp\n"
    "      · have h2 : (' ' == c) = false := by simpa [BEq.comm] using hc\n"
    "        rw [h2, Bool.false_or]\n"
    "        simp [hc]\n"
    "  intro parenBranch s\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  cases parenBranch with\n"
    "  | false => simp [Id.run, pure, Id.instMonad]\n"
    "  | true =>\n"
    "    simp only [Id.run, Bool.true_and, if_pos, beq_iff_eq]\n"
    "    rw [body_norm, loop_gen]\n"
    "    simp [pure, Id.instMonad]",
)


# ===========================================================================
# ADMISSIBILITY (non-vacuity) — must VERIFY (else PRECOND-TOO-STRONG).
# ===========================================================================

# admiss-f2p-shaped-ground: the frozen obligation is `∀ parenBranch s, P …` with NO
# precondition hypothesis, so there is no `Requires` to instantiate. The analogue of
# PRECOND-TOO-STRONG on a total carrier is the obligation being UNSATISFIABLE at
# exactly an F2P-shaped input, so this case discharges the spec predicate AT the two
# concrete branch-active points — by EVALUATION, as `have`s — BEFORE closing the
# frozen obligation verbatim. The load-bearing one is (true, ['a']): branch active,
# NO space, i.e. the input class the reported failure aborts on, where the demanded
# verdict is `Except.ok false`. The second, (true, [' ']), pins the SET corner so
# the case witnesses both verdicts rather than only the unset one. Nothing is
# assumed: no new declaration, no axiom/lemma/sorry, and the theorem STATEMENT is
# byte-identical — only the tactic body gains two `have`s, which variant_scope
# permits. If either `have` FAILED to close by `rfl` the modeled behaviour would be
# unsatisfiable at the very input the F2P exercises => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    _PROOF,
    "  have _f2p : problem_spec_kernSHit true ['a']\n"
    "      (implementation_kernSHit true ['a']) := rfl\n"
    "  have _set : problem_spec_kernSHit true [' ']\n"
    "      (implementation_kernSHit true [' ']) := rfl\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in
# place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# prepatch-error: the pre-patch placement — the membership read runs even when no
# space was present inside the active branch, where the marker was never bound, so
# the routine ABORTS (the reported referenced-before-assignment failure), modeled
# as `Except.error ()`. This is nagini's (A) prepatch-unconditional-read ported to
# the Except carrier. Correct on every input EXCEPT (branch active, no space), where
# it returns `Except.error ()` instead of `Except.ok false`. Attacks clause
# (P-well) — the never-aborts guarantee.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool := Id.run do\n"
    "  let mut hit : Bool := false\n"
    "  if parenBranch then\n"
    "    if s.contains ' ' then\n"
    "      hit := true\n"
    "    else\n"
    "      return Except.error ()\n"
    "  return Except.ok hit",
)

# hit-eq-parenBranch: the flag is just the outer branch gate — report the flag set
# whenever the branch was entered, ignoring space presence. This is nagini's (B)
# partial-domain `hit = entered` ported. Correct on (branch inactive) and (branch
# active + space) but WRONG on (branch active, no space): returns `Except.ok true`
# where (P-val) demands `Except.ok false`. Attacks clause (P-val), the
# `s.contains ' '` conjunct.
_RIV_EQ_BRANCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
    "  Except.ok parenBranch",
)

# always-false: never reports the flag set. This is nagini's (D) always-false
# rival ported. Correct on the three flag-unset input classes but WRONG on (branch
# active + space), where (P-val) demands `Except.ok true` (a space was present, so
# the substituted marker is a member). Probes that (P-val) actually pins the
# POSITIVE verdict, not only the negative ones. Attacks clause (P-val), the set
# case. (nagini's (C) value-swap and (E) narrow (True,False) rivals collapse onto
# this behaviour on the folded carrier — see the CARRIER NARROWING note — and are
# not shipped as separate cases.)
_RIV_FALSE = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
    "  Except.ok false",
)

# ignore-branch-gate: the flag is just space-presence, ignoring the branch gate —
# report the flag set whenever a space is present, even when the branch is INACTIVE.
# This rival has no direct nagini counterpart: nagini's precondition forbade a
# marker outside the entered branch, so the (branch inactive, space present) input
# was inadmissible there; on lean it is reachable (no precondition hypothesis), so
# this attacks the `parenBranch` conjunct of (P-val) independently. Correct on the
# branch-active domain but WRONG on (branch inactive, space present): returns
# `Except.ok true` where (P-val) demands `Except.ok false`. Attacks clause (P-val),
# the `parenBranch` conjunct.
_RIV_IGNORE_GATE = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
    "  Except.ok (s.contains ' ')",
)


# flag-as-agreement: the flag is set when the branch gate and space-presence AGREE
# — i.e. the conjunction is replaced by `==` (xnor). Correct on three of the four
# input corners; WRONG on exactly (branch INACTIVE, no space), where it returns
# `Except.ok true` and (P-val) demands `Except.ok false`. This rival exists because
# the four shipped above leave that corner unattacked: `prepatch-error` and
# `hit-eq-parenBranch` both probe (true, no space), `always-false` probes (true,
# space), `ignore-branch-gate` probes (false, space) — so (false, no space), the
# all-negative corner, was pinned by no witness at all. A rival wrong ONLY there is
# the surgically-minimal probe of it, and it is the lean counterpart of nagini's (E)
# narrow one-sub-domain rival (whose own sub-domain, (True,False), is empty on this
# folded carrier). Attacks clause (P-val) at the corner where BOTH conjuncts are
# false, confirming the spec demands `false` there for the right reason rather than
# by accident of the other three probes.
_RIV_AGREE = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
    "  Except.ok (parenBranch == s.contains ' ')",
)


# negate-membership: the flag is the NEGATION of the observable inside the active
# branch — `parenBranch && !s.contains ' '`. This is nagini's (C) VALUE-SWAP rival,
# ported. An earlier revision of this file dropped it as a duplicate of
# `always-false`; measured by evaluation, that is false — at (true, ['a']) the spec
# and always-false both give `Except.ok false` while this rival gives
# `Except.ok true`, so the two rivals disagree at the very corner the claim said
# they shared. It is wrong at BOTH branch-active corners (returns `true` where the
# spec demands `false` at (true, no space); returns `false` where the spec demands
# `true` at (true, space)), which no other single rival here does: it inverts the
# observable rather than dropping or replacing it. Attacks clause (P-val).
_RIV_NEGATE = _swap(
    _BASE,
    _IMPL,
    "def implementation_kernSHit\n"
    "    (parenBranch : Bool) (s : List Char) : Except Unit Bool :=\n"
    "  Except.ok (parenBranch && !s.contains ' ')",
)


# --- witnesses ---------------------------------------------------------------------
# Each witness states `¬ problem_spec_kernSHit parenBranch s (impl parenBranch s)`
# at a concrete input, unfolds the spec + impl, and closes by `simp` (which reduces
# `Except.ok`/`&&`/`List.contains` and discharges the residual boolean disequality;
# `decide` is unavailable — `Except Unit Bool` has no `DecidableEq`). Each ELABORATES
# against its rival (wrong result at that input) and FAILS on gold (which satisfies
# the spec everywhere). All inputs are literal — no opaque term, no carrier
# conditioning, so the assumptions are trivially consistent.

# (P-well): branch active, NO space. gold `Except.ok false`; prepatch rival aborts
# with `Except.error ()`. Probe point (true, ['a']).
_WIT_PREPATCH = (
    "example : ¬ problem_spec_kernSHit true ['a']\n"
    "    (implementation_kernSHit true ['a']) := by\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  simp"
)

# (P-val), space conjunct: branch active, NO space. gold `Except.ok false`; the
# hit=parenBranch rival returns `Except.ok true`. Probe point (true, ['a']).
_WIT_EQ_BRANCH = (
    "example : ¬ problem_spec_kernSHit true ['a']\n"
    "    (implementation_kernSHit true ['a']) := by\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  simp"
)

# (P-val), set case: branch active, space present. gold `Except.ok true`; the
# always-false rival returns `Except.ok false`. Probe point (true, [' ']).
_WIT_FALSE = (
    "example : ¬ problem_spec_kernSHit true [' ']\n"
    "    (implementation_kernSHit true [' ']) := by\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  simp"
)

# (P-val), parenBranch conjunct: branch INACTIVE, space present. gold
# `Except.ok false`; the ignore-branch-gate rival returns `Except.ok true`. Probe
# point (false, [' ']) — varies the `parenBranch` binder to false, which the other
# three witnesses hold at true.
_WIT_IGNORE_GATE = (
    "example : ¬ problem_spec_kernSHit false [' ']\n"
    "    (implementation_kernSHit false [' ']) := by\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  simp"
)

# (P-val), all-negative corner: branch INACTIVE, NO space (the empty string). gold
# `Except.ok false`; the flag-as-agreement rival returns `Except.ok true` (both
# conjuncts false, so they agree). Probe point (false, []) — the fourth corner of the
# (parenBranch × space-presence) square, which no other witness here visits, and the
# only witness holding BOTH binders at their negative value.
_WIT_AGREE = (
    "example : ¬ problem_spec_kernSHit false []\n"
    "    (implementation_kernSHit false []) := by\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  simp"
)


# (P-val), inverted observable: branch active, space present. gold `Except.ok true`;
# the negate-membership rival returns `Except.ok false`. Probe point (true, [' ']).
# Stated at the SET corner rather than at (true, ['a']) deliberately: the rival is
# wrong at both branch-active corners, and refuting it where the spec demands the
# POSITIVE verdict is the half that `always-false` cannot be told apart from at
# (true, ['a']).
_WIT_NEGATE = (
    "example : ¬ problem_spec_kernSHit true [' ']\n"
    "    (implementation_kernSHit true [' ']) := by\n"
    "  unfold problem_spec_kernSHit implementation_kernSHit\n"
    "  simp"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-flat-and",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLAT,
        "rationale": (
            "structurally-different but CORRECT impl: the nested branch/space guards are "
            "collapsed into a single conjunction `parenBranch && s.contains ' '` guarding one "
            "assignment, default flag unset — output equals the frozen impl's on every input. "
            "The theorem STATEMENT is byte-identical and the FROZEN proof body still closes "
            "(both forms reduce to the same conjunction under `cases parenBranch <;> cases "
            "s.contains ' ' <;> rfl`); no reproof, no new axiom/lemma/sorry. Ports nagini's (F) "
            "flat short-circuit positive. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to the nested-branch impl shape). "
            "STRENGTH, measured and stated so the record is not read as more than it is: this "
            "reshape is NOT pointwise definitionally equal to the frozen impl (a generic "
            "`implA p s = implFlat p s := by rfl` FAILS), so it is a real reshape rather than a "
            "re-spelling — but the frozen `cases parenBranch <;> cases s.contains ' '` split "
            "makes the two sides converge, so the frozen script absorbs it and the obligation is "
            "NOT re-proven. This case therefore attests that the spec is not over-fit to the "
            "frozen BRANCH NESTING; the case that shows the spec admits a different "
            "COMPUTATION of the observable, with a genuinely moved proof, is `pos-any-scan`."
        ),
    },
    {
        "id": "pos-direct-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "a structurally different CORRECT impl returning the flag value directly (no `Id.run "
            "do`, no `let mut`, no branch): `Except.ok (parenBranch && s.contains ' ')`. Ports "
            "nagini's (G) grounded-oracle-delegate positive — the flag is defined by the "
            "transparent conjunction, not an opaque answer-key, so returning it directly IS the "
            "modeled behaviour, not a wrong echo. The theorem STATEMENT is byte-identical and the "
            "FROZEN proof body still closes; no reproof, no new axiom/lemma/sorry. "
            "STRENGTH, measured: not pointwise defeq to the frozen impl (a generic `implA p s = "
            "implDirect p s := by rfl` FAILS — the `Id.run do`/`let mut` term does not reduce "
            "against an un-instantiated `s`), so the reshape is real; but it IS closed by the "
            "frozen script unchanged, so the obligation is not re-proven, and this impl is the "
            "spec's own right-hand side transcribed. That is a legitimate positive only because "
            "the observable is the TRANSPARENT conjunction and not an opaque answer-key, so there "
            "is no ungrounded echo to exploit; it is the WEAKEST positive here, and "
            "`pos-any-scan` is the one that moves the proof. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition bound to the monadic impl shape rather than the "
            "behaviour)."
        ),
    },

    {
        "id": "pos-any-scan",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ANY,
        "rationale": (
            "a CORRECT reshape that computes space-presence by a DIFFERENT function than "
            "the spec names: `s.any (fun c => ' ' == c)` in place of `s.contains ' '`. This "
            "is the only positive in this battery whose obligation is genuinely RE-PROVEN "
            "rather than absorbed by the frozen script — measured, the frozen proof body "
            "FAILS on it (`Tactic 'rfl' failed: ... Except.ok (true && s.any fun c => ' ' == "
            "c) is not definitionally equal to Except.ok (true && false)`), because `s.any` "
            "does not reduce against an un-instantiated `s` the way `s.contains ' '` does "
            "under the frozen `cases`. It closes with one rewrite by the library bridge "
            "`List.any_beq`; no case split, no new axiom/lemma/sorry, statement "
            "byte-identical. Its verification is therefore evidence that the spec admits a "
            "different COMPUTATION of the observable, not merely a re-spelling of the frozen "
            "term (which is all the two positives above establish — both are closed by the "
            "frozen `cases … <;> rfl` unchanged). If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition would pin `List.contains` as the syntactic route to "
            "space-presence rather than the behaviour)."
        ),
    },

    {
        "id": "pos-for-loop-scan",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOR_LOOP,
        "rationale": (
            "the faithful IMPERATIVE skeleton: space-presence computed by an explicit "
            "`for c in s do if c == ' ' then hit := true` scan over the character "
            "sequence — no library predicate at all — with the branch gate kept as the "
            "outer `if`. Behaviourally identical to the frozen impl on every input. "
            "This is the STRONGEST soundness positive here: measured, the frozen proof "
            "body does NOT close it (the `forIn` term does not reduce against an "
            "un-instantiated `s`), so the obligation is genuinely RE-PROVEN, and unlike "
            "`pos-any-scan` the reshape changes the impl's CONTROL SHAPE (a monadic "
            "fold over a mutable accumulator) rather than swapping one library "
            "predicate for another. The proof normalises the elaborated loop body — "
            "the `do`-notation wraps it as `do pure PUnit.unit; pure (ForInStep.yield "
            "…)`, which is why the bare `List.forIn_yield_eq_foldl` rewrite does not "
            "fire and unguided `simp` diverges — then folds and inducts on the list "
            "generalising the accumulator. Both steps are `have`s inside the tactic "
            "body: no new axiom/lemma/sorry, statement byte-identical. An earlier "
            "revision recorded this reshape as an unclosed PROOF-ENGINEERING gap; the "
            "gap is closed and the case is shipped. If it FAILS => SPEC-TOO-STRONG "
            "(the postcondition would admit only impls computing the observable by a "
            "library call, rejecting the loop the modeled routine actually is)."
        ),
    },

    # ---- admissibility / non-vacuity (must VERIFY) ----
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is `∀ parenBranch s, P …` with NO precondition hypothesis, so "
            "there is no `Requires` to instantiate; the analogue of PRECOND-TOO-STRONG on a "
            "TOTAL carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped "
            "input. This case discharges the spec predicate AT that concrete input by "
            "evaluation, as a `have` (`problem_spec_kernSHit true ['a'] "
            "(implementation_kernSHit true ['a']) := rfl` — branch active, NO space, the "
            "input class the reported failure aborts on, demanded verdict `Except.ok "
            "false`), plus a second `have` at (true, [' ']) so both the unset and the SET "
            "verdict are witnessed concretely; only then is the frozen obligation closed "
            "VERBATIM. Nothing is assumed: no new declaration, no axiom/lemma/sorry, the "
            "theorem statement is byte-identical, and only the tactic body changes. If "
            "either `have` could not close by `rfl` the modeled behaviour would be "
            "unsatisfiable at the very input the F2P exercises => PRECOND-TOO-STRONG. "
            "(Ports nagini's `admissibility-f2p-shaped`, which defended the same input class "
            "through that carrier's value precondition.)"
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "prepatch-error",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "the pre-patch placement: the membership read runs even when no space was present "
            "inside the active branch, where the marker was never bound. Its faithful real patch "
            "is the UNCHANGED helper, which on the reported F2P input enters the branch but "
            "produces no space, so the marker is never bound and reading it raises the "
            "referenced-before-assignment error — the F2P test aborts with an exception. It would "
            "NOT resolve; this is precisely the failure the patch fixes (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause (P-well) — the result must ALWAYS be `Except.ok _`. On (branch "
            "active, no space) the rival returns `Except.error ()` while the spec demands "
            "`Except.ok false`. Witness probes (true, ['a']) — branch active, no space — where "
            "the abort is observable. If it VERIFIES => SPEC-TOO-WEAK (the never-aborts guarantee "
            "is unpinned)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "hit-eq-parenBranch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EQ_BRANCH,
        "refinement": (
            "the flag is just the outer branch gate — reported set whenever the branch was "
            "entered, regardless of whether a space was present. Its faithful real patch reports "
            "processing-applied on the branch-active-but-no-space input, driving the downstream "
            "marker post-processing against a marker that was never created; on that path the "
            "helper mis-handles the never-created marker and the F2P assertion FAILS. It would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P-val), the `s.contains ' '` conjunct. On (branch active, no "
            "space) the rival returns `Except.ok true` where the spec demands `Except.ok false`. "
            "Witness probes (true, ['a']). This rival and prepatch-error are wrong at the same "
            "input for DIFFERENT reasons — one aborts, one returns the wrong flag — so they share "
            "the probe point legitimately. If it VERIFIES => SPEC-TOO-WEAK (the space conjunct is "
            "unpinned)."
        ),
        "witness": _WIT_EQ_BRANCH,
    },
    {
        "id": "always-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FALSE,
        "refinement": (
            "never reports the flag set. Its faithful real patch deletes the membership read and "
            "always leaves the flag unset; on the branch-active-with-space case the downstream "
            "marker substitution is gated on the flag being set, so the substituted marker is "
            "never restored and the parsed result keeps the marker garbage — the F2P exact-value "
            "assertion FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P-val), the SET case. On (branch active, space present) the "
            "rival returns `Except.ok false` where the spec demands `Except.ok true`. Witness "
            "probes (true, [' ']) — distinct from the no-space probes, varying `s.contains ' '` "
            "to true. Proves (P-val) pins the positive verdict, not only the negative ones. If it "
            "VERIFIES => SPEC-TOO-WEAK (the set case is unpinned). (nagini's narrow (True,False) "
            "rival has an empty sub-domain on this folded carrier; its VALUE-SWAP rival does port "
            "and is shipped separately as `negate-membership`, which shares this probe point but "
            "is wrong at the other branch-active corner too — see the module header CARRIER "
            "NARROWING note.)"
        ),
        "witness": _WIT_FALSE,
    },
    {
        "id": "ignore-branch-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_GATE,
        "refinement": (
            "the flag is just space-presence, ignoring the branch gate — reported set whenever a "
            "space is present, even when the bracket-handling branch is inactive. Its faithful "
            "real patch would set the flag for inputs that never entered the branch, running the "
            "downstream marker post-processing against a string for which no marker was ever "
            "created; the P2P/regression inputs that DON'T enter the branch but contain spaces "
            "would be mis-handled and their assertions FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P-val), the `parenBranch` conjunct. On (branch inactive, space "
            "present) the rival returns `Except.ok true` where the spec demands `Except.ok "
            "false`. Witness probes (false, [' ']) — the ONLY witness holding `parenBranch` at "
            "FALSE, so it varies that binder (the other three hold it true). This input is "
            "inadmissible in nagini (its precondition forbade a marker outside the branch) but "
            "reachable on lean, so this rival has no nagini counterpart. If it VERIFIES => "
            "SPEC-TOO-WEAK (the branch-gate conjunct is unpinned)."
        ),
        "witness": _WIT_IGNORE_GATE,
    },
    {
        "id": "flag-as-agreement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_AGREE,
        "refinement": (
            "the flag is set when the branch gate and space-presence AGREE rather than when "
            "both hold (`==` in place of `&&`). Its faithful real patch reports "
            "processing-applied for inputs that never entered the bracket-handling branch AND "
            "contain no space — i.e. for ordinary inputs that the helper should hand back "
            "untouched. On that path the downstream marker restoration is gated on the flag, "
            "so it runs against a string for which no marker was ever created, and the "
            "restoration step then rewrites a marker symbol that is not there; the "
            "PASS_TO_PASS inputs that take the untouched route would be mis-handled and their "
            "assertions FAIL. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P-val) at the ALL-NEGATIVE corner. On (branch inactive, no "
            "space) the rival returns `Except.ok true` where the spec demands `Except.ok "
            "false`. Witness probes (false, []) — the fourth corner of the (parenBranch × "
            "space-presence) square, which NO other witness in this battery visits: "
            "prepatch-error and hit-eq-parenBranch both probe (true, no space), always-false "
            "and negate-membership probe (true, space), ignore-branch-gate probes "
            "(false, space). A rival wrong "
            "ONLY there is the surgically-minimal probe of that corner, and it is the lean "
            "counterpart of nagini's (E) narrow one-sub-domain rival, whose own sub-domain is "
            "empty on this folded carrier. If it VERIFIES => SPEC-TOO-WEAK (the spec would be "
            "demanding `false` at that corner only by accident of the other three probes)."
        ),
        "witness": _WIT_AGREE,
    },
    {
        "id": "negate-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEGATE,
        "refinement": (
            "the flag is the NEGATION of the observable inside the active branch "
            "(`!s.contains ' '` in place of `s.contains ' '`). Its faithful real patch "
            "inverts the membership test, so on the branch-active-WITH-space path — "
            "where a fresh marker was substituted for the spaces and is therefore "
            "necessarily present — it reports processing-NOT-applied and skips the "
            "downstream marker restoration entirely, leaving the substituted marker "
            "in the parsed result; and on the branch-active-no-space path it reports "
            "processing-applied for a marker that was never created, driving the "
            "restoration against a string that has none. Both the F2P input class and "
            "the substituted-marker class are mis-handled and their assertions FAIL. "
            "It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (P-val), which pins the flag to the observable and not "
            "to its complement. This rival is wrong at BOTH branch-active corners — at "
            "(true, no space) it returns `Except.ok true` where the spec demands "
            "`Except.ok false`, and at (true, space) it returns `Except.ok false` where "
            "the spec demands `Except.ok true` — which no other rival here does: it "
            "INVERTS the observable rather than dropping it (`always-false`), replacing "
            "it with the gate (`hit-eq-parenBranch`), or discarding the gate "
            "(`ignore-branch-gate`). Ports nagini's (C) value-swap rival, which an "
            "earlier revision of this battery dropped as a claimed duplicate of "
            "`always-false`; measured by evaluation that claim is FALSE — at "
            "(true, ['a']) the spec and always-false both give `Except.ok false` while "
            "this rival gives `Except.ok true`, so they disagree at exactly the corner "
            "the claim said they shared. Witness probes (true, [' ']), the SET corner, "
            "where the demanded verdict is the positive one. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would not distinguish the observable from its "
            "negation)."
        ),
        "witness": _WIT_NEGATE,
    },
]


# No @ContractOnly axioms are consumed by this spec: the marker-membership step is
# modeled DEEPLY as the transparent conjunction `parenBranch && s.contains ' '`, so
# there is no opaque callee with a constraining property. The axiom lane belongs to
# G-AX regardless and is empty here.
AXIOM_TESTS = []

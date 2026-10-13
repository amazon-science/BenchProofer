"""properties.py — PBT falsification manifest for django__django-15375 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the soundness positives, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function resolves an aggregate node from two boolean observables:

    implementation_resolveAggregate
        (isTerminalAggregation hasFallback : Bool) : ResolvedExpr

pinned by a postcondition of TWO independent, load-bearing clauses over a fully
transparent `ResolvedExpr := { wrapped, terminal }` carrier:

    (P1) result.wrapped  = hasFallback              -- node identity
    (P2) result.terminal = isTerminalAggregation    -- the terminal marker (the FIX)

There is NO opaque callee: the whole result is decided by the two boolean inputs,
so every rival is refutable by `decide` at a concrete input — no carrier
conditioning is needed. The input domain is the four boolean pairs.

  * (P1) says the returned node is the coalescing wrapper exactly when a fallback
    value was supplied, and the bare aggregate otherwise.
  * (P2) says the returned node's terminal marker equals the marker the aggregate
    was resolved with — UNCONDITIONALLY, whether or not the node is the wrapper.
    This is the repaired behavior: pre-patch the freshly-built wrapper keeps its
    non-terminal default and (P2) fails when a fallback wrapper is produced while
    resolving a terminal aggregation.

The frame obligation (the read-only inputs) is discharged structurally: both
inputs appear on the right of an equality in the spec, so a result component left
free is directly observable. There is no aliasing / fractional-permission class
to port (referential transparency) — see PORTING NOTES.

PORTING NOTES (which nagini cases port, which are omitted, and why)
------------------------------------------------------------------
The nagini sibling contracts a three-input `resolve_aggregation(requested_final,
has_fallback, fallback_resolvable)`. This bundle models only the purely
functional core over TWO observables: `requested_final <-> isTerminalAggregation`
(nagini's `is_final_aggregation` clause -> P2) and `has_fallback <-> hasFallback`
(nagini's `supplies_fallback` clause -> P1). The third nagini input
`fallback_resolvable` is NOT modeled here — it feeds only the no-op resolution
branch that touches neither observable — so nagini cases keyed on it have no
counterpart, which is carrier narrowing, not an omission of substance.

  * nagini `pos-control-construct-marked` -> `pos-construct-marked`: build the
    wrapper's terminal flag at construction time (no post-hoc reassignment).
    A different executable shape producing the identical observable object;
    proof re-closed with the frozen tactic.
  * nagini `pos-control-intermediate-local` -> `pos-functional-form`: a
    structurally different CORRECT impl (pure `if`-expression, no `Id.run do` /
    `mut`) definitionally equal to the spec; proof re-closed by `cases … <;>
    simp`. Stands as a soundness positive of a different impl FORM (the carrier
    is transparent, so there is no oracle to echo).
  * nagini `weak-drop-propagation` -> `weak-drop-propagation`: the PRE-PATCH tail
    — return the wrapper with its default (`false`) terminal marker. Attacks P2.
  * nagini `weak-hardcode-true` -> `weak-hardcode-true`: the bogus hints-list
    "fix" — mark every wrapper terminal by a constant `true`. Attacks P2 on the
    non-terminal-with-fallback sub-domain.
  * nagini `weak-return-bare-aggregate` -> `weak-return-bare-aggregate`: the
    object-identity rival — return the bare aggregate on the fallback path.
    Attacks P1 (the second observable added to kill exactly this rival).
  * nagini `weak-inverted-wrap-path` -> `weak-inverted-wrap-path`: invert the
    wrapping decision. Attacks P1 with the opposite sign on both branches.
  * nagini `weak-negated-final-flag` -> `weak-negated-final-flag`: propagate the
    NEGATION of the marker. Attacks P2 with the wrong sign, so a "uses the input
    somewhere" heuristic would miss it.
  * `weak-marker-only-on-wrapper` and `weak-identity-keyed-on-marker` have NO
    nagini counterpart: they were added here (audit, attack D) to close two
    measured gaps in the ported lane — P2 was attacked only on the hasFallback=true
    branch, and the (false,false) input cell was named by no witness.
  * nagini `admiss-self-call` -> `admiss-ground-terminal-with-fallback`. An
    earlier revision recorded this lane as "vacuous on this carrier" because the
    frozen obligation carries no precondition hypothesis. That reason is WRONG,
    and an audit pass replaced it with the case: on a total carrier the analogue
    of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, which is testable directly — discharge the spec predicate
    by evaluation at the concrete F2P cell (isTerminalAggregation = true,
    hasFallback = true) as a `have`, then close the frozen obligation verbatim.
    "No precondition binder to attack" is not the same claim as "the obligation
    is satisfiable at the input the fix is about", and only the second is what
    this lane certifies. Measured: real build, exit 0.
  * nagini's frame / fractional-permission probe is N/A: Lean is referentially
    transparent (no `Acc`, no aliased input to overwrite). Both inputs are pinned
    on the RHS of the spec equalities, so the read-only-input hole cannot arise.
  * There is no divergence / non-termination class to port, but NOT because a
    diverging impl is unwritable: `partial def implementation_resolveAggregate
    … := implementation_resolveAggregate …` (plus an `Inhabited ResolvedExpr`
    instance) IS expressible here and passes `variant_scope`. It simply does not
    VERIFY — measured, exit 1, `Tactic 'unfold' failed to unfold
    'implementation_resolveAggregate'` — because vanilla Lean claims the
    obligation of every run, not only terminating ones, so there is no vacuous
    pass to exploit. Lean is unaffected by the velvet `partial`-semantics spec
    hole recorded in the corpus-wide termination-semantics finding (which is scoped to the 401
    velvet bundles and explicitly excludes lean); nothing to ship here.
    Re-measured by the audit pass, which also asked the question that decides
    whether the class is SHIPPABLE as a reject case rather than merely absent: can
    a witness refute the diverging rival? No. A witness must reduce the impl to
    compare the two components, and against a `partial def` the kernel has no
    equation to unfold, so the witness build fails on the RIVAL side — the half
    that must SUCCEED — with that same `Tactic 'unfold' failed to unfold` (measured,
    exit 1). The gate would score that `witness-unproven`, i.e. inconclusive, not
    a rejection. So the class is un-shippable here for a reason about the carrier's
    reducibility, not about proof difficulty.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input, checked in a file with the frozen obligation removed. Each
must (1) ELABORATE against the rival and (2) FAIL against the frozen solution (a
real discriminator, not a tautology). All seven witnesses below were built BOTH
ways with scripts/lean_verify.sh (rival exit 0, gold exit 1), and each gold-side
failure was read to confirm it is a SEMANTIC refutation — `decide` reports the
negation "is false", i.e. the kernel evaluated the claim and found the frozen impl
satisfies the spec there — not an unknown identifier, a type error, or a stuck
reduction. The carrier is transparent, so no witness binds a hypothesis (nothing
to be inconsistent).

An independent audit pass re-derived all four builds per witness rather than
trusting the above (28 real builds). Rival 0 / gold 1 reproduced for all seven,
and the FORGERY control was run on each: a file differing from the witness ONLY
in dropping the `¬` — i.e. claiming the impl is CORRECT at that input — builds 0
against gold and 1 against the rival, the exact inversion of the witness pair.
So the gold-side exit code tracks the CLAIM and not the file shape: the kernel is
deciding these propositions, and a forged witness asserting agreement could not
have been recorded as a refutation. The rival-side disagreement sets were also
enumerated by `#eval` over all four inputs, confirming each rival differs from
the frozen impl observably (attack C) and that each witness's input lies inside
its own rival's disagreement set: drop {(T,T)}, hardcode {(F,T)}, bare
{(F,T),(T,T)}, inverted {all four}, negated {(F,T),(T,T)},
marker-only-on-wrapper {(T,F)}, identity-keyed-on-marker {(F,F)}.

DOMAIN COVERAGE. The input domain is exactly four boolean pairs, and the reject
lane names all four: (T,T) drop / bare, (F,T) hardcode / negated, (T,F) inverted /
marker-only-on-wrapper, (F,F) identity-keyed-on-marker. Both spec clauses are
attacked on BOTH branches of the wrapping decision — P2 at hasFallback=true (drop,
hardcode, negated) and at hasFallback=false (marker-only-on-wrapper); P1 on the
fallback path (bare) and the no-fallback path (inverted, identity-keyed-on-marker).

SPEC-TOO-WEAK / SPEC-TOO-STRONG probes run by the audit pass and NOT shipped as
cases (they add no discrimination the seven rivals above do not already have, and
a battery is not improved by redundant cases):
  * wrong impls, all correctly REJECTED (exit 1, `⊢ False` on the disagreeing
    input cells, so the rejection is the postcondition and not a tactic gap):
    swap the two components (`wrapped := isTerminalAggregation, terminal :=
    hasFallback`, wrong at (F,T),(T,F)); a constant node (`{true, true}`, wrong at
    three cells); and conjunctive coupling of the marker to the wrapping decision
    (`terminal := isTerminalAggregation && hasFallback`, wrong at exactly (T,F) —
    the near-miss that reads the right input but couples it to the wrong one).
  * correct reshapes, all VERIFIED (exit 0): a four-way `match` on the input pair
    with the results written as literals; pure boolean algebra (`wrapped :=
    hasFallback && !false`, `terminal := isTerminalAggregation || false`); and a
    bounded `for _ in [0:1]` loop that assigns the whole record inside the loop
    body (this last one closes under the FROZEN tactic `simp [Id.run, pure, bind]`
    — three other tactic spellings failed on it first, which is a property of the
    tactic and not of the spec). No faithful correct impl was found that the spec
    rejects, and no wrong impl was found that it accepts.
"""
from pathlib import Path

INSTANCE = "django__django-15375"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl/proof-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. The full gold impl body (the entire `Id.run do` block) is a
# single unique substring lying strictly inside the impl region; every variant
# replaces it wholesale, so the region boundary and the spec view are preserved.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  -- The aggregate is marked as terminal exactly when it is resolved as a\n"
    "  -- terminal aggregation.\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    -- No fallback supplied: return the bare aggregate node.\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  -- A fallback is supplied: build the coalescing wrapper (which starts out\n"
    "  -- non-terminal) and carry the aggregate's terminal marker onto it.\n"
    "  let mut wrapperTerminal := false\n"
    "  wrapperTerminal := terminal\n"
    "  return { wrapped := true, terminal := wrapperTerminal }"
)
assert _BASE.count(_GOLD_IMPL) == 1

# The frozen proof (the full tactic block), re-emitted byte-identically by the
# positives that keep the frozen `theorem correct_*` STATEMENT and only alter the
# impl. Unique in the file.
_GOLD_PROOF = (
    "theorem correct_resolveAggregate :\n"
    "    ∀ (isTerminalAggregation hasFallback : Bool),\n"
    "      problem_spec_resolveAggregate isTerminalAggregation hasFallback\n"
    "        (implementation_resolveAggregate isTerminalAggregation hasFallback) := by\n"
    "  intro isTerminalAggregation hasFallback\n"
    "  unfold problem_spec_resolveAggregate implementation_resolveAggregate\n"
    "  cases hasFallback <;> simp [Id.run, pure, bind]"
)
assert _BASE.count(_GOLD_PROOF) == 1


def _impl(new_impl: str) -> str:
    return _swap(_BASE, _GOLD_IMPL, new_impl)


def _impl_and_proof(new_impl: str, new_proof: str) -> str:
    return _swap(_swap(_BASE, _GOLD_IMPL, new_impl), _GOLD_PROOF, new_proof)


# ===========================================================================
# SOUNDNESS POSITIVES — structurally-different CORRECT impls that MUST verify.
# ===========================================================================

# (pos-construct-marked) Stamp the wrapper's terminal flag AT CONSTRUCTION rather
# than constructing non-terminal then reassigning. Same observable object; the
# frozen tactic still closes because `cases hasFallback <;> simp [...]` reduces
# both branches identically. If it fails => SPEC-TOO-STRONG.
_POS_CONSTRUCT_IMPL = (
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  -- Different shape: stamp the terminal marker at construction time rather\n"
    "  -- than constructing non-terminal then reassigning.\n"
    "  return { wrapped := true, terminal := terminal }"
)
_POS_CONSTRUCT = _impl(_POS_CONSTRUCT_IMPL)

# (pos-functional-form) A pure functional impl (no `Id.run do`, no `mut`): a
# single `if`-expression definitionally equal to the two spec clauses. Proof
# re-closed by `cases hasFallback <;> simp`.
_POS_FUNCTIONAL_IMPL = (
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr :=\n"
    "  if hasFallback then\n"
    "    { wrapped := true, terminal := isTerminalAggregation }\n"
    "  else\n"
    "    { wrapped := false, terminal := isTerminalAggregation }"
)
_POS_FUNCTIONAL_PROOF = (
    "theorem correct_resolveAggregate :\n"
    "    ∀ (isTerminalAggregation hasFallback : Bool),\n"
    "      problem_spec_resolveAggregate isTerminalAggregation hasFallback\n"
    "        (implementation_resolveAggregate isTerminalAggregation hasFallback) := by\n"
    "  intro isTerminalAggregation hasFallback\n"
    "  unfold problem_spec_resolveAggregate implementation_resolveAggregate\n"
    "  cases hasFallback <;> simp"
)
_POS_FUNCTIONAL = _impl_and_proof(_POS_FUNCTIONAL_IMPL, _POS_FUNCTIONAL_PROOF)


# ===========================================================================
# ADMISSIBILITY — the obligation must be SATISFIABLE at the F2P-shaped input.
# ===========================================================================
# The frozen obligation is an unguarded `∀` over two Bools, so there is no
# precondition BINDER to over-constrain. The analogue on a total carrier is the
# obligation being unsatisfiable at exactly the input the behavior is about: the
# terminal aggregation that also carries a fallback (both observables true), the
# cell where the wrapper must be produced AND must carry the terminal marker.
# This case discharges `problem_spec_resolveAggregate true true
# (implementation_resolveAggregate true true)` by EVALUATION as a `have`, then
# closes the frozen obligation with the frozen tactic, byte-identical, after it.
# Nothing is assumed: the impl is the frozen one, no declaration is added, the
# theorem statement is untouched, and the `have` is discharged by `decide` (the
# kernel evaluates it) rather than by any appeal to the general theorem. If that
# ground instance could NOT be discharged, the obligation would be unsatisfiable
# at the very input it exists to pin => PRECOND-TOO-STRONG.
_ADMISS_PROOF = _swap(
    _GOLD_PROOF,
    "  intro isTerminalAggregation hasFallback\n",
    "  have _ground : problem_spec_resolveAggregate true true\n"
    "      (implementation_resolveAggregate true true) := by\n"
    "    unfold problem_spec_resolveAggregate implementation_resolveAggregate\n"
    "    decide\n"
    "  intro isTerminalAggregation hasFallback\n",
)
_ADMISS_GROUND = _swap(_BASE, _GOLD_PROOF, _ADMISS_PROOF)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject".
# ===========================================================================

# (weak-drop-propagation) PRE-PATCH tail: return the wrapper with its non-terminal
# default marker, dropping the propagation. Correct wherever isTerminalAggregation
# is false; wrong exactly when both inputs are true. Attacks P2.
_RIVAL_DROP = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  -- BUG: return the wrapper with its non-terminal default, dropping the\n"
    "  -- propagation of the aggregate's terminal marker.\n"
    "  return { wrapped := true, terminal := false }"
)

# (weak-hardcode-true) Mark every wrapper terminal by a CONSTANT true. Correct only
# when isTerminalAggregation is true; wrong on a non-terminal aggregate that has a
# fallback. Attacks P2 on the opposite sub-domain from the drop rival.
_RIVAL_HARDCODE = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  -- BUG: hard-code the marker true instead of propagating the input.\n"
    "  return { wrapped := true, terminal := true }"
)

# (weak-return-bare-aggregate) Object-identity rival: return the BARE aggregate on
# the fallback path. It carries the correct terminal marker (P2 holds) but is not
# the wrapper, so P1 fails. This is exactly what the second observable discriminates.
_RIVAL_BARE = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  -- BUG: return the bare aggregate on the fallback path (no wrapper). Its\n"
    "  -- terminal marker is correct, so a marker-only spec would pass this.\n"
    "  return { wrapped := false, terminal := terminal }"
)

# (weak-inverted-wrap-path) Invert the wrapping decision: bare node when a fallback
# is supplied, wrapper when not. Sets wrapped opposite to hasFallback on both
# branches, so P1 fails on every input where the two inputs differ in the branch.
_RIVAL_INVERTED = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  -- BUG: invert which path builds the wrapper.\n"
    "  if hasFallback then\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  return { wrapped := true, terminal := terminal }"
)

# (weak-marker-only-on-wrapper) Propagate the marker ONLY onto the wrapper and
# leave the BARE node's marker at the non-terminal default. Attacks (P2) on the
# no-fallback branch, which no other rival here reaches: all four other P2 rivals
# only ever alter the hasFallback=true arm, so each of them agrees with the frozen
# impl on `.terminal` for every input with hasFallback=false (machine-checked).
# Wrong exactly at (true, false).
_RIVAL_MARKER_WRAPPER_ONLY = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    -- BUG: leave the bare node's marker at the non-terminal default instead\n"
    "    -- of carrying the aggregate's marker onto it.\n"
    "    return { wrapped := false, terminal := false }\n"
    "  return { wrapped := true, terminal := terminal }"
)

# (weak-identity-keyed-on-marker) Decide the node identity from the WRONG
# observable on the no-fallback branch: key `wrapped` on the terminal marker
# instead of on hasFallback. Wrong at exactly ONE input, (false, false) — the
# only cell in the four-point domain that no other witness here names. The one
# other rival that is wrong at (false,false), weak-inverted-wrap-path, is wrong on
# ALL FOUR inputs, so it cannot attest that this cell is separately pinned.
_RIVAL_IDENTITY_ON_MARKER = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    -- BUG: decide the node identity from the terminal marker rather than\n"
    "    -- from whether a fallback was supplied.\n"
    "    return { wrapped := !isTerminalAggregation, terminal := terminal }\n"
    "  return { wrapped := true, terminal := terminal }"
)

# (weak-negated-final-flag) Keep the correct wrapper structure (P1 holds) but
# propagate the NEGATION of the marker onto the wrapper. Attacks P2 with the wrong
# sign — a "uses the input somewhere" heuristic would not catch it.
_RIVAL_NEGATED = _impl(
    "def implementation_resolveAggregate\n"
    "    (isTerminalAggregation hasFallback : Bool) : ResolvedExpr := Id.run do\n"
    "  let mut terminal := isTerminalAggregation\n"
    "  if !hasFallback then\n"
    "    return { wrapped := false, terminal := terminal }\n"
    "  -- BUG: propagate the NEGATION of the aggregate's terminal marker.\n"
    "  return { wrapped := true, terminal := !terminal }"
)


# --- witnesses (checked in a file with the frozen obligation removed) -------
# Each negates the spec predicate at one concrete boolean pair; the carrier is
# transparent, so `decide` closes and no witness binds a hypothesis.

def _wit(term: str, fb: str) -> str:
    args = f"{term} {fb}"
    return (
        "example : ¬ problem_spec_resolveAggregate\n"
        f"    {args}\n"
        "    (implementation_resolveAggregate\n"
        f"      {args}) := by\n"
        "  unfold problem_spec_resolveAggregate implementation_resolveAggregate\n"
        "  decide"
    )


# (T,T): gold => terminal=true, drop => terminal=false. Attacks P2, varies both
# binders at true.
_WIT_DROP = _wit("true", "true")
# (F,T): gold => terminal=false, hardcode => terminal=true. Attacks P2 on the
# non-terminal-with-fallback sub-domain (varies isTerminalAggregation=false).
_WIT_HARDCODE = _wit("false", "true")
# (T,T): gold => wrapped=true, bare => wrapped=false. Attacks P1 (identity).
_WIT_BARE = _wit("true", "true")
# (T,F): gold => wrapped=false, inverted => wrapped=true. Attacks P1 on the
# no-fallback branch (varies hasFallback=false — the only reject that does).
_WIT_INVERTED = _wit("true", "false")
# (F,T): gold => terminal=false, negated => terminal=true. Attacks P2 (wrong sign).
_WIT_NEGATED = _wit("false", "true")
# (T,F): gold => terminal=true, marker-only-on-wrapper => terminal=false. Attacks
# P2 on the NO-FALLBACK branch — the only witness here that does.
_WIT_MARKER_WRAPPER_ONLY = _wit("true", "false")
# (F,F): gold => wrapped=false, identity-keyed-on-marker => wrapped=true. Attacks
# P1 at the fourth domain cell, which no other witness names.
_WIT_IDENTITY_ON_MARKER = _wit("false", "false")


SPEC_TESTS = [
    # ---- soundness positives (must VERIFY) ----
    {"id": "pos-construct-marked", "kind": "soundness", "expect": "verify",
     "module": _POS_CONSTRUCT,
     "rationale": "a correct impl with a DIFFERENT executable shape — stamp the "
                  "wrapper's terminal marker at construction time rather than "
                  "constructing non-terminal then reassigning. Produces the identical "
                  "observable object, satisfying (P1) result.wrapped = hasFallback and "
                  "(P2) result.terminal = isTerminalAggregation on every input; the "
                  "frozen tactic still closes. If it fails to verify the spec is "
                  "over-fit to the reassignment shape => SPEC-TOO-STRONG."},
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a structurally-different correct impl: a pure functional "
                  "`if`-expression (no `Id.run do` / `mut`) whose two components are "
                  "definitionally the two spec clauses, so `correct_` re-closes by "
                  "`cases hasFallback <;> simp`. The carrier is transparent, so there is "
                  "no oracle to echo; this stands purely as a soundness positive of a "
                  "different impl FORM. If it fails the spec is over-fit to the "
                  "imperative shape => SPEC-TOO-STRONG."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-ground-terminal-with-fallback", "kind": "admissibility",
     "expect": "verify", "module": _ADMISS_GROUND,
     "rationale": "the obligation must be SATISFIABLE at the input the modeled "
                  "behavior is about, not only in the abstract. The frozen "
                  "obligation is an unguarded `∀` over two Bools, so there is no "
                  "precondition binder to over-constrain; the analogue on a total "
                  "carrier is the obligation being unsatisfiable at exactly the "
                  "F2P-shaped cell. So this case discharges "
                  "`problem_spec_resolveAggregate true true "
                  "(implementation_resolveAggregate true true)` — the terminal "
                  "aggregation that also carries a fallback, where the wrapper must "
                  "be produced (P1) AND must carry the terminal marker (P2) — by "
                  "EVALUATION as a `have` (`decide`, so the kernel computes it and "
                  "the general theorem is never appealed to), then closes the "
                  "frozen obligation verbatim with the frozen tactic. Impl is the "
                  "frozen one, statement byte-identical, no declaration added. If "
                  "the ground instance could not be discharged the spec would be "
                  "unsatisfiable at the input it exists to pin => "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "weak-drop-propagation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP, "witness": _WIT_DROP,
     "refinement": "this is the pre-patch behavior: the freshly-built wrapper keeps "
                   "its non-terminal default and the marker is never propagated. For a "
                   "terminal aggregation carrying a fallback (both inputs true — the "
                   "F2P cell), the wrapper stays non-terminal and is stranded in the "
                   "inner query, so the backend emits a malformed nested select and the "
                   "F2P `test_aggregation_default_after_annotation` crashes instead of "
                   "returning its value. The faithful real patch does NOT resolve.",
     "rationale": "attacks (P2) result.terminal = isTerminalAggregation. Witness at "
                  "(true, true): gold => terminal true, rival => terminal false, so the "
                  "equality fails. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-hardcode-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HARDCODE, "witness": _WIT_HARDCODE,
     "refinement": "this is the incorrect mailing-list patch (a CONSTANT marker). It "
                   "marks every fallback wrapper terminal even when the underlying "
                   "aggregate is not a terminal aggregation, so a non-terminal "
                   "aggregate-with-fallback is wrongly promoted, changing the emitted "
                   "SQL and breaking an existing (non-terminal) aggregate test. The "
                   "faithful real patch does NOT resolve the full test set.",
     "rationale": "attacks (P2) on the opposite sub-domain from the drop rival: the "
                  "spec pins the marker to the input UNCONDITIONALLY. Witness at "
                  "(false, true): gold => terminal false, rival => terminal true. This "
                  "is the reject that keys isTerminalAggregation=false, which the drop "
                  "rival cannot reach. Built both ways (rival 0, gold 1)."},
    {"id": "weak-return-bare-aggregate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BARE, "witness": _WIT_BARE,
     "refinement": "returning the bare aggregate on the fallback path drops the "
                   "coalescing wrapper, so the resolved expression no longer supplies "
                   "the fallback value on an empty aggregate. Every default-value test "
                   "asserts the fallback is returned; without the wrapper they get the "
                   "bare (empty) result and FAIL. The faithful real patch does NOT "
                   "resolve.",
     "rationale": "the object-identity rival: it carries the correct terminal marker "
                  "(P2 holds) and is rejected SOLELY by (P1) result.wrapped = "
                  "hasFallback — the second observable exists to discriminate exactly "
                  "this. Witness at (true, true): gold => wrapped true, rival => wrapped "
                  "false. Built both ways (rival 0, gold 1)."},
    {"id": "weak-inverted-wrap-path", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERTED, "witness": _WIT_INVERTED,
     "refinement": "inverts the wrapping decision: returns the bare aggregate when a "
                   "fallback WAS supplied (losing the fallback) and fabricates a wrapper "
                   "when NO fallback was supplied (wrapping a node that should be bare, "
                   "changing the SQL). Both the fallback tests and the no-fallback "
                   "aggregate tests FAIL. The faithful real patch does NOT resolve.",
     "rationale": "attacks (P1): result.wrapped is set OPPOSITE to hasFallback on both "
                  "branches. Witness at (true, false): gold => wrapped false, rival => "
                  "wrapped true. This is the ONLY reject varying hasFallback=false — "
                  "without it a rival mishandling only the no-fallback path would slip "
                  "by. Built both ways (rival 0, gold 1)."},
    {"id": "weak-negated-final-flag", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NEGATED, "witness": _WIT_NEGATED,
     "refinement": "stamps the wrapper with the NEGATED marker. For a terminal "
                   "aggregation with a fallback the wrapper wrongly becomes "
                   "non-terminal — the same stranding as the pre-patch bug, so the F2P "
                   "still crashes; and for a non-terminal one it wrongly becomes "
                   "terminal. The faithful real patch (negated propagation) does NOT "
                   "resolve.",
     "rationale": "attacks (P2) with the WRONG SIGN — result.terminal = "
                  "not isTerminalAggregation — which a 'uses the input somewhere' "
                  "heuristic would miss. Witness at (false, true): gold => terminal "
                  "false, rival => terminal true. Built both ways (rival 0, gold 1)."},
    {"id": "weak-marker-only-on-wrapper", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MARKER_WRAPPER_ONLY, "witness": _WIT_MARKER_WRAPPER_ONLY,
     "refinement": "carries the aggregate's terminal marker onto the coalescing "
                   "wrapper but leaves the BARE node non-terminal. A terminal "
                   "aggregation with no fallback then resolves to a node that is not "
                   "marked terminal, so it is not emitted as a terminal column and the "
                   "no-fallback terminal aggregate tests FAIL — while every "
                   "fallback-carrying case, including the F2P cell, still behaves. The "
                   "faithful real patch does NOT resolve the full test set.",
     "rationale": "attacks (P2) on the branch where hasFallback is FALSE. The spec "
                  "pins result.terminal = isTerminalAggregation unconditionally, in "
                  "the unwrapped case as well as the wrapped one; every other P2 rival "
                  "here alters only the hasFallback=true arm, so each agrees with the "
                  "frozen impl on .terminal at every hasFallback=false input "
                  "(machine-checked), leaving this half of the clause unattested. "
                  "Witness at (true, false): gold => terminal true, rival => terminal "
                  "false. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-identity-keyed-on-marker", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_IDENTITY_ON_MARKER, "witness": _WIT_IDENTITY_ON_MARKER,
     "refinement": "on the no-fallback path it decides node identity from the terminal "
                   "marker instead of from whether a fallback was supplied, so a "
                   "NON-terminal aggregate with no fallback is wrapped in a coalescing "
                   "node that was never asked for. That injects a fallback wrapper into "
                   "the emitted SQL for a plain aggregate, so the ordinary no-default "
                   "aggregate tests FAIL. The faithful real patch does NOT resolve.",
     "rationale": "attacks (P1) at (false, false), the fourth cell of the four-point "
                  "domain and the only one no other witness in this battery names. It "
                  "is wrong at that input ALONE (machine-checked), so its rejection "
                  "attests that the spec pins the bare/wrapper identity there "
                  "specifically; the one other rival wrong at (false,false), "
                  "weak-inverted-wrap-path, is wrong on all four inputs and so cannot "
                  "isolate this cell. Witness at (false, false): gold => wrapped "
                  "false, rival => wrapped true. Built both ways (rival 0, gold 1)."},
]

"""properties.py — PBT falsification manifest for django__django-12209 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (the
proof body is reused verbatim — see below); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

This battery is PORTED from the nagini sibling's `properties.py`; that manifest
is the design document. The nagini surface contracts a pure boolean decision
`store_single_table(pk_explicit, force_insert, pk_set, adding, pk_has_default)`
whose result is `pk_set and not forces_insert(...) and update_matched_row()`,
where `update_matched_row()` is a nullary @ContractOnly axiom (the outcome of the
unchanged UPDATE primitive). The lean carrier is NARROWER and fully transparent:
it models the pure ROUTING DECISION as a `SaveDecision { forcesFresh,
attemptsUpdate }` with NO opaque callee. The nagini↔lean binder bijection:

    pk_explicit    <-> verbatimLoad
    force_insert   <-> forceFresh
    adding         <-> isNew
    pk_has_default <-> keyHasDefault
    pk_set         <-> keySet

DEFENDED SURFACE
----------------
    implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault
        keySet : Bool) : SaveDecision

pinned by two independent top-level clauses of `problem_spec_saveDecision`:

  clause 1 (forcesFresh):
    result.forcesFresh = forcesFreshInsert verbatimLoad forceFresh isNew keyHasDefault
      = forceFresh || (!verbatimLoad && !forceFresh && isNew && keyHasDefault)
  clause 2 (attemptsUpdate):
    result.attemptsUpdate = (keySet && !result.forcesFresh)

Both clauses are FULLY TRANSPARENT — `forcesFreshInsert` is a concrete boolean
def and the whole predicate is a function of the five boolean inputs, so every
rival is refutable by `decide` at a concrete input; no carrier conditioning is
needed.

The discriminating content of the gold fix is the single conjunct `!verbatimLoad`
inside `forcesFreshInsert` (repo `not raw`). A pre-patch impl drops it; that is
wrong EXACTLY on the sub-domain verbatimLoad=true, forceFresh=false, isNew=true,
keyHasDefault=true — the verbatim replay of a record carrying an explicit key
whose key field has a default must still attempt the in-place update, not be
steered straight to a fresh insert.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
  * nagini `pos-reorder`  -> `pos-reorder`  (single-disjunction correct impl).
  * nagini `pos-cheapest` -> `pos-cheapest` (clause-1 RHS written out with an
    intermediate short-cut local). Both are structurally different but correct;
    the frozen proof `cases <;> exact ⟨rfl,rfl⟩` closes ANY total-boolean impl
    that agrees with the spec, so the proof body is reused unchanged (the spec
    obligation and its statement are byte-identical).
  * nagini `prepatch-drop-conjunct` -> `prepatch-drop-conjunct` (THE bug: drops
    the `!verbatimLoad` conjunct — the exact pre-gold guard).
  * nagini `invert-conjunct` -> `invert-conjunct` (opposite-polarity conjunct).
  * nagini `drop-force-insert-factor` -> `drop-force-insert-factor` (the
    effective verdict no longer OR-s in the caller's explicit fresh-insert
    demand).
  * nagini `drop-pk-set` -> `drop-pk-set` (the update-attempt gate drops the
    key-present factor). This is the sole rival on clause 2.
  * nagini `echo-update-row` is VACUOUS here: it echoes the nullary
    @ContractOnly axiom `update_matched_row()`, but the lean model has NO opaque
    callee — `attemptsUpdate` is fully pinned to `keySet && !forcesFresh` with
    nothing to echo. Omitted, not dropped-for-difficulty.
  * nagini `admiss-fshape` tested that the read-only precondition was
    establishable for an F2P-shaped self-call. PORTED as
    `admiss-ground-verbatim-replay`. An earlier revision of this manifest OMITTED
    it, reasoning that the lean obligation is `∀ (...booleans...), problem_spec
    ...` with no precondition hypothesis and so has nothing to over-constrain.
    That reason was WRONG, and an audit pass measured it so: on a total carrier
    the analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
    an F2P-shaped input, which a positive that discharges the predicate at that
    concrete input — by evaluation, as a `have`, before closing the frozen
    obligation verbatim — tests directly. Landed and seen to verify (exit 0).
  * nagini's frame/permission-mutation class is VACUOUS: lean is referentially
    transparent, so there is no fractional-permission read-only frame to subvert
    (the nagini manifest itself already records this class as N/A).
  * `AXIOM_TESTS` are dropped: the axiom lane is G-AX's job and this gate ignores
    them.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input. It is checked in a file with the frozen obligation removed
and must (1) elaborate against the rival (the rival provably contradicts the
spec) and (2) FAIL against the frozen solution (so it is a real discriminator,
not a tautology). All five witnesses below were built both ways with
scripts/lean_verify.sh. The witnesses vary every one of the five input binders
across both boolean values (see the per-case rationale).

Each witness's gold-side failure is `decide` DECIDING the claim (it reports the
proposition it proved), not a stuck reduction, a missing identifier or a type
error — the carrier is five booleans and a pair of concrete boolean defs, so
nothing here is opaque to the kernel. An audit pass confirmed that the gold-side
exit code tracks the CLAIM rather than the file, by building, for every reject
case, a forgery differing from the witness only in dropping the `¬`: each forgery
ELABORATES against the frozen solution (exit 0) and FAILS against its rival (exit
1) — the exact mirror of the witness, so the exit codes carry information about
what is asserted.

RIVAL COVERAGE. Over the 32-point boolean domain the five rivals jointly
distinguish 26 of 32 inputs from the frozen decision (measured, not asserted:
prepatch-drop-conjunct 2, invert-conjunct 4, drop-force-insert-factor 14,
drop-pk-set 7, attempt-extra-factor 2). Every clause and every binder is pinned
at some point by some rival, in BOTH directions for the conjunct polarity
(prepatch vs invert) and for clause 2's gate (weakened by `drop-pk-set`,
strengthened by `attempt-extra-factor`). The 6 undistinguished points are a
HONEST residual, recorded rather than glossed: at each, the short-cut is inert for
a reason these five rivals happen to agree with the frozen decision about — e.g.
(false,false,false,true,true) and (false,false,true,false,true), where exactly one
of isNew/keyHasDefault holds so the AND is false either way. A rival aimed there
would have to disagree with the spec about an input on which every mutation
attempted here coincides with it; none of the wrong impls this battery or its
audit could construct does.
"""
from pathlib import Path

INSTANCE = "django__django-12209"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region of Solution.lean.
# ---------------------------------------------------------------------------

# The gold do-block body (from the first `let mut` through the `return`).
_GOLD_DO = (
    "  let mut forced := forceFresh\n"
    "  -- Skip the update attempt (force a fresh insert) when adding a newly created\n"
    "  -- record whose key field has a default — but only for an ordinary save, never\n"
    "  -- for a verbatim replay carrying an explicit key.\n"
    "  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then\n"
    "    forced := true\n"
    "  -- An in-place update is attempted only when a key value is present and a fresh\n"
    "  -- insert is not being forced.\n"
    "  let attemptsUpdate := keySet && !forced\n"
    "  return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }\n"
)
assert _BASE.count(_GOLD_DO) == 1, "drift: gold do-block not found verbatim"

# The gold force-insert guard line (leading conjunct is the gold fix).
_GUARD = "  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then\n"
assert _BASE.count(_GUARD) == 1, "drift: guard line not unique"

# The update-attempt gate line.
_ATTEMPT = "  let attemptsUpdate := keySet && !forced\n"
assert _BASE.count(_ATTEMPT) == 1, "drift: attempt line not unique"

# The effective-verdict initializer.
_INIT = "  let mut forced := forceFresh\n"
assert _BASE.count(_INIT) == 1, "drift: init line not unique"

# The frozen proof body. Used ONLY by the admissibility case, which prepends
# `have`s and then closes the frozen obligation VERBATIM (statement untouched,
# no new declaration, no assumption token) — so `variant_scope` holds.
_PROOF = (
    "  intro verbatimLoad forceFresh isNew keyHasDefault keySet\n"
    "  cases verbatimLoad <;> cases forceFresh <;> cases isNew <;>\n"
    "    cases keyHasDefault <;> cases keySet <;>\n"
    "    exact ⟨rfl, rfl⟩\n"
)
assert _BASE.count(_PROOF) == 1, "drift: frozen proof body not found verbatim"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-reorder) Structurally-different but CORRECT: the effective fresh-insert
# verdict is computed in ONE disjunction (matching forcesFreshInsert exactly),
# with no mutable local and no `if`. Semantically identical to gold; different
# executable shape. The frozen proof `cases <;> exact ⟨rfl,rfl⟩` closes it
# unchanged. If it fails to verify, the spec is over-fit to the gold control-flow
# shape => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _GOLD_DO,
    "  let forced := forceFresh || ((!verbatimLoad) && (!forceFresh) && isNew && keyHasDefault)\n"
    "  let attemptsUpdate := keySet && !forced\n"
    "  return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }\n",
)

# (pos-cheapest) The cheapest CORRECT impl: clause 1's RHS written out with an
# intermediate short-cut local ORed against the caller's demand, then clause 2's
# RHS. Mirrors the postcondition verbatim; must verify (else SPEC-TOO-STRONG).
_POS_CHEAPEST = _swap(
    _BASE, _GOLD_DO,
    "  let sc := (!verbatimLoad) && (!forceFresh) && isNew && keyHasDefault\n"
    "  let forced := forceFresh || sc\n"
    "  let attemptsUpdate := keySet && !forced\n"
    "  return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }\n",
)


# ===========================================================================
# ADMISSIBILITY (obligation satisfiable at an F2P-shaped input) — "verify"
# ===========================================================================
# The impl region is left FROZEN; the proof region gains two `have`s that
# DISCHARGE the obligation, BY EVALUATION, at the concrete input the regression
# turns on, before the frozen general proof runs verbatim.
#
# This is the lane a TOTAL carrier still needs. The frozen obligation carries no
# precondition hypothesis, so there is no `Requires` to be too strong in the
# nagini sense — but the analogue is the obligation being UNSATISFIABLE at
# exactly an F2P-shaped point. A `problem_spec` that no concrete input can
# discharge (inconsistent, or vacuously unreachable at the interesting point)
# would still let the general `∀`-theorem close for the wrong reason. Evaluating
# the predicate at a NAMED point shows it is genuinely inhabited there, which the
# `∀`-proof alone does not.
#
# Two `have`s, because the first alone would be too weak: the spec pins `result`
# to a term over the same inputs, so discharging it says nothing about WHICH
# decision that input produces — it would read identically if the input landed in
# an uninteresting branch. The second `have` EVALUATES the modeled decision at
# that point down to a concrete `SaveDecision`, pinning the admission to the
# verbatim-replay-attempts-an-update outcome the fixture-replay F2P asserts.
_ADMISS = _swap(
    _BASE, _PROOF,
    "  have _ground : problem_spec_saveDecision true false true true true\n"
    "      (implementation_saveDecision true false true true true) := ⟨rfl, rfl⟩\n"
    "  have _value : implementation_saveDecision true false true true true\n"
    "      = { forcesFresh := false, attemptsUpdate := true } := rfl\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (prepatch-drop-conjunct) THE discriminating bug: drop the leading
# `(!verbatimLoad) &&` conjunct from the guard — the EXACT pre-gold behaviour.
# Correct on every verbatimLoad=false input, WRONG on the verbatim-replay
# sub-domain.
_RIVAL_PREPATCH = _swap(
    _BASE, _GUARD,
    "  if (!forced) && isNew && keyHasDefault then\n",
)

# (invert-conjunct) Opposite-direction bug: use `verbatimLoad` instead of
# `!verbatimLoad`, so the fresh-insert short-cut engages ONLY for a verbatim
# replay and is suppressed for an ordinary save.
_RIVAL_INVERT = _swap(
    _BASE, _GUARD,
    "  if (verbatimLoad) && (!forced) && isNew && keyHasDefault then\n",
)

# (drop-force-insert-factor) The effective verdict no longer starts from the
# caller's explicit fresh-insert demand: initialize `forced` to false, so the
# verdict is forced on ONLY by the short-cut and ignores forceFresh entirely.
_RIVAL_DROP_FORCE = _swap(
    _BASE, _INIT,
    "  let mut forced := false\n",
)

# (drop-pk-set) The update-attempt gate drops the key-present factor: attempt an
# update whenever the verdict does not force a fresh insert, regardless of whether
# a key value is present. Sole rival on clause 2.
_RIVAL_DROP_PKSET = _swap(
    _BASE, _ATTEMPT,
    "  let attemptsUpdate := !forced\n",
)

# (attempt-extra-factor) ADDED by the audit pass. The four rivals above leave a
# measured blind spot: over the 32-point boolean domain, the ordinary-save input
# (verbatimLoad=false, forceFresh=false, isNew=false, keyHasDefault=false,
# keySet=true) — a plain update of a stored record whose key field has no default
# — is a point at which NONE of them differs from the frozen decision, so nothing
# in the battery pinned the update attempt there. This rival ADDS a conjunct to
# the update-attempt gate (requiring the record be newly created or its key field
# carry a default) instead of dropping one, so it is a strictly-stronger gate:
# correct wherever that extra factor happens to hold, wrong on the ordinary save
# that is the single commonest shape the routine sees. It attacks clause 2 in the
# opposite direction from drop-pk-set, which only ever weakens the gate.
_RIVAL_ATTEMPT_EXTRA = _swap(
    _BASE, _ATTEMPT,
    "  let attemptsUpdate := keySet && !forced && (isNew || keyHasDefault)\n",
)


# --- witnesses (checked with obligation removed) ---------------------------
# Each negates the spec predicate at one concrete input; the carrier is fully
# transparent so `decide` discharges after unfolding the two defs and the pure
# helper. Every witness was built against the rival (must elaborate) AND against
# the frozen solution (must fail).

def _wit(v: str, f: str, n: str, k: str, s: str) -> str:
    return (
        f"example : ¬ problem_spec_saveDecision {v} {f} {n} {k} {s}\n"
        f"    (implementation_saveDecision {v} {f} {n} {k} {s}) := by\n"
        "  unfold problem_spec_saveDecision implementation_saveDecision forcesFreshInsert\n"
        "  decide"
    )


# verbatim replay, no forced insert, newly created, key has default, key present.
# gold: forcesFresh=false (verbatim replay is exempt) so attemptsUpdate=true;
# rival drops `!verbatimLoad` and forces a fresh insert => forcesFresh=true.
_WIT_PREPATCH = _wit("true", "false", "true", "true", "true")

# ordinary save (verbatimLoad=false), otherwise the genuinely-new default-key
# case: gold forces a fresh insert (forcesFresh=true); the inverted rival
# suppresses it (forcesFresh=false).
_WIT_INVERT = _wit("false", "false", "true", "true", "true")

# caller explicitly demanded a fresh insert (forceFresh=true), short-cut inert
# (isNew=false). gold forcesFresh=true; the rival that ignores forceFresh gives
# forcesFresh=false, and attemptsUpdate flips too.
_WIT_DROP_FORCE = _wit("false", "true", "false", "false", "true")

# no key value present (keySet=false), no forced insert. gold attemptsUpdate=false
# (nothing to match); the rival that drops the key-present factor gives true.
_WIT_DROP_PKSET = _wit("false", "false", "false", "false", "false")

# the ordinary save left unpinned by the other four rivals: a stored record with a
# key value present, not newly created, key field carrying no default, no fresh
# insert demanded. gold forcesFresh=false and attemptsUpdate=true (the in-place
# update IS attempted); the rival's extra factor suppresses it => attemptsUpdate
# =false.
_WIT_ATTEMPT_EXTRA = _wit("false", "false", "false", "false", "true")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but correct impl: the effective fresh-insert verdict is "
                  "computed in ONE disjunction matching forcesFreshInsert, with no mutable local "
                  "and no `if`, and attemptsUpdate in a single expression. Pure boolean logic; the "
                  "frozen proof `cases <;> exact ⟨rfl,rfl⟩` closes it unchanged. If it fails to "
                  "verify, the spec is over-fit to the gold control-flow shape => SPEC-TOO-STRONG."},
    {"id": "pos-cheapest", "kind": "soundness", "expect": "verify",
     "module": _POS_CHEAPEST,
     "rationale": "the cheapest CORRECT impl, written as clause 1's RHS (short-cut local ORed with "
                  "the caller's demand) followed by clause 2's RHS. Must verify (else "
                  "SPEC-TOO-STRONG); demonstrates the grounded routing decision is satisfiable by a "
                  "faithful minimal impl in a different shape from gold."},

    # ---- admissibility (obligation satisfiable at an F2P-shaped input) ----
    {"id": "admiss-ground-verbatim-replay", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the obligation must be SATISFIABLE, by evaluation, at exactly the input the "
                  "regression turns on (verbatimLoad=true, forceFresh=false, isNew=true, "
                  "keyHasDefault=true, keySet=true — the replay of a record supplied verbatim with "
                  "an explicit key whose key field carries a default). The impl region is left "
                  "FROZEN; the proof gains two `have`s and then closes the frozen obligation "
                  "verbatim, so the statement is byte-identical and no declaration or assumption "
                  "token is introduced. The first `have` discharges the spec predicate at that "
                  "point; the second EVALUATES the decision there to the concrete "
                  "`{forcesFresh := false, attemptsUpdate := true}`, so the admission is pinned to "
                  "the attempt-the-update outcome the fixture-replay F2P asserts rather than merely "
                  "to the predicate being closable. On a total carrier this is the PRECOND-TOO-"
                  "STRONG analogue: a spec unsatisfiable at an F2P-shaped point would still let the "
                  "general ∀-theorem close for the wrong reason. If it fails to verify, the "
                  "obligation is not inhabited where the issue lives."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "prepatch-drop-conjunct", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "witness": _WIT_PREPATCH,
     "refinement": "drops the gold-added `!verbatimLoad` conjunct (repo `not raw and`) — the EXACT "
                   "pre-gold guard. Its faithful real patch is the Django-3.0 regression: replaying "
                   "a record with an explicit, already-stored key whose key field has a default "
                   "takes the straight-to-fresh-insert short-cut and issues a second insert "
                   "(duplicate-key failure) instead of updating the matching row. The "
                   "fixture-replay F2P (the round-trip of a record supplied verbatim with an "
                   "explicit key) FAILS; it would NOT resolve. A verifying rival here would be a "
                   "true verify-does-not-imply-resolve break.",
     "rationale": "the discriminating bug on the verbatim-replay sub-domain (correct for "
                  "verbatimLoad=false, wrong for verbatimLoad=true). Rejection source: clause 1 "
                  "(`result.forcesFresh = forcesFreshInsert ...`). Witness (verbatimLoad=true, "
                  "forceFresh=false, isNew=true, keyHasDefault=true, keySet=true): forcesFreshInsert "
                  "is false so the spec demands forcesFresh=false and attemptsUpdate=true, but the "
                  "rival forces a fresh insert (forcesFresh=true, attemptsUpdate=false). Seen to "
                  "elaborate against the rival and fail against gold. If it verified => SPEC-TOO-WEAK."},
    {"id": "invert-conjunct", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "witness": _WIT_INVERT,
     "refinement": "uses `verbatimLoad` instead of `!verbatimLoad`, engaging the short-cut ONLY for "
                   "a verbatim replay and suppressing it for an ordinary save — the mirror of the "
                   "gold fix. Its faithful real patch would re-attempt an update on a genuinely-new "
                   "default-key ordinary create (the very fast-path the original commit added) "
                   "instead of going straight to a fresh insert, and would still mishandle the "
                   "verbatim replay; it would NOT resolve.",
     "rationale": "opposite-direction conjunct bug. Rejection source: clause 1. Witness "
                  "(verbatimLoad=false, forceFresh=false, isNew=true, keyHasDefault=true, "
                  "keySet=true): forcesFreshInsert is true so the spec demands forcesFresh=true, "
                  "but this impl suppresses the short-cut (forcesFresh=false). Seen to elaborate "
                  "against the rival and fail against gold. Varies the verbatimLoad binder against "
                  "prepatch-drop-conjunct (false here, true there), so the polarity is pinned in "
                  "both directions. If it verified => SPEC-TOO-WEAK (the conjunct polarity unpinned)."},
    {"id": "drop-force-insert-factor", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FORCE,
     "witness": _WIT_DROP_FORCE,
     "refinement": "the effective verdict no longer starts from the caller's explicit fresh-insert "
                   "demand (forced initialized to false, ignoring forceFresh). Its faithful real "
                   "patch would attempt an in-place update on a save where the caller demanded a "
                   "fresh insert, violating the force-insert contract many saves depend on; it "
                   "would NOT resolve.",
     "rationale": "partial-domain on the forceFresh disjunct of forcesFreshInsert. Rejection "
                  "source: clause 1 — forcesFresh = forceFresh || short-cut. Witness "
                  "(verbatimLoad=false, forceFresh=true, isNew=false, keyHasDefault=false, "
                  "keySet=true): forceFresh is true so the spec demands forcesFresh=true (and "
                  "attemptsUpdate=false), but the rival (short-cut inert) yields forcesFresh=false "
                  "and attemptsUpdate=true. Seen to elaborate against the rival and fail against "
                  "gold. Sole witness with forceFresh=true. If it verified => SPEC-TOO-WEAK (the "
                  "explicit-demand override unpinned)."},
    {"id": "drop-pk-set", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_PKSET,
     "witness": _WIT_DROP_PKSET,
     "refinement": "drops the key-present factor from the update-attempt gate, attempting an update "
                   "even when NO key value is present. Its faithful real patch would report/attempt "
                   "an in-place update for a record with no primary-key value — the update path is "
                   "never reached without a key — fabricating an update on the no-key save path; it "
                   "would NOT resolve.",
     "rationale": "the sole rival on clause 2 (attemptsUpdate = keySet && !forcesFresh), on the "
                  "keySet factor (correct when keySet=true, wrong when keySet=false). Witness "
                  "(verbatimLoad=false, forceFresh=false, isNew=false, keyHasDefault=false, "
                  "keySet=false): forcesFresh=false so the spec demands attemptsUpdate=false, but "
                  "the rival returns true. Seen to elaborate against the rival and fail against "
                  "gold. Sole witness with keySet=false. If it verified => SPEC-TOO-WEAK (keySet "
                  "unpinned)."},
    {"id": "attempt-extra-factor", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ATTEMPT_EXTRA,
     "witness": _WIT_ATTEMPT_EXTRA,
     "refinement": "ADDS a factor to the update-attempt gate (requiring the record be newly created "
                   "or its key field carry a default) rather than dropping one, so the gate is "
                   "strictly stronger than the spec's. Its faithful real patch would skip the "
                   "in-place update for an ordinary save of an already-stored record whose key "
                   "field has no default — the single commonest save there is — and issue a fresh "
                   "insert instead, duplicating rows on every plain update; it would NOT resolve.",
     "rationale": "the second rival on clause 2 (attemptsUpdate = keySet && !forcesFresh), attacking "
                  "it in the OPPOSITE direction from drop-pk-set: that one weakens the gate, this "
                  "one strengthens it. Closes a blind spot measured over the 32-point boolean "
                  "domain — at (verbatimLoad=false, forceFresh=false, isNew=false, "
                  "keyHasDefault=false, keySet=true) none of the other four rivals differs from the "
                  "frozen decision, so nothing pinned the update attempt on the ordinary-save "
                  "input. Witness at that point: forcesFresh=false and a key value is present, so "
                  "the spec demands attemptsUpdate=true, but the rival's extra factor suppresses it "
                  "(false). Built against the rival (elaborates, exit 0) and against the frozen "
                  "solution (fails, exit 1, `decide` deciding the claim rather than getting stuck). "
                  "If it verified => SPEC-TOO-WEAK (clause 2 pinned only from below)."},
]

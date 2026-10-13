# properties.py — G-PBT spec-lane manifest for astropy__astropy-14096 (lean).
#
# NOT a Lean file: a record of adversarially-reasoned falsification cases. Each
# case is a FULL Solution.lean variant produced by region surgery, so only the
# impl region (and, where a positive legitimately reproves, the proof body) ever
# differs and `markers.same_spec` holds by construction. Every `expect="reject"`
# case additionally ships a `witness` — a Lean snippet that has been SEEN to
# elaborate against the rival and to FAIL against the frozen solution.
#
# ------------------------------------------------------------------ DEFENDED SURFACE
#   problem_spec_resolveAttr (self : CoordObj) (attr : String)
#                            (result : Except AttrError AttrValue) : Prop
#
# The carrier is almost entirely OPAQUE: `CoordObj` and `AttrValue` are opaque
# types with no closed inhabitant, and both callees — `handledCase` and
# `ordinaryLookup` — are opaque functions with NO constraining axiom. So no
# literal input decides anything and `decide` is useless here. Every witness
# below therefore CONDITIONS on the carrier instead of computing it: it fixes a
# concrete `attr`, and describes the callee results at that point by hypothesis.
# The hypotheses are kept as weak as each refutation needs (one fact per opaque
# term, plus a separation assumption) and each set has been checked jointly
# SATISFIABLE — the gate's `example <binders> : False` probe fails on all
# thirteen, which is the required outcome. That probe's tactic set is deliberately
# incomplete, so satisfiability was additionally confirmed POSITIVELY, by
# exhibiting a model.
#
# AUDIT CORRECTION on the FORM of that model argument. An earlier revision of
# this header claimed the confirmation was `∃ self ..., <hypotheses>` elaborating
# against the frozen file itself. That claim is FALSE and was measured false: the
# carrier admits no such existential, because `CoordObj` and `AttrValue` have no
# closed inhabitant at all (`example : Nonempty CoordObj := by exact?` and the
# same for `AttrValue` both FAIL, exit 1, and `#synth Inhabited CoordObj` reports
# `failed to synthesize`). Every `∃ self, ...` over this carrier is unprovable
# whether or not the body is consistent, so it could never have been evidence.
# What was actually run, and what holds, is the model stated OUTSIDE the frozen
# file: re-instantiate the signature over `MObj := Unit`, `MVal := Bool` with the
# two callees as total functions chosen to satisfy every witness's separation
# assumption at once, and each hypothesis conjunction is then provable as an
# `∃ self, ...` over THAT carrier (all thirteen reject witnesses plus the
# admissibility case's own `have`, fourteen existentials in one file, exit 0, closed
# by `simp [mHandled]` / `simp [mOrdinary]` — note `decide` fails here, since the
# `Decidable` instance for an `Except AttrError MVal` disequality is not
# synthesizable). A contradictory hypothesis set admits no such model, so this is
# the positive half the `: False` probe cannot supply.
#
# The same model file does second duty on FAITHFULNESS, since the three-valued
# resolution aggregate is what this revision widened. Its `mHandled` maps the four
# names measured raising on the real worktree to `some (Except.error …)` with the
# measured failure classes, and its `mOrdinary` maps the F2P name `prop` to the
# measured `random_attr` report. Over that carrier the widened C1 ADMITS the
# raising names (`problem_spec_M () "altaz" (Except.error {missing :=
# "to_geodetic"})`, and likewise `lsr`), the `.getD`-shaped faithful impl is
# admitted at EVERY point, the raise-swallowing rival is REJECTED at `altaz`, and
# a failure manufactured from the requested name is still REJECTED at `prop` — so
# widening C1 provably did not cost the discrimination C2 carries. Separately,
# every witness proposition remains outright REFUTABLE on gold — `fun w => w
# (correct_resolveAttr self "<attr>")` inhabits `¬ problem_spec … → False` at all
# thirteen probe points, one file, exit 0 — so no gold-side failure below can be a
# tactic accident.
#
# WHY THE REJECTIONS ARE ATTRIBUTABLE TO THE SPEC, structurally. The spec is
# FUNCTIONAL: it determines the result uniquely, and in fact characterizes it.
# Both facts are machine-checked against the frozen file —
#   `problem_spec_resolveAttr self attr r₁ → problem_spec_resolveAttr self attr r₂
#      → r₁ = r₂`   and
#   `problem_spec_resolveAttr self attr r ↔ r = implementation_resolveAttr self attr`
# both elaborate by case analysis on `handledCase self attr`. So "verifies"
# is equivalent to "pointwise equal to the frozen impl", which is what makes
# each reject case below a claim about BEHAVIOR rather than about tactics: a
# rival is rejected exactly when it differs observably at some input, and the
# witness names such an input. It also bounds the SPEC-TOO-WEAK risk: any impl
# the spec admits agrees with the frozen one everywhere, so no observably-wrong
# rival can verify.
#
# Correspondingly, each witness's failure against the frozen solution is a
# SEMANTIC refutation and not a tactic accident: the proposition each witness
# asserts is outright REFUTABLE on gold, since `correct_resolveAttr self attr`
# inhabits the very predicate the witness negates. `(fun w => w
# (correct_resolveAttr self "aa")) : ¬ problem_spec ... → False` elaborates at
# each of the probe points used below, so no tactic choice could ever close the
# gold-side build.
#
# Load-bearing postcondition clauses (what an attacker must defeat):
#   (C1) ∀ r, handledCase self attr = some r → result = r
#        — when a domain-specific branch APPLIES, the result is that branch's own
#        outcome, surfaced unchanged: the value it resolved, or the failure
#        evaluating it raised. Nothing else may outrank it, and neither half may
#        be replaced by anything the hook manufactures. The resolution aggregate
#        is three-valued (`some (Except.ok v)` / `some (Except.error e)` / `none`)
#        because the branches are evaluated expressions, not guards: mapping.md
#        records four requested names measured on the real worktree whose
#        transform-target branch is ENTERED and RAISES (`altaz` an AttributeError
#        naming `to_geodetic`, `lsr` a TypeError, `galactocentric` a ConvertError,
#        `hcrs` a UnitsError), with the fail path provably not reached. C1's
#        `Except.error` half is what pins those — BOTH fields of the payload, the
#        reported name and the failure class — and it is attacked by
#        `atk-swallow-branch-raise` (drops the failure entirely) and by
#        `atk-reclassify-branch-failure` (keeps the name, re-labels the class),
#        and controlled by `pos-explicit-three-way-dispatch`.
#   (C2) handledCase self attr = none → result = ordinaryLookup self attr
#        — when no domain branch applies, the result is EXACTLY the ordinary
#        attribute-access outcome for the SAME name, propagated verbatim: not a
#        synthesized error, not the outcome for a different name, and not the
#        ordinary outcome with its reported name overwritten.
#
# C2 is the clause the instance turns on, and it is strong in a specific way
# worth spelling out: it is an equality against the ordinary-access outcome as a
# whole, so it pins the ERROR PAYLOAD too. The F2P regression test asserts the
# surfaced attribute error blames the genuinely-missing inner name and not the
# name that was requested (`pytest.raises(AttributeError, match="random_attr")`
# while `prop` is what was asked for), so an impl that keeps the raise-vs-return
# shape but re-keys the reported name to `attr` is still observably distinct.
# The rival `atk-relabel-reported-name` below is exactly that near-miss, and it
# is the reason C2 cannot be weakened to "the result is an error iff the
# ordinary outcome is an error".
#
# ------------------------------------------------------------------ BINDER COVERAGE
# The spec has two input binders. `attr` is varied across the reject witnesses
# (thirteen distinct literals, one per rival, so no two rivals are refuted at the
# same probe point). `self` cannot be varied by a literal — `CoordObj` is opaque
# and has no closed term (`Nonempty CoordObj` is not derivable: `exact?` finds
# nothing, and `#synth Inhabited CoordObj` reports `failed to synthesize`; the
# same holds for `AttrValue`, both measured) — so every witness quantifies over
# it and pins the per-`self` facts it needs in hypotheses; that is the only form
# the carrier admits, and the rivals differ in WHICH facts about `self` they are
# refuted by, which is the discrimination the binder can actually carry here.
# Those facts are the meaningful variation, and they cover every combination of
# the two callees' outcomes:
#   handledCase = none, ordinary ≠ a specific synthesized error  -> synth-attr, synth-const
#   handledCase = none, ordinary differs across two names        -> decorated-name
#   handledCase = none, ordinary ERRORS with a foreign name      -> relabel
#   handledCase = none, ordinary SUCCEEDS with a value           -> discard-ordinary-value
#   handledCase = some (ok v), ordinary ≠ ok v                   -> drop-branches
#   handledCase = some (ok v), no assumption on ordinary at all   -> branch-errors
#   handledCase = some (ok v), ordinary SUCCEEDS with w ≠ v       -> ordinary-outranks
#   handledCase = some (error e), ordinary ≠ error e              -> swallow-branch-raise
#   handledCase = some (error e) with a NON-DEFAULT kind, no
#     assumption on ordinary at all                              -> reclassify-branch-failure
#   handledCase = none HERE but = some (ok v) at a FOREIGN name   -> foreign-resolution
#   handledCase = none, ordinary ERRORS with a NON-DEFAULT kind   -> fallback-reclassify-failure
#   handledCase = none, ordinary ERRORS (payload FREE), and
#     = some (ok v) at a FOREIGN name                             -> fallback-swallow-failure
#
# FIFTH-AUDIT NOTE on the last two rows, and on how the gap was located. The
# eleven rivals above were each rebuilt and then run against every OTHER rival's
# witness — a full 11x11 subsumption matrix, 110 cross builds, of which 103 exit 1
# and 7 are legitimate one-directional overlaps between rivals in the same family.
# Reading the matrix by SUB-DOMAIN rather than by case showed C2's FAILING half
# was covered only partially, in the same shape the fourth audit found on C1's:
#   * the failure CLASS on the fallback path was pinned by the positives alone.
#     `atk-relabel-reported-name` pins the reported NAME there, but a rival that
#     keeps that name and re-labels only the class survives its witness, and
#     survived all eleven (exit 1, eleven for eleven, measured).
#   * a fallback that propagates values verbatim but SWALLOWS the ordinary
#     protocol's failure, substituting a foreign resolution's value, likewise
#     survived all eleven. `atk-discard-ordinary-value` propagates the failure
#     perfectly by design, and `atk-foreign-resolution-value`'s fallback overrides
#     the ordinary outcome unconditionally, so its witness needs only a
#     disequality and never visits the erroring side.
# Both rivals ARE rejected by the frozen spec (exit 1 as modules), so these were
# battery gaps and not spec holes: nothing in the table refuted an impl the spec
# does reject. `atk-fallback-reclassify-failure` and `atk-fallback-swallow-failure`
# close them, and are the C2 analogues of `atk-reclassify-branch-failure` and
# `atk-swallow-branch-raise` respectively. The swallow row is independent of ALL
# eleven predecessors in both directions (measured); the reclassify row's witness
# additionally fires on the three cruder synthesized-failure rivals
# (relabel, synth-const, synth-attr), a one-directional overlap in the same family
# as the seven already in the matrix, since each of those also puts a
# non-verbatim failure on the fallback path.
#
# For completeness on the other lanes probed in that audit, all with real builds:
# six NEWLY-WRITTEN wrong impls beyond the thirteen below were each REJECTED with a
# genuine spec-residue goal (no SPEC-TOO-WEAK hole found), and five
# NEWLY-WRITTEN correct reshapes beyond the three positives below — via
# `Option.elim`, via `isSome` + `.get`, via `<|>` + `getD`, with the match arms
# reversed and the payload field-rebuilt, and with the outcome `let`-hoisted inside
# the monad — each VERIFIED (no SPEC-TOO-STRONG hole found). There is no
# `set_option loom.semantics.termination` on this carrier and no loop in the impl,
# so there is no termination obligation for a divergence rival to attack.
#
# FAITHFULNESS-REPAIR NOTE on the two `some (error e)` rows. They are the rows
# that probe C1's raised-failure half — the arm the resolution aggregate gained
# when it was widened from `Option AttrValue` to `Option (Except AttrError
# AttrValue)`. Every other rival's hypotheses put the aggregate at `none` or at
# `some (ok v)`, so an impl free to tamper with a branch's raised failure was
# refuted by nothing in this table. Read `atk-swallow-branch-raise`'s
# `refinement` for its honest scope: its real analogue was BUILT and RUN and it
# does resolve the recorded test set, so the case attests faithfulness strength,
# not a resolve hole.
#
# FOURTH-AUDIT NOTE on why that half needs TWO rows. A raised failure is a
# two-field payload (the name it reports, the class of failure observed), and the
# swallow row pins neither field individually: it discards the failure wholesale
# and is refuted by a disequality against the ordinary outcome, which says
# nothing about which COMPONENT of the payload survives. So an impl that keeps
# the reported name and re-labels only the class was refuted by nothing here, and
# the class component was pinned by the positives alone — the same gap the fourth
# row closes for C2's success half. `atk-reclassify-branch-failure` closes this
# one. It is the exact analogue, on C1's raising half, of what
# `atk-relabel-reported-name` is on C2: a near-miss that tampers with one field
# of an error payload while getting everything else right. Measured mutually
# independent of the swallow row in both directions (neither witness fires on the
# other's rival, exit 1 both ways).
#
# SECOND-AUDIT NOTE on the last row. It is the only row whose hypotheses mention
# the resolution callee at TWO different names at once, and the only rival whose
# fabricated fallback outcome is an `Except.ok` rather than an `Except.error` —
# so it is the one point in the table where C2 is attacked from the
# invents-a-success side. See case (9) below.
#
# AUDIT NOTE on the fourth row. Before the audit this table listed no rival at
# `handledCase = none` with the ordinary protocol SUCCEEDING: all four C2 rivals
# were refuted at points where the ordinary outcome is an error (relabel) or
# where the assumption is merely a disequality against a synthesized error, which
# an erroring ordinary outcome already satisfies. So C2's success half — "a value
# the ordinary protocol produced is handed back verbatim" — was pinned by the
# positives only, never by a rival. `atk-discard-ordinary-value` below closes it.
#
# ------------------------------------------------------------------ PORT NOTES
# See `assessment` in the submitted payload for the full nagini correspondence:
# which nagini cases ported, which have no counterpart on this carrier and why.
from pathlib import Path

INSTANCE = "astropy__astropy-14096"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it edits and is unique in the
# file, so the manifest breaks loudly if the frozen solution ever moves.
# ---------------------------------------------------------------------------

# The fallback tail of the impl: everything the no-branch-applies path does.
_FALLBACK = """  -- Fall back to the object's ordinary attribute-access protocol, propagating
  -- its outcome verbatim.
  return ordinaryLookup self attr"""

# The domain-branch prologue of the impl.
_BRANCHES = """  -- Try the domain-specific resolution branches; surface the outcome of
  -- whichever applies, value or raised failure alike.
  if let some r := handledCase self attr then
    return r
"""

# The whole impl body (prologue + fallback), for variants that reshape both.
_IMPL = """def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue := Id.run do
""" + _BRANCHES + _FALLBACK

# The frozen proof body, replaced by positives that reshape the impl.
_PROOF = """  intro self attr
  unfold problem_spec_resolveAttr implementation_resolveAttr
  cases h : handledCase self attr with
  | none =>
    refine ⟨?_, ?_⟩
    · intro r hr; exact Option.noConfusion hr
    · intro _; rfl
  | some r =>
    refine ⟨?_, ?_⟩
    · intro r' hr'; exact Option.some_inj.mp hr'
    · intro hc; exact Option.noConfusion hc"""

for _anchor in (_FALLBACK, _BRANCHES, _IMPL, _PROOF):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"anchor drifted: {_anchor[:60]!r}")


# ---------------------------------------------------------------------------
# SOUNDNESS positives — structurally different, still CORRECT, and reproven.
# Each keeps the `theorem correct_resolveAttr` STATEMENT byte-identical and only
# rewrites the tactic body; all three proof scripts below were built and close.
#
# All three are genuinely reshaped and not the frozen impl relabeled: for each,
# `example (self) (attr) : implementation_resolveAttr self attr = <frozen body>
# := by rfl` FAILS (`Tactic 'rfl' failed`, exit 1), so none is definitionally
# equal to the frozen impl and each carries a real proof obligation. Honest
# caveat on the word "reproven", re-measured against the bytes shipped here by
# grafting the frozen tactic body onto each variant: it still closes on
# `pos-functional-match` and `pos-option-getd-combinator` (exit 0), so for those
# two the rewritten scripts are a different route to the same obligation rather
# than a strictly necessary one, and what they establish is that the spec admits
# the reshaped BEHAVIOR. It does NOT close on `pos-explicit-three-way-dispatch`
# (exit 1) — taking the resolution outcome apart by name leaves a goal the frozen
# script cannot discharge — so that case, the control for the widened C1, is a
# genuinely new obligation and not a restatement of the frozen one.
# ---------------------------------------------------------------------------

# A pure functional `match` in place of the imperative `Id.run do` early-return.
# Same two-case dispatch, no monadic wrapper; the proof collapses to `simp` on
# each branch because there is no `Id.run` to unfold.
_POS_MATCH = _swap(
    _BASE, _IMPL,
    """def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue :=
  match handledCase self attr with
  | some r => r
  | none => ordinaryLookup self attr""")
_POS_MATCH = _swap(
    _POS_MATCH, _PROOF,
    """  intro self attr
  unfold problem_spec_resolveAttr implementation_resolveAttr
  cases h : handledCase self attr with
  | none => simp
  | some v => simp""")

# Combinator form: default the resolution outcome to the ordinary one. No explicit
# case split in the impl at all — the dispatch is `Option.getD`, which works
# directly on the three-valued aggregate because a branch's own outcome and the
# ordinary outcome inhabit the same type — a genuinely different executable shape.
_POS_GETD = _swap(
    _BASE, _IMPL,
    """def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue :=
  (handledCase self attr).getD (ordinaryLookup self attr)""")
_POS_GETD = _swap(
    _POS_GETD, _PROOF,
    """  intro self attr
  unfold problem_spec_resolveAttr implementation_resolveAttr
  cases h : handledCase self attr with
  | none => simp
  | some v => simp""")

# Explicit three-way dispatch: the resolution outcome is taken apart by NAME
# rather than surfaced as a whole, so each of the three cases the modeled function
# actually has — a branch resolved a value, a branch was reached and its
# evaluation raised, no branch applied — is answered by its own arm. This is the
# CONTROL for the widened resolution outcome: if the spec admitted only the
# resolve-a-value sub-case in practice, the raising arm could not be discharged.
_POS_THREE_WAY = _swap(
    _BASE, _IMPL,
    """def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue :=
  match handledCase self attr with
  | some (Except.ok v) => Except.ok v
  | some (Except.error e) => Except.error e
  | none => ordinaryLookup self attr""")
_POS_THREE_WAY = _swap(
    _POS_THREE_WAY, _PROOF,
    """  intro self attr
  unfold problem_spec_resolveAttr implementation_resolveAttr
  cases h : handledCase self attr with
  | none => simp
  | some r =>
    cases r with
    | ok v => simp
    | error e => simp""")

# ---------------------------------------------------------------------------
# ADMISSIBILITY positive — the obligation binds NO precondition (`∀ self attr`),
# so it must be discharged over the WHOLE unrestricted input domain. To test
# that, this variant PARTITIONS the `attr` domain on a decidable predicate of the
# name and answers on each half by a DIFFERENT executable route (combinator on
# one side, explicit `match` on the other). The obligation therefore has to close
# on both halves separately, and the impl is NOT definitionally equal to the
# frozen one, so the frozen proof body cannot be reused — it is replaced by a
# script that does the domain split explicitly. If this could not verify, the
# admitted domain would be narrower than the binder claims.
#
# AUDIT NOTE: an earlier form of this case hoisted the resolution outcome into a
# `let` and kept the frozen proof body. That was vacuous: a `let` in term
# position zeta-reduces, so the hoisted impl was POINTWISE DEFINITIONALLY EQUAL
# to the frozen impl (`example (self) (attr) : implementation_resolveAttr self
# attr = <frozen body> := by rfl` elaborates, exit 0). It was the frozen impl
# under another spelling, verified by the frozen proof, and tested nothing. The
# partition below is not defeq (the same `rfl` probe fails, exit 1).
#
# SECOND AUDIT NOTE — what the partition does NOT test, and the `have f2p` that
# fixes it. The domain split is a real obligation (re-measured against the shipped
# bytes: the frozen proof body does NOT close on this impl, exit 1, as it also does
# not on `pos-explicit-three-way-dispatch`, while it does close on the other two
# soundness positives), but it is a claim about the WHOLE domain closing, not about any named
# point being reachable. On a total carrier that leaves the PRECOND-TOO-STRONG
# direction untested, because the analogue of an over-strong precondition here is
# the obligation being unsatisfiable at exactly an F2P-shaped input. So the proof
# below now discharges the obligation at that concrete point FIRST, as a `have`,
# before closing the frozen obligation verbatim: a non-empty requested name that
# no domain branch resolves, where the ordinary protocol fails reporting some
# OTHER name — and it pins the resulting outcome to carry that other name, which
# is the observable the regression turns on.
#
# That `have` DISCRIMINATES rather than decorating: grafted unchanged onto the
# historic-behaviour rival's file (`_ATK_SYNTH_ATTR`) it FAILS (exit 1,
# `unsolved goals ... ⊢ Except.error { missing := "prop" } = ordinaryLookup self
# "prop"` and `⊢ "prop" = m`), while on the frozen file it closes (exit 0). So it
# is a live check that the admitted domain reaches the point the instance exists
# to fix, not an `assumption`-shaped no-op.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE, _IMPL,
    """def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue :=
  -- Partition the WHOLE name domain and answer on each half by a DIFFERENT
  -- executable route, so the obligation must be discharged on both halves.
  if attr.isEmpty then
    (handledCase self attr).getD (ordinaryLookup self attr)
  else
    match handledCase self attr with
    | some r => r
    | none => ordinaryLookup self attr""")
_ADMISS = _swap(
    _ADMISS, _PROOF,
    """  -- (a) ADMISSIBILITY AT THE F2P-SHAPED POINT. Before closing the general
  -- obligation, discharge it at exactly the concrete input the regression turns
  -- on: a non-empty requested name that NO domain branch resolves, where the
  -- ordinary protocol fails reporting some OTHER name. If the obligation were
  -- unsatisfiable at that input, this `have` could not be built and the admitted
  -- domain would exclude the very point the instance exists to fix.
  have f2p : ∀ (self : CoordObj) (m : String),
      handledCase self "prop" = none →
      ordinaryLookup self "prop" = Except.error { missing := m } →
      m ≠ "prop" →
      problem_spec_resolveAttr self "prop"
          (implementation_resolveAttr self "prop")
        ∧ implementation_resolveAttr self "prop"
            = Except.error { missing := m } := by
    intro self m hNone hErr _
    refine ⟨?_, ?_⟩
    · unfold problem_spec_resolveAttr implementation_resolveAttr
      refine ⟨?_, ?_⟩
      · intro r hr; rw [hNone] at hr; exact Option.noConfusion hr
      · intro _; simp [hNone]
    · unfold implementation_resolveAttr; simp [hNone, hErr]
  -- (b) the general obligation, over the whole unrestricted input domain.
  intro self attr
  unfold problem_spec_resolveAttr implementation_resolveAttr
  by_cases hE : attr.isEmpty = true
  · rw [if_pos hE]
    cases h : handledCase self attr with
    | none => simp [h]
    | some v => simp [h]
  · rw [if_neg hE]
    cases h : handledCase self attr with
    | none => simp [h]
    | some v => simp [h]""")

# ---------------------------------------------------------------------------
# UNIQUENESS rivals — each attacks a named clause, each with a witness that was
# built against both files.
# ---------------------------------------------------------------------------

# (1) The historic behavior: on the no-branch path, synthesize an error keyed to
# the name that was REQUESTED, rather than reporting the ordinary outcome.
_ATK_SYNTH_ATTR = _swap(
    _BASE, _FALLBACK,
    """  -- Report a failure keyed to the requested name itself.
  return Except.error { missing := attr }""")

# (2) A degenerate variant of the same evasion: synthesize an error keyed to a
# fixed name of the impl's own choosing, ignoring both callees.
_ATK_SYNTH_CONST = _swap(
    _BASE, _FALLBACK,
    """  -- Report a failure keyed to a fixed name of its own choosing.
  return Except.error { missing := "" }""")

# (3) ARGUMENT attack: it really does consult the ordinary protocol — so any
# clause phrased as "delegates on the fallback path" would accept it — but it
# passes a DECORATED name, so the outcome is the ordinary one for a different
# name. Refutable without knowing anything about what the callee computes.
_ATK_WRONG_ARG = _swap(
    _BASE, _FALLBACK,
    """  -- Consult the ordinary protocol, but for a decorated form of the name.
  return ordinaryLookup self ("_" ++ attr)""")

# (4) Drops the domain-specific resolution prologue entirely, so the ordinary
# protocol answers for EVERY name. Attacks C1 rather than C2.
_ATK_DROP_BRANCHES = _swap(_BASE, _BRANCHES, "")

# (5) The NEAR-MISS, and the sharpest rival here. It consults the ordinary
# protocol, propagates a successful value verbatim, and raises exactly when the
# ordinary protocol raises — so it agrees with the frozen solution on the whole
# success sub-domain and on the raise-vs-return shape everywhere. It differs on
# one thing only: it RE-KEYS the reported name to the requested `attr`, which is
# precisely the observable the F2P test discriminates. Its witness is stated at
# its own probe point, in the sub-domain where the ordinary protocol's reported
# name differs from the requested one.
_ATK_RELABEL = _swap(
    _BASE, _FALLBACK,
    """  -- Consult the ordinary protocol, but report any failure under the requested
  -- name rather than the name that protocol itself reports.
  match ordinaryLookup self attr with
  | Except.ok v => return Except.ok v
  | Except.error _ => return Except.error { missing := attr }""")

# (6) C1 RESULT-SHAPE attack (added by audit). The four rivals above that probe
# `handledCase = none` leave C1's consequent — "the result is THAT value" —
# attacked only by `_ATK_DROP_BRANCHES`, which defeats C1 by removing the branch
# dispatch altogether. This rival KEEPS the dispatch, so the control flow is
# right and the branch is genuinely consulted, and gets the OUTCOME wrong: on the
# resolving path it reports a failure instead of yielding the resolved value. It
# separates "a domain branch was reached" from "its value is what comes back".
_ATK_BRANCH_ERRORS = _swap(
    _BASE, _BRANCHES,
    """  -- Consult the domain-specific branches, but report a failure when one applies.
  if let some _ := handledCase self attr then
    return Except.error { missing := attr }
""")

# (7) PRIORITY-INVERSION near-miss (added by audit). The sharpest C1 rival: it
# consults BOTH callees and returns a genuine outcome of one of them, never a
# synthesized error. It agrees with the frozen solution on the whole sub-domain
# where the ordinary protocol fails (there it defers to the domain branch, then
# to the ordinary error) and on the whole sub-domain where no branch applies. It
# differs only where BOTH resolve: it lets the ordinary protocol OUTRANK the
# domain-specific branch, which is exactly the precedence C1 pins ("nothing else
# may outrank it"). No clause phrased as "the fallback path delegates" or as
# "both callees are consulted" would reject it.
_ATK_ORDINARY_WINS = _swap(
    _BASE, _IMPL,
    """def implementation_resolveAttr (self : CoordObj) (attr : String) :
    Except AttrError AttrValue :=
  -- Let the ordinary protocol outrank the domain-specific branches.
  match ordinaryLookup self attr with
  | Except.ok w => Except.ok w
  | Except.error e =>
    match handledCase self attr with
    | some r => r
    | none => Except.error e""")

# (8) C2 SUCCESS-HALF attack (added by audit). The four C2 rivals above are all
# refuted at points where the ordinary protocol FAILS: `relabel` assumes it errors
# outright, and the other three assume only a disequality against a synthesized
# error, which an erroring ordinary outcome already witnesses. So none of them
# pins C2's other half — that a value the ordinary protocol SUCCESSFULLY produced
# is handed back verbatim. This rival propagates the ordinary FAILURE perfectly
# (payload included, so `atk-relabel-reported-name`'s witness does not touch it)
# and discards its SUCCESS, substituting a synthesized error. It is refuted only
# in the sub-domain no other rival's witness visits: no branch applies and the
# ordinary protocol returns a value.
_ATK_DISCARD_OK = _swap(
    _BASE, _FALLBACK,
    """  -- Consult the ordinary protocol and propagate its failure verbatim, but
  -- refuse to hand back a value it successfully produced.
  match ordinaryLookup self attr with
  | Except.ok _ => return Except.error { missing := attr }
  | Except.error e => return Except.error e""")

# (9) FOREIGN-RESOLUTION attack (added by a second audit). The nagini design
# document carries two rivals against its NORMAL-RETURN GUARD: the fallback path
# hands back a plain value — the requested name itself, or an unrelated resolved
# value — instead of reporting the ordinary attribute-access outcome. Neither
# transliterates literally: the first is ill-typed here (`attr : String` is not an
# `AttrValue`), and the second looks like it needs a closed `AttrValue`, which this
# carrier has none of (`Nonempty AttrValue` is not derivable, measured — `#synth`
# reports `failed to synthesize`). But the BEHAVIORAL content — the fallback
# fabricates a SUCCESS out of something other than the ordinary outcome for the
# name that was requested — needs no closed value at all: it can source one from
# a resolution at a DIFFERENT name, which the carrier supplies as an opaque term.
# That is this rival, and it is why that lane is expressible after all.
#
# It is distinct from all eight rivals above, and the sharp statement of HOW is
# this: it is the only rival whose fallback FABRICATES A SUCCESS. Enumerated
# (THIRD-AUDIT CORRECTION — an earlier revision of this block said "every other C2
# rival puts an `Except.error` on the fallback path", naming the three
# synthesize/decorate rivals and `atk-discard-ordinary-value`, and that is FALSE
# on two counts, checked against the rival sources: `atk-ordinary-lookup-of-
# decorated-name` returns `ordinaryLookup self ("_" ++ attr)`, a genuine callee
# outcome that is an `Except.ok` whenever the protocol succeeds at the decorated
# name, and `atk-relabel-reported-name` — omitted from that enumeration
# altogether, though it is a C2 rival — propagates successes verbatim as
# `Except.ok v`. So the discriminating property is not error-vs-value on the
# fallback path):
#   * `atk-synthesize-error-for-requested-name`, `atk-synthesize-constant-error`
#     and `atk-discard-ordinary-value` fabricate a FAILURE there;
#   * `atk-ordinary-lookup-of-decorated-name` and `atk-relabel-reported-name`
#     fabricate nothing — each returns a genuine outcome of the ordinary protocol
#     (for the wrong name, or with the reported name re-keyed).
# This rival is the only one that puts on the fallback path an `Except.ok` the
# ordinary protocol never produced for the requested name — and the value inside
# it is still a genuine callee result, just the result of resolving a DIFFERENT
# name. So it attacks C2's success half from the opposite side from
# `atk-discard-ordinary-value`: that rival discards a real success, this one
# invents one. A clause phrased as "the fallback may not fabricate a FAILURE"
# would admit it, which is what makes it worth its own case.
_ATK_FOREIGN_RESOLUTION = _swap(
    _BASE, _FALLBACK,
    """  -- Hand back a value some UNRELATED name's resolution produced, instead of the
  -- ordinary attribute-access outcome for the name actually requested.
  match handledCase self "jj" with
  | some (Except.ok v) => return Except.ok v
  | _ => return ordinaryLookup self attr""")


# (12) C2 FAILURE-CLASS attack (added by a FIFTH audit, and the first of the two
# gaps that audit found). C1's raising half has both of its payload components
# pinned by a rival — the reported name by nothing (it is surfaced whole) and the
# class by `atk-reclassify-branch-failure`. C2's failing half did NOT: its
# reported-name component is pinned by `atk-relabel-reported-name`, but its CLASS
# component was pinned by the positives alone. Every C2 rival above either
# fabricates the payload wholesale (the two synthesize rivals,
# `atk-discard-ordinary-value`), or re-keys the NAME while leaving the class
# alone (`atk-relabel-reported-name`), or changes the argument
# (`atk-ordinary-lookup-of-decorated-name`), or invents a success
# (`atk-foreign-resolution-value`). So an impl that propagates the ordinary
# protocol's failure under the name that protocol itself reports, and re-labels
# only the CLASS, was refuted by nothing in this table — MEASURED, not argued:
# built as a rival and checked against every one of the eleven witnesses this
# manifest shipped before this row was added, and all eleven FAIL on it (exit 1,
# eleven for eleven), while the frozen spec does reject it (module exit 1).
#
# This rival is exactly that near-miss, and it is the precise analogue on C2's
# failing half of what `atk-reclassify-branch-failure` is on C1's. It matters for
# the same measured reason: mapping.md records the ordinary protocol's failure
# being able to carry a class that is not an attribute-lookup failure at all (a
# value the protocol computes on demand can fail in the same open-ended way as a
# transform target), so re-labelling changes the observable there.
_ATK_FALLBACK_CLOBBER_KIND = _swap(
    _BASE, _FALLBACK,
    """  -- Consult the ordinary protocol and keep the name its failure reports, but
  -- re-classify that failure as an attribute-lookup failure rather than
  -- surfacing the class it actually carried.
  match ordinaryLookup self attr with
  | Except.ok v => return Except.ok v
  | Except.error e => return Except.error { missing := e.missing }""")


# (13) C2 SWALLOW-THE-FAILURE attack (added by the same FIFTH audit; the second
# gap). The two directions on C2's success half are both covered —
# `atk-discard-ordinary-value` DISCARDS a real success and
# `atk-foreign-resolution-value` INVENTS one where the ordinary outcome is not
# that value. Neither is refuted where the ordinary protocol FAILS and a success
# is substituted for that failure: `atk-discard-ordinary-value` propagates the
# failure perfectly (that is its whole design), and
# `atk-foreign-resolution-value`'s fallback overrides the ordinary outcome
# UNCONDITIONALLY, so its witness only ever needs the disequality and never
# visits the erroring side. Measured: this rival survives every one of the eleven
# witnesses this manifest shipped before this row was added (exit 1, eleven for
# eleven), and the frozen spec rejects it (module exit 1).
#
# So this is the swallow shape on C2 — the exact analogue of what
# `atk-swallow-branch-raise` is on C1. It propagates a value the ordinary
# protocol produced verbatim, and where that protocol RAISES it drops the failure
# and substitutes a value some unrelated name's resolution produced. A clause
# phrased as "a value the ordinary protocol produces is handed back verbatim"
# would admit it; only C2's being an equality on the WHOLE outcome rejects it.
_ATK_FALLBACK_SWALLOW = _swap(
    _BASE, _FALLBACK,
    """  -- Hand back a value some UNRELATED name's resolution produced in place of the
  -- failure the ordinary attribute-access protocol reported for the name asked for.
  match ordinaryLookup self attr with
  | Except.ok v => return Except.ok v
  | Except.error e =>
    match handledCase self "rr" with
    | some (Except.ok v) => return Except.ok v
    | _ => return Except.error e""")


# (10) WIDENED-CLAUSE attack. C1 pins the result to the outcome of whichever
# domain branch applies — the value it resolved OR the failure evaluating it
# raised, surfaced unchanged. Every rival above probes only the resolve-a-value
# sub-case, so the raising sub-case was pinned by the positives alone. This rival
# honours the resolve-a-value sub-case exactly and DISCARDS the other one: when
# the branch that applies raises, it drops that failure and answers with the
# ordinary attribute-access protocol instead. It is refuted in the sub-domain no
# other witness visits.
_ATK_SWALLOW_RAISE = _swap(
    _BASE, _BRANCHES,
    """  -- Consult the domain-specific branches but honour only the sub-case where one
  -- of them resolves a value; when the branch that applies raises instead, drop
  -- its failure and let the ordinary protocol answer.
  if let some (Except.ok v) := handledCase self attr then
    return Except.ok v
""")


# (11) FAILURE-CLASS attack (added by a FOURTH audit, and the gap that audit
# found). C1 is an equality against the applying branch's own outcome, and on the
# raising half that outcome is an `AttrError` with TWO fields: the name the
# failure reports and the CLASS of failure observed. Every rival above leaves the
# `kind` field entirely alone — `atk-swallow-branch-raise`, the only other rival
# on the raising half, discards the branch's failure WHOLESALE and is refuted by
# a disequality against the ordinary outcome, which says nothing about which
# component of the payload survives. So the `kind` component was pinned by the
# positives alone: an impl free to keep the reported name and re-label the class
# was refuted by nothing in this table.
#
# This rival is exactly that near-miss. It reaches the branch, it surfaces a
# failure and not a value, and it preserves the reported NAME verbatim; it
# differs only in re-classifying the failure as an attribute-lookup failure —
# the one class `AttrError` defaults to, and the only class a manufactured
# no-such-attribute report can carry. That is the sharpest form of the
# substitution the fallback clause exists to forbid, because it survives any
# clause phrased over the reported name alone.
#
# It is a live distinction on this carrier and not a spelling: mapping.md records
# three of the four measured raising names carrying a class that is NOT an
# attribute-lookup failure, so re-labelling changes the observable at every one
# of them. Machine-checked to be distinct from `atk-swallow-branch-raise` in BOTH
# directions: that rival's witness does NOT fire on this one (exit 1) and this
# witness does NOT fire on that one (exit 1), so neither case subsumes the other.
_ATK_CLOBBER_KIND = _swap(
    _BASE, _BRANCHES,
    """  -- Consult the domain-specific branches; when the branch that applies raises,
  -- keep the name its failure reports but re-classify it as an attribute-lookup
  -- failure rather than surfacing the class the failure actually carried.
  if let some r := handledCase self attr then
    match r with
    | Except.ok v => return Except.ok v
    | Except.error e => return Except.error { missing := e.missing }
""")


# --------------------------------------------------------------- witnesses
# Shape shared by all thirteen: fix a concrete `attr`, describe the opaque callee
# results at that point by hypothesis, then derive that the spec predicate
# cannot hold of what the rival returns there. Each hypothesis set is jointly
# satisfiable (the gate's `: False` probe fails on every one of them, verified).
#
# AUDIT-VERIFIED DISCRIMINATION. Every claim in this block was RE-MEASURED against
# the bytes shipped here — the postcondition was widened in this revision (C1's
# resolution aggregate went from `Option AttrValue` to `Option (Except AttrError
# AttrValue)`; see the FAITHFULNESS-REPAIR NOTE above), so nothing is carried over
# from a record written against the earlier spec. Exit codes observed:
#   * BATTERY, thirteen rivals: witness-vs-rival 0, witness-vs-gold 1, rival module
#     nonzero — thirteen for thirteen. Four positives: module 0, and each `rfl`-against-
#     the-frozen-impl probe nonzero, so every positive is a genuine RESHAPE the spec
#     admits rather than a copy of the frozen impl.
#   * FLIP (forged claim) — same binders, same probe point, asserting the spec DOES
#     hold of the impl there: 0 against the frozen solution, nonzero against the
#     rival, thirteen for thirteen. So each gold-side 1 TRACKS THE CLAIM rather than
#     reflecting a fixed tactic mismatch, which is what makes it evidence.
#   * REVEAL (typed residue) — the final tactic of each witness replaced by a
#     deliberate type error, to read what the equation actually normalizes to on each
#     side. Thirteen pairs, all decisive: the gold side reports `has type True`
#     (the equation was PROVED for the frozen impl) or a manifestly TRUE concrete
#     equation, while the rival side reports a manifestly FALSE one (e.g.
#     `Except.error { missing := "pp" } = Except.error { missing := "pp", kind :=
#     "TypeError" }`, `Except.ok v = Except.error e`). So each refutation rests on a
#     real disagreement between the two impls, not on a failure to unfold.
#   * CONSISTENCY probe — the gate's `example <binders> : False` on each hypothesis
#     set: nonzero, thirteen for thirteen (a set that were contradictory would close
#     it).
#   * CROSS-CHECK against the CORRECT reshapes — every witness built against ALL
#     FOUR positives (`pos-functional-match`, `pos-option-getd-combinator`,
#     `pos-explicit-three-way-dispatch`, `admiss-unrestricted-input-domain`): 52
#     builds, all nonzero. A witness that fired on a merely-reshaped correct impl
#     would be attesting to a tactic mismatch; none of them does.
#   * NECESSARY REFUTATION, which is stronger than reading any error text and is
#     why no per-witness normal-form reading is relied on here: at all thirteen probe
#     points `(fun w => w (correct_resolveAttr self L)) : ¬ problem_spec … → False`
#     elaborates against the frozen file (one file, exit 0). The proposition each
#     witness asserts is therefore outright REFUTABLE on gold, so each gold-side
#     failure is FORCED by the spec and no tactic choice could ever have closed it.
#   * SATISFIABILITY, positively: fourteen `∃ self, <hypotheses>` over the
#     independently authored `Unit`/`Bool` model, exit 0 — the thirteen reject
#     witnesses plus the admissibility case's own `have`. The same file admits the
#     widened C1 at the measured raising names and still rejects a failure
#     manufactured from the requested name, so the widening cost no discrimination.
#   * `hOther` was checked LOAD-BEARING for `atk-foreign-resolution-value`:
#     dropping it makes the witness fail against its own rival (exit 1).
#   * SUBSUMPTION: every witness built against every OTHER rival. No witness is
#     redundant — each of the thirteen is the only one that fires on its own rival,
#     except for the one-directional same-family overlaps recorded in the
#     FIFTH-AUDIT NOTE above, and `atk-fallback-swallow-failure`'s witness fires on
#     no other rival at all in either direction.
# Independently, the manifest's structural argument was machine-checked against the
# shipped spec in one file (exit 0): it is FUNCTIONAL and CHARACTERIZING — see the
# block above — so "verifies" is equivalent to "pointwise equal to the frozen
# impl", and each rejection below is a claim about BEHAVIOR, not about tactics.

_W_SYNTH_ATTR = r'''example (self : CoordObj)
    (hNone : handledCase self "aa" = none)
    (hDiff : ordinaryLookup self "aa" ≠ Except.error { missing := "aa" }) :
    ¬ problem_spec_resolveAttr self "aa"
        (implementation_resolveAttr self "aa") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, Id.run] at h
  exact hDiff h.symm
'''

_W_SYNTH_CONST = r'''example (self : CoordObj)
    (hNone : handledCase self "bb" = none)
    (hDiff : ordinaryLookup self "bb" ≠ Except.error { missing := "" }) :
    ¬ problem_spec_resolveAttr self "bb"
        (implementation_resolveAttr self "bb") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, Id.run] at h
  exact hDiff h.symm
'''

_W_WRONG_ARG = r'''example (self : CoordObj)
    (hNone : handledCase self "cc" = none)
    (hDiff : ordinaryLookup self "_cc" ≠ ordinaryLookup self "cc") :
    ¬ problem_spec_resolveAttr self "cc"
        (implementation_resolveAttr self "cc") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, Id.run] at h
  exact hDiff h
'''

_W_DROP_BRANCHES = r'''example (self : CoordObj) (v : AttrValue)
    (hSome : handledCase self "dd" = some (Except.ok v))
    (hDiff : ordinaryLookup self "dd" ≠ Except.ok v) :
    ¬ problem_spec_resolveAttr self "dd"
        (implementation_resolveAttr self "dd") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.1 (Except.ok v) hSome
  simp only [Id.run] at h
  exact hDiff h
'''

_W_BRANCH_ERRORS = r'''example (self : CoordObj) (v : AttrValue)
    (hSome : handledCase self "ff" = some (Except.ok v)) :
    ¬ problem_spec_resolveAttr self "ff"
        (implementation_resolveAttr self "ff") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.1 (Except.ok v) hSome
  simp only [hSome, Id.run, pure] at h
  exact absurd h (by simp)
'''

_W_ORDINARY_WINS = r'''example (self : CoordObj) (v w : AttrValue)
    (hSome : handledCase self "gg" = some (Except.ok v))
    (hOk : ordinaryLookup self "gg" = Except.ok w)
    (hNe : w ≠ v) :
    ¬ problem_spec_resolveAttr self "gg"
        (implementation_resolveAttr self "gg") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.1 (Except.ok v) hSome
  simp only [hOk] at h
  simp_all
'''

_W_DISCARD_OK = r'''example (self : CoordObj) (v : AttrValue)
    (hNone : handledCase self "hh" = none)
    (hOk : ordinaryLookup self "hh" = Except.ok v) :
    ¬ problem_spec_resolveAttr self "hh"
        (implementation_resolveAttr self "hh") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, hOk, Id.run, bind, pure] at h
  simp_all
'''

_W_FOREIGN_RESOLUTION = r'''example (self : CoordObj) (v : AttrValue)
    (hNone : handledCase self "ii" = none)
    (hOther : handledCase self "jj" = some (Except.ok v))
    (hDiff : ordinaryLookup self "ii" ≠ Except.ok v) :
    ¬ problem_spec_resolveAttr self "ii"
        (implementation_resolveAttr self "ii") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, hOther, Id.run, bind, pure] at h
  simp_all
'''

_W_RELABEL = r'''example (self : CoordObj) (m : String)
    (hNone : handledCase self "ee" = none)
    (hErr : ordinaryLookup self "ee" = Except.error { missing := m })
    (hName : m ≠ "ee") :
    ¬ problem_spec_resolveAttr self "ee"
        (implementation_resolveAttr self "ee") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, hErr, Id.run, bind, pure] at h
  simp_all
'''

_W_SWALLOW_RAISE = r'''example (self : CoordObj) (e : AttrError)
    (hRaise : handledCase self "kk" = some (Except.error e))
    (hDiff : ordinaryLookup self "kk" ≠ Except.error e) :
    ¬ problem_spec_resolveAttr self "kk"
        (implementation_resolveAttr self "kk") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.1 (Except.error e) hRaise
  simp only [hRaise, Id.run] at h
  exact absurd h hDiff
'''

# The FAILURE-CLASS witness. It needs ONE hypothesis and no separation assumption
# at all: the branch that applies at "mm" raises a failure whose class is not the
# attribute-lookup default. C1 then pins the result to be that very failure,
# which the rival contradicts because it re-emits the name under the default
# class. Refutation is by constructor-field disjointness on `AttrError`, so
# nothing about the ordinary protocol is assumed.
_W_CLOBBER_KIND = r'''example (self : CoordObj)
    (hRaise : handledCase self "mm"
        = some (Except.error { missing := "nn", kind := "TypeError" })) :
    ¬ problem_spec_resolveAttr self "mm"
        (implementation_resolveAttr self "mm") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.1 (Except.error { missing := "nn", kind := "TypeError" }) hRaise
  simp only [hRaise, Id.run, pure] at h
  exact absurd h (by simp)
'''


# The C2 FAILURE-CLASS witness. Two hypotheses: no branch applies at "oo", and
# the ordinary protocol there fails with a class that is NOT the attribute-lookup
# default. C2 then pins the result to be that very failure, which the rival
# contradicts because it re-emits the name under the default class. Refutation is
# by constructor-field disjointness on `AttrError`, so nothing further is assumed.
_W_FALLBACK_CLOBBER_KIND = r'''example (self : CoordObj)
    (hNone : handledCase self "oo" = none)
    (hErr : ordinaryLookup self "oo"
        = Except.error { missing := "pp", kind := "TypeError" }) :
    ¬ problem_spec_resolveAttr self "oo"
        (implementation_resolveAttr self "oo") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, hErr, Id.run, bind, pure] at h
  simp_all
'''

# The C2 SWALLOW witness. Three hypotheses, three DIFFERENT opaque terms: no
# branch applies at "qq", a branch DOES resolve a value at the foreign name "rr",
# and the ordinary protocol at "qq" FAILS. C2 pins the result to that failure;
# the rival hands back the foreign value instead, and `Except.ok v = Except.error e`
# is refuted by constructor disjointness. Note the error payload `e` is left
# entirely free — the refutation does not depend on WHICH failure it is, which is
# what separates this case from the reported-name and class rivals.
_W_FALLBACK_SWALLOW = r'''example (self : CoordObj) (v : AttrValue) (e : AttrError)
    (hNone : handledCase self "qq" = none)
    (hOther : handledCase self "rr" = some (Except.ok v))
    (hErr : ordinaryLookup self "qq" = Except.error e) :
    ¬ problem_spec_resolveAttr self "qq"
        (implementation_resolveAttr self "qq") := by
  unfold problem_spec_resolveAttr implementation_resolveAttr
  intro hc
  have h := hc.2 hNone
  simp only [hNone, hOther, hErr, Id.run, bind, pure] at h
  simp_all
'''


SPEC_TESTS = [
    # ------------------------------------------------------------- positives
    {
        "id": "pos-functional-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": "structurally-different CORRECT impl: the imperative "
                     "`Id.run do` early-return is replaced by a pure functional "
                     "`match` on the resolution outcome. Both clauses hold "
                     "unchanged — C1 by the `some` arm, C2 by the `none` arm — "
                     "and the obligation is discharged for the new shape (the "
                     "`theorem correct_resolveAttr` statement is byte-identical; "
                     "only the tactic body differs, and it closes without any "
                     "`Id.run` unfolding). The impl is not definitionally equal "
                     "to the frozen one — the pointwise `rfl` probe fails — so "
                     "this is a real reshape. If this could not verify, the spec "
                     "would be constraining the impl's syntactic form rather "
                     "than its input→output behavior: SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-option-getd-combinator",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GETD,
        "rationale": "a second CORRECT shape with no case split in the impl at "
                     "all: the applying branch's own outcome is defaulted to the "
                     "ordinary outcome via `Option.getD`. This "
                     "is the most distant executable shape from the frozen impl "
                     "that is still behaviorally identical, so it is the "
                     "strongest available check that C1 and C2 pin BEHAVIOR and "
                     "not control flow. Statement untouched; not definitionally "
                     "equal to the frozen impl (the pointwise `rfl` probe fails).",
    },
    {
        "id": "pos-explicit-three-way-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_THREE_WAY,
        "rationale": "the OVER-REJECTION CONTROL for the widened resolution "
                     "outcome. The other two soundness positives surface the "
                     "outcome of the applying branch as a whole (`some r => r`), "
                     "so neither of them ever names the sub-case in which the "
                     "branch that applies RAISES. This one takes the outcome "
                     "apart by name and answers each of the three cases the "
                     "modeled function actually has in its own arm — branch "
                     "resolved a value, branch reached and raised, no branch "
                     "applied. It is behaviorally identical to the frozen impl "
                     "and must verify; if it could not, C1 would be admitting "
                     "the resolve-a-value sub-case only and the raising sub-case "
                     "would be unsatisfiable rather than pinned — the spec would "
                     "be unusable on exactly the inputs the faithfulness repair "
                     "was made for. Not definitionally equal to the frozen impl "
                     "(the nested match on an opaque outcome does not reduce; the "
                     "pointwise `rfl` probe fails, exit 1), and unlike the other "
                     "two soundness positives the FROZEN proof body does not close "
                     "on it either (measured, exit 1), so the obligation it "
                     "carries is a new one rather than a restatement.",
    },
    {
        "id": "admiss-unrestricted-input-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation binds `∀ (self : CoordObj) (attr : String)` "
                     "with NO precondition hypothesis, so the modeled function "
                     "must be total on its whole input domain. This variant "
                     "PARTITIONS the `attr` domain on a decidable predicate of "
                     "the name and answers on each half by a different executable "
                     "route, so the obligation has to close separately on both "
                     "halves of a partition that covers every name — which is "
                     "what confirms the whole unrestricted domain is admitted, "
                     "rather than one representative point. The impl is NOT "
                     "definitionally equal to the frozen one (the pointwise `rfl` "
                     "probe fails), so the frozen proof body does not apply and "
                     "the case carries a real obligation — measured: the frozen "
                     "proof body FAILS on this impl (exit 1), unlike on the two "
                     "outcome-as-a-whole soundness positives where it happens to "
                     "close; the proof "
                     "script does the domain split explicitly. It additionally "
                     "discharges the obligation at the concrete F2P-SHAPED input "
                     "as a `have`, BEFORE closing the frozen obligation verbatim: "
                     "a non-empty requested name no domain branch resolves, where "
                     "the ordinary protocol fails reporting some OTHER name, with "
                     "the surfaced outcome pinned to carry that other name. That "
                     "is what tests the PRECOND-TOO-STRONG direction on a total "
                     "carrier — the analogue of an over-strong precondition is the "
                     "obligation being unsatisfiable at exactly that input — and "
                     "it discriminates: the same `have` grafted onto the "
                     "historic-behaviour rival FAILS (exit 1), so it is not an "
                     "`assumption`-shaped no-op. If it could not verify, the "
                     "admitted domain would be narrower than the binder claims.",
    },

    # ------------------------------------------------------------- rivals
    {
        "id": "atk-synthesize-error-for-requested-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_SYNTH_ATTR,
        "witness": _W_SYNTH_ATTR,
        "rationale": "attacks C2 (`handledCase = none → result = ordinaryLookup "
                     "self attr`). On the no-branch path this returns a "
                     "self-synthesized `Except.error { missing := attr }` instead "
                     "of the ordinary attribute-access outcome. The witness fixes "
                     "attr = \"aa\", assumes no branch applies there, and assumes "
                     "the ordinary outcome at that point is not that particular "
                     "error — the exact sub-domain where the rival is wrong. Both "
                     "hypotheses concern DIFFERENT opaque terms and are jointly "
                     "satisfiable, so the refutation is not vacuous.",
        "refinement": "Its faithful real patch keeps the fallback path "
                      "manufacturing an attribute error naming the attribute that "
                      "was requested. The F2P test "
                      "test_subclass_property_exception_error requires the "
                      "surfaced error to blame the genuinely-missing inner name "
                      "(`pytest.raises(AttributeError, match=\"random_attr\")`) "
                      "while the requested name is `prop`; an error keyed to the "
                      "requested name does not match, the test still fails, and "
                      "the patch does NOT resolve. This is the historic behavior "
                      "the instance exists to change, so a verifying rival here "
                      "would be a true verify-does-not-imply-resolve break.",
    },
    {
        "id": "atk-synthesize-constant-error",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_SYNTH_CONST,
        "witness": _W_SYNTH_CONST,
        "rationale": "also attacks C2, at a DIFFERENT probe point (attr = "
                     "\"bb\") and by a different evasion: the fallback ignores "
                     "both callees entirely and returns a constant error. Shares "
                     "no witness with the rival above because it fails for a "
                     "different reason — that one is wrong only where the "
                     "ordinary outcome differs from the requested-name error, "
                     "this one wherever the ordinary outcome is not the fixed "
                     "constant — so each gets its own probe point rather than "
                     "claiming a sub-domain the manifest never demonstrates.",
        "refinement": "A faithful real patch whose fallback raises an attribute "
                      "error with a fixed unrelated name cannot match the F2P "
                      "test's `match=\"random_attr\"` assertion, which is keyed "
                      "to the name the ordinary access protocol itself reports. "
                      "Only actually consulting that protocol produces that name, "
                      "so the patch does NOT resolve.",
    },
    {
        "id": "atk-ordinary-lookup-of-decorated-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_WRONG_ARG,
        "witness": _W_WRONG_ARG,
        "rationale": "an ARGUMENT attack on C2 rather than a result attack: the "
                     "rival DOES consult the ordinary protocol, so any weaker "
                     "clause phrased as \"the fallback path delegates\" would "
                     "accept it. C2 is an equality against the ordinary outcome "
                     "FOR THE SAME NAME, so passing a decorated name violates it. "
                     "The witness needs no knowledge of what the callee computes "
                     "— only that its results at the decorated and undecorated "
                     "names differ, which is the single separation assumption the "
                     "refutation requires.",
        "refinement": "A faithful real patch that consults the ordinary access "
                      "protocol for a decorated form of the attribute name "
                      "reports the wrong name on the fallback path, so the F2P "
                      "test's `match=\"random_attr\"` assertion still fails; and "
                      "on names the ordinary protocol WOULD have resolved it now "
                      "returns a different value or raises, breaking the "
                      "attribute-resolution behavior the sky-coordinate P2P suite "
                      "pins (e.g. test_frame_attr_getattr, test_extra_attributes). "
                      "Not resolved on either count.",
    },
    {
        "id": "atk-drop-domain-resolution-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_DROP_BRANCHES,
        "witness": _W_DROP_BRANCHES,
        "rationale": "the only rival attacking C1 (`∀ v, handledCase = some v → "
                     "result = Except.ok v`) rather than C2: the domain-specific "
                     "resolution prologue is dropped, so the ordinary protocol "
                     "answers for every name including those a domain branch "
                     "resolves. The witness probes attr = \"dd\" in the sub-domain "
                     "where a branch DOES resolve (handledCase = some v) and the "
                     "ordinary outcome is not that value — the complementary half "
                     "of the input space from the four C2 rivals, which all probe "
                     "handledCase = none.",
        "refinement": "Its faithful real patch deletes the domain-specific "
                      "resolution branches, so frame aliases, frame attributes, "
                      "embedded-frame delegation and transform-target names stop "
                      "resolving. The F2P test would incidentally still pass — its "
                      "attribute is resolved by no branch — but a SWE-bench "
                      "resolution requires the PASS_TO_PASS suite to hold too, and "
                      "this breaks it broadly (test_multiple_aliases, "
                      "test_frame_attr_getattr, test_transform_to, "
                      "test_attr_inheritance among the 426 sky-coordinate P2P "
                      "tests). Not resolved.",
    },
    {
        "id": "atk-relabel-reported-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_RELABEL,
        "witness": _W_RELABEL,
        "rationale": "the NEAR-MISS, and the case that shows C2 must be an "
                     "equality on the whole outcome rather than on its "
                     "success/failure shape. This rival consults the ordinary "
                     "protocol, propagates successes verbatim, and fails exactly "
                     "when that protocol fails — agreeing with the frozen "
                     "solution on the entire success sub-domain and on "
                     "raise-vs-return everywhere. It differs only in re-keying "
                     "the REPORTED NAME to `attr`. Because it agrees with gold "
                     "over strictly more of the domain than the other C2 rivals, "
                     "it gets its own probe point (attr = \"ee\") in the "
                     "sub-domain its rationale actually claims: where the "
                     "ordinary protocol reports a name `m ≠ \"ee\"`. The three "
                     "hypotheses are jointly satisfiable (nothing forces the "
                     "opaque protocol to report the requested name).",
        "refinement": "This is the rival whose faithful real patch is closest to "
                      "resolving and still does not. It consults the ordinary "
                      "access protocol on the fallback path and re-raises under "
                      "the requested attribute name, so it produces an "
                      "AttributeError in exactly the situations the frozen "
                      "behavior does — but the F2P test asserts on WHICH name is "
                      "blamed: `pytest.raises(AttributeError, match=\"random_attr\")` "
                      "with `prop` requested. Re-keying to the requested name "
                      "surfaces `prop`, the assertion does not match, and the "
                      "patch does NOT resolve. A spec that accepted it would be "
                      "exactly the verify-does-not-imply-resolve hole this "
                      "instance is built to exclude.",
    },
    {
        "id": "atk-branch-resolves-but-errors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_BRANCH_ERRORS,
        "witness": _W_BRANCH_ERRORS,
        "rationale": "attacks C1's CONSEQUENT rather than its reachability. The "
                     "other C1 rival removes the branch dispatch entirely, so a "
                     "clause that only required the branches to be CONSULTED "
                     "would still reject it; this one keeps the dispatch intact "
                     "and gets the outcome wrong, reporting a failure on the very "
                     "path where a branch resolved the name. C1 pins the result to "
                     "be that value, so the witness needs only the single "
                     "hypothesis that a branch resolves at its probe point "
                     "(attr = \"ff\"): `Except.error _ = Except.ok v` is refuted "
                     "by constructor disjointness, with no assumption about the "
                     "ordinary protocol at all.",
        "refinement": "A faithful real patch that reaches the domain-specific "
                      "resolution branches and then raises instead of returning "
                      "their value stops every domain-resolvable name from "
                      "resolving, while also raising where the frozen behavior "
                      "returns. The F2P test would be unaffected (its attribute "
                      "is resolved by no branch), but a SWE-bench resolution "
                      "needs PASS_TO_PASS too, and this breaks it across the "
                      "sky-coordinate suite (test_multiple_aliases, "
                      "test_frame_attr_getattr, test_transform_to, "
                      "test_attr_inheritance are among the 426 P2P tests). "
                      "Not resolved.",
    },
    {
        "id": "atk-ordinary-outranks-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_ORDINARY_WINS,
        "witness": _W_ORDINARY_WINS,
        "rationale": "the PRECEDENCE near-miss, and the only rival here whose "
                     "every output is a genuine outcome of one of the two callees "
                     "— it never synthesizes an error and never decorates a name, "
                     "so no clause phrased as \"the fallback path delegates\" or "
                     "as \"both callees are consulted\" can reject it. It agrees "
                     "with the frozen solution wherever no branch applies AND "
                     "wherever the ordinary protocol fails; it differs only where "
                     "BOTH resolve, by letting the ordinary protocol outrank the "
                     "domain-specific branch. That is precisely the precedence C1 "
                     "fixes, so its witness probes attr = \"gg\" in the sub-domain "
                     "its rationale claims: a branch resolves to `v`, the ordinary "
                     "protocol succeeds with some `w ≠ v`. The three hypotheses "
                     "are jointly satisfiable (nothing ties the two opaque "
                     "callees' results together).",
        "refinement": "A faithful real patch that consults the ordinary access "
                      "protocol first and only falls back to the domain-specific "
                      "resolution when that protocol fails inverts the documented "
                      "precedence: names that a domain branch is supposed to "
                      "answer would instead be answered by ordinary access "
                      "wherever it happens to succeed, changing observable "
                      "attribute resolution for frame aliases and frame "
                      "attributes that shadow an ordinary attribute. The "
                      "sky-coordinate P2P suite pins that resolution "
                      "(test_multiple_aliases, test_frame_attr_getattr, "
                      "test_extra_attributes), so the patch does NOT resolve.",
    },
    {
        "id": "atk-discard-ordinary-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_DISCARD_OK,
        "witness": _W_DISCARD_OK,
        "rationale": "closes the one half of C2 no other rival attacked: that a "
                     "value the ordinary protocol SUCCESSFULLY produced is handed "
                     "back verbatim. Every other C2 rival is refuted where that "
                     "protocol FAILS — `atk-relabel-reported-name` assumes it "
                     "errors outright, and the three synthesize/decorate rivals "
                     "assume only a disequality against a synthesized error, which "
                     "an erroring ordinary outcome already witnesses — so before "
                     "this case the success half of the fallback path was pinned by "
                     "the positives alone and by no rival. This rival propagates "
                     "the ordinary FAILURE perfectly, payload included, so it is "
                     "untouched by the relabel witness; it discards the SUCCESS, "
                     "substituting a synthesized error. Its witness therefore "
                     "probes attr = \"hh\" in the sub-domain no other witness "
                     "visits: no branch applies and the ordinary protocol returns "
                     "a value. The two hypotheses concern different opaque terms "
                     "and are jointly satisfiable.",
        "refinement": "A faithful real patch whose fallback path calls the "
                      "ordinary access protocol but converts any value it returns "
                      "into an attribute error stops every name that only ordinary "
                      "access resolves from resolving at all — while still raising "
                      "with the right name where that protocol raises, so the F2P "
                      "test would incidentally pass. A SWE-bench resolution needs "
                      "PASS_TO_PASS too, and this breaks it broadly across the 426 "
                      "sky-coordinate P2P tests (any test reading an ordinary "
                      "instance attribute through the resolution hook, e.g. "
                      "test_extra_attributes, test_attr_inheritance). Not resolved.",
    },
    {
        "id": "atk-swallow-branch-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_SWALLOW_RAISE,
        "witness": _W_SWALLOW_RAISE,
        "rationale": "attacks C1 in the sub-case every other rival leaves to the "
                     "positives: the branch that applies RAISES rather than "
                     "resolving a value. C1 is an equality against that branch's "
                     "own outcome, whichever of the two it is, so surfacing it "
                     "unchanged is pinned on both halves. This rival honours the "
                     "resolve-a-value half exactly — so no other witness touches "
                     "it — and discards the other half, dropping the failure the "
                     "branch raised and letting the ordinary protocol answer in "
                     "its place. Its witness probes attr = \"kk\" where the "
                     "applying branch raises `e` and the ordinary outcome at that "
                     "name is not `e`; the two hypotheses concern different "
                     "opaque terms and are jointly satisfiable.",
        "refinement": "HONEST SCOPE, measured rather than argued. Its faithful "
                      "real patch wraps the resolution-branch block in a handler "
                      "that swallows whatever it raises and falls through to "
                      "`self.__getattribute__(attr)`. Built in the instance image "
                      "at base_commit with patch.diff applied and the test patch "
                      "applied, it PASSES the F2P test and leaves the "
                      "test_sky_coord.py suite byte-identical to gold "
                      "(1 failed / 427 passed / 3 skipped / 1 xfailed on both, the "
                      "single failure being the environment's stale leap-second "
                      "file, identical on gold). So this rival is NOT a "
                      "verify-does-not-imply-resolve hole and is not claimed to "
                      "be one: the recorded test set does not observe which "
                      "exception escapes the hook. What it does attest is "
                      "FAITHFULNESS strength. The real function propagates that "
                      "exception verbatim — measured on the same worktree, "
                      "`sc.altaz` raises AttributeError('NoneType' object has no "
                      "attribute 'to_geodetic'), `sc.lsr` a TypeError, "
                      "`sc.galactocentric` a ConvertError, `sc.hcrs` a UnitsError, "
                      "each with `return self.transform_to(attr)` in the traceback "
                      "— and a spec silent there would model a function that is "
                      "free to substitute its own failure, which is the very "
                      "substitution the fallback clause exists to forbid. The case "
                      "is here so that clause is pinned by a rival on both halves "
                      "and not by the positives alone.",
    },
    {
        "id": "atk-reclassify-branch-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_CLOBBER_KIND,
        "witness": _W_CLOBBER_KIND,
        "rationale": "attacks C1's raised-failure half at the COMPONENT no other "
                     "rival touches: the CLASS of the failure, as opposed to the "
                     "name it reports. C1 is an equality against the applying "
                     "branch's own outcome, and on the raising half that outcome "
                     "is an `AttrError` carrying both a reported name and a kind. "
                     "Every other rival leaves the kind field alone — "
                     "`atk-swallow-branch-raise`, the only other rival on this "
                     "half, discards the branch's failure WHOLESALE and is "
                     "refuted by a disequality against the ordinary outcome, "
                     "which pins nothing about which component of the payload "
                     "survives — so before this case the kind component was "
                     "pinned by the positives alone. This rival reaches the "
                     "branch, surfaces a failure rather than a value, and "
                     "preserves the reported NAME verbatim; it differs only by "
                     "re-classifying the failure as an attribute-lookup failure, "
                     "the class `AttrError` defaults to and the only class a "
                     "manufactured no-such-attribute report can carry. So it "
                     "survives any clause phrased over the reported name alone, "
                     "which is what makes it worth its own case. Its witness "
                     "probes attr = \"mm\" with the single hypothesis that the "
                     "applying branch there raises a failure whose class is not "
                     "the default; the refutation is by constructor-field "
                     "disjointness on `AttrError` and assumes nothing about the "
                     "ordinary protocol, so no separation assumption is needed "
                     "and the hypothesis is trivially satisfiable. Distinct from "
                     "`atk-swallow-branch-raise` in BOTH directions, measured: "
                     "that rival's witness does not fire on this one (exit 1) and "
                     "this witness does not fire on that one (exit 1), so neither "
                     "case subsumes the other.",
        "refinement": "HONEST SCOPE, on the same footing as "
                      "`atk-swallow-branch-raise`'s: the recorded test set does "
                      "not observe which exception CLASS escapes the hook, so a "
                      "faithful real patch that re-raised each branch failure as "
                      "an attribute-lookup failure under the name that failure "
                      "already reported is NOT claimed to be a "
                      "verify-does-not-imply-resolve hole, and this case is not "
                      "offered as one. What it attests is FAITHFULNESS strength. "
                      "The real function propagates the branch's failure "
                      "verbatim, class included, and mapping.md records three of "
                      "the four measured raising names carrying a class that is "
                      "not an attribute-lookup failure at all — so a spec silent "
                      "on the class would model a function free to re-label any "
                      "of them, which is the substitution the fallback clause "
                      "exists to forbid. The case is here so that both COMPONENTS "
                      "of the raised payload are pinned by a rival rather than by "
                      "the positives alone, the same reason the reported-name "
                      "component gets `atk-relabel-reported-name`.",
    },
    {
        "id": "atk-foreign-resolution-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_FOREIGN_RESOLUTION,
        "witness": _W_FOREIGN_RESOLUTION,
        "rationale": "attacks C2 from the side no other rival covers: the "
                     "fallback FABRICATES A SUCCESS — it is the only rival that "
                     "puts on the no-branch path an `Except.ok` the ordinary "
                     "protocol never produced for the requested name. THIRD-AUDIT "
                     "CORRECTION to this rationale's own earlier wording, which "
                     "claimed every other C2 rival puts an `Except.error` there "
                     "and named the two synthesize rivals, the decorated-name "
                     "rival and `atk-discard-ordinary-value`: that enumeration is "
                     "false and was measured false against the rival sources. Only "
                     "the two synthesize rivals and `atk-discard-ordinary-value` "
                     "fabricate a failure; `atk-ordinary-lookup-of-decorated-name` "
                     "returns `ordinaryLookup self (\"_\" ++ attr)`, which is an "
                     "`Except.ok` wherever the protocol succeeds at the decorated "
                     "name, and `atk-relabel-reported-name` (a C2 rival the old "
                     "list omitted entirely) propagates successes verbatim. So the "
                     "discriminating property is not error-vs-value on the fallback "
                     "path but WHERE the success comes from: here the fallback "
                     "returns `Except.ok v` for a `v` that is a genuine resolution "
                     "result for a DIFFERENT name than the one requested, so the "
                     "rival never synthesizes a payload out of nothing. C2 is an "
                     "equality against the ordinary outcome for the "
                     "SAME name, which is what rejects it, and a clause phrased as "
                     "\"the fallback may not fabricate a FAILURE\" would admit it. "
                     "The witness probes "
                     "attr = \"ii\" where no branch resolves, a branch DOES "
                     "resolve at the foreign name \"jj\", and the ordinary "
                     "outcome at \"ii\" is not that value; the three hypotheses "
                     "concern three different opaque terms and are jointly "
                     "satisfiable (the gate's `: False` probe fails on them). It "
                     "is also the surviving analogue of the nagini "
                     "normal-return-guard lane, whose literal transliterations "
                     "are ill-typed or need a closed `AttrValue` this carrier "
                     "does not have.",
        "refinement": "A faithful real patch whose fallback path returns a value "
                      "belonging to some other name's resolution — rather than "
                      "consulting the ordinary access protocol for the name asked "
                      "for — raises no error at all on the path the regression "
                      "exercises, so the F2P test's "
                      "`pytest.raises(AttributeError, match=\"random_attr\")` "
                      "reports DID NOT RAISE and the patch does NOT resolve. It "
                      "also hands back visibly wrong values for ordinary "
                      "attribute reads, breaking the sky-coordinate P2P suite "
                      "(test_extra_attributes, test_attr_inheritance) on top of "
                      "the F2P failure.",
    },
    {
        "id": "atk-fallback-reclassify-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_FALLBACK_CLOBBER_KIND,
        "witness": _W_FALLBACK_CLOBBER_KIND,
        "rationale": "attacks C2's failing half at the COMPONENT no other rival "
                     "touched: the CLASS of the failure, as opposed to the name "
                     "it reports. C2 is an equality against the ordinary "
                     "attribute-access outcome AS A WHOLE, so on the failing side "
                     "it pins both fields of the payload. The reported-name field "
                     "is pinned by a rival — `atk-relabel-reported-name` — but "
                     "before this case the CLASS field was pinned by the positives "
                     "alone, and that was MEASURED rather than argued: this rival "
                     "was built and checked against all eleven other witnesses in "
                     "this manifest and every one of them FAILS on it (exit 1, "
                     "eleven for eleven), so nothing here refuted it. It is the "
                     "exact analogue on C2's failing half of what "
                     "`atk-reclassify-branch-failure` is on C1's raising half: it "
                     "consults the ordinary protocol, propagates its successes "
                     "verbatim, raises exactly where it raises, and preserves the "
                     "reported NAME — differing only by re-labelling the class as "
                     "an attribute-lookup failure, the class `AttrError` defaults "
                     "to. So it survives any clause phrased over the reported name "
                     "alone, which is what earns it its own case. Its witness "
                     "probes attr = \"oo\" with two hypotheses on two different "
                     "opaque terms — no branch applies there, and the ordinary "
                     "outcome is a failure whose class is not the default — "
                     "jointly satisfiable, with the refutation by "
                     "constructor-field disjointness on `AttrError`.",
        "refinement": "HONEST SCOPE, on the same footing as "
                      "`atk-reclassify-branch-failure`'s and "
                      "`atk-swallow-branch-raise`'s: the recorded test set asserts "
                      "on WHICH NAME the surfaced failure blames "
                      "(`match=\"random_attr\"`), not on which exception class "
                      "escapes, so a faithful real patch that re-raised the "
                      "ordinary protocol's failure as an attribute-lookup failure "
                      "under the name that protocol already reported is NOT "
                      "claimed to be a verify-does-not-imply-resolve hole, and "
                      "this case is not offered as one. What it attests is "
                      "FAITHFULNESS strength. The ordinary access protocol's "
                      "failure is propagated verbatim by the modeled function, "
                      "class included — a value that protocol computes on demand "
                      "can fail in the same open-ended way a transform target can, "
                      "which is exactly why `AttrError` carries a `kind` at all — "
                      "so a spec silent on the class would model a function free "
                      "to re-label it. The case is here so BOTH components of the "
                      "fallback payload are pinned by a rival rather than by the "
                      "positives alone, which is the same reason the "
                      "reported-name component gets `atk-relabel-reported-name`.",
    },
    {
        "id": "atk-fallback-swallow-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_FALLBACK_SWALLOW,
        "witness": _W_FALLBACK_SWALLOW,
        "rationale": "the SWALLOW shape on C2 — the exact analogue of what "
                     "`atk-swallow-branch-raise` is on C1 — and the second sub-"
                     "domain this manifest left unrefuted. The two directions on "
                     "C2's success half are covered: "
                     "`atk-discard-ordinary-value` DISCARDS a value the ordinary "
                     "protocol produced, and `atk-foreign-resolution-value` "
                     "INVENTS one. Neither is refuted where that protocol FAILS "
                     "and a success is substituted for the failure: the former "
                     "propagates the failure PERFECTLY, payload included (that is "
                     "its whole design), and the latter's fallback overrides the "
                     "ordinary outcome UNCONDITIONALLY, so its witness needs only "
                     "a disequality and never visits the erroring side. MEASURED: "
                     "this rival survives all eleven other witnesses in this "
                     "manifest (exit 1, eleven for eleven), so it was refuted by "
                     "nothing here. It propagates a value the ordinary protocol "
                     "produced verbatim, and where that protocol raises it drops "
                     "the failure and hands back a value some unrelated name's "
                     "resolution produced — so it never fabricates a payload out "
                     "of nothing, and a clause phrased as \"a value the ordinary "
                     "protocol produces is handed back verbatim\" would admit it. "
                     "Only C2's being an equality on the WHOLE outcome rejects it. "
                     "Its witness probes attr = \"qq\" with three hypotheses on "
                     "three different opaque terms — no branch applies there, a "
                     "branch resolves at the foreign name \"rr\", and the ordinary "
                     "outcome at \"qq\" is a failure — jointly satisfiable. The "
                     "failure payload is left entirely FREE, which is what "
                     "separates this refutation from the reported-name and class "
                     "rivals: it does not depend on which failure it is.",
        "refinement": "A faithful real patch whose fallback path consults the "
                      "ordinary access protocol, returns any value it produces, "
                      "and on a failure substitutes a value belonging to some "
                      "other name's resolution raises nothing at all on the path "
                      "the regression exercises — so the F2P test's "
                      "`pytest.raises(AttributeError, match=\"random_attr\")` "
                      "reports DID NOT RAISE and the patch does NOT resolve. It "
                      "also hands back visibly wrong values wherever ordinary "
                      "attribute access legitimately fails, breaking the "
                      "sky-coordinate P2P suite (test_extra_attributes, "
                      "test_attr_inheritance) on top of the F2P failure. This is a "
                      "genuine verify-does-not-imply-resolve rival, unlike the two "
                      "failure-class cases whose scope is faithfulness only.",
    },
]

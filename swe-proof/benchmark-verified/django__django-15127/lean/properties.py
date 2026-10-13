# properties.py — G-PBT falsification battery for django__django-15127 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over; the mechanics are re-expressed against this backend's carrier. Each
# SPEC_TESTS case is a FULL Solution.lean variant that shares the FROZEN spec
# byte-for-byte (only the impl region — and, where a positive control honestly
# reproves — the proof body is edited), screened by variant_scope before any
# build. Every expect="reject" case carries a refutation `witness`: a snippet that
# ELABORATES against the rival and FAILS on the frozen solution, so the rejection
# is attributable to the postcondition and not to a frozen tactic script that
# merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   resolveTagMap (tagsSettingChanged : Bool)
#                 (defaultTags overrideTags prevTagMap : List (Int × String))
#                 : List (Int × String)
#   One obligation, `theorem correct_resolveTagMap`, quantified over all four
#   inputs with NO precondition hypothesis. Its postcondition has exactly TWO
#   independent top-level clauses, and together they are exhaustive in the Bool:
#     (1) tagsSettingChanged = true  → result = mergeTags defaultTags overrideTags
#     (2) tagsSettingChanged = false → result = prevTagMap
#   `mergeTags d o = o ++ d` is a TRANSPARENT total function of its two arguments
#   (the overrides ahead of the defaults, so a first-match association lookup over
#   the result yields the override value for a level carried by both sources and
#   the default value otherwise). There is no `opaque` callee and no axiom
#   anywhere in this bundle, so the whole carrier COMPUTES: every witness below
#   states the refutation at concrete literal inputs and closes by `decide`. No
#   witness needs to condition on the carrier, and none binds anything — so none
#   can be `witness-inconsistent`.
#
# WHAT THE SPEC DEFENDS (the load-bearing facts, carried from the nagini sibling):
#   * Under the change-indicator, the result is REDERIVED from the two current
#     configuration sources with the override taking precedence per level. This
#     closes all three merge classes the nagini battery separated:
#       - a level both sources carry      -> the override value wins;
#       - a level only the defaults carry -> the default value survives;
#       - a level only the override carries -> present, with the override value
#         (this is the discriminating class the sole F2P test turns on).
#   * Under any other configuration change the previously-cached mapping is
#     returned EXACTLY, so the second clause is not free-floating either.
#   Because clause (1) pins the result to `mergeTags` — a function OF the two
#   inputs, not an opaque answer-key — the nagini sibling's "ungrounded oracle
#   echo" analysis carries over unchanged: the honest cheapest impl IS the merge,
#   so there is no answer-key to echo without doing the work. The rivals below
#   therefore attack the merge DIRECTION, a DROPPED sub-domain of levels, the
#   never-rederived (stale) branch, the override being ignored outright, and the
#   guard being inverted so the two clauses are satisfied on the wrong sides.
#
# CARRIER NARROWING vs the nagini sibling. Nagini modeled the mapping as a
# three-slot record behind fractional read permission and contracted a per-slot
# identity pin; this backend models the same behavior over a transparent
# association list. Every nagini rival that attacked the MERGE SEMANTICS has a
# direct counterpart here (the per-case `rationale` names the nagini id it ports),
# and the per-slot attacks become sub-domain attacks on the single list-valued
# clause.
#
# AUDIT NOTE (independent re-derivation of every case). The two prose pointers
# that used to read "see the id map in `assessment`" / "see `assessment`" were
# DANGLING: no `assessment` object is defined in this module or consumed by the
# gate, so they cited evidence a reader cannot inspect. The per-nagini-id mapping
# now lives in each case's own `rationale`, and the per-case rival/gold witness
# exit codes are recorded in meta.json's G-PBT case list. Two substantive repairs
# accompanied that: `weak-empty-new-levels` was added (the nagini
# uniq-empty-custom shape was recorded as "collapsed into weak-drop-new-levels",
# but it is a DISTINCT impl on this carrier — the level's key survives and only
# its tag is blanked — and it lands as its own rival), and
# `weak-recompute-when-cache-empty` was added to cover a conditional near-miss on
# clause (2) that no existing rival reached.
#
# LANES THAT DO NOT PORT (each stated with its reason; none is a hard case dodged):
#   * FRAME-MUTATION — the nagini sibling's #1 class and its two rivals
#     (uniq-frame-mutate-defaults / uniq-frame-mutate-override) both rejected for
#     INSUFFICIENT PERMISSION after writing a read-only input in place. Lean is
#     referentially transparent: there is no aliasing and no fractional
#     permission, so "store into a read-only input" is not expressible at all and
#     the lane is genuinely VACUOUS here. No substitute is fabricated.
#     DEMONSTRATED, not asserted: the nearest expressible analogue — rebind a
#     local shadowing an input (`let mut d := defaultTags; d := mergeTags …`) and
#     return the merge — was built and it VERIFIES (exit 0), because rebinding a
#     local cannot be observed by any caller and the impl is still correct. So the
#     class cannot yield a rejectable rival here rather than merely being hard to
#     write: there is no observable "the input was damaged" for a spec to forbid.
#   * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class. An earlier
#     pass of this port recorded the class as vacuous on the grounds that
#     "`implementation_resolveTagMap` is a total Lean `def`, so a diverging
#     implementation cannot be written". That reason is FALSE and was retracted on
#     measurement: substituting a `while true do tagMap := …` body for the frozen
#     impl body yields a file whose IMPL REGION ELABORATES FINE (the do-notation
#     `while` compiles to `forIn Lean.Loop.mk`, needing no termination measure);
#     the only errors are in the proof region, at the frozen `rfl`. So a diverging
#     rival IS expressible here. What makes it unshippable is the witness side,
#     also measured: `¬ problem_spec_… (implementation_… …)` against that rival
#     fails with ``Tactic `decide` failed for proposition … forIn Lean.Loop.mk``,
#     i.e. the gate's own `_STUCK_REDUCTION` screen (`stuck_screen="reduction"`) —
#     the kernel cannot reduce the loop term, so no `decide`-shaped witness can
#     refute it and a case built on it would be recorded `witness-undecided`
#     rather than `rejected`. This bundle sets no
#     `loom.semantics.termination` option at all, so nothing here discharges a
#     termination obligation and the spec genuinely does not pin termination.
#     Recorded as a KNOWN HOLE (the spec is incomplete in this direction), NOT as
#     "the battery is complete because the class is empty".
#   * AXIOM_TESTS — dropped: the axiom lane is G-AX's job and this gate ignores
#     them. This bundle has no consumed axiom and no deep-model reference anyway
#     (the combination of the two sources is modeled directly), so G-AX is a skip
#     stub and the nagini axiom probes have no target here.
# ESCALATED SPEC FINDING (not patched here — a spec change must re-clear the
# equivalence and conformance gates, which are outside this lane). Clause (1) pins
# the result to LIST equality with `overrideTags ++ defaultTags`, but the behavior
# being modeled is a mapping keyed by level, and mapping.md + conformance_check.py
# both declare the carrier bijection to be "the dict the assoc list denotes under
# FIRST-MATCH lookup". Those two are not the same relation: the list form also
# fixes the multiplicity and ordering of shadowed entries, which the denoted
# mapping cannot observe. Consequence, machine-checked: a faithful impl that emits
# one entry per level —
#     overrideTags ++ defaultTags.filter (fun p => !overrideTags.any (…p.1))
# — denotes the SAME mapping as the frozen impl on every input tried (200k fuzzed
# inputs under the bundle's own pinned seed 15127, compared with
# conformance_check.py's own first-match collapse AND against its
# `{**defaults, **overrides}` oracle: 0 disagreements), yet the frozen spec
# PROVABLY refutes it: `¬ problem_spec_… (that impl …)` elaborates (exit 0) at
# e.g. tagsSettingChanged=true, defaultTags=[(40,"error")],
# overrideTags=[(40,"bad")], prevTagMap=[], while the same claim against the frozen
# impl fails (exit 1) with `decide` reporting the postcondition TRUE there. So the
# spec is SPEC-TOO-STRONG on the dedup axis: it rejects a correct patch. This is a
# soundness hole in the direction that costs benchmark validity least (it cannot
# admit a wrong impl) but it is still a defect, and it is reported rather than
# worked around. The battery below deliberately contains NO rival that turns on
# list multiplicity/order alone, so nothing here attests to that over-strong edge.
# The same edge makes its DUAL a deliberately-omitted VACUOUS rival, checked so the
# omission is a decision and not an oversight: `overrideTags ++ overrideTags ++
# defaultTags` (every override entry duplicated) is REJECTED by the frozen spec
# (module build exit 1) and a `decide` witness against it elaborates (exit 0), so
# it would have shipped as a clean-looking reject case — but it denotes the SAME
# mapping as the frozen impl on the declared carrier bijection (0 disagreements in
# 200,014 inputs against conformance_check.py's own first-match collapse and its
# `{**defaults, **overrides}` oracle at the pinned seed). Its rejection would
# therefore attest to the raw-list-equality artifact above, not to the modeled
# behavior, so it is NOT shipped: per attack C a rival that is observably
# identical to gold is vacuous.
from pathlib import Path

INSTANCE = "django__django-15127"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each lies ENTIRELY inside the region it names and is unique in
# the file, so the manifest breaks LOUDLY if the frozen solution ever changes.
# ---------------------------------------------------------------------------

# The whole frozen impl body (inside impl-start / impl-end).
_IMPL_OLD = """  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := mergeTags defaultTags overrideTags
  return tagMap"""

# The frozen tactic body (inside proof-start / proof-end). Only the BODY: the
# `theorem correct_resolveTagMap` statement above it is never touched, so the
# obligation survives byte-identically in every case.
_PROOF_OLD = """  intro tagsSettingChanged defaultTags overrideTags prevTagMap
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    subst h <;> rfl"""

for _a in (_IMPL_OLD, _PROOF_OLD):
    assert _BASE.count(_a) == 1, f"frozen anchor drifted: {_a!r}"


def _variant(impl, proof=None):
    """A full Solution.lean with the impl body replaced (and optionally the
    tactic body honestly re-closed for a reshaped positive control)."""
    src = _swap(_BASE, _IMPL_OLD, impl)
    if proof is not None:
        src = _swap(src, _PROOF_OLD, proof)
    return src


# ===========================================================================
# ADMISSIBILITY (verify) — the obligation must be SATISFIABLE at an F2P-shaped
# input. On this total, precondition-free carrier the analogue of
# PRECOND-TOO-STRONG is not "the Requires is unestablishable" (there is no
# Requires) but "the postcondition is UNSATISFIABLE at exactly the input the
# failing test observes" — a spec that pins the result to two contradictory
# things at that point would be proven at no input and every rival would still be
# rejected, so nothing else in the battery would notice. The case discharges
# `problem_spec_resolveTagMap` BY EVALUATION at the concrete F2P-shaped point, as
# a `have`, and only THEN closes the frozen obligation verbatim.
#
# The impl region is left byte-identical to the frozen one and the theorem
# STATEMENT is untouched; only the tactic body grows, so no assumption is
# introduced (no axiom/sorry/native_decide/new theorem).
#
# The `have` is load-bearing rather than a tautology, and that was MEASURED, not
# argued: it applies the real `problem_spec_resolveTagMap` at the point, so
# prepending the identical `have` to the weak-never-rederive rival and to the
# weak-drop-new-levels near-miss makes each file fail AT THE `have`'s OWN LINE
# (``Tactic `decide` proved that the proposition ¬(…)``) rather than later in the
# frozen script. A `have` that merely restated a definitional identity would have
# elaborated against those rivals too, which is the documented way this lane goes
# hollow elsewhere in the corpus.
_ADM_HAVE = """  have adm_f2p :
      problem_spec_resolveTagMap true
        [(10, "debug"), (20, "info"), (25, "success"), (30, "warning"), (40, "error")]
        [(20, "info"), (10, ""), (30, ""), (40, "bad"), (25, ""), (12, "custom")]
        [(10, "debug"), (20, "info"), (25, "success"), (30, "warning"), (40, "error")]
        (implementation_resolveTagMap true
          [(10, "debug"), (20, "info"), (25, "success"), (30, "warning"), (40, "error")]
          [(20, "info"), (10, ""), (30, ""), (40, "bad"), (25, ""), (12, "custom")]
          [(10, "debug"), (20, "info"), (25, "success"), (30, "warning"), (40, "error")]) := by
    unfold problem_spec_resolveTagMap implementation_resolveTagMap mergeTags
    decide
"""

_ADM_F2P = _variant(_IMPL_OLD, _ADM_HAVE + _PROOF_OLD)


def _wit(tags_changed, defaults, overrides, prev, note):
    """A refutation witness: `¬ problem_spec_… (implementation_… …)` at a
    CONCRETE literal input, closed by `decide`.

    The carrier is fully transparent (no opaque callee, no axiom), so `decide`
    computes both sides and no conditioning is needed. The head binds nothing, so
    there are no hypotheses that could be jointly unsatisfiable.

    Each witness below was built against the rival (must ELABORATE) and against
    the frozen solution (must FAIL) before shipping. Both builds are re-run by the
    gate for every case and their outcomes are recorded per case in meta.json
    (`gates.G-PBT.data.cases[].witness_checked` / `witness_subject`); the frozen
    side fails with `decide` reporting the postcondition TRUE at that input, i.e.
    a semantic refutation rather than a missing identifier or a stuck reduction.
    """
    args = f"{tags_changed} {defaults} {overrides} {prev}"
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_resolveTagMap {args}\n"
        f"    (implementation_resolveTagMap {args}) := by\n"
        f"  unfold problem_spec_resolveTagMap implementation_resolveTagMap mergeTags\n"
        f"  decide"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Where a reshape breaks the frozen tactic
# script the proof is honestly RE-CLOSED: the theorem STATEMENT stays
# byte-identical and no new axiom / lemma / sorry / native_decide is introduced.
# ===========================================================================

# pos-reorder: handle the NON-rederive case FIRST (early-return the cached
# mapping), then fall through to the recomputation. This reverses the branch
# order of the frozen impl and drops the accumulator entirely. Ports the nagini
# sibling's pos-control-reorder argument.
_POS_REORDER = _variant(
    """  if !tagsSettingChanged then
    return prevTagMap
  return mergeTags defaultTags overrideTags""",
    """  intro tagsSettingChanged defaultTags overrideTags prevTagMap
  cases tagsSettingChanged <;>
    refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all""",
)

# pos-inline: a local-variable reshape — bind the recomputed mapping to a named
# local FIRST (spelling the combination out in place of the helper call, which is
# definitionally the same term), and make the guard an explicit `= true` test.
# Same values, different statement shape; the frozen tactic body still closes it.
# Ports the nagini sibling's pos-control-inline argument.
_POS_INLINE = _variant(
    """  let recomputed := overrideTags ++ defaultTags
  let mut tagMap := prevTagMap
  if tagsSettingChanged = true then
    tagMap := recomputed
  return tagMap"""
)

# pos-match: a THIRD correct shape — dispatch by pattern match on the indicator
# with a direct return in each arm, so neither the accumulator nor an `if` is
# used. This is the shape whose two arms are written independently, which is
# exactly what a postcondition over-fit to a single-assignment accumulator would
# reject. No nagini counterpart; added because a battery whose only positives
# reshape the SAME `if` says less about clause independence.
_POS_MATCH = _variant(
    """  match tagsSettingChanged with
  | true => return mergeTags defaultTags overrideTags
  | false => return prevTagMap""",
    """  intro tagsSettingChanged defaultTags overrideTags prevTagMap
  cases tagsSettingChanged <;>
    refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all""",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits ONLY the impl region; each carries a witness that
# elaborates against the rival and FAILS on the frozen solution. The rivals are
# left with the FROZEN tactic body: that body will not close for a reshaped impl,
# which is precisely why the gate reads the witness instead of the rival's build.
# ===========================================================================

# weak-never-rederive: THE PRE-PATCH BEHAVIOR (the shape Solution_prepatch.lean
# carries). The cached mapping is returned unconditionally; the recomputation
# never happens. Ports uniq-stale-no-derivation.
_RIV_STALE = _variant(
    """  let mut tagMap := prevTagMap
  return tagMap"""
)

# weak-defaults-win: the merge DIRECTION inverted — the two sources are combined
# in the opposite order, so under a first-match lookup the DEFAULT value wins for
# a level both sources carry and the override is shadowed. Ports
# uniq-default-wins.
_RIV_DEFAULT_WINS = _variant(
    """  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := mergeTags overrideTags defaultTags
  return tagMap"""
)

# weak-drop-new-levels: partial-domain on the EXACT discriminating class. Override
# entries are kept only for levels the defaults ALREADY carry, so a level
# contributed solely by the override is silently dropped from the result. Levels
# both sources carry still resolve override-first, which makes this a NEAR-MISS
# that agrees with the frozen behavior over strictly more of the domain than
# weak-no-override does — hence its own witness, at a level only the override
# carries. Ports uniq-drop-custom-slot / uniq-empty-custom (the two nagini
# per-slot shapes collapse into this one sub-domain attack on the list carrier).
_RIV_DROP_NEW = _variant(
    """  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := (overrideTags.filter (fun p => defaultTags.any (fun q => q.1 == p.1)))
      ++ defaultTags
  return tagMap"""
)

# weak-no-override: the recomputation fires, but from the DEFAULTS ALONE — the
# override source is ignored entirely. The blunt sibling of weak-drop-new-levels:
# it is wrong for every level the override carries, not only the new ones. No
# separate nagini id; it is the degenerate end of the same merge-direction family
# and it independently pins that clause (1)'s right-hand side must depend on
# `overrideTags` at all.
_RIV_NO_OVERRIDE = _variant(
    """  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := defaultTags
  return tagMap"""
)

# weak-empty-new-levels: the second, DISTINCT near-miss on the discriminating
# class. A level the defaults do not carry is KEPT in the result, but its tag is
# blanked to the empty string; levels both sources carry pass through untouched.
# This is not the same impl as weak-drop-new-levels (which removes the entry
# outright): here the key set of the result is exactly the frozen key set, so
# every clause about WHICH levels are present still holds and only the VALUE at a
# newly introduced level is wrong. Ports nagini uniq-empty-custom, which the port
# had recorded as collapsing into weak-drop-new-levels; it does not collapse on
# this carrier, and it is the closest wrong impl to gold in the battery.
_RIV_EMPTY_NEW = _variant(
    """  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := (overrideTags.map (fun p =>
      if defaultTags.any (fun q => q.1 == p.1) then p else (p.1, "")))
      ++ defaultTags
  return tagMap"""
)

# weak-recompute-when-cache-empty: a CONDITIONAL violation of clause (2). The
# recomputation also fires when the cached mapping happens to be empty, so the
# rival agrees with the frozen behavior everywhere except on that one sub-domain.
# Every other rival deviates uniformly across its clause; this one is correct on
# most of both clauses, which is what makes it the sharpest test that clause (2)
# is pinned for EVERY cached value rather than merely on the inputs the other
# witnesses happen to use. No nagini counterpart.
_RIV_EMPTY_CACHE = _variant(
    """  let mut tagMap := prevTagMap
  if tagsSettingChanged || prevTagMap.isEmpty then
    tagMap := mergeTags defaultTags overrideTags
  return tagMap"""
)

# weak-inverted-guard: the guard is INVERTED, so the recomputation fires on the
# other configuration changes and the cached mapping is left as-is on the one that
# matters. This is the only rival that violates clause (2) — it is refuted at
# tagsSettingChanged = false, where the frozen behavior must return the cached
# mapping and the rival returns the recomputation. Ports uniq-wrong-branch.
_RIV_INVERTED = _variant(
    """  let mut tagMap := prevTagMap
  if !tagsSettingChanged then
    tagMap := mergeTags defaultTags overrideTags
  return tagMap"""
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different CORRECT impl: the non-rederive case is handled "
            "FIRST as an early return of the cached mapping and the recomputation "
            "falls through, with no accumulator at all. Behaviourally identical on "
            "both arms of the exhaustive Bool, so both postcondition clauses hold. "
            "The frozen tactic body no longer matches the reshaped branch tree, so "
            "the proof is honestly re-closed by casing on the indicator (`cases … "
            "<;> refine … <;> first | rfl | simp_all`); the `theorem "
            "correct_resolveTagMap` STATEMENT is byte-identical and no new "
            "axiom/lemma/sorry/native_decide is introduced. If a faithful correct "
            "impl cannot verify => SPEC-TOO-STRONG (the postcondition would be "
            "over-fit to one branch order). Ports nagini pos-control-reorder."
        ),
    },
    {
        "id": "pos-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": (
            "local-variable reshape: the recomputed mapping is bound to a named "
            "local before the guard, the combination of the two sources is spelled "
            "out in place of the helper call, and the guard is written as an "
            "explicit `= true` test. Confirms the spec is not sensitive to whether "
            "the merge is reached through the helper name or written out. HONEST "
            "LIMIT of this case, recorded rather than overclaimed: `mergeTags d o` "
            "REDUCIBLY unfolds to `o ++ d` and `if c then` to `if c = true then`, "
            "so the reshape is DEFINITIONALLY equal to the frozen impl — which is "
            "why the frozen tactic body still closes it unchanged, and why it is a "
            "weak positive on its own. It earns its place as a cheap regression on "
            "the helper-vs-spelled-out question; the load-bearing soundness "
            "evidence is pos-reorder and pos-match, whose branch trees are NOT "
            "definitionally the frozen one and which therefore need a re-closed "
            "proof. If it cannot verify => SPEC-TOO-STRONG. Ports nagini "
            "pos-control-inline."
        ),
    },
    {
        "id": "pos-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": (
            "a THIRD correct shape: dispatch by pattern match on the indicator, each "
            "arm returning directly, so neither the accumulator nor an `if` appears. "
            "The two arms are written INDEPENDENTLY, which is what a postcondition "
            "over-fit to a single-assignment accumulator would reject — so this "
            "defends clause independence rather than just branch order. Proof "
            "honestly re-closed by casing on the indicator; statement byte-identical. "
            "No nagini counterpart (added for clause-independence coverage). If it "
            "cannot verify => SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": (
            "ports nagini admiss-f2p-shaped-input, whose in-body self-call "
            "established a half-permission Requires. This carrier has NO "
            "precondition, so the faithful analogue is not 'the Requires is "
            "establishable' but 'the postcondition is SATISFIABLE at exactly an "
            "F2P-shaped input' — the total-carrier form of PRECOND-TOO-STRONG. An "
            "earlier pass of this port recorded the lane as N/A because the "
            "obligation has no precondition hypothesis; that reasoning is wrong "
            "(it would retire the lane on the 366 precondition-free lean bundles "
            "that carry one), and the case is landed here instead. It discharges "
            "`problem_spec_resolveTagMap` BY EVALUATION (`decide`) at the "
            "concrete F2P-shaped point — the built-in defaults, an override that "
            "re-tags several known levels (some to the empty tag) AND introduces "
            "a level the defaults do not carry, and a cached mapping still "
            "holding the defaults-only value — as a `have`, and only then closes "
            "the frozen obligation verbatim. So the spec is shown satisfiable at "
            "the very input the sole FAIL_TO_PASS test observes, not merely "
            "provable in the abstract. The impl region is byte-identical to the "
            "frozen one and the theorem STATEMENT is untouched; only the tactic "
            "body grows, and no axiom/sorry/native_decide/new theorem appears. "
            "NOT a tautology, and that is measured: the identical `have` "
            "prepended to the weak-never-rederive rival and to the "
            "weak-drop-new-levels near-miss fails at its own line on both, so it "
            "genuinely applies the spec at that point. If it cannot verify => "
            "PRECOND-TOO-STRONG (the obligation would be unsatisfiable at the "
            "F2P input, which no rival in the battery would reveal)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED; else SPEC-TOO-WEAK) ----
    {
        "id": "weak-never-rederive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STALE,
        "refinement": (
            "returning the cached mapping unconditionally IS the pre-patch behavior "
            "this bundle's prepatch variant reproduces and G-DIFF flags: nothing "
            "reacts to a configuration change, so the cache keeps the value it was "
            "computed with at import time. The sole FAIL_TO_PASS test installs an "
            "override mapping (including a level the defaults do not carry) and "
            "asserts the cache equals it; with no recomputation the cache keeps the "
            "defaults-only mapping and the assertion fails. Its faithful real "
            "counterpart is the UNPATCHED code, which by construction does NOT "
            "resolve — so a verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by postcondition clause (1): with tagsSettingChanged = true the "
            "result must equal `mergeTags defaultTags overrideTags`, and the rival "
            "returns `prevTagMap`, which is an unrelated input. Attacks clause (1) at "
            "a point where the recomputed mapping and the cached mapping differ, i.e. "
            "it discriminates the binders overrideTags vs prevTagMap. If it VERIFIES "
            "=> SPEC-TOO-WEAK. Ports nagini uniq-stale-no-derivation."
        ),
        # Rederive requested; the override carries a level the defaults do not, so
        # the recomputation differs from the cached mapping. gold => the merge,
        # rival => the stale cached mapping.
        "witness": _wit(
            "true", '[(40, "error")]', '[(12, "custom")]', '[(40, "error")]',
            "rederive requested, override adds a level absent from the defaults: "
            "gold recomputes, rival keeps the cached mapping",
        ),
    },
    {
        "id": "weak-defaults-win",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DEFAULT_WINS,
        "refinement": (
            "combining the two configuration sources in the opposite order makes the "
            "DEFAULT value win for any level both sources carry, so a level the user "
            "re-tags keeps its built-in value. The FAIL_TO_PASS test re-tags levels "
            "the defaults already carry and asserts the cache equals the override "
            "mapping exactly; with the default winning, those levels keep their "
            "built-in values and the equality fails. A faithful patch that combined "
            "the sources in this order does NOT resolve."
        ),
        "rationale": (
            "REJECTED by postcondition clause (1), which pins the result to "
            "`mergeTags defaultTags overrideTags` — override-precedence. The rival "
            "computes `mergeTags overrideTags defaultTags`; on an input where both "
            "sources carry the SAME level these are different lists, so the pinned "
            "equality cannot hold. Attacks clause (1) on the both-sources-overlap "
            "sub-domain, discriminating the ORDER of defaultTags vs overrideTags. If "
            "it VERIFIES => SPEC-TOO-WEAK. Ports nagini uniq-default-wins."
        ),
        # Both sources carry level 40 with different values, so the two orders
        # produce different lists. gold => override first, rival => defaults first.
        "witness": _wit(
            "true", '[(40, "error")]', '[(40, "bad")]', '[(40, "error")]',
            "a level BOTH sources carry: gold puts the override value first, "
            "the rival puts the default value first",
        ),
    },
    {
        "id": "weak-drop-new-levels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_NEW,
        "refinement": (
            "keeping override entries only for levels the defaults already carry "
            "corresponds to a recomputation that updates the known levels but drops "
            "the ones the user introduces. The FAIL_TO_PASS test's override mapping "
            "includes a level the built-in defaults do not carry, and asserts the "
            "cache equals that mapping; with the new level dropped, a lookup for it "
            "falls back to the empty tag instead of the configured one and the "
            "assertion fails. A faithful patch that filtered the recomputation to "
            "the built-in levels does NOT resolve."
        ),
        "rationale": (
            "REJECTED by postcondition clause (1): the pinned right-hand side carries "
            "EVERY override entry, and the rival's filter removes those whose level "
            "the defaults do not carry, so the two lists differ. This is a NEAR-MISS "
            "of weak-no-override — it still resolves overlapping levels "
            "override-first, so it agrees with the frozen behavior over strictly more "
            "of the domain — and it therefore gets its OWN witness, at a level only "
            "the override carries, which is the exact sub-domain its rationale "
            "claims. If it VERIFIES => SPEC-TOO-WEAK. Ports nagini "
            "uniq-drop-custom-slot / uniq-empty-custom (the two nagini per-slot "
            "shapes collapse into this one sub-domain attack on the list carrier)."
        ),
        # Level 12 is carried ONLY by the override, so the rival's filter drops it
        # while gold keeps it. Note the overlapping-level sub-domain is deliberately
        # NOT exercised here: the rival is correct there, which is what makes this a
        # near-miss needing its own point.
        "witness": _wit(
            "true", '[(20, "info")]', '[(12, "custom")]', '[(20, "info")]',
            "a level only the OVERRIDE carries: gold keeps it, the rival filters "
            "it out because the defaults do not carry it",
        ),
    },
    {
        "id": "weak-no-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_OVERRIDE,
        "refinement": (
            "recomputing from the DEFAULTS ALONE corresponds to a recomputation that "
            "reads the built-in source but never the user-supplied one. The "
            "FAIL_TO_PASS test asserts the cache equals the override mapping it "
            "installed; a defaults-only cache matches it on no re-tagged level at "
            "all, so the assertion fails. A faithful patch that recomputed from the "
            "built-in defaults only does NOT resolve. It is also the blunt sibling of "
            "weak-drop-new-levels: wrong for EVERY level the override carries, not "
            "only the newly introduced ones."
        ),
        "rationale": (
            "REJECTED by postcondition clause (1): the result must equal "
            "`mergeTags defaultTags overrideTags`, which contains every override "
            "entry, and the rival returns `defaultTags`. This independently pins that "
            "clause (1)'s right-hand side must DEPEND on overrideTags at all — a "
            "rival ignoring that binder entirely is the one a battery that never "
            "varied it would miss. Refuted at its own input point (a two-entry "
            "defaults list, distinct from every other witness) so its claimed "
            "sub-domain is really demonstrated. If it VERIFIES => SPEC-TOO-WEAK. No "
            "single nagini id; the degenerate end of the nagini merge-direction "
            "family."
        ),
        # Defaults carry two levels, the override re-tags one of them; the rival
        # drops the override entry entirely. gold => override entry first.
        "witness": _wit(
            "true", '[(20, "info"), (40, "error")]', '[(40, "bad")]',
            '[(20, "info"), (40, "error")]',
            "the override source is ignored outright: gold prepends its entry, "
            "the rival returns the defaults unchanged",
        ),
    },
    {
        "id": "weak-empty-new-levels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY_NEW,
        "refinement": (
            "keeping a level the built-in defaults do not carry but blanking its "
            "tag corresponds to a recomputation that registers the user's new "
            "levels yet fails to carry their configured labels across. The sole "
            "FAIL_TO_PASS test installs an override mapping that includes a level "
            "the defaults do not carry and asserts the cache equals that mapping "
            "exactly; with the label blanked the key is present but its value is "
            "the empty tag instead of the configured one, so the equality fails. A "
            "faithful patch that carried the new levels over without their values "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by postcondition clause (1): the pinned right-hand side "
            "carries every override entry with ITS OWN value, and the rival "
            "replaces the value with the empty tag at any level the defaults do "
            "not carry. Distinct from weak-drop-new-levels rather than a respelling "
            "of it: that rival REMOVES the entry, so the two disagree with the "
            "frozen result in different components (key set vs value at a present "
            "key), and this one leaves the result's key set exactly equal to the "
            "frozen one. It is therefore the closest wrong impl in the battery — "
            "the strongest available test that clause (1) pins the VALUES and not "
            "merely which levels appear. If it VERIFIES => SPEC-TOO-WEAK. Ports "
            "nagini uniq-empty-custom, which an earlier pass of this port recorded "
            "as inexpressible-by-collapse; the audit re-derived it and it lands."
        ),
        # Level 12 is carried ONLY by the override, so the rival blanks its tag
        # while gold keeps "custom". The overlapping sub-domain is deliberately not
        # exercised: the rival is correct there, which is what makes it a near-miss.
        "witness": _wit(
            "true", '[(20, "info")]', '[(12, "custom")]', '[(20, "info")]',
            "a level only the OVERRIDE carries: gold keeps its configured tag, "
            "the rival keeps the level but blanks the tag",
        ),
    },
    {
        "id": "weak-recompute-when-cache-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY_CACHE,
        "refinement": (
            "also recomputing whenever the cached mapping happens to be empty "
            "corresponds to a receiver that treats an empty cache as a licence to "
            "rebuild on ANY configuration change. It resolves the FAIL_TO_PASS "
            "test, but it discards a cached mapping that must be preserved across "
            "unrelated configuration changes whenever that cache is empty — the "
            "cache stops being a function of the change that was actually signalled. "
            "A faithful patch with this extra disjunct is not the behavior the "
            "second clause describes."
        ),
        "rationale": (
            "REJECTED by postcondition clause (2): with tagsSettingChanged = false "
            "the result must equal prevTagMap for EVERY cached value, and the rival "
            "returns the recomputation on the sub-domain where that cache is empty. "
            "Unlike every other rival here it agrees with the frozen behavior on "
            "most of BOTH clauses and deviates only on that sub-domain, so it is "
            "the case that keeps clause (2) from being satisfied by a rival that is "
            "merely right at the particular cached values the other witnesses use. "
            "If it VERIFIES => SPEC-TOO-WEAK. No nagini counterpart."
        ),
        # The FALSE side with an EMPTY cache — the exact sub-domain the extra
        # disjunct reaches. gold returns the empty cached mapping untouched; the
        # rival recomputes, which differs because the two sources are non-empty.
        "witness": _wit(
            "false", '[(25, "success")]', '[(12, "custom")]', "[]",
            "no rederive requested and the cached mapping is empty: gold returns "
            "it untouched, the rival recomputes",
        ),
    },
    {
        "id": "weak-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVERTED,
        "refinement": (
            "inverting the guard makes the recomputation fire for the OTHER "
            "configuration changes and leaves the cache untouched for the one that "
            "matters. On the FAIL_TO_PASS test's change it would not recompute, so a "
            "lookup for a newly configured level returns the empty tag and the "
            "assertion fails; and it would needlessly recompute on unrelated "
            "configuration changes, discarding a cache that must be preserved. A "
            "faithful patch guarded the other way round does NOT resolve."
        ),
        "rationale": (
            "REJECTED by postcondition clause (2) — the ONLY rival here that violates "
            "the second clause, which is why it is not redundant with the others: "
            "with tagsSettingChanged = false the result must equal `prevTagMap`, and "
            "the rival returns the recomputation instead. (It violates clause (1) "
            "symmetrically on the other side.) The witness deliberately probes the "
            "FALSE side of the indicator, so this is also the case that keeps the "
            "battery from holding that binder fixed across every rival. If it "
            "VERIFIES => SPEC-TOO-WEAK. Ports nagini uniq-wrong-branch."
        ),
        # The FALSE side of the indicator, where the cached mapping (here empty)
        # must be returned untouched. gold => the cached mapping, rival => the
        # recomputation, which differs because the defaults are non-empty.
        "witness": _wit(
            "false", '[(30, "warning")]', "[]", "[]",
            "no rederive requested: gold returns the cached mapping untouched, "
            "the rival recomputes it",
        ),
    },
]


# The axiom lane belongs to G-AX, which this gate ignores. This bundle consumes no
# callee axiom and carries no deep-model reference (the combination of the two
# configuration sources is modeled directly over a transparent carrier), so the
# nagini sibling's axiom probes have no target here either.
AXIOM_TESTS = []

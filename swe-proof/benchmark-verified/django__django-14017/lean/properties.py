# properties.py — G-PBT falsification battery for django__django-14017 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte and keeps the
# `theorem correct_mergeFilters` STATEMENT byte-identical (the two soundness positives
# and every rival edit only the impl region — the frozen proof body still closes for
# both positives; the admissibility case additionally inserts satisfiability `have`s
# INSIDE the tactic body, ahead of the frozen closing cascade, which it re-emits
# verbatim), checked by variant_scope + the Lean
# verifier. Every expect="reject" case carries a refutation `witness`: a self-contained
# snippet that ELABORATES against the rival and FAILS on the frozen solution, so the
# rejection is attributable to the spec and not to a tactic script that merely stopped
# matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   mergeFilters (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult
#   The abstraction of a filter-node merge: given the left node (only its emptiness
#   is behaviourally relevant), an operand (three observable attributes: whether it is
#   itself a filter node, whether it is a standalone boolean-valued condition, and
#   whether it is empty), and a connector, it decides whether the operand may be
#   merged and, if so, which of three outcomes is produced. The SINGLE postcondition
#   `problem_spec_mergeFilters` is a conjunction of two independent clauses:
#     (A) ACCEPT/REJECT domain — `mergeable other = false ↔ result = rejected`, where
#         `mergeable other = other.isFilter || other.boolValued`. This is a biconditional:
#         the operand is rejected EXACTLY when it is neither a filter node nor a
#         standalone boolean condition. It pins both directions — a rejectable operand
#         MUST be rejected, and an acceptable operand must NOT be rejected. (This is the
#         discriminating content of the fix: accept a non-filter operand that is usable
#         on its own as a boolean condition.)
#     (B) BRANCH selection — when `mergeable other = true`, the result is fully
#         determined: an empty operand contributes nothing (`keepLeft`); failing that an
#         empty left node contributes nothing (`keepRight`); otherwise a fresh node
#         merging both under `conn` (`merged conn`). This pins the two identity branches,
#         the merge branch, AND that the merge carries EXACTLY the requested `conn`.
#
# The carrier is FULLY TRANSPARENT: `FilterNode`, `Operand`, `Connector`, `MergeResult`
# all derive `DecidableEq`, `mergeable` is a total transparent `def`, and there is NO
# opaque callee and NO constraining axiom (mapping.md: the operand attributes the merge
# inspects are modeled DEEPLY as boolean fields, not axiomatized). So every reject
# witness is stated at a CONCRETE input and closed with `decide` — no carrier
# conditioning is needed, and there is no opaque term to block refutation.
#
# LANES THAT DO NOT PORT (see 'assessment' for the full disposition):
#   * FRAME / PERMISSION-MUTATION. Nagini's surface had no heap parameter (all five
#     inputs pass-by-value primitives), so its battery already carried no frame-mutation
#     rival; and lean is referentially transparent regardless. The frame obligation here
#     lives inside clause (B) — the result's outcome and, for the merge branch, the
#     carried connector are pinned to the inputs — and is attacked structurally by the
#     branch/connector rivals. VACUOUS class.
#   * DIVERGENCE / NON-TERMINATION (nagini `weak-diverge-no-answer`, keyed off its
#     `Requires(MustTerminate(2))` totality obligation). Nothing to port, but NOT because
#     a diverging body is unwritable — `partial def` writes one and it passes variant_scope,
#     so that reason would be false. The class is unportable because divergence is not an
#     OBSERVABLE of this value carrier, in either of the two shapes it can take (both
#     measured with the real verifier):
#       - a `partial` loop whose result is DEAD (`while true do i := i + 1` before a
#         constant return) is discarded by the kernel, so the impl reduces definitionally
#         to that constant. Such a rival is refuted as a VALUE error, not a termination one
#         (its `decide` witness lands: rival exit 0 / gold exit 1), and the value error it
#         commits is one the clause-(A) rivals below already pin. Redundant, not new.
#       - a genuinely value-DEPENDENT divergence (`partial def spin n := spin (n+1)` feeding
#         the returned outcome) makes the impl term IRREDUCIBLE, so no witness can
#         discriminate it: `decide` fails on the rival side too (`Tactic 'decide' failed`,
#         exit 1 against BOTH the rival and gold), and the variant itself does not verify.
#     So on this backend the lane has nothing a witness could attribute to the spec. This is
#     the LEAN disposition and it is not the velvet `partial`-semantics known spec hole
#     (the corpus-wide termination-semantics finding): that hole needs
#     `set_option loom.semantics.termination "partial"`, which this bundle does not carry —
#     a diverging impl here does not verify vacuously, it does not verify at all.
#   * ADMISSIBILITY — LANDED BY AUDIT as `admiss-f2p-shape` (it was previously dropped,
#     for a reason that is wrong). The dropped reason was "the lean obligation
#     `∀ self other conn, problem_spec … (impl …)` carries no precondition hypothesis, so
#     nothing could be PRECOND-TOO-STRONG". The premise is true and the conclusion does
#     not follow: on a TOTAL carrier the analogue of an over-strong precondition is the
#     obligation being UNSATISFIABLE at exactly an F2P-shaped input — the postcondition
#     internally inconsistent there, so that no result value at all could discharge it and
#     the frozen impl is verified only because the reader never evaluated the clauses at
#     that point. The case tests that directly: `problem_spec_mergeFilters` is discharged
#     BY EVALUATION (`decide`), as two `have`s, at the two discriminating F2P operand
#     shapes — a NON-filter standalone-boolean operand, non-empty, into an empty left node
#     (pins `keepRight`) and into a NON-empty left node under `conn = or_` (pins
#     `merged or_`) — with the claimed result supplied CONCRETELY rather than as
#     `implementation_mergeFilters …`, so the step cannot be satisfied by echoing the impl.
#     The `have`s are then `clear`ed and the frozen tactic body closes the obligation
#     verbatim, so the case is still a faithful positive.
#     Informativeness control (audit, machine-checked with the real verifier): the same
#     shape asserting the spec of a WRONG result at the first input (`keepLeft` in place of
#     `keepRight`) does NOT close — `decide` reports the proposition, exit 1 — while the
#     shipped case elaborates, exit 0. So the `have` really evaluates the postcondition at
#     these inputs instead of discharging anything put in front of it.
#     If this case FAILS => PRECOND-TOO-STRONG (the obligation is unsatisfiable at exactly
#     the operand shape the fix is for).
#   * UNGROUNDED-ORACLE ECHO. As in nagini, the postcondition is fully GROUNDED in the
#     input attributes (`mergeable`, the emptiness fields, `conn`); there is no @Pure
#     answer-key to echo. N/A.
#   * AXIOM_TESTS (nagini had none). The axiom lane is G-AX's job and there is no opaque
#     callee here anyway. Empty.
#
# CARRIER NARROWING / BROADENING vs nagini:
#   * nagini `weak-control-flow-no-raise` (4f: a syntactic guard on an always-false
#     condition, so it never raises and returns a merge tag on the both-false operand)
#     and `weak-accept-everything` (4c: drops the guard) are DISTINCT in nagini only
#     because nagini distinguishes raise-vs-return control flow. On lean the "reject"
#     outcome is the VALUE `MergeResult.rejected`, not an exceptional control-flow effect,
#     so both collapse into the single rival `weak-accept-nonmergeable` (returns a
#     non-`rejected` value on the neither-mergeable operand). Refuted by clause (A) → the
#     4c/4f pair is ported as one case, noted here so the omission of a second is not a gap.
#     The collapse is DEFINITIONAL, not merely argued: transcribing 4f's always-false guard
#     (`if false then return MergeResult.rejected` ahead of the branch chain) and 4c's
#     guard-less body as two `def`s, `∀ s o c, rival_cfe s o c = rival_acceptnm s o c`
#     closes by `rfl`, and they agree on all 32 carrier inputs while both differing from
#     gold on the same 8. So a separate 4f case would be a VACUOUS duplicate — the same
#     impl under another spelling — which is why it is dropped rather than ported.
#   * ADDED `weak-skip-keepright`: nagini's `weak-branch-swap` (P2) touches the
#     empty-operand branch but its witness never reaches the empty-LEFT-node branch. The
#     lean carrier lets us pin the `keepRight` outcome directly, so a dedicated rival
#     varies the `self.empty` binder at a reject point (the one binder every other
#     witness holds at `false`) and attacks clause (B)'s keepRight sub-clause.
from pathlib import Path

INSTANCE = "django__django-14017"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchor ------------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and both positives) swap THIS block; the frozen proof body
# closes unchanged for the positives (a `cases … <;> decide` over the finite carrier),
# so the proof region is never touched.
_IMPL = (
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !(other.isFilter || other.boolValued) then\n"
    "    return MergeResult.rejected\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  if self.empty then\n"
    "    return MergeResult.keepRight\n"
    "  return MergeResult.merged conn"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reshape-nested: structurally-different but behaviourally identical. Keeps the
# `Id.run do` shape but reorders the acceptance disjunction, and replaces the flat
# short-circuit chain with an explicit NESTED if over the non-empty-operand arm
# (test the left node's emptiness inside the `!other.empty` branch). Output equals
# the frozen impl's on every input; the byte-identical theorem statement still closes
# with the frozen proof body (`cases … <;> decide` is insensitive to impl shape). No
# reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG.
_POS_RESHAPE = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !(other.boolValued || other.isFilter) then\n"
    "    return MergeResult.rejected\n"
    "  if !other.empty then\n"
    "    if self.empty then\n"
    "      return MergeResult.keepRight\n"
    "    else\n"
    "      return MergeResult.merged conn\n"
    "  return MergeResult.keepLeft",
)

# pos-pure-hoist: a structurally different CORRECT impl written as a pure functional
# `def` (no `Id.run do`, no early return) that hoists the mergeability test to the top
# and nests the branch selection under it. Semantics identical on every input; the
# byte-identical theorem statement closes with the frozen proof body. If it FAILS =>
# SPEC-TOO-STRONG (postcondition bound to the monadic/short-circuit impl shape).
_POS_PURE = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult :=\n"
    "  if mergeable other then\n"
    "    (if other.empty then MergeResult.keepLeft\n"
    "     else if self.empty then MergeResult.keepRight\n"
    "     else MergeResult.merged conn)\n"
    "  else MergeResult.rejected",
)


# ===========================================================================
# ADMISSIBILITY (satisfiability at the F2P-shaped input) — must VERIFY.
# ===========================================================================
# The frozen tactic body, verbatim, split at its `intro` so the probes can be
# inserted BETWEEN the intro and the closing cascade. Anchored (unique, exact) so a
# Solution.lean edit fails loudly here instead of silently shipping an
# admissibility case whose obligation is closed some other way.
_TAC_INTRO = "  intro self other conn\n"
_TAC_CLOSE = (
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  obtain ⟨se⟩ := self\n"
    "  obtain ⟨of, ob, oe⟩ := other\n"
    "  cases conn <;> cases se <;> cases of <;> cases ob <;> cases oe <;> decide"
)
assert _BASE.count(_TAC_INTRO + _TAC_CLOSE) == 1, "proof anchor drifted"

# Two satisfiability probes at the discriminating F2P operand shapes. The claimed
# result is written out CONCRETELY (not as `implementation_mergeFilters …`), so the
# `have` cannot be discharged by echoing the impl — it must evaluate both clauses of
# the postcondition at that input and find them jointly satisfiable there.
_ADMISS_PROBES = (
    # (a) a NON-filter standalone-boolean operand, non-empty, into an EMPTY left
    #     node: clause (A) must NOT force `rejected` (the operand is mergeable) and
    #     clause (B)'s cascade must pin `keepRight`. Jointly satisfiable at
    #     `keepRight` iff the widened acceptance and the keepRight branch agree.
    "  have admissible_keepRight :\n"
    "      problem_spec_mergeFilters\n"
    "        { empty := true } { isFilter := false, boolValued := true, empty := false }\n"
    "        Connector.and_ MergeResult.keepRight := by\n"
    "    unfold problem_spec_mergeFilters mergeable\n"
    "    decide\n"
    # (b) the same operand into a NON-empty left node under conn = or_: the merge
    #     branch, carrying EXACTLY the requested connector.
    "  have admissible_merged :\n"
    "      problem_spec_mergeFilters\n"
    "        { empty := false } { isFilter := false, boolValued := true, empty := false }\n"
    "        Connector.or_ (MergeResult.merged Connector.or_) := by\n"
    "    unfold problem_spec_mergeFilters mergeable\n"
    "    decide\n"
    # Cleared, so the frozen body below closes the real obligation unaided.
    "  clear admissible_keepRight admissible_merged\n"
)
_ADMISS = _swap(
    _BASE,
    _TAC_INTRO + _TAC_CLOSE,
    _TAC_INTRO + _ADMISS_PROBES + _TAC_CLOSE,
)
# The frozen closing cascade must survive verbatim: the probes are inserted ahead of
# it, so the frozen discharge is reproven, not replaced.
assert _TAC_CLOSE in _ADMISS, "admissibility case no longer closes with the frozen body"


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the witness — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-prepatch-narrowed-guard: rejects any operand that is not itself a filter node,
# ignoring the standalone-boolean-condition predicate — this IS the pre-patch guard.
# WRONG on the discriminating sub-domain (not a filter node, but a standalone boolean
# condition): rejects where the spec requires acceptance. Attacks clause (A), the
# "must NOT reject an acceptable operand" direction.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !other.isFilter then\n"
    "    return MergeResult.rejected\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  if self.empty then\n"
    "    return MergeResult.keepRight\n"
    "  return MergeResult.merged conn",
)

# weak-mirror-narrowed-guard: the mirror error — accepts only standalone boolean
# conditions and rejects same-kind filter nodes. WRONG on the (filter node, not a
# standalone boolean condition) sub-domain: rejects where the spec requires acceptance.
# Attacks clause (A), same direction, at a DIFFERENT binder setting (isFilter=true,
# boolValued=false).
_RIV_MIRROR = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !other.boolValued then\n"
    "    return MergeResult.rejected\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  if self.empty then\n"
    "    return MergeResult.keepRight\n"
    "  return MergeResult.merged conn",
)

# weak-accept-nonmergeable: drops the rejection guard entirely and never returns
# `rejected`; on the neither-mergeable operand (not a filter node AND not a standalone
# boolean condition) it returns a non-`rejected` value. Attacks clause (A), the "must
# REJECT a non-mergeable operand" direction. (Ports nagini's 4c accept-everything AND
# 4f control-flow-no-raise, which coincide on this value carrier — see header.)
_RIV_ACCEPT = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  if self.empty then\n"
    "    return MergeResult.keepRight\n"
    "  return MergeResult.merged conn",
)

# weak-branch-swap: correct accept-domain, but swaps the two identity outcomes —
# returns `keepRight` on an empty OPERAND and `keepLeft` on an empty left node. Attacks
# clause (B): on an empty operand the spec pins `keepLeft`.
_RIV_BRANCH_SWAP = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !(other.isFilter || other.boolValued) then\n"
    "    return MergeResult.rejected\n"
    "  if other.empty then\n"
    "    return MergeResult.keepRight\n"
    "  if self.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  return MergeResult.merged conn",
)

# weak-skip-keepright: correct accept-domain and empty-operand branch, but SKIPS the
# empty-left-node short-circuit and falls through to the merge branch. On a non-empty
# operand into an EMPTY left node the spec pins `keepRight` but the rival returns
# `merged conn`. Attacks clause (B)'s keepRight sub-clause; the only rival that varies
# the `self.empty` binder at a reject point (all others hold it at `false`).
_RIV_SKIP_KEEPRIGHT = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !(other.isFilter || other.boolValued) then\n"
    "    return MergeResult.rejected\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  return MergeResult.merged conn",
)

# weak-branch-precedence: correct accept-domain, and each identity branch returns the
# RIGHT outcome in isolation — but the two are tested in the wrong ORDER, so when BOTH
# sides are empty the left-node-empty test wins and the rival returns `keepRight` where
# the spec's `if other.empty then keepLeft else if self.empty then …` cascade pins
# `keepLeft`. Attacks clause (B)'s branch PRECEDENCE, the one sub-clause the other
# branch rivals leave unattacked: `weak-branch-swap` and `weak-skip-keepright` each vary a
# single emptiness binder while holding the other at `false`, so neither reaches the
# both-empty corner where the cascade's order is the only thing that decides the outcome.
# Observably wrong on exactly the 8 both-empty-accepted inputs.
_RIV_BRANCH_PRECEDENCE = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !(other.isFilter || other.boolValued) then\n"
    "    return MergeResult.rejected\n"
    "  if self.empty then\n"
    "    return MergeResult.keepRight\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  return MergeResult.merged conn",
)

# weak-wrong-merge-connector: correct accept-domain and branch selection, but the merge
# branch carries a FIXED connector instead of the requested `conn`. On the both-non-empty
# merge with `conn = or_` the spec pins `merged or_` but the rival returns `merged and_`.
# Attacks clause (B)'s connector sub-clause; the only rival that varies `conn` to `or_`.
_RIV_CONN = _swap(
    _BASE,
    _IMPL,
    "def implementation_mergeFilters\n"
    "    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do\n"
    "  if !(other.isFilter || other.boolValued) then\n"
    "    return MergeResult.rejected\n"
    "  if other.empty then\n"
    "    return MergeResult.keepLeft\n"
    "  if self.empty then\n"
    "    return MergeResult.keepRight\n"
    "  return MergeResult.merged Connector.and_",
)


# --- witnesses ---------------------------------------------------------------------
# Each states `¬ problem_spec_mergeFilters self other conn (impl self other conn)` at a
# concrete input, unfolds the spec + impl + `mergeable`, and closes with `decide` over
# the finite `DecidableEq` carrier. It ELABORATES against the rival (which produces the
# wrong outcome there) and FAILS on gold with `decide could not prove …` (gold satisfies
# the spec everywhere). No opaque term, so no carrier conditioning and no hypothesis.

# clause (A), acceptance direction, at (isFilter=false, boolValued=true): mergeable, so
# gold does NOT reject; the prepatch rival rejects.
_WIT_PREPATCH = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := false } { isFilter := false, boolValued := true, empty := false } Connector.and_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := false } { isFilter := false, boolValued := true, empty := false } Connector.and_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)

# clause (A), acceptance direction, at (isFilter=true, boolValued=false): mergeable, so
# gold does NOT reject; the mirror rival rejects.
_WIT_MIRROR = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := false } { isFilter := true, boolValued := false, empty := false } Connector.and_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := false } { isFilter := true, boolValued := false, empty := false } Connector.and_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)

# clause (A), rejection direction, at (isFilter=false, boolValued=false): NOT mergeable,
# so gold MUST reject; the accept-nonmergeable rival returns `merged`.
_WIT_ACCEPT = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := false } { isFilter := false, boolValued := false, empty := false } Connector.and_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := false } { isFilter := false, boolValued := false, empty := false } Connector.and_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)

# clause (B), keepLeft branch, at an empty OPERAND (other.empty=true, mergeable): gold
# pins `keepLeft`; the branch-swap rival returns `keepRight`.
_WIT_BRANCH_SWAP = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := false } { isFilter := true, boolValued := false, empty := true } Connector.and_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := false } { isFilter := true, boolValued := false, empty := true } Connector.and_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)

# clause (B), keepRight branch, at (self.empty=true, other non-empty, mergeable): gold
# pins `keepRight`; the skip-keepright rival returns `merged conn`. VARIES self.empty.
_WIT_SKIP_KEEPRIGHT = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := true } { isFilter := true, boolValued := false, empty := false } Connector.and_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := true } { isFilter := true, boolValued := false, empty := false } Connector.and_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)

# clause (B), branch PRECEDENCE, at BOTH sides empty (mergeable): gold's cascade tests the
# operand first and pins `keepLeft`; the precedence rival tests the left node first and
# returns `keepRight`. The only witness that holds self.empty AND other.empty at true.
_WIT_BRANCH_PRECEDENCE = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := true } { isFilter := true, boolValued := false, empty := true } Connector.and_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := true } { isFilter := true, boolValued := false, empty := true } Connector.and_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)

# clause (B), connector sub-clause, at both-non-empty with conn=or_ (mergeable): gold
# pins `merged or_`; the wrong-connector rival returns `merged and_`. VARIES conn.
_WIT_CONN = (
    "example : ¬ problem_spec_mergeFilters\n"
    "    { empty := false } { isFilter := true, boolValued := false, empty := false } Connector.or_\n"
    "    (implementation_mergeFilters\n"
    "      { empty := false } { isFilter := true, boolValued := false, empty := false } Connector.or_) := by\n"
    "  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable\n"
    "  decide"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reshape-nested",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": (
            "structurally-different but CORRECT impl: reorders the acceptance disjunction and "
            "replaces the flat short-circuit chain with an explicit nested if over the "
            "non-empty-operand arm. Output equals the frozen impl's on every input; the "
            "byte-identical theorem statement closes with the FROZEN proof body "
            "(`cases … <;> decide` over the finite carrier is insensitive to impl shape) — no "
            "reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to the flat short-circuit shape)."
        ),
    },
    {
        "id": "pos-pure-hoist",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure functional `def` (no "
            "`Id.run do`, no early return) that hoists the mergeability test to the top and "
            "nests the branch selection under it. Semantics identical on every input; the "
            "byte-identical theorem statement closes with the frozen proof body. If it FAILS "
            "=> SPEC-TOO-STRONG (postcondition bound to the monadic impl shape rather than the "
            "behaviour)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "LANDED BY AUDIT; the lane had been dropped for the wrong reason (\"the frozen "
            "obligation has no precondition, so nothing can be PRECOND-TOO-STRONG\"). The "
            "obligation IS an unconditional universal, so no hypothesis can be over-strong "
            "— but the analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at "
            "an F2P-shaped input (the postcondition internally inconsistent there, so that "
            "no result value could discharge it and the frozen impl verifies only because "
            "nothing evaluated the clauses at that point). This case tests that directly: "
            "`problem_spec_mergeFilters` is discharged BY EVALUATION (`decide`), as two "
            "`have`s, at the two discriminating F2P operand shapes — a NON-filter "
            "standalone-boolean operand, non-empty, into an EMPTY left node (clause (A) must "
            "not force `rejected` and clause (B) pins `keepRight`) and into a NON-EMPTY left "
            "node under conn=or_ (pins `merged or_`, connector carried exactly) — with the "
            "claimed result written CONCRETELY, not as `implementation_mergeFilters …`, so "
            "the step cannot be satisfied by echoing the impl. The `have`s are then cleared "
            "and the frozen tactic body closes the obligation verbatim (anchored by assert). "
            "Informativeness control (audit, machine-checked): the same shape asserting the "
            "spec of a WRONG result at the first input (`keepLeft` for `keepRight`) does NOT "
            "close — `decide` reports the proposition, exit 1 — while this case elaborates, "
            "exit 0. If this case FAILS => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch-narrowed-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the pre-patch behaviour: reject any operand that is not itself a filter "
            "node, ignoring the standalone-boolean-condition predicate. Its faithful real patch "
            "keeps the old narrow guard, so an operand that is a standalone boolean condition "
            "but not a filter node still raises TypeError and the F2P tests that combine a "
            "filter node with a standalone boolean condition FAIL — this is precisely the bug "
            "the patch fixes. It would NOT resolve (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause (A), the acceptance direction. On (isFilter=false, "
            "boolValued=true) the operand is mergeable, so the spec forbids `rejected`, but the "
            "rival rejects. Witness probes that exact operand and closes with `decide`. If it "
            "VERIFIES => SPEC-TOO-WEAK (the widened acceptance is unpinned)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "weak-mirror-narrowed-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MIRROR,
        "refinement": (
            "the mirror error — accept only standalone boolean conditions and reject same-kind "
            "filter nodes. A faithful patch with this guard would raise TypeError when merging "
            "a filter node with another filter node and break the regression tests that combine "
            "two same-kind filter nodes. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (A), the acceptance direction, at a DIFFERENT binder setting "
            "than the prepatch witness: (isFilter=true, boolValued=false) is mergeable, so the "
            "spec forbids `rejected`, but the rival rejects. Varies the isFilter/boolValued "
            "binders. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_MIRROR,
    },
    {
        "id": "weak-accept-nonmergeable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ACCEPT,
        "refinement": (
            "drops the rejection guard entirely; never returns the rejected outcome. A faithful "
            "patch that accepts any object would not raise TypeError on a non-filter, "
            "non-conditional operand, then build a filter node from a junk operand and break "
            "downstream, so the tests that rely on rejecting bad operands FAIL. It would NOT "
            "resolve. (Ports nagini's accept-everything AND control-flow-no-raise, which "
            "coincide on this value carrier — the reject outcome is a value, not a control-flow "
            "effect, so there is no separate raise-vs-return rival to distinguish.)"
        ),
        "rationale": (
            "REJECTED by clause (A), the REJECTION direction. On (isFilter=false, "
            "boolValued=false) the operand is not mergeable, so the spec pins `rejected`, but "
            "the rival returns a merge outcome. Witness probes the both-false operand and closes "
            "with `decide`. If it VERIFIES => SPEC-TOO-WEAK (the reject domain is unpinned)."
        ),
        "witness": _WIT_ACCEPT,
    },
    {
        "id": "weak-branch-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BRANCH_SWAP,
        "refinement": (
            "swaps the two identity outcomes: returns the operand-copy outcome on an empty "
            "OPERAND and the left-node-copy outcome on an empty left node. The real analogue "
            "returns a copy of the wrong side in each identity branch, so merging a non-empty "
            "conditional operand into an empty left node would yield an empty node instead of "
            "the operand-carrying one — the with-empty-Q F2P subtest FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (B), keepLeft branch. On an empty operand (other.empty=true) the "
            "spec pins `keepLeft`, but the rival returns `keepRight`. Witness varies the "
            "other.empty binder (true, where every other reject witness holds it false) and "
            "closes with `decide`. If it VERIFIES => SPEC-TOO-WEAK (the identity branches are "
            "unpinned)."
        ),
        "witness": _WIT_BRANCH_SWAP,
    },
    {
        "id": "weak-skip-keepright",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP_KEEPRIGHT,
        "refinement": (
            "skips the empty-left-node short-circuit and falls through to the merge branch, so "
            "a non-empty operand merged into an EMPTY left node builds a fresh combined node "
            "instead of just keeping the operand. The real analogue would combine into an empty "
            "container rather than returning a copy of the operand, changing the resulting node "
            "and breaking the empty-left-node behaviour the tests assert. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (B), keepRight branch. On (self.empty=true, non-empty mergeable "
            "operand) the spec pins `keepRight`, but the rival returns `merged conn`. Witness "
            "varies the self.empty binder to true — the one binder every other witness holds at "
            "false — and closes with `decide`. If it VERIFIES => SPEC-TOO-WEAK (the "
            "empty-left-node branch is unpinned)."
        ),
        "witness": _WIT_SKIP_KEEPRIGHT,
    },
    {
        "id": "weak-branch-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BRANCH_PRECEDENCE,
        "refinement": (
            "each identity branch returns the correct side in isolation, but the two tests "
            "are applied in the wrong ORDER, so when both operands are trivial the left "
            "node's emptiness decides first. The real analogue checks its own emptiness "
            "before the operand's, so merging two trivial operands returns a copy of the "
            "wrong side — the resulting node is built from the operand rather than the "
            "calling node, changing which type and content the caller gets back in the "
            "both-trivial case the regression tests cover. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (B), branch PRECEDENCE. The spec's consequent is a cascade "
            "(`if other.empty then keepLeft else if self.empty then keepRight else …`), so "
            "on a mergeable operand with other.empty=true AND self.empty=true it pins "
            "`keepLeft`; the rival returns `keepRight`. This is the sub-clause the other "
            "branch rivals cannot reach: weak-branch-swap and weak-skip-keepright each vary "
            "one emptiness binder with the other held at false, where either ORDER of the "
            "two tests gives the same answer. Witness is the only one holding BOTH "
            "emptiness binders at true. If it VERIFIES => SPEC-TOO-WEAK (the cascade's "
            "precedence is unpinned and the spec would admit either identity outcome when "
            "both sides are trivial)."
        ),
        "witness": _WIT_BRANCH_PRECEDENCE,
    },
    {
        "id": "weak-wrong-merge-connector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONN,
        "refinement": (
            "accept-domain and branch selection correct, but the merge branch carries a fixed "
            "connector instead of the requested one. The real analogue sets the combined node's "
            "connector to the wrong join (AND vs OR), so a disjunctive combination would build a "
            "conjunctive node and the F2P combined-boolean-expression test would return the "
            "wrong rows. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (B), connector sub-clause. On the both-non-empty merge with "
            "conn=or_ the spec pins `merged or_`, but the rival returns `merged and_`. Witness "
            "varies the conn binder to or_ (the only witness that does) and closes with `decide`. "
            "If it VERIFIES => SPEC-TOO-WEAK (the carried connector is unpinned)."
        ),
        "witness": _WIT_CONN,
    },
]


# No axioms are consumed by this spec: the operand attributes the merge inspects are
# modeled DEEPLY as boolean fields over a transparent `DecidableEq` carrier, and there
# is no opaque callee. The axiom lane is therefore empty and belongs to G-AX regardless.
AXIOM_TESTS = []

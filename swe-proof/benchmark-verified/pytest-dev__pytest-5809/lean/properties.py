# properties.py — PBT falsification battery for pytest-dev__pytest-5809 (lean).
#
# PORT of the nagini sibling's battery to the lean carrier. NOT a Lean module:
# a record of adversarial cases the G-PBT gate executes. Every spec case is a
# full Solution.lean variant that shares the frozen spec byte-identically (only
# the impl region — and, where noted, the proof body — is swapped via _swap, so
# variant_scope.same_spec holds by construction). Each reject case additionally
# carries a `witness`: a Lean snippet that provably discriminates the rival from
# the frozen solution at a concrete input.
#
# ----------------------------------------------------------------------------
# DEFENDED SURFACE
# ----------------------------------------------------------------------------
# One modeled function: the construction of the request-parameter mapping that
# is submitted when a captured terminal session is uploaded. It is a total
# function of the caller-supplied `contents : String` returning an ordered list
# of (key, value) pairs. The load-bearing postcondition pins the ENTIRE mapping:
#
#   result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]
#
# This single list-equality clause carries several independent obligations that
# a rival can attack in isolation:
#
#   * the FIRST pair forwards `contents` verbatim into the value slot (the only
#     input binder — the only place the result depends on the input);
#   * the SECOND pair fixes the language-neutral highlighter constant. This is
#     the entry the fix actually changes: the language-neutral value is invariant
#     of the interpreter, replacing an interpreter-version-derived value that the
#     F2P test now forbids;
#   * the THIRD pair fixes the retention constant;
#   * list equality also pins the COUNT (no extra pair) and the ORDER of the
#     three pairs — "these three pairs, in this order, are the entire mapping".
#
# ----------------------------------------------------------------------------
# PORTING NOTES (which nagini cases ported, which are vacuous/collapsed here)
# ----------------------------------------------------------------------------
# The nagini sibling models THREE separate field-producing functions
# (paste_mode_field / paste_body_field / paste_expiry_field), each with its own
# postcondition, plus a fractional-permission frame discipline and an axiom lane.
# The lean bundle narrows the surface to the single mapping-construction
# function, so the nagini cases re-project onto its clauses:
#
#   * paste_mode_field's load-bearing "== text_token()" clause  -> the ("lexer",
#     "text") pair of the list. nagini's weak-mode-wrong-const ports directly.
#   * nagini's weak-mode-prepatch-branch is a PARTIAL-DOMAIN rival: correct on
#     one sub-domain, wrong on the rest. Its specific partition (a py_major
#     binder) does not exist here — the modeled post-fix behavior is
#     version-independent. But the CLASS is not therefore inexpressible: this
#     carrier has a binder to partition, `contents`, and weak-lexer-partial-
#     domain below is correct exactly on the empty-contents sub-domain and wrong
#     on every non-empty one. That is the obligation the global wrong-constant
#     rival cannot reach — that the clause is INVARIANT across the input domain,
#     not merely pinned at some inputs. Ported as a re-partitioned rival, NOT
#     collapsed onto the wrong-constant one.
#   * nagini's pos-mode-branch-split (branch, return the correct value in both
#     arms) re-partitions the same way: pos-branch-split below branches on
#     `contents` and emits the correct pair either way. It carries what the first
#     two positives cannot — both of those reduce to the spec's own normal form,
#     so the frozen bare-`rfl` proof closes them; a symbolic branch does not
#     reduce, so this positive is the only one whose obligation needs an actual
#     case split. A correct impl whose CONTROL FLOW inspects the input must still
#     be admitted, or the spec is over-fit to branch-free shapes.
#     A fourth positive, pos-propositional-eq, covers the remaining obligation
#     shape: all three of the above are closed by `rfl` (bare or under a split),
#     i.e. each is DEFINITIONALLY the spec's normal form. A correct impl that
#     agrees only PROPOSITIONALLY (`contents ++ ""`, the identity but not by
#     reduction) needs a rewrite instead, and measured, the frozen bare `rfl`
#     fails on it while `simp` closes it.
#   * paste_body_field identity clause -> the ("code", contents) pair. nagini's
#     weak-body-drop-first ports directly (drop the leading element of the
#     forwarded input). nagini's pos-body-local-reshape ports as pos-2.
#   * paste_expiry_field clause -> the ("expiry", "1week") pair. nagini's
#     weak-expiry-wrong-const ports directly.
#   * FRAME-MUTATION (frame-mutate-contents) is Nagini fractional-permission
#     machinery. Lean is referentially transparent — `contents : String` is an
#     immutable value passed to a total pure `def`, so there is no aliasing, no
#     mutation operator to invoke, and no permission to under-grant — so that
#     class is VACUOUS here. The read-only-forward discipline it defended is
#     instead pinned structurally: the spec fixes result[0] = ("code", contents),
#     and the code-mishandling rivals below attack exactly that. Not fabricated
#     as a substitute; reported vacuous.
#   * The half-permission ADMISSIBILITY case (admiss-body-half-perm) is NOT
#     vacuous, and an earlier pass recorded it as such on a reason that measures
#     wrong. Its nagini MECHANISM (a fractional permission established at a
#     self-call) has no counterpart here, but the LANE does: the analogue on a
#     total carrier is the obligation being unsatisfiable at exactly an F2P-shaped
#     input. "The frozen obligation has no precondition" is not a demonstration
#     that the lane is empty — it only says the Nagini spelling is unavailable.
#     Ported as admiss-ground-f2p-input, which discharges the obligation at a
#     concrete non-empty session payload by EVALUATION before closing the frozen
#     obligation verbatim. Without it this battery tested two of the three
#     directions this gate exists to test.
#   * DIVERGENCE / non-termination: a KNOWN HOLE, not a vacuous class, and an
#     earlier pass had this backwards too. The frozen impl is a total `def`, but a
#     variant is free to write `partial def` (variant_scope bans sorry/axiom/
#     native_decide, not `partial`), and a diverging impl of this shape IS
#     writable and IS rejected by the verifier. What cannot be built is the
#     WITNESS: the non-terminating term never reduces, so `decide` on the
#     refutation reports its `Decidable` instance "did not reduce to `isTrue` or
#     `isFalse`" — the stuck-reduction shape the gate screens as
#     witness-undecided, which discriminates nothing because the same error
#     appears for a true claim. So the rejection could not be attributed to the
#     spec and the case is not shippable here. Recorded as a hole in what this
#     battery can certify, not as a class that does not exist.
#   * AXIOM_TESTS: dropped — the axiom lane is G-AX's job and this gate ignores it.
#
# Five lean-carrier rivals have no nagini counterpart but attack clauses of the
# list-equality spec that nagini split across the dict machinery: COUNT, ORDER
# and the pair KEYS. weak-order-swap attacks the ordering obligation;
# weak-count-extra-pair and weak-count-missing-pair attack the COUNT obligation
# from both directions (a fourth pair appended, and a required pair dropped).
# The count clause is claimed in the DEFENDED SURFACE above, so it is attacked
# rather than merely asserted: the ordering rival permutes a 3-element list and
# leaves the length untouched, so it cannot witness the count obligation.
# weak-lexer-wrong-key attacks the KEY half of a pair (right value, wrong
# parameter name) — nagini's carrier binds each field by its own function, so no
# single postcondition there pins the name a value is bound to.
# weak-lexer-empty-domain is the complement of weak-lexer-partial-domain: every
# other rival here is refuted at a NON-empty input, so the empty-contents point
# was the one sub-domain no witness sampled.
#
# WITNESS POINTS. The rivals deliberately refute at DISTINCT inputs rather than
# sharing one, so the battery's coverage is a set of genuinely different points
# and not one point spelled ten ways: "hi", "abc", "session-output", "xyz",
# "foo", "log", "term-log", and "" (the empty sub-domain). The two code-slot
# rivals in particular are near-misses of each other refuted at different inputs.
# ----------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5809"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Region-surgery: replace EXACTLY one unique occurrence of `old` (which must
    live inside the impl region — or, for a positive control, the proof body).
    Editing only those regions guarantees variant_scope.same_spec(_BASE, result)
    holds and the frozen `theorem correct_*` statement is preserved."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors that lie ENTIRELY inside the impl region and are unique ----------
# The whole gold impl body (accumulator over `++`), used to reshape positives.
_GOLD_IMPL = """Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("lexer", "text")]
  params := params ++ [("expiry", "1week")]
  return params"""

# Single-line impl anchors for the field-mishandling rivals (each unique — the
# spec's own occurrence of e.g. ("lexer", "text") is not prefixed by `params :=`).
_GOLD_CODE_LINE = '  params := params ++ [("code", contents)]'
_GOLD_LEXER_LINE = '  params := params ++ [("lexer", "text")]'
_GOLD_EXPIRY_LINE = '  params := params ++ [("expiry", "1week")]'


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-1) DIRECT-LITERAL reshape. Structurally different from the frozen
# accumulator-over-`++` shape: the mapping is built as one list literal with no
# mutable state and no folding. Semantically identical, so the frozen proof
# (`intro; unfold; rfl`) still closes. If this CORRECT impl failed to verify, the
# postcondition would be over-fit to the exact accumulator text => SPEC-TOO-STRONG.
_POS_LITERAL_IMPL = '[("code", contents), ("lexer", "text"), ("expiry", "1week")]'
_POS_LITERAL = _swap(_BASE, _GOLD_IMPL, _POS_LITERAL_IMPL)

# (pos-2) CONS-PREPEND reshape (the local-reshape positive ported from nagini's
# pos-body-local-reshape). Builds the SAME list by prepending onto a seed in the
# reverse of the frozen append order, exercising a different data-flow shape.
# Reduces to the same normal form, so `rfl` closes. Must verify or SPEC-TOO-STRONG.
_POS_CONS_IMPL = """Id.run do
  let mut params : List (String × String) := [("expiry", "1week")]
  params := ("lexer", "text") :: params
  params := ("code", contents) :: params
  return params"""
_POS_CONS = _swap(_BASE, _GOLD_IMPL, _POS_CONS_IMPL)

# (pos-3) BRANCH-SPLIT reshape — the positive ported from nagini's
# pos-mode-branch-split, re-partitioned onto the only binder this carrier has.
# The control flow INSPECTS `contents` but emits the SAME correct lexer pair in
# both arms, so the value is input-invariant even though the data flow is not.
# This is the one positive whose obligation is not closed by the frozen bare
# `rfl`: a branch on a symbolic `contents` does not reduce, so the proof body
# takes a case split (`split <;> rfl`) — permitted, since a variant may reprove
# and the frozen theorem STATEMENT is untouched. If a faithful correct impl that
# branches on the input could not be proven, the spec would be over-fit to
# branch-free shapes => SPEC-TOO-STRONG.
_POS_BRANCH_IMPL = """Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  if contents.isEmpty then
    params := params ++ [("lexer", "text")]
  else
    params := params ++ [("lexer", "text")]
  params := params ++ [("expiry", "1week")]
  return params"""
_GOLD_PROOF_BODY = """  intro contents
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  rfl"""
_POS_BRANCH_PROOF = """  intro contents
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  split <;> rfl"""
_POS_BRANCH = _swap(
    _swap(_BASE, _GOLD_IMPL, _POS_BRANCH_IMPL),
    _GOLD_PROOF_BODY, _POS_BRANCH_PROOF)

# (pos-4) PROPOSITIONAL-EQUALITY reshape, added by the second independent audit.
# The three positives above all land on a term the spec's own right-hand side
# reduces to, so each is closed either by the frozen bare `rfl` or by `rfl` under
# a case split — i.e. every one of them is DEFINITIONALLY the spec's normal form.
# That leaves an obligation shape untested: a correct impl whose agreement with
# the spec is only PROPOSITIONAL. Appending the empty string to the forwarded
# value is the identity, but not by reduction — `contents ++ ""` and `contents`
# are distinct terms for a symbolic `contents`, so the proof must actually rewrite
# with a library lemma rather than compute. Measured: the frozen bare `rfl` FAILS
# on this impl and `simp` closes it, which is what makes the case load-bearing
# rather than a fourth spelling of the same normal form. If a correct impl could
# only be admitted when it reduces to the spec's syntactic normal form, the spec
# would be over-fit to definitional agreement => SPEC-TOO-STRONG.
_POS_PROP_PROOF = """  intro contents
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  simp"""
_POS_PROP = _swap(
    _swap(_BASE, _GOLD_CODE_LINE,
          '  params := params ++ [("code", contents ++ "")]'),
    _GOLD_PROOF_BODY, _POS_PROP_PROOF)


# ===========================================================================
# ADMISSIBILITY (the third lane) — expect "verify"
# ===========================================================================
# The frozen obligation carries no precondition, so there is no guard that could
# be too strong in the Nagini sense. The analogue on a TOTAL carrier is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input — a spec that
# quantifies over every `contents` but that nothing can actually discharge at the
# input the test exercises. A positive that discharges the obligation at that
# concrete input, BY EVALUATION, before closing the frozen obligation verbatim,
# tests that directly.
#
# The `have _mapping` step is what makes this more than a restatement: it reduces
# the modeled behavior at a concrete non-empty session payload all the way down to
# a literal three-pair list, so the admission is pinned to the mapping actually
# assembled rather than closed by reflexivity over the same unevaluated term.
# Measured load-bearing: transplanted onto a wrong impl, the `have` ITSELF fails
# (`decide` proves its equation false) independently of the frozen obligation, so
# it is not a step that would pass regardless of what the impl does.
#
# Nothing is assumed: no new declaration, no new axiom, the theorem STATEMENT is
# byte-identical, and both `have`s sit inside the existing tactic body.
_ADMISS_HAVE = """  have _mapping : implementation_buildPasteParams "captured-session-output"
      = [("code", "captured-session-output"), ("lexer", "text"),
         ("expiry", "1week")] := by decide
  have _ground : problem_spec_buildPasteParams "captured-session-output"
      (implementation_buildPasteParams "captured-session-output") := by
    unfold problem_spec_buildPasteParams
    rw [_mapping]
"""
_ADMISS_GROUND = _swap(_BASE, _GOLD_PROOF_BODY, _ADMISS_HAVE + _GOLD_PROOF_BODY)


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject" (each with a discriminating witness)
# ===========================================================================

# (weak-lexer) WRONG highlighter constant. Ports nagini's weak-mode-wrong-const
# AND (collapsed — no py_major binder) weak-mode-prepatch-branch: returns the
# interpreter-version-derived highlighter the fix removes for EVERY input,
# instead of the language-neutral constant. Violates the ("lexer", "text") pair.
_RIVAL_LEXER = _swap(_BASE, _GOLD_LEXER_LINE,
                     '  params := params ++ [("lexer", "python3")]')
_WIT_LEXER = '''example : ¬ problem_spec_buildPasteParams "hi"
    (implementation_buildPasteParams "hi") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-code-drop) Drop the leading element of the forwarded input. Ports
# nagini's weak-body-drop-first. Forwards contents into the code slot but shifts
# it, so result[0] = ("code", contents.drop 1) ≠ ("code", contents) on every
# non-empty input. Attacks the ONLY input binder (`contents`).
_RIVAL_CODE_DROP = _swap(_BASE, _GOLD_CODE_LINE,
                         '  params := params ++ [("code", contents.drop 1)]')
_WIT_CODE_DROP = '''example : ¬ problem_spec_buildPasteParams "abc"
    (implementation_buildPasteParams "abc") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-code-const) IGNORE the input entirely, posting a fixed code value. A
# near-miss to weak-code-drop that fails differently: it does not depend on
# `contents` at all, so it agrees with gold on NO non-empty input rather than
# shifting. Distinct witness input pins that its violation is input-INDEPENDENT
# (the result never varies with the binder). Attacks the same input binder from
# the "unused input" direction that the drop rival cannot express.
_RIVAL_CODE_CONST = _swap(_BASE, _GOLD_CODE_LINE,
                          '  params := params ++ [("code", "")]')
_WIT_CODE_CONST = '''example : ¬ problem_spec_buildPasteParams "session-output"
    (implementation_buildPasteParams "session-output") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-expiry) WRONG retention constant. Ports nagini's weak-expiry-wrong-const.
# Violates the ("expiry", "1week") pair.
_RIVAL_EXPIRY = _swap(_BASE, _GOLD_EXPIRY_LINE,
                      '  params := params ++ [("expiry", "1day")]')
_WIT_EXPIRY = '''example : ¬ problem_spec_buildPasteParams "xyz"
    (implementation_buildPasteParams "xyz") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-order) SWAP the order of the last two pairs. No nagini counterpart (the
# nagini carrier is an unordered dict); here the postcondition is a LIST equality
# that pins order, so a rival emitting the right three pairs in the wrong order
# still violates it. Attacks the ordering obligation of the list-equality clause.
_RIVAL_ORDER_IMPL = """Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("expiry", "1week")]
  params := params ++ [("lexer", "text")]
  return params"""
_RIVAL_ORDER = _swap(_BASE, _GOLD_IMPL, _RIVAL_ORDER_IMPL)
_WIT_ORDER = '''example : ¬ problem_spec_buildPasteParams "foo"
    (implementation_buildPasteParams "foo") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-lexer-partial) PARTIAL-DOMAIN rival — the re-partitioned port of nagini's
# weak-mode-prepatch-branch. Correct exactly on the empty-contents sub-domain and
# wrong on every non-empty one, so it satisfies the load-bearing lexer clause at
# some inputs while violating it at the rest. This is the obligation the GLOBAL
# wrong-constant rival cannot reach: that the highlighter clause holds for EVERY
# `contents`, not merely at the inputs a spot check would sample. The witness is
# stated at a non-empty input, i.e. inside the sub-domain where the rival breaks.
_RIVAL_LEXER_PARTIAL = _swap(
    _BASE, _GOLD_LEXER_LINE,
    '  params := params ++ [("lexer", if contents.isEmpty then "text" else "python3")]')
_WIT_LEXER_PARTIAL = '''example : ¬ problem_spec_buildPasteParams "hi"
    (implementation_buildPasteParams "hi") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-count-extra) COUNT obligation, from the TOO-MANY direction: emit the three
# required pairs correctly and then APPEND a fourth. Every individual clause the
# other rivals defend is satisfied — code forwards, lexer and expiry are right,
# the order of the first three is right — so this is refuted solely by the
# "these three pairs are the ENTIRE mapping" half of the list equality.
_RIVAL_COUNT_EXTRA_IMPL = """Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("lexer", "text")]
  params := params ++ [("expiry", "1week")]
  params := params ++ [("format", "text")]
  return params"""
_RIVAL_COUNT_EXTRA = _swap(_BASE, _GOLD_IMPL, _RIVAL_COUNT_EXTRA_IMPL)
_WIT_COUNT_EXTRA = '''example : ¬ problem_spec_buildPasteParams "log"
    (implementation_buildPasteParams "log") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-count-missing) COUNT obligation, from the TOO-FEW direction: emit only the
# first two pairs, leaving the retention parameter off the mapping entirely. A
# near-miss to weak-expiry-wrong-const that fails differently — that rival sends
# the retention parameter with a wrong value, this one omits the pair — so it pins
# that the spec forbids leaving a parameter FREE, not merely mis-valued.
_RIVAL_COUNT_MISSING_IMPL = """Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("lexer", "text")]
  return params"""
_RIVAL_COUNT_MISSING = _swap(_BASE, _GOLD_IMPL, _RIVAL_COUNT_MISSING_IMPL)
_WIT_COUNT_MISSING = '''example : ¬ problem_spec_buildPasteParams "log"
    (implementation_buildPasteParams "log") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-lexer-key) WRONG PARAMETER NAME on the load-bearing pair, added by the
# second independent audit. Every rival above attacks a VALUE slot, the pair
# COUNT, or the ORDER; none attacks a KEY. This one emits the correct highlighter
# value under a different parameter name, so the mapping carries the right
# instruction spelled wrong: the service is never told which highlighter to use,
# while a value-only check on the encoded body would still find the expected
# token somewhere in it. Pins that the spec fixes the NAME each value is bound to
# and not merely the multiset of values present.
_RIVAL_LEXER_KEY = _swap(_BASE, _GOLD_LEXER_LINE,
                         '  params := params ++ [("mode", "text")]')
_WIT_LEXER_KEY = '''example : ¬ problem_spec_buildPasteParams "term-log"
    (implementation_buildPasteParams "term-log") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''

# (weak-lexer-empty) The COMPLEMENT partial-domain rival, added by the second
# independent audit: correct on every NON-empty input and wrong exactly on the
# empty one. weak-lexer-partial-domain partitions the same binder the other way,
# and every one of the eight rivals above is refuted at a NON-EMPTY input — so
# the empty-contents point was the one sub-domain the battery never sampled, and
# a rival that is wrong only there would have been missed by every existing
# witness. Its witness is therefore stated at "" specifically. Together the two
# partial-domain rivals pin the highlighter clause across BOTH halves of the only
# partition this carrier's single binder admits.
_RIVAL_LEXER_EMPTY = _swap(
    _BASE, _GOLD_LEXER_LINE,
    '  params := params ++ [("lexer", if contents.isEmpty then "python3" else "text")]')
_WIT_LEXER_EMPTY = '''example : ¬ problem_spec_buildPasteParams ""
    (implementation_buildPasteParams "") := by
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  decide'''


SPEC_TESTS = [
    {
        "id": "pos-literal-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LITERAL,
        "rationale": "structurally-different CORRECT impl: build the mapping as a "
                     "single list literal with no mutable accumulator. Same normal "
                     "form, so the frozen proof closes. Must verify or the "
                     "postcondition is over-fit to the accumulator shape "
                     "(SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-cons-prepend",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONS,
        "rationale": "local-reshape positive (ported from nagini pos-body-local-"
                     "reshape): build the SAME list by prepending onto a seed in "
                     "reversed order. Different data flow, identical result, `rfl` "
                     "closes. Must verify or SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-branch-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH,
        "rationale": "branch-split positive (the re-partitioned port of nagini "
                     "pos-mode-branch-split): the control flow INSPECTS the input "
                     "binder but emits the correct lexer pair in both arms. The "
                     "only positive whose obligation the frozen bare `rfl` does "
                     "not close — a branch on a symbolic input does not reduce, "
                     "so the proof body takes a case split (the theorem STATEMENT "
                     "is untouched). Must verify or the spec is over-fit to "
                     "branch-free impl shapes (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-propositional-eq",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PROP,
        "rationale": "PROPOSITIONAL-equality positive: the forwarded value is "
                     "appended with the empty string, which is the identity but "
                     "NOT by reduction — for a symbolic input the two terms are "
                     "distinct, so agreement with the spec must be rewritten with "
                     "a library lemma rather than computed. The other three "
                     "positives all land on the spec's own definitional normal "
                     "form; measured, the frozen bare `rfl` FAILS here and `simp` "
                     "closes it, so this is the only positive testing that the "
                     "spec admits a correct impl that agrees only "
                     "propositionally. Must verify or the spec is over-fit to "
                     "definitional agreement (SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-ground-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_GROUND,
        "rationale": "ADMISSIBILITY lane. The frozen obligation is unconditioned, "
                     "so the total-carrier analogue of PRECOND-TOO-STRONG is the "
                     "obligation being unsatisfiable at exactly an F2P-shaped "
                     "input. This discharges it at a concrete non-empty captured "
                     "session payload BY EVALUATION — the modeled behavior is "
                     "reduced to a literal three-pair list as a `have`, so the "
                     "admission is pinned to the mapping actually assembled and "
                     "not closed by reflexivity over the same unevaluated term — "
                     "and then closes the frozen obligation verbatim. Measured "
                     "load-bearing: transplanted onto a wrong impl the `have` "
                     "ITSELF fails, independently of the frozen obligation. "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical. Verifies, else the modeled behavior would "
                     "be unsatisfiable at a normal input.",
    },
    {
        "id": "weak-lexer-wrong-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LEXER,
        "rationale": "REJECT from the ('lexer','text') pair of the list-equality "
                     "postcondition: the rival emits the interpreter-version-derived "
                     "highlighter the fix removes, for every input.",
        "refinement": "its faithful real patch keeps the interpreter-version-derived "
                      "highlighter value. Under the F2P's actual runtime the encoded "
                      "request body carries that value, and the test now asserts the "
                      "language-neutral value appears instead — so the assertion "
                      "FAILS and the patch does NOT resolve. (This is exactly the "
                      "original bug; with no version binder on this carrier the "
                      "pre-patch branch and the wrong-constant rival coincide.)",
        "witness": _WIT_LEXER,
    },
    {
        "id": "weak-lexer-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LEXER_PARTIAL,
        "rationale": "PARTIAL-DOMAIN reject on the ('lexer','text') pair, "
                     "re-partitioned onto the only binder this carrier has: the "
                     "rival is CORRECT on the empty-contents sub-domain and wrong "
                     "on every non-empty one. Refuted at a non-empty input. This "
                     "attacks the INVARIANCE of the highlighter clause across the "
                     "input domain — the obligation the global wrong-constant "
                     "rival cannot reach, since that one is wrong everywhere.",
        "refinement": "its faithful real patch requests the language-neutral "
                      "highlighter only when the captured session is empty and the "
                      "interpreter-version-derived one otherwise. Under the F2P's "
                      "actual runtime the uploaded session is NON-empty, so the "
                      "encoded request body carries the version-derived value and "
                      "the assertion that the language-neutral value appears FAILS "
                      "— it does NOT resolve. A rival that is right on a sub-domain "
                      "the test never exercises is the sharpest kind of near-miss.",
        "witness": _WIT_LEXER_PARTIAL,
    },
    {
        "id": "weak-lexer-empty-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LEXER_EMPTY,
        "rationale": "COMPLEMENT partial-domain reject on the ('lexer','text') "
                     "pair: correct on every NON-empty input and wrong exactly on "
                     "the empty one. Every other rival in this battery is refuted "
                     "at a non-empty input, so the empty-contents point was the "
                     "one sub-domain no witness sampled and a rival wrong only "
                     "there would have escaped all of them. Refuted at \"\" "
                     "specifically. Together with weak-lexer-partial-domain this "
                     "pins the highlighter clause across BOTH halves of the only "
                     "partition this carrier's single binder admits.",
        "refinement": "its faithful real patch requests the version-derived "
                      "highlighter only when the captured session is empty and "
                      "the language-neutral one otherwise. Stated honestly: the "
                      "F2P uploads a NON-empty session, so this rival's encoded "
                      "body would carry the language-neutral value there and the "
                      "test would PASS — it is refuted by the modeled "
                      "postcondition, which pins the clause at every `contents` "
                      "including the empty one, and is carried because the "
                      "sub-domain a test never exercises is exactly where an "
                      "unattacked clause hides. The reverse-partitioned sibling "
                      "weak-lexer-partial-domain is the one whose F2P actually "
                      "fails.",
        "witness": _WIT_LEXER_EMPTY,
    },
    {
        "id": "weak-lexer-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LEXER_KEY,
        "rationale": "REJECT from the KEY half of the ('lexer','text') pair — the "
                     "obligation no other rival attacks. Every other rival changes "
                     "a VALUE, the pair COUNT, or the ORDER; this one emits the "
                     "correct highlighter value bound to a different parameter "
                     "name, so the right instruction is spelled wrong. Pins that "
                     "the spec fixes WHICH name each value is bound to and not "
                     "merely the multiset of values present.",
        "refinement": "its faithful real patch submits the highlighter value under "
                      "a different parameter name. The remote service is then "
                      "never told which highlighter to use, and the F2P reads the "
                      "highlighter parameter by name out of the encoded body, so "
                      "that assertion FAILS — it does NOT resolve. Note a "
                      "value-only substring check would still have found the token "
                      "elsewhere in the body, which is why the key obligation is "
                      "worth its own rival.",
        "witness": _WIT_LEXER_KEY,
    },
    {
        "id": "weak-count-extra-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_COUNT_EXTRA,
        "rationale": "REJECT from the COUNT obligation of the list equality, from "
                     "the TOO-MANY direction: all three required pairs are emitted "
                     "correctly and in order, then a fourth is appended. Every "
                     "clause the other rivals defend is satisfied, so the "
                     "rejection is attributable solely to 'these three pairs are "
                     "the ENTIRE mapping'. No nagini counterpart — its carrier "
                     "splits the mapping across separate field functions, so no "
                     "single postcondition there pins the count.",
        "refinement": "its faithful real patch submits one extra named parameter "
                      "alongside the three the fix assembles. The postcondition "
                      "pins the mapping to exactly three entries, so the model "
                      "would no longer mirror the assembled mapping: an extra "
                      "parameter is an unrequested instruction to the remote "
                      "service, and the modeled behavior must not admit it.",
        "witness": _WIT_COUNT_EXTRA,
    },
    {
        "id": "weak-count-missing-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_COUNT_MISSING,
        "rationale": "REJECT from the COUNT obligation, from the TOO-FEW "
                     "direction: the retention pair is omitted from the mapping "
                     "entirely. Near-miss to weak-expiry-wrong-const, which sends "
                     "that parameter with a WRONG value — this one leaves it off, "
                     "pinning that the spec forbids a parameter being left FREE "
                     "and not merely mis-valued.",
        "refinement": "its faithful real patch omits the retention parameter from "
                      "the submitted mapping. The F2P reads the retention entry out "
                      "of the encoded request body and asserts it is present with "
                      "the one-week value; with the pair dropped that entry is "
                      "absent from the body, so the assertion FAILS — it does NOT "
                      "resolve.",
        "witness": _WIT_COUNT_MISSING,
    },
    {
        "id": "weak-code-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CODE_DROP,
        "rationale": "REJECT from the ('code', contents) pair: dropping the leading "
                     "element makes result[0] = ('code', contents.drop 1) ≠ "
                     "('code', contents) on every non-empty input. Attacks the input "
                     "binder `contents`.",
        "refinement": "its faithful real patch forwards the captured output minus its "
                      "leading byte into the code field. The encoded request body's "
                      "code entry is then missing its leading character, so the F2P "
                      "assertion that the full contents appear verbatim FAILS — it "
                      "does NOT resolve.",
        "witness": _WIT_CODE_DROP,
    },
    {
        "id": "weak-code-input-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CODE_CONST,
        "rationale": "REJECT from the ('code', contents) pair, from the "
                     "input-INDEPENDENT direction: the code value never depends on "
                     "`contents`, so result[0] ≠ ('code', contents) for every "
                     "non-empty input. Near-miss to weak-code-drop-first, refuted at "
                     "a DISTINCT input to demonstrate the result's failure to track "
                     "the binder.",
        "refinement": "its faithful real patch posts a fixed code value ignoring the "
                      "captured session output. The encoded request body's code entry "
                      "is then not the uploaded contents at all, so the F2P assertion "
                      "that the full contents appear verbatim FAILS — it does NOT "
                      "resolve.",
        "witness": _WIT_CODE_CONST,
    },
    {
        "id": "weak-expiry-wrong-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EXPIRY,
        "rationale": "REJECT from the ('expiry','1week') pair: the rival emits a "
                     "different retention constant. Ports nagini weak-expiry-wrong-"
                     "const.",
        "refinement": "its faithful real patch sets a different retention window. "
                      "The F2P reads the retention entry out of the encoded request "
                      "body and asserts the one-week value appears there, so a "
                      "changed window makes that assertion FAIL — it does NOT "
                      "resolve. (The retention entry is not the one the fix changes, "
                      "but it IS pinned by the F2P, so this is a load-bearing "
                      "reject and not merely hunk fidelity.)",
        "witness": _WIT_EXPIRY,
    },
    {
        "id": "weak-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ORDER,
        "rationale": "REJECT from the ORDERING obligation of the list-equality "
                     "postcondition: the rival emits the correct three pairs but in "
                     "the wrong order, so the list equality fails. No nagini "
                     "counterpart (its carrier is an unordered dict); attacks a "
                     "structural clause transparent on the list carrier.",
        "refinement": "its faithful real patch assembles the same three parameters "
                      "in a different order, producing a differently-ordered encoded "
                      "request body. The postcondition pins the exact ordering the "
                      "fix assembles, so the model would no longer mirror the "
                      "assembled mapping. Stated honestly: the F2P reads each "
                      "parameter out of the body independently, so a reordering "
                      "alone would still satisfy it — this rival is refuted by the "
                      "ORDER clause of the modeled postcondition, which is stricter "
                      "than the test. It is carried because the spec pins order and "
                      "an unattacked clause is an untested clause, not because a "
                      "reordering would break the F2P.",
        "witness": _WIT_ORDER,
    },
]

"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8035 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region (which the consumer spec view elides) is changed, and the
single ``theorem correct_keepPrivateMember`` survives with a byte-identical
STATEMENT — so ``markers.same_spec`` holds by construction and any rejection is
attributable to the postcondition rather than to a tampered spec.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. ONE obligation, ``correct_keepPrivateMember``, over the
per-member keep/drop decision

    keepPrivateMember (privateMembers : PrivateMembersOption) (memberName : String)
                      (hasDoc undocMembers dropAsInherited : Bool) -> Bool

with NO precondition (the ``correct_*`` binder is a bare ``∀`` over every input
tuple, so the domain is total). The postcondition is a SINGLE master equality:

  (M) result = (if hasDoc || undocMembers then
                  match privateMembers with
                  | .disabled  => false
                  | .all       => true
                  | .names ns  => if dropAsInherited then false
                                                     else ns.contains memberName
                else false)

(M) is grounded ENTIRELY in the five inputs — no ``opaque`` callee, no
``axiom``, every term a concrete ``def`` over ``DecidableEq`` carriers — so it is
fully computable and a refutation is a plain ``decide`` at a literal input. It
carries five INDEPENDENT pieces of content, and the battery attacks each:

  * the documentable GATE ``hasDoc || undocMembers``, which is a *conjunct* on
    the ``.names`` arm and on the ``.all`` arm but must NOT gate the ``.disabled``
    arm (which is ``false`` either way) — and which reads BOTH of its disjuncts;
  * the three-way dispatch on ``privateMembers``, pinned separately at
    ``.disabled`` (drop), ``.all`` (keep) and ``.names`` (name-selective);
  * the name selectivity itself — the load-bearing content of the modeled
    behaviour: with an explicit selection the member is kept exactly when its OWN
    identifier occurs in that selection, NOT whenever a selection is present;
  * the inherited-member carve-out, which applies ONLY on the ``.names`` arm
    (``.all`` keeps such a member; this asymmetry is its own defended clause);
  * that ``memberName`` is actually consulted against ``ns`` rather than
    replaced by some coarser property of ``ns``.

CARRIER NOTE (why every witness is a bare ``decide`` at literals). ``(M)`` is a
decidable proposition over ``PrivateMembersOption``/``String``/``Bool``, all
``DecidableEq``, so each witness states the negation of the spec predicate
directly at a concrete five-tuple:

    example : ¬ problem_spec_keepPrivateMember (…) (…) … (implementation_… …) := by
      unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
      decide

No binder is needed and therefore no hypothesis can be inconsistent: the
"conditioning on the carrier" technique is not reached for here because nothing
in this spec is opaque. Verified for all nine rivals: the rival MODULE fails to
build, the witness build against the rival exits 0, and the same witness against
the frozen solution exits ≠ 0 — and the gold-side failure is in every case
`decide` REPORTING the proposition false (it reduced and refuted the negation),
never a stuck reduction, an unknown identifier or a parse error, so each is a
real discriminator and not a tautology. No banned token (``sorry`` / ``admit`` / ``native_decide`` / a new
``axiom`` / ``opaque``) appears in any variant or witness, no helper lemma is
added, and every ``expect="verify"`` case reproves the byte-identical obligation
(the three SOUNDNESS positives close under the FROZEN tactic body — verified,
exit 0 — so no positive passes by having been neutered; the admissibility case
keeps the frozen impl AND the frozen tactic body, prefixing only `have`s that are
`clear`ed before it runs).

ADVERSARIAL READ of the nagini classes. The sibling battery contracts TWO
functions over Nagini's fractional-permission carrier — a per-member
keep-decision [site A] and a selector-list merge [site B] — and ships 9 spec
cases. Dispositions (full accounting in the footer):

AUDIT RECORD (independent adversarial re-derivation of a recorded SOUND).
Attacks run with real builds; scratch outside the bundle. What was MEASURED:

  * STATEMENT INTEGRITY — the `theorem correct_keepPrivateMember` statement is
    byte-identical to the frozen file in all cases, and everything outside the
    `-- impl-start`/`-- impl-end` region is byte-identical too (except the
    admissibility case, which touches only the proof region and leaves the impl
    frozen). No case reformats or weakens the obligation.
  * WITNESS DISCRIMINATION, RE-DERIVED — all 9 reject cases rebuilt on both
    sides: rival exit 0, gold exit 1, gold's first error `Tactic `decide` proved
    that the proposition ¬(…)` in every case, i.e. the kernel REDUCED the claim
    and refuted it because (M) holds there.
  * FORGERY TEST (B′) — for all 9, a second file differing ONLY in the claim
    (the `¬` dropped, so it asserts (M) HOLDS at the witness point) was built on
    both sides: it builds CLEAN on gold (exit 0) and FAILS on the rival (exit 1,
    same `decide` message). So gold's exit code fully TRACKS the claim in both
    directions — none of these rejections is hollow.
  * RIVAL WRONGNESS (C) — the whole 504-point carrier was enumerated. Every
    rival differs from the frozen decision observably: 264/30/42/42/10/24/21/21/96
    points respectively. None is a mere reshape and none is definitionally equal.
  * SPEC-TOO-WEAK PROBE (D) — five NEW wrong impls the battery does not contain
    (the empty-selection arm reading the inherited observation; the gate read as
    a CONJUNCTION; a PREFIX match instead of identifier equality; the carve-out
    INVERTED; the gate reading only the keep-undocumented input) were all
    REJECTED. No spec hole found.
  * SPEC-TOO-STRONG PROBE (E) — three NEW correct reshapes were proven: the gate
    factored out front as one boolean product; membership via a RECURSIVE
    impl-region helper (bridged to the frozen lookup by an in-proof `have` and
    `List.contains_eq_mem`); and membership stated as the decidable proposition
    `decide (memberName ∈ ns)`. All verify, so the spec pins the VALUE and not one
    spelling of the lookup. No soundness hole.
  * ADMISSIBILITY (defect FOUND and FIXED) — the case formerly recorded as this
    battery's `admissibility` probe was hollow: its impl is observationally
    identical to the frozen decision at all 504 points and it closes under the
    frozen bare-`∀` tactic body, so it never evaluated (M) at any concrete input
    and could not detect the total-carrier analogue of PRECOND-TOO-STRONG. It is
    re-labelled `soundness` (which is what it honestly is) and a real
    admissibility case was landed: see admiss-scenario-shaped-input.
  * DIVERGENCE (F′) — re-measured rather than argued. This backend has no
    `loom.semantics.termination` setting; the frozen impl is a total Lean `def`.
    A diverging rival IS expressible (make the signature `partial def` and loop),
    it passes variant scope, and it is REJECTED — but no witness can be built
    against it: `decide` cannot reduce the `forIn Lean.Loop.mk` term, so the
    witness fails on the RIVAL (the half that must succeed), which is
    `witness-unproven`, not a refutation. So the class yields no ADMISSIBLE
    reject case here. Recorded as a known carrier limit, not as a shippable case.

  * SITE A, value/partial-domain — APPLIES and is the core of this battery. The
    nagini ``boolean-collapse`` rival IS the pre-fix behaviour (collapse the
    three-state selection to a truthy flag) and ports directly. This carrier
    makes the three states EXPLICIT as an inductive and the inherited-member
    observation an explicit input, so the same master equality is additionally
    attackable at each dispatch state, at each disjunct of the gate, and at the
    name lookup itself.
  * SITE A, asymmetry / inherited-member carve-out — PORTS HERE (unlike on the
    velvet sibling, where the observation is not a field of the carrier).
    ``dropAsInherited`` is a first-class binder of (M) and the carve-out is a
    real clause, so the nagini rival re-expresses cleanly with a witness.
  * SITE A, frame-mutation (``write-names``) — VACUOUS. The sibling MANDATES it
    because the name list is held read-only at half permission and an impl that
    WRITES to it must be rejected for insufficient permission. Lean is
    referentially transparent: every input is an immutable value, there is no
    heap and no aliasing, so there is no read-only input to overwrite and no
    substitute probe to build. Not fabricated.
  * SITE B (the selector-list merge) — NOT MODELED here. This bundle carries
    exactly one obligation, the per-member keep-decision (mapping.md); the
    list-merge behaviour is a separate function with no counterpart on this
    carrier. All four site-B cases are legitimately omitted as carrier
    narrowing.
  * DIVERGENCE / non-termination — NO ADMISSIBLE CASE, and the reason is a
    WITNESS limit rather than an expressibility one. AUDIT CORRECTION: the
    earlier claim here was that "a diverging implementation cannot be written at
    all" because ``implementation_*`` is a total Lean ``def``. That was measured
    FALSE — the signature lies inside the impl region, so a variant may make it
    ``partial def`` and loop, and such a variant passes variant scope and IS
    rejected. What it cannot carry is a witness: ``decide`` cannot reduce the
    resulting ``forIn Lean.Loop.mk`` term, so the witness build fails against the
    RIVAL (the half that must succeed) and the case would land
    ``witness-unproven`` — an inconclusive outcome, not a refutation. So the
    class ships no case here; recorded as a known carrier limit. (The known-hole
    disposition of ``the corpus-wide termination-semantics finding`` is specific to velvet bundles
    under ``set_option loom.semantics.termination "partial"``, where a
    non-terminating impl satisfies every ``ensures`` vacuously and the frozen
    spec ADMITS the rival. That is not this backend: here it is rejected.)
  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason the sibling records: (M)
    equates the result to a fully-unfolded expression over the inputs, so there
    is no opaque answer-key an impl could echo.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries two
real-callee soundness probes; that is G-AX's job (axiom_check.py / mapping.md)
and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8035"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single impl-region anchor: the WHOLE frozen decision body. It lies wholly
# between `-- impl-start` and `-- impl-end` (so the spec view, hence same_spec,
# is untouched) and is unique in the file (asserted at load, so the manifest
# breaks loudly if the frozen solution ever changes). Every case below replaces
# exactly this text and nothing else — in particular the `theorem
# correct_keepPrivateMember` statement AND its frozen tactic body are carried
# over verbatim by all three positives.
# ---------------------------------------------------------------------------
_IMPL = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep"""

if _BASE.count(_IMPL) != 1:
    raise AssertionError("impl anchor drifted: frozen decision body not verbatim")

_OPT = "PrivateMembersOption"


def _witness(privateMembers, memberName, hasDoc, undocMembers, dropAsInherited):
    """`¬ problem_spec_… args (implementation_… args)`, decided at literals.

    The spec predicate is applied DIRECTLY (no tester machinery: this backend's
    obligation is a bare predicate), at a five-tuple of literals, and closed by
    `decide` after unfolding both defs. The head binds nothing, so there are no
    hypotheses that could be jointly unsatisfiable — the witness asserts a
    closed decidable falsehood-of-the-spec at one concrete input.
    """
    args = (f"({privateMembers}) {memberName} "
            f"{hasDoc} {undocMembers} {dropAsInherited}")
    return ("example : ¬ problem_spec_keepPrivateMember\n"
            f"    {args}\n"
            "    (implementation_keepPrivateMember\n"
            f"      {args}) := by\n"
            "  unfold problem_spec_keepPrivateMember "
            "implementation_keepPrivateMember\n"
            "  decide\n")


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# The nagini site-A positive re-shapes a FLAT early-return cascade into a
# nested tree. The frozen impl here is already the nested tree staged through a
# mutable local, so the same "structurally different but correct" intent is
# re-expressed by running the reshape in the OTHER direction: flatten to an
# early-return cascade, drop the mutable local entirely, and invert the gate
# into a leading guard. Same observable Bool at every input, so (M) still holds.
# Verified: closes under the FROZEN tactic body, exit 0.
# ===========================================================================
_IMPL_POS_CASCADE = """  if !(hasDoc || undocMembers) then
    return false
  match privateMembers with
  | PrivateMembersOption.disabled => return false
  | PrivateMembersOption.all      => return true
  | PrivateMembersOption.names ns =>
      if dropAsInherited then
        return false
      return ns.contains memberName"""

# ===========================================================================
# (2) POSITIVE CONTROL — a second, further-removed correct shape (verify).
# No imperative scaffolding at all: a single pure `match` whose `.names` arm is
# one boolean conjunction rather than a nested conditional, and whose gate is
# pushed INTO the two arms it actually constrains (`.disabled` needs no gate).
# This is the shape most likely to break a form-tuned tactic script while being
# observationally identical, so it is the sharper SPEC-TOO-STRONG probe.
# Verified: closes under the FROZEN tactic body, exit 0.
# ===========================================================================
_IMPL_POS_EXPR = """  match privateMembers with
  | PrivateMembersOption.disabled => false
  | PrivateMembersOption.all      => hasDoc || undocMembers
  | PrivateMembersOption.names ns =>
      (hasDoc || undocMembers) && !dropAsInherited && ns.contains memberName"""

# ===========================================================================
# (3) SOUNDNESS — an EAGER-lookup correct reshape (verify).
# AUDIT NOTE: this module was previously carried as the battery's
# `kind="admissibility"` case. It is not one: its impl is observationally
# identical to the frozen decision at every input (enumerated over the whole
# 504-point carrier during the audit: 0 differing points) and it closes under
# the FROZEN bare-`∀` tactic body, so it discharges the obligation exactly the
# way the two other positives do and never evaluates (M) at any concrete input.
# That makes it a third SOUNDNESS reshape — a real one, since deciding the name
# lookup EAGERLY (before the gate and before the dispatch, on inputs where the
# frozen shape never evaluates it) is a genuinely different computation order —
# but it cannot detect the total-carrier analogue of PRECOND-TOO-STRONG, which
# is what the admissibility lane exists for. Re-labelled `soundness` and kept;
# the real admissibility case is (4) below.
# Verified: closes under the FROZEN tactic body, exit 0.
# ===========================================================================
_IMPL_EAGER = """  let documentable := hasDoc || undocMembers
  let namedHere : Bool :=
    match privateMembers with
    | PrivateMembersOption.names ns => ns.contains memberName
    | _                             => false
  let mut keep := false
  if documentable then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names _  =>
        if dropAsInherited then
          keep := false
        else
          keep := namedHere
  else
    keep := false
  return keep"""

# ===========================================================================
# (4) ADMISSIBILITY — the obligation discharged AT a concrete scenario-shaped
# input, by evaluation, before the frozen obligation is closed verbatim.
# AUDIT ADDITION. The frozen obligation is a bare `∀` with no hypothesis arrow,
# so there is no precondition that could be too strong — but on a TOTAL carrier
# "there is no precondition" is the wrong test, and it is not what makes this
# lane vacuous. The analogue of PRECOND-TOO-STRONG here is (M) being
# UNSATISFIABLE at exactly the input shape the modeled scenario presents, which
# a case probes DIRECTLY by discharging the post-image at that concrete input by
# evaluation rather than by a bare-`∀` reproof.
#
# The input is the shape the modeled behaviour is pinned at: a one-name explicit
# selection, with a documentable member that IS named in it (must be kept) and a
# second documentable member that is NOT (must be dropped) — the two halves the
# name-selective reading has to separate.
#
# The third `have` is what makes this a probe rather than a restatement: at the
# SAME unnamed-member input it evaluates (M) to FALSE for the keep answer. So the
# two positive halves are real evaluations of the postcondition and not steps
# that would close for any output at all — the obligation is satisfiable AND it
# discriminates there. If any of the three failed, (M) would be unsatisfiable, or
# indifferent, at the one input the modeled behaviour exists for.
#
# Scope: the impl region is the FROZEN impl, UNTOUCHED (this case changes the
# proof region only); the `theorem correct_keepPrivateMember` STATEMENT is
# byte-identical, the frozen tactic body follows the `have`s verbatim, and the
# `have`s are `clear`ed so they cannot participate in it. No new declaration, no
# new axiom, no `sorry`. Verified: exit 0.
# ===========================================================================
_ADM_SEL = 'PrivateMembersOption.names ["m1"]'

_PROOF = """  intro privateMembers memberName hasDoc undocMembers dropAsInherited
  unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
  cases privateMembers <;>
    cases hasDoc <;> cases undocMembers <;> cases dropAsInherited <;>
    rfl"""

if _BASE.count(_PROOF) != 1:
    raise AssertionError("proof anchor drifted: frozen tactic body not verbatim")

_ADM_HAVES = f"""  -- Positive halves: (M) is SATISFIABLE, by evaluation, at exactly the input
  -- shape the modeled scenario presents — a one-name explicit selection with a
  -- documentable member that IS named in it (kept) and a second documentable
  -- member that is NOT (dropped).
  have adm_named : problem_spec_keepPrivateMember
      ({_ADM_SEL}) "m1" true false false
      (implementation_keepPrivateMember
        ({_ADM_SEL}) "m1" true false false) := by
    unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
    decide
  have adm_unnamed : problem_spec_keepPrivateMember
      ({_ADM_SEL}) "m2" true false false
      (implementation_keepPrivateMember
        ({_ADM_SEL}) "m2" true false false) := by
    unfold problem_spec_keepPrivateMember implementation_keepPrivateMember
    decide
  -- Informativeness control: at that SAME unnamed-member input (M) evaluates to
  -- FALSE for the keep answer, so the two halves above are genuine evaluations
  -- rather than steps that would close for any output at all.
  have adm_discriminates : ¬ problem_spec_keepPrivateMember
      ({_ADM_SEL}) "m2" true false false true := by
    unfold problem_spec_keepPrivateMember
    decide
  clear adm_named adm_unnamed adm_discriminates
"""

# ===========================================================================
# UNIQUENESS rivals. Each is a WRONG decision sharing the frozen spec, so each
# must be rejected; each carries a witness verified to hold of the rival and to
# FAIL on the frozen solution.
# ===========================================================================

# (4) THE pre-fix behaviour, ported from the nagini boolean-collapse rival:
# collapse the three-state selection to a presence flag, so every documentable
# member is kept whenever ANY selection is supplied, regardless of name.
_IMPL_COLLAPSE = """  let enabled :=
    match privateMembers with
    | PrivateMembersOption.disabled => false
    | _                             => true
  return enabled && (hasDoc || undocMembers)"""

# (5) The inherited-member carve-out dropped on the `.names` arm (the nagini
# asymmetry rival): a named member is kept even when it is present only as an
# inherited member the run was told to leave out.
_IMPL_NO_CARVEOUT = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns => keep := ns.contains memberName
  else
    keep := false
  return keep"""

# (6) The blanket state mishandled as the empty one: drop every member even when
# the run asks for all of them.
_IMPL_ALL_AS_DISABLED = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := false
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep"""

# (7) The empty state mishandled as the blanket one: keep every documentable
# member when NO selection was supplied at all.
_IMPL_DISABLED_AS_ALL = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := true
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep"""

# (8) The documentable gate dropped from the `.names` arm: a named member is kept
# on the strength of the selection alone, even when it is undocumented and
# undocumented members are not being kept.
_IMPL_DROP_GATE = """  let mut keep := false
  match privateMembers with
  | PrivateMembersOption.disabled => keep := false
  | PrivateMembersOption.all      => keep := hasDoc || undocMembers
  | PrivateMembersOption.names ns =>
      if dropAsInherited then
        keep := false
      else
        keep := ns.contains memberName
  return keep"""

# (9) The gate reads only ONE of its two disjuncts: the keep-undocumented
# setting is ignored, so an undocumented member is dropped even when the run
# asks for undocumented members.
_IMPL_GATE_IGNORES_UNDOC = """  let mut keep := false
  if hasDoc then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep"""

# (10) The carve-out applied on the WRONG arm: the inherited-member test is
# honoured on `.names` (correctly) but ALSO consulted on the blanket arm, so a
# member the run was told to leave out is dropped even when every private member
# is wanted. This attacks the carve-out asymmetry in the direction the
# `.names`-side rival cannot reach: it is wrong only where the spec says the
# carve-out must NOT fire.
_IMPL_CARVEOUT_ON_ALL = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := !dropAsInherited
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.contains memberName
  else
    keep := false
  return keep"""

# (11) An EMPTY explicit selection read as the blanket one: with a selection
# supplied that names nothing, every documentable member is kept. Agrees with the
# frozen decision on every non-empty selection, so only a witness at `ns = []`
# catches it.
_IMPL_EMPTY_MEANS_ALL = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := ns.isEmpty || ns.contains memberName
  else
    keep := false
  return keep"""

# (12) The name lookup replaced by a coarser property of the selection: a
# NON-EMPTY selection keeps every documentable member, so the member's own
# identifier is never consulted. Reaches the `.names` arm correctly (it honours
# the gate and the carve-out) and is wrong only in what it tests there.
_IMPL_IGNORES_NAME = """  let mut keep := false
  if hasDoc || undocMembers then
    match privateMembers with
    | PrivateMembersOption.disabled => keep := false
    | PrivateMembersOption.all      => keep := true
    | PrivateMembersOption.names ns =>
        if dropAsInherited then
          keep := false
        else
          keep := !ns.isEmpty
  else
    keep := false
  return keep"""


SPEC_TESTS = [
    {
        "id": "pos-control-flat-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _IMPL_POS_CASCADE),
        "rationale": "Structurally different but CORRECT: the nested tree staged "
                     "through a mutable local is flattened into an early-return "
                     "cascade — the gate is inverted into a leading guard and the "
                     "local is removed entirely — which is the nagini site-A "
                     "positive's reshape run in the opposite direction. Every "
                     "branch yields the same Bool as the frozen shape at every "
                     "input, so the master equality (M) `result = (if hasDoc || "
                     "undocMembers then <dispatch> else false)` still discharges, "
                     "and the byte-identical obligation closes under the frozen "
                     "tactic body (no new lemma, no weakening). Must verify, else "
                     "SPEC-TOO-STRONG: a faithful correct decision that the spec "
                     "refuses would mean the postcondition over-constrains the "
                     "SHAPE of the computation rather than its value.",
    },
    {
        "id": "pos-control-pure-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _IMPL_POS_EXPR),
        "rationale": "A second, further-removed CORRECT shape: no imperative "
                     "scaffolding at all, the gate pushed into the two dispatch "
                     "arms it actually constrains (the empty-selection arm is "
                     "`false` with or without it), and the explicit-selection arm "
                     "written as one boolean conjunction `(hasDoc || undocMembers) "
                     "&& !dropAsInherited && ns.contains memberName` instead of a "
                     "nested conditional. Boolean-equivalent to (M) at every "
                     "input, so it must verify; this is the sharper "
                     "SPEC-TOO-STRONG probe precisely because it is the shape most "
                     "likely to defeat a form-tuned proof while being "
                     "observationally identical — and the obligation still closes "
                     "under the frozen tactic body.",
    },
    {
        "id": "pos-control-eager-name-lookup",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _IMPL_EAGER),
        "rationale": "A third CORRECT reshape: the name lookup is decided "
                     "EAGERLY, before the gate and before the dispatch, i.e. on "
                     "inputs where the frozen shape never evaluates it, and the "
                     "gate is staged through a named local. Observationally "
                     "identical to (M) at every input (enumerated over the whole "
                     "504-point carrier during the audit: 0 differing points), so "
                     "it must verify; if it did not, (M) would be constraining "
                     "the ORDER in which the inputs are consulted rather than the "
                     "value, which is SPEC-TOO-STRONG. AUDIT RE-LABEL: this case "
                     "was previously carried as the battery's `admissibility` "
                     "case. It is not one — it closes under the frozen bare-∀ "
                     "tactic body and never evaluates (M) at a concrete input, so "
                     "it could not detect the total-carrier analogue of "
                     "PRECOND-TOO-STRONG. Kept as the soundness probe it actually "
                     "is; see admiss-scenario-shaped-input for the real lane.",
    },
    {
        "id": "admiss-scenario-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _ADM_HAVES + _PROOF),
        "rationale": "AUDIT ADDITION — the admissibility lane, landed rather than "
                     "recorded as vacuous. The obligation is a bare ∀ with no "
                     "hypothesis arrow, so no precondition can be too strong; on "
                     "a TOTAL carrier that is NOT what makes the lane vacuous, and "
                     "the analogue of PRECOND-TOO-STRONG is (M) being "
                     "UNSATISFIABLE at exactly the input shape the modeled "
                     "scenario presents. This case probes that directly: it "
                     "discharges (M) BY EVALUATION (`decide`) at a one-name "
                     "explicit selection, for a documentable member that IS named "
                     "in it (kept) and a second that is NOT (dropped), as `have`s "
                     "BEFORE closing the frozen obligation verbatim. A third "
                     "`have` is the informativeness control: at that same "
                     "unnamed-member input (M) evaluates to FALSE for the keep "
                     "answer, so the positive halves are real evaluations rather "
                     "than steps that close for any output. The impl region is the "
                     "FROZEN impl untouched and the `have`s are `clear`ed, so the "
                     "obligation is reproven and not replaced. If any half failed "
                     "=> PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE at the very "
                     "input the modeled behaviour exists for.",
    },

    {
        "id": "uniq-collapse-selection-to-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_COLLAPSE),
        "refinement": "This IS the pre-fix behaviour: the three-state selection is "
                      "read as a mere presence flag, so every documentable member "
                      "is kept whenever a selection is supplied at all. In the "
                      "failing scenario a selection naming ONE member is supplied "
                      "and the test asserts that only that member is documented; "
                      "this decision keeps the OTHER documentable member too, so "
                      "the generated output carries an entry the test forbids. A "
                      "faithful counterpart therefore reproduces exactly the "
                      "regression the change removes and does NOT resolve the "
                      "failing test — so if it verified, that is a genuine "
                      "verify-does-not-imply-resolve break, not an artifact.",
        "rationale": "REJECT from (M) on the `.names` arm: the spec demands "
                     "`ns.contains memberName`, the rival returns `true` for any "
                     "non-empty state. Refuted at (`.names [\"a\"]`, `\"b\"`, "
                     "hasDoc, no-undoc, not-inherited) — a documentable member "
                     "whose identifier is NOT in the supplied selection, where the "
                     "spec says drop and the rival keeps. If it verified => "
                     "SPEC-TOO-WEAK (name selectivity unenforced), which is the "
                     "load-bearing content of the whole obligation.",
        "witness": _witness(f'{_OPT}.names ["a"]', '"b"', "true", "false", "false"),
    },
    {
        "id": "uniq-names-arm-ignores-inherited-carveout",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_NO_CARVEOUT),
        "refinement": "Ports the nagini asymmetry rival. A faithful counterpart "
                      "that dropped the inherited-member carve-out from the "
                      "explicit-selection arm would keep a member that is present "
                      "only because it was inherited from an ancestor the run was "
                      "told to leave out, whenever that member's identifier "
                      "happens to occur in the selection. The change establishes "
                      "that carve-out precisely so the leave-out setting still "
                      "applies in the explicit-selection state; a counterpart "
                      "without it documents members the run excluded, so it "
                      "diverges from the decision the tests pin and does NOT "
                      "resolve.",
        "rationale": "REJECT from (M) via the carve-out clause, which is asymmetric "
                     "— it guards ONLY the `.names` arm, never `.all`. Refuted at "
                     "(`.names [\"b\"]`, `\"b\"`, hasDoc, no-undoc, "
                     "dropAsInherited=TRUE): the spec's `if dropAsInherited then "
                     "false` yields drop, the rival's bare `ns.contains` yields "
                     "keep. Together with uniq-blanket-keeps-inherited (which "
                     "moves the same binder at the `.all` state) this is what "
                     "makes `dropAsInherited` discriminated in BOTH directions "
                     "rather than only where the carve-out fires. If it verified "
                     "=> SPEC-TOO-WEAK (the carve-out unpinned).",
        "witness": _witness(f'{_OPT}.names ["b"]', '"b"', "true", "false", "true"),
    },
    {
        "id": "uniq-blanket-state-drops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_ALL_AS_DISABLED),
        "refinement": "A faithful counterpart that dropped every member in the "
                      "blanket state would document NO private member when the run "
                      "asks for all of them — the long-standing behaviour that "
                      "predates the change and that the passing tests continue to "
                      "assert. It would break the blanket-selection scenario "
                      "outright, so it does NOT resolve (it regresses a test that "
                      "already passes).",
        "rationale": "REJECT from (M) at the `.all` dispatch state, which the spec "
                     "pins to `true` under the gate. Refuted at (`.all`, `\"x\"`, "
                     "hasDoc, no-undoc, not-inherited): the spec keeps, the rival "
                     "drops. Distinct clause and distinct sub-domain from every "
                     "`.names` rival — no membership rival reaches this arm. If it "
                     "verified => SPEC-TOO-WEAK (the blanket state unpinned).",
        "witness": _witness(f'{_OPT}.all', '"x"', "true", "false", "false"),
    },
    {
        "id": "uniq-empty-state-keeps",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_DISABLED_AS_ALL),
        "refinement": "A faithful counterpart that kept every documentable member "
                      "when NO selection was supplied would document private "
                      "members by default — over-disclosure the default must "
                      "prevent, and which the no-selection test asserts against "
                      "(it expects nothing documented for such a member). It does "
                      "NOT resolve; it breaks the no-selection scenario.",
        "rationale": "REJECT from (M) at the `.disabled` dispatch state, pinned to "
                     "`false` unconditionally. Refuted at (`.disabled`, `\"y\"`, "
                     "hasDoc, no-undoc, not-inherited): the spec drops, the rival "
                     "keeps. Completes coverage of the third dispatch state — the "
                     "one the other six rivals all leave correct. If it verified "
                     "=> SPEC-TOO-WEAK (the empty state unpinned).",
        "witness": _witness(f'{_OPT}.disabled', '"y"', "true", "false", "false"),
    },
    {
        "id": "uniq-names-arm-drops-doc-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_DROP_GATE),
        "refinement": "A faithful counterpart that surfaced a named member on the "
                      "strength of the selection ALONE — without also requiring it "
                      "to be documented, or undocumented members to be kept this "
                      "run — would document an undocumented member that every "
                      "scenario in the suite expects to be dropped. The gate is "
                      "not part of what the change alters; a counterpart that "
                      "loses it diverges from the decision the tests pin on both "
                      "sides of the change and does NOT resolve.",
        "rationale": "REJECT from (M) via the documentable gate as a CONJUNCT on "
                     "the `.names` arm: the spec evaluates the dispatch only under "
                     "`hasDoc || undocMembers`, the rival dispatches "
                     "unconditionally. Refuted at (`.names [\"b\"]`, `\"b\"`, "
                     "hasDoc=FALSE, undocMembers=FALSE, not-inherited) — an "
                     "undocumented member that IS named, where the spec drops and "
                     "the rival keeps. Note the member is IN the selection here, "
                     "unlike the collapse rival, so the two are refuted at "
                     "genuinely different points for different reasons. If it "
                     "verified => SPEC-TOO-WEAK (the gate unpinned on the "
                     "explicit-selection arm).",
        "witness": _witness(f'{_OPT}.names ["b"]', '"b"', "false", "false", "false"),
    },
    {
        "id": "uniq-gate-ignores-undoc-setting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_GATE_IGNORES_UNDOC),
        "refinement": "A faithful counterpart whose gate consulted only whether the "
                      "member is documented, ignoring the keep-undocumented "
                      "setting, would drop undocumented members even when the run "
                      "explicitly asks for them — a behaviour orthogonal to the "
                      "change and asserted by the scenarios that already pass. It "
                      "does NOT resolve.",
        "rationale": "REJECT from (M) via the SECOND disjunct of the gate: the spec "
                     "reads `hasDoc || undocMembers`, the rival reads `hasDoc` "
                     "alone. Refuted at (`.all`, `\"z\"`, hasDoc=FALSE, "
                     "undocMembers=TRUE, not-inherited) — one of the two witnesses "
                     "that move `undocMembers` off `false` (the other being "
                     "uniq-names-arm-ignores-membername), and the only one that "
                     "does so at a dispatch state where the gate is the SOLE reason "
                     "the spec keeps. If it verified => SPEC-TOO-WEAK (the gate's "
                     "second disjunct unread, so a rival ignoring that input "
                     "entirely would pass).",
        "witness": _witness(f'{_OPT}.all', '"z"', "false", "true", "false"),
    },
    {
        "id": "uniq-blanket-keeps-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_CARVEOUT_ON_ALL),
        "refinement": "The inherited-member carve-out is ASYMMETRIC: it belongs to "
                      "the explicit-selection state only. A faithful counterpart "
                      "that also consulted it in the blanket state would silently "
                      "drop members that were inherited from an ancestor left out "
                      "of the documentation even though the run asked for every "
                      "private member — narrowing the blanket selection that the "
                      "already-passing blanket scenario asserts documents them. It "
                      "does NOT resolve: it regresses a scenario that passes on "
                      "both sides of the change.",
        "rationale": "REJECT from (M) at the `.all` arm, which the spec pins to "
                     "`true` under the gate with NO reference to dropAsInherited. "
                     "Refuted at (`.all`, `\"x\"`, hasDoc, no-undoc, "
                     "dropAsInherited=TRUE): the spec keeps, the rival drops. This "
                     "is the ONLY rival wrong exactly where the carve-out must NOT "
                     "fire — uniq-names-arm-ignores-inherited-carveout attacks the "
                     "same clause from the opposite side (dropping it where it MUST "
                     "fire), so the two together pin the asymmetry rather than just "
                     "the carve-out's presence. If it verified => SPEC-TOO-WEAK: "
                     "the spec would not distinguish the arm the carve-out guards.",
        "witness": _witness(f'{_OPT}.all', '"x"', "true", "false", "true"),
    },
    {
        "id": "uniq-empty-selection-means-blanket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_EMPTY_MEANS_ALL),
        "refinement": "A faithful counterpart that treated a selection naming "
                      "NOTHING as a request for everything would document every "
                      "private member on a run whose selection is empty — the "
                      "over-disclosure the name-selective reading exists to make "
                      "impossible, and the opposite of what an empty selection "
                      "asks for. It does NOT resolve: it keeps members no "
                      "scenario's selection names.",
        "rationale": "REJECT from (M) on the `.names` arm at the boundary the other "
                     "rivals never reach: `ns.contains memberName` on an EMPTY `ns` "
                     "is `false`, so the spec drops, while the rival's `ns.isEmpty "
                     "|| ...` keeps. Refuted at (`.names []`, `\"a\"`, hasDoc, "
                     "no-undoc, not-inherited). This is the only witness in the "
                     "battery at an empty explicit selection: the rival agrees with "
                     "the frozen decision at EVERY non-empty selection, so no other "
                     "case's witness point can catch it, and it is what pins the "
                     "`names []` sub-domain that separates 'a selection naming "
                     "nothing' from 'no selection' (`.disabled`) and from "
                     "'everything' (`.all`). If it verified => SPEC-TOO-WEAK: an "
                     "empty selection would be unconstrained.",
        "witness": _witness(f'{_OPT}.names []', '"a"', "true", "false", "false"),
    },
    {
        "id": "uniq-names-arm-ignores-membername",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_IGNORES_NAME),
        "refinement": "A NEAR-MISS counterpart: it honours the gate, honours all "
                      "three dispatch states and honours the inherited-member "
                      "carve-out, and is wrong only in testing whether the "
                      "selection is non-empty instead of whether it contains this "
                      "member's own identifier. On the failing scenario — a "
                      "one-name selection — it keeps every documentable member, "
                      "which is the behaviour the change exists to replace, so it "
                      "does NOT resolve. It matters as its own case because it "
                      "isolates the `memberName` input: it agrees with the correct "
                      "decision everywhere the selection is empty or names every "
                      "candidate, so only a witness that varies the member's "
                      "identifier against the selection can catch it.",
        "rationale": "REJECT from (M) at the name lookup itself: the spec tests "
                     "`ns.contains memberName`, the rival tests `!ns.isEmpty` and "
                     "so never consults `memberName`. Refuted at (`.names [\"a\", "
                     "\"c\"]`, `\"q\"`, hasDoc=false, undocMembers=TRUE, "
                     "not-inherited) — a multi-name selection, an identifier "
                     "absent from it, and the gate met through the "
                     "keep-undocumented setting rather than through documentation, "
                     "which is a distinct point from the collapse rival's "
                     "(single-name selection, gate met via hasDoc). If it verified "
                     "=> SPEC-TOO-WEAK: `memberName` would be an input the spec "
                     "does not force any implementation to read.",
        "witness": _witness(f'{_OPT}.names ["a", "c"]', '"q"', "false", "true",
                            "false"),
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING. The sibling ships 9 SPEC cases across TWO
# contracted functions: a per-member keep-decision [site A] and a selector-list
# merge [site B]. This bundle carries exactly ONE obligation — the per-member
# keep-decision — so every site-B case has no counterpart on this carrier.
#
#   nagini case (site)                          -> here
#   -----------------------------------------------------------------------
#   pos-control-A-nested-tree              (A)  -> pos-control-flat-cascade
#                                                                  RE-EXPRESSED
#   admissibility-A-readonly-names         (A)  -> admiss-scenario-shaped-input
#                                                                     RE-AIMED
#                                        (audit: the case that formerly answered
#                                         this row, admiss-eager-name-lookup, was
#                                         a soundness reshape in an admissibility
#                                         slot; it is re-labelled and kept as
#                                         pos-control-eager-name-lookup, and the
#                                         lane is landed properly here)
#   frame-mutation-A-write-names           (A)  -> (none)              VACUOUS
#   partial-domain-A-boolean-collapse      (A)  -> uniq-collapse-selection-to-flag
#                                                                       PORTED
#   asymmetry-A-mode2-ignores-inherited    (A)  -> uniq-names-arm-ignores-
#                                                  inherited-carveout    PORTED
#   pos-control-B-merged-noop-loop         (B)  -> (none)        NOT-MODELED (B)
#   frame-mutation-B-write-members         (B)  -> (none)        NOT-MODELED (B)
#   partial-domain-B-drop-extra-names      (B)  -> (none)        NOT-MODELED (B)
#   partial-domain-B-noop-dropped          (B)  -> (none)        NOT-MODELED (B)
#   (no sibling)                                -> pos-control-pure-expression
#                                                                        ADDED
#   (no sibling)                                -> uniq-blanket-state-drops ADDED
#   (no sibling)                                -> uniq-empty-state-keeps   ADDED
#   (no sibling)                                -> uniq-names-arm-drops-doc-gate
#                                                                        ADDED
#   (no sibling)                                -> uniq-gate-ignores-undoc-setting
#                                                                        ADDED
#   (no sibling)                                -> uniq-names-arm-ignores-
#                                                   membername            ADDED
#   (no sibling)                                -> uniq-blanket-keeps-inherited
#                                                                        ADDED
#   (no sibling)                                -> uniq-empty-selection-means-
#                                                   blanket               ADDED
#
# Result: 13 lean cases (3 soundness, 1 admissibility, 9 uniqueness) against
# nagini's 9 (2 soundness, 1 admissibility, 6 uniqueness). Case-count parity is
# NOT the target and is not what happened: 4 of the sibling's cases are dropped
# as carrier narrowing and 1 as vacuous, and 9 new cases are added because THIS
# carrier exposes structure nagini's flattens (see ADDED). The 13th is the audit's
# added admissibility case; the count moved from 12 because the case that used to
# fill the admissibility slot is now counted as the soundness reshape it is.
#
# RE-EXPRESSED (positive control): the sibling flattens-to-nested; the frozen
#   impl here is ALREADY the nested tree, so the same intent runs the reshape in
#   the opposite direction (flatten to an early-return cascade, drop the mutable
#   local). A second positive with no imperative scaffolding at all was added
#   because on a tactic-proof backend a positive is only informative if it
#   really could have broken the proof, and the pure-expression shape is the one
#   most likely to. Both close under the FROZEN tactic body (verified, exit 0),
#   so neither passes by weakening the obligation.
# RE-AIMED (admissibility): the sibling's probe re-establishes a half-permission
#   + numeric-bound precondition on a scenario-shaped input. This obligation has
#   NO precondition, so that exact probe has no counterpart — but the LANE is not
#   vacuous, and the audit corrected an earlier reading that treated it as such.
#   The analogue of PRECOND-TOO-STRONG on a total carrier is (M) being
#   unsatisfiable at exactly a scenario-shaped input, which
#   admiss-scenario-shaped-input probes by discharging (M) BY EVALUATION at that
#   concrete input (plus an informativeness control that evaluates it to FALSE for
#   the wrong answer at the same point) before closing the frozen obligation
#   verbatim. That is a real probe: it fails if the obligation is unsatisfiable or
#   indifferent there, neither of which a bare-∀ reproof can detect.
# VACUOUS (frame-mutation, site A): the sibling MANDATES a rival that WRITES to
#   the read-only name list, rejected for insufficient permission. Lean is
#   referentially transparent — immutable values, no heap, no aliasing — so
#   there is no read-only input to overwrite and no substitute probe exists. Not
#   fabricated (per the porting map, this class is vacuous on lean). What makes
#   this the VACUOUS disposition rather than a difficulty excuse is that the class
#   cannot produce an `expect="reject"` case here AT ALL, and that is
#   demonstrable, not merely argued: the nearest Lean analogue of the sibling's
#   value-neutral write is a value-neutral REBUILD of the list in the
#   explicit-selection arm (`let ns := ns.map (fun s => s)` before the lookup).
#   It has no permission to lack, so it is observationally identical to the
#   frozen decision at every input and therefore CANNOT carry a discriminating
#   witness — a witness refuting it would have to refute the frozen solution too.
#   Built during this audit for the record: the variant fails only because the
#   frozen `rfl` script no longer closes on the reshaped term (exit 1, `Tactic
#   'rfl' failed`, the `.names` arm goal), which is precisely the tactic-mismatch
#   outcome the witness requirement exists to refuse to count. So the class
#   yields no admissible reject case rather than a hard one.
# PORTED (2): the boolean collapse (the pre-fix behaviour) and the
#   inherited-member asymmetry both have real counterpart clauses in (M) and
#   real discriminating witnesses. Note the asymmetry rival is portable here but
#   NOT on the velvet sibling, where the inherited-member observation is not part
#   of the carrier: on this carrier `dropAsInherited` is a first-class binder.
# NOT-MODELED (all four site-B cases): the selector-list merge is a SEPARATE
#   contracted function in the sibling; this bundle carries one obligation, the
#   per-member keep-decision, so the merge — its positive control, its
#   frame-mutation reject, its drop-extra-names reject and its no-op-dropped
#   reject — has no counterpart. Omitted as carrier narrowing (451/500 lean
#   bundles carry exactly one `theorem correct_*` where the sibling contracts
#   five or more functions); chasing parity would mean fabricating rivals for a
#   behaviour this bundle does not model. This is a known gap, recorded, not an
#   omission for difficulty.
# ADDED (9): this carrier makes explicit what nagini's encodes as a numeric mode
#   plus a fold, so the single master equality is attackable clause by clause:
#     * uniq-blanket-state-drops         — the `.all` dispatch state;
#     * uniq-empty-state-keeps           — the `.disabled` dispatch state;
#     * uniq-names-arm-drops-doc-gate    — the gate as a conjunct on `.names`;
#     * uniq-gate-ignores-undoc-setting  — the gate's SECOND disjunct;
#     * uniq-names-arm-ignores-membername— the name lookup itself (near-miss);
#     * uniq-blanket-keeps-inherited     — the carve-out's ASYMMETRY, attacked
#       where the carve-out must NOT fire (the `.all` arm), which is the half the
#       `.names`-side carve-out rival structurally cannot reach;
#     * uniq-empty-selection-means-blanket — the `ns = []` boundary of the name
#       lookup, the one sub-domain on which every other rival agrees with gold;
#     * pos-control-pure-expression      — a second, sharper correct shape.
#   None is a fabricated wrongness: each is a real regression of a real clause,
#   each with a machine-checked witness that holds of the rival and fails on gold.
#   The 9th ADDED case is the audit's admiss-scenario-shaped-input.
#
# CLAUSE / BINDER COVERAGE. (M) is the single obligation; it is DEFENDED by three
#   soundness positives plus the admissibility case, and ATTACKED by all nine
#   rivals. Every independent piece of content in (M) is attacked by some rival:
#   the gate (drops-doc-gate; gate-ignores-undoc for its second disjunct), each
#   of the three dispatch states (empty-state-keeps / blanket-state-drops /
#   collapse + ignores-membername), the name selectivity (collapse,
#   ignores-membername, empty-selection-means-blanket at its `ns = []` boundary)
#   and the inherited-member carve-out in BOTH directions (ignores-carveout where
#   it must fire, blanket-keeps-inherited where it must not).
#   Every INPUT BINDER is varied by the witnesses rather than held fixed:
#     privateMembers  — `.disabled`, `.all`, `.names []`, `.names ["a"]`,
#                       `.names ["b"]`, `.names ["a","c"]` (all three
#                       constructors, and the explicit list at three lengths
#                       INCLUDING empty);
#     memberName      — "b", "x", "y", "z", "q", both INSIDE the supplied
#                       selection (drops-doc-gate, ignores-carveout) and OUTSIDE
#                       it (collapse, ignores-membername) — the distinction the
#                       whole modeled behaviour turns on;
#     hasDoc          — true (6 witnesses) and false (3);
#     undocMembers    — false (7) and TRUE (gate-ignores-undoc,
#                       ignores-membername);
#     dropAsInherited — false (7) and TRUE (ignores-carveout,
#                       blanket-keeps-inherited — so the binder is moved at the
#                       `.names` state where the carve-out FIRES and at the
#                       `.all` state where it must NOT).
#   The nine witnesses probe NINE DISTINCT input points and no two rivals share a
#   witness. The two rivals that are nearest each other are collapse and
#   ignores-membername: they agree wherever the selection is non-empty, the
#   member is absent from it AND the member is not a dropped inherited one —
#   they part company on `dropAsInherited=true`, where collapse still keeps and
#   ignores-membername honours the carve-out. (Enumerated, not asserted: over the
#   non-empty-selection/member-absent sub-domain the two differ on exactly the
#   dropAsInherited=true points.) They are nonetheless refuted at deliberately
#   different points — differing in selection length, in which disjunct meets the
#   gate, and in `hasDoc` — so neither rationale claims a sub-domain the manifest
#   does not demonstrate.
#
# WITNESS MECHANICS. (M) is fully computable — no `opaque` term, no `axiom`,
#   every carrier `DecidableEq` — so each witness states `¬ problem_spec_… args
#   (implementation_… args)` at a five-tuple of LITERALS and closes by `decide`
#   after unfolding. No witness binds anything, so the gate's
#   inconsistent-hypothesis probe has nothing to find: there are no assumptions
#   to be jointly unsatisfiable. Conditioning on the carrier is not reached for
#   because nothing here is opaque. Verified for all nine: rival module build
#   exits 1, witness-vs-rival exits 0, witness-vs-gold exits 1. The gold-side
#   failure was READ, not just counted: in each case the message is `decide`
#   proved the proposition false, i.e. the kernel reduced the claim and refuted
#   it because the spec HOLDS at that input — never `did not reduce to isTrue or
#   isFalse`, never an unknown constant, never a parse error. A gold-side failure
#   of any of those other shapes would not discriminate, and the exit code alone
#   cannot tell them apart.
#
# DIVERGENCE lane: NO ADMISSIBLE CASE — a WITNESS limit, not an expressibility
#   one. AUDIT CORRECTION, measured with real builds. The earlier text here said
#   `implementation_keepPrivateMember` is a total Lean `def` so "a diverging
#   implementation cannot be written at all". That is false: the signature lives
#   INSIDE the impl region, so a variant may write `partial def` and loop
#   (`while true do ...`). Such a variant passes variant scope (checked: no
#   problems) and IS rejected by the verifier (exit 1, the frozen `rfl` no longer
#   closes) — so the spec does not admit it and there is no spec hole here.
#   What the class cannot supply is a WITNESS: against the diverging rival
#   `decide` cannot reduce the `forIn Lean.Loop.mk` term, so the witness build
#   fails on the RIVAL — the half that must SUCCEED — and the gate would record
#   `witness-unproven`, an inconclusive outcome rather than a refutation. Measured:
#   witness-vs-diverging-rival exit 1 with ``Tactic `decide` failed for
#   proposition ¬(… forIn Lean.Loop.mk …)``. So the class ships nothing here and
#   this is a recorded carrier limit on the WITNESS mechanism, not a claim that the
#   rival is inexpressible and not a hole in the spec.
#   The known-hole disposition of the corpus-wide termination-semantics finding is specific to
#   velvet bundles under `loom.semantics.termination "partial"`, where the frozen
#   spec ADMITS a non-terminating rival that satisfies every `ensures` vacuously
#   while its faithful counterpart hangs the failing test; that is a different
#   backend, not this one (here the diverging rival is rejected).
#
# AXIOM_TESTS: dropped. The sibling's two real-callee soundness probes are
#   G-AX's job (axiom_check.py / mapping.md); the G-PBT gate ignores AXIOM_TESTS.
AXIOM_TESTS = []

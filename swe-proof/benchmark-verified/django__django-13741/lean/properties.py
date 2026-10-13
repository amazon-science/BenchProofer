"""properties.py — PBT falsification manifest for django__django-13741 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY the implementation region
(and, for the positive controls, the proof body), so `variant_scope.same_spec`
holds by construction and each rejection is attributable to the postcondition
rather than to a tampered spec. No case introduces an `axiom`, a helper
`theorem`/`lemma`, `sorry`/`admit`, or `native_decide`, and every
`theorem correct_passwordHashField` STATEMENT is re-emitted byte-identically.

DEFENDED SURFACE
----------------
One modeled function, one obligation:

    implementation_passwordHashField
        (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome

pinned by a two-conjunct postcondition, each conjunct independently attackable:

    result.disabled = disabledArg.getD true                          -- (C1)
    result.changed  = (if result.disabled then false                  -- (C2)
                       else !(valEq initial data))

(C1) is the CONFIGURATION clause: the effective non-editability setting is the
caller's value when one was supplied and the default `true` when none was. It
has two independently-wrong directions — the wrong default on the absent-setting
sub-domain, and failing to honour a supplied setting — and it is the clause the
FAIL_TO_PASS observable reads directly.

(C2) is the DECISION clause, itself two sub-domains joined by the branch on
`result.disabled`: a non-editable field never reports a change, and an editable
one reports a change exactly when the two values differ under `valEq`, which
treats a missing value as the empty string. A rival can be correct on either
sub-domain and wrong on the other, so both are attacked separately, and the
missing-vs-empty boundary inside `valEq` is attacked on its own.

The carrier is FULLY TRANSPARENT — `FieldOutcome` derives `DecidableEq`,
`valEq` is a concrete `String` comparison, and there is no `opaque` callee or
axiom anywhere in the spec. So every rival is refutable by `decide` at concrete
literal inputs and NO witness needs to condition on the carrier; consequently no
witness binds a hypothesis, and there is nothing that could be inconsistent.

Coverage of the surface this bundle models: the single obligation is defended by
3 soundness + 1 admissibility `expect="verify"` cases and attacked by 6
`expect="reject"` cases; all three of the gate's directions (SPEC-TOO-WEAK,
SPEC-TOO-STRONG, PRECOND-TOO-STRONG) are therefore exercised; both
top-level conjuncts and all three sub-domains are attacked; and each of the
three input binders is VARIED across the reject witnesses —
`disabledArg` ∈ {`none`, `some true`, `some false`}, `initial` ∈ {`none`, three
distinct strings}, `data` ∈ {`none`, `some ""`, distinct strings} — over six
DISTINCT input points, so no rival's refutation borrows another's.

PORTING NOTES (which nagini cases port, which are omitted and why)
------------------------------------------------------------------
The nagini sibling contracts TWO functions (`make_field`, `differs`) over a
`Field` structure plus a `PSeq` fold; this bundle models the construction and
the change decision as ONE input→output relation, so several nagini cases
collapse onto the same conjunct here and the permission-based ones have no
counterpart at all. Case-count parity is not the target; clause and binder
coverage is.

  * `mf-pos-control-ternary` -> `pos-branchless-record` — the same argument (a
    structurally different but behaviourally identical impl must verify, else
    the spec is SPEC-TOO-STRONG), re-expressed as a branchless functional record
    literal with no `Id.run do`/`let mut`. Proof re-closed with `exact ⟨rfl, rfl⟩`.
  * `df-pos-control-reorder` -> `pos-branch-reorder` — nagini's branch-reorder
    positive, carried over verbatim in argument: the editable branch is tested
    first and the non-editable case falls through. Proof re-closed by
    case-splitting the configuration and simplifying the inverted guard.
  * `mf-disabled-default-false` -> `default-not-disabled` — the pre-patch
    behaviour on the absent-setting sub-domain; attacks (C1)'s default.
  * `mf-required-default-true` is OMITTED: the second boolean carrier nagini
    contracted (the other constructor default) is NOT modeled here — this
    bundle's `FieldOutcome` carries only the non-editability setting and the
    change decision, so there is no binder for that rival to abuse and any
    substitute would be fabricated. This is carrier narrowing, not a dropped
    proof.
  * `mf-ignore-explicit-disabled` -> `override-explicit-setting` — attacks the
    OTHER direction of (C1): honouring an explicitly supplied setting rather
    than overwriting it.
  * added `flag-not-recorded` — a NEAR-MISS with no nagini counterpart, and the
    reason the two conjuncts are separable at all: it decides the change
    correctly (so (C2) reads as gold does) but reports the wrong effective
    setting in the outcome. Without it a rival that got the decision right and
    the recorded configuration wrong would satisfy every other witness's input
    point. It is refuted at its OWN point (two equal values, no setting
    supplied), where the decision agrees with gold and only (C1) separates them.
  * `df-drop-short-circuit` -> `no-short-circuit` — the partial-domain attack on
    the non-editable sub-domain of (C2).
  * `df-always-false` -> `never-reports-change` — the mirror partial-domain
    attack on the editable sub-domain of (C2); this is the deleted-override
    behaviour the fix replaces with a configuration-driven decision.
  * `df-none-not-empty` -> `missing-not-empty` — the missing-vs-empty boundary
    inside `valEq`, re-expressed as raw `Option` equality instead of nagini's
    fold. The ONLY rival whose witness sets `initial := none`.
  * `df-frame-mutate-disabled` and `df-frame-mutate-data` are OMITTED as
    VACUOUS: they are fractional-permission probes (a write to an input held at
    half permission). Lean is referentially transparent — the impl is a pure
    total function of its arguments and there is no aliased input to write — so
    this class cannot be expressed here. No substitute is fabricated. Note the
    frame obligation itself is NOT unmet: both components of the outcome are
    pinned by (C1)+(C2), so nothing is left free for a rival to fill.
  * `mf-admiss-caller` and `df-admiss-self-call` -> `admiss-ground-default`.
    An earlier pass dropped BOTH as vacuous on the ground that the lean
    obligation is `∀ disabledArg initial data, problem_spec …` with no
    precondition hypothesis, so there is no precondition to be too strong.
    That reason is wrong, and the lane is now carried. "No precondition" is not
    the same as "nothing to establish": on a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, which a `∀`-statement can be while still being provable
    only vacuously. The positive below discharges the obligation at that
    concrete input BY EVALUATION, as a `have`, before closing the frozen
    obligation verbatim — so it attests that the modeled behaviour really does
    produce the headline outcome there, rather than that the quantifier ranges
    over a domain nothing was ever computed on. Measured load-bearing: the same
    two `have`s FAIL against the `default-not-disabled` rival impl (the
    `_observable` evaluation is refuted, `decide` proving the equation false),
    so the case is not a restatement of the obligation.
  * The divergence/non-termination class does not arise: the nagini sibling
    carries no `diverge-*` / `nonterm-*` / `weak-diverge` case, and on lean the
    class is genuinely vacuous in any event — `implementation_passwordHashField`
    is a total Lean `def`, so a diverging implementation cannot be written.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores
    it. (The nagini sibling had none either — both deep legs are A-reference.)
  * No soundness positive was dropped for a proof that would not close; all
    four `expect="verify"` cases below build.
  * added `pos-symmetric-compare` (no nagini counterpart): a correct reshape that
    is NOT definitionally equal to the frozen impl, so it is the only positive
    whose obligation does not close by reduction. See its rationale.

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligation
removed. Each was built BOTH ways with scripts/lean_verify.sh and SEEN to
discriminate — rival exit 0, frozen solution exit 1.
"""
from pathlib import Path

INSTANCE = "django__django-13741"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    matched and is unique, so silent drift (Solution.lean edited) fails loudly
    at import time rather than producing a quietly meaningless variant."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. `_GOLD_BODY` lies ENTIRELY inside the impl region (it starts
# after the `def` header's `:=`) and is unique in the file; each variant swaps
# it wholesale, so no edit can stray into the spec view.
# ---------------------------------------------------------------------------

_GOLD_BODY = """Id.run do
  -- The effective disabled setting: the caller's value, or the default when
  -- the caller supplied none.
  let disabled := disabledArg.getD true
  let mut changed := false
  -- A disabled field is never editable, so it never reports a change.
  if disabled then
    return { disabled := disabled, changed := false }
  -- Otherwise compare the initial value against the submission (missing ↦ "").
  if !(valEq initial data) then
    changed := true
  return { disabled := disabled, changed := changed }"""

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers. The
    `theorem correct_passwordHashField` STATEMENT is re-emitted byte-identically
    inside `new_proof_body` (see `_THM_STMT`); only the tactic body changes,
    which `variant_scope` permits and which a reshaped impl requires."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# The frozen obligation, byte-identical. Asserted against _BASE so a change to
# the theorem statement upstream breaks this manifest loudly.
_THM_STMT = """theorem correct_passwordHashField :
    ∀ (disabledArg : Option Bool) (initial data : Option String),
      problem_spec_passwordHashField disabledArg initial data
        (implementation_passwordHashField disabledArg initial data) := by"""
if _BASE.count(_THM_STMT) != 1:
    raise AssertionError("drift: theorem correct_passwordHashField statement")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-branchless-record) A branchless functional impl: no `Id.run do`, no
# `let mut`, no early return — the outcome is a single record literal whose
# `changed` component is the spec's own conditional. Behaviourally identical.
_POS_BRANCHLESS = _swap_proof(
    _swap(
        _BASE,
        _GOLD_BODY,
        "let disabled := disabledArg.getD true\n"
        "  { disabled := disabled,\n"
        "    changed := if disabled then false else !(valEq initial data) }",
    ),
    _THM_STMT + "\n"
    "  intro disabledArg initial data\n"
    "  exact ⟨rfl, rfl⟩\n",
)

# (pos-branch-reorder) The imperative shape kept, but the two branches tested in
# the INVERTED order: the editable case is handled first and returns the
# comparison directly, with the non-editable case falling through to the
# never-changed outcome. Semantically identical; different source and a
# different guard polarity.
_POS_REORDER = _swap_proof(
    _swap(
        _BASE,
        _GOLD_BODY,
        "Id.run do\n"
        "  let disabled := disabledArg.getD true\n"
        "  -- The editable case first: a change is reported exactly when the\n"
        "  -- initial and submitted values differ (missing ↦ \"\").\n"
        "  if !disabled then\n"
        "    return { disabled := disabled, changed := !(valEq initial data) }\n"
        "  -- Otherwise the field is not editable, so it never reports a change.\n"
        "  return { disabled := disabled, changed := false }",
    ),
    _THM_STMT + "\n"
    "  intro disabledArg initial data\n"
    "  unfold problem_spec_passwordHashField implementation_passwordHashField\n"
    "  simp only [Id.run]\n"
    "  by_cases h : disabledArg.getD true\n"
    "  · simp only [h, Bool.not_true, if_false, if_true]; exact ⟨rfl, rfl⟩\n"
    "  · simp only [h, Bool.not_false, if_true, Bool.false_eq_true, if_false]\n"
    "    exact ⟨rfl, rfl⟩\n",
)


# (pos-symmetric-compare) A third correct impl whose equivalence to the frozen
# one is NOT definitional. The two positives above are both `rfl`-closable: their
# `changed` component reduces to the spec's own conditional, so they exercise the
# spec's tolerance of a different SOURCE shape but not of a different
# COMPUTATION. This one compares the two values in the opposite order. Equality
# of the normalised values is symmetric, so it is behaviourally identical, but
# the obligation no longer closes by reduction — it needs `eq_comm`. That makes
# it the only positive that would catch a spec accidentally pinned to one
# operand order rather than to the equality relation.
_POS_SYMMETRIC = _swap_proof(
    _swap(
        _BASE,
        _GOLD_BODY,
        "let disabled := disabledArg.getD true\n"
        "  { disabled := disabled,\n"
        "    changed := if disabled then false else !(valEq data initial) }",
    ),
    _THM_STMT + "\n"
    "  intro disabledArg initial data\n"
    "  unfold problem_spec_passwordHashField implementation_passwordHashField\n"
    "  refine ⟨rfl, ?_⟩\n"
    "  by_cases h : disabledArg.getD true <;>\n"
    "    simp only [h, if_true, if_false, Bool.false_eq_true, valEq] <;>\n"
    "    simp [eq_comm]\n",
)


# ===========================================================================
# ADMISSIBILITY (precond-too-strong probe) — expect "verify"
# ===========================================================================

# (admiss-ground-default) The frozen obligation is a bare `∀` with no
# precondition hypothesis, so there is no guard to relax. The analogue on this
# total carrier is whether the obligation is SATISFIABLE at a normal,
# headline-shaped input rather than only in the abstract — a `∀` can be provable
# while nothing was ever computed at the input that matters. This case pins that
# down: the impl and the frozen tactic body are untouched, and two `have`s are
# PREPENDED to the existing proof body.
#
#   `_observable` EVALUATES the modeled behaviour at the headline input (no
#   setting supplied, two differing values) down to a concrete outcome, so the
#   admission is tied to the actual values produced there;
#   `_ground` then discharges the spec predicate at that same input by rewriting
#   with `_observable` and `decide`.
#
# Both are load-bearing rather than decorative: built against the
# `default-not-disabled` rival impl, `_observable`'s `decide` proves the
# equation FALSE (exit 1), so these lines distinguish the frozen behaviour from
# a wrong one. Stating `_ground` directly as `by decide` does NOT work — the
# spec predicate is a `Prop` conjunction with no `Decidable` instance
# (`failed to synthesize Decidable (problem_spec_passwordHashField …)`), which
# is why it goes through the evaluated `_observable` rewrite.
_ADMISS_GROUND = _swap_proof(
    _BASE,
    _THM_STMT + "\n"
    "  have _observable : implementation_passwordHashField none (some \"aaa\") (some \"bbb\")\n"
    "      = { disabled := true, changed := false } := by decide\n"
    "  have _ground : problem_spec_passwordHashField none (some \"aaa\") (some \"bbb\")\n"
    "      (implementation_passwordHashField none (some \"aaa\") (some \"bbb\")) := by\n"
    "    unfold problem_spec_passwordHashField\n"
    "    rw [_observable]\n"
    "    decide\n"
    "  intro disabledArg initial data\n"
    "  unfold problem_spec_passwordHashField implementation_passwordHashField\n"
    "  simp only [Id.run]\n"
    "  by_cases h : disabledArg.getD true\n"
    "  · simp only [h, if_true]; exact ⟨rfl, rfl⟩\n"
    "  · simp only [h, Bool.false_eq_true, if_false]\n"
    "    by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩\n",
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (default-not-disabled) When no setting is supplied, fall back to the plain
# base default instead of the required one. Correct whenever a setting IS
# supplied; wrong on the entire absent-setting sub-domain — which is exactly the
# sub-domain the F2P observable reads.
_RIVAL_DEFAULT = _swap(
    _BASE, _GOLD_BODY,
    "Id.run do\n"
    "  let disabled := disabledArg.getD false\n"
    "  let mut changed := false\n"
    "  if disabled then\n"
    "    return { disabled := disabled, changed := false }\n"
    "  if !(valEq initial data) then\n"
    "    changed := true\n"
    "  return { disabled := disabled, changed := changed }",
)

# (flag-not-recorded) NEAR-MISS: decides the change from the correctly-defaulted
# setting (so the decision component agrees with gold everywhere) but RECORDS
# the un-defaulted setting in the outcome. Attacks (C1) alone, at a point where
# (C2) cannot distinguish it.
_RIVAL_NOTRECORDED = _swap(
    _BASE, _GOLD_BODY,
    "Id.run do\n"
    "  let effective := disabledArg.getD true\n"
    "  let reported := disabledArg.getD false\n"
    "  let mut changed := false\n"
    "  if effective then\n"
    "    return { disabled := reported, changed := false }\n"
    "  if !(valEq initial data) then\n"
    "    changed := true\n"
    "  return { disabled := reported, changed := changed }",
)

# (override-explicit-setting) Force the non-editable setting unconditionally,
# discarding a caller-supplied one. Correct on the absent-setting sub-domain and
# on a supplied `true`; wrong whenever the caller supplied `false`.
_RIVAL_OVERRIDE = _swap(
    _BASE, _GOLD_BODY,
    "Id.run do\n"
    "  let disabled := true\n"
    "  let mut changed := false\n"
    "  if disabled then\n"
    "    return { disabled := disabled, changed := false }\n"
    "  if !(valEq initial data) then\n"
    "    changed := true\n"
    "  return { disabled := disabled, changed := changed }",
)

# (no-short-circuit) Record the setting correctly but always compare the values,
# dropping the guarantee that a non-editable field never reports a change.
# Correct on every editable field; wrong on the non-editable sub-domain.
_RIVAL_NOGUARD = _swap(
    _BASE, _GOLD_BODY,
    "Id.run do\n"
    "  let disabled := disabledArg.getD true\n"
    "  let mut changed := false\n"
    "  if !(valEq initial data) then\n"
    "    changed := true\n"
    "  return { disabled := disabled, changed := changed }",
)

# (never-reports-change) The mirror partial-domain attack: never report a change,
# whatever the setting. Correct on every non-editable field; wrong on the
# editable sub-domain, where the decision must follow the two values rather than
# a constant.
_RIVAL_CONSTFALSE = _swap(
    _BASE, _GOLD_BODY,
    "Id.run do\n"
    "  let disabled := disabledArg.getD true\n"
    "  return { disabled := disabled, changed := false }",
)

# (missing-not-empty) Compare the two optional values RAW instead of treating a
# missing value as the empty string. Correct whenever both values are present or
# both absent; wrong exactly on the missing-vs-empty boundary.
_RIVAL_RAWEQ = _swap(
    _BASE, _GOLD_BODY,
    "Id.run do\n"
    "  let disabled := disabledArg.getD true\n"
    "  let mut changed := false\n"
    "  if disabled then\n"
    "    return { disabled := disabled, changed := false }\n"
    "  if !(initial == data) then\n"
    "    changed := true\n"
    "  return { disabled := disabled, changed := changed }",
)


# --- witnesses -------------------------------------------------------------
# Each negates the spec predicate at ONE concrete input, in a file where the
# frozen obligation has been removed (so no tactic script can interfere). The
# carrier is fully transparent (`FieldOutcome` derives `DecidableEq`, `valEq` is
# a concrete String comparison, no `opaque`/`axiom` in the spec), so `decide`
# closes and NO witness binds a hypothesis — there is nothing to be
# inconsistent. All six were built both ways: rival exit 0, gold exit 1.

def _wit(disabled_arg: str, initial: str, data: str) -> str:
    args = f"{disabled_arg} {initial} {data}"
    return (
        "example : ¬ problem_spec_passwordHashField\n"
        f"    {args}\n"
        f"    (implementation_passwordHashField {args}) := by\n"
        "  unfold problem_spec_passwordHashField implementation_passwordHashField\n"
        "  decide"
    )


# No setting supplied, two differing values. Gold: the default applies, so the
# field is non-editable and reports no change. Rival: the plain fallback leaves
# it editable, so it both records the wrong setting AND reports a change.
_WIT_DEFAULT = _wit("none", '(some "aaa")', '(some "bbb")')

# No setting supplied, two EQUAL values — the point at which the decision
# component is `false` for gold and rival alike, so only the recorded setting
# separates them. Gold records the default; the rival records the un-defaulted
# value. Varies `initial`/`data` to an equal-pair the other witnesses never use.
_WIT_NOTRECORDED = _wit("none", '(some "s")', '(some "s")')

# An editable setting explicitly supplied, with a present initial value and an
# ABSENT submission (so the values differ under the missing↦empty rule). Gold
# honours the supplied setting and reports a change; the rival overrides it to
# non-editable and reports none. Varies `data := none`.
_WIT_OVERRIDE = _wit("(some false)", '(some "h")', "none")

# A non-editable setting explicitly supplied, with two differing values — the
# only witness that sets `disabledArg := some true`. Gold short-circuits to no
# change; the rival compares anyway and reports one.
_WIT_NOGUARD = _wit("(some true)", '(some "aaa")', '(some "bbb")')

# An editable setting supplied, with two differing values. Gold reports a
# change; the rival's constant reports none.
_WIT_CONSTFALSE = _wit("(some false)", '(some "aaa")', '(some "bbb")')

# The missing-vs-empty boundary on an editable field: an ABSENT initial value
# against an EMPTY submitted one. The only witness that sets `initial := none`
# and the only one that uses the empty string. Gold treats them as equal and
# reports no change; the rival's raw comparison reports one.
_WIT_RAWEQ = _wit("(some false)", "none", '(some "")')


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {"id": "pos-branchless-record", "kind": "soundness", "expect": "verify",
     "module": _POS_BRANCHLESS,
     "rationale": "A structurally different but behaviourally identical impl: a "
                  "branchless functional record literal (no imperative do-block, no "
                  "mutable accumulator, no early return) in place of the frozen "
                  "imperative shape. Must verify — both conjuncts hold definitionally, "
                  "so the obligation re-closes with `exact ⟨rfl, rfl⟩` (statement "
                  "re-emitted byte-identically; only the tactic body changes). If it "
                  "failed, the spec would be over-fit to the imperative shape rather "
                  "than to the input→output relation => SPEC-TOO-STRONG. Ports "
                  "nagini's `mf-pos-control-ternary` argument."},
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "A second correct impl with the two branches INVERTED: the editable "
                  "case is tested first (on the negated guard) and returns the "
                  "comparison directly, with the non-editable case falling through. "
                  "Semantically identical; the postcondition is agnostic to branch "
                  "order. Proof re-closed by case-splitting the configuration and "
                  "simplifying the inverted guard polarity. If it failed, the spec "
                  "would be over-fit to one branch order => SPEC-TOO-STRONG. Ports "
                  "nagini's `df-pos-control-reorder`."},
    {"id": "pos-symmetric-compare", "kind": "soundness", "expect": "verify",
     "module": _POS_SYMMETRIC,
     "rationale": "A correct impl that is NOT definitionally equal to the frozen one: "
                  "it compares the two normalised values in the opposite operand order. "
                  "The other two positives both close by `exact ⟨rfl, rfl⟩` — their "
                  "`changed` component reduces to the spec's own conditional — so they "
                  "test tolerance of a different SOURCE shape but not of a different "
                  "COMPUTATION that agrees only up to a semantic law. Here the "
                  "obligation cannot close by reduction and needs `eq_comm`, which is "
                  "what makes it the positive that would catch a spec pinned to one "
                  "operand order instead of to the equality relation. Must verify: "
                  "equality of the normalised values is symmetric, so the impl is "
                  "behaviourally identical at every input. If it failed, the spec would "
                  "constrain the comparison's direction, which the modeled behaviour "
                  "does not => SPEC-TOO-STRONG. No nagini counterpart (added by audit)."},

    # ---------------- admissibility (must VERIFY) ----------------
    {"id": "admiss-ground-default", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_GROUND,
     "rationale": "PRECOND-TOO-STRONG probe. The frozen obligation carries NO "
                  "precondition hypothesis, so there is no guard to relax; on a total "
                  "carrier the honest analogue is whether the obligation is "
                  "SATISFIABLE at a normal, headline-shaped input rather than only in "
                  "the abstract — a bare `∀` can be provable while nothing was ever "
                  "computed at the input that matters. So the modeled behaviour is "
                  "EVALUATED at the headline input (no setting supplied, two differing "
                  "values) down to a concrete outcome as `_observable`, and the spec "
                  "predicate is then discharged at that same input as `_ground` by "
                  "rewriting with it, BEFORE the frozen obligation is closed verbatim. "
                  "Must verify; if it failed, the modeled behaviour would be "
                  "unsatisfiable at exactly a normal input => PRECOND-TOO-STRONG. "
                  "Nothing is assumed: no new declaration, no axiom/lemma/sorry, "
                  "statement re-emitted byte-identically, impl untouched, and the two "
                  "`have`s sit inside the existing tactic body. They are load-bearing "
                  "rather than decorative — built against the `default-not-disabled` "
                  "rival impl, `_observable`'s `decide` proves the equation FALSE, so "
                  "these lines separate the frozen behaviour from a wrong one instead "
                  "of restating the obligation. (`_ground` cannot be stated as a bare "
                  "`by decide`: the spec predicate is a `Prop` conjunction with no "
                  "`Decidable` instance, hence the evaluated rewrite.) Ports nagini's "
                  "`mf-admiss-caller` / `df-admiss-self-call`, which an earlier pass "
                  "dropped on the mistaken ground that no precondition means nothing "
                  "to establish."},

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {"id": "default-not-disabled", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DEFAULT, "witness": _WIT_DEFAULT,
     "refinement": "This is the pre-patch behaviour. Its faithful real patch supplies "
                   "only the long-standing constructor default and never establishes "
                   "the non-editability default, so a field built with no setting "
                   "supplied stays editable. The FAIL_TO_PASS test asserts precisely "
                   "that a default-constructed field IS non-editable, so that tree "
                   "fails it and does NOT resolve — a verifying rival here would be a "
                   "true verify-does-not-imply-resolve break.",
     "rationale": "Attacks (C1) `result.disabled = disabledArg.getD true` on the "
                  "absent-setting sub-domain: the fallback must be the non-editable "
                  "default, not the plain base one. Correct whenever a setting IS "
                  "supplied, so this is a partial-domain rival. Witness at "
                  "`disabledArg := none` with two differing values: gold records "
                  "non-editable and reports no change, the rival records editable and "
                  "reports a change. Built both ways (rival exit 0, gold exit 1). "
                  "Ports nagini's `mf-disabled-default-false`."},
    {"id": "flag-not-recorded", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOTRECORDED, "witness": _WIT_NOTRECORDED,
     "refinement": "Its faithful real patch leaves the constructor recording the "
                   "un-defaulted setting on the field while making the change decision "
                   "behave as though the default had been applied — i.e. it keeps a "
                   "bespoke override that suppresses the change instead of configuring "
                   "the field. The FAIL_TO_PASS test reads the field's recorded "
                   "setting DIRECTLY (not just the change decision), so that tree fails "
                   "it and does NOT resolve. This is the rival the F2P's added "
                   "assertion exists to catch.",
     "rationale": "NEAR-MISS isolating (C1) from (C2): the change decision is computed "
                  "from the correctly-defaulted setting, so the `changed` component "
                  "agrees with gold at EVERY input; only the recorded `disabled` "
                  "component is wrong. Given its own input point for that reason — "
                  "`disabledArg := none` with two EQUAL values, where both impls report "
                  "no change and (C1) is the sole discriminator, so the rationale's "
                  "sub-domain claim is the one the witness actually demonstrates. No "
                  "nagini counterpart: nagini's two carriers were separate functions, "
                  "whereas here the configuration and the decision share one outcome "
                  "and could be independently corrupted. Built both ways (rival exit 0, "
                  "gold exit 1)."},
    {"id": "override-explicit-setting", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVERRIDE, "witness": _WIT_OVERRIDE,
     "refinement": "Its faithful real patch OVERWRITES a caller-supplied setting "
                   "instead of only filling in an absent one. A caller that explicitly "
                   "asks for an editable field silently gets a non-editable one — a "
                   "divergence the fill-in-if-absent semantics never causes, and one "
                   "that breaks the caller-override contract the issue and the "
                   "PASS_TO_PASS form tests rely on. It does not faithfully resolve.",
     "rationale": "Attacks the OTHER direction of (C1): `disabledArg.getD true` must "
                  "return the supplied value when one is present, so an explicit "
                  "setting has to survive. Correct on the absent-setting sub-domain and "
                  "on a supplied non-editable value; wrong only when the caller "
                  "supplied the editable one. Witness at `disabledArg := some false` "
                  "with a present initial value and an ABSENT submission (varying the "
                  "`data := none` binder): gold honours the setting and reports a "
                  "change, the rival forces non-editable and reports none. Built both "
                  "ways (rival exit 0, gold exit 1). Ports nagini's "
                  "`mf-ignore-explicit-disabled`."},
    {"id": "no-short-circuit", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOGUARD, "witness": _WIT_NOGUARD,
     "refinement": "Its faithful real patch drops the guard that makes a non-editable "
                   "field ignore submitted data, so such a field reports a change "
                   "whenever the submitted value differs from the stored one. The "
                   "FAIL_TO_PASS test asserts no change is reported for exactly that "
                   "field with two differing values, so it does NOT resolve.",
     "rationale": "Partial-domain attack on the non-editable sub-domain of (C2) "
                  "(`if result.disabled then false`): records the setting correctly but "
                  "always compares, so on a non-editable field with differing values it "
                  "returns a change where the clause demands `false`. Correct on every "
                  "editable field. Witness at `disabledArg := some true` — the only "
                  "witness that supplies the non-editable setting explicitly, so this "
                  "sub-domain is probed with the setting SUPPLIED rather than defaulted "
                  "and the rejection cannot be confused with a default-handling bug. "
                  "Built both ways (rival exit 0, gold exit 1). Ports nagini's "
                  "`df-drop-short-circuit`."},
    {"id": "never-reports-change", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONSTFALSE, "witness": _WIT_CONSTFALSE,
     "refinement": "Its faithful real patch keeps the bespoke override that reports no "
                   "change unconditionally, instead of letting the decision follow the "
                   "field's configuration. As the GENERAL decision that is unsound — an "
                   "editable field with differing values must report a change, and the "
                   "PASS_TO_PASS form tests submit data to editable fields and expect "
                   "change detection. Relying on the configuration rather than a "
                   "constant is the whole content of the fix, so this does not resolve.",
     "rationale": "Partial-domain attack on the editable sub-domain of (C2) "
                  "(`else !(valEq initial data)`), and the exact mirror of "
                  "`no-short-circuit`: correct on every non-editable field, wrong "
                  "whenever an editable field's values differ. Witness at "
                  "`disabledArg := some false` with two differing values: gold reports "
                  "a change, the rival's constant reports none. Distinct from "
                  "`no-short-circuit`'s point (opposite setting) because the two rivals "
                  "fail on opposite sub-domains. Built both ways (rival exit 0, gold "
                  "exit 1). Ports nagini's `df-always-false`."},
    {"id": "missing-not-empty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RAWEQ, "witness": _WIT_RAWEQ,
     "refinement": "Its faithful real patch omits the normalisation that treats a "
                   "missing value on either side as the empty string, so an editable "
                   "field whose stored value is absent and whose submission is empty is "
                   "reported as changed. That is the spurious-change case the framework "
                   "decision guards against and which the PASS_TO_PASS "
                   "render-with-absent-value tests rely on, so it does not faithfully "
                   "resolve.",
     "rationale": "Partial-domain attack on the missing-vs-empty boundary INSIDE the "
                  "editable branch of (C2): `valEq` maps a missing value and the empty "
                  "string to the same value, so they must compare EQUAL, whereas raw "
                  "optional equality distinguishes them. Correct whenever both values "
                  "are present or both absent. Witness at `initial := none`, "
                  "`data := some \"\"` — the only witness that sets `initial` absent and "
                  "the only one using the empty string, so this is the sole rival "
                  "varying that binder; without it a rival mishandling only the "
                  "absent-value boundary would satisfy every other witness's input "
                  "point. Built both ways (rival exit 0, gold exit 1). Ports nagini's "
                  "`df-none-not-empty`."},
]

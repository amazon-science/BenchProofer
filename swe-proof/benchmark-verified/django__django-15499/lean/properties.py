"""properties.py — PBT falsification manifest for django__django-15499 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY the implementation region
(and, for the positive controls, the proof body), so `variant_scope.same_spec`
holds by construction, every `theorem correct_*` statement survives byte
identically, and each rejection is attributable to the postcondition rather than
to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function decides the outcome of pairing a model-creation step with a
following step that reconfigures managers:

    implementation_optimizeCreateThenAlterManagers
        (model : ModelState) (targetName : String)
        (newManagers : List (String × String)) : List ModelState

`ModelState` records the five components the optimization reads or rewrites:
`name`, `fields`, `options`, `bases`, `managers`. The postcondition has TWO
independent top-level conjuncts, both stated over a FULLY TRANSPARENT carrier
(`sameModel` is `String.toLower` equality; the collapsed step is a structure
update) — there is no `opaque` callee anywhere, so every rival is refutable at a
concrete literal input and no witness needs to condition on the carrier:

  * (COLLAPSE) `sameModel model.name targetName = true → result =
    [{ model with managers := newManagers }]`. This single clause pins FIVE
    independent facts at once, because the structure-update frame fixes four
    components while substituting one:
      - the result is a ONE-element list (the pair really does collapse),
      - `managers` is the RECONFIGURED list `newManagers` — the newly-added
        behavior this instance is about,
      - `name` is the creation step's own identifier, NOT the lower-cased
        comparison key the guard uses,
      - `fields`, `options`, `bases` are carried over UNCHANGED from the
        creation step (the following step supplies none of them).
  * (NO-COLLAPSE) `sameModel model.name targetName = false → result = []`. When
    the following step names a DIFFERENT model the two steps are independent and
    no collapsed step is produced.

Frame discipline: nagini expressed "the creation step is read-only" as fractional
permission (`Acc(model.X, 1/2)`). Lean is referentially transparent, so there is
no permission class to port — but the frame obligation itself is NOT vacuous
here, because it is discharged STRUCTURALLY by the `{ model with … }` payload:
the four carried-over components are OBSERVABLE parts of the result, so a rival
that substitutes any of them is refuted by the COLLAPSE equality itself. That is
what `uniq-clobbers-options`, `uniq-clobbers-fields` and `uniq-clobbers-bases`
attack, and it is why the class is subsumed rather than fabricated.

PORTING NOTES (which nagini cases ported, which were omitted and why)
---------------------------------------------------------------------
The nagini sibling models a WIDER surface: its `reduce_create` carries an
`op_kind` tag ranging over TWO follow-up step kinds (an options reconfiguration
and a manager reconfiguration) plus explicit `op_options`/`op_managers`
arguments, and states an IFF pinning exactly when a collapse happens. This
bundle models only the manager-reconfiguration pairing — the pairing is fixed at
the TYPE level, there is no kind tag and no options argument — so every nagini
case attached to the kind dispatch or to the options-reconfiguration arm has no
counterpart at all. Case-count narrowing here is carrier narrowing, not thinner
coverage.

Ported:
  * `uniq-prepatch-no-manager-fold` + `uniq-skip-all` -> ONE case,
    `uniq-never-collapse`. On nagini these are distinct impls (drop one of two
    fold branches vs. drop both). Here the modeled pairing IS the manager one,
    so "omit the manager arm" and "never collapse anything" are literally the
    same implementation (`return []`) — shipping both would be the same rival
    twice under two ids, and its witness would be the same input for the same
    reason.
  * `uniq-ignore-name` -> `uniq-ignore-model-identity` — collapses regardless of
    which model the following step names, attacking (NO-COLLAPSE).
  * `uniq-fold-installs-lower-name` -> `uniq-collapse-lowers-identifier` — the
    previously-admitted P1 break, re-expressed: the collapsed step takes the
    lower-cased comparison key as its identifier instead of the creation step's
    own. Nagini needed name and name_lower as two DISTINCT integer tokens to
    catch this; here `String.toLower` is modeled deeply, so the witness exhibits
    a real mixed-case identifier and the discrimination is computed, not
    postulated.
  * `uniq-mgr-carries-model-managers` -> `uniq-carries-original-managers` — the
    load-bearing clause: collapses but keeps the creation step's own managers.
  * `uniq-mgr-clobbers-options` -> `uniq-clobbers-options`.
  * `uniq-mgr-clobbers-fields` -> `uniq-clobbers-fields`.
  * `pos-control-reorder` / `pos-control-name-first` -> `pos-functional-form` /
    `pos-inverted-guard`. Nagini's two positives both reshape the dispatch over
    its two follow-up kinds, which does not exist here; the ARGUMENT they carry
    (a structurally different but behaviorally identical impl must still verify,
    else SPEC-TOO-STRONG) is preserved with the two reshapes this carrier admits
    — dropping the imperative do-block entirely, and negating the guard with the
    branches swapped. Both proofs re-closed honestly inside the proof region with
    the obligation statement re-emitted byte-identically.

Added (not in nagini, needed for clause coverage here):
  * `uniq-clobbers-bases` — nagini names (BASES) load-bearing but ships no rival
    attacking the bases component alone. On this carrier `bases` is a distinct
    pinned component of the COLLAPSE payload, so it gets its own rival; without
    it a variant mishandling only that component would verify unnoticed.
  * `uniq-exact-identifier-guard` — added by AUDIT. Both nagini and the original
    port attack the guard in one direction only: nagini's `uniq-ignore-name` and
    this bundle's `uniq-ignore-model-identity` DROP it, and every other rival
    keeps it verbatim. Nothing probed it in the STRENGTHENING direction, where the
    case-folding is lost but the comparison remains. That direction is only
    expressible here — nagini compared two integer key tokens, so "exact vs
    case-insensitive" had no counterpart on its carrier, whereas this bundle
    models `String.toLower` deeply. Without it a variant that compared the two
    identifiers exactly would have verified unnoticed on all seven previous
    witnesses, since each already spells its two identifiers alike modulo the
    case gold folds away.

  * `uniq-concatenates-managers` — added by AUDIT. The managers component was
    attacked only by total substitution (`uniq-carries-original-managers`), so
    nothing probed the weaker mis-selection where the reconfigured managers are
    PRESENT but not ALONE. The spec pins that component by EQUALITY, and this
    rival is what distinguishes an equality from a containment.

Ported (recovered by AUDIT, previously recorded as an omission):
  * `admiss-f2p-self-call` -> `admiss-ground-f2p-input`. The port dropped this
    lane on the ground that the frozen obligation has no precondition hypothesis
    to over-constrain. That is not a demonstration of vacuity: on a total carrier
    the analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
    an F2P-shaped input, and a positive that discharges the spec predicate at
    that concrete input BY EVALUATION — as a `have`, before closing the frozen
    obligation verbatim — tests it directly. It was landed and it verifies, so
    the lane was expressible here all along.

Omitted:
  * `frame-mutate-managers`, `frame-mutate-options` — the fractional-permission
    class. Nagini-specific; Lean is referentially transparent, so no impl can
    write a caller's value and there is no INSUFFICIENT PERMISSION rejection to
    reproduce. Not replaced by a fabricated substitute — the read-only intent is
    covered structurally by the three clobber rivals above.
  * `uniq-opt-carries-alter-managers` — attacks the OPTIONS-reconfiguration arm
    (its (OPT-FOLD) clause). That arm is pre-existing behavior this bundle does
    not model at all: there is no kind tag to select it and no `op_options`
    binder to mis-place, so the rival cannot even be written here. Carrier
    narrowing.
  * `uniq-mgr-clobbers-options` overlapped nagini's OPTIONS/MANAGERS symmetry;
    only the manager-arm half is portable, and that is the half shipped.
  * Divergence / non-termination lane — the nagini sibling carries NO
    `diverge-*` / `nonterm-*` / `weak-diverge` case, so there was nothing to
    port. Independently, the class is genuinely vacuous on this backend:
    `implementation_optimizeCreateThenAlterManagers` is a total Lean `def`, so a
    non-terminating implementation cannot be expressed. (This is the lean
    disposition; it is NOT the velvet `partial`-semantics spec hole recorded in
    the corpus-wide termination-semantics finding, which does not apply to a total `def`.)
  * `AXIOM_TESTS` — dropped; the axiom lane is G-AX's job and this gate ignores
    it. (This bundle declares no axiom and no `opaque` callee in any case.)

No soundness positive was dropped for want of a proof.

WITNESSES
---------
Every reject case carries a `witness` negating the spec predicate at ONE
concrete literal input, checked in a file with the frozen obligation removed. All
nine were built BOTH ways with scripts/lean_verify.sh: exit 0 against the rival
(the rival provably contradicts the spec there) and exit 1 against the frozen
solution (a real discriminator, not a tautology). No witness binds a hypothesis
— the carrier computes, so there is nothing that could be inconsistent.

`String.toLower` does not reduce under `decide` or `rfl`; `simp [String.toLower,
String.map_eq]` closes it, which is what every witness below uses. (Measured:
`decide` fails on `sameModel "Foo" "foo" = true` because its `Decidable` instance
does not reduce, and `rfl` reports the two sides are not definitionally equal.)

Every gold-side refutation is additionally required to be SEMANTIC rather than a
tactic stall, and the difference is visible in the residual: gold's build must
fail leaving `⊢ False`, i.e. the tactic fully COMPUTED both conjuncts, found the
spec satisfied, and was left with the impossible goal the negation demands. A
witness whose gold-side residual is an unreduced term has not refuted anything —
the exit code would be 1 whether the claim were true or false. The audit check
that separates the two is to assert the POSITIVE claim about gold at the same
input with the same tactic: it must SUCCEED (exit 0), proving the tactic is
capable at that point, so the negation's failure is attributable to the spec
holding there and not to the tactic giving up. All nine witnesses pass that
control, and the control is stronger than that: the FLIPPED claim (same input,
same tactic, the `¬` dropped) elaborates against the frozen solution at exit 0
and FAILS against the rival at exit 1, for every one of the nine. Gold's exit
code therefore tracks what the witness CLAIMS and not merely what it mentions,
which is what makes the `⊢ False` residual admissible evidence rather than a
coincidence of shape. `bind` is in the simp set because without it the do-block's
join point survives on the guard-FALSE branch and the residual is
`⊢ ¬(do PUnit.unit; []) = []` — a stall, not a refutation.

All three input binders are varied across the nine witnesses, at NINE distinct
input points (AUDIT: this previously read "eight distinct input points" and was
false — `uniq-never-collapse` and `uniq-exact-identifier-guard` shipped the
byte-identical witness, so the eight witnesses stood at only seven points. The
never-collapse witness now sits at its own point with the two identifiers spelled
alike, which also makes it a cleaner attribution: that rival has nothing to do
with case-folding). Both top-level conjuncts are attacked, the guard is attacked
in both directions (dropped, and strengthened to exact equality), and the
managers component is attacked both by total substitution and by concatenation.
"""
from pathlib import Path

INSTANCE = "django__django-15499"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence; assert it matched so silent drift (the
    frozen Solution.lean edited under us) fails loudly instead of shipping a
    variant that no longer says what its rationale claims."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Each lies ENTIRELY inside the impl region and is unique in
# the whole file (the proof region mentions the same identifiers but never these
# exact `return` lines).
# ---------------------------------------------------------------------------

_IMPL_HEAD = (
    "def implementation_optimizeCreateThenAlterManagers\n"
    "    (model : ModelState) (targetName : String)\n"
    "    (newManagers : List (String × String)) : List ModelState := Id.run do\n"
)

# The whole frozen impl body.
_IMPL_BODY = (
    "  if sameModel model.name targetName then\n"
    "    return [{ model with managers := newManagers }]\n"
    "  return []"
)

# The collapse return alone — the line every clobber rival rewrites.
_COLLAPSE = "    return [{ model with managers := newManagers }]"

assert _BASE.count(_IMPL_HEAD + _IMPL_BODY) == 1
assert _BASE.count(_COLLAPSE) == 1

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers. The
    `theorem correct_*` STATEMENT is re-emitted byte-identically inside
    `new_proof_body`; only the tactic body changes, which variant_scope permits
    (and which a reshaped impl genuinely requires)."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# The obligation statement, re-emitted verbatim by each positive control.
_THM = (
    "theorem correct_optimizeCreateThenAlterManagers :\n"
    "    ∀ (model : ModelState) (targetName : String)\n"
    "      (newManagers : List (String × String)),\n"
    "      problem_spec_optimizeCreateThenAlterManagers model targetName newManagers\n"
    "        (implementation_optimizeCreateThenAlterManagers model targetName newManagers) := by"
)
assert _BASE.count(_THM) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify".
# Structurally different but behaviorally IDENTICAL impls. If one of these
# cannot verify, the spec is over-fit to the frozen impl's shape rather than to
# its behavior => SPEC-TOO-STRONG.
# ===========================================================================

# (pos-functional-form) Drop the imperative do-block entirely: a pure functional
# `if … then … else …` expression. Same decision on every input; the proof
# re-closes by case-splitting the guard and `simp`.
_POS_FUNCTIONAL = _swap_proof(
    _swap(
        _BASE, _IMPL_HEAD + _IMPL_BODY,
        "def implementation_optimizeCreateThenAlterManagers\n"
        "    (model : ModelState) (targetName : String)\n"
        "    (newManagers : List (String × String)) : List ModelState :=\n"
        "  if sameModel model.name targetName then "
        "[{ model with managers := newManagers }] else []",
    ),
    _THM + "\n"
    "  intro model targetName newManagers\n"
    "  unfold problem_spec_optimizeCreateThenAlterManagers\n"
    "    implementation_optimizeCreateThenAlterManagers\n"
    "  by_cases h : sameModel model.name targetName = true\n"
    "  · simp [h]\n"
    "  · simp only [Bool.not_eq_true] at h\n"
    "    simp [h]\n",
)

# (pos-inverted-guard) Keep the do-block but NEGATE the guard and swap the two
# arms: return the empty result early when the models differ, otherwise fall
# through to the collapsed step. Same decision table, opposite branch order.
_POS_INVERTED = _swap_proof(
    _swap(
        _BASE, _IMPL_BODY,
        "  if !sameModel model.name targetName then\n"
        "    return []\n"
        "  return [{ model with managers := newManagers }]",
    ),
    _THM + "\n"
    "  intro model targetName newManagers\n"
    "  unfold problem_spec_optimizeCreateThenAlterManagers\n"
    "    implementation_optimizeCreateThenAlterManagers\n"
    "  by_cases h : sameModel model.name targetName = true\n"
    "  · simp [Id.run, h]\n"
    "    rfl\n"
    "  · simp only [Bool.not_eq_true] at h\n"
    "    simp [Id.run, h]\n"
    "    rfl\n",
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject".
# Each shares the spec exactly and changes only the impl region.
# ===========================================================================

# (uniq-never-collapse) Never produce a collapsed step. This is the pre-patch
# behavior for the modeled pairing, and — on this carrier — also nagini's
# "remove both fold branches" rival, since the manager pairing is the only one
# modeled here.
_RIVAL_NEVER = _swap(_BASE, _IMPL_BODY, "  return []")

# (uniq-ignore-model-identity) Collapse UNCONDITIONALLY, dropping the
# same-model guard entirely.
_RIVAL_IGNORE_ID = _swap(
    _BASE, _IMPL_BODY, "  return [{ model with managers := newManagers }]")

# (uniq-collapse-lowers-identifier) Collapse correctly slot-for-slot EXCEPT the
# collapsed step takes the lower-cased comparison key as its identifier instead
# of the creation step's own identifier.
_RIVAL_LOWER_ID = _swap(
    _BASE, _COLLAPSE,
    "    return [{ model with name := targetName.toLower, "
    "managers := newManagers }]")

# (uniq-carries-original-managers) Collapse, but keep the creation step's OWN
# managers rather than the reconfigured ones — the load-bearing clause.
_RIVAL_OLD_MANAGERS = _swap(
    _BASE, _COLLAPSE, "    return [{ model with managers := model.managers }]")

# (uniq-clobbers-options) Install the reconfigured managers correctly but ALSO
# overwrite the options component with the same reconfigured list.
_RIVAL_CLOB_OPTS = _swap(
    _BASE, _COLLAPSE,
    "    return [{ model with options := newManagers, "
    "managers := newManagers }]")

# (uniq-clobbers-fields) Install the reconfigured managers correctly but ALSO
# overwrite the fields component with the same reconfigured list.
_RIVAL_CLOB_FIELDS = _swap(
    _BASE, _COLLAPSE,
    "    return [{ model with fields := newManagers, "
    "managers := newManagers }]")

# (uniq-clobbers-bases) Install the reconfigured managers correctly but ALSO
# replace the bases component with a synthesized value.
_RIVAL_CLOB_BASES = _swap(
    _BASE, _COLLAPSE,
    "    return [{ model with bases := [model.name], "
    "managers := newManagers }]")

# (uniq-concatenates-managers) Added by AUDIT. Collapse correctly slot-for-slot
# EXCEPT the collapsed step's managers are the creation step's own list with the
# reconfigured ones APPENDED, rather than REPLACED by them. Every pre-existing
# rival on the managers component either substitutes a wholly wrong list
# (`uniq-carries-original-managers`) or leaves it right; nothing probed the
# weaker mis-selection that keeps `newManagers` present but not ALONE, which is
# what the spec's equality actually pins.
_RIVAL_APPEND_MANAGERS = _swap(
    _BASE, _COLLAPSE,
    "    return [{ model with managers := model.managers ++ newManagers }]")

# (uniq-exact-identifier-guard) Compare the two identifiers with EXACT string
# equality instead of case-insensitively. Added by audit: every pre-existing
# rival either keeps the guard verbatim or drops it entirely, so the guard's
# case-folding — the `sameModel` half of BOTH conjuncts — was never attacked in
# the strengthening direction. This rival agrees with the frozen impl on all
# seven pre-existing witness inputs where the two identifiers are already
# spelled identically, so it needs its own input to separate.
_RIVAL_EXACT_GUARD = _swap(
    _BASE, _IMPL_BODY,
    "  if model.name = targetName then\n"
    "    return [{ model with managers := newManagers }]\n"
    "  return []")


# ---------------------------------------------------------------------------
# Witnesses. Each negates the spec predicate at one concrete literal input.
# `String.toLower` is stuck under `decide`/`rfl`, so the guard is computed with
# `simp [String.toLower, String.map_eq]`; `Id.run`/`pure` unfold the do-block.
# No witness binds a hypothesis (the carrier computes), so there is nothing that
# could be inconsistent.
# ---------------------------------------------------------------------------

def _wit(model: str, target: str, mgrs: str) -> str:
    return (
        "example : ¬ problem_spec_optimizeCreateThenAlterManagers\n"
        f"    {model}\n"
        f'    "{target}" {mgrs}\n'
        "    (implementation_optimizeCreateThenAlterManagers\n"
        f"      {model}\n"
        f'      "{target}" {mgrs}) := by\n'
        "  unfold problem_spec_optimizeCreateThenAlterManagers\n"
        "    implementation_optimizeCreateThenAlterManagers\n"
        "  simp [Id.run, pure, bind, sameModel, String.toLower, String.map_eq]"
    )


def _model(name: str, fields: str = "[]", options: str = "[]",
           bases: str = "[]", managers: str = "[]") -> str:
    return (f'{{ name := "{name}", fields := {fields}, options := {options}, '
            f"bases := {bases}, managers := {managers} }}")


# Same model, reconfigured managers supplied: the spec demands a one-element
# collapsed step; the rival produces the empty result. The two identifiers are
# spelled IDENTICALLY here so this input point is disjoint from
# `_WIT_EXACT_GUARD`'s (AUDIT: the two witnesses were previously byte-identical,
# which meant the battery's eight witnesses covered only SEVEN input points and
# the never-collapse rival was being refuted at a point whose case-folding is
# irrelevant to it). Also carries a non-empty fields component.
_WIT_NEVER = _wit(
    _model("Alpha", fields='[("id", "AutoField")]'), "Alpha",
    '[("objects", "Mgr")]')

# A DIFFERENT model named: the spec demands the empty result; the rival
# collapses anyway. The only witness on the (NO-COLLAPSE) conjunct.
_WIT_IGNORE_ID = _wit(_model("Foo"), "Other", '[("objects", "Manager")]')

# A mixed-case identifier matched case-insensitively against an all-caps target:
# the collapsed step must keep the creation step's own "Foo", the rival installs
# the lower-cased key "foo". Varies `targetName` to a third distinct casing.
_WIT_LOWER_ID = _wit(_model("Foo"), "FOO", '[("objects", "Manager")]')

# The creation step already carries managers and the following step supplies
# DIFFERENT ones: gold installs the reconfigured pair, the rival keeps the
# original. The only witness where the two manager lists both matter and differ.
_WIT_OLD_MANAGERS = _wit(
    _model("Bar", managers='[("objects", "M0")]'), "bar",
    '[("things", "M1")]')

# The creation step carries a non-empty options component: gold carries it over,
# the rival replaces it with the reconfigured manager list.
_WIT_CLOB_OPTS = _wit(
    _model("Baz", options='[("db_table", "t")]'), "baz",
    '[("objects", "Manager")]')

# The creation step carries a non-empty fields component: gold carries it over,
# the rival replaces it.
_WIT_CLOB_FIELDS = _wit(
    _model("Qux", fields='[("id", "AutoField")]'), "qux",
    '[("objects", "Manager")]')

# The creation step carries a non-empty bases component: gold carries it over,
# the rival synthesizes a different one.
_WIT_CLOB_BASES = _wit(
    _model("Quux", bases='["Base"]'), "quux", '[("objects", "Manager")]')

# The two identifiers name the SAME model but are spelled with different casing:
# gold matches them case-insensitively and collapses, the exact-equality rival
# sees two distinct strings and produces the empty result. The only witness where
# the two identifiers differ AS STRINGS yet still denote the same model — the
# input that separates a case-folding guard from an exact one.
_WIT_EXACT_GUARD = _wit(_model("Foo"), "foo", '[("objects", "Manager")]')

# The creation step already carries managers and the following step supplies a
# DIFFERENT one: gold's collapsed step carries EXACTLY the reconfigured list,
# while the rival carries the concatenation, which contains it but is not equal
# to it. Identifiers spelled with different casing (`Beta`/`BETA`), so the point
# is distinct from every other witness's.
_WIT_APPEND_MANAGERS = _wit(
    _model("Beta", managers='[("objects", "M0")]'), "BETA",
    '[("things", "M1")]')


# ---------------------------------------------------------------------------
# ADMISSIBILITY (attack F). The frozen obligation carries no precondition
# hypothesis, so the analogue on this total carrier is whether the obligation is
# SATISFIABLE at an F2P-shaped input rather than whether a guard admits one. A
# spec whose two conjuncts were jointly unsatisfiable at the very input the
# instance is about would still be provable-looking in the ∀-form only if no
# ground instance were ever discharged; discharging one BY EVALUATION, as a
# `have`, before closing the frozen obligation verbatim, tests that directly.
# The ground point is the F2P shape: a mixed-case creation step identifier
# matched case-insensitively against the following step's lower-cased target,
# with a two-manager reconfiguration supplied.
# ---------------------------------------------------------------------------
_ADM_MODEL = _model("Foo")
_ADM_MGRS = '[("objects", "Manager"), ("things", "Manager")]'
_ADM_GROUND = (
    "  have _ground : problem_spec_optimizeCreateThenAlterManagers\n"
    f"      {_ADM_MODEL}\n"
    f'      "foo" {_ADM_MGRS}\n'
    "      (implementation_optimizeCreateThenAlterManagers\n"
    f"        {_ADM_MODEL}\n"
    f'        "foo" {_ADM_MGRS}) := by\n'
    "    unfold problem_spec_optimizeCreateThenAlterManagers\n"
    "      implementation_optimizeCreateThenAlterManagers\n"
    "    simp [Id.run, pure, bind, sameModel, String.toLower, String.map_eq]\n")

# The frozen tactic body, verbatim, appended after the ground `have`.
_FROZEN_TACTICS = _BASE[
    _BASE.index(_THM) + len(_THM) + 1: _BASE.index(_PROOF_TAIL)].rstrip("\n")

_ADMISS = _swap_proof(_BASE, _THM + "\n" + _ADM_GROUND + _FROZEN_TACTICS + "\n")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-functional-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNCTIONAL,
        "rationale": "a structurally-different but behaviorally IDENTICAL impl: the "
                     "imperative do-block is dropped for a pure functional "
                     "if/then/else expression. Every input produces the same result, "
                     "so both conjuncts of the postcondition still hold; the "
                     "obligation is re-closed honestly inside the proof region "
                     "(guard case-split + simp) with the `theorem "
                     "correct_optimizeCreateThenAlterManagers` statement re-emitted "
                     "byte-identically. Carries nagini's pos-control argument: if a "
                     "faithful correct impl in a different shape cannot verify, the "
                     "spec is over-fit to the frozen impl's syntax rather than to its "
                     "behavior => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inverted-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INVERTED,
        "rationale": "a second correct impl with the guard NEGATED and the two arms "
                     "swapped: return the empty result early when the two steps name "
                     "different models, otherwise fall through to the collapsed step. "
                     "Same decision table, opposite branch order — the counterpart of "
                     "nagini's branch-reorder positive on a carrier with a single "
                     "branch pair. Proof re-closed by the same case-split plus a "
                     "`rfl` to discharge the do-block's join point. Must verify or "
                     "the spec is sensitive to branch order => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must VERIFY; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-ground-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "added by AUDIT; the port dropped this lane as vacuous on the "
                     "ground that the frozen obligation has no precondition "
                     "hypothesis, which is not a demonstration. On a total carrier the "
                     "analogue of PRECOND-TOO-STRONG is the obligation being "
                     "UNSATISFIABLE at an F2P-shaped input, and this case tests that "
                     "directly: it prepends a `have` that discharges "
                     "`problem_spec_optimizeCreateThenAlterManagers` BY EVALUATION at "
                     "the concrete point model.name=\"Foo\", targetName=\"foo\", "
                     "newManagers=[(\"objects\",\"Manager\"),(\"things\",\"Manager\")] "
                     "— the mixed-case identifier matched case-insensitively against "
                     "the following step's lower-cased target, with a two-manager "
                     "reconfiguration supplied — and only then closes the frozen "
                     "obligation with its tactic body re-emitted verbatim. Nothing is "
                     "assumed: no new declaration, no new axiom, the `theorem "
                     "correct_optimizeCreateThenAlterManagers` statement byte-identical. "
                     "If the two conjuncts could not BOTH be discharged at that ground "
                     "point the spec would be unsatisfiable exactly where the instance "
                     "lives, and the ∀-form's provability would be attesting to nothing "
                     "=> PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "uniq-never-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NEVER,
        "witness": _WIT_NEVER,
        "refinement": "this IS the pre-patch behavior for the modeled pairing: no "
                      "collapse rule exists for a following manager-reconfiguration "
                      "step, so the pair is left as two separate steps. The F2P test "
                      "asserts that a creation step followed by a same-model manager "
                      "reconfiguration optimizes to a SINGLE creation step carrying "
                      "the reconfigured managers; with no collapse the pair stays "
                      "un-collapsed (two operations) and the equality assertion "
                      "fails. It resolves nothing — so a verifying rival here would "
                      "be a true verify-does-not-imply-resolve break. On this carrier "
                      "this single impl covers BOTH nagini rivals in the class "
                      "(omit-the-manager-arm and omit-every-arm), because the manager "
                      "pairing is the only one modeled.",
        "rationale": "attacks the (COLLAPSE) conjunct wholesale: when the two steps "
                     "name the same model the spec demands a one-element result, and "
                     "the rival returns the empty list. Witness at model.name=\"Foo\" "
                     "vs targetName=\"foo\" with a reconfigured manager list — the "
                     "F2P-shaped input. Built both ways (rival exit 0, gold exit 1).",
    },
    {
        "id": "uniq-ignore-model-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_IGNORE_ID,
        "witness": _WIT_IGNORE_ID,
        "refinement": "its faithful real patch omits the same-model check from the "
                      "added collapse rule, so a creation step is fused with a "
                      "manager reconfiguration naming a DIFFERENT model: two "
                      "unrelated models' components are merged and the second "
                      "model's reconfiguration is silently discarded, corrupting the "
                      "migration. Several P2P optimizer tests assert that steps "
                      "touching different models are left independent (and that "
                      "optimization is stable), and would fail — it does NOT resolve.",
        "rationale": "the ONLY rival attacking the (NO-COLLAPSE) conjunct: "
                     "`sameModel model.name targetName = false → result = []`. "
                     "Witness at model.name=\"Foo\" vs targetName=\"Other\" — the "
                     "identifiers differ case-insensitively, so gold produces the "
                     "empty result while the rival collapses. This is also the only "
                     "witness that drives the guard FALSE, so without it the battery "
                     "would say nothing about the spec's second conjunct. Built both "
                     "ways (rival exit 0, gold exit 1).",
    },
    {
        "id": "uniq-collapse-lowers-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LOWER_ID,
        "witness": _WIT_LOWER_ID,
        "refinement": "the previously-admitted P1 break, carried over: the collapsed "
                      "step is built with the lower-cased comparison key as its model "
                      "identifier instead of the creation step's own "
                      "case-preserved identifier. It does collapse the pair and does "
                      "install the reconfigured managers, but renames the model to "
                      "its all-lowercase key. The F2P test compares the optimized "
                      "output against a creation step for the mixed-case model name; "
                      "the serialized comparison fails on the identifier, so it does "
                      "NOT resolve. Nagini caught this only after splitting display "
                      "name and comparison key into two distinct tokens; here the "
                      "case-folding is modeled deeply, so the discrimination is "
                      "computed rather than postulated.",
        "rationale": "attacks the IDENTIFIER component of the (COLLAPSE) payload: the "
                     "structure update `{ model with managers := newManagers }` pins "
                     "`name` to the creation step's own value, so substituting the "
                     "lower-cased key violates the equality even though the managers "
                     "are right. Witness at model.name=\"Foo\", targetName=\"FOO\" — "
                     "a third distinct casing, matched case-insensitively, where gold "
                     "keeps \"Foo\" and the rival installs \"foo\". Built both ways "
                     "(rival exit 0, gold exit 1).",
    },
    {
        "id": "uniq-carries-original-managers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OLD_MANAGERS,
        "witness": _WIT_OLD_MANAGERS,
        "refinement": "the load-bearing case. Its faithful real patch adds the "
                      "collapse rule but wires the collapsed step's managers to the "
                      "CREATION step's own managers rather than to the following "
                      "step's reconfigured ones: the pair collapses to one step, yet "
                      "the entire effect of the manager reconfiguration is lost. The "
                      "F2P test asserts the collapsed step carries the reconfigured "
                      "manager list; this yields the creation step's original list "
                      "instead, the comparison fails, and it does NOT resolve. This "
                      "is precisely the newly-added behavior, so a verifying rival "
                      "here would be the strongest possible SPEC-TOO-WEAK finding.",
        "rationale": "attacks the MANAGERS component of the (COLLAPSE) payload: the "
                     "spec pins `managers := newManagers`, the rival pins it to "
                     "`model.managers`. Witness at a creation step already carrying "
                     "[(\"objects\",\"M0\")] paired with a reconfiguration supplying "
                     "[(\"things\",\"M1\")] — the only witness where both manager "
                     "lists are non-empty AND differ, so it is the only input that "
                     "separates the two. Also varies the `newManagers` binder away "
                     "from the value the other six hold. Built both ways (rival exit "
                     "0, gold exit 1).",
    },
    {
        "id": "uniq-clobbers-options",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CLOB_OPTS,
        "witness": _WIT_CLOB_OPTS,
        "refinement": "its faithful real patch installs the reconfigured managers "
                      "correctly but also overwrites the collapsed step's options "
                      "component with them. A manager-reconfiguration step supplies "
                      "no options at all, so such a patch destroys the model's "
                      "declared options on every collapse. The P2P optimizer tests "
                      "that collapse a creation step with an options "
                      "reconfiguration, and those that round-trip a creation step "
                      "carrying options, would read back wrong options — it does NOT "
                      "resolve.",
        "rationale": "attacks the OPTIONS component of the (COLLAPSE) payload, which "
                     "the structure-update frame pins UNCHANGED to the creation "
                     "step's value. This is one of the three cases carrying nagini's "
                     "read-only-frame argument structurally, since the carried-over "
                     "components are observable parts of the result rather than an "
                     "aliased side effect. Witness at a creation step whose options "
                     "are [(\"db_table\",\"t\")] — non-empty, so gold's carried-over "
                     "value and the rival's substituted one differ; varies the "
                     "`model` binder's options field, which no other witness moves. "
                     "Built both ways (rival exit 0, gold exit 1).",
    },
    {
        "id": "uniq-clobbers-fields",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CLOB_FIELDS,
        "witness": _WIT_CLOB_FIELDS,
        "refinement": "its faithful real patch installs the reconfigured managers "
                      "correctly but also overwrites the collapsed step's field list "
                      "with them, so every collapse destroys the model's fields. The "
                      "F2P test asserts the collapsed step keeps the creation step's "
                      "field list, and the P2P tests that collapse a creation step "
                      "carrying real fields would produce a model with the wrong "
                      "columns — it does NOT resolve.",
        "rationale": "attacks the FIELDS component of the (COLLAPSE) payload, pinned "
                     "UNCHANGED by the structure-update frame. Witness at a creation "
                     "step whose fields are [(\"id\",\"AutoField\")] — non-empty, so "
                     "the carried-over and substituted values differ; varies the "
                     "`model` binder's fields field, which no other witness moves. "
                     "Built both ways (rival exit 0, gold exit 1).",
    },
    {
        "id": "uniq-clobbers-bases",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CLOB_BASES,
        "witness": _WIT_CLOB_BASES,
        "refinement": "its faithful real patch installs the reconfigured managers "
                      "correctly but synthesizes a new bases component for the "
                      "collapsed step instead of carrying the creation step's over. A "
                      "manager-reconfiguration step supplies no bases, so a collapsed "
                      "step would claim the wrong inheritance and the model's "
                      "inherited fields/behavior would change. The P2P tests that "
                      "collapse a creation step declaring explicit bases assert the "
                      "bases survive; they would fail — it does NOT resolve. Not "
                      "present in the nagini battery, which names this clause "
                      "load-bearing but ships no rival for it; added here so the "
                      "component is not left unattacked.",
        "rationale": "attacks the BASES component of the (COLLAPSE) payload, pinned "
                     "UNCHANGED by the structure-update frame. Witness at a creation "
                     "step whose bases are [\"Base\"] — non-empty and distinct from "
                     "the synthesized [model.name], so gold and the rival differ; "
                     "varies the `model` binder's bases field, which no other witness "
                     "moves. Built both ways (rival exit 0, gold exit 1).",
    },
    {
        "id": "uniq-concatenates-managers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_APPEND_MANAGERS,
        "witness": _WIT_APPEND_MANAGERS,
        "refinement": "its faithful real patch collapses the pair and does install the "
                      "reconfigured managers, but ADDS them to the creation step's own "
                      "list instead of REPLACING it. The collapsed step then declares "
                      "every manager the creation step declared plus every reconfigured "
                      "one, so a reconfiguration that was meant to REMOVE or REPLACE a "
                      "manager silently keeps it, and the default manager (the first in "
                      "the list) can be the stale one. The F2P test compares the "
                      "optimized output against a creation step carrying exactly the "
                      "reconfigured list; the longer list fails the comparison, so it "
                      "does NOT resolve.",
        "rationale": "added by AUDIT to close a real gap on the MANAGERS component of "
                     "the (COLLAPSE) payload. The spec pins `managers := newManagers` by "
                     "EQUALITY, but every pre-existing rival on this component either "
                     "keeps it correct or substitutes a wholly disjoint list "
                     "(`uniq-carries-original-managers`), so nothing probed the weaker "
                     "mis-selection in which the reconfigured managers are PRESENT but "
                     "not ALONE — the failure mode a containment-style spec would admit. "
                     "Witness at a creation step carrying [(\"objects\",\"M0\")] paired "
                     "with a reconfiguration supplying [(\"things\",\"M1\")], "
                     "identifiers spelled \"Beta\"/\"BETA\" so the input point is "
                     "distinct from every other witness's. Built both ways (rival exit "
                     "0, gold exit 1 with a `⊢ False` residual).",
    },
    {
        "id": "uniq-exact-identifier-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EXACT_GUARD,
        "witness": _WIT_EXACT_GUARD,
        "refinement": "its faithful real patch guards the new collapse rule with an "
                      "EXACT comparison of the two identifiers instead of the "
                      "case-insensitive one the optimizer uses everywhere else. Whenever "
                      "the following step spells the model's identifier with different "
                      "casing than the creation step did, the pair is left "
                      "un-collapsed even though both steps name the same model — the "
                      "optimization silently stops firing on that input class. It does "
                      "NOT resolve: the optimizer's other collapse rules all agree the "
                      "two steps refer to one model there, so the output disagrees with "
                      "the surrounding rules and the pairing that should reduce to a "
                      "single step stays as two.",
        "rationale": "attacks the GUARD of both conjuncts rather than either payload: "
                     "the spec's antecedents are `sameModel model.name targetName`, a "
                     "case-insensitive match, so an exact-equality guard sends an input "
                     "the spec places in the (COLLAPSE) case into the empty result. "
                     "Added by audit to close a real gap: the seven pre-existing rivals "
                     "either keep the guard verbatim or drop it wholesale, so no case "
                     "probed the guard in the STRENGTHENING direction, and a variant "
                     "that lost the case-folding would have verified unnoticed. Needs "
                     "its own input — it agrees with the frozen impl on every witness "
                     "whose two identifiers are already spelled alike. Witness at "
                     "model.name=\"Foo\" vs targetName=\"foo\": the strings differ, the "
                     "lower-cased keys agree, so gold collapses and the rival returns "
                     "the empty result. Built both ways (rival exit 0, gold exit 1 with "
                     "a `⊢ False` residual).",
    },
]


# ===========================================================================
# AXIOM LANE — none. This bundle declares no `axiom` and no `opaque` callee: the
# modeled decision performs only a case-insensitive identifier comparison and a
# structure update, both modeled deeply, so there is no over-approximation to
# probe. The axiom lane is G-AX's job in any case and this gate ignores
# AXIOM_TESTS.
# ===========================================================================
AXIOM_TESTS = []

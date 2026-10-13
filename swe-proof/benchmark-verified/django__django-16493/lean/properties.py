"""properties.py — G-PBT falsification battery for django__django-16493 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a three-input identity domain):

  recordedStorage
      (originalCallable : Option Nat) (evaluatedStorage : Nat)
      (defaultStorage : Nat) : Option Nat
      result = (let storage := originalCallable.getD evaluatedStorage
                if storage = defaultStorage then none else some storage)

  Identities are modeled as ``Nat`` (mapping.md: identity bijection).
  ``originalCallable`` is the ORIGINAL reference (``some c`` = a caller-supplied
  reference of identity ``c``; ``none`` = none supplied); ``evaluatedStorage``
  is the EVALUATED instance; ``defaultStorage`` is the module-global default.
  The result records, if anything, the ORIGINAL reference — ``getD`` selects the
  supplied reference when present, else the evaluated instance — and records it
  ONLY when that reference differs from the default.

  The single top-level clause folds three inseparable sub-decisions, each pinned
  to a distinct binder:

    * WHICH REFERENCE is compared and recorded — ``originalCallable.getD
      evaluatedStorage`` — so a supplied reference wins over the evaluated
      instance. Pinned by ``originalCallable`` and ``evaluatedStorage``.
    * WHAT IS COMPARED against the default — the SELECTED reference, not the
      evaluated instance. This is the discriminating decision: the two coincide
      unless a supplied reference EVALUATES to the default while itself being a
      distinct identity, which is exactly the case the F2P observable exercises.
    * WHETHER anything is recorded at all — ``none`` iff the selected reference
      equals the default, ``some storage`` otherwise. Pinned by ``defaultStorage``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because the modeled inputs are held at
    fractional (read-only) permission and a rival that overwrites one is
    rejected for insufficient permission. Lean is referentially transparent:
    the three inputs are plain immutable values (``Option Nat`` / ``Nat``),
    there is no half-permission to violate and no aliasing to exploit, so this
    class has NO expressible instance here. No substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the three inputs (``getD`` plus an identity
    comparison and a concrete ``none``/``some`` split), fully unfolded. The
    bundle declares no ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []), so there is no answer key an implementation
    could echo without doing the work. The honest analogue is the
    cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN (the pre-patch guard) — APPLIES, and is the load-bearing
    rival. The pre-fix compared the EVALUATED instance to the default instead of
    the selected reference. It is correct on every configuration EXCEPT the one
    where a supplied reference evaluates to the default — the F2P sub-domain —
    so it is refuted precisely there.

  * VALUE / ALWAYS-INCLUDE / DROP-REFERENCE-PREFERENCE — APPLY. Rivals that
    record on every input (never omit the default), or that compare/record the
    evaluated instance instead of the selected reference, each violate the one
    clause on a distinct sub-domain and are refuted with witnesses at distinct
    inputs.

  * SUPPLIED-REFERENCE-EXEMPTED-FROM-THE-COMPARISON — APPLIES, and is the leg an
    audit added. The comparison against the default has to run on the SELECTED
    reference on BOTH legs of ``getD``. A rival that applies it only on the
    fallback leg — recording any SUPPLIED reference unconditionally — is wrong
    only where a supplied reference's own identity IS the default, and is
    value-identical to the frozen impl at every other point, including all four
    points the rivals above are refuted at. See
    ``weak-supplied-reference-exempt``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked to HOLD of its rival and to
FAIL on the frozen solution (so it discriminates rather than asserting a
tautology).

BINDER COVERAGE. All three input binders are varied across the reject witnesses
so the battery exercises the spec's dependence on each rather than probing one
point repeatedly:
  * ``originalCallable`` — refuted at ``some _`` (prepatch-guard, drop-reference)
    AND at ``none``, on BOTH legs of the ``getD`` fallback: where the fallback
    value equals the default and omitting is correct (always-record) and where it
    differs and must be recorded (no-fallback).
  * ``evaluatedStorage`` — refuted where it EQUALS the default (prepatch-guard,
    always-record) AND where it is a distinct non-default value (drop-reference,
    no-fallback).
  * ``defaultStorage`` — held at ``7`` for prepatch-guard, ``2`` for
    supplied-reference-exempt and ``0`` for the others, so it is not pinned to a
    single value across the lane.
``pts`` = 5 distinct input points.

The four ``some``/``none`` × default/non-default combinations of the SELECTED
reference are each pinned by exactly one witness, which is what makes the lane
exhaustive over the spec's own case split rather than merely varied:
  * ``(some 1) 7 7`` — supplied, differs from default (record it) — and the
    evaluated instance coincides with the default, the F2P corner.
  * ``(some 2) 5 2`` — supplied, EQUALS the default (omit it).
  * ``none 4 0``     — fallback, differs from default (record it).
  * ``none 0 0``     — fallback, equals the default (omit it).
``(some 5) 3 0`` additionally separates the recorded IDENTITY (supplied) from the
evaluated one.

The ``none``-branch pair is load-bearing rather than decorative. A rival that
honours a supplied reference correctly but records NOTHING when none was supplied
is value-identical to the frozen impl at the other three witness points, so it is
caught only at ``none 4 0`` — the fallback leg where the evaluated instance is
non-default. ``none 0 0`` alone cannot distinguish "fall back to the evaluated
instance" from "record nothing when unsupplied", since both omit there.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total selection/comparison over the inputs' own
identities, so there is no axiom-soundness / axiom-containment obligation to
probe here (that lane belongs to G-AX in any case). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-16493"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat := Id.run do\n"
    "  let storage := originalCallable.getD evaluatedStorage\n"
    "  let mut result : Option Nat := none\n"
    "  if storage ≠ defaultStorage then\n"
    "    result := some storage\n"
    "  return result\n"
)

_PROOF_BODY = (
    "  intro originalCallable evaluatedStorage defaultStorage\n"
    "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : originalCallable.getD evaluatedStorage = defaultStorage\n"
    "  · simp [h]\n"
    "  · simp [h]\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each is a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN (= the pre-fix bug): select the original reference correctly,
# but compare the EVALUATED instance to the default instead of the selected
# reference. Diverges exactly where a supplied reference evaluates to the
# default (the F2P sub-domain).
_PREPATCH_GUARD = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat := Id.run do\n"
    "  let storage := originalCallable.getD evaluatedStorage\n"
    "  let mut result : Option Nat := none\n"
    "  if evaluatedStorage ≠ defaultStorage then\n"
    "    result := some storage\n"
    "  return result\n"
)

# ALWAYS-RECORD: select the reference correctly but record it unconditionally,
# never omitting it when it equals the default.
_ALWAYS_RECORD = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat := Id.run do\n"
    "  let storage := originalCallable.getD evaluatedStorage\n"
    "  return some storage\n"
)

# DROP-REFERENCE-PREFERENCE: compare and record the EVALUATED instance, ignoring
# the supplied original reference. The omit/record decision may still be right,
# but the recorded identity is the evaluated one.
_DROP_REFERENCE = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat := Id.run do\n"
    "  let storage := evaluatedStorage\n"
    "  let mut result : Option Nat := none\n"
    "  if storage ≠ defaultStorage then\n"
    "    result := some storage\n"
    "  return result\n"
)

# NO-FALLBACK: honour the supplied reference correctly, but when NO reference was
# supplied record nothing at all instead of falling back to the evaluated
# instance. This rival agrees with the frozen impl on every input the other three
# rivals are refuted at (`(some 1) 7 7`, `none 0 0`, `(some 5) 3 0`), so it probes
# the `getD` FALLBACK leg — the `originalCallable = none` branch with a
# non-default evaluated instance — which no other case in this battery pins.
_NO_FALLBACK = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat :=\n"
    "  match originalCallable with\n"
    "  | none => none\n"
    "  | some c => if c = defaultStorage then none else some c\n"
)

# SUPPLIED-REFERENCE-EXEMPT: run the default comparison ONLY on the `getD`
# fallback leg, recording any SUPPLIED reference unconditionally. Wrong exactly
# where a supplied reference's own identity IS the default; value-identical to
# the frozen impl everywhere else, so no other rival's witness point catches it.
_SUPPLIED_EXEMPT = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat :=\n"
    "  match originalCallable with\n"
    "  | some c => some c\n"
    "  | none => if evaluatedStorage = defaultStorage then none else some evaluatedStorage\n"
)

# POSITIVE CONTROL 2 (soundness): a correct reshape that spells the omit/record
# decision as an `Option.filter` over the selected reference rather than as an
# `if`/`then`/`else` — a different eliminator, not a different value. The frozen
# script does not apply, so the obligation is re-proved for the new shape.
_POS_FILTER = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat :=\n"
    "  (some (originalCallable.getD evaluatedStorage)).filter (fun s => s ≠ defaultStorage)\n"
)
_POS_FILTER_PROOF = (
    "  intro originalCallable evaluatedStorage defaultStorage\n"
    "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
    "  by_cases h : originalCallable.getD evaluatedStorage = defaultStorage\n"
    "  · simp [Option.filter, h]\n"
    "  · simp [Option.filter, h]\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional expression (no `Id.run do` / `let mut`), spelling the
# omit/record decision as the spec's own `if … then none else some`. Same value
# on every input; the frozen script no longer applies to the new shape, so the
# obligation is re-proved (statement byte-identical, no new lemma/axiom).
_POS_CONTROL = (
    "def implementation_recordedStorage\n"
    "    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :\n"
    "    Option Nat :=\n"
    "  let storage := originalCallable.getD evaluatedStorage\n"
    "  if storage = defaultStorage then none else some storage\n"
)
_POS_PROOF = (
    "  intro originalCallable evaluatedStorage defaultStorage\n"
    "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
    "  rfl\n"
)



SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_recordedStorage`
    # STATEMENT is byte-identical; the tactic body is re-proved for the new shape
    # (the frozen `simp only [Id.run …]` is tuned to the `Id.run do` form). No
    # helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_CONTROL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` and "
            "spells the selection+decision as one functional expression (`let "
            "storage := originalCallable.getD evaluatedStorage; if storage = "
            "defaultStorage then none else some storage`) must satisfy `result = "
            "(let storage := originalCallable.getD evaluatedStorage; if storage = "
            "defaultStorage then none else some storage)`; if it cannot, the spec "
            "is SPEC-TOO-STRONG. Proof: after `unfold` both sides are the same "
            "let/if term, so the goal closes by `rfl` — no new declaration, axiom, "
            "or assumption token."
        ),
    },

    {
        "id": "pos-option-filter",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_FILTER), _PROOF_BODY, _POS_FILTER_PROOF),
        "rationale": (
            "a second correct reshape, varying the ELIMINATOR rather than the "
            "value: the omit/record decision is spelled as `Option.filter (fun s "
            "=> s ≠ defaultStorage)` over the selected reference instead of as "
            "the spec's `if storage = defaultStorage then none else some "
            "storage`. It agrees with the frozen impl on every input, so it must "
            "satisfy the obligation; if a faithful correct impl expressed through "
            "a different `Option` eliminator were rejected, the spec would be "
            "SPEC-TOO-STRONG in a way the `if`-shaped positive control cannot "
            "detect (that one reuses the spec's own syntactic form). Proof: case "
            "split on whether the selected reference equals the default and "
            "reduce `Option.filter` on each branch — no new declaration, axiom, "
            "or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only provable in
    # the abstract. The frozen theorem carries NO precondition hypothesis (the
    # behavior is total, so `∀` is unguarded), so nagini's precondition-admission
    # probe has no binder to attack here; the honest analogue is to discharge the
    # spec predicate at the F2P ground input (a supplied reference distinct from
    # the default that EVALUATES to the default) inside the proof region,
    # alongside the frozen obligation. If that ground instance could not be
    # discharged, the modeled behavior would be unsatisfiable at exactly the input
    # the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-callable-evaluates-default-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_recordedStorage (some 1) 7 7\n"
            "      (implementation_recordedStorage (some 1) 7 7) := by\n"
            "    unfold problem_spec_recordedStorage implementation_recordedStorage\n"
            "    decide\n"
            + _PROOF_BODY,
        ),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a supplied "
            "reference `some 1` distinct from the default `7` that EVALUATES to "
            "the default: `evaluatedStorage = 7`), where the spec requires the "
            "reference be recorded (`some 1`) rather than omitted, by `decide`; "
            "then the frozen obligation is closed verbatim. Verifies (else the "
            "spec is unsatisfiable at the normal input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-guard-on-evaluated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_GUARD),
        "refinement": (
            "this is the pre-fix behavior: the omit/record decision is taken from "
            "the EVALUATED instance rather than the selected original reference, "
            "while the recorded value is still the selected reference. Its faithful "
            "real patch is exactly the pre-patch code, which OMITS the storage "
            "reference for a field whose supplied callable evaluates to the "
            "default. That fails the F2P observable (a callable that returns the "
            "default must still be recorded as a non-default reference), because "
            "the entry is absent. It does NOT resolve — this is the leg's prepatch."
        ),
        "rationale": (
            "REJECT from the clause `result = (let storage := originalCallable.getD "
            "evaluatedStorage; if storage = defaultStorage then none else some "
            "storage)`: at `originalCallable = some 1`, `evaluatedStorage = 7 = "
            "defaultStorage` the selected reference is `1 ≠ 7`, so the spec demands "
            "`some 1`, but the rival's guard on the evaluated instance (`7 = 7`) "
            "yields `none`. Refuted where a supplied reference evaluates to the "
            "default — the discriminating sub-domain — with `defaultStorage` set to "
            "7 so that binder is not pinned to a single value across the lane."
        ),
        "witness": (
            "-- Refuted where a supplied reference (identity 1) evaluates to the\n"
            "-- default (identity 7): the reference differs from the default, so it\n"
            "-- must be recorded, even though the evaluated instance IS the default.\n"
            "example : ¬ problem_spec_recordedStorage (some 1) 7 7\n"
            "    (implementation_recordedStorage (some 1) 7 7) := by\n"
            "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-always-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_RECORD),
        "refinement": (
            "recording the reference unconditionally emits a storage entry even "
            "when the field uses the plain default (no supplied reference, and the "
            "evaluated instance IS the default); the pre-existing deconstruction "
            "tests assert the storage entry is ABSENT for a default-storage field "
            "(the default is re-supplied automatically on rebuild). Always-record "
            "breaks those. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = (let storage := originalCallable.getD "
            "evaluatedStorage; if storage = defaultStorage then none else some "
            "storage)`: at `originalCallable = none`, `evaluatedStorage = 0 = "
            "defaultStorage` the selected reference equals the default, so the spec "
            "demands `none` (omit), but the rival returns `some 0`. Refuted with NO "
            "reference supplied (`originalCallable = none`), varying that binder off "
            "the `some _` value the other rivals use."
        ),
        "witness": (
            "-- Refuted with no supplied reference and the evaluated instance equal\n"
            "-- to the default: the field uses the plain default, so nothing is\n"
            "-- recorded — an always-record impl wrongly surfaces an entry.\n"
            "example : ¬ problem_spec_recordedStorage none 0 0\n"
            "    (implementation_recordedStorage none 0 0) := by\n"
            "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-reference-preference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_REFERENCE),
        "refinement": (
            "comparing and recording the EVALUATED instance instead of the supplied "
            "original reference corresponds to recording the evaluated storage "
            "rather than the caller's reference; the rebuilt field would lose the "
            "supplied (deferred) reference, so the pre-existing deconstruction test "
            "that asserts the recorded value IS the supplied reference (not its "
            "evaluated result) fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = (let storage := originalCallable.getD "
            "evaluatedStorage; if storage = defaultStorage then none else some "
            "storage)`: at `originalCallable = some 5`, `evaluatedStorage = 3`, "
            "`defaultStorage = 0` the selected reference is `5`, so the spec demands "
            "`some 5`, but the rival records the evaluated instance `some 3`. "
            "Refuted where the supplied reference and the evaluated instance are "
            "DISTINCT non-default identities, exercising `evaluatedStorage` at a "
            "value other than the default."
        ),
        "witness": (
            "-- Refuted where the supplied reference (identity 5) differs from the\n"
            "-- evaluated instance (identity 3): the recorded value must be the\n"
            "-- supplied reference, not the evaluated result.\n"
            "example : ¬ problem_spec_recordedStorage (some 5) 3 0\n"
            "    (implementation_recordedStorage (some 5) 3 0) := by\n"
            "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-no-fallback-when-unsupplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_FALLBACK),
        "refinement": (
            "this rival records the supplied reference correctly whenever one was "
            "supplied, but when NONE was supplied it records nothing at all instead "
            "of falling back to the evaluated instance. Its faithful real patch "
            "would drop the storage reference for every field configured with a "
            "non-default storage instance directly (no callable supplied), so the "
            "pre-existing deconstruction tests that assert a directly-configured "
            "non-default storage IS recorded fail — the entry is absent. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = (let storage := originalCallable.getD "
            "evaluatedStorage; if storage = defaultStorage then none else some "
            "storage)`: at `originalCallable = none`, `evaluatedStorage = 4`, "
            "`defaultStorage = 0` the `getD` FALLBACK selects the evaluated "
            "instance `4 ≠ 0`, so the spec demands `some 4`, but the rival returns "
            "`none`. This pins the fallback leg of `getD`, which no other case in "
            "this battery pins: the rival is value-identical to the frozen impl at "
            "all three points the other rivals are refuted at, so none of them "
            "would catch it. The `originalCallable = none` branch was previously "
            "exercised only where the evaluated instance EQUALS the default "
            "(`none 0 0`), where omitting is CORRECT — that point cannot "
            "distinguish 'fall back to the evaluated instance' from 'record "
            "nothing when unsupplied'."
        ),
        "witness": (
            "-- Refuted with NO supplied reference and a non-default evaluated\n"
            "-- instance (identity 4, default 0): with nothing supplied the\n"
            "-- evaluated instance IS the reference to record, so omitting it is\n"
            "-- wrong. Distinct from `none 0 0`, where omitting is correct.\n"
            "example : ¬ problem_spec_recordedStorage none 4 0\n"
            "    (implementation_recordedStorage none 4 0) := by\n"
            "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-supplied-reference-exempt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SUPPLIED_EXEMPT),
        "refinement": (
            "this rival applies the differs-from-the-default test only on the "
            "`getD` FALLBACK leg: a supplied reference is recorded "
            "unconditionally, without ever being compared to the default. Its "
            "faithful real patch records a storage entry for a field whose "
            "supplied reference IS the default reference itself — the "
            "configuration where the reference and the default coincide — so the "
            "entry is emitted where the pre-existing deconstruction tests assert "
            "it is ABSENT (a field that names the default needs no entry; the "
            "default is re-supplied automatically on rebuild). It does NOT "
            "resolve: it also leaves the F2P observable untouched, since it "
            "changes nothing about a supplied reference distinct from the default."
        ),
        "rationale": (
            "REJECT from the clause `result = (let storage := originalCallable.getD "
            "evaluatedStorage; if storage = defaultStorage then none else some "
            "storage)`: at `originalCallable = some 2`, `evaluatedStorage = 5`, "
            "`defaultStorage = 2` the selected reference is `2 = defaultStorage`, "
            "so the spec demands `none` (omit), but the rival records `some 2`. "
            "This pins the fourth and last cell of the spec's own case split — a "
            "SUPPLIED reference whose identity EQUALS the default — which no other "
            "case in this battery pins: the rival is value-identical to the frozen "
            "impl at all four points the others are refuted at (`(some 1) 7 7`, "
            "`none 0 0`, `(some 5) 3 0`, `none 4 0`), so none of them would catch "
            "it. It also moves `defaultStorage` to a third value (`2`) and is the "
            "only witness where the evaluated instance is non-default while the "
            "result is correctly omitted, separating 'compare the selected "
            "reference' from 'compare only the fallback'."
        ),
        "witness": (
            "-- Refuted where the SUPPLIED reference (identity 2) is itself the\n"
            "-- default (identity 2), while the evaluated instance (5) is not:\n"
            "-- the selected reference coincides with the default, so nothing is\n"
            "-- recorded. Exempting a supplied reference from the comparison\n"
            "-- wrongly records it. Distinct from `(some 1) 7 7`, where the\n"
            "-- supplied reference differs from the default and MUST be recorded.\n"
            "example : ¬ problem_spec_recordedStorage (some 2) 5 2\n"
            "    (implementation_recordedStorage (some 2) 5 2) := by\n"
            "  unfold problem_spec_recordedStorage implementation_recordedStorage\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the default identity is a
# plain input and the selection/comparison is modeled directly, so there is no
# in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []

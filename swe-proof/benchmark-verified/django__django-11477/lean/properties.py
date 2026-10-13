"""properties.py — G-PBT falsification battery for django__django-11477 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS case is a
FULL ``Solution.lean`` variant built by region-surgery over the frozen file: a
case edits ONLY text inside the ``-- impl-start`` / ``-- impl-end`` region and
(for the reproven / ground-instance positives) inside the
``-- proof-start`` / ``-- proof-end`` region, so ``markers.same_spec`` holds by
construction and the ``theorem correct_capture`` STATEMENT stays byte-identical.
Any verify/reject outcome is therefore attributable to the postcondition, not to
a tampered spec. ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (see Solution.lean / mapping.md):

  capture
      (path : List Char) (outcome : Option (ScanOutcome V))
      : Option (List Char × List (Option V) × List (Nat × Option V))

  The single modeled obligation reshapes the outcome of a scan into the data a
  caller consumes. Its postcondition is a case split on ``outcome`` with, on the
  ``some sc`` branch, an EXACT equality against a triple built entirely from the
  inputs. Four independent top-level components, each pinned to distinct binders:

    (C0) OUTCOME PRESENCE — a failed scan (``outcome = none``) yields ``none``;
         a successful scan yields ``some _``. Pinned by ``outcome``.
    (C1) LEFTOVER — the first component equals ``path.drop sc.consumed`` (the
         portion beyond the consumed prefix). Pinned by ``path`` and
         ``sc.consumed``.
    (C2) NAMED MAPPING — the third component equals
         ``sc.namedCaptures.filter carriesValue``: exactly the named captures
         that CARRY a value, in order; an absent (no-value) named capture
         contributes NOTHING. This is the load-bearing decision. Pinned by
         ``sc.namedCaptures``.
    (C3) POSITIONAL CHOICE — the second component equals
         ``if (filtered named).isEmpty then sc.positionalCaptures else []``: the
         positional captures are reported ONLY when the named mapping is empty.
         Pinned by ``sc.positionalCaptures`` and, via the guard, by
         ``sc.namedCaptures``.

  The captured VALUE type is abstract (a type variable ``V``): the modeled
  behavior never inspects a captured value, it only decides presence
  (``carriesValue`` = the value ``isSome``) and carries the value through.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because the modeled inputs are held at
    fractional (read-only) permission, so a rival that writes back to one is
    rejected for insufficient permission. Lean is referentially transparent: the
    inputs are plain immutable values, there is no half-permission to violate and
    no aliasing to exploit, so this class has NO expressible instance here. No
    substitute is fabricated for it. DEMONSTRATED, not asserted: the closest
    analogue this carrier admits — an impl that rebinds BOTH modeled inputs to
    scrambled values (``path.reverse ++ path``; an outcome with ``consumed + 7``
    and both capture lists reversed) before returning the correct triple built
    from the original binders — VERIFIES. There is no observer of the write, so
    the spec has nothing to reject; the nagini instance's whole force came from
    the permission system, which has no analogue here.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a triple built only from the inputs (a ``drop``, a ``filter`` over a
    decidable predicate, and an ``isEmpty`` guard), fully unfolded. The bundle
    declares no ``opaque``/``axiom`` (meta.json axioms == [],
    deep_model_references == []), so there is no answer key an implementation
    could echo without doing the work. The honest analogue is the
    cheapest-correct POSITIVE CONTROL below.

  * WEAK-UNFILTERED (= the pre-patch behavior) — APPLIES, load-bearing. The
    pre-fix retained EVERY named capture, including the ones carrying no value.
    It violates C2 on any input with an absent named capture — the F2P
    sub-domain — and is refuted precisely there.

  * PARTIAL-DOMAIN (drop the first carried capture) — APPLIES. Correct whenever
    fewer than one named capture carries a value, wrong whenever the front of the
    named mapping carries a value; a subtler near-miss than the unfiltered rival,
    refuted at a two-carried-capture input.

  * POSITIONAL-CHOICE (always report positionals) — APPLIES, attacks C3. Drops
    the ``if named empty`` selection guard and always reports the positional
    captures, even when the named mapping is non-empty.

  * LEFTOVER (report the whole path) — APPLIES, attacks C1. Ignores the consumed
    prefix and returns the full path as the leftover.

  * NONE-HANDLING (invent an outcome on failure) — APPLIES, attacks C0. Returns a
    ``some`` triple on a failed scan where the spec demands ``none``.

  * ABSENCE-LEAK (retain a no-value named capture at the TAIL only) — APPLIES,
    attacks C2 on a strictly NARROWER sub-domain than the unfiltered rival. It
    filters correctly except that it re-appends the LAST named capture when that
    one carries no value. It therefore AGREES with the unfiltered rival's verdict
    nowhere except at inputs whose trailing named capture is absent, and agrees
    with GOLD on every input whose trailing named capture carries a value —
    machine-checked at ``namedCaptures := [(0, none), (1, some 2)]``, where its
    ground instance of the spec elaborates. A rival that is correct except on the
    tail is invisible to a byte-fuzzer and to the unfiltered rival's witness.

  * GUARD-ARGUMENT (choose positionals off the UNFILTERED mapping) — APPLIES,
    attacks C3's GUARD ARGUMENT rather than its polarity or its branches. It
    computes the named mapping exactly as the spec does, and then tests
    ``sc.namedCaptures.isEmpty`` — the PRE-filter mapping — where the spec tests
    the filtered one. It agrees with gold on every input where filtering does not
    change emptiness (machine-checked at ``namedCaptures := [(0, some 1)]``) and
    diverges exactly where every named capture is absent AND positionals exist —
    the one sub-domain where the two emptiness tests come apart, and the one the
    positional-choice rival cannot reach because that rival drops the guard
    entirely rather than mis-arguing it.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen ``Id.run
do`` form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``/``simp``-able concrete input (``V := Nat``);
each was checked to HOLD of its rival (elaborates) and to FAIL on the frozen
solution (unsolved ``False``), so it discriminates rather than asserting a
tautology.

BINDER COVERAGE. All input binders of the spec predicate are varied across the
reject witnesses so the battery exercises the spec's dependence on each:
  * ``outcome`` — refuted at ``some _`` (four rivals) AND at ``none``
    (none-handling).
  * ``path`` — held non-empty (``['a','b']``) for the leftover rival where it is
    load-bearing, ``[]`` elsewhere.
  * ``sc.consumed`` — refuted where it is NON-ZERO (leftover: ``consumed = 1``),
    the only value at which a whole-path leftover diverges from the drop.
  * ``sc.namedCaptures`` — varied across an absent-only entry (unfiltered),
    two carried entries (drop-first), one carried entry (positional-choice),
    empty (leftover), and a MIXED carried-then-absent pair (absence-leak), the
    only shape that separates a tail-only violation from a whole-list one.
  * ``sc.positionalCaptures`` — non-empty where it is load-bearing
    (positional-choice and guard-argument: ``[some 9]``), empty elsewhere.
``pts`` = 7 distinct input points.

The two positives were themselves checked for vacuity rather than assumed
load-bearing, since a positive that passes trivially tests nothing:

  * the soundness reshape does NOT close under the frozen tactic body (that build
    fails ``No goals to be solved``), so its ``rfl``-per-branch proof is a genuine
    RE-proof for the new shape, not the frozen script riding along;
  * the admissibility ground instance does NOT hold of the rivals — the identical
    ``have`` fails with ``Tactic `rfl` failed`` when carried over the unfiltered
    and whole-path impls — so it is discriminating evaluation at the F2P-shaped
    input, not a tautology any impl would satisfy.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
scan outcome is supplied as input data and the reshape is modeled directly, so
there is no in-model axiom obligation for the PBT axiom lane to re-discharge
(that lane belongs to G-AX in any case). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-11477"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors (each unique inside Solution.lean; verified at load). The FULL
# impl-region body and the FULL frozen tactic body, so every replacement lands
# entirely inside the region it means to edit.
# ---------------------------------------------------------------------------
_IMPL_GOLD = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) := Id.run do\n"
    "  let some sc := outcome | return none\n"
    "  let mut named : List (Nat × Option V) := []\n"
    "  for entry in sc.namedCaptures do\n"
    "    if carriesValue entry then\n"
    "      named := named ++ [entry]\n"
    "  let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "  return some (path.drop sc.consumed, positional, named)"
)

_PROOF_BODY = (
    "  intro path outcome\n"
    "  unfold problem_spec_capture implementation_capture\n"
    "  cases outcome with\n"
    "  | none => rfl\n"
    "  | some sc =>\n"
    "    -- The desugared loop body bridges to `capture_loop`'s clean body after\n"
    "    -- `simp only [bind]`; rewriting it leaves `init = [] ++ filter …` to settle.\n"
    "    simp only [Option.elim, Id.run, bind, capture_loop]\n"
    "    rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full variant by swapping ONLY the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally-different but CORRECT impl — a
# direct functional `match` (no `Id.run do` / `let mut` / `for` loop), spelling
# the named mapping as the spec's own `sc.namedCaptures.filter carriesValue`.
# Same value on every input; the frozen `capture_loop` bridge no longer applies
# to the new shape, so the obligation is re-proved (statement byte-identical, no
# new lemma/axiom): after `unfold` both branches are the same term, so each
# closes by `rfl`.
# ---------------------------------------------------------------------------
_POS_IMPL = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let named := sc.namedCaptures.filter carriesValue\n"
    "    let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "    some (path.drop sc.consumed, positional, named)"
)
_POS_PROOF = (
    "  intro path outcome\n"
    "  unfold problem_spec_capture implementation_capture\n"
    "  cases outcome with\n"
    "  | none => rfl\n"
    "  | some sc => rfl"
)
_POS_CONTROL = _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (positive control): discharge the spec predicate at the normal
# F2P-shaped ground input (a successful scan with one carried named capture, one
# ABSENT named capture, and a positional capture) inside the proof region,
# alongside the frozen obligation. The frozen theorem binds NO precondition
# hypothesis (the behavior is total), so nagini's precondition-admission probe
# has no binder to attack; the honest analogue is to confirm the obligation is
# SATISFIABLE (non-vacuous) at exactly the input the F2P exercises. If that
# ground instance could not be discharged the modeled behavior would be
# unsatisfiable at the normal input. Nothing is assumed: the STATEMENT is
# byte-identical, the ground instance is a `have` inside the existing tactic body
# closed by `unfold … ; rfl`, and no new declaration/axiom/`sorry` is introduced.
# ---------------------------------------------------------------------------
_ADM_GROUND = (
    "  have _ground : problem_spec_capture (V := Nat) ['x', 'y']\n"
    "      (some { consumed := 1, namedCaptures := [(0, some 5), (1, none)],\n"
    "              positionalCaptures := [some 9] })\n"
    "      (implementation_capture (V := Nat) ['x', 'y']\n"
    "        (some { consumed := 1, namedCaptures := [(0, some 5), (1, none)],\n"
    "                positionalCaptures := [some 9] })) := by\n"
    "    unfold problem_spec_capture implementation_capture\n"
    "    rfl\n"
)
_ADM = _swap(_BASE, _PROOF_BODY, _ADM_GROUND + _PROOF_BODY)


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (each a full variant; only the impl body changes, so the
# spec and the theorem STATEMENT stay byte-identical). Each carries a witness
# SEEN to discriminate.
# ---------------------------------------------------------------------------

# WEAK-UNFILTERED (= the pre-patch behavior): retain EVERY named capture,
# including the ones carrying no value. Violates C2.
_UNFILTERED = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let named := sc.namedCaptures\n"
    "    let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "    some (path.drop sc.consumed, positional, named)"
)

# PARTIAL-DOMAIN (drop the FIRST carried capture): filter correctly but drop the
# head of the resulting mapping. Correct when 0 or 1 named capture carries a
# value; wrong when >=2 do. Violates C2 on that sub-domain.
_DROP_FIRST = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let named := (sc.namedCaptures.filter carriesValue).tail\n"
    "    let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "    some (path.drop sc.consumed, positional, named)"
)

# POSITIONAL-CHOICE (always report positionals): drop the `if named empty`
# selection guard and report the positional captures unconditionally. Violates
# C3 whenever the named mapping is non-empty.
_POS_ALWAYS = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let named := sc.namedCaptures.filter carriesValue\n"
    "    some (path.drop sc.consumed, sc.positionalCaptures, named)"
)

# LEFTOVER (report the whole path): ignore the consumed prefix. Violates C1
# whenever the consumed prefix is non-empty.
_LEFTOVER = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let named := sc.namedCaptures.filter carriesValue\n"
    "    let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "    some (path, positional, named)"
)

# NONE-HANDLING (invent an outcome on failure): return a `some` triple on a
# failed scan. Violates C0.
_NONE_SOME = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => some ([], [], [])\n"
    "  | some sc =>\n"
    "    let named := sc.namedCaptures.filter carriesValue\n"
    "    let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "    some (path.drop sc.consumed, positional, named)"
)


# ABSENCE-LEAK (retain a no-value named capture at the TAIL only): filter
# correctly, then re-append the LAST named capture when it carries no value.
# Violates C2 only on inputs whose trailing named capture is absent — a strictly
# narrower sub-domain than the unfiltered rival's, and one that agrees with gold
# whenever the trailing named capture carries a value.
_ABSENCE_LEAK = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let kept := sc.namedCaptures.filter carriesValue\n"
    "    let named := match sc.namedCaptures.getLast? with\n"
    "      | some e => if carriesValue e then kept else kept ++ [e]\n"
    "      | none => kept\n"
    "    let positional := if named.isEmpty then sc.positionalCaptures else []\n"
    "    some (path.drop sc.consumed, positional, named)"
)

# GUARD-ARGUMENT (choose the positionals off the UNFILTERED mapping): compute the
# named mapping exactly as the spec does, but test emptiness of the PRE-filter
# list. Violates C3 exactly where filtering changes emptiness — every named
# capture absent AND positionals present.
_GUARD_UNFILTERED = (
    "def implementation_capture {V : Type}\n"
    "    (path : List Char) (outcome : Option (ScanOutcome V)) :\n"
    "    Option (List Char × List (Option V) × List (Nat × Option V)) :=\n"
    "  match outcome with\n"
    "  | none => none\n"
    "  | some sc =>\n"
    "    let named := sc.namedCaptures.filter carriesValue\n"
    "    let positional := if sc.namedCaptures.isEmpty then sc.positionalCaptures else []\n"
    "    some (path.drop sc.consumed, positional, named)"
)


# ---------------------------------------------------------------------------
# Witnesses. Each states ¬ (spec … (impl …)) at a CONCRETE input (V := Nat) and
# is discharged by `simp` unfolding the spec/impl over the concrete outcome.
# Each was built against the rival (elaborates) and against the frozen solution
# (unsolved `False`), so it is a real discriminator, not a tautology.
# ---------------------------------------------------------------------------
def _witness(scan, path="[]"):
    return (
        f"example : ¬ problem_spec_capture (V := Nat) {path}\n"
        f"    ({scan})\n"
        f"    (implementation_capture (V := Nat) {path}\n"
        f"      ({scan})) := by\n"
        f"  simp [problem_spec_capture, implementation_capture, carriesValue]"
    )


_W_UNFILTERED = _witness(
    "some { consumed := 0, namedCaptures := [(0, none)], positionalCaptures := [] }"
)
_W_DROP_FIRST = _witness(
    "some { consumed := 0, namedCaptures := [(0, some 1), (1, some 2)], "
    "positionalCaptures := [] }"
)
_W_POS_ALWAYS = _witness(
    "some { consumed := 0, namedCaptures := [(0, some 1)], "
    "positionalCaptures := [some 9] }"
)
_W_LEFTOVER = _witness(
    "some { consumed := 1, namedCaptures := [], positionalCaptures := [] }",
    "['a', 'b']",
)
_W_NONE_SOME = _witness("none")
# Trailing named capture ABSENT, leading one CARRIED: the leak keeps the trailing
# no-value entry. A mixed pair, so it is not the unfiltered rival's point.
_W_ABSENCE_LEAK = _witness(
    "some { consumed := 0, namedCaptures := [(0, some 1), (1, none)], "
    "positionalCaptures := [] }"
)
# Every named capture ABSENT (so the filtered mapping is empty but the raw one is
# not) AND positionals present: the one sub-domain where the two emptiness tests
# disagree. The spec reports the positionals; the rival suppresses them.
_W_GUARD_UNFILTERED = _witness(
    "some { consumed := 0, namedCaptures := [(0, none)], "
    "positionalCaptures := [some 9] }"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-functional-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` "
            "loop and spells the named mapping directly as the spec's own "
            "`sc.namedCaptures.filter carriesValue` inside a functional `match`. "
            "Same value on every input, so it must satisfy the exact-triple "
            "postcondition; if it cannot, the spec is SPEC-TOO-STRONG. Proof: "
            "after `unfold` both branches are the same term, so each closes by "
            "`rfl` — no new declaration, axiom, or assumption token; the "
            "`theorem correct_capture` STATEMENT is byte-identical."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal F2P-shaped ground input.
    # =====================================================================
    {
        "id": "admiss-absent-named-group-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "the obligation is discharged at the F2P ground input (a successful "
            "scan carrying one named capture with a value `(0, some 5)`, one "
            "ABSENT named capture `(1, none)`, and a positional capture "
            "`[some 9]`), where the spec requires the absent capture contribute "
            "nothing and — the mapping being non-empty — the positionals be "
            "suppressed, by `unfold … ; rfl`; then the frozen obligation is "
            "closed verbatim. Verifies (else the spec is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the STATEMENT is byte-identical, the ground instance is a "
            "`have` inside the existing tactic body, no new "
            "declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-unfiltered-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNFILTERED),
        "witness": _W_UNFILTERED,
        "refinement": (
            "this is the pre-fix behavior: retain EVERY named capture, including "
            "the ones carrying no value. Its faithful real patch is exactly the "
            "pre-patch code, which surfaces an absent optional named capture as a "
            "no-value entry. Downstream, rebuilding the URL turns that no-value "
            "entry into a spurious literal, corrupting the result — so it does "
            "NOT resolve the optional-parameter F2P observables; this is the "
            "leg's prepatch."
        ),
        "rationale": (
            "REJECT from clause C2 (`named = sc.namedCaptures.filter "
            "carriesValue`): at a scan whose sole named capture carries no value "
            "`(0, none)`, the spec demands the empty mapping, but the unfiltered "
            "rival keeps the no-value entry. Refuted where a named capture is "
            "absent — the discriminating sub-domain."
        ),
    },
    {
        "id": "weak-drop-first-carried",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_FIRST),
        "witness": _W_DROP_FIRST,
        "refinement": (
            "filtering correctly but dropping the head of the retained mapping "
            "corresponds to a patch that omits the FIRST carried named capture. "
            "The patterns the F2P exercises put a required named capture first, so "
            "the rebuilt/reversed URL loses its leading required argument — it "
            "does NOT resolve. A subtler near-miss than the unfiltered rival, "
            "agreeing with gold whenever fewer than two captures carry a value, so "
            "it gets its own witness at a two-carried-capture input."
        ),
        "rationale": (
            "REJECT from clause C2: at a scan with two carried named captures "
            "`[(0, some 1), (1, some 2)]` the spec demands both, but the rival "
            "drops the first, yielding `[(1, some 2)]`. Refuted where >=2 named "
            "captures carry a value, a strictly more discriminating point than the "
            "unfiltered rival's single absent entry."
        ),
    },
    {
        "id": "weak-positional-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_POS_ALWAYS),
        "witness": _W_POS_ALWAYS,
        "refinement": (
            "dropping the `if named empty` selection guard and always reporting "
            "the positional captures corresponds to a patch that feeds the "
            "positional captures alongside a non-empty named mapping. Post-fix the "
            "positionals are suppressed whenever any named capture carries a "
            "value; extra positional arguments would break view dispatch — it does "
            "NOT resolve the args/kwargs-split F2P."
        ),
        "rationale": (
            "REJECT from clause C3 (`positional = if named.isEmpty then "
            "sc.positionalCaptures else []`): at a scan with a carried named "
            "capture `(0, some 1)` and a positional capture `[some 9]`, the spec "
            "demands the empty positional list, but the rival reports `[some 9]`. "
            "Refuted where `sc.positionalCaptures` is non-empty AND the named "
            "mapping is non-empty, varying both those binders off the other "
            "rivals' values."
        ),
    },
    {
        "id": "weak-leftover-whole-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LEFTOVER),
        "witness": _W_LEFTOVER,
        "refinement": (
            "reporting the whole path instead of the portion beyond the consumed "
            "prefix corresponds to a patch that fails to slice off the matched "
            "prefix. The leftover path drives further resolution; returning the "
            "un-sliced path re-matches the already-consumed segment and misroutes "
            "— it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 (leftover `= path.drop sc.consumed`): at "
            "`path = ['a','b']`, `sc.consumed = 1` the spec demands `['b']`, but "
            "the rival returns `['a','b']`. Refuted where `sc.consumed` is "
            "NON-ZERO and `path` is non-empty — the only sub-domain where a "
            "whole-path leftover diverges from the drop, exercising both those "
            "binders."
        ),
    },
    {
        "id": "weak-none-invents-outcome",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NONE_SOME),
        "witness": _W_NONE_SOME,
        "refinement": (
            "returning a `some` triple on a failed scan corresponds to a patch "
            "that fabricates a match where the pattern did not match. A failed "
            "scan must yield no outcome; inventing one would route a non-matching "
            "path to a view — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C0 (`outcome = none → result = none`): at "
            "`outcome = none` the spec demands `none`, but the rival returns "
            "`some ([], [], [])`. Refuted at the `outcome = none` branch, varying "
            "the `outcome` binder off the `some _` value the other four rivals "
            "use."
        ),
    },
    {
        "id": "weak-absence-leak-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABSENCE_LEAK),
        "witness": _W_ABSENCE_LEAK,
        "refinement": (
            "retaining the TRAILING named capture when it carries no value "
            "corresponds to a patch that filters the mapping but re-admits the "
            "last entry unconditionally — an off-by-one in the retention test. "
            "The surviving no-value entry is exactly the shape the fix exists to "
            "remove: downstream, rebuilding the URL renders that absent value as "
            "a spurious literal segment, so a path whose OPTIONAL trailing "
            "capture did not participate round-trips to a different URL and the "
            "optional-parameter and translated-URL F2P observables still fail — "
            "it does NOT resolve. Strictly narrower than the unfiltered rival: it "
            "agrees with the fixed behavior on every input whose trailing named "
            "capture carries a value."
        ),
        "rationale": (
            "REJECT from clause C2 (`named = sc.namedCaptures.filter "
            "carriesValue`): at `[(0, some 1), (1, none)]` the spec demands "
            "`[(0, some 1)]`, but the leak yields `[(0, some 1), (1, none)]`. "
            "This is a TAIL-ONLY violation — checked to be observably CORRECT at "
            "`[(0, none), (1, some 2)]`, where its ground instance of the spec "
            "elaborates — so it is a genuine near-miss and not a reshape of the "
            "unfiltered rival. It also varies `sc.namedCaptures` onto a MIXED "
            "carried/absent pair no other rival uses."
        ),
    },
    {
        "id": "weak-guard-on-unfiltered-mapping",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GUARD_UNFILTERED),
        "witness": _W_GUARD_UNFILTERED,
        "refinement": (
            "computing the named mapping correctly but selecting the positional "
            "captures off the PRE-filter mapping corresponds to a patch that "
            "fixes the mapping and leaves the downstream emptiness test reading "
            "the OLD, unfiltered value. When every named capture is absent the "
            "corrected mapping is empty and the positional captures must be "
            "reported; this rival still sees a non-empty raw mapping and "
            "suppresses them, so a route whose only captures are absent optional "
            "named ones loses its positional arguments and dispatch still breaks "
            "— it does NOT resolve. This is the half-fix the load-bearing "
            "decision invites, and it is the one the positional-choice rival "
            "cannot reach: that rival drops the guard, this one mis-argues it."
        ),
        "rationale": (
            "REJECT from clause C3 (`positional = if named.isEmpty then "
            "sc.positionalCaptures else []`, where `named` is the FILTERED "
            "mapping): at `namedCaptures := [(0, none)]` with "
            "`positionalCaptures := [some 9]` the filtered mapping is empty so "
            "the spec demands `[some 9]`, but the rival tests the raw mapping, "
            "finds it non-empty, and reports `[]`. Refuted at the only "
            "sub-domain where the two emptiness tests come apart (all named "
            "captures absent AND positionals present) — checked to be observably "
            "CORRECT at `[(0, some 1)]` with the same positionals, so the case "
            "attacks C3's GUARD ARGUMENT specifically rather than its polarity."
        ),
    },
]


# ===========================================================================
# AXIOM lane — NONE. The bundle declares no callee axiom (axioms region empty,
# meta.json axioms == []); the axiom lane is G-AX's job and this gate ignores
# AXIOM_TESTS.
# ===========================================================================
AXIOM_TESTS = []

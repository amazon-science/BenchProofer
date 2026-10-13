"""properties.py — G-PBT falsification battery for pydata__xarray-2905 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over one read-only input).

  prepareData (w : Incoming) return (out : Obj)
      require w.isRecognized = true → w.valuesPayload.isSome = true
      ensures out = forwarded w                                          -- master

  where  forwarded w = if w.isRecognized then w.valuesPayload.getD w.obj
                                          else w.obj

An incoming data object is described by exactly the three observables the
dispatch consults: its own identity (``obj``), the stored values it exposes if
any (``valuesPayload : Option Obj``), and whether it is one of the recognized
container types (``isRecognized : Bool``). The desired behaviour is a total
dispatch: an object of a recognized container type is unwrapped to the stored
values it exposes; EVERY other object — INCLUDING one that merely exposes a
values payload — is forwarded unchanged. The load-bearing clause is the pair of
branch obligations folded into ``out = forwarded w``:

    isRecognized = true  → out = valuesPayload.getD obj    (unwrap)
    isRecognized = false → out = obj                        (passthrough)

This is a FULLY-GROUNDED oracle: ``out`` is pinned to a field of the input on
BOTH branches (``forwarded`` is a concrete ``def`` in the ``pure`` region; the
``axioms`` region declares NO ``axiom`` — there is no opaque answer key to echo).
So there is no "wrong echo that still verifies" and the positive controls are
honest cheapest-reshape controls; the rivals attack the two branch domains
directly. Both input observables that the dispatch reads (``valuesPayload``,
``isRecognized``) are FREE, so a partial-domain rival is refutable at a concrete
point.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the nagini
    sibling because a by-reference input carries a fractional heap permission an
    impl can overwrite (there ``data.*`` are ``Acc(...,1/2)`` read-only). This
    backend is referentially transparent, there is no heap and no aliasing, and
    this bundle declares no ``mut`` binder at all — so there is no read-only
    input to overwrite and no substitute probe to fabricate. Reported as an
    omission, not faked.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. ``forwarded`` is a total unfolded function of
    the method's own argument; no consumed axiom, nothing to echo.
  * PARTIAL-DOMAIN / VALUE — the heart of this surface. A rival right on part of
    the domain but diverting a sub-domain to the wrong forwarded object: unwrap
    a value that is NOT of a recognized container type merely because it exposes
    a payload (the pre-image bug), forward a recognized value unchanged instead
    of unwrapping it, or invert the two arms.
  * FREE-INPUT PRESERVATION — the post-image reads two free observables
    (``isRecognized`` and ``valuesPayload``). A rival can get one arm right and
    still misforward the other, so the reject witnesses move ``isRecognized`` off
    any fixed value (both ``false`` and ``true`` are probed) and each rival that
    ignores an observable is refuted where that observable is load-bearing.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The four reject witnesses sit at four DISTINCT input points:
the prepatch rival at a non-recognized value that exposes a payload
(``isRecognized = false``, the exact antecedent of the passthrough clause), the
never-unwrap rival at a recognized value (``isRecognized = true``, the unwrap
clause's antecedent), the swapped rival at a third recognized point with a
distinct ``obj`` / payload literal, and the unguarded-unwrap rival at a
non-recognized value exposing NO payload (``valuesPayload = none``). Between them
``isRecognized`` takes both ``false`` and ``true``, ``valuesPayload`` takes both
``some _`` and ``none``, and ``obj`` takes three distinct values, so no rival is
refuted at a point that pins any binder the dispatch reads.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and the gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` (the dispatch is
modeled deeply as ``forwarded``; ``meta.json`` axioms == []), so there is nothing
in that lane for this spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-2905"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). The
# ---- `forwarded` def in the `pure` region uses a one-line `if … then … else …`,
# ---- so this multi-line `let out := if …` / `return out` block is unique. ----
_IMPL_GOLD = (
    "    let out :=\n"
    "      if w.isRecognized then\n"
    "        w.valuesPayload.getD w.obj\n"
    "      else\n"
    "        w.obj\n"
    "    return out"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: prepareData body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a positive control that reshapes the impl or an admissibility case that
# ---- adds an in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). ----
_PROOF_GOLD = (
    "prove_correct prepareData by\n"
    "  loom_solve\n"
    "  simp_all [forwarded]"
)
assert _PROOF_GOLD in _BASE, "proof anchor drift"

# A retuned proof that closes for any reshape observationally equal to gold: it
# case-splits on the single dispatch observable before unfolding. Touches only
# the elided tactic body; the `prove_correct prepareData by` header is unchanged.
_PROOF_CASES = (
    "prove_correct prepareData by\n"
    "  loom_solve\n"
    "  cases h : w.isRecognized <;> simp_all [forwarded]"
)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `prepareDataTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input (the tester
# ---- returns `true` when the precondition fails, so every witness point below
# ---- satisfies the require `isRecognized → valuesPayload.isSome`). Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. Every argument is a concrete literal so `decide`
# ---- reduces fully (Incoming derives DecidableEq, Obj := Nat). ----
_TESTER = (
    "extract_program_for prepareData\n"
    "prove_precondition_decidable_for prepareData\n"
    "prove_postcondition_decidable_for prepareData\n"
    "derive_tester_for prepareData\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `prove_correct` header and only
    # retunes the elided tactic body (a single `cases` on the dispatch
    # observable before unfolding) — the post-image is unchanged on every input.
    # =====================================================================
    {
        "id": "pos-flipped-branch-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the passthrough case first via a negated guard, unwrap in
        # the else. Same forwarded object on every input.
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    let out :=\n"
                  "      if !w.isRecognized then\n"
                  "        w.obj\n"
                  "      else\n"
                  "        w.valuesPayload.getD w.obj\n"
                  "    return out"),
            _PROOF_GOLD, _PROOF_CASES),
        "rationale": "negating the dispatch guard and swapping the two arms leaves "
                     "the forwarded object unchanged on every input, so "
                     "`out = forwarded w` still holds; a correct reshape must "
                     "verify, else SPEC-TOO-STRONG on guard polarity.",
    },
    {
        "id": "pos-match-on-recognized",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the boolean dispatch written as a `match` on the observable
        # instead of an `if`. Order-independent over the two bool constructors,
        # so the returned value is unchanged.
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    let out :=\n"
                  "      match w.isRecognized with\n"
                  "      | true  => w.valuesPayload.getD w.obj\n"
                  "      | false => w.obj\n"
                  "    return out"),
            _PROOF_GOLD, _PROOF_CASES),
        "rationale": "writing the same total dispatch as a `match` on the "
                     "recognized-ness observable returns the same object on both "
                     "cases, so the post-image is unchanged; a correct reshape "
                     "must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method's `require` (isRecognized → valuesPayload.isSome)
    # is satisfied by every F2P-shaped input the tests build, so the usual
    # "a normal input satisfies the precondition" probe is discharged by every
    # reject witness below (each sits at an in-domain point). The residual
    # admissibility risk is that the post-image is DEGENERATE at the interesting
    # point — a spec no impl can meet reads exactly like a spec every impl meets.
    # This case discharges an in-region `assert`, at concrete F2P-shaped points,
    # that the dispatch is NON-DEGENERATE: a NON-recognized value that DOES expose
    # a payload is forwarded UNCHANGED (its identity, NOT the payload — the exact
    # behaviour the failing test demands of an arbitrary object with a `.values`
    # attribute), while a recognized value IS unwrapped to its payload. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof body is retuned only to clear the extra assert goal by
    # `decide` (allowed — the tactic body is elided from the spec view). The
    # assert is live, not decoration: a false claim at those points leaves an
    # unsolved goal.
    # =====================================================================
    {
        "id": "admiss-dispatch-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "    assert (with_name_prefix `admiss\n"
                "      (forwarded { obj := 0, valuesPayload := some 1, isRecognized := false } = 0\n"
                "        ∧ forwarded { obj := 0, valuesPayload := some 1, isRecognized := true } = 1\n"
                "        ∧ forwarded { obj := 0, valuesPayload := some 1, isRecognized := false } ≠ 1))\n"
                + _IMPL_GOLD),
            _PROOF_GOLD,
            "prove_correct prepareData by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [forwarded]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at concrete "
                     "F2P-shaped points: a NON-recognized value that exposes a "
                     "payload forwards to its own identity (and NOT to the payload) "
                     "— the behaviour the failing test demands of an arbitrary "
                     "object with a `.values` attribute — while a recognized value "
                     "unwraps to its payload. The in-region assert must discharge "
                     "(else the obligation is degenerate at the interesting point); "
                     "the impl is kept verbatim so `out = forwarded w` discharges "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-unwrap-on-payload-presence",
        "kind": "uniqueness",
        "expect": "reject",
        # THE F2P rival — the pre-image behaviour: forward the exposed payload
        # whenever one is present, IGNORING whether the object is a recognized
        # container type. On this carrier the sibling's two pre-image rivals
        # (`getattr(data,'values',data)` and unconditional `data = data.values`)
        # COLLAPSE to this single impl: `valuesPayload.getD obj` yields the
        # payload iff present and the object itself otherwise, and there is no
        # separate always-present payload field to distinguish an unconditional
        # unwrap from a presence-guarded one (see accounting note below).
        "module": _swap(_BASE, _IMPL_GOLD,
                        "    let out := w.valuesPayload.getD w.obj\n    return out"),
        "refinement": "this is the pre-image dispatch: an object is replaced by the "
                      "stored values it exposes on the mere PRESENCE of such a "
                      "payload, irrespective of its type. The failing test builds a "
                      "bespoke object that is not a recognized container type yet "
                      "exposes a values payload and asserts it is stored AS ITSELF "
                      "(so it lands in an object-dtype array intact); a faithful "
                      "counterpart that keeps unwrapping on payload presence "
                      "reproduces the pre-image behaviour and replaces that object "
                      "by its payload. It does NOT resolve the F2P.",
        "rationale": "REJECT from the passthrough clause "
                     "(isRecognized = false → out = obj): on a non-recognized value "
                     "that exposes a payload the rival returns the payload, not the "
                     "object. Refuted at exactly that antecedent "
                     "(isRecognized = false, valuesPayload = some _), the only "
                     "sub-domain where the pre-image and the fix diverge.",
        "witness": _TESTER +
                   "example : prepareDataTester "
                   "{ obj := 0, valuesPayload := some 1, isRecognized := false } "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-never-unwrap",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the unwrap entirely: forward the object unchanged always. Correct
        # on every passthrough input; wrong on every recognized container (which
        # must be unwrapped to its payload). Ignores BOTH observables.
        "module": _swap(_BASE, _IMPL_GOLD,
                        "    let out := w.obj\n    return out"),
        "refinement": "never unwrapping means a real patch that DELETED the unwrap "
                      "step; a recognized container type (pd.Series / pd.Index / "
                      "pd.DataFrame) would no longer be reduced to its stored "
                      "values, breaking the pass-to-pass tests that exercise those "
                      "container inputs — a different, non-resolving program.",
        "rationale": "REJECT from the unwrap clause "
                     "(isRecognized = true → out = valuesPayload.getD obj): for a "
                     "recognized value the rival returns the object itself, not its "
                     "payload. Refuted at a recognized value that exposes a payload "
                     "(isRecognized = true) — the mirror antecedent of the prepatch "
                     "rival, so the two do not pin the isRecognized binder.",
        "witness": _TESTER +
                   "example : prepareDataTester "
                   "{ obj := 0, valuesPayload := some 1, isRecognized := true } "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-swapped-arms",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverts the two arms: forward the object on the recognized arm and
        # unwrap on the passthrough arm — both arms individually wrong. A
        # cross-check that neither branch obligation is satisfied by the mirror
        # assignment.
        "module": _swap(_BASE, _IMPL_GOLD,
                        "    let out :=\n"
                        "      if w.isRecognized then\n"
                        "        w.obj\n"
                        "      else\n"
                        "        w.valuesPayload.getD w.obj\n"
                        "    return out"),
        "refinement": "unwrapping the WRONG cases (recognized containers pass "
                      "through, non-recognized payload-bearing objects get "
                      "unwrapped) is the opposite of the fix; it resolves neither "
                      "the F2P nor the pandas pass-to-pass tests.",
        "rationale": "REJECT from the unwrap clause: on a recognized value the rival "
                     "returns the object, not its payload. Refuted at a third "
                     "recognized point with a distinct `obj` (=3) and payload "
                     "(some 7) literal, so the `obj` binder is moved off the value "
                     "the other witnesses hold it at.",
        "witness": _TESTER +
                   "example : prepareDataTester "
                   "{ obj := 3, valuesPayload := some 7, isRecognized := true } "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-always-unwrap-no-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # The UNCONDITIONAL unwrap, as its own rival rather than folded into
        # weak-unwrap-on-payload-presence. Takes the exposed payload with NO
        # fallback to the object at all: when no payload is exposed it forwards a
        # fixed unrelated object instead of the incoming one. Distinct from the
        # presence-guarded rival exactly on the sub-domain where no payload
        # exists, which is where a `getD w.obj` fallback and a hard take differ.
        "module": _swap(_BASE, _IMPL_GOLD,
                        "    let out := w.valuesPayload.getD 0\n    return out"),
        "refinement": "taking the exposed payload unconditionally, with no fallback "
                      "to the incoming object, is the unguarded form of the "
                      "pre-image dispatch: an object that is not a recognized "
                      "container AND exposes no stored values is not forwarded at "
                      "all. A faithful counterpart replaces every such plain object "
                      "with something unrelated to it, so it neither restores the "
                      "passthrough the failing test demands nor keeps the "
                      "pass-to-pass tests that feed ordinary objects through this "
                      "step. It does NOT resolve the F2P.",
        "rationale": "REJECT from the passthrough clause "
                     "(isRecognized = false → out = obj), at the sub-domain the "
                     "other rivals leave unattacked: NO exposed payload "
                     "(valuesPayload = none) on a non-recognized value. Gold "
                     "forwards `obj`; the rival forwards its fallback constant. "
                     "This is the only reject witness that moves the "
                     "`valuesPayload` binder off `some _`, so the manifest no "
                     "longer pins it, and it moves `obj` to a third literal (=5).",
        "witness": _TESTER +
                   "example : prepareDataTester "
                   "{ obj := 5, valuesPayload := none, isRecognized := false } "
                   "= false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 partial-domain rivals)
# over a single-method decision `normalize_self_describing(data)`. This bundle
# models the SAME dispatch as ONE method `prepareData` whose input observables
# (`obj`, `valuesPayload : Option`, `isRecognized : Bool`) are the faithful
# carrier of the sibling's four read-only fields (mapping.md §2): the sibling's
# `exposes_values` boolean + `values_identity` field collapse into the single
# `valuesPayload : Option Obj` (present ↔ some).
#
#   sibling case                            -> here
#   -----------------------------------------------------------------------
#   pos-control-reordered-early-return      -> pos-flipped-branch-...   PORTED
#   pos-control-conditional-expression      -> pos-match-on-recognized  PORTED
#   admiss-self-call-in-domain              -> admiss-dispatch-...       RE-AIMED
#   frame-mutation-overwrite-predicate      -> (none)                   VACUOUS
#   frame-mutation-overwrite-identity       -> (none)                   VACUOUS
#   partial-domain-prepatch-exposes-values  -> weak-unwrap-on-payload-  PORTED
#   partial-domain-always-unwrap            -> weak-always-unwrap-no-fb  PORTED
#   partial-domain-never-unwrap             -> weak-never-unwrap         PORTED
#   partial-domain-swapped-results          -> weak-swapped-arms         PORTED
#
# RE-AIMED (admissibility): the sibling discharges the function's own `Requires`
#   (fractional read permissions + the recognized⇒exposes invariant) via a
#   self-call, proving the precondition admits a normal input. This backend's
#   `require` (isRecognized → valuesPayload.isSome) is satisfied by every reject
#   witness point below (all in-domain), so that probe is already covered; the
#   admissibility case is re-aimed at the residual total-domain risk — that the
#   post-image is DEGENERATE at the interesting point — by asserting in-region,
#   at concrete F2P-shaped points, that a non-recognized payload-bearing value
#   forwards UNCHANGED (not to its payload) and a recognized value unwraps.
#
# VACUOUS (2): frame-mutation-overwrite-{predicate,identity}. The sibling holds
#   each `data.*` at Acc(...,1/2) read-only, so an impl that WRITES the input is
#   rejected by the permission system. This backend is referentially transparent
#   — no heap, no aliasing, no `mut` binder — so there is no read-only carrier to
#   overwrite and no substitute probe. Reported as an omission, not fabricated.
#
# PORTED SEPARATELY (was previously MERGED — corrected): the sibling
#   distinguishes the pre-patch `getattr(data,'values',data)` (unwrap on payload
#   PRESENCE, falling back to the object) from an unconditional `data =
#   data.values` (take the payload, no fallback). An earlier revision of this
#   manifest asserted the carrier COLLAPSES the two, on the ground that the only
#   object available to forward is the one that is present. That is false on this
#   carrier and was measured so: the presence-guarded form is
#   `valuesPayload.getD w.obj`, the unguarded form supplies a fallback that is
#   NOT the incoming object, and the two disagree on every input whose payload is
#   absent. The unguarded rival is therefore carried in its own right as
#   weak-always-unwrap-no-fallback, refuted at (isRecognized = false,
#   valuesPayload = none) — a point no other witness in the battery visits.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# COVERAGE. The single independent top-level clause `out = forwarded w` folds two
#   branch obligations; BOTH are attacked — the passthrough arm
#   (isRecognized = false → out = obj) by weak-unwrap-on-payload-presence, the
#   unwrap arm (isRecognized = true → out = valuesPayload.getD obj) by
#   weak-never-unwrap and weak-swapped-arms, and the passthrough arm again at its
#   EMPTY-payload sub-domain by weak-always-unwrap-no-fallback. Binders moved by
#   the reject witnesses: `isRecognized` ∈ {false, true}; `obj` ∈ {0, 3, 5};
#   `valuesPayload` ∈ {some _, none}. The prepatch and never-unwrap rivals sit at
#   MIRROR recognized-ness points so neither pins the `isRecognized` binder.
#
#   An earlier revision held `valuesPayload` at `some _` in EVERY witness and
#   argued that was not a gap, on the ground that a `none` payload on the
#   non-recognized arm is a sub-domain where the fix and every plausible rival
#   agree. That argument was wrong and is retracted: a rival is expressible there
#   (any impl that forwards something other than `w.obj` when no payload is
#   exposed), the frozen spec does reject it, and the refutation decides by
#   evaluation like the others. weak-always-unwrap-no-fallback occupies exactly
#   that point, so no witness point in this battery pins `valuesPayload` any
#   longer. The one sub-domain that remains unattacked is (isRecognized = true,
#   valuesPayload = none) — and that one is genuinely unattackable, because the
#   method's `require` excludes it from the domain, so an impl free to do anything
#   there is CORRECT and verifies (confirmed by build). pts = 4.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the dispatch is modeled deeply as `forwarded`; meta.json
#   axioms == [], deep_model_references == []), so there is nothing here for this
#   gate to probe.
AXIOM_TESTS = []

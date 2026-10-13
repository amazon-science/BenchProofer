"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24149 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — which the consumer spec view elides — is changed, so
``markers.same_spec`` holds and the ``prove_correct selectReference`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a single read-only input):

  selectReference (xs : List Float) return (out : Except ExtractErr Float)
    require xs ≠ []
    ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))       (C1)

The method picks the representative scalar of a non-empty sequence used as a
reference point. ``firstFinite`` (the first element passing the scalar
finiteness predicate, or ``none`` when every element is non-finite) and
``firstElement`` (the first element taken unconditionally) are fully transparent
``def``s in the ``pure`` region — NOT opaque oracles; the ``axioms`` region
declares no ``axiom``. The single top-level ``ensures`` clause C1 pins THREE
independent facets of the outcome at once, each grounded in the sole input
binder ``xs``:

  (F-ok)  the outcome is always ``Except.ok`` — a value is produced for every
          non-empty input, never the error leg;
  (F-fin) on the common path (a finite element exists, ``firstFinite = some v``)
          the value is that first FINITE element ``v`` — the identity facet, with
          an ORDER sub-facet: it is the FIRST finite element, not merely SOME
          finite one (attacked separately, since a rival can return a wrong value
          that is itself perfectly finite);
  (F-fb)  on the all-non-finite path (``firstFinite = none``) the value is the
          first element ``firstElement xs`` taken unconditionally — the fallback
          facet (the behaviour the fix adds).

F-ok is the discriminating behaviour the public issue reports: on an
all-non-finite input the extraction previously escaped as a raised failure
rather than producing a representative. A wrong rival must violate one of
F-ok / F-fin / F-fb.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling holds its
    coordinate sequence at a fractional heap permission and its MANDATORY frame
    rival overwrites that read-only input to trip INSUFFICIENT PERMISSION. This
    backend is referentially transparent and this bundle declares NO ``mut``
    binder: ``xs`` is an immutable value, there is no heap, no aliasing and no
    permission system to trip. There is no read-only input to overwrite and no
    substitute probe to fabricate, so the class is vacuous (per the porting map,
    legitimately dropped, not faked).
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. C1 is a total function of
    the sole input ``xs`` (``firstFinite`` / ``firstElement`` are concrete
    ``def``s written directly over the carrier, not axiomatized answer-keys the
    impl could echo without doing the work). The cheapest correct impl returns
    ``(firstFinite xs).getD (firstElement xs)`` directly, which the positive
    controls cover honestly. There is no consumed contract to attack.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: ``xs`` is
    observed through ``firstFinite`` (two outcomes: ``some v`` / ``none``) and
    ``firstElement``; a rival right on part of that observation space but
    diverging on a sub-region is the natural falsifier. The four rivals below
    partition the space along F-ok / F-fin (identity AND order) / F-fb.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, and NOT shippable as a
    reject case on this bundle. CORRECTED BY THE THIRD AUDIT: this bundle carries
    ``set_option loom.semantics.termination "total"`` (Solution.lean line 4), NOT
    ``"partial"`` as earlier revisions of this file asserted three times. The
    disposition that error produced was wrong in BOTH halves, so both are restated
    from real builds:

      - The NAIVE diverging rival (correct value, then a measure-less spinning
        loop) is REJECTED, not admitted: the verifier emits `error: Decreasing
        annotations are required in total correctness semantics` (measured, exit
        1). So the nagini ``rival-nonterm-vacuous`` (U5 / the G-PANEL-1 atk_4
        class) is NOT admitted by this spec.
      - It is nevertheless UNSHIPPABLE as a reject case, for a TOOLING reason
        rather than a spec one, and this is the part a reader must not re-derive:
        the termination error fires on the METHOD BODY, i.e. while elaborating the
        module itself, before any appended `example` is reached. Measured: a
        witness file carrying only the tautology ``example : True := trivial``
        against that rival still exits 1 with the SAME decreasing-annotation
        error. So the gate's first half ("the witness ELABORATES against the
        rival") can never be satisfied — no witness whatsoever, honest or forged,
        can elaborate in a file the rival makes uncompilable. Landing it would
        record ``witness-unproven`` and FAIL the gate, so the case is correctly
        absent; the reason is the carrier's file-level rejection, not a missing
        witness idea.

    NOTHING remains open in this class, and this paragraph RETRACTS the narrower
    hole a previous revision escalated in ``spec_holes``. That revision claimed
    that under ``"total"`` the termination obligation is discharged by ANY measure
    expression, the strict-decrease side condition never being proven, and reported
    a rival that spins with an explicit ``decreasing (0 : Nat)`` while returning a
    WRONG value (``Except.ok 0``, ignoring ``xs`` entirely) as VERIFYING CLEANLY at
    exit 0. RE-MEASURED on this bundle with real builds, that shape is REJECTED at
    exit 1 on the MEASURE's own descent goal, ``unsolved goals case
    «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``, and so is a strictly INCREASING
    measure (``decreasing k`` over ``k := k + 1``, leaving ``⊢ k + 1 < k``). The
    side condition IS proven; the escalation is withdrawn and no spec hole is
    reported from this class.
    THE MECHANISM, so the retraction does not rest on one build:
    ``set_option loom.semantics.termination "total"`` (line 4) itself opens the
    ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``, the
    ``openScope `TotalCorrectness`` arm), line 7 opens it again explicitly, and
    ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and emits
    ``⌜measure b' < measure b⌝`` as a goal the proof must discharge. Only the
    ``PartialCorrectness`` twin takes a measure and drops it, which is why the two
    header lines have to move together and do here. The class stays unshipped for
    the TOOLING reason above, on the witness side, not a semantic one.

THE WITNESS ON A `List Float` CARRIER. Concrete ``Float`` literals do NOT reduce
under ``decide`` (measured: ``Float.isFinite 1.0 = true`` leaves the
``Decidable`` instance stuck, so ``firstFinite [1.0]`` never computes), and the
tester route (``derive_tester_for``) needs a decidable postcondition it cannot
synthesise over ``Float`` equality. So a witness cannot pin ``xs`` to a value;
instead it HYPOTHESISES the two observations at a symbolic ``xs``
(``firstFinite xs = …``, and where needed a relation on ``firstElement xs`` —
exactly the sub-region the rival's facet is wrong on) and shows the extracted
program's output differs from the spec's there. Reaching the program uses
Velvet's own extractor: ``extract_program_for`` gives
``selectReferenceExec = NonDetT.run ∘ selectReference``, and
``NonDetT.run (pure x) = DivM.res x``, so the goal is
``selectReferenceExec xs ≠ DivM.res (Except.ok ((firstFinite xs).getD
(firstElement xs)))``. Checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict; each witness (1) elaborates
against the rival and (2) FAILS against the frozen solution — verified during
authoring by two real builds per case. No ``sorry``/``admit``/``native_decide``/
``axiom``: the hypotheses are ordinary equalities/inequalities of the transparent
observations, not assumptions of the conclusion, and each is individually
SATISFIABLE (the consistency probe cannot derive ``False`` from the binders).

WITNESS PLACEMENT / BINDER COVERAGE. Because ``xs`` is observed through
``firstFinite`` and ``firstElement``, "varying the binder" means varying those
observations. The three rivals probe ``firstFinite`` at BOTH its outcomes
(``none`` for F-ok and F-fb, ``some v`` for F-fin) and relate ``firstElement``
to the pinned value on the fallback path, so no observation of the sole input is
held fixed across the battery (three distinct hypothesis regions = three
distinct probe points). Every top-level facet of C1 is attacked by exactly one
rival, and the four positive controls defend the whole obligation.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; both unchanged
element-extraction routines are modeled DEEPLY by the pure ``def``s
``firstFinite`` / ``firstElement``, validated == the real callees by
axiom_check.py under G-AX, which is a separate gate). There is no
axiom-soundness / axiom-containment obligation for this gate to probe here, and
the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24149"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start` / `-- impl-end` region and is unique in Solution.lean
# ---- (both facts asserted at load by _swap). Every SPEC variant reshapes
# ---- exactly one of these, so `same_spec` holds and the obligation survives.

# The frozen straight-line impl body (finite-first, unconditional fallback via
# `Option.getD`). Used by every whole-body reshape (positives + rivals).
_GOLD_BODY = """    let found := firstFinite xs
    let result := found.getD (firstElement xs)
    return Except.ok result"""
assert _BASE.count(_GOLD_BODY) == 1, "frozen impl body drifted from expected text"

# The first executable line of the impl body — for prepending the admissibility
# assert while keeping the frozen body (and thus the frozen proof) verbatim.
_GOLD_BODY_HEAD = "    let found := firstFinite xs"
assert _BASE.count(_GOLD_BODY_HEAD) == 1, "impl-body-head anchor drifted"


def _reshape(new_body):
    """Whole-body impl reshape (frozen `prove_correct` tactic body kept)."""
    return _swap(_BASE, _GOLD_BODY, new_body)


# The frozen obligation's tactic body. `variant_scope` freezes the obligation
# STATEMENT (the `method ... require ... ensures` header, which lives in the
# spec view) but explicitly permits a variant to reprove it, so a reshape whose
# value flow is NOT definitionally the frozen one may supply the extra tactic
# steps its own shape needs. Keeping the header and appending is what makes a
# non-defeq positive control possible at all: without it every positive is
# forced to be defeq to gold, and then it tests nothing (see the audit note at
# the foot of this file).
_GOLD_PROOF = "prove_correct selectReference by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen prove_correct block drifted"


def _reshape_reproved(new_body, extra_tactics):
    """Impl reshape + extra tactic steps appended to the frozen proof."""
    src = _swap(_BASE, _GOLD_BODY, new_body)
    return _swap(src, _GOLD_PROOF, _GOLD_PROOF + "\n" + extra_tactics)


def _assert_in_region(assert_text, extra_tactics):
    """Prepend an in-region `assert` to the frozen body, keeping the body (and
    so C1's own discharge) verbatim, and append the tactics that discharge it."""
    src = _swap(_BASE, _GOLD_BODY_HEAD, assert_text + "\n" + _GOLD_BODY_HEAD)
    return _swap(src, _GOLD_PROOF, _GOLD_PROOF + "\n" + extra_tactics)


# ---- witness preamble. Reaches the rival's extracted program through Velvet's
# ---- extractor and states, at a symbolic `xs` whose observations are fixed by
# ---- hypothesis, that the rival's output differs from the modeled spec value.
# ---- Checked in a file whose `prove_correct` block is stripped.
def _witness(head_binders, tail_tactics):
    return (
        "extract_program_for selectReference\n\n"
        f"example {head_binders} :\n"
        "    selectReferenceExec xs\n"
        "      ≠ DivM.res (Except.ok ((firstFinite xs).getD (firstElement xs)))"
        " := by\n"
        "  unfold selectReferenceExec selectReference\n"
        + tail_tactics)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different but
    # CORRECT impls that MUST verify. If a faithful correct reshape cannot
    # verify, the spec is SPEC-TOO-STRONG. Each keeps the
    # `ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))`
    # obligation and its frozen `loom_solve` proof; only the executable body
    # (elided from the spec view) is reshaped.
    # =====================================================================
    {
        "id": "pos-explicit-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: replace the `Option.getD` fold with an explicit `match` on the
        # finiteness outcome, all-non-finite (`none`) arm written first. Same two
        # legs, same values, different control shape. `loom_solve` still closes
        # (the frozen proof is kept). If it fails to verify the postcondition is
        # over-fit to the `getD` spelling => SPEC-TOO-STRONG.
        "module": _reshape(
            "    let result := match firstFinite xs with\n"
            "      | none => firstElement xs\n"
            "      | some v => v\n"
            "    return Except.ok result"),
        "rationale": "an explicit two-arm match on the finiteness outcome (none "
                     "arm first) computes the same value on both legs as the "
                     "`Option.getD` fold, so C1 (`out = Except.ok "
                     "((firstFinite xs).getD (firstElement xs))`) still holds; a "
                     "correct reshape must verify (else SPEC-TOO-STRONG on the "
                     "`getD`-vs-`match` spelling).",
    },
    {
        "id": "pos-hoisted-fallback",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist the unconditional fallback into a typed local, then
        # decide the leg with an `if` on `Option.isSome` and project with `get!`
        # instead of folding with `getD`.
        #
        # AUDIT REPAIR (was definitionally equal to gold). The previous form only
        # `let`-bound the fallback before the same `getD` fold, which is defeq to
        # the frozen body — measured: `rfl` closes
        #   (let fallback := firstElement xs; (firstFinite xs).getD fallback)
        #     = (firstFinite xs).getD (firstElement xs)
        # so the frozen `loom_solve` discharged it for free and the case could not
        # have detected a spec over-fit to the `getD` spelling. The `isSome`/`get!`
        # shape is NOT defeq (measured: `rfl` FAILS on the corresponding equation,
        # and `loom_solve` alone leaves the unsolved goal
        #   `Except.ok (if (firstFinite xs).isSome = true then (firstFinite xs).get!
        #      else firstElement xs) = Except.ok ((firstFinite xs).getD …)`),
        # so verifying it requires a real case split on the observation. That is
        # what makes this a live SPEC-TOO-STRONG probe rather than a free pass.
        "module": _reshape_reproved(
            "    let found := firstFinite xs\n"
            "    let fallback := firstElement xs\n"
            "    let result := if found.isSome then found.get! else fallback\n"
            "    return Except.ok result",
            "  cases h : firstFinite xs <;> simp [h]\n"),
        "rationale": "deciding the leg with `if (firstFinite xs).isSome` and "
                     "projecting with `get!` — over a hoisted fallback local — "
                     "computes the same value on both legs as the `Option.getD` "
                     "fold, so C1 (`out = Except.ok ((firstFinite xs).getD "
                     "(firstElement xs))`) still holds; a correct reshape must "
                     "verify (else SPEC-TOO-STRONG on the `getD` spelling). Unlike "
                     "the `getD`-preserving hoist this shape is NOT definitionally "
                     "the frozen body, so the obligation is genuinely re-proven by "
                     "a case split on the observation rather than discharged for "
                     "free.",
    },
    {
        "id": "pos-direct-return",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the intermediate lets and return the modeled expression
        # directly. This is the honest cheapest-correct impl and the
        # grounded-oracle stand-in: `firstFinite`/`firstElement` are transparent
        # `def`s, so returning their combination IS the pinned selection (no
        # answer-key to echo). Must verify, else C1 is self-inconsistent
        # (SPEC-TOO-STRONG).
        "module": _reshape(
            "    return Except.ok ((firstFinite xs).getD (firstElement xs))"),
        "rationale": "the straight-line `return Except.ok ((firstFinite xs).getD "
                     "(firstElement xs))` is the simplest correct impl; it meets "
                     "C1 by definitional equality and demonstrates the spec is not "
                     "echo-vulnerable (the only value satisfying C1 is the actual "
                     "selection, grounded in `xs` by transparent defs). If it "
                     "failed to verify C1 would be self-inconsistent => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-all-nonfinite-in-domain",
        "kind": "admissibility",
        "expect": "verify",
        # The regression-shaped input — a single-element all-non-finite
        # coordinate sequence — must be IN-DOMAIN and land on the fallback leg
        # PRODUCING that element, not the error leg. There is no `require` that
        # could exclude it (the only precondition is `xs ≠ []`), so the residual
        # admissibility risk is that the modeled fallback leg is DEGENERATE /
        # unreachable.
        #
        # AUDIT REPAIR (was a tautology). The previous form of this assert read
        #   ∀ ys, firstFinite ys = none → (firstFinite ys).getD (firstElement ys)
        #                                  = firstElement ys
        # which is just `Option.getD_none` after rewriting by the hypothesis: it
        # holds for ANY function substituted for `firstFinite`, including one
        # that is constantly `none` and one that never returns `none` — measured,
        # both discharge. So it constrained `firstFinite` not at all and did not
        # establish that the fallback leg is REACHABLE, which is the only thing
        # this case exists to show.
        #
        # The form below is EXISTENTIAL in the observation instead: for a
        # non-finite scalar `y` it asserts the concrete sequence `[y]` is
        # non-empty (in-domain), that `firstFinite` actually REPORTS `none` there
        # (the fallback leg is genuinely reached — this is the conjunct the old
        # form could not state), and that the pinned value is `y` itself, the
        # sequence's own first element. Measured non-tautological: it FAILS when
        # `firstFinite` is replaced by an always-`some` model (unsolved goal
        # `False`), i.e. it does discriminate a degenerate fallback leg. The
        # frozen body is kept verbatim so C1 still discharges by the frozen
        # `loom_solve`; the appended tactics discharge only the new assert.
        "module": _assert_in_region(
            "    assert (with_name_prefix `adm\n"
            "      (∀ y : Float, isFiniteVal y = false →\n"
            "        [y] ≠ [] ∧ firstFinite [y] = none ∧\n"
            "          (firstFinite [y]).getD (firstElement [y]) = y))",
            "  intro y hy\n"
            "  refine ⟨by simp, ?_, ?_⟩\n"
            "  · simp [firstFinite, List.find?, hy]\n"
            "  · simp [firstFinite, List.find?, hy, firstElement]\n"),
        "rationale": "the regression-shaped input (a one-element all-non-finite "
                     "sequence) is in-domain and the fallback leg is REACHED "
                     "there and produces that element: for a non-finite scalar "
                     "`y`, `[y] ≠ []` (in-domain), `firstFinite [y] = none` (the "
                     "fallback leg is genuinely entered, not degenerate), and the "
                     "pinned value is `y` itself. The in-region assert must "
                     "discharge (else the modeled fallback leg would be "
                     "unreachable / the regression input unmodeled); the frozen "
                     "body is kept verbatim so C1 still discharges too. If it "
                     "failed => PRECOND/DOMAIN-TOO-STRONG. (Non-tautological by "
                     "construction: the `firstFinite [y] = none` conjunct fails "
                     "for an always-`some` model of the observation, which the "
                     "previous `Option.getD_none` restatement could not detect.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete sub-region of the input's observation space, and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test `test_bar_all_nan`.
    # =====================================================================

    # ---- F-ok: the outcome is always a produced value, never the error leg ----
    {
        "id": "weak-no-fallback-raises",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: take the first finite element, and when none
        # is finite propagate the failure as the error leg instead of falling
        # back. Correct on the common (finite) path; wrong exactly on the
        # all-non-finite path, where it raises rather than producing a value.
        "module": _reshape(
            "    let found := firstFinite xs\n"
            "    let result := match found with\n"
            "      | some v => Except.ok v\n"
            "      | none   => Except.error ExtractErr.noFiniteFound\n"
            "    return result"),
        "refinement": "this is the exact pre-change behaviour: no fallback when no "
                      "element is finite, so the extraction escapes as a raised "
                      "failure. On the all-non-finite regression input "
                      "(`ax.bar([np.nan])`) that failure is caught by neither the "
                      "inner nor the outer handler and crashes the bar-drawing "
                      "call — the F2P test `test_bar_all_nan` fails. It would NOT "
                      "resolve (this is the prepatch witness).",
        "rationale": "REJECT from F-ok (`out = Except.ok …`): on an all-non-finite "
                     "input the impl returns the error leg where the post-image "
                     "demands a produced value. Refuted at any `xs` with "
                     "`firstFinite xs = none`. If it verified => SPEC-TOO-WEAK "
                     "(the crash the fix removes would be admitted).",
        "witness": _witness(
            "(xs : List Float) (h : firstFinite xs = none)",
            "  simp [NonDetT.run, pure, h]\n"),
    },

    # ---- F-fin: the common-path value is the first FINITE element ----
    {
        "id": "weak-first-element-always",
        "kind": "uniqueness",
        "expect": "reject",
        # The value/identity attack: return the first element unconditionally,
        # even when a finite element exists further along. Correct on the
        # all-non-finite path (there the first element IS the pinned fallback);
        # wrong exactly on a leading-non-finite-then-finite input, where it
        # anchors on the leading non-finite element instead of the first finite
        # one.
        "module": _reshape(
            "    let result := firstElement xs\n"
            "    return Except.ok result"),
        "refinement": "a counterpart that anchored on the first element "
                      "unconditionally (the fallback extractor on the common "
                      "path) would return the LEADING non-finite coordinate "
                      "instead of the first finite one whenever the sequence "
                      "leads with a non-finite value; the reference point flowing "
                      "through the downstream geometry would be wrong (non-finite "
                      "where a finite value exists), so the value-sensitive bar "
                      "tests still fail. It would NOT resolve.",
        "rationale": "REJECT from F-fin (`firstFinite xs = some v -> value = v`): "
                     "on a leading-non-finite-then-finite input the impl returns "
                     "the first element where the post-image demands the first "
                     "FINITE element `v`. Refuted at any `xs` with `firstFinite xs "
                     "= some v` and `firstElement xs ≠ v`. If it verified => "
                     "SPEC-TOO-WEAK (the identity pin would be vacuous).",
        "witness": _witness(
            "(xs : List Float) (v : Float)\n"
            "    (h1 : firstFinite xs = some v) (h2 : firstElement xs ≠ v)",
            "  simp [NonDetT.run, pure, h1]\n"
            "  exact h2\n"),
    },

    # ---- F-fb: the all-non-finite fallback value is the actual first element --
    {
        "id": "weak-fallback-constant-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # The fallback-value attack (a facet the flag-carrier sibling could not
        # test — there the all-non-finite representative is pinned to 0 by the
        # abstraction, so returning 0 is CORRECT; on this `List Float` carrier the
        # fallback is the actual first element, which is non-finite and generally
        # not 0). Return the finite element when one exists, but a constant 0 on
        # the all-non-finite path. Correct on the common path; wrong exactly when
        # every element is non-finite and the first element is not 0.
        "module": _reshape(
            "    let result := match firstFinite xs with\n"
            "      | some v => v\n"
            "      | none   => (0 : Float)\n"
            "    return Except.ok result"),
        "refinement": "a counterpart that fell back to a fixed constant instead "
                      "of the sequence's actual first element would anchor the "
                      "reference point on the wrong value on the all-non-finite "
                      "path — the regression input's expected representative is "
                      "its own first (non-finite) coordinate, not 0, so the bar "
                      "geometry differs from the expected outcome and the F2P "
                      "test still fails. It would NOT resolve.",
        "rationale": "REJECT from F-fb (`firstFinite xs = none -> value = "
                     "firstElement xs`): on an all-non-finite input whose first "
                     "element is not 0 the impl returns the constant 0 where the "
                     "post-image demands the unconditional first element. Refuted "
                     "at any `xs` with `firstFinite xs = none` and `firstElement "
                     "xs ≠ 0` — the fallback-value sub-region no other rival "
                     "attacks. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(
            "(xs : List Float)\n"
            "    (h1 : firstFinite xs = none) (h2 : (0 : Float) ≠ firstElement xs)",
            "  simp only [NonDetT.run, pure, h1, Option.getD_none]\n"
            "  intro h\n"
            "  exact h2 (by injection (DivM.res.inj h))\n"),
    },

    # ---- F-fin, ORDER sub-facet: it is the FIRST finite element, not just A
    # ---- finite one (ADDED BY AUDIT — no counterpart in the sibling battery) --
    {
        "id": "weak-last-finite-not-first",
        "kind": "uniqueness",
        "expect": "reject",
        # The ORDER attack. `weak-first-element-always` attacks F-fin only where
        # the selected element is NON-finite (it anchors on a leading non-finite
        # value), so a rival that always returns a genuinely FINITE element — just
        # the WRONG one — is not touched by any other case in this battery. This
        # one scans back-to-front and so returns the LAST finite element. Correct
        # on the whole all-non-finite path, and correct on every input with
        # exactly one finite element; wrong exactly when TWO OR MORE elements are
        # finite, where the pinned value is the leftmost and this returns the
        # rightmost. Refuted at e.g. a sequence whose first finite element is not
        # its last (measured inhabited: `firstFinite [1.0, 2.0] = some 1.0` while
        # the reversed scan yields `some 2.0`).
        "module": _reshape(
            "    let result := match (xs.reverse).find? isFiniteVal with\n"
            "      | some v => v\n"
            "      | none   => firstElement xs\n"
            "    return Except.ok result"),
        "refinement": "a counterpart that scanned the sequence back-to-front "
                      "would pick the LAST finite coordinate rather than the "
                      "first whenever two or more coordinates are finite. The "
                      "representative flowing into the downstream geometry would "
                      "then be a different (finite, so not obviously invalid) "
                      "coordinate, shifting the computed span for every ordinary "
                      "multi-element input — the value-sensitive bar tests, which "
                      "the all-non-finite regression does not exercise, still "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from F-fin, ORDER sub-facet (`firstFinite xs = some v "
                     "-> value = v`, where `firstFinite` is the LEFTMOST finite "
                     "element): on an input with two or more finite elements this "
                     "returns the rightmost where the post-image demands the "
                     "leftmost. Refuted at any `xs` whose first finite element `v` "
                     "differs from its last finite element `w`. This is the "
                     "sub-region NO other rival reaches — `weak-first-element-"
                     "always` only diverges where the returned element is itself "
                     "non-finite, so a rival returning the wrong FINITE element "
                     "would otherwise go unattacked. If it verified => "
                     "SPEC-TOO-WEAK (C1 would pin only 'some finite element', not "
                     "the FIRST one).",
        "witness": (
            "extract_program_for selectReference\n\n"
            "example (xs : List Float) (v w : Float)\n"
            "    (h1 : firstFinite xs = some v)\n"
            "    (h2 : (xs.reverse).find? isFiniteVal = some w) (h3 : w ≠ v) :\n"
            "    selectReferenceExec xs\n"
            "      ≠ DivM.res (Except.ok ((firstFinite xs).getD"
            " (firstElement xs))) := by\n"
            "  unfold selectReferenceExec selectReference\n"
            "  simp [NonDetT.run, pure, h1, h2]\n"
            "  exact h3\n"),
    },

    # ---- F-fin, PREDICATE sub-facet: the selector tests FINITENESS, not merely
    # ---- not-being-NaN (ADDED BY THE SECOND AUDIT — no counterpart in the
    # ---- sibling battery, and not reachable by any other case here) ----------
    {
        "id": "weak-not-nan-not-finite",
        "kind": "uniqueness",
        "expect": "reject",
        # The PREDICATE attack. Every other F-fin rival gets the PREDICATE right
        # and the position or the leg wrong; this one scans front-to-back in the
        # correct order and returns a genuinely selected element, but selects on
        # the WEAKER test `x == x` (true for every value except NaN) instead of on
        # finiteness. The two predicates agree on NaN and on every ordinary value
        # and disagree at exactly one place: an INFINITY, which is not NaN
        # (`inf == inf`) yet is not finite either. So the rival is correct on the
        # whole all-non-finite-by-NaN path and on every input free of infinities,
        # and wrong exactly when an infinity precedes the first finite element,
        # where it anchors on the infinity.
        #
        # Measured NOT subsumed: the frozen spec rejects this rival (exit 1) and
        # NONE of the four witnesses above refutes it (all four fail against it,
        # exit 1 each) — they pin the leg, the position and the fallback value,
        # none of them the predicate. Without this case C1 could be read as
        # pinning "the first non-NaN element" rather than the first FINITE one.
        # Hypothesis region measured inhabited at a concrete leading-infinity
        # sequence (`firstFinite [i, v] = some v` while the not-NaN scan yields
        # `some i`).
        "module": _reshape(
            "    let result := match xs.find? (fun x => x == x) with\n"
            "      | some v => v\n"
            "      | none   => firstElement xs\n"
            "    return Except.ok result"),
        "refinement": "a counterpart whose scalar test rejected only not-a-number "
                      "values while accepting the infinities would, on a sequence "
                      "whose leading coordinate is infinite, anchor the reference "
                      "point on that infinity instead of on the first genuinely "
                      "finite coordinate. The downstream geometry would then be "
                      "computed from a non-finite representative — an infinite "
                      "span rather than a real one — so the value-sensitive bar "
                      "tests (which the all-non-finite regression does not "
                      "exercise) still fail. It would NOT resolve.",
        "rationale": "REJECT from F-fin, PREDICATE sub-facet (`firstFinite xs = "
                     "some v -> value = v`, where the selection test is "
                     "FINITENESS, not merely being non-NaN): on an input whose "
                     "first non-NaN element is an infinity preceding the first "
                     "finite element, this returns the infinity where the "
                     "post-image demands the first FINITE element. Refuted at any "
                     "`xs` whose finiteness scan and not-NaN scan disagree. This "
                     "is the sub-region NO other rival reaches — the other three "
                     "F-fin/F-fb rivals all select on the right predicate and get "
                     "the leg, the position or the fallback value wrong. If it "
                     "verified => SPEC-TOO-WEAK (C1 would pin only 'the first "
                     "non-NaN element', admitting an infinite representative).",
        "witness": _witness(
            "(xs : List Float) (v w : Float)\n"
            "    (h1 : firstFinite xs = some v)\n"
            "    (h2 : xs.find? (fun x => x == x) = some w) (h3 : w ≠ v)",
            "  simp [NonDetT.run, pure, h1, h2]\n"
            "  exact h3\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (4 positive
# controls — 3 soundness + 1 admissibility — and 5 uniqueness/frame rivals) plus
# 4 AXIOM_TESTS. Every SPEC case is accounted for below.
#
# CARRIER NARROWING. The sibling contracts TWO structurally-identical functions
# `select_position_x0` / `select_position_xconv` over a `List[int]` finiteness-
# FLAG carrier (0 == non-finite, non-zero == finite), pinning the result to the
# first-finite value via @Pure folds plus two @ContractOnly axioms, under a
# read-only half-permission and a MustTerminate(2) total-correctness obligation.
# This bundle models the single purely-functional CORE — the per-sequence
# element-extraction step — over the RICHER `List Float` carrier, with the two
# extractors modeled DEEPLY as transparent `def`s (`firstFinite` / `firstElement`)
# and one method `selectReference`. The two functions collapse to one (they were
# byte-identical), and the half-permission machinery has no counterpart on a
# referentially-transparent backend. The sibling's MustTerminate(2) obligation DOES
# have a counterpart here — this bundle's `termination "total"` — which is why the
# non-termination class is restated below as "not shippable for a tooling reason"
# rather than as a spec hole (the third audit's correction).
#
#   sibling case (nagini)              -> here                              status
#   ---------------------------------------------------------------------------
#   pos-control-reordered              -> pos-explicit-match                RESHAPED
#   pos-control-local                  -> pos-hoisted-fallback              RESHAPED
#   pos-fold-grounded                  -> pos-direct-return                 RE-EXPR
#   admiss-f2p-all-nan                 -> admiss-all-nonfinite-in-domain    RE-AIMED
#   rival-frame-mutation (MANDATORY)   -> (none)                           VACUOUS
#   rival-prepatch-no-fallback         -> weak-no-fallback-raises          PORTED
#   rival-wrong-selector-leading-nan   -> weak-first-element-always        PORTED
#   rival-inverted-guard               -> (subsumed)                       SUBSUMED
#   rival-nonterm-vacuous              -> (none, SPEC-CLOSED)          NO WITNESS
#
# 3 reshaped/re-expressed positives + 1 re-aimed admissibility + 2 ported rivals
# + 3 ADDED rivals (weak-fallback-constant-zero, weak-last-finite-not-first and
# weak-not-nan-not-finite, none with a sibling counterpart) = 9 SPEC cases;
# 1 vacuous, 1 subsumed, 1 closed by the semantics and unwitnessable.
#
# ------------------------------------------------------------------------------
# INDEPENDENT AUDIT (post-port). Three defects were found and repaired here; the
# frozen artifact was not touched. Recorded so the next reader does not have to
# re-derive them:
#
#  1. admiss-all-nonfinite-in-domain was a TAUTOLOGY. Its assert restated
#     `Option.getD_none` after rewriting by its own hypothesis, so it discharged
#     for ANY model of the observation — measured: it still discharges when
#     `firstFinite` is replaced by a constantly-`none` function AND by an
#     always-`some` one. It therefore never established the thing the case
#     exists to establish, that the fallback leg is REACHABLE. Repaired to an
#     existential form over a concrete one-element sequence that asserts
#     `firstFinite [y] = none` outright; measured non-tautological (it FAILS,
#     unsolved goal `False`, against the always-`some` model). The in-region
#     assert mechanism was confirmed LIVE first: a deliberately false claim
#     (`firstFinite ys = none → firstElement ys = 0`) leaves an unsolved goal.
#
#  2. pos-hoisted-fallback was DEFINITIONALLY EQUAL to the frozen body — `rfl`
#     closes its body against gold's, so the frozen `loom_solve` discharged it
#     for free and it could not detect the over-fit it claimed to test. Repaired
#     to an `isSome`/`get!` shape that is measurably NOT defeq (`rfl` fails;
#     `loom_solve` alone leaves an unsolved goal) and so is genuinely re-proven.
#     pos-direct-return is also defeq to gold and is KEPT deliberately: it is the
#     cheapest-correct/echo control, whose whole point is that the modeled
#     expression itself is admissible.
#
#  3. The F-fin lane had a GAP. `weak-first-element-always` diverges from C1 only
#     where the value it returns is itself NON-finite, so a rival returning the
#     wrong but genuinely FINITE element was unattacked — C1 could have been read
#     as pinning "some finite element" rather than the FIRST. Closed by the added
#     weak-last-finite-not-first (back-to-front scan), whose witness was built
#     and checked by the audit: it elaborates against the rival (exit 0) and
#     FAILS on the frozen solution (exit 1) with a SEMANTIC error (`h3 : w ≠ v`
#     offered where `False` is required, i.e. gold agrees at that point), and its
#     consistency probe cannot derive `False` (exit 1).
#
# SECOND INDEPENDENT AUDIT (post-port, post-first-audit). Every claim recorded
# above was RE-DERIVED with real builds rather than trusted, and all of them held:
# the four reject witnesses each elaborate against their rival (exit 0) and fail
# against the frozen solution (exit 1); the two `Type mismatch` gold-side
# signatures were additionally subjected to the FORGERY test (attack B'), and
# gold's exit code tracks the claim — flipping each witness's claim to assert the
# frozen impl is CORRECT at that point makes gold's build SUCCEED (exit 0) while
# the same flipped claim FAILS against the rival (exit 1), so the signatures are
# genuine refutations and not claim-independent noise. The three repairs the first
# audit recorded were independently confirmed real: the old admissibility form
# does hold for an ARBITRARY model of the observation (exit 0 with `g` universally
# quantified) while the repaired form does NOT (exit 1), `rfl` does fail on the
# `isSome`/`get!` body against gold's, and the assert lane is live (a deliberately
# false in-region claim leaves an unsolved goal). The four witness hypothesis
# regions were shown positively INHABITED at concrete sequences (attack C), so no
# rival is vacuous. `Float` literals were re-confirmed irreducible
# (`Float.isFinite 1.0 = true` is an unsolved goal), which is what forces the
# hypothesis-conditioned witness form.
#
# It found ONE real gap, now closed: the PREDICATE facet of F-fin. All four
# existing rivals select on the right predicate and err in the leg, the position
# or the fallback value, so a rival selecting on the WEAKER not-a-number test
# (`x == x`, which accepts the infinities) was unattacked — measured: the frozen
# spec rejects it (exit 1) yet none of the four shipped witnesses refutes it (all
# four fail against it). C1 could therefore have been read as pinning "the first
# non-NaN element" rather than the first FINITE one. Closed by the added
# weak-not-nan-not-finite, whose witness was built by the audit: exit 0 against
# the rival, exit 1 against the frozen solution, consistency probe cannot derive
# `False` (exit 1), and the flipped claim builds on gold (exit 0).
#
# Attack E was re-run with a MAXIMALLY different correct reshape the battery did
# not contain — a hand-rolled `let rec` scan replacing the library `List.find?`,
# proven equal to `firstFinite` by induction — and it VERIFIES (exit 0), so the
# spec is not over-fit to the library scan. An impl behaving arbitrarily OUTSIDE
# the precondition (error leg on the empty list) also verifies, confirming
# `require xs ≠ []` is genuinely consumed rather than decorative; and an
# `Option.elim` reshape and a precondition-consuming `head!` fallback both verify.
# The dropped sibling `rival-inverted-guard` was rebuilt to check the SUBSUMED
# claim rather than accept it: the frozen spec rejects it (exit 1) and it is
# refuted by BOTH shipped witnesses it is claimed to be subsumed by (F-ok and
# F-fin, exit 0 each), so it adds no distinct probe point and the drop is honest.
#
# Attack D (tuned wrong impls) found NO spec hole: four new rivals the battery
# did not contain — error leg on the FINITE path, last-finite instead of first,
# fallback to the LAST element instead of the first, and the sibling's
# inverted-guard shape — were all REJECTED by the frozen spec (exit 1 each).
# Attack E (correct reshapes) found NO soundness hole: `Option.elim` and
# `if isSome then get!` reshapes both VERIFY once their own tactic tail is
# supplied (exit 0 each), which `variant_scope` permits since only the
# obligation's STATEMENT is frozen. Every witness's hypotheses were additionally
# shown POSITIVELY inhabited at concrete inputs (the one-element all-non-finite
# sequence for F-ok/F-fb; a leading-non-finite-then-finite pair for F-fin; a
# two-finite-element sequence for the order facet) — a stronger check than the
# gate's probe, which only fails a witness whose binders are refutably
# contradictory.
#
# THIRD INDEPENDENT AUDIT (post-port, post-second-audit). Every shipped case was
# rebuilt from scratch; all 9 reproduced their declared outcome (4 positives exit
# 0, 5 rivals exit 1). Attack A (statement integrity) is CLEAN: the spec view
# outside the impl region is byte-identical to the frozen file for all 9 cases,
# and the `method … require … ensures … do` header is byte-identical for all 9 —
# the only two out-of-region deltas are the appended tactic lines that
# `variant_scope` explicitly permits (pos-hoisted-fallback, admiss-*), and neither
# touches the statement. Attack B: each of the 5 witnesses rebuilt to exit 0 on
# its rival, exit 1 on gold, with the consistency probe unable to derive `False`
# (exit 1). Attack B' (FORGERY) was run on ALL FIVE, not only the `Type mismatch`
# pair, and gold's exit code tracks the claim in every case: flipping the claim
# from `≠` to `=` makes gold BUILD (exit 0) and the rival FAIL (exit 1), five for
# five — so no signature is claim-independent noise and no case is hollow.
# The two prior repairs were re-confirmed by direct defeq probes: the old hoist
# body IS defeq to gold (`rfl` closes it, exit 0 — the repair was needed) and the
# shipped `isSome`/`get!` body is NOT (`rfl` fails, exit 1 — the repair is real).
# The admissibility assert is live and non-tautological: substituting an
# always-`some` model of the observation makes it FAIL (exit 1) while the
# constantly-`none` model passes (exit 0), so the `firstFinite [y] = none` conjunct
# does discriminate a degenerate fallback leg; a deliberately false in-region claim
# (`firstElement [y] = 0`) also fails (exit 1), confirming the assert mechanism
# carries signal. `Float` irreducibility re-confirmed (`decide` fails on
# `Float.isFinite 1.0 = true`), which is what forces the hypothesis-conditioned
# witness form.
#
# It found ONE defect, now repaired, and it was in the PROSE rather than in a case:
# this file asserted three times that the bundle carries `termination "partial"`
# when Solution.lean line 4 reads `"total"`, and used that false premise to record
# the non-termination class as a spec hole that ADMITS a diverging rival. Both
# halves were wrong (the naive diverging rival is REJECTED, exit 1) and the real
# reason the case cannot ship is a tooling one (the termination error makes the
# rival's file uncompilable, so even `example : True := trivial` fails against it,
# exit 1). Restated from builds in the header and in the accounting block below.
# Attacks D and E were re-run and found NO new hole: six further wrong impls
# (error leg on the finite path, last-element fallback, a singleton-input domain
# carve-out, a `headD` spelling of first-element-always, a non-finite-to-zero
# clamp, and the faithful both-legs-wrong inverted guard) were ALL rejected (exit
# 1 each); three further correct reshapes (`Option.elim`, an `orElse` fold, and a
# `headD`-spelled fallback) and an impl behaving arbitrarily outside the
# precondition ALL verify (exit 0 each). The one "genuine hole" that pass recorded,
# the non-decreasing-measure class, has since been RE-MEASURED and RETRACTED: the
# `decreasing (0 : Nat)` spinner is rejected at exit 1 on `|- 0 < 0`, so no spec
# hole is escalated from this cell at all (see the DIVERGENCE block below).
# ------------------------------------------------------------------------------
#
# RESHAPED / RE-EXPRESSED (positives): the sibling's two reshape positives
#   (invert the guard so the fallback branch is tested first; hoist the guard
#   predicate into a typed local) map to pos-explicit-match (explicit two-arm
#   match, none-arm first) and pos-hoisted-fallback (hoist the fallback into a
#   local). The sibling's pos-fold-grounded returns the @Pure fold directly in
#   the finite branch to show the P1 oracle is grounded, not echo-able; here
#   `firstFinite`/`firstElement` are transparent `def`s (no oracle at all), so
#   the analog is pos-direct-return, which returns the modeled expression
#   directly — the honest cheapest-correct impl.
# RE-AIMED (admissibility): the sibling asserts the F2P-shaped all-non-finite
#   input (`[0]`) satisfies every value precondition and sits in the fallback
#   branch, using an assert-style probe (a self-call being blocked by
#   MustTerminate). This method has only `require xs ≠ []`, so nothing could
#   exclude the input; the residual risk is a DEGENERATE fallback leg. Re-aimed
#   to assert that on every all-non-finite input the fallback leg produces the
#   unconditional first element (a value, not the error leg) — the regression
#   the fix targets is modeled and reachable.
# PORTED (rivals): weak-no-fallback-raises is the sibling's prepatch rival
#   (F-ok / the error leg the missing fallback re-introduces — the exact crash
#   the F2P test checks). weak-first-element-always is the sibling's
#   wrong-selector rival (F-fin / anchoring on the leading non-finite element
#   instead of the first finite one — the P1 identity attack).
# ADDED (weak-fallback-constant-zero): the F-fb fallback-VALUE facet. On the
#   sibling's flag carrier the all-non-finite representative is pinned to 0 by
#   the abstraction, so `rep = 0` is CORRECT there and the facet is unattackable
#   (the sibling says so explicitly). On this `List Float` carrier the fallback
#   is the actual first element (a non-finite float, generally not 0), so the
#   facet IS attackable and MUST be attacked or a rival that fell back to a fixed
#   constant would verify while breaking the value-sensitive regression. Not a
#   fabricated wrongness — a real F-fb divergence with a machine-checked witness
#   and a refinement argument (a constant fallback anchors the bar on the wrong
#   coordinate).
# SUBSUMED (rival-inverted-guard): the sibling's inverted-guard rival trips TWO
#   rejection sources at once — the missing-fallback crash on the all-non-finite
#   path AND the wrong-selector on the finite path. On this deep model those two
#   surfaces are exactly weak-no-fallback-raises (F-ok) and weak-first-element-
#   always (F-fin), so it adds no distinct probe point.
#   RE-DERIVED BY THE THIRD AUDIT rather than accepted, because the faithful shape
#   matters and an earlier audit's rebuild used a variant that was actually CORRECT
#   on the `none` leg. The faithful inverted guard is
#       match firstFinite xs with
#       | some _ => Except.ok (firstElement xs)          -- F-fin wrong
#       | none   => Except.error ExtractErr.noFiniteFound -- F-ok wrong
#   i.e. wrong on BOTH legs. Measured: the frozen spec REJECTS it (exit 1), and it
#   is refuted by BOTH shipped witnesses it is claimed to be subsumed by — the
#   F-ok witness (exit 0) and the F-fin witness (exit 0). Each of those two
#   refutations happens at the SAME sub-region and for the SAME reason as in the
#   case that already ships it, so shipping the combined rival would duplicate two
#   existing probe points rather than add one. The drop is therefore honest.
# VACUOUS (rival-frame-mutation, MANDATORY on nagini): the sibling overwrites the
#   read-only input held at a fractional heap permission to trip INSUFFICIENT
#   PERMISSION before any postcondition is considered. This backend is
#   referentially transparent: `xs` is an immutable value, this bundle declares
#   NO `mut` binder, there is no heap, no aliasing and no permission system.
#   There is no read-only input to overwrite and no substitute probe to build, so
#   the class is vacuous (per the porting map, legitimately dropped, not
#   fabricated). Its ARGUMENT (a patch mutating the caller's coordinate array in
#   place would corrupt the rendered geometry) has no value footprint the spec
#   can force here — `selectReference` is read-only by construction, returning a
#   fresh `Except` value.
# NOT SHIPPABLE (rival-nonterm-vacuous, U5) — restated by the THIRD AUDIT, which
#   found the previous entry factually wrong about this bundle's own semantics.
#   This bundle carries `termination "total"`, not `"partial"`. Consequences,
#   both measured:
#     * The naive rival (correct value, then a measure-less spinning loop) is
#       REJECTED (exit 1, `Decreasing annotations are required in total
#       correctness semantics`) — so the spec does NOT admit it and the old
#       "SPEC HOLE / the frozen spec ADMITS the rival" claim was false.
#     * It still cannot ship as a reject case, but for a TOOLING reason: the
#       termination error fires while elaborating the METHOD BODY, so the file is
#       uncompilable before any appended `example` runs. A witness carrying only
#       `example : True := trivial` against that rival ALSO exits 1 with the same
#       error (measured), so the gate's "witness elaborates against the rival"
#       half is unsatisfiable for every possible witness. Landing it would record
#       `witness-unproven` and FAIL the gate.
#     * The SHARPER rival, the one that cannot be dismissed as merely missing the
#       annotation, CARRIES a measure that does not decrease. It is REJECTED TOO,
#       at exit 1, on the MEASURE's own descent goal:
#           unsolved goals
#           case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#       and a strictly INCREASING measure fares the same way (`decreasing k` over
#       `k := k + 1` leaves `|- k + 1 < k`).
#   RETRACTION. A previous revision recorded that second shape as VERIFYING at
#   exit 0 and escalated it in the audit payload's `spec_holes` as a narrower
#   residual hole ("`total` discharges the termination obligation with ANY measure
#   expression; the strict-decrease side condition is never proven"), reporting a
#   spinner with `decreasing (0 : Nat)` returning the WRONG `Except.ok 0`. The
#   builds above withdraw that: the side condition IS proven and the constant
#   measure fails it. Nothing from this class is escalated.
#   Mechanism, so this does not rest on one build: line 4's
#   `set_option loom.semantics.termination "total"` itself opens the
#   `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`, the
#   `openScope `TotalCorrectness` arm), line 7 opens it again, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#   `measure b' < measure b` as a goal the proof must discharge; only the
#   `PartialCorrectness` twin takes a measure and discards it.
#
# BINDER / CLAUSE COVERAGE. The sole input binder is `xs`; the single top-level
#   clause C1 folds three facets (F-ok: outcome is a produced value; F-fin: the
#   common-path value is the first finite element — with an ORDER sub-facet, that
#   it is the FIRST such element and not merely a finite one, and a PREDICATE
#   sub-facet, that the test is FINITENESS and not merely being non-NaN; F-fb: the
#   all-non-finite fallback value is the actual first element). C1 is DEFENDED by
#   the four positive controls and ATTACKED at every facet: F-ok by
#   weak-no-fallback-raises, F-fin by weak-first-element-always (identity, where
#   the wrong value is non-finite), by weak-last-finite-not-first (order, where
#   the wrong value IS finite) and by weak-not-nan-not-finite (predicate, where
#   the selector accepts an infinity), F-fb by weak-fallback-constant-zero. `xs`
#   is observed through `firstFinite` at BOTH outcomes (`none` for the F-ok and
#   F-fb rivals, `some v` for the three F-fin rivals), through `firstElement`
#   (related to the pinned value on the F-fb path), through the back-to-front scan
#   (the order facet) and through the weaker not-NaN scan (the predicate facet),
#   so no observation of the input is pinned across the battery —
#   five DISTINCT hypothesis regions (pts=5): {firstFinite = none},
#   {firstFinite = some v ∧ firstElement ≠ v}, {firstFinite = none ∧
#   firstElement ≠ 0}, {firstFinite = some v ∧ reverse-scan = some w ∧ w ≠ v},
#   {firstFinite = some v ∧ not-NaN-scan = some w ∧ w ≠ v}.
#   Every witness's binders are jointly SATISFIABLE (the consistency probe cannot
#   derive `False`) and, checked additionally by the audit, positively INHABITED
#   at concrete inputs.
#
# WITNESS FORM. Concrete `Float` literals do not reduce under `decide` and the
#   tester route needs a `DecidableEq Float` postcondition it cannot synthesise,
#   so every witness CONDITIONS on the two transparent observations at a symbolic
#   `xs` (see the header). Each witness `extract_program_for`s `selectReference`
#   (extraction needs no decidability), fixes the observations by hypothesis, and
#   states the extracted output differs from the modeled spec value there.
#   Confirmed empirically during authoring (and re-checked by the gate's two
#   builds per reject case): each witness ELABORATES against its rival and FAILS
#   against the frozen solution; no `sorry`/`admit`/`native_decide`/`axiom`.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the `axioms` region is empty — the extractors are
#   modeled directly by the transparent `def`s `firstFinite` / `firstElement`,
#   validated == the real callees by axiom_check.py under the separate G-AX gate),
#   so there is nothing here for this gate to probe.
AXIOM_TESTS = []

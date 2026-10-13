"""properties.py — G-PBT falsification battery for astropy__astropy-7606 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct compareName`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over two input binders — the receiver's
own identifying name ``selfName`` and the three-valued interpretation outcome
``outcome`` of the arbitrary operand). The comparison hands back a verdict:

    compareName (selfName : List Char) (outcome : InterpretOutcome)
        return (out : Except CmpErr Verdict)
      (P1) ensures out = compareSpec selfName outcome
      (P2) ensures ∃ v, out = Except.ok v
      (P3) ensures outcome = .uninterpretable → out = Except.ok .deferred
      (P4) ensures ∀ name, outcome = .sameKind name →
                     out = Except.ok (.decided (decide (selfName = name)))
      (P5) ensures outcome = .otherKind → out = Except.ok (.decided false)

``compareSpec`` is a fully unfolded ``def`` in the ``pure`` region: an
uninterpretable operand yields ``deferred`` (the interpretation failure is
absorbed, NEVER escaping as an error), a same-kind operand compares equal iff
the two names coincide, a different-kind operand is unequal. There is NO opaque
answer key to echo — the load-bearing oracle is a total function of the method's
OWN inputs, so a faithful case-for-case dispatch IS the correct impl and any
divergent verdict fails the postcondition.

The load-bearing clause (the one that senses the modeled change) is P3 together
with P2: an operand the interpreter cannot denote must produce the graceful
DECLINE (``deferred`` / ``Except.ok``), never an escaped error and never a
definite verdict. The pre-image lets the interpretation failure escape as an
error; the desired behaviour absorbs it. P4 additionally pins the same-kind
verdict to NAME AGREEMENT (sensitive to both ``selfName`` and the bound
``name``), and P5 pins the different-kind verdict to ``false``.

CARRIER NOTE (decisive for the witness route). Every carrier here is TRANSPARENT:
``InterpretOutcome`` / ``Verdict`` / ``CmpErr`` carry ``DecidableEq`` and
``compareSpec`` is a concrete ``def``, so a rival's violation reduces to a
decidable equality of concrete values. HOWEVER, the two quantified/∃ clauses
(P2 ``∃ v``; P4 ``∀ name``) make ``prove_postcondition_decidable_for`` fail — the
tester route (``derive_tester_for`` → ``…Tester args = false``) is UNAVAILABLE
here (measured: the ∃/∀ clauses leave unsolved ``Decidable`` goals, exactly the
django__django-11964 situation). So each witness instead refutes the method's
Hoare triple DIRECTLY at a concrete input:
``¬ triple True (compareName selfName outcome) (fun out => P1 ∧ … ∧ P5)`` closed
by ``unfold compareName; simp [triple, pure, compareSpec] <;> decide``. Every
witness was SEEN to discriminate — it ELABORATES against the rival (EXIT 0) and
FAILS against the frozen solution (EXIT 1), with two real builds per case. The
witness heads bind nothing beyond concrete literals, so there is no consistency
obligation to satisfy.

WHY ``compareSpec`` IS IN THE SIMP SET (this is load-bearing, not cosmetic).
Without it the P1 conjunct ``out = compareSpec selfName outcome`` survives
``simp`` as an UNREDUCED application, and the two consequences were both measured:
  * against the frozen solution the leftover goal is a false
    ``¬ (Except.ok … = compareSpec … )`` whose ``Decidable`` instance cannot be
    synthesised, so the gold-side build fails with ``failed to synthesize
    Decidable`` — a STUCK UNFOLDING rather than a decided refutation. The gate
    reads any gold-side failure as "gold satisfies the spec here", so that exit
    code attested to a refutation the kernel never performed.
  * P1 was consequently INERT: a rival violating ONLY P1 (every other clause
    satisfied) produced a witness that failed against the RIVAL too — measured,
    exit 1 — i.e. the case would have landed as ``witness-unproven``
    (inconclusive), not as a refutation.
With ``compareSpec`` unfolded, every gold-side build instead fails with
``Tactic `decide` proved that the proposition False is false`` — a SEMANTIC
refutation of the concrete claim — and the P1-only rival is refuted at exit 0.
Re-measured after the change: 5 rival builds exit 0, 5 gold builds exit 1 by
decided refutation, and 14 forgeries stating the same template at points where
each rival is CORRECT all exit 1, so the template tracks truth rather than shape.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling notes NO read-only
    ``Acc(x,1/2)`` input exists even there (``self``/``other`` are plain value
    booleans); on this referentially-transparent backend ``selfName`` and
    ``outcome`` are immutable values, no ``mut`` binder is declared, there is no
    heap and no aliasing — so there is no read-only input to overwrite and no
    substitute probe to build. Not fabricated (per the porting map).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
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
  * SOUNDNESS / positive controls — APPLY. A structurally different but faithful
    dispatch must still verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY — the nagini sibling self-calls to show the precondition ADMITS
    a normal F2P-shaped input. This bundle carries NO ``require`` clause (the
    comparison is total), so that probe is degenerate; the case is RE-AIMED at
    the residual admissibility risk on a transparent carrier — that the post-image
    is DEGENERATE (does not actually demand the graceful decline on the
    uninterpretable arm, name-agreement on the same-kind arm, and ``false`` on the
    different-kind arm). An in-region assert pins all three arms (and the
    name-sensitivity of the same-kind arm) at F2P-shaped points; the impl is kept
    verbatim so the method's own obligation still discharges.
  * UNINTERPRETABLE-ARM / VALUE rivals — APPLY: the escaped-error pre-image, a
    definite verdict on the uninterpretable arm, a name-insensitive same-kind
    verdict, and a wrong different-kind verdict.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` — the
interpretation callee is modeled as a FREE input owed no contract (the
postconditions hold for EVERY value of ``outcome``), and the comparison itself is
modeled DEEPLY as ``compareSpec``. The nagini file's AXIOM_TESTS drive the REAL
post-patch dunders in Docker (G-AX's job); this gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7606"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (dispatch on the outcome, return it).
_IMPL = (
    "    let result : Except CmpErr Verdict :=\n"
    "      match outcome with\n"
    "      | .uninterpretable => Except.ok .deferred\n"
    "      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))\n"
    "      | .otherKind       => Except.ok (.decided false)\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the (retuned) proof without disturbing the obligation.
_IMPL_TOP = "    let result : Except CmpErr Verdict :="
assert _BASE.count(_IMPL_TOP) == 1, "impl top-line drifted from expected text"

# Individual match arms (each unique, wholly inside the impl region). The
# single-arm rivals swap exactly one.
_ARM_UNINTERP = "      | .uninterpretable => Except.ok .deferred"
assert _BASE.count(_ARM_UNINTERP) == 1, "uninterpretable arm not unique"
_ARM_SAME = "      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))"
assert _BASE.count(_ARM_SAME) == 1, "sameKind arm not unique"
_ARM_OTHER = "      | .otherKind       => Except.ok (.decided false)"
assert _BASE.count(_ARM_OTHER) == 1, "otherKind arm not unique"

# The FULL frozen proof body. A positive that reshapes the impl may retune this;
# the tactic body is elided from the spec view, so it is a proof reshape, not a
# spec change. Unique in the file.
_PROOF = "prove_correct compareName by\n  loom_solve\n  cases outcome <;> simp_all"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _with_impl(new_impl: str) -> str:
    return _swap(_BASE, _IMPL, new_impl)


# ---- WITNESSES. The spec is a `method` CONTRACT whose ∃/∀ `ensures` clauses
# ---- make `prove_postcondition_decidable_for` fail, so the tester route is
# ---- unavailable (measured). Each witness refutes the method's Hoare triple
# ---- DIRECTLY at one concrete input, checked in a file whose `prove_correct`
# ---- block has been stripped so no tactic script can mask the verdict.
# ---- `triple`/`pure` come from the frozen `Velvet.Std` import; the head binds
# ---- only concrete literals, so there is no consistency obligation.
def _witness(self_name: str, outcome: str) -> str:
    return (
        f"example : ¬ triple (l := Prop) (True)\n"
        f"    (compareName {self_name} {outcome})\n"
        f"    (fun out => out = compareSpec {self_name} {outcome}\n"
        f"      ∧ (∃ v, out = Except.ok v)\n"
        f"      ∧ ({outcome} = .uninterpretable → out = Except.ok .deferred)\n"
        f"      ∧ (∀ name, {outcome} = .sameKind name →\n"
        f"          out = Except.ok (.decided (decide ({self_name} = name))))\n"
        f"      ∧ ({outcome} = .otherKind → out = Except.ok (.decided false))) := by\n"
        f"  unfold compareName\n"
        f"  simp [triple, pure, compareSpec] <;> decide\n"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG. Each keeps the five `ensures` obligations and only reshapes
# the executable surface (+ its elided proof body where needed).
# ===========================================================================

# Reorder the dispatch arms (decide the two definite kinds first, decline last).
# Same verdict on every (selfName, outcome); the frozen `cases outcome <;>
# simp_all` still closes the byte-identical obligation. Ports the nagini
# pos-control "different control shape, same behaviour" argument.
_POS_REORDER_BODY = (
    "    let result : Except CmpErr Verdict :=\n"
    "      match outcome with\n"
    "      | .sameKind name   => Except.ok (.decided (decide (selfName = name)))\n"
    "      | .otherKind       => Except.ok (.decided false)\n"
    "      | .uninterpretable => Except.ok .deferred\n"
    "    return result"
)

# Factor the common `Except.ok` wrapper out of every arm: build the bare
# `Verdict` by cases, then wrap once on return. A different data-flow shape (the
# error-carrier is introduced once, not per-arm) computing the same result. The
# frozen proof's trailing `cases outcome <;> simp_all` is now redundant (the goal
# closes under `loom_solve` alone), so the proof body is retuned to just
# `loom_solve` — a proof reshape, the spec view is untouched.
_POS_FACTOR_BODY = (
    "    let verdict : Verdict :=\n"
    "      match outcome with\n"
    "      | .uninterpretable => .deferred\n"
    "      | .sameKind name   => .decided (decide (selfName = name))\n"
    "      | .otherKind       => .decided false\n"
    "    return Except.ok verdict"
)
_POS_FACTOR_PROOF = "prove_correct compareName by\n  loom_solve"


# ===========================================================================
# ADMISSIBILITY (re-aimed) — the nagini sibling self-calls on an F2P-shaped input
# to show the precondition ADMITS it. This bundle carries NO `require` clause
# (the comparison is total), so that probe is degenerate. Re-aimed at the
# residual risk on a transparent carrier: that the post-image is DEGENERATE — it
# does NOT actually demand the graceful decline on the uninterpretable arm, name
# agreement on the same-kind arm, and `false` on the different-kind arm. An
# in-region assert pins all three arms (incl. same-kind agreement AND
# disagreement, so name-sensitivity is pinned) at F2P-shaped points; the impl is
# kept verbatim so the method's own obligation still discharges, and the proof
# gains a `refine ⟨rfl, rfl, rfl, rfl⟩` arm to close the ground assert. The
# assert is LIVE — a false conjunct (e.g. claiming same-kind DISagreement is
# `decided true`) leaves an unsolved goal (verified out of band).
# ===========================================================================
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss\n"
    "      (compareSpec ['a'] .uninterpretable = Except.ok .deferred\n"
    "       ∧ compareSpec ['a'] (.sameKind ['a']) = Except.ok (.decided true)\n"
    "       ∧ compareSpec ['a'] (.sameKind ['b']) = Except.ok (.decided false)\n"
    "       ∧ compareSpec ['a'] .otherKind = Except.ok (.decided false)))\n"
    + _IMPL_TOP
)
_ADMISS_PROOF = (
    "prove_correct compareName by\n"
    "  loom_solve\n"
    "  refine ⟨rfl, rfl, rfl, rfl⟩"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    {
        "id": "pos-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER_BODY),
        "rationale": "PASS SOURCE = P1..P5. Reordering the dispatch (decide the two "
                     "definite kinds first, decline last) sends each outcome to the "
                     "SAME verdict as gold, so `out = compareSpec selfName outcome` "
                     "and all four implication/∃ clauses still discharge under the "
                     "frozen `cases outcome <;> simp_all`. A structurally-different "
                     "faithful reshape MUST verify, else the postcondition is over-fit "
                     "to the exact arm ORDER => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-factor-ok",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_with_impl(_POS_FACTOR_BODY), _PROOF, _POS_FACTOR_PROOF),
        "rationale": "PASS SOURCE = P1..P5. Building the bare `Verdict` by cases and "
                     "wrapping `Except.ok` ONCE on return (a different data-flow shape: "
                     "the error-carrier is introduced once, not per-arm) reproduces "
                     "`compareSpec selfName outcome` on every outcome, so all clauses "
                     "discharge; the now-redundant trailing tactic is dropped (proof "
                     "reshape only — the spec view is untouched). A second honest shape "
                     "verifying confirms the spec is not over-fit to the per-arm "
                     "wrapper form. Else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed)
    # =====================================================================
    {
        "id": "admiss-arms-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_TOP, _ADMISS_ASSERT), _PROOF, _ADMISS_PROOF),
        "rationale": "PASS SOURCE = the post-image is satisfiable AND non-degenerate at "
                     "F2P-shaped points. The in-region assert pins the uninterpretable "
                     "arm to the graceful decline (`Except.ok .deferred`), the "
                     "same-kind arm to name AGREEMENT (`decided true` when names "
                     "coincide) AND name DISagreement (`decided false` when they "
                     "differ), and the different-kind arm to `decided false` — so the "
                     "spec genuinely demands each verdict, distinct from an escaped "
                     "error or a constant. The assert must discharge (else the "
                     "obligation is degenerate/unsatisfiable at the interesting point) "
                     "and the frozen body keeps `out = compareSpec selfName outcome` "
                     "intact, so the module verifies. Since the comparison is total, "
                     "there is no precondition to over-strengthen; this defends against "
                     "a hollow/degenerate post-image instead. Re-aimed from the nagini "
                     "precondition-admits probe (vacuous: no `require` clause).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (all three outcome kinds exercised; selfName/name varied),
    # and the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test.
    # =====================================================================
    {
        "id": "weak-uninterp-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image bug: on an uninterpretable operand, let the interpretation
        # failure ESCAPE to the caller as an error instead of declining.
        "module": _swap(_BASE, _ARM_UNINTERP,
                        "      | .uninterpretable => Except.error .interpretationEscaped"),
        "refinement": "this is the pre-image exactly: on an operand the interpreter "
                      "cannot denote (e.g. the null operand the issue reports), the "
                      "interpretation failure is left to escape to the caller as an "
                      "error instead of being absorbed into a graceful decline. A "
                      "faithful real counterpart that let that failure propagate would "
                      "RAISE on `x == None` for an unrecognized-name receiver — exactly "
                      "the crash the issue reports — so the failing test (which asserts "
                      "such a comparison yields a definite verdict, not an exception) "
                      "does NOT resolve. This is the G-DIFF discriminator.",
        "rationale": "REJECT from P2 (`∃ v, out = Except.ok v`) and P3 "
                     "(`uninterpretable → out = Except.ok .deferred`): the rival "
                     "returns `Except.error`, so no `Except.ok v` exists and the "
                     "decline clause is violated. Refuted at "
                     "(selfName=['a'], .uninterpretable). If it verified => "
                     "SPEC-TOO-WEAK (admits the escaped-error pre-image).",
        "witness": _witness("['a']", "InterpretOutcome.uninterpretable"),
    },
    {
        "id": "weak-uninterp-decided",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on the uninterpretable arm: return a DEFINITE verdict (false)
        # instead of declining. Total (never escapes) but decides where it must
        # defer — the "definite decision instead of NotImplemented" pre-patch shape
        # the nagini sibling models for the sibling dunder.
        "module": _swap(_BASE, _ARM_UNINTERP,
                        "      | .uninterpretable => Except.ok (.decided false)"),
        "refinement": "a faithful counterpart that returned a DEFINITE verdict on an "
                      "uninterpretable operand (rather than declining) would refuse to "
                      "hand off to the reflected/identity comparison: `x == None` and "
                      "`x not in (None, …)` would be forced to a definite answer here "
                      "instead of deferring to identity, so membership/reflected "
                      "comparisons that the failing test exercises resolve against the "
                      "wrong operand — it would NOT resolve faithfully.",
        "rationale": "REJECT from P1 (`out = compareSpec selfName outcome`) and P3: on "
                     "the uninterpretable arm the spec pins `Except.ok .deferred`, but "
                     "the rival returns `Except.ok (.decided false)`. Refuted at "
                     "(selfName=['a'], .uninterpretable) — distinct behaviour from the "
                     "escape rival (definite verdict vs escaped error). If it verified "
                     "=> SPEC-TOO-WEAK (defer collapsed into a definite decision).",
        "witness": _witness("['a']", "InterpretOutcome.uninterpretable"),
    },
    {
        "id": "weak-samekind-name-insensitive",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the same-kind arm: report equal (decided true) for
        # every same-kind operand, dropping the name-agreement check. Correct
        # exactly when the names DO coincide; wrong when they differ.
        "module": _swap(_BASE, _ARM_SAME,
                        "      | .sameKind name   => Except.ok (.decided true)"),
        "refinement": "a faithful counterpart that reported equal for every same-kind "
                      "operand — dropping the `self.name == other.name` conjunct — would "
                      "declare two DIFFERENTLY-named unrecognized units equal, so the "
                      "regression/comparison tests that distinguish them observe the "
                      "wrong verdict; it would NOT resolve on the name-disagreement "
                      "sub-domain.",
        "rationale": "REJECT from P1 and P4 (`∀ name, .sameKind name → out = "
                     ".decided (decide (selfName = name))`): the rival ignores the "
                     "names and always decides `true`, so at a same-kind operand whose "
                     "name DIFFERS from `selfName` the spec demands `decided false`. "
                     "Refuted at (selfName=['a'], .sameKind ['b']) — moving the name "
                     "binder off agreement, exercising P4's dependence on BOTH selfName "
                     "and the bound name. If it verified => SPEC-TOO-WEAK (the "
                     "name-agreement discriminator is hollow).",
        "witness": _witness("['a']", "(InterpretOutcome.sameKind ['b'])"),
    },
    {
        "id": "weak-samekind-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual near-miss on the same-kind arm: NEVER report equal (decided false),
        # dropping the definite-EQUAL outcome. Correct when the names differ; wrong
        # when they coincide. Its separating input MOVES the name binder onto
        # AGREEMENT (selfName = name), the point the previous rival holds apart.
        "module": _swap(_BASE, _ARM_SAME,
                        "      | .sameKind name   => Except.ok (.decided false)"),
        "refinement": "a faithful counterpart that reported unequal for every same-kind "
                      "operand — hard-returning `False` and never checking name "
                      "agreement — would declare an unrecognized unit UNEQUAL to an "
                      "equally-named one, so `unit == \"FOO\"` for a matching name is "
                      "False and the failing test's positive-equality assertion FAILS "
                      "— it would NOT resolve on the name-agreement sub-domain.",
        "rationale": "REJECT from P1 and P4: the rival always decides `false` on the "
                     "same-kind arm, so at a same-kind operand whose name COINCIDES "
                     "with `selfName` the spec demands `decided true`. Refuted at "
                     "(selfName=['a'], .sameKind ['a']) — the name-AGREEMENT point the "
                     "insensitive rival cannot be caught at, so the two same-kind "
                     "rivals probe DISTINCT points for DISTINCT reasons. If it verified "
                     "=> SPEC-TOO-WEAK (never reports equal).",
        "witness": _witness("['a']", "(InterpretOutcome.sameKind ['a'])"),
    },
    {
        "id": "weak-otherkind-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the different-kind arm: report equal (decided true)
        # for an operand of a DIFFERENT kind. Correct on the other two arms;
        # wrong on the otherKind arm.
        "module": _swap(_BASE, _ARM_OTHER,
                        "      | .otherKind       => Except.ok (.decided true)"),
        "refinement": "a faithful counterpart that reported equal for a different-kind "
                      "operand would declare an unrecognized unit EQUAL to a genuine "
                      "recognized unit (a value of a different kind), so `unit == u.m` "
                      "is True where the failing test asserts `unit != u.m`; it would "
                      "NOT resolve on the different-kind sub-domain.",
        "rationale": "REJECT from P1 and P5 (`otherKind → out = .decided false`): the "
                     "rival returns `decided true` on the different-kind arm where the "
                     "spec pins `decided false`. Refuted at (selfName=['z'], "
                     ".otherKind) — the third outcome kind, with selfName moved off "
                     "['a'] to confirm the different-kind verdict is name-independent. "
                     "If it verified => SPEC-TOO-WEAK (a different-kind operand wrongly "
                     "reported equal).",
        "witness": _witness("['z']", "InterpretOutcome.otherKind"),
    },
    {
        "id": "weak-samekind-defer",
        "kind": "uniqueness",
        "expect": "reject",
        # DECLINE where a definite verdict is owed: the same-kind arm hands back
        # `deferred` instead of deciding name agreement. Distinct from every other
        # rival — the other four either escape, or decide the WRONG boolean; this
        # one refuses to decide at all on an arm the spec pins to a definite
        # verdict. It is the live half of the nagini `always-defer` shape, aimed
        # at the one arm where declining is wrong.
        "module": _swap(_BASE, _ARM_SAME,
                        "      | .sameKind name   => Except.ok .deferred"),
        "refinement": "a faithful counterpart that declined on a same-kind operand — "
                      "handing off to the reflected/identity comparison instead of "
                      "comparing the two names — would never report a definite EQUAL for "
                      "an equally-named operand of this kind: the comparison falls through "
                      "to identity, which is False for two distinct objects, so the "
                      "failing test's positive-equality assertion FAILS. It would NOT "
                      "resolve.",
        "rationale": "REJECT from P1 and P4: on the same-kind arm the spec pins a DEFINITE "
                     "verdict `decided (decide (selfName = name))`, but the rival returns "
                     "`deferred`. Refuted at (selfName=['a'], .sameKind ['a']). This "
                     "attacks the DEFER/DECIDE axis in the direction the other rivals do "
                     "not: weak-uninterp-decided decides where it must defer, this one "
                     "defers where it must decide. If it verified => SPEC-TOO-WEAK (the "
                     "spec would not force a definite verdict on the same-kind arm).",
        "witness": _witness("['a']", "(InterpretOutcome.sameKind ['a'])"),
    },
    {
        "id": "weak-always-defer",
        "kind": "uniqueness",
        "expect": "reject",
        # Total, never escapes, always declines — the maximally non-committal
        # impl. Correct ONLY on the uninterpretable arm. Ports the nagini
        # `rival-unparsed-always-defer` case directly (it IS expressible here).
        "module": _swap(_BASE, _IMPL, "    return Except.ok .deferred"),
        "refinement": "a faithful counterpart that declined for EVERY operand would make "
                      "the comparison hand off to the reflected/identity comparison in all "
                      "cases, so an equally-named operand of this kind is never reported "
                      "equal (identity is False for distinct objects) and the failing "
                      "test's positive-equality assertion FAILS. It also never reports the "
                      "definite inequality the different-kind arm owes. It would NOT "
                      "resolve.",
        "rationale": "REJECT from P1, P4 and P5: the rival declines on every arm, so both "
                     "definite arms are violated. Refuted at "
                     "(selfName=['a'], .sameKind ['a']). Its refutation point coincides "
                     "with weak-samekind-defer's, but the IMPLS differ observably (this "
                     "one is also wrong at .otherKind, verified by a second build that "
                     "refutes it at (['z'], .otherKind) where weak-samekind-defer is "
                     "CORRECT), so it is not the same attack written twice. If it verified "
                     "=> SPEC-TOO-WEAK (a constantly-declining comparison would satisfy "
                     "the spec).",
        "witness": _witness("['a']", "(InterpretOutcome.sameKind ['a'])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 6 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) PLUS 2 AXIOM_TESTS, contracting
# TWO abstracted dunders — `eq_unparsed_name` (= UnrecognizedUnit.__eq__, the F2P
# hunk) and `eq_unit` (= UnitBase.__eq__, the behaviourally-inert second hunk).
#
# CARRIER NARROWING. This velvet bundle models ONLY the F2P-discriminating
# function, `UnrecognizedUnit.__eq__`, as the single method `compareName`
# (mapping.md §1); the second hunk `UnitBase.__eq__` is recorded as
# behaviourally inert for the harness (mapping.md §1.1) and carries NO separately-
# observable fixed behaviour, so it gets no method and no counterpart here. Every
# nagini `eq_unit` case therefore has no counterpart at all — this is carrier
# narrowing, not an omission-for-difficulty. The three-valued Python tag
# (RES_TRUE/RES_FALSE/RES_NOTIMPL) maps to `Verdict` (`decided true` / `decided
# false` / `deferred`); the crucial extra distinction this carrier makes and the
# nagini three-valued tag CANNOT is the ESCAPED-ERROR outcome
# (`Except.error .interpretationEscaped`) — the pre-image's actual failure — which
# nagini can only model as a totality obligation on the tag.
#
#   nagini case                          kind          -> here                       disposition
#   --------------------------------------------------------------------------------------------
#   pos-unparsed-restructured            soundness     -> pos-reorder-arms           PORTED
#                                                         + pos-factor-ok            PORTED (2nd shape)
#   pos-unit-restructured                soundness     -> (none)                     NARROWED (eq_unit unmodeled)
#   admiss-defer-self-call               admissibility -> admiss-arms-nondegenerate  RE-AIMED
#   rival-unparsed-defer-as-false        uniqueness    -> weak-uninterp-decided      PORTED
#   rival-unparsed-never-true            uniqueness    -> weak-samekind-always-false PORTED
#   rival-unparsed-always-defer          uniqueness    -> weak-always-defer          PORTED
#   rival-unit-defer-as-false            uniqueness    -> (none)                     NARROWED (eq_unit unmodeled)
#   rival-unit-notunit-as-false          uniqueness    -> weak-otherkind-true (dual) RE-AIMED
#   (added: the actual pre-image escape) -> weak-uninterp-escape                     ADDED
#   (added: name-insensitivity on P4)    -> weak-samekind-name-insensitive          ADDED
#   (added: decline where a verdict is owed) -> weak-samekind-defer                  ADDED
#   AXIOM_TESTS (ax-abstraction-sound,
#                ax-abstraction-containment)            -> (none)                    G-AX
#
# 4 ported, 1 re-aimed positive->none, 3 added, several narrowed = 10 velvet cases
# (2 verify soundness + 1 verify admissibility + 7 reject).
#
# PORTED (pos-unparsed-restructured -> pos-reorder-arms + pos-factor-ok): the
#   nagini sibling ships ONE structurally-different correct `eq_unparsed_name`
#   (definite case collapsed into a computed boolean). It is carried by TWO honest
#   reshape positives: reorder the dispatch arms (frozen proof still closes) and
#   factor the `Except.ok` wrapper out of every arm (proof retuned to bare
#   `loom_solve`). Both verify (two real builds).
# NARROWED (pos-unit-restructured, rival-unit-*): every `eq_unit` case attaches to
#   `UnitBase.__eq__`, which this bundle does not model (behaviourally inert for
#   the harness). No counterpart — carrier narrowing, reported not omitted.
# RE-AIMED (admiss-defer-self-call -> admiss-arms-nondegenerate): the nagini probe
#   self-calls to show the precondition admits an F2P input. This method has NO
#   `require` clause, so that probe is vacuous; re-aimed at a DEGENERATE post-image
#   via a live in-region assert pinning all three arms + name-sensitivity. Verified
#   to build; the assert is live (a false conjunct leaves an unsolved goal, checked
#   out of band).
# PORTED (rival-unparsed-defer-as-false -> weak-uninterp-decided): return a
#   DEFINITE verdict on the uninterpretable arm instead of declining — the "defer
#   collapsed into a definite decision" pre-patch shape. Refuted at
#   (['a'], .uninterpretable).
# PORTED (rival-unparsed-never-true -> weak-samekind-always-false): never report a
#   definite EQUAL on the same-kind arm — refuted at the name-AGREEMENT point
#   (['a'], .sameKind ['a']).
# RE-AIMED (rival-unit-notunit-as-false -> weak-otherkind-true): the nagini rival
#   returns a definite verdict on the "coerced but not a genuine unit" sub-domain
#   for `eq_unit`; that sub-domain maps onto THIS carrier's different-kind arm
#   (`otherKind`, mapping.md §2 — a non-`UnrecognizedUnit` interpretation), so the
#   analogue is a wrong different-kind verdict, refuted at (['z'], .otherKind).
# ADDED (weak-uninterp-escape): the ACTUAL pre-image the F2P observes — the
#   interpretation failure ESCAPES as an error (`Except.error`) rather than a
#   definite tag. The nagini three-valued tag cannot express an escaped error
#   (it models the raise only as a totality obligation); this carrier can, so the
#   G-DIFF discriminator is defended directly. Refuted at (['a'], .uninterpretable)
#   via P2 (`∃ v, out = Except.ok v`).
# ADDED (weak-samekind-name-insensitive): the same-kind arm's P4 clause depends on
#   BOTH `selfName` and the bound `name`; this rival drops the name check (always
#   `decided true`) and is refuted at name DISagreement (['a'], .sameKind ['b']),
#   the dual of weak-samekind-always-false. Together the two same-kind rivals pin
#   P4 in both directions.
# PORTED (rival-unparsed-always-defer -> weak-always-defer): "always defer" IS
#   expressible on this carrier — `return Except.ok .deferred` — and it is NOT
#   subsumed by the other rivals. An earlier revision of this manifest recorded it
#   as NARROWED on the argument that its P4/P5 violations were "already attacked";
#   that argument was wrong. The shipped rivals all either escape or decide the
#   WRONG boolean; none of them DECLINES on an arm the spec pins to a definite
#   verdict, so the defer-where-a-verdict-is-owed direction of the DEFER/DECIDE
#   axis was unattacked. Landed with two real builds (rival exit 0, gold exit 1 by
#   decided refutation) plus a forgery control at (['a'], .uninterpretable), the
#   one point where it IS correct, which exits 1 as required. `weak-samekind-defer`
#   is shipped alongside it as the single-arm version: the two share a refutation
#   POINT but differ observably (weak-samekind-defer is correct at .otherKind,
#   weak-always-defer is not — confirmed by a build refuting the latter at
#   (['z'], .otherKind), exit 0).
# VACUOUS (frame-mutation): the nagini file itself states NO read-only Acc(x,1/2)
#   input exists (self/other are plain value booleans); on this referentially-
#   transparent backend there is no mutable heap reference, no `mut` binder, no
#   substitute probe. Not fabricated.
# DIVERGENCE (no nagini counterpart) - the class is INAPPLICABLE to this impl
#   and CLOSED BY THE SEMANTICS against any rival that manufactures it. The
#   frozen impl is LOOP-FREE (straight-line ``let`` over immutable values, no
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
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job; this bundle declares no
#   axiom (the interpretation callee is a free input owed no contract; the
#   comparison is modeled deeply as `compareSpec`), and this gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Two input binders: `selfName : List Char` and
#   `outcome : InterpretOutcome` (with the same-kind arm binding an inner `name`).
#   The five reject witnesses probe FIVE distinct input points (pts=5):
#     (['a'], .uninterpretable)  weak-uninterp-escape       [P2, P3]
#     (['a'], .uninterpretable)  weak-uninterp-decided      [P1, P3]  (distinct rival: definite vs escape)
#     (['a'], .sameKind ['b'])   weak-samekind-name-insensitive [P1, P4 @ disagreement]
#     (['a'], .sameKind ['a'])   weak-samekind-always-false [P1, P4 @ agreement]
#     (['z'], .otherKind)        weak-otherkind-true        [P1, P5]
#   `outcome` ranges over ALL THREE constructors; the same-kind `name` binder is
#   varied across agreement (['a']=['a']) and disagreement (['a']≠['b']) so P4's
#   dependence on BOTH selfName and name is exercised; `selfName` takes ['a'] and
#   ['z'] (the different-kind verdict is confirmed name-independent). Clause
#   coverage: P1 attacked by every value rival AND live in its own right (measured:
#   a rival violating ONLY P1 is refuted at exit 0 once `compareSpec` is in the
#   witness simp set — see the CARRIER NOTE); P2/P3 by the two uninterpretable
#   rivals (escape violates P2, decided violates P3, both violate P1-on-that-arm);
#   P4 attacked in THREE directions by the three same-kind rivals (always-true at
#   disagreement, always-false at agreement, and DECLINE where a definite verdict
#   is owed); P5 by weak-otherkind-true and weak-always-defer. Every independent
#   top-level clause is attacked, and the two uninterpretable witnesses fail for
#   DIFFERENT reasons (escaped error vs definite verdict), not one attack written
#   twice.
#
#   PROBED AND FOUND CLOSED (no spec hole). Eight further wrong impls were built
#   and every one was rejected with a discriminating witness: decline on the
#   different-kind arm; a definite `true` on the uninterpretable arm; an INVERTED
#   name test on the same-kind arm (`selfName ≠ name`); an escaped error on the
#   same-kind arm; an escaped error on the different-kind arm; and a same-kind test
#   against a CONSTANT name that ignores `selfName` entirely. None verified, so no
#   SPEC-TOO-WEAK hole was found on any arm. Four correct reshapes were also built:
#   the symmetric name test (`name = selfName`) and the `BEq` spelling
#   (`selfName == name`) both VERIFY under the frozen proof, and an `if`-based
#   per-arm `return` shape verifies under a bare `loom_solve`; a
#   precompute-the-boolean-then-dispatch shape needed
#   `all_goals (cases outcome <;> simp_all [compareSpec])` to close. No faithful
#   correct impl was found that the spec rejects, so no SPEC-TOO-STRONG hole
#   either.
AXIOM_TESTS = []

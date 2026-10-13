"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25775 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the single
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both regions the consumer spec view elides, so
``markers.same_spec`` holds by construction and the ``prove_correct
textAntialiased`` header survives). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND its refutation ``witness`` ELABORATES
against the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one contracted method, one clause)
----------------------------------------------------
  textAntialiased (requested : Option Bool) (ambient : Bool) return (out : Bool)
    ensures out = resolveAA requested ambient                            -- (C1)

  resolveAA requested ambient = match requested with
                                | none   => ambient
                                | some b => b

C1 is the WHOLE obligation and the only impl-constraining clause. It decomposes
into two independent legs, and every rival below attacks one of them:

  (C1a) requested = none      =>  out = ambient      (the ambient default stands)
  (C1b) requested = some b    =>  out = b            (an explicit per-object
                                                      choice supersedes the
                                                      ambient default entirely —
                                                      note the right-hand side
                                                      does NOT mention `ambient`)

These are exactly what the failing tests observe: an object given an explicit
choice reads that choice back verbatim (C1b), and an object given no explicit
choice reads back the ambient/global default (C1a).

GROUNDED, NOT AN ORACLE ECHO. ``resolveAA`` is a transparent two-branch ``def``
over the method's OWN two arguments — the bundle declares no ``axiom`` and no
``opaque`` (meta.json axioms == [] and deep_model_references == []). So there is
no answer key an impl could echo without doing the work, and the
UNGROUNDED-ORACLE-ECHO class does not apply. As on the nagini sibling, its place
is taken by honest cheapest-impl POSITIVE CONTROLS (``pos-*``): ``return
resolveAA requested ambient`` is the cheapest correct impl and it MUST verify,
while any impl that resolves the two legs differently fails C1 at a concrete
point (the seven rivals below demonstrate that at all six points of the domain).

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle contracts FOUR heap procedures (build / set / get / copy) over
a mutable object carrying TWO fields — a boolean preference and a redraw flag —
under fractional permissions. This velvet bundle contracts ONE method: the pure
resolution of the effective per-object flag from (optional explicit choice,
ambient default). That is carrier narrowing, not an omission, and it makes four
nagini classes inexpressible here. They are listed in the port ``assessment``
and NO substitute probe is fabricated for any of them:

  * FRAME / PERMISSION-MUTATION — VACUOUS. Lean and Velvet are referentially
    transparent: there is no heap, no aliasing, and no fractional permission to
    subvert; both parameters are immutable values and neither is declared
    ``mut``. The two MANDATORY nagini frame rivals (force a write through the
    read-only getter input; write back into the read-only copy source) have no
    counterpart at all.
  * REDRAW-FLAG rivals — VACUOUS. This carrier models no redraw flag; the
    resolution is a pure value with no second component. The nagini rivals that
    DROP the redraw flag attack a field this bundle does not model.
  * OBJECT-TO-OBJECT PROPAGATION rivals — VACUOUS. Copying state from one object
    to another is not part of the modeled resolution kernel; the nagini copy
    rivals map onto no part of C1.
  * SEPARATE-SETTER rivals — FOLDED, not dropped. The nagini setter's value
    clause (store exactly the supplied value) and the nagini constructor's
    explicit-choice clause are the SAME clause on this carrier: C1b. The nagini
    no-op-setter and negating-setter rivals are therefore re-expressed as
    ``rival-ignore-requested`` and ``rival-negate-requested`` against C1b.

DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE SEMANTICS
against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS MECHANICS. On a tactic-proof backend "did not verify" is the DEFAULT
outcome of reshaping an impl (the frozen ``loom_solve`` is tuned to the frozen
form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a machine-checked refutation witness.
The carrier here is FULLY TRANSPARENT — two booleans, no opaque callee — so the
Velvet tester path is live and needs no conditioning: ``extract_program_for`` /
``prove_{pre,post}condition_decidable_for`` / ``derive_tester_for`` yield a
computable ``textAntialiasedTester : Option Bool → Bool → Bool``, and each
witness states ``textAntialiasedTester <requested> <ambient> = false`` at ONE
concrete pair of literals, i.e. "the extracted rival program VIOLATES the
contract at this input". No witness binds any hypothesis (every input is a
decidable literal), so the gate's inconsistency probe has nothing to check and
no ``witness-inconsistent`` risk exists here. No banned token appears
(``sorry`` / ``admit`` / ``native_decide`` / ``axiom`` / ``opaque``).

Every witness was checked out-of-band with ``scripts/lean_verify.sh``, both
halves, plus a read of the gold-side error text: each ELABORATES against its
rival (exit 0) and FAILS against the frozen solution with ``Tactic `decide`
proved that the proposition … is false`` — a genuine SEMANTIC refutation of the
witness on gold, not a stuck reduction. That distinction matters: a stuck
``decide`` would only show the kernel could not evaluate gold, whereas this says
gold positively SATISFIES the contract at the very input where the rival breaks
it. So each witness asserts something true of the wrong impl and false of the
right one.

BINDER / CLAUSE COVERAGE. Both input binders are varied by the reject witnesses,
and between them the seven witnesses probe ALL SIX points of the input domain
(``{none, some false, some true} × {false, true}``):

  * ``requested`` at all three of its values — ``none``
    (``rival-default-true``, ``rival-default-false``), ``some true``
    (``rival-ignore-requested``, ``rival-and-ambient``,
    ``rival-negate-requested``), ``some false`` (``rival-leak-ambient``,
    ``rival-const-true``).
  * ``ambient`` at BOTH polarities, which is what stops a rival from hard-coding
    the fallback invisibly: ``rival-default-true`` is refutable ONLY at
    ``ambient = false`` and ``rival-default-false`` ONLY at ``ambient = true``;
    ``rival-leak-ambient`` is refutable ONLY at ``ambient = true`` (at
    ``ambient = false`` letting the ambient value leak through is unobservable),
    while ``rival-and-ambient`` is refutable ONLY at ``ambient = false``. Without
    that last pair, a rival that merged the per-object choice with the ambient
    default in ONE direction would sit outside every probed point.
  * Both legs of C1 are attacked: C1a by ``rival-default-true`` /
    ``rival-default-false``, C1b by the other five.

Exactly one witness INPUT is shared, by ``rival-ignore-requested`` and
``rival-and-ambient`` at ``(some true, false)``, and it is shared legitimately:
that is ``rival-and-ambient``'s ONLY failing point in the whole domain, and at
it the two rivals compute the same wrong value by the same mechanism (the
ambient ``false`` suppresses an explicit ``true``). Neither rationale claims a
sub-domain the manifest does not demonstrate.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. There is no axiomatized callee to
probe (meta.json axioms == [], deep_model_references == []), and the axiom lane
belongs to G-AX regardless; this gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25775"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. `_IMPL` is the FULL body of the single `-- impl-start` /
# `-- impl-end` region and `_PROOF` the FULL `prove_correct` command, verbatim.
# Both are unique in the frozen file (asserted at import), so every replacement
# below lands wholly inside a region the consumer spec view elides — which is
# what makes `same_spec` hold by construction rather than by inspection.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- Start from the ambient/global default, then let an explicit per-object\n"
    "    -- choice override it when one was supplied.\n"
    "    let aa := match requested with\n"
    "      | none   => ambient\n"
    "      | some b => b\n"
    "    return aa"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

_PROOF = "prove_correct textAntialiased by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the tactic body retuned (for a correct reshape
    whose residual goal `loom_solve` alone no longer closes). The
    `prove_correct textAntialiased` header is preserved verbatim and no new
    declaration is introduced — the obligation survives intact."""
    return _swap(_impl(body), _PROOF, proof)


# ---------------------------------------------------------------------------
# Witness builder. The carrier is two booleans with no opaque callee, so the
# postcondition is genuinely decidable and the tester path computes: the witness
# says "the extracted rival program does NOT satisfy the contract at this
# concrete input". It is checked in a file whose `prove_correct` block has been
# stripped, so no tactic script can mask the verdict.
# ---------------------------------------------------------------------------
def _witness(requested, ambient):
    return (
        "extract_program_for textAntialiased\n"
        "prove_precondition_decidable_for textAntialiased\n"
        "prove_postcondition_decidable_for textAntialiased\n"
        "derive_tester_for textAntialiased\n"
        "\n"
        f"example : textAntialiasedTester {requested} {ambient} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation, C1 is SPEC-TOO-STRONG (over-fit to one code form). Each was
    # confirmed with a real build (exit 0). Ports the nagini pos-* controls:
    # nagini's three (direct construction, and two field-write reorderings) are
    # re-aimed at the reshapes this carrier admits — the field-write orderings
    # have no counterpart because there are no fields to write.
    # =====================================================================
    {
        "id": "pos-resolve-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest HONEST correct impl: report the pure resolution directly
        # instead of re-spelling its branch structure inline.
        "module": _impl("    return resolveAA requested ambient"),
        "rationale": (
            "C1 is literally `out = resolveAA requested ambient`, and the "
            "post-image is GROUNDED in the method's own two arguments (a "
            "transparent two-branch def; the bundle declares no axiom/opaque), so "
            "reporting it directly is the cheapest correct impl and MUST verify — "
            "else C1 is SPEC-TOO-STRONG. Doubles as the evidence that C1 is not "
            "echo-vulnerable: because the post-image is not an answer key, any "
            "impl that resolves either leg differently is refutable at a concrete "
            "input, which the seven rivals below exhibit across the whole domain. "
            "Ports the nagini pos-build-direct (construct with the resolved value "
            "rather than routing through a second call). Frozen proof retained."
        ),
    },
    {
        "id": "pos-branch-order-swapped",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: write the two-branch resolution in the REVERSE branch order —
        # the explicit choice first, the ambient fallback second. Pointwise equal
        # on every input; a different code form for the same resolution.
        "module": _impl(
            "    -- Report the explicit per-object choice when one exists;\n"
            "    -- otherwise the ambient default stands.\n"
            "    return (match requested with\n"
            "      | some b => b\n"
            "      | none   => ambient)"
        ),
        "rationale": (
            "a correct impl whose two branches are written in the REVERSE order "
            "of the frozen form (explicit choice first, ambient fallback second) "
            "and which returns the match directly rather than binding a local. "
            "Pointwise identical on all six inputs, so C1 still discharges and "
            "the frozen proof closes as-is. Must verify, else C1 is "
            "SPEC-TOO-STRONG (over-fit to one branch order). Ports the nagini "
            "pos-set-reorder / pos-copy-reorder ORDERING controls, whose "
            "field-write form has no counterpart on a carrier with no fields."
        ),
    },
    {
        "id": "pos-resolve-getd",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: express the resolution with the library fallback combinator
        # instead of an explicit match. Same value everywhere, but no longer
        # DEFINITIONALLY the frozen form, so the residual goal needs the case
        # split — supplied inside the existing tactic body, no new declaration.
        "module": _impl_reproved(
            "    let aa := requested.getD ambient\n    return aa",
            "prove_correct textAntialiased by\n"
            "  loom_solve\n"
            "  cases requested <;> rfl",
        ),
        "rationale": (
            "a correct impl expressing the resolution with the library "
            "option-fallback combinator rather than an explicit two-branch match: "
            "equal to the post-image at every input but not definitionally, so "
            "this is a real test of whether C1 admits a non-syntactic reshape. "
            "Must verify, else SPEC-TOO-STRONG. The obligation is UNCHANGED — the "
            "`prove_correct textAntialiased` header is byte-identical and the "
            "residual goal is closed by a case split on the option inside the "
            "existing tactic body; no helper lemma, no new declaration, no "
            "assumption token."
        ),
    },
    {
        "id": "pos-control-flow-isSome",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a genuinely different CONTROL SHAPE — test for the presence of
        # an explicit choice with a boolean guard and return from two separate
        # exits, instead of one match-valued return.
        "module": _impl_reproved(
            "    if requested.isSome then\n"
            "      return requested.getD ambient\n"
            "    else\n"
            "      return ambient",
            "prove_correct textAntialiased by\n"
            "  loom_solve <;> cases requested <;> simp_all [resolveAA]",
        ),
        "rationale": (
            "a correct impl with a different CONTROL shape: a boolean presence "
            "guard and two separate exits rather than a single match-valued "
            "return. Both exits agree with the post-image on their branch, so C1 "
            "holds on the whole domain and it must verify (else SPEC-TOO-STRONG "
            "against control-flow reshaping). Obligation preserved byte-identically; "
            "the two residual goals are closed by a case split plus the frozen "
            "pure def's own unfolding inside the existing tactic body — no new "
            "lemma or axiom."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The nagini admiss-* cases establish that the
    # READ-ONLY precondition Acc(.,1/2) is non-vacuous (a pure read succeeds
    # under the half permission). This method carries NO `require` clause at all
    # (the pre-conditions region is empty) and both parameters are immutable
    # values, so there is no precondition to admit and no permission to exercise:
    # that half of the nagini case is inexpressible. The residual admissibility
    # risk on a total domain is whether the post-image is SATISFIABLE at the
    # inputs the failing tests actually exercise — so the probe is re-aimed
    # there, discharging C1's two legs at ground F2P-shaped inputs alongside the
    # frozen obligation.
    # =====================================================================
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct textAntialiased by\n"
            "  have _explicit : resolveAA (some true) false = true := by decide\n"
            "  have _fallback : resolveAA none false = false := by decide\n"
            "  loom_solve",
        ),
        "rationale": (
            "the post-image is discharged by evaluation at the two ground "
            "F2P-shaped inputs — an explicit per-object choice that CONTRADICTS "
            "the ambient default (C1b: the choice must win) and no explicit "
            "choice at all (C1a: the ambient default must stand) — before the "
            "frozen obligation is closed verbatim. Must verify; if either ground "
            "instance could not be discharged, C1 would be unsatisfiable at "
            "exactly the inputs the failing tests exercise (the analogue of "
            "PRECOND-TOO-STRONG on a carrier with an empty precondition). Nothing "
            "is assumed: no new declaration, the `prove_correct textAntialiased` "
            "header is byte-identical, and both ground facts are `have`s inside "
            "the existing tactic body."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve the failing tests, so a
    # VERIFYING rival here would be a true verify-does-not-imply-resolve break
    # rather than an artifact, and (b) a machine-checked refutation witness at a
    # concrete input, confirmed to elaborate against the rival and to FAIL
    # semantically on the frozen solution.
    # =====================================================================
    {
        "id": "rival-ignore-requested",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-CHANGE behavior verbatim (it is this bundle's
        # Solution_prepatch.lean impl): the effective flag is read straight from
        # the ambient/global default and the per-object choice is ignored
        # entirely. Folds BOTH nagini rivals that drop the per-object value: the
        # constructor that ignores its argument and the no-op setter — on this
        # carrier they are the same defect against C1b.
        "module": _impl(
            "    -- The effective flag is taken from the ambient default only.\n"
            "    return ambient"
        ),
        "refinement": (
            "a resolution that ignores the explicit per-object choice reports the "
            "ambient/global default for an object that was given a choice. The "
            "failing tests assert that an object given an explicit choice reads "
            "exactly that choice back, and that a later explicit assignment is "
            "read back verbatim; both FAIL when the choice is discarded, because "
            "the value observed is the ambient default instead. This is the "
            "pre-change behavior the fix replaces, so its faithful real patch is "
            "the unpatched code and would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1b (`requested = some b => out = b`): at `requested = "
            "some true` with `ambient = false` the contract requires `true` and "
            "the rival returns `false`. Attacks the leg whose right-hand side does "
            "not mention `ambient` at all. If it VERIFIED => SPEC-TOO-WEAK (the "
            "spec would admit the original defect)."
        ),
        "witness": _witness("(some true)", "false"),
    },
    {
        "id": "rival-and-ambient",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on C1b in ONE direction: the explicit choice is honoured only
        # to the extent the ambient default already permits it (conjunction), so
        # an explicit `true` cannot raise a `false` ambient default. Agrees with
        # the contract at five of the six inputs.
        "module": _impl(
            "    let aa := match requested with\n"
            "      | none   => ambient\n"
            "      | some b => b && ambient\n"
            "    return aa"
        ),
        "refinement": (
            "combining the explicit per-object choice with the ambient default by "
            "conjunction instead of letting the choice supersede it means an "
            "object given an explicit enabling choice still reports disabled "
            "whenever the ambient default is disabled. The failing tests assert "
            "that an explicit choice is read back verbatim regardless of the "
            "ambient default, so a faithful patch that gated the per-object flag "
            "on the global one would FAIL that assertion on the disabled-ambient "
            "configuration and would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1b: its right-hand side is `b`, with no dependence on "
            "`ambient`, so gating the choice on the ambient value violates it "
            "wherever the two disagree in this direction — at `requested = some "
            "true` with `ambient = false` the contract requires `true` and the "
            "rival returns `false`. That single point is this rival's ENTIRE "
            "failure set (it agrees with the contract at the other five inputs), "
            "so the witness sits exactly on the sub-domain the rationale claims. "
            "It is the one input shared with rival-ignore-requested, and shared "
            "legitimately: at that input both rivals compute the same wrong value "
            "by the same mechanism (a disabled ambient default suppressing an "
            "explicit enabling choice)."
        ),
        "witness": _witness("(some true)", "false"),
    },
    {
        "id": "rival-leak-ambient",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on C1b in the OTHER direction: the ambient default LEAKS
        # THROUGH an explicit choice (disjunction), so an explicit disabling
        # choice cannot lower an enabled ambient default. Refutable ONLY at
        # `ambient = true` — the polarity rival-and-ambient cannot expose, and
        # what makes the `ambient` binder load-bearing for this leg.
        "module": _impl(
            "    let aa := match requested with\n"
            "      | none   => ambient\n"
            "      | some b => b || ambient\n"
            "    return aa"
        ),
        "refinement": (
            "letting the ambient default leak through an explicit per-object "
            "choice by disjunction means an object given an explicit disabling "
            "choice still reports enabled whenever the ambient default is "
            "enabled — and the enabled ambient default is the configuration the "
            "failing tests run under. Those tests assert that an object given an "
            "explicit disabling choice reads that choice back, and that the "
            "rendered output for an explicitly-disabled object differs from the "
            "default one; both FAIL when the global value survives the "
            "per-object choice, so a faithful patch that merged the two flags "
            "rather than superseding would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1b: at `requested = some false` with `ambient = true` "
            "the contract requires `false` and the rival returns `true`. This is "
            "the rival whose defect is INVISIBLE at `ambient = false`, so it is "
            "what makes the `ambient` binder load-bearing on the explicit-choice "
            "leg; it is also this rival's only failing point, so the witness "
            "probes exactly the claimed sub-domain."
        ),
        "witness": _witness("(some false)", "true"),
    },
    {
        "id": "rival-negate-requested",
        "kind": "uniqueness",
        "expect": "reject",
        # Ports the nagini negating setter: the explicit choice is consulted but
        # stored INVERTED. Wrong for both polarities of the choice; refuted here
        # at `ambient = true`, a point no other witness probes.
        "module": _impl(
            "    let aa := match requested with\n"
            "      | none   => ambient\n"
            "      | some b => !b\n"
            "    return aa"
        ),
        "refinement": (
            "a resolution that inverts the explicit per-object choice reports the "
            "opposite of what was requested. The failing tests assert that an "
            "object given an explicit enabling choice reads back enabled and one "
            "given an explicit disabling choice reads back disabled; an inverting "
            "patch FAILS both, for either polarity of the choice, so it would NOT "
            "resolve. Ports the nagini negating-setter rival."
        ),
        "rationale": (
            "REJECT from C1b (`requested = some b => out = b`): the rival returns "
            "`!b`, so it is wrong at every input carrying an explicit choice. "
            "Refuted at `requested = some true` with `ambient = true` — a point "
            "no other witness probes, and one where the ambient default happens "
            "to AGREE with the contract's answer, so the refutation is "
            "attributable to the inversion alone and not to any fallback defect."
        ),
        "witness": _witness("(some true)", "true"),
    },
    {
        "id": "rival-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Ports the nagini constant-True getter: report enabled regardless of
        # every input. Branches on nothing at all, isolating the pure value
        # defect from any control-flow question.
        "module": _impl(
            "    -- Report the flag as enabled unconditionally.\n"
            "    return true"
        ),
        "refinement": (
            "a resolution that always reports the flag enabled reads back enabled "
            "for an object whose effective flag is disabled. The failing tests "
            "assert that an object given an explicit disabling choice reads back "
            "disabled, and that the value read back agrees with the flag the "
            "object actually carries; a constant-enabled getter FAILS both and "
            "would NOT resolve. Ports the nagini constant-True getter rival."
        ),
        "rationale": (
            "REJECT from C1 wherever the resolved flag is `false`: at `requested "
            "= some false` with `ambient = false` the contract requires `false` "
            "and the rival returns `true`. Probed on the explicit-choice leg with "
            "a disabling choice — a `(some false, false)` input no other witness "
            "reaches — so the refutation exercises C1b rather than the fallback."
        ),
        "witness": _witness("(some false)", "false"),
    },
    {
        "id": "rival-default-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER leg, C1a: honours an explicit choice but hard-codes
        # the fallback to enabled instead of consulting the ambient default.
        # Refutable ONLY at `ambient = false`.
        "module": _impl(
            "    let aa := match requested with\n"
            "      | none   => true\n"
            "      | some b => b\n"
            "    return aa"
        ),
        "refinement": (
            "hard-coding the no-choice fallback to enabled, rather than "
            "consulting the ambient/global default, makes an object with no "
            "explicit choice report enabled even when the ambient default is "
            "disabled. The failing tests assert that an object with no explicit "
            "choice reads back the ambient default, which FAILS whenever that "
            "default is disabled — so a faithful patch that seeded the field with "
            "a literal instead of the configured default would NOT resolve on the "
            "fallback sub-domain."
        ),
        "rationale": (
            "REJECT from C1a (`requested = none => out = ambient`): at `requested "
            "= none` with `ambient = false` the contract requires `false` and the "
            "rival returns `true`. Attacks the fallback leg, which the five "
            "explicit-choice rivals leave untouched."
        ),
        "witness": _witness("none", "false"),
    },
    {
        "id": "rival-default-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of rival-default-true: the fallback is hard-coded to DISABLED.
        # Refutable ONLY at `ambient = true`. Together the pair pins C1a at both
        # polarities of `ambient`, so no rival can hard-code the fallback and
        # survive on one polarity.
        "module": _impl(
            "    let aa := match requested with\n"
            "      | none   => false\n"
            "      | some b => b\n"
            "    return aa"
        ),
        "refinement": (
            "hard-coding the no-choice fallback to disabled makes an object with "
            "no explicit choice report disabled even when the ambient default is "
            "enabled — and the enabled ambient default is the configuration the "
            "failing tests run under, so this FAILS the assertion that a "
            "no-choice object reads back the ambient default, and also the "
            "rendered-output comparison between a default object and an "
            "explicitly-enabled one. It would NOT resolve, at the fallback "
            "polarity the constant-enabled seed cannot expose."
        ),
        "rationale": (
            "REJECT from C1a: at `requested = none` with `ambient = true` the "
            "contract requires `true` and the rival returns `false`. Paired with "
            "rival-default-true this pins the fallback at BOTH values of the "
            "`ambient` binder, so a rival cannot hard-code a fallback constant "
            "and slip past a battery that probed only one polarity."
        ),
        "witness": _witness("none", "true"),
    },
]

# The axiom lane is G-AX's job and this gate ignores it; there is no axiomatized
# callee to probe in any case (meta.json axioms == [], deep_model_references == []).
AXIOM_TESTS = []

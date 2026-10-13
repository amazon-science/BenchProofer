"""properties.py — G-PBT falsification battery for django__django-15973 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct relationDependencies`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (``relationDependencies (f appLabel modelName) return (out)``).
The migration dependencies a relational field induces, in the scope of the
model that owns it. Three input binders — the field configuration ``f`` (its
target reference, its optional intermediary/through reference, and an optional
swappable-setting name), the owning ``appLabel``, and the owning ``modelName`` —
and a SINGLE load-bearing postcondition clause:

    (Q) out = relationDeps f appLabel modelName

The method has NO ``require`` clause; the admitted input domain is total.

CARRIER — fully transparent, unlike the sibling opaque-callee bundles. The
relation resolver is modeled DEEPLY (a concrete four-arm function of the
reference and the owning scope; validated == the real resolver by G-AX), and
``relationDeps`` composes it with the base/through dependency shaping — every
sub-behavior reduces under ``decide``. So each reject witness is a concrete
``…Tester … = false`` that the kernel evaluates directly (via
``derive_tester_for``), with NO conditioning on an opaque term required, and each
gold-side failure is a PLAIN EVALUATION (``decide`` proved the claim false)
rather than a tactic mismatch. The one mechanical caveat: the qualified/bare
resolver arms apply a case fold that does not kernel-reduce, so witnesses probe
the branches through already-resolved references (the ``resolved`` / ``selfRef``
arms), which exercise the SAME dependency-shaping combination the fold-bearing
arms feed into — the divergence each rival is built to expose lives in the
shaping, not in the fold. That caveat is measured, not assumed: ``decide`` on
``resolveRef (RelRef.qualified …)`` reports reduction "stuck at the `Decidable`
instance ``(String.mapAux Char.toLower 0 …)``", and ``decide +kernel`` fails the
same way, so the fold is genuinely unavailable to a kernel witness here.

Q composes several independent sub-behaviors, and the reject lane attacks each:
  * the through/intermediary dependency must resolve the INTERMEDIARY reference
    (the single behavioural delta of the fix), not the field's own target;
  * it must resolve BOTH components of that reference, not just the object name;
  * the through dependency must be PRESENT whenever the relation is routed
    through an intermediary;
  * the base dependency must honour the swappable-setting branch;
  * the base dependency must resolve in the owner's scope with the scope
    arguments in the CORRECT order;
  * the two dependencies must be emitted in the CORRECT POSITIONS (Q pins a
    list, and list equality is positional).

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries a mandatory framing rival (write back into a read-only input held at
    a fractional heap permission ``Acc(list_pred(...),1/2)``). Lean and Velvet
    are referentially transparent: the inputs are immutable values, this bundle
    declares NO ``mut`` binder, there is no heap and no aliasing — so there is no
    read-only input to mutate and no substitute probe to build. Not fabricated
    (per the porting map, this class is vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A. Q pins ``out`` to ``relationDeps f appLabel
    modelName``, a concrete data-flow over the actual input carrier (the
    reference shape, the through option, the swappable option, and the owning
    scope). There is no opaque answer-key an impl could echo; the only value
    satisfying Q is the one PRODUCED by the modeled shaping.
  * PARTIAL-DOMAIN rivals (the heart of nagini's battery — the pre-patch bug of
    resolving the WRONG reference for the through dependency, plus the
    lower-case / split-point near-misses) — the central pre-patch rival PORTS
    directly and is refuted at a concrete input; the case-fold and split-point
    near-misses are subsumed here (see the footer): the resolver is modeled as a
    total four-arm function, so its per-character normalization is not a separate
    impl decision this method makes — it is inside the deeply-modeled callee that
    G-AX validates, not inside the region a variant edits.

WITNESS PLACEMENT. The method is computable (the resolver is a concrete ``def``,
not an opaque axiom), so ``extract_program_for`` succeeds and each witness
reaches Q through Velvet's tester machinery: ``relationDependenciesTester f
appLabel modelName = false`` says the extracted program's result violates the
postcondition at that concrete input, checked in a file whose ``prove_correct``
block is stripped. Every witness reduces under ``decide``. The five reject
witnesses move all three binders — the field configuration ``f`` (target shape,
through present/absent, swappable present/absent), ``appLabel``, and
``modelName``.

Each witness's gold-side failure was re-derived under audit by FLIPPING the claim
(``= false`` -> ``= true``) and rebuilding against the frozen solution: the
flipped claim BUILDS on gold (exit 0) and fails on the rival, so gold's exit code
tracks what the witness asserts rather than reflecting a shape mismatch. The
discrimination is a real kernel refutation in every case.
"""
from pathlib import Path

INSTANCE = "django__django-15973"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the two `let`s and the
# ---- `return`). It lies wholly inside the single -- impl-start / -- impl-end
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap), so each edit keeps same_spec by construction and leaves the
# ---- frozen `prove_correct relationDependencies` statement intact.
_IMPL = (
    "    let d : Dep := baseDep f appLabel modelName\n"
    "    let deps : List Dep := match f.through with\n"
    "      | none     => [d]\n"
    "      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]\n"
    "    return deps"
)
assert _BASE.count(_IMPL) == 1, "relationDependencies impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header survives), so a positive control that
# ---- reshapes the impl may retune its tactic script without touching the spec
# ---- or dropping the obligation.
_PROOF = (
    "prove_correct relationDependencies by\n"
    "  loom_solve\n"
    "  simp_all [relationDeps]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY relationDependencies's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_reproved(new_impl, new_proof):
    """As `_impl`, but also retunes the elided `prove_correct` TACTIC BODY.

    For a positive control whose assembly shape is not DEFINITIONALLY the frozen
    one: the frozen script leaves a residual goal, so the obligation has to be
    reproven for the new shape. Both regions are elided from the consumer spec
    view, so `same_spec` holds and the obligation's statement is untouched.
    """
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- concrete input points for the admissibility case. Written as one-line
# ---- record literals: a multi-line brace literal inside the `do` block does not
# ---- parse (`unexpected identifier; expected '}'`), measured.
def _dep(app, name):
    return (f'{{ app := "{app}", name := "{name}", '
            f"fieldName := none, create := true }}")


_ADM_ROUTED = ('{ target := RelRef.resolved "testapp" "Publisher", '
               'through := some (RelRef.resolved "contract" "Contract"), '
               "swappable := none }")
_ADM_UNROUTED = ('{ target := RelRef.resolved "testapp" "Publisher", '
                 "through := none, swappable := none }")
_ADM_SWAPPABLE = ("{ target := RelRef.selfRef, through := none, "
                  'swappable := some "AUTH_USER_MODEL" }')
_ADM_SELF_ROUTED = ("{ target := RelRef.selfRef, "
                    "through := some RelRef.selfRef, swappable := none }")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `relationDependenciesTester f appLabel modelName = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped.
_TESTER = (
    "extract_program_for relationDependencies\n"
    "prove_precondition_decidable_for relationDependencies\n"
    "prove_postcondition_decidable_for relationDependencies\n"
    "derive_tester_for relationDependencies\n\n"
)


def _witness(field_lit, app_label, model_name):
    return (
        _TESTER
        + f'example : relationDependenciesTester ({field_lit}) '
        + f'"{app_label}" "{model_name}" = false := by\n  decide\n'
    )


# Readable RelField literal helper. Refs are given as already-resolved
# (`RelRef.resolved app name`) or `RelRef.selfRef` so the tester reduces under
# `decide` (the qualified/bare arms apply a case fold that does not
# kernel-reduce); the dependency-shaping combination each rival abuses is
# exercised identically through these arms.
def _field(target, through, swappable):
    return (f"{{ target := {target}, through := {through}, "
            f"swappable := {swappable} }}")


_RESOLVED = "RelRef.resolved"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Ports the nagini positive
    # control's ARGUMENT ("a faithful, structurally-different correct impl is not
    # rejected") onto this carrier.
    #
    # AUDIT REPAIR. The original case here only renamed the frozen locals (`d` ->
    # `base`) and lifted the `some` arm's expression into a second `let`. That is
    # a DEFINITIONAL (zeta) reshape, not a structural one: measured, `rfl` closes
    # the equation between that body and the frozen body, and the frozen proof
    # script therefore discharges it without doing any new work. It passed
    # honestly while testing nothing — the SPEC-TOO-STRONG direction was
    # unprobed. Replaced with an assembly the carrier does NOT identify with the
    # frozen one: cons the base dependency onto a tail produced by eliminating
    # the intermediary option with `Option.elim`. Measured: this body with the
    # FROZEN proof verbatim FAILS (residual goal `baseDep … :: f.through.elim …
    # = match f.through with …`), so the obligation is genuinely REPROVEN here by
    # the retuned tactic body, and it then verifies EXIT 0. Both the impl region
    # and the `prove_correct` body are elided from the consumer spec view, so
    # `same_spec` holds and the frozen obligation's statement is byte-identical.
    # =====================================================================
    {
        "id": "pos-elim-cons-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return baseDep f appLabel modelName ::\n"
            "      f.through.elim [] (fun thr => [mkDep (resolveRef thr appLabel modelName)])",
            "prove_correct relationDependencies by\n"
            "  loom_solve\n"
            "  simp only [relationDeps]\n"
            "  cases f.through <;> simp_all"),
        "rationale": "PASS SOURCE = Q. Assembling the result as a CONS of the base "
                     "dependency onto a tail obtained by eliminating the "
                     "intermediary option (`Option.elim` — empty when the relation "
                     "is not routed, a singleton intermediary dependency when it "
                     "is) is observationally identical to the frozen impl on both "
                     "legs, but is NOT definitionally equal to it: the frozen "
                     "proof script leaves the residual goal `baseDep … :: "
                     "f.through.elim … = match f.through with …`, so Q is "
                     "REPROVEN for the new shape by casing on the option. A "
                     "faithful correct impl whose assembly shape differs MUST "
                     "verify; if it could not, the postcondition would "
                     "over-constrain the assembly shape rather than the dependency "
                     "VALUES (SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — added by audit. The port omitted this lane, reasoning that
    # the method has no `require` clause so nothing could exclude an input. That
    # disposes of the PRECOND-TOO-STRONG probe in its classic form but not of the
    # lane: on a TOTAL carrier the analogue is the obligation being UNSATISFIABLE
    # at an issue-shaped input, which a positive that discharges Q at that
    # concrete input — by evaluation, as a `have`, before closing the frozen
    # obligation verbatim — tests directly. Landed rather than recorded as
    # vacuous; measured EXIT 0.
    #
    # Content-bearing on purpose: `_BASE` verbatim would only re-test that the
    # shipped bundle verifies (G-VERIFY's job) and would attest nothing about
    # admissibility. Each `have` pins what one reachable sub-domain of Q
    # EVALUATES to, so the case fails if any sub-domain is unreachable or
    # resolves to something other than the shape this battery's rivals attack.
    # =====================================================================
    {
        "id": "admiss-total-domain-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- Admissibility on a total domain: no `require` can exclude an\n"
            "    -- input, so the live risk is an UNSATISFIABLE post-image at an\n"
            "    -- issue-shaped input. Each point is discharged by evaluation\n"
            "    -- BEFORE the frozen body runs for the real argument.\n"
            f"    have _routedCrossApp : relationDeps {_ADM_ROUTED} "
            f'"authors" "author" = [{_dep("testapp", "Publisher")}, '
            f'{_dep("contract", "Contract")}] := by\n'
            "      decide\n"
            f"    have _unrouted : relationDeps {_ADM_UNROUTED} "
            f'"authors" "author" = [{_dep("testapp", "Publisher")}] := by\n'
            "      decide\n"
            f"    have _swappableTarget : relationDeps {_ADM_SWAPPABLE} "
            f'"authors" "author" = [{_dep("__setting__", "AUTH_USER_MODEL")}] := by\n'
            "      decide\n"
            f"    have _selfRouted : relationDeps {_ADM_SELF_ROUTED} "
            f'"authors" "author" = [{_dep("authors", "author")}, '
            f'{_dep("authors", "author")}] := by\n'
            "      decide\n"
            + _IMPL),
        "rationale": "the method has NO `require` clause, so the domain is total "
                     "and the classic 'a normal input is admitted' probe has "
                     "nothing to exclude. Re-aimed at the residual admissibility "
                     "risk on a total carrier: that Q's post-image is jointly "
                     "SATISFIABLE, and that each sub-domain the postcondition "
                     "distinguishes is REACHABLE with the value the rivals are "
                     "aimed at. Four points are discharged by `decide` inside the "
                     "elided impl region — a relation routed through an "
                     "intermediary in a DIFFERENT application than its target "
                     "(the two-element list whose second entry is the "
                     "intermediary's own pair); an unrouted relation (the "
                     "one-element list); a swappable target (the sentinel "
                     "setting dependency); and a self-reference routed through "
                     "itself (both entries the owning pair) — after which the "
                     "frozen body discharges the ensures for the real argument. "
                     "If any point were unreachable or evaluated differently, "
                     "the obligation would be unsatisfiable exactly where the "
                     "battery aims (PRECOND-TOO-STRONG on this carrier).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve.
    # =====================================================================

    # ---- the through dependency must resolve the INTERMEDIARY reference ----
    {
        "id": "weak-through-uses-target",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton VERBATIM: when the relation is routed through an
        # intermediary, resolve the field's own TARGET reference for the extra
        # dependency instead of the intermediary reference. Correct on every
        # input where target and through resolve identically; wrong otherwise.
        "module": _impl(
            "    let d : Dep := baseDep f appLabel modelName\n"
            "    let deps : List Dep := match f.through with\n"
            "      | none     => [d]\n"
            "      | some thr => [d, mkDep (resolveRef f.target appLabel modelName)]\n"
            "    return deps"),
        "refinement": "this IS the pre-patch behaviour: the intermediary "
                      "dependency is computed from the field's own target "
                      "reference rather than from the intermediary reference. On "
                      "the failing scenario the intermediary model lives in a "
                      "DIFFERENT application from the target, so the intermediary "
                      "dependency points at the target's application instead of "
                      "the intermediary's, and the required dependency set is "
                      "missing the intermediary's entry — exactly the failure the "
                      "fix repairs. It would NOT resolve.",
        "rationale": "REJECT from Q: `relationDeps` pins the second list element "
                     "to `mkDep (resolveRef thr …)` (the intermediary), so any "
                     "impl resolving `f.target` for it violates the postcondition "
                     "whenever the two references resolve to different pairs. "
                     "Verifying would be SPEC-TOO-WEAK (the intermediary vs target "
                     "distinction unenforced). Refuted at a field whose target and "
                     "through are in different apps.",
        "witness": _witness(
            _field(f'{_RESOLVED} "testapp" "Publisher"',
                   f'some ({_RESOLVED} "contract" "Contract")', "none"),
            "authors", "author"),
    },

    # ---- the through dependency must resolve BOTH components of the ----
    # ---- intermediary reference, not just the object name ----
    {
        "id": "weak-through-app-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The finer near-miss: build the intermediary dependency's OBJECT NAME
        # correctly from the intermediary reference, but take its APP LABEL from
        # the field's own target reference. Correct only when target and through
        # resolve to the same app; wrong when they live in different apps. Built
        # by projecting the resolver's returned pair componentwise (`.1`/`.2`) in
        # the impl region — this does NOT re-open the modeled `resolveRef` callee,
        # it only reads the (app, name) pair the callee already returns.
        "module": _impl(
            "    let d : Dep := baseDep f appLabel modelName\n"
            "    let deps : List Dep := match f.through with\n"
            "      | none     => [d]\n"
            "      | some thr => [d, { app := (resolveRef f.target appLabel modelName).1,\n"
            "                          name := (resolveRef thr appLabel modelName).2,\n"
            "                          fieldName := none, create := true }]\n"
            "    return deps"),
        "refinement": "a subtler variant of the pre-patch bug: the intermediary "
                      "dependency's object name is resolved correctly from the "
                      "intermediary reference, but its application label is taken "
                      "from the field's own target. On the failing scenario the "
                      "intermediary model lives in a DIFFERENT application from the "
                      "target, so the intermediary dependency points at the "
                      "target's application while carrying the intermediary's "
                      "object name — a dependency on a pair that names no real "
                      "model, so the required intermediary entry is still missing. "
                      "It would NOT resolve.",
        "rationale": "REJECT from Q: `relationDeps` pins the second list element to "
                     "`mkDep (resolveRef thr …)`, whose app component is "
                     "`(resolveRef thr …).1`; an impl taking the app from "
                     "`resolveRef f.target …` violates the postcondition whenever "
                     "target and through resolve to different apps. Verifying would "
                     "leave the app half of the intermediary resolution unenforced "
                     "(SPEC-TOO-WEAK), which weak-through-uses-target — flipping "
                     "BOTH components at once — does not isolate. Refuted at a "
                     "field whose target and through are in different apps.",
        "witness": _witness(
            _field(f'{_RESOLVED} "testapp" "Publisher"',
                   f'some ({_RESOLVED} "contract" "Contract")', "none"),
            "authors", "author"),
    },

    # ---- the through dependency must be PRESENT when routed through ----
    {
        "id": "weak-drop-through",
        "kind": "uniqueness",
        "expect": "reject",
        # Never appends the intermediary dependency: returns just the base
        # dependency on every input, dropping the through entry entirely. Correct
        # only when the relation is not routed through an intermediary.
        "module": _impl(
            "    let d : Dep := baseDep f appLabel modelName\n"
            "    let deps : List Dep := match f.through with\n"
            "      | none     => [d]\n"
            "      | some thr => [d]\n"
            "    return deps"),
        "refinement": "dropping the intermediary dependency entirely is what a "
                      "real patch that removed the through-dependency branch would "
                      "do: a relation routed through an intermediary model would "
                      "no longer depend on that model's creation, so the "
                      "intermediary's entry is absent from the dependency set and "
                      "the create ordering the tests pin is broken. It would NOT "
                      "resolve.",
        "rationale": "REJECT from Q: `relationDeps` returns a TWO-element list on "
                     "the through leg (`[baseDep …, mkDep (resolveRef thr …)]`); "
                     "an impl returning a singleton contradicts the postcondition "
                     "by list length on any routed relation. Refuted at a field "
                     "with a through reference.",
        "witness": _witness(
            _field(f'{_RESOLVED} "app1" "One"',
                   f'some ({_RESOLVED} "app2" "Two")', "none"),
            "authors", "author"),
    },

    # ---- the base dependency must honour the swappable branch ----
    {
        "id": "weak-ignore-swappable",
        "kind": "uniqueness",
        "expect": "reject",
        # Base dependency always resolves the field's target, ignoring the
        # swappable-setting branch. Correct whenever the target is not swappable;
        # wrong for a swappable target, where the base dependency must point at
        # the swappable setting under its sentinel application.
        "module": _impl(
            "    let d : Dep := mkDep (resolveRef f.target appLabel modelName)\n"
            "    let deps : List Dep := match f.through with\n"
            "      | none     => [d]\n"
            "      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]\n"
            "    return deps"),
        "refinement": "a real patch that dropped the swappable-setting branch "
                      "would emit a concrete dependency on the resolved target for "
                      "a field pointing at a swappable model, instead of the "
                      "indirect dependency on the swappable setting under its "
                      "sentinel application — breaking the tests that pin the "
                      "swappable-model dependency shape. It would NOT resolve.",
        "rationale": "REJECT from Q: `relationDeps` routes the base dependency "
                     "through `baseDep`, whose swappable arm yields the sentinel "
                     "`__setting__` dependency; an impl that always resolves "
                     "`f.target` contradicts the postcondition for any swappable "
                     "field. Verifying would leave the swappable clause unenforced "
                     "(SPEC-TOO-WEAK). Refuted at a field with a swappable "
                     "setting.",
        "witness": _witness(
            _field(f'{_RESOLVED} "testapp" "Publisher"', "none",
                   'some "AUTH_USER_MODEL"'),
            "authors", "author"),
    },

    # ---- the two dependencies must be emitted in the CORRECT ORDER ----
    {
        "id": "weak-deps-order-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit: every shipped rival attacked the dependency VALUES, so
        # the postcondition's ORDER half (Q pins a LIST, whose second element is
        # the intermediary's) was unattacked. This rival computes both
        # dependencies correctly and emits them transposed — a rival wrong ONLY
        # in position, which no value-level rival isolates.
        "module": _impl(
            "    let d : Dep := baseDep f appLabel modelName\n"
            "    let deps : List Dep := match f.through with\n"
            "      | none     => [d]\n"
            "      | some thr => [mkDep (resolveRef thr appLabel modelName), d]\n"
            "    return deps"),
        "refinement": "emitting the intermediary dependency BEFORE the base "
                      "dependency inverts the order of the dependency list a "
                      "routed relation induces. The dependency list is consumed "
                      "positionally by the callers that shape the ordering "
                      "constraints, so a patch that transposed the two entries "
                      "would hand back the intermediary where the target "
                      "dependency is expected and vice versa, breaking the tests "
                      "that pin the dependency sequence of a routed relation. It "
                      "would NOT resolve.",
        "rationale": "REJECT from Q: `relationDeps` pins `out` to a LIST whose "
                     "FIRST element is `baseDep f appLabel modelName` and whose "
                     "SECOND is `mkDep (resolveRef thr …)`; list equality is "
                     "positional, so an impl emitting them transposed violates the "
                     "postcondition on every routed relation whose two "
                     "dependencies differ. Verifying would leave the ORDER half of "
                     "Q unenforced (SPEC-TOO-WEAK) — the shipped value-level "
                     "rivals all keep the order and so cannot isolate it. Refuted "
                     "at the cross-application routed field.",
        "witness": _witness(
            _field(f'{_RESOLVED} "testapp" "Publisher"',
                   f'some ({_RESOLVED} "contract" "Contract")', "none"),
            "authors", "author"),
    },

    # ---- the base dependency must resolve with the scope args in order ----
    {
        "id": "weak-base-args-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Base dependency resolves the target with the owning scope arguments
        # SWAPPED (modelName as app label, appLabel as model name). For a
        # self-reference this yields the swapped owning pair; correct only when
        # the owner's app label and model name coincide. Moves the appLabel and
        # modelName binders that the other reject witnesses hold fixed.
        "module": _impl(
            "    let d : Dep := match f.swappable with\n"
            "      | some s => { app := \"__setting__\", name := s, fieldName := none, create := true }\n"
            "      | none   => mkDep (resolveRef f.target modelName appLabel)\n"
            "    let deps : List Dep := match f.through with\n"
            "      | none     => [d]\n"
            "      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]\n"
            "    return deps"),
        "refinement": "resolving in the owner's scope with the application label "
                      "and model name transposed points a self-referential or "
                      "bare-name relation's base dependency at the wrong "
                      "application/object pair, breaking the self-FK and "
                      "same-app dependency tests that pin the owning scope's "
                      "orientation. It would NOT resolve.",
        "rationale": "REJECT from Q: `relationDeps`'s base dependency resolves the "
                     "target in the scope `(appLabel, modelName)` in that order; "
                     "transposing them contradicts the postcondition whenever the "
                     "two differ (e.g. a self-reference resolves to the transposed "
                     "owning pair). Refuted at a self-reference with distinct "
                     "appLabel and modelName, which also varies both scope "
                     "binders the other witnesses fix.",
        "witness": _witness(
            _field("RelRef.selfRef", "none", "none"),
            "aaa", "bbb"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 4 uniqueness rivals) plus an empty
# AXIOM_TESTS. This bundle models the SAME operation (the migration dependencies
# a relational field induces, including the intermediary-model dependency of the
# issue) but over a fully TRANSPARENT, referentially-pure carrier, so the
# frame/permission class collapses while the partial-domain rivals port directly
# and gain machine-checked witnesses. Every sibling case is accounted for below.
#
#   sibling case (nagini)         -> here
#   -----------------------------------------------------------------------
#   pos-control-local-reshape     -> pos-elim-cons-reshape          PORTED
#   admissibility-f2p-shaped      -> admiss-total-domain-reachable  RE-AIMED
#   frame-mutate-through-ref      -> (none)                         VACUOUS
#   wrong-ref-primary-prepatch    -> weak-through-uses-target       PORTED
#   wrong-app-from-primary        -> weak-through-app-only          PORTED
#   no-lowercase-objname          -> (none)                         SUBSUMED (deep-model callee)
#   split-on-last-dot             -> (none)                         SUBSUMED (deep-model callee)
#   AXIOM_TESTS (empty)           -> (none)                         DROPPED
#
# ADDED (4, no direct sibling counterpart, faithful to the sibling's
# spec-strength SPIRIT on this carrier's transparent sub-behaviors — the nagini
# model contracts only the through-reference resolution as a scalar (app, name)
# pair, whereas this bundle models the WHOLE dependency list, so the base
# dependency's swappable branch and scope-argument order are additional
# transparent clauses of the sole postcondition worth attacking):
#   weak-drop-through        — omits the intermediary dependency entirely
#       (attacks the presence/length of the through entry).
#   weak-ignore-swappable    — base dependency ignores the swappable branch.
#   weak-base-args-swapped   — base dependency resolves with the owning scope
#       arguments transposed (also the case that moves appLabel/modelName).
#   weak-deps-order-swapped  — both dependencies computed CORRECTLY but emitted
#       transposed (attacks the ORDER half of Q, which every value-level rival
#       leaves untouched). Added by audit.
#
# PORTED / SUBSUMED, with reasons:
#   * wrong-ref-primary-prepatch -> weak-through-uses-target is the literal
#     pre-patch bug (resolve the field's own target for the intermediary
#     dependency instead of the intermediary reference), refuted at a
#     different-app field.
#   * wrong-app-from-primary (the nagini near-miss that took only the app label
#     from the wrong reference) is PORTED as weak-through-app-only. It IS a
#     distinct impl-region decision on this carrier: the impl reads the resolver's
#     returned pair componentwise (`(resolveRef thr …).2` for the name,
#     `(resolveRef f.target …).1` for the app), which does NOT re-open the modeled
#     `resolveRef` callee — it only projects the (app, name) pair the callee
#     already returns. The rival rejects and its witness discriminates (rival
#     elaborates, gold fails with a semantic `decide proved … is false`) at a
#     field whose target and through are in different apps. It isolates the
#     app-half of the intermediary resolution that weak-through-uses-target
#     (which flips both components at once) does not.
#   * no-lowercase-objname and split-on-last-dot attack the RESOLVER's internal
#     normalization (the object-name case fold and the first-vs-last split point).
#     Here the resolver is a deeply-modeled A-reference callee (`resolveRef`,
#     validated == the real resolver by G-AX), NOT logic inside the region a
#     variant edits. A variant cannot re-open the callee without touching the
#     frozen pure region, so these are not expressible as impl-region rivals;
#     their soundness is G-AX's charge (it fuzzes mixed-case and dotted-multi
#     references against the real resolver), not this gate's. Recorded rather
#     than faked.
#
# RE-AIMED (was OMITTED; corrected by audit):
#   * admissibility-f2p-shaped -> admiss-total-domain-reachable. The sibling case
#     discharges the operation's PRECONDITION (a dot in the intermediary
#     reference) for a normal input, and this method has no `require` clause, so
#     the classic form of the probe is indeed vacuous. The earlier reasoning then
#     dropped the LANE, arguing the post-image is satisfiable "by construction"
#     because the frozen proof verifies. That argument proves the obligation is
#     satisfiable by GOLD's body, which is G-VERIFY's charge, and leaves the
#     admissibility direction of THIS gate untested. The analogue on a total
#     carrier is the obligation being unsatisfiable at an issue-shaped input, and
#     a positive that discharges Q at that concrete input BY EVALUATION tests it
#     directly — so the lane is landed rather than recorded as vacuous. Measured
#     EXIT 0; the four `have`s also pin that each sub-domain the rivals attack is
#     REACHABLE with the value they assume.
#
# VACUOUS (frame / permission-mutation): nagini's frame-mutate-through-ref relies
#   on a fractional heap permission an impl can overwrite
#   (`Acc(list_pred(through_ref),1/2)`). This backend is referentially
#   transparent and this bundle declares no `mut` PARAMETER — all inputs are
#   immutable values with no heap footprint — so there is no read-only input to
#   overwrite and no substitute probe to build. No permission probe fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   `resolveRef` == the real resolver, including the case fold and first-dot
#   split the subsumed near-misses concern) and this gate ignores AXIOM_TESTS
#   regardless.
#
# COVERAGE. The sole obligation (`prove_correct relationDependencies`) is
# defended (pos-elim-cons-reshape), shown SATISFIABLE at four concrete
# issue-shaped inputs (admiss-total-domain-reachable), and attacked by five
# rivals. The single postcondition clause Q is attacked at each of its
# independent sub-behaviors: the intermediary-reference resolution
# (weak-through-uses-target), the app half of that resolution in isolation
# (weak-through-app-only), the presence of the through entry
# (weak-drop-through), the swappable branch of the base dependency
# (weak-ignore-swappable), the base dependency's scope-argument order
# (weak-base-args-swapped), and the POSITION of the two entries
# (weak-deps-order-swapped). All three input binders are varied across the
# reject witnesses: the field configuration `f` moves its target shape (resolved
# vs selfRef), its through option (some vs none), and its swappable option (some
# vs none); `appLabel` and `modelName` move at weak-base-args-swapped
# ("aaa"/"bbb") against the others' ("authors"/"author").
#
# SPEC-STRENGTH PROBES RUN BY THE AUDIT and NOT shipped (each rejected, so each
# is a clause the frozen spec already pins — recorded so the next reader does
# not re-derive them): the through dependency resolved with the owning scope
# arguments transposed; the through dependency built with `create := false`; the
# through dependency carrying a non-`none` `fieldName`; and the swappable
# sentinel written with the setting name as the application and the sentinel as
# the object name. No wrong impl was found that the spec accepts.
AXIOM_TESTS = []

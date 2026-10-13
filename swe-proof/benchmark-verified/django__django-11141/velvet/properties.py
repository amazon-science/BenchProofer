"""properties.py — G-PBT falsification battery for django__django-11141 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery edits only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body — both of
which the consumer spec view elides — so ``markers.same_spec`` holds and the
``prove_correct classifyMigrationSources`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier: ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over one read-only sources input).

    classifyMigrationSources (sources : List MigrationSource)
        return (out : List Bool)
      ensures out = classifyAll sources

There is ONE method, ONE top-level post-image clause, and NO ``require`` clause
(the admitted domain is total). ``classifyAll`` is a fully unfolded function of
the method's own argument: it maps, in input order, the per-source verdict
``classify`` over every source. ``classify m`` is a total, fully unfolded pure
function of the source's four observations:

    classify m = if m.isPackage
                 then (!m.migrationNames.isEmpty || m.ignoreMissing)
                 else false

The load-bearing content of ``out = classifyAll sources`` is that each source's
verdict is decided by package-ness, the discovered-migration emptiness, and the
keep-empty configuration flag ALONE — the implicit-namespace observation
(``isNamespace``) is a carried field that the verdict does NOT read. The four
per-source observations are the sub-structure the reject rivals below abuse.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival writes back into a read-only sequence input that
    carries only a fractional heap permission and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every parameter
    is an immutable value, this bundle declares NO ``mut`` parameter (``sources``
    is read-only by being non-``mut``), there is no heap and no aliasing. There
    is no read-only input to overwrite and no permission system to trip, so the
    class is vacuous. No substitute is fabricated (per the porting map, this
    class is legitimately dropped here rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``classifyAll sources`` — computed entirely from the method's
    own argument by a concrete ``def`` in the ``pure`` region (the ``axioms``
    region is empty; no opaque answer key, no consumed callee contract). There
    is no value an echo could carry that satisfies the ensures yet is
    behaviourally wrong — the unique satisfier IS the grounded classification.
    The honest controls are the cheapest faithful reshapes (the ``pos-*``).
  * CONTROL-FLOW / SIDE-EFFECT — N/A. The method returns a pure ``List Bool``
    verdict; the migrated-vs-unmigrated control point IS the returned Bool,
    fully captured by the ensures. There is no raise / effect difference
    invisible to the value abstraction.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. The per-source decision surface
    has several sub-domains a rival can get right on most inputs yet diverge on
    one: the implicit-namespace-independence (the B1 fix), the discovered-name
    emptiness (the B2 fix), and the keep-empty-flag disjunct.

CARRIER NOTE — WHY WITNESSES ARE LOOP-FREE. The frozen impl is a ``while`` loop;
its extracted program compiles to ``forIn`` / well-founded recursion and does
NOT reduce under kernel ``decide`` (the ``classifyMigrationSourcesTester`` gets
stuck on the loop). Every reject rival below is therefore written LOOP-FREE (a
single ``List.map`` closed form), so ITS extracted program reduces and
``classifyMigrationSourcesTester args = false`` decides against it. This is
exactly what makes each witness a discriminator: the SAME ``decide`` fails to
reduce against the frozen loop-based solution, so half 2 (fails on gold) holds
by construction while half 1 (elaborates against the rival) is a genuine
counterexample. The carrier is fully transparent (the four observations are
concrete ``Bool``/``List String``), so no opaque leaf blocks reduction and no
conditioning on a hypothesis is needed — every witness is a concrete literal.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; the
classification is modeled deeply over concrete observations (``classify`` /
``classifyAll``), so nothing in the proof rests on a callee contract. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11141"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim (between -- impl-start and -- impl-end).
# ---- Full-replacement rivals and the closed-form positive swap THIS for a new
# ---- body; the fragment lies wholly inside the impl region and is unique. ----
_GOLD_IMPL = (
    "    let mut result : List Bool := []\n"
    "    let mut i := sources.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ sources.length\n"
    "      invariant result = classifyAll (sources.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let m := sources[i - 1]!\n"
    "      result := classify m :: result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _GOLD_IMPL in _BASE, "gold impl region drifted from Solution.lean"

# ---- the loop-body step (element read + front-prepend), for the in-loop
# ---- reshape positive. Unique in the file, wholly inside the impl region. ----
_LOOP_STEP = (
    "      let m := sources[i - 1]!\n"
    "      result := classify m :: result"
)
assert _BASE.count(_LOOP_STEP) == 1, "loop-step anchor drift"

# ---- the accumulator-init line, for prepending the admissibility assert. ----
_RESULT_INIT = "    let mut result : List Bool := []\n"
assert _BASE.count(_RESULT_INIT) == 1, "result-init anchor drift"

# ---- the frozen proof block (tactic body only; elided from the spec view, so a
# ---- reshaped positive or an admissibility assert may retune it without
# ---- touching the spec or the `prove_correct` header). Unique in the file. ----
_PROVE = (
    "prove_correct classifyMigrationSources by\n"
    "  loom_solve\n"
    "  rw [classifyAll_drop_step sources i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _BASE.count(_PROVE) == 1, "frozen proof block drifted from Solution.lean"


# ---- witness preamble: reach the method contract through Velvet's own tester
# ---- machinery. `classifyMigrationSourcesTester args = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. Each argument is a
# ---- concrete literal list, so `decide` reduces (the loop-free rival) or gets
# ---- stuck (the frozen loop).
_TESTER = (
    "extract_program_for classifyMigrationSources\n"
    "prove_precondition_decidable_for classifyMigrationSources\n"
    "prove_postcondition_decidable_for classifyMigrationSources\n"
    "derive_tester_for classifyMigrationSources\n\n"
)


def _witness(sources_lit):
    return _TESTER + (
        f"example : classifyMigrationSourcesTester {sources_lit} = false := by\n"
        "  decide\n")


# ---- MigrationSource literal helper for readable witnesses / asserts. Field
# ---- order: isPackage, isNamespace, migrationNames, ignoreMissing.
def _src(pkg, ns, names, ignore):
    ns_list = "[" + ", ".join(f'"{n}"' for n in names) + "]"
    return (f"{{ isPackage := {str(pkg).lower()}, "
            f"isNamespace := {str(ns).lower()}, "
            f"migrationNames := {ns_list}, "
            f"ignoreMissing := {str(ignore).lower()} }}")


# ---- reject-rival bodies (loop-free closed forms over `sources.map`). ----

# B1: reintroduce the removed implicit-namespace guard — a source with no single
# backing file is unmigrated outright, BEFORE consulting package-ness / the
# discovered names. `classify` OMITS `isNamespace`, so this diverges wherever a
# namespace source is a package with discovered migrations.
_R_MARKER = (
    "    let out := sources.map (fun m =>\n"
    "      if m.isNamespace then false\n"
    "      else (if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing)\n"
    "            else false))\n"
    "    return out"
)

# B2: every source that is a package is migrated UNCONDITIONALLY, ignoring the
# discovered-name emptiness and the keep-empty flag.
_R_EMPTY = (
    "    let out := sources.map (fun m => m.isPackage)\n"
    "    return out"
)

# Drop the keep-empty disjunct: migrated iff a package AND at least one
# discovered migration, dropping `|| m.ignoreMissing`.
_R_DROP_TOLERATE = (
    "    let out := sources.map (fun m => m.isPackage && !m.migrationNames.isEmpty)\n"
    "    return out"
)

# Supporting mechanical mirror: invert every verdict.
_R_INVERTED = (
    "    let out := sources.map (fun m =>\n"
    "      !(if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing)\n"
    "        else false))\n"
    "    return out"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation with a byte-identical
    # statement and retunes only the elided proof body (or nothing).
    # =====================================================================
    {
        "id": "pos-closed-form-direct",
        "kind": "soundness",
        "expect": "verify",
        # Loop-free reshape: return the modeled classification directly. A wholly
        # different executable shape (no accumulator loop) over identical logic;
        # `loom_solve` alone closes it since the ensures is `out = classifyAll
        # sources` definitionally. This is the honest cheapest correct impl (it
        # must compute the real classification of its own argument), the analogue
        # of the sibling's direct grounded-computation positive.
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    let out := classifyAll sources\n    return out"),
            _PROVE,
            "prove_correct classifyMigrationSources by\n  loom_solve"),
        "rationale": "a loop-free impl that produces the modeled classification "
                     "directly is observationally `classifyAll sources` on every "
                     "input, so the single ensures clause discharges; a correct "
                     "reshape must verify, else the postcondition is over-fit to "
                     "the accumulator-loop code form => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inline-elem-read",
        "kind": "soundness",
        "expect": "verify",
        # In-loop reshape: inline the indexed element read into the classify call
        # instead of naming it in a `let`. Same backward accumulator loop, same
        # front-prepend and invariants, same value flow — the frozen proof still
        # closes verbatim. The analogue of the sibling's branch-reordered positive
        # (structurally different, behaviourally identical).
        "module": _swap(
            _BASE, _LOOP_STEP,
            "      result := classify sources[i - 1]! :: result"),
        "rationale": "inlining the indexed element read (`sources[i-1]!`) into the "
                     "front-prepend leaves the accumulator loop, the invariants "
                     "and the assembled value unchanged, so `out = classifyAll "
                     "sources` still holds and the frozen proof closes; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on the code form.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the sibling's
    # "a normal F2P-shaped input satisfies the precondition" probe is vacuous:
    # nothing could exclude an in-domain input. Re-aimed at the residual risk on
    # a total domain — that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point. This case discharges a live in-region `assert`, at a
    # concrete three-source list, that the classification really discriminates
    # the sub-behaviours the fix cares about: a namespace package WITH a
    # discovered migration (the F2P scenario: no backing file) classifies the
    # SAME as a file-backed package with the same migration — both migrated —
    # demonstrating the implicit-namespace observation does not gate the verdict;
    # and an empty non-tolerated package classifies unmigrated. The surrounding
    # impl is kept verbatim so the ensures clause still discharges; the proof is
    # retuned only to clear the extra assert goal by `decide` (allowed — the
    # tactic body is elided from the spec view). The assert is live: a false
    # claim about the same point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-classification-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _RESULT_INIT,
                "    assert (with_name_prefix `admiss\n"
                "      (classifyAll\n"
                "        [{ isPackage := true, isNamespace := true, "
                "migrationNames := [\"m\"], ignoreMissing := false },\n"
                "         { isPackage := true, isNamespace := false, "
                "migrationNames := [\"m\"], ignoreMissing := false },\n"
                "         { isPackage := true, isNamespace := false, "
                "migrationNames := [], ignoreMissing := false }]\n"
                "        = [true, true, false]))\n"
                + _RESULT_INIT),
            _PROVE,
            "prove_correct classifyMigrationSources by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [classifyAll_drop_step sources i (by omega) (by omega)]; "
            "simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at an "
                     "F2P-shaped point: a namespace package with a discovered "
                     "migration classifies the SAME (migrated) as a file-backed "
                     "package with the same migration — so the modeled behaviour "
                     "genuinely does NOT read the implicit-namespace observation "
                     "the fix removes from the decision — and an empty "
                     "non-tolerated package classifies unmigrated. The in-region "
                     "assert must discharge (else the classification would be "
                     "constant / the obligation degenerate); the impl is kept "
                     "verbatim so the ensures clause discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the
    # frozen spec that MUST be rejected, each with a machine-checked refutation
    # witness at a concrete input (the decidable boundary) and the argument that
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-namespace-dependence",
        "kind": "uniqueness",
        "expect": "reject",
        # The B1 pre-patch behaviour: reintroduce the removed implicit-namespace
        # guard, so a source with no single backing file is unmigrated outright.
        "module": _swap(_BASE, _GOLD_IMPL, _R_MARKER),
        "refinement": "this IS the pre-patch behaviour on the removed guard: a "
                      "source with no single backing file is discarded as "
                      "unmigrated before its discovered migrations are consulted. "
                      "Its faithful real counterpart sends an implicit namespace "
                      "package that holds a discovered migration into the "
                      "unmigrated set, so that migration is never discovered and "
                      "the forwards plan cannot be built — exactly the failing "
                      "test, which asserts a namespace-package migration IS "
                      "loaded. It would NOT resolve.",
        "rationale": "REJECT from `out = classifyAll sources`: `classify` OMITS "
                     "`isNamespace`, so on a source that is a package with a "
                     "discovered migration and no backing file the post-image "
                     "demands `true` but the rival returns `false`. Verifying "
                     "would be SPEC-TOO-WEAK (the namespace-independence the fix "
                     "pins is unenforced). This is the ONLY reject witness moving "
                     "`isNamespace` to true.",
        "witness": _witness("[" + _src(True, True, ["m"], False) + "]"),
    },
    {
        "id": "weak-empty-as-migrated",
        "kind": "uniqueness",
        "expect": "reject",
        # The B2 pre-patch behaviour: every source that is a package is migrated
        # unconditionally, ignoring the discovered-name count and the flag.
        "module": _swap(_BASE, _GOLD_IMPL, _R_EMPTY),
        "refinement": "this IS the pre-patch behaviour on the count check: a "
                      "package exposing no discovered migrations and with the "
                      "keep-empty flag off is nonetheless recorded migrated. Its "
                      "faithful real counterpart regresses the test that asserts "
                      "an empty package must NOT be treated as migrated. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = classifyAll sources`: on a package source "
                     "with no discovered migrations and the keep-empty flag off "
                     "the post-image demands `false` (via `!isEmpty || "
                     "ignoreMissing`) but the rival returns `true`. Verifying "
                     "would be SPEC-TOO-WEAK (the emptiness sub-clause unpinned). "
                     "Refuted at an empty non-tolerated package.",
        "witness": _witness("[" + _src(True, False, [], False) + "]"),
    },
    {
        "id": "weak-drop-keep-empty-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the keep-empty disjunct: migrated iff a package AND at least one
        # discovered migration, dropping `|| m.ignoreMissing`.
        "module": _swap(_BASE, _GOLD_IMPL, _R_DROP_TOLERATE),
        "refinement": "a real patch that recorded a package migrated only when it "
                      "exposes at least one discovered migration — dropping the "
                      "keep-empty configuration disjunct — classifies a "
                      "configured-to-keep empty package as unmigrated, "
                      "contradicting the documented keep-empty contract the "
                      "pass-to-pass tests bracket. It would NOT resolve.",
        "rationale": "REJECT from `out = classifyAll sources` via the "
                     "`|| m.ignoreMissing` disjunct: on a package source with no "
                     "discovered migrations but the keep-empty flag ON the "
                     "post-image demands `true` but the rival returns `false`. "
                     "This is the ONLY reject witness moving `ignoreMissing` to "
                     "true.",
        "witness": _witness("[" + _src(True, False, [], True) + "]"),
    },
    {
        "id": "weak-inverted-verdict-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting mechanical mirror: invert every verdict. Diverges on EVERY
        # input; refuted here at a NON-package source, the only witness that moves
        # `isPackage` to false and exercises the `else false` (non-package) branch.
        "module": _swap(_BASE, _GOLD_IMPL, _R_INVERTED),
        "refinement": "inverting every verdict records every successfully-imported "
                      "package in the wrong set and every non-package in the other, "
                      "so essentially all loader tests (failing + pass-to-pass) "
                      "fail. It would NOT resolve. (Supporting near-miss; carries a "
                      "real refinement but does not replace the reasoned "
                      "partial-domain attacks above.)",
        "rationale": "REJECT from `out = classifyAll sources` for every input: the "
                     "rival returns `!classify m`. Refuted at a NON-package source "
                     "— where `classify` (hence the post-image) demands `false` "
                     "but the inverted rival returns `true`. This is the ONLY "
                     "reject witness moving `isPackage` to false, exercising the "
                     "non-package `else false` branch.",
        "witness": _witness("[" + _src(False, False, [], False) + "]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — one of which is the mandatory
# frame-mutation rival) over `is_migrated_app(has_regular_file_marker,
# exposes_search_path, migration_names, treat_empty_as_migrated) -> int`, whose
# per-input decision equals a grounded `@Pure migrated_code(...)`. This bundle
# contracts a SINGLE method `classifyMigrationSources` that maps the same
# per-source verdict (`classify`) over a `List MigrationSource`, so the sibling's
# scalar per-app decision maps onto the per-source `classify` and each rival
# re-aims at the corresponding sub-term of the one post-image
# `out = classifyAll sources`. The sibling's `has_regular_file_marker` (file
# marker PRESENT) is the negation of this backend's `isNamespace` (no backing
# file); both are OMITTED from the grounded verdict, and that omission is the B1
# fix both batteries pin.
#
#   sibling case                        -> here                             status
#   --------------------------------------------------------------------------------
#   pos-reorder-branch                  -> pos-inline-elem-read              PORTED (reshape)
#   pos-direct-oracle                   -> pos-closed-form-direct            PORTED (direct grounded)
#   admiss-fshaped-input                -> admiss-classification-nondegenerate RE-AIMED
#   frame-mutation-append-names         -> (none)                           VACUOUS
#   partial-domain-marker-dependence    -> weak-namespace-dependence        PORTED (B1)
#   partial-domain-empty-as-migrated    -> weak-empty-as-migrated           PORTED (B2)
#   partial-domain-drop-tolerate        -> weak-drop-keep-empty-flag        PORTED
#   inverted-codes-supporting           -> weak-inverted-verdict-supporting PORTED
#
# 6 ported, 1 re-aimed, 1 vacuous = maps the full sibling battery.
#
# VACUOUS (frame-mutation-append-names): the sibling's MANDATORY frame-mutation
#   rival keeps the gold body then writes back into the sole read-only sequence
#   input (`migration_names`) granted only at half permission, and must be
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, the method declares no
#   `mut` parameter (`sources` is read-only by being non-`mut`), there is no heap
#   and no aliasing. There is no read-only input to overwrite and no permission
#   system to trip, so the class is vacuous. No substitute is fabricated.
# RE-AIMED (admissibility): the sibling establishes the read-only half-permission
#   input is usable at 1/2 and a normal F2P-shaped input meets the precondition
#   via an in-region self-call. This backend has no permissions and no `require`
#   clause, so nothing could exclude a normal input — that probe is vacuous. It
#   is re-aimed at the residual admissibility risk on a total domain: that the
#   post-image is UNSATISFIABLE / DEGENERATE. The case discharges a concrete
#   in-region assert that the classification is exactly the per-source verdict at
#   an F2P-shaped point AND is namespace-independent (a namespace package with a
#   migration classifies the same as a file-backed one) — non-degenerate.
# PORTED-RESHAPED (pos-reorder-branch): the sibling's positive control reorders
#   the scalar decision into a single boolean expression with the branches
#   reordered. This backend's frozen impl is a backward accumulator loop, so the
#   reshape SPIRIT — "structurally different, behaviourally identical" — is
#   carried by pos-inline-elem-read (inline the indexed read into the classify
#   call); the direct grounded computation (the sibling's pos-direct-oracle) is
#   carried loop-free by pos-closed-form-direct.
#
# DIVERGENCE lane - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the four per-source
#   observations that `classifyAll` reads (pts = 4 distinct input points):
#     isPackage       — true (namespace-dependence, empty-as-migrated,
#                        drop-keep-empty), FALSE (inverted-verdict): both.
#     isNamespace     — TRUE (namespace-dependence), false (the other three):
#                        both. Only namespace-dependence moves it, which is the
#                        point — `classify` must NOT read it (B1 fix).
#     migrationNames  — non-empty (namespace-dependence), EMPTY (empty-as-migrated,
#                        drop-keep-empty, inverted-verdict): both.
#     ignoreMissing   — false (namespace-dependence, empty-as-migrated,
#                        inverted-verdict), TRUE (drop-keep-empty): both.
#   Every independent sub-clause of the post-image is attacked: the
#   namespace-independence (namespace-dependence / B1), the discovered-name
#   emptiness (empty-as-migrated / B2), the keep-empty disjunct
#   (drop-keep-empty), and the non-package `else false` branch + overall value
#   (inverted-verdict). No independent sub-term is left unattacked, and no binder
#   is held at a single value across all reject witnesses.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the classification is modeled deeply — `classify` / `classifyAll`),
#   so there is nothing here for this gate to probe.
AXIOM_TESTS = []

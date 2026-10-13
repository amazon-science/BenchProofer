"""properties.py — G-PBT falsification battery for django__django-11477 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct bindCaptures`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  bindCaptures (namedGroups : List Named) (positionalGroups : List String)
    return (out : Bindings)
    ensures out.named = keepPresent namedGroups
    ensures out.positional = (if out.named = [] then positionalGroups else [])

``keepPresent`` is a total, fully-unfolded pure fold over the capture list: it
concatenates the per-group contributions in order, where a group that bound a
value contributes itself and a group that bound nothing contributes nothing
(``keepOne``). The two independent ``ensures`` clauses pin, respectively:
  * (C1) the keyword bindings are EXACTLY the value-bearing groups, in order —
    the retention behaviour; and
  * (C2) the positional bindings are surfaced ONLY when there is no keyword
    binding, and are otherwise empty — the selection behaviour.
Both clauses are grounded in the two inputs (``namedGroups`` /
``positionalGroups``); neither is pinned to an opaque oracle, so there is no
answer-key echo to build.

ADVERSARIAL READ of the sibling classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer.)
  * WEAK / UNFILTERED — APPLIES, the headline SPEC-TOO-WEAK probe: keep EVERY
    group verbatim (the pre-patch behaviour), so a group that bound nothing
    leaks into the keyword bindings. Refuted by C1.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the domain but
    diverging on a sub-domain (dropping the FIRST group; leaking a TRAILING
    value-less group). Correct exactly on the complementary sub-domain.
  * CONTROL-FLOW on the selection clause — APPLIES: always surfacing the
    positional bindings regardless of whether keyword bindings exist. Refuted by
    C2.
  * UNGROUNDED-ORACLE ECHO — N/A. ``keepPresent`` / ``keepOne`` are concrete
    ``def``s in the ``pure`` region (the ``axioms`` region is empty — no opaque
    answer key to echo); the cheapest correct impl simply evaluates ``keepPresent``,
    which the positive controls cover honestly.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
frozen impl is a ``while`` loop, whose extracted tester does NOT reduce under
``decide`` (the fixpoint is opaque to the kernel) — which is exactly why every
witness FAILS against the frozen solution (half 2) yet ELABORATES against each
loop-free rival (half 1), making it a genuine discriminator rather than a
tautology. The four witnesses sit at four DISTINCT input points and vary the
binders: ``namedGroups`` ranges over a single value-less group, a single
value-bearing group, and a value-bearing-then-value-less pair; and the selection
rival is the only witness whose ``positionalGroups`` is NON-EMPTY — the sole
sub-domain on which surfacing the positional bindings is observably wrong. A
rival that read the selection guard correctly would satisfy that witness, so the
manifest demonstrates C2's dependence on ``positionalGroups`` (and on
``out.named``'s emptiness), not merely a value at one pinned point.
"""
from pathlib import Path

INSTANCE = "django__django-11477"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (the WHOLE `do` body; lies wholly inside the single
# ---- impl region and is unique in Solution.lean). ---------------------------
_IMPL = (
    "    -- impl-start\n"
    "    let mut result : List Named := []\n"
    "    let mut i := namedGroups.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ namedGroups.length\n"
    "      invariant result = keepPresent (namedGroups.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := namedGroups[i - 1]!\n"
    "      result := keepOne p ++ result\n"
    "      i := i - 1\n"
    "    return ⟨result, if result = [] then positionalGroups else []⟩\n"
    "    -- impl-end"
)

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a variant may retune it without touching the spec
# ---- or dropping the obligation. Unique in the file.
_PROOF = (
    "prove_correct bindCaptures by\n"
    "  loom_solve\n"
    "  rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]\n"
    "  simp_all"
)

# The reshaped/loop-free variants own no loop index `i`, so the frozen tactic
# script (which names `i`) does not apply. For soundness positives we retune to
# a script that closes the new shape; for reject rivals we reduce to the bare
# solver (they must NOT verify regardless — the proof body is elided from the
# spec view, and the rejection is attributable to the postcondition).
_SOLVE = "prove_correct bindCaptures by\n  loom_solve"


def _impl(new_impl, proof=_SOLVE):
    """Reshape the whole impl body AND retune the tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `bindCapturesTester namedGroups positionalGroups = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. `Named` /`Bindings`
# ---- carry DecidableEq, so each witness closes by `decide`.
def _tester(body):
    return ("extract_program_for bindCaptures\n"
            "prove_precondition_decidable_for bindCaptures\n"
            "prove_postcondition_decidable_for bindCaptures\n"
            "derive_tester_for bindCaptures\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify; else the post-image is SPEC-TOO-STRONG. Each
    # keeps the obligation and only reshapes the executable surface. Replacing
    # the mutable backward-fold with a direct `keepPresent` evaluation removes
    # the loop, so the reproof collapses to the bare `loom_solve` (no drop-step
    # lemma needed) — the contract is a pair of point-wise equalities over
    # immutable values.
    # =====================================================================
    {
        "id": "pos-control-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: evaluate the keyword bindings directly via the pure fold and
        # bind the positional selection with a single conditional expression,
        # replacing the mutable accumulator loop. Observationally identical on
        # every input.
        "module": _impl(
            "    -- impl-start\n"
            "    let named : List Named := keepPresent namedGroups\n"
            "    let pos : List String := if named = [] then positionalGroups else []\n"
            "    return ⟨named, pos⟩\n"
            "    -- impl-end"),
        "rationale": "a direct evaluation of the keyword-binding fold plus a pure "
                     "conditional for the positional selection computes the "
                     "identical `out` on every input and adds no loop obligation, "
                     "so both `ensures` clauses discharge under the bare "
                     "`loom_solve`; else SPEC-TOO-STRONG on impl shape.",
    },
    {
        "id": "pos-control-match-selection",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: express the positional selection by a `match` on the keyword
        # bindings instead of an equality guard. Same result on both arms.
        "module": _impl(
            "    -- impl-start\n"
            "    let named : List Named := keepPresent namedGroups\n"
            "    let pos : List String := match named with\n"
            "      | [] => positionalGroups\n"
            "      | _  => []\n"
            "    return ⟨named, pos⟩\n"
            "    -- impl-end"),
        "rationale": "matching on the keyword-binding list to decide the "
                     "positional selection computes the same result on both arms "
                     "as the equality guard, so both clauses still hold; a correct "
                     "reshape must verify (else SPEC-TOO-STRONG on branch form).",
    },

    # =====================================================================
    # ADMISSIBILITY — there is NO `require` clause, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude an
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point. This case discharges an in-region `assert` pinning the
    # keyword-binding value at the two F2P-shaped inputs — a required group
    # followed by an ABSENT optional group (the value-less group must be
    # DROPPED), and two present groups (both kept, in order). The surrounding
    # impl is kept verbatim so the method's own obligation still discharges; the
    # assert is live (a false claim about the same points leaves an unsolved
    # goal — checked during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-shape-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- impl-start\n"
            "    assert (with_name_prefix `assert\n"
            "      (keepPresent [(\"arg1\", some \"1\"), (\"arg2\", none)] = [(\"arg1\", some \"1\")] ∧\n"
            "       keepPresent [(\"arg1\", some \"1\"), (\"arg2\", some \"2\")]\n"
            "         = [(\"arg1\", some \"1\"), (\"arg2\", some \"2\")]))\n"
            "    let mut result : List Named := []\n"
            "    let mut i := namedGroups.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ namedGroups.length\n"
            "      invariant result = keepPresent (namedGroups.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let p := namedGroups[i - 1]!\n"
            "      result := keepOne p ++ result\n"
            "      i := i - 1\n"
            "    return ⟨result, if result = [] then positionalGroups else []⟩\n"
            "    -- impl-end",
            proof=(
                "prove_correct bindCaptures by\n"
                "  loom_solve\n"
                "  all_goals first\n"
                "    | decide\n"
                "    | (rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]; simp_all)")),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped inputs: with one present group followed by an "
                     "absent optional group it demands the value-less group be "
                     "DROPPED (one binding kept), and with two present groups it "
                     "demands both kept in order. The in-region assert must "
                     "discharge (else the obligation is unsatisfiable / "
                     "degenerate); the impl is kept verbatim so the method's own "
                     "`ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-unfiltered-keep-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep EVERY group verbatim — the pre-patch behaviour (no per-group
        # value test). A group that bound nothing leaks into the keyword
        # bindings.
        "module": _impl(
            "    -- impl-start\n"
            "    let named : List Named := namedGroups\n"
            "    return ⟨named, if named = [] then positionalGroups else []⟩\n"
            "    -- impl-end"),
        "refinement": "keeping every group verbatim is exactly the pre-patch "
                      "behaviour; a value-less optional group is carried into the "
                      "keyword bindings as an entry bound to nothing, so a reversed "
                      "or translated URL recovers a spurious argument for a group "
                      "that never participated — the precise asymmetry the failing "
                      "tests pin. It would NOT resolve.",
        "rationale": "REJECT from C1 (`out.named = keepPresent namedGroups`): "
                     "`keepPresent` drops the value-less groups the unfiltered copy "
                     "keeps, so the two disagree whenever any group bound nothing. "
                     "Verifying would be SPEC-TOO-WEAK. Refuted at a single "
                     "value-less group.",
        "witness": _tester(
            "example : bindCapturesTester [(\"a\", none)] [] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-drop-first-group",
        "kind": "uniqueness",
        "expect": "reject",
        # Discard the FIRST group unconditionally (keep the fold over the tail).
        # Correct exactly when the first group bound nothing; wrong when the
        # first group is value-bearing.
        "module": _impl(
            "    -- impl-start\n"
            "    let named : List Named := keepPresent namedGroups.tail\n"
            "    return ⟨named, if named = [] then positionalGroups else []⟩\n"
            "    -- impl-end"),
        "refinement": "dropping the first group discards a REQUIRED leading named "
                      "capture from the keyword bindings on the happy path; the "
                      "failing patterns put a required named group first, so the "
                      "reversed/translated URL loses its required argument. A "
                      "byte-fuzzer would not target 'the first element "
                      "specifically'. It would NOT resolve.",
        "rationale": "REJECT from C1: on any input whose first group bound a value, "
                     "`keepPresent namedGroups.tail` omits index 0 and thus differs "
                     "from `keepPresent namedGroups`. Correct on the complementary "
                     "sub-domain (first group value-less) — a genuine "
                     "partial-domain rival. Refuted at a single value-bearing "
                     "group.",
        "witness": _tester(
            "example : bindCapturesTester [(\"a\", some \"x\")] [] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-always-positional",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct keyword bindings, but ALWAYS surface the positional bindings,
        # dropping the selection guard. Violates C2 whenever the keyword bindings
        # are non-empty.
        "module": _impl(
            "    -- impl-start\n"
            "    let named : List Named := keepPresent namedGroups\n"
            "    return ⟨named, positionalGroups⟩\n"
            "    -- impl-end"),
        "refinement": "always surfacing the positional bindings ignores the "
                      "'only when there are no keyword bindings' selection; a route "
                      "with named groups would then receive extra positional "
                      "arguments alongside its keyword arguments and misdispatch — "
                      "does NOT resolve the argument/keyword split the failing tests "
                      "assert.",
        "rationale": "REJECT from C2 (`out.positional = if out.named = [] then "
                     "positionalGroups else []`): with a non-empty keyword binding "
                     "the clause demands the positional bindings be empty, but the "
                     "rival returns them verbatim. Verifying would be "
                     "SPEC-TOO-WEAK on the selection clause. Refuted at the only "
                     "witness whose `positionalGroups` is non-empty, which is what "
                     "makes C2's dependence on `positionalGroups` observable.",
        "witness": _tester(
            "example : bindCapturesTester [(\"a\", some \"x\")] [\"p\"] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-leak-trailing-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the correct bindings, but additionally leak a value-less TRAILING
        # group back into the keyword bindings. Correct unless the last group is
        # value-less.
        "module": _impl(
            "    -- impl-start\n"
            "    let named : List Named :=\n"
            "      keepPresent namedGroups ++ (namedGroups.reverse.take 1).filter (fun p => p.2.isNone)\n"
            "    return ⟨named, if named = [] then positionalGroups else []⟩\n"
            "    -- impl-end"),
        "refinement": "re-appending a value-less trailing group reproduces the "
                      "exact reported bug: a non-participating optional group is "
                      "surfaced in the keyword bindings bound to nothing, so a "
                      "translated URL recovers a spurious trailing argument — does "
                      "NOT resolve the optional-parameter tests.",
        "rationale": "REJECT from C1: the leaked trailing entry (a group bound to "
                     "nothing) is absent from `keepPresent namedGroups`, so the two "
                     "disagree whenever the last group is value-less. Rejected by "
                     "the retention clause; verifying would be SPEC-TOO-WEAK. "
                     "Refuted at a present-then-absent pair (a sub-domain the "
                     "other rivals do not probe).",
        "witness": _tester(
            "example : bindCapturesTester [(\"a\", some \"x\"), (\"b\", none)] [] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 frame-mutation, 4 uniqueness rivals, 1 admissibility). This bundle
# models the purely-functional core — a single method `bindCaptures` — where the
# sibling contracts `select_captures` over a permission-bearing heap. The value
# surface carries across intact; the permission surface does not exist here.
# Every sibling case is accounted for below.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape                 -> pos-control-direct-fold        PORTED
#                                          (+ pos-control-match-selection ADDED)
#   frame-mutation-keys                 -> (none)                         VACUOUS
#   weak-unfiltered-prepatch            -> weak-unfiltered-keep-all       PORTED
#   partial-domain-drop-first           -> weak-drop-first-group          PORTED
#   positional-choice-always-copy       -> weak-always-positional         PORTED
#   absence-leak-trailing               -> weak-leak-trailing-absent      PORTED
#   admissibility-f2p-shape             -> admiss-f2p-shape-nondegenerate RE-AIMED
#
# 5 ported, 1 re-aimed, 1 vacuous; 1 positive control added.
#
# VACUOUS (frame-mutation-keys): the sibling's mandatory frame-mutation rival
#   writes to a read-only input carrying only a fractional heap permission and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, this bundle declares no
#   `mut` binder, there is no heap and no aliasing. There is no read-only input
#   to overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated (per the porting map, this class is legitimately
#   dropped here rather than replaced).
# RE-AIMED (admissibility): the sibling establishes the precondition for a normal
#   input. There is NO `require` clause here, so that probe is vacuous. It is
#   re-aimed at the residual admissibility risk on a total domain: that the
#   post-image is unsatisfiable / degenerate at the interesting point. The case
#   discharges an in-region assert pinning the keyword-binding value at the two
#   F2P-shaped inputs (an absent optional group dropped; two present groups kept).
# ADDED (1): pos-control-match-selection — a second structurally-different correct
#   impl (the selection expressed as a `match` rather than an equality guard), so
#   the soundness surface is defended by two distinct reshapes.
#
# BINDER / CLAUSE COVERAGE. Both `ensures` clauses are attacked:
#   * C1 (`out.named = keepPresent namedGroups`) by weak-unfiltered-keep-all,
#     weak-drop-first-group, and weak-leak-trailing-absent, across three distinct
#     sub-domains (a value-less group leaked; the first group dropped; a
#     value-less trailing group leaked);
#   * C2 (`out.positional = if out.named = [] then positionalGroups else []`) by
#     weak-always-positional.
#   `namedGroups` is varied across the four witnesses (a value-less group; a
#   value-bearing group; a value-bearing-then-value-less pair). `positionalGroups`
#   is varied by weak-always-positional — the ONLY witness whose `positionalGroups`
#   is non-empty, which is exactly the point that demonstrates C2's dependence on
#   `positionalGroups` (and on the emptiness of `out.named`). The four witnesses
#   sit at four DISTINCT input points (pts=4).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle has no axioms
#   and no deep-model references (meta.json axioms == []), and this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []

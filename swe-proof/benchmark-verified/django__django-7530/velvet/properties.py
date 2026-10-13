"""properties.py — G-PBT falsification battery for django__django-7530 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery edits only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, both of
which the consumer spec view elides — so ``markers.same_spec`` holds by
construction and the ``prove_correct appModelPairs`` header survives. A
rejection is therefore attributable to the postcondition, never to a tampered
spec.

DEFENDED SURFACE (one contracted method, one read-only input, no ``require``).

    appModelPairs (apps : List AppEntry) return (out : List (Nat × Nat))
        ensures out = allPairs apps

``allPairs`` is a total, fully unfolded ``def`` over the method's own argument:
it concatenates, in registry order, each entry's own (label, model) pairs —
every entry paired with EACH of the models THAT entry owns
(``appPairs a = a.2.map (fun m => (a.1, m))``), and never a model belonging only
to some other entry. The single input ``apps`` is FREE; the reject rivals abuse
its sub-structure — the per-entry label ``a.1``, the per-entry model list
``a.2``, and the pairing of the two.

The load-bearing content of ``out = allPairs apps`` is that each entry
contributes exactly its OWN models (soundness: no foreign entry's model offered
under this label), ALL of them (completeness), each paired with the correct
label. The rivals attack each of those independently.

CARRIER NOTE — WHY EVERY REJECT CASE CARRIES A ``witness_reference``. The frozen
impl keeps a ``while`` loop, and under ``loom.semantics.choice "demonic"`` its
extracted program elaborates through ``Classical.choice``, which the kernel
cannot unfold. MEASURED: ``appModelPairsTester [(0,[10]),(1,[11])] = false``
against the FROZEN solution fails with

    Tactic `decide` failed ... its `Decidable` instance ... did not reduce to
    `isTrue` or `isFalse`

— stuck reduction, not refutation. That exit code carries NO information: the
identical error appears for a TRUE claim about the frozen impl, so a forged
witness asserting a rival is *correct* would clear both halves of the
discrimination check. This is the ``witness-undecided`` failure mode, and it is
why "half 2 holds because gold's loop does not reduce" is NOT evidence of
anything. Every reject case below therefore ships an explicit
``witness_reference`` — ``_LOOPFREE``, a loop-free variant that implements the
frozen spec CORRECTLY (it verifies; see ``pos-closed-form-direct``, which ships
the same source as an ``expect="verify"`` case so the battery itself records
that loop-freeness is not what any rival is rejected for). Against that
reference each witness fails with

    Tactic `decide` proved that the proposition ... is false

— a real refutation. All five were confirmed by hand with
``scripts/lean_verify.sh``: witness ELABORATES against its rival (exit 0), and
FAILS-by-refutation against the reference (exit 1, "proved ... is false").

The carrier is fully transparent (labels and models are concrete ``Nat``,
entries concrete ``List``), so no opaque leaf blocks reduction; every witness is
a concrete literal registry and no witness binds a hypothesis. Hence no
conditioning is used, and there are no assumptions that could be jointly
unsatisfiable (``witness-inconsistent`` is not reachable here).

WITNESS PLACEMENT / BINDER VARIATION. The five witnesses sit at FIVE distinct
registries and between them move the input's sub-structure off any fixed value:
labels take 0/1/2/3, models take 10/11/12/20, per-entry model-list length takes
1 and 2, registry length takes 1 and 2. r1/r2 need two entries with disjoint
models (so the union differs from each entry's own set); r3 needs one entry
owning two models (so "first only" drops something); r4/r5 need only a single
entry (the identity perturbation is visible there). No two rivals share a
refutation point.

ADVERSARIAL READ of the sibling classes:

  * FRAME-MUTATION — VACUOUS on this backend. The sibling probes whether a
    read-only fractional-permission input can be overwritten to satisfy the
    postcondition vacuously. Lean/Velvet is referentially transparent — no heap,
    no aliasing — and this bundle declares NO ``mut`` parameter (``apps`` is
    read-only by being non-``mut``), so there is no read-only input to overwrite
    and no substitute probe. Reported N/A; not fabricated.

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

  * UNGROUNDED-ORACLE ECHO — N/A. ``allPairs`` is a total ``def`` over the
    method's own argument and the ``axioms`` region is empty (the proof consumes
    no callee contract), so there is no opaque answer-key an impl could echo
    without doing the work. The positives are honest reshapes instead.

AXIOM lane: EMPTY. This bundle consumes no ``axiom``; the changed behaviour is
modeled deeply and its fidelity to the real registry callee is a G-AX / G-CONF
concern. The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-7530"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim (between -- impl-start and -- impl-end).
# ---- Full-replacement rivals and the loop-free positive swap THIS for a new
# ---- body; the fragment lies wholly inside the impl region and is unique. ----
_GOLD_IMPL = (
    "    let mut result : List (Nat × Nat) := []\n"
    "    let mut i := apps.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ apps.length\n"
    "      invariant result = allPairs (apps.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let a := apps[i - 1]!\n"
    "      result := appPairs a ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _GOLD_IMPL in _BASE, "gold impl region drifted from Solution.lean"

# ---- the loop-body step (element read + front-prepend), for the in-loop
# ---- reshape positive. Unique in the file, wholly inside the impl region. ----
_LOOP_STEP = (
    "      let a := apps[i - 1]!\n"
    "      result := appPairs a ++ result"
)
assert _LOOP_STEP in _BASE, "loop-step anchor drift"

# ---- the accumulator-init line, for prepending the admissibility assert. ----
_RESULT_INIT = "    let mut result : List (Nat × Nat) := []\n"
assert _BASE.count(_RESULT_INIT) == 1, "result-init anchor drift"

# ---- the frozen proof block (tactic body only; elided from the spec view, so a
# ---- reshaped positive may retune it without touching the spec or the
# ---- `prove_correct` header). Unique in the file. ----
_PROVE = (
    "prove_correct appModelPairs by\n"
    "  loom_solve\n"
    "  rw [allPairs_drop_step apps i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _PROVE in _BASE, "frozen proof block drifted from Solution.lean"

_BARE_PROVE = "prove_correct appModelPairs by\n  loom_solve"


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A loop-free impl that produces the modeled enumeration
# directly: CORRECT (it verifies — measured exit 0, and shipped below as
# `pos-closed-form-direct` so the battery records that loop-freeness is not what
# any rival is rejected for) and REDUCIBLE (no `while`, so no Classical.choice,
# so `decide` reaches a verdict). Every reject witness is refuted against THIS
# rather than against the frozen solution, whose loop leaves `decide` stuck for
# every claim — true or false — and so discriminates nothing.
# ---------------------------------------------------------------------------
_LOOPFREE = _swap(
    _swap(_BASE, _GOLD_IMPL, "    let out := allPairs apps\n    return out"),
    _PROVE, _BARE_PROVE)


# ---- witness preamble: reach the method contract through Velvet's own tester
# ---- machinery. `appModelPairsTester args = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict. The tester names are introduced
# ---- by the directives inside the witness itself, so they exist on both sides
# ---- of the comparison by construction.
_TESTER = (
    "extract_program_for appModelPairs\n"
    "prove_precondition_decidable_for appModelPairs\n"
    "prove_postcondition_decidable_for appModelPairs\n"
    "derive_tester_for appModelPairs\n\n"
)


def _witness(reg):
    return _TESTER + (
        f"example : appModelPairsTester {reg} = false := by\n  decide\n")


# ---- reject-rival bodies. Written loop-free so the rival side of each witness
# ---- also reduces; the rejection itself is on the `ensures_1` goal (measured:
# ---- every rival below fails with `unsolved goals / case «ensures_1: out =
# ---- allPairs apps»`, i.e. the postcondition, not a tactic mismatch). ----
_R_WHOLE_UNION = (
    "    let everyModel : List Nat := (apps.map (fun a => a.2)).flatten\n"
    "    let out := (apps.map (fun a => everyModel.map (fun m => (a.1, m)))).flatten\n"
    "    return out"
)
_R_COMPLEMENT = (
    "    let everyModel : List Nat := (apps.map (fun a => a.2)).flatten\n"
    "    let out := (apps.map (fun a =>\n"
    "      (everyModel.filter (fun m => ! a.2.contains m)).map (fun m => (a.1, m)))).flatten\n"
    "    return out"
)
_R_FIRST_ONLY = (
    "    let out := (apps.map (fun a => (a.2.take 1).map (fun m => (a.1, m)))).flatten\n"
    "    return out"
)
_R_WRONG_MODEL = (
    "    let out := (apps.map (fun a => a.2.map (fun m => (a.1, m + 1)))).flatten\n"
    "    return out"
)
_R_WRONG_LABEL = (
    "    let out := (apps.map (fun a => a.2.map (fun m => (a.1 + 1, m)))).flatten\n"
    "    return out"
)


def _rival(body):
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _PROVE, _BARE_PROVE)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation with a byte-identical
    # statement and retunes only the elided proof body. Both measured exit 0.
    # =====================================================================
    {
        "id": "pos-closed-form-direct",
        "kind": "soundness",
        "expect": "verify",
        # The same source used as `witness_reference` by every reject case.
        # Shipping it as a verify case is what makes the reference honest: the
        # battery itself records that a loop-free impl of this spec VERIFIES, so
        # loop-freeness is not the property any rival is being rejected for.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that produces the modeled enumeration "
                     "directly is observationally `allPairs apps` on every "
                     "registry, so the single ensures clause discharges under a "
                     "bare `loom_solve`; a correct reshape must verify, else the "
                     "postcondition is over-fit to the accumulator-loop code "
                     "form => SPEC-TOO-STRONG. This is also the "
                     "`witness_reference` every reject case is refuted against, "
                     "so its verifying status is load-bearing for the whole "
                     "battery and is recorded here rather than assumed.",
    },
    {
        "id": "pos-inline-elem-read",
        "kind": "soundness",
        "expect": "verify",
        # In-loop reshape: inline the indexed element read into the prepend
        # instead of naming it in a `let`. Same backward accumulator loop, same
        # front-prepend and invariants, same value flow — the frozen proof still
        # closes verbatim, so this probes over-fit to the `let`-binding form
        # without changing the algorithm.
        "module": _swap(
            _BASE, _LOOP_STEP,
            "      result := appPairs apps[i - 1]! ++ result"),
        "rationale": "inlining the indexed element read (`apps[i-1]!`) into the "
                     "front-prepend leaves the accumulator loop, the invariants "
                     "and the assembled value unchanged, so `out = allPairs apps` "
                     "still holds and the frozen proof closes; a correct reshape "
                     "must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the sibling's
    # "a normal aligned input satisfies the precondition" probe is vacuous:
    # nothing could exclude an F2P-shaped input. Re-aimed at the residual risk
    # on a total domain — that the post-image is UNSATISFIABLE / DEGENERATE at
    # the interesting point. This case discharges a live in-region `assert`, at
    # a concrete two-entry registry, that the enumeration really discriminates:
    # for `[(0,[10]),(1,[11])]` it is exactly `[(0,10),(1,11)]` (each label
    # paired with its OWN model, in registry order). The surrounding impl is
    # kept verbatim so the ensures clause still discharges; the proof body is
    # retuned only to clear the extra assert goal by `decide`.
    #
    # The assert is LIVE, and that was checked rather than asserted: perturbing
    # the claim to the FALSE `= [(0,10),(1,12)]` at the same point makes the
    # variant fail to build. So this case cannot pass by the assert being
    # ignored.
    # =====================================================================
    {
        "id": "admiss-enumeration-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _RESULT_INIT,
                "    assert (with_name_prefix `admiss\n"
                "      (allPairs [((0:Nat),[(10:Nat)]),(1,[11])] = [(0,10),(1,11)]))\n"
                + _RESULT_INIT),
            _PROVE,
            "prove_correct appModelPairs by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [allPairs_drop_step apps i (by omega) (by omega)]; simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at an "
                     "F2P-shaped point: for a two-entry registry with disjoint "
                     "models the enumeration is exactly each label paired with "
                     "its OWN model in registry order, so the modeled behaviour "
                     "genuinely distinguishes the per-entry ownership at issue. "
                     "The in-region assert must discharge (else an unsatisfiable "
                     "/ degenerate obligation) and the impl is kept verbatim so "
                     "the ensures clause discharges too. Verified live: the same "
                     "assert with a FALSE right-hand side fails to build.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a distinct concrete registry, refuted against `_LOOPFREE` (the frozen
    # loop cannot decide anything — see the CARRIER NOTE), plus the argument
    # that its faithful counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-whole-registry-union",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_R_WHOLE_UNION),
        "refinement": "this is the PRE-IMAGE behaviour: pair every entry's label "
                      "with the flat union of ALL entries' models — a per-entry "
                      "query that silently returns the whole-project model list "
                      "for each label. Its faithful counterpart feeds the "
                      "consistency scan (label, model) pairs naming models the "
                      "label does not own; the failing test walks every recorded "
                      "call and resolves each model against its claimed owning "
                      "label, raising on the first invalid combination — so it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = allPairs apps`: `allPairs` pairs each "
                     "label with its OWN models only, and this impl pairs it with "
                     "the whole-registry union, so on any registry with a foreign "
                     "model the enumerations differ. Refuted at "
                     "`[(0,[10]),(1,[11])]`, where entry 0 must contribute only "
                     "`(0,10)` but the union impl also emits `(0,11)`.",
        "witness": _witness("[((0:Nat),[(10:Nat)]),(1,[11])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-complement-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_R_COMPLEMENT),
        "refinement": "pairs each label with the FOREIGN models (the union minus "
                      "its own) — the exact opposite selection. A counterpart "
                      "consulting every OTHER entry's models under this label "
                      "offers only models the label does not own, so every "
                      "recorded call is an invalid combination and the failing "
                      "test's per-call resolution raises immediately; it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = allPairs apps`: `allPairs` keeps exactly "
                     "each entry's own models and the complement keeps the rest, "
                     "so they disagree on every registry with both an owned and a "
                     "foreign model. Refuted at `[(0,[10]),(2,[12])]`, a distinct "
                     "point (labels 0/2, models 10/12) from the union rival, "
                     "where entry 0 must emit `(0,10)` but the complement emits "
                     "`(0,12)`. Not shared with the union rival: the two differ "
                     "on whether the entry's OWN models are retained, and the "
                     "complement drops them where the union keeps them.",
        "witness": _witness("[((0:Nat),[(10:Nat)]),(2,[12])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-model-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_R_FIRST_ONLY),
        "refinement": "keeps only the FIRST of each entry's own models, dropping "
                      "the rest. Every pair it emits is VALID, so this is the "
                      "near-miss that no invalid-combination check would catch; "
                      "it fails on COMPLETENESS instead — a counterpart scanning "
                      "one model per entry omits every other owned model from the "
                      "consistency scan, so the pairs the failing test requires "
                      "to be present are absent and it would NOT resolve.",
        "rationale": "REJECT from `out = allPairs apps` (COMPLETENESS): `allPairs` "
                     "emits every owned model and this impl emits only the first. "
                     "Refuted at `[(0,[10,11])]` — a single entry owning two "
                     "models, the smallest registry exposing the drop — where the "
                     "post-image demands `[(0,10),(0,11)]` and the impl yields "
                     "only `[(0,10)]`. This is the only witness that moves an "
                     "entry's model-list length above 1, so it is the only one "
                     "that constrains the spec's dependence on that sub-structure.",
        "witness": _witness("[((0:Nat),[(10:Nat),(11:Nat)])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-wrong-model-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_R_WRONG_MODEL),
        "refinement": "applies the correct per-entry selection but perturbs each "
                      "gathered model identity (`m + 1`). A counterpart yielding a "
                      "perturbed model identity names a model no label owns, so "
                      "the failing test's resolution of each recorded model "
                      "against its label raises; it would NOT resolve.",
        "rationale": "REJECT from `out = allPairs apps`: `allPairs` pairs each "
                     "label with `m` exactly, and this impl pairs it with `m + 1`, "
                     "so the MODEL component of every pair is off by one. Refuted "
                     "at `[(0,[20])]` (model 20, distinct from the other "
                     "witnesses' models), where the post-image demands `(0,20)` "
                     "and the impl emits `(0,21)`.",
        "witness": _witness("[((0:Nat),[(20:Nat)])]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-wrong-label-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_R_WRONG_LABEL),
        "refinement": "keeps each entry's own models but pairs them with a "
                      "perturbed label (`a.1 + 1`) — attributing every model to "
                      "the wrong owner. A counterpart that mislabels the pairs "
                      "attributes each model to a label that does not own it, "
                      "exactly the invalid-combination failure at issue, so the "
                      "failing test's per-call resolution raises; it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = allPairs apps`: `allPairs` pairs each "
                     "model with its OWN label `a.1`, and this impl pairs it with "
                     "`a.1 + 1`, so the LABEL component of every pair is wrong. "
                     "Refuted at `[(3,[10])]` (label 3, distinct from the other "
                     "witnesses' labels), where the post-image demands `(3,10)` "
                     "and the impl emits `(4,10)`. This is the only rival that "
                     "abuses the label sub-component of the pairing — without it "
                     "a rival mishandling only the label would go unnoticed.",
        "witness": _witness("[((3:Nat),[(10:Nat)])]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Sibling -> velvet accounting. The sibling battery has 8 SPEC cases (1
# soundness positive, 1 admissibility, 6 uniqueness rivals) over a SINGLE
# contracted function that gathers the members belonging to one target group in
# roster order. This bundle contracts a SINGLE method `appModelPairs` that
# enumerates every registry entry's own (label, model) pairs, so the sibling's
# per-position gather maps onto the per-entry model enumeration and each rival
# re-aims at the corresponding sub-term of the one post-image
# `out = allPairs apps`.
#
#   sibling case                    -> here                             status
#   ----------------------------------------------------------------------------
#   pos-explicit-else               -> pos-inline-elem-read              PORTED (reshape)
#   (added)                         -> pos-closed-form-direct            ADDED (loop-free; also the witness reference)
#   admiss-self-call                -> admiss-enumeration-nondegenerate   RE-AIMED
#   frame-mutate-owner              -> (none)                            VACUOUS
#   frame-mutate-member             -> (none)                            VACUOUS
#   rival-prepatch-allmembers       -> weak-whole-registry-union         PORTED (the bug)
#   rival-complement-filter         -> weak-complement-filter            PORTED
#   rival-partial-first             -> weak-first-model-only             PORTED (re-aimed: completeness)
#   rival-wrong-member-value        -> weak-wrong-model-identity         PORTED
#   (added)                         -> weak-wrong-label-identity         ADDED (label-binder coverage)
#
# 4 ported, 1 re-aimed positive, 1 re-aimed admissibility, 2 vacuous, 2 added.
#
# RE-AIMED (admissibility): the sibling establishes that the two read-only
#   half-permission inputs are usable at 1/2 and that a normal aligned roster
#   meets the precondition. This backend has no permissions and no `require`
#   clause, so nothing could exclude a normal input — that probe is vacuous. It
#   is re-aimed at the residual admissibility risk on a total domain: that the
#   post-image is UNSATISFIABLE / DEGENERATE. The case discharges a concrete
#   in-region assert that the two-entry enumeration is exactly the per-entry
#   pairing, and the assert was confirmed live (a false variant fails to build).
#
# VACUOUS (frame-mutate-owner, frame-mutate-member): the sibling writes into a
#   read-only half-permission roster stream to trip INSUFFICIENT PERMISSION.
#   This backend is referentially transparent, has no heap or aliasing, and this
#   bundle declares NO `mut` parameter — there is no read-only input to
#   overwrite and no substitute probe. Not fabricated.
#
# PORTED / re-aimed (weak-first-model-only): the sibling's partial-first rival
#   gathers the FIRST roster member unconditionally, diverging on one sub-domain.
#   This bundle's per-entry carrier has no single privileged position across the
#   whole registry; the closest same-family attack is a partial/incomplete
#   selection — keep only the FIRST of each entry's own models — refuted on any
#   entry owning two or more. Same class (a domain-incomplete selection, correct
#   on part of the domain), re-aimed to the per-entry model list.
#
# ADDED (2):
#   pos-closed-form-direct — a structurally MORE different soundness positive
#     (no loop at all). Required independently of the sibling: it is the
#     `witness_reference` for all five reject cases, and the gate demands a
#     reference that VERIFIES, so the battery records that verdict itself.
#   weak-wrong-label-identity — binder coverage. The sibling's rivals all attack
#     the gathered MEMBER identity/selection; the symmetric label component of
#     the pairing is otherwise unattacked, and no other witness moves the label
#     sub-component off each entry's true label.
#
# CONSIDERED AND DROPPED — order permutation. A rival returning the entries'
#   pairs in REVERSE registry order is rejected by the frozen spec (measured:
#   exit 1 on `ensures_1`, and a witness discriminates it against the
#   reference). It is NOT shipped because it has no honest `refinement`: per
#   mapping.md §2.1 the real observable is order-INSENSITIVE (the scanned labels
#   are an unordered collection and the failing test inspects the recorded calls
#   as an unordered collection), so its faithful counterpart WOULD resolve the
#   instance. Shipping it would record a spec-strength result for a distinction
#   the benchmark does not measure — the spec is stricter than the observable
#   here, which is a tolerated representative choice, not a rival's error.
#
# NOT PORTABLE AS A REJECT CASE - divergence, but CLOSED BY THE SEMANTICS rather
#   than admitted. THIS RETRACTS the note that stood here, which said the
#   diverging rival VERIFIES on this cell and called the class a KNOWN SPEC HOLE.
#   Re-measured, it does not verify: this bundle is checked under total
#   correctness (the `set_option` on line 4 itself opens `TotalCorrectness`, and
#   line 7 opens it again), so the verifier demands a decreasing measure on every
#   loop. A rival that loops without one is refused at elaboration, and the
#   sharper rival that supplies a CONSTANT measure is refused on the measure's own
#   descent goal (`case «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0`, measured on this
#   cell against the frozen file). What makes it unshippable is the WITNESS
#   CONTRACT, not spec weakness: a reject case needs a witness that ELABORATES
#   against the rival, and a rejected rival's module does not compile at all
#   (the descent obligation fails at the `method` itself, ahead of any appended
#   tester), so no witness can. See the module docstring, which already states
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   this account, for the mechanism and the gate measurement.
#
# COVERAGE. The single input binder `apps` and its sub-structure are moved
#   across the five reject witnesses: labels {0,1,2,3}; models {10,11,12,20};
#   per-entry model-list length {1,2}; registry length {1,2}. pts = 5 distinct
#   input registries. Independent sub-terms of the post-image attacked: WHICH
#   models each entry contributes — own vs. whole-union
#   (weak-whole-registry-union) and own vs. complement (weak-complement-filter);
#   COMPLETENESS of the per-entry model set (weak-first-model-only); the MODEL
#   component of each pair (weak-wrong-model-identity); the LABEL component of
#   each pair (weak-wrong-label-identity). No independent sub-term of the one
#   post-image clause is left unattacked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the changed behaviour is modeled deeply), so there is nothing here
#   for this gate to probe.
AXIOM_TESTS = []

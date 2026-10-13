"""properties.py — G-PBT falsification battery for django__django-11163 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and be REFUTED
against a subject known to satisfy the spec — here an explicit
``witness_reference`` rather than the frozen solution, for the reason set out in
the CARRIER NOTE).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); the
sibling's per-case adversarial argument is carried over and re-expressed against
this backend's carrier. Case-count parity is NOT the target — the Lean-family
bundle models only the purely-functional core (a single contracted ``method``),
so nagini cases attached to unmodeled behaviour or to nagini-only machinery have
no counterpart. The Nagini->velvet accounting block at the bottom of this file
records exactly which sibling cases ported, which were omitted, and why.

DEFENDED SURFACE. One contracted method over three input binders:

  selectModelFields (candidates : List Int) (selector : Option (List Int))
                    (excl : List Int) return (out : List Int)
    ensures out = selectNames selector excl candidates        -- (C1) load-bearing
    ensures selector = some [] → out = []                     -- (C2)
    ensures ∀ n, n ∈ out → n ∈ candidates ∧ keep selector excl n = true  -- (C3)

There is NO ``require`` clause and NO ``axiom`` in this bundle. ``selectNames``
and its per-element decision ``keep`` are fully-unfolded ``def``s in the ``pure``
region — total functions of the three inputs, with no opaque answer key to echo.
``keep`` distinguishes the three situations the issue turns on:
  * ``selector = none``        — no selector: every candidate is admissible;
  * ``selector = some present`` — a supplied selector keeps a candidate only if
    its name is IN ``present``. Decided by the PRESENCE of the selector, not by
    whether it lists anything: ``some []`` keeps NOTHING;
  * ``excl`` removes any candidate whose name it contains (``[]`` removes none).

So (C1) pins a per-element decision over all three binders (``selector``,
``excl``, and the ``candidates`` element under test), and each reject rival below
abuses a distinct one: the present-empty-selector distinction (the exact bug),
the absent-selector keep-all branch, the exclusion conjunct, and the per-element
source ordering/multiplicity.

CARRIER NOTE (decisive for the witness route). The frozen impl is a BACKWARD
``while`` loop whose extracted program (``selectModelFieldsExec``) does NOT
kernel-reduce under ``decide``: the ``prove_postcondition_decidable_for`` route
leaves the loop's ``wp`` stuck. MEASURED, for all four reject witnesses, against
the frozen solution:

    error: Tactic `decide` failed for proposition
      selectModelFieldsTester [1] (some []) [] = false
    because its `Decidable` instance ... did not reduce to `isTrue` or `isFalse`.

That is EXIT 1 on gold, so it satisfies the gate's two-build shape — but it is a
STUCK REDUCTION, not a refutation. The kernel never evaluated the claim, so the
identical error appears for a TRUE claim about the frozen impl; the exit code
therefore discriminates NOTHING on its own (this is exactly the condition
``gates/pbt.py::_stuck`` screens for and reports as ``witness-undecided``). An
earlier revision of this file asserted gold's failure was "a genuine failure on
gold"; that claim was WRONG and is retracted here.

What makes the reject lane sound is therefore NOT gold: it is a ``witness_reference``
— a loop-free impl that SHARES the frozen spec and independently VERIFIES, whose
extracted program does reduce, so ``decide`` returns a real verdict. Each reject
case below names ``_REF_DIRECT`` (the ``pos-direct`` impl: ``return selectNames
selector excl candidates``, an ``expect="verify"`` case of this battery) explicitly,
and against it every witness is REFUTED SEMANTICALLY. MEASURED, same four
witnesses, against ``_REF_DIRECT``:

    error: Tactic `decide` proved that the proposition
      selectModelFieldsTester [1] (some []) [] = false
    is false

i.e. the kernel computed the tester and found the claim false — a true semantic
refutation, which is what "the reference satisfies the spec at this input" must
look like. Naming the reference explicitly rather than leaning on the gate's
positive-fallback is what puts that evidence in the artifact: the gate verifies
the reference shares the spec and verifies before trusting it.

Every reject rival is authored STRAIGHT-LINE so its own extracted program reduces
(the half that must ELABORATE). Each stays wrong for a VALUE reason — it returns
a list that differs from ``selectNames`` at the probed input — not for a shape
reason; the straight-line form is only what lets the witness name the
counterexample. Per-case builds re-run during the audit: EXIT 0 against the
rival, EXIT 1 (semantic) against ``_REF_DIRECT``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this class
    as MANDATORY because ``names``/``edit``/``allowed``/``blocked`` hold
    fractional heap permissions (``Acc(.,1/2)``) an impl can illegally overwrite.
    Lean and Velvet are referentially transparent: ``candidates``, ``selector``
    and ``excl`` are immutable values, none is declared ``mut``, there is no heap
    and no aliasing — so there is no read-only input to mutate and no substitute
    probe to build. The two nagini frame-mut rivals (frame-mut-names,
    frame-mut-edit) are NOT ported and NOT replaced. DEMONSTRATED rather than
    asserted (independent audit): an impl body that assigns a parameter,
    ``candidates := candidates ++ [0]``, does not even parse —

        error: `candidates` cannot be mutated, only variables declared using
        `let mut` can be mutated.

    That is a front-end rejection of the VARIANT, not the spec rejecting a
    behaviour, so no such rival could ever carry a discriminating witness: there
    is no impl for the witness to elaborate against. The class is genuinely
    inexpressible on this carrier.
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
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class: (C1) is pinned to a total,
    fully-unfolded function of the method's own inputs (``selectNames`` and
    ``keep`` are concrete ``def``s; the ``axioms`` region is empty), so there is
    no answer key to echo. Any WRONG value fails (C1) — demonstrated by every
    reject rival. Covered instead by the pos-direct positive control (returning
    ``selectNames …`` directly is a correct grounded impl, not an echo).
  * PARTIAL-DOMAIN / VALUE rivals — APPLY: the nagini uniqueness value rivals port
    onto the three ``ensures`` clauses, each diverging from gold on the exact
    sub-domain its abused branch governs.

WITNESS PLACEMENT. The five reject witnesses probe four distinct input points so
that all three input binders are varied across the battery:
  * weak-truthiness           — candidates=[1], selector=some [], excl=[]:
    a PRESENT-EMPTY selector, where the rival keeps everything (gold keeps none);
  * weak-restrict-none-drops  — candidates=[1], selector=none, excl=[]:
    an ABSENT selector, where the rival keeps nothing (gold keeps all);
  * weak-drop-removal         — candidates=[1], selector=none, excl=[1]:
    a NON-EMPTY exclusion, where the rival keeps an excluded name (gold drops it);
  * weak-partial-first        — candidates=[1,2], selector=none, excl=[]:
    a two-element candidate list, where the rival drops the FIRST source element
    (gold keeps both, in order);
  * weak-reverse-order        — candidates=[1,2], selector=none, excl=[]:
    the SAME input point as weak-partial-first, deliberately: it separates the
    two independent contents of (C1) at one point. partial-first attacks WHICH
    names survive (an omission, which (C3) would also see); reverse-order
    attacks the ORDER they are emitted in (a permutation, which neither (C2)
    nor (C3) can see — every name is still a member and still passes `keep`).
    A permutation rival is the one wrong impl class the sorted F2P/P2P
    observations cannot distinguish, so the spec must carry it alone.
The selector binder is moved across all three of its meaningful shapes
(``some []``, ``none``, and — via the drop-removal / partial-first points —
``none`` again but with the OTHER two binders varied); the excl binder is moved
between ``[]`` and ``[1]``; the candidates binder is moved between length-1 and
length-2. No two rivals are refuted at the same point.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY by ``keep``/``selectNames`` — see mapping.md §3). There is no
axiom-soundness/containment obligation to probe here, and the gate ignores
``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-11163"
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

# The WHOLE executable body of the method: the backward while loop that prepends
# each kept name.
_IMPL = (
    "    let mut result : List Int := []\n"
    "    let mut i := candidates.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ candidates.length\n"
    "      invariant result = selectNames selector excl (candidates.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := candidates[i - 1]!\n"
    "      result := (if keep selector excl c then [c] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the (retuned) proof without disturbing the obligation.
_IMPL_TOP = "    let mut result : List Int := []\n    let mut i := candidates.length"
assert _BASE.count(_IMPL_TOP) == 1, "impl top drifted from expected text"

# The FULL frozen proof body. A variant that reshapes the impl may retune this;
# the tactic body is elided from the spec view, so it is a proof reshape, not a
# spec change. Unique in the file.
_PROOF = (
    "prove_correct selectModelFields by\n"
    "  loom_solve\n"
    "  rw [selectNames_drop_step selector excl candidates i (by omega) (by omega)]\n"
    "  rw [‹result = selectNames selector excl (candidates.drop i)›]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `selectModelFieldsTester candidates selector excl = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. There is no `require`
# ---- clause, so every input reaches the postcondition (no vacuous pass on an
# ---- excluded one). `decide` reduces the extracted STRAIGHT-LINE program of each
# ---- rival; against the frozen looped solution the `Exec` never reduces, so the
# ---- witness fails on gold — the discriminator.
_TESTER = (
    "extract_program_for selectModelFields\n"
    "prove_precondition_decidable_for selectModelFields\n"
    "prove_postcondition_decidable_for selectModelFields\n"
    "derive_tester_for selectModelFields\n\n"
)

# ---- witness reference. The frozen looped impl cannot DECIDE anything (see the
# ---- CARRIER NOTE: `decide` gets stuck on its `Exec`, so its EXIT 1 attests to
# ---- nothing), so every reject case is refuted against this loop-free impl of
# ---- the SAME spec instead. It is the `pos-direct` module verbatim, and
# ---- `pos-direct` is an `expect="verify"` case of this battery, so the fact that
# ---- it satisfies the frozen spec is itself machine-checked here — twice over,
# ---- since the gate independently re-verifies a `witness_reference` (it must
# ---- share the frozen spec AND verify) before allowing a refutation against it.
# ---- An impl the verifier accepts cannot violate its own spec, so a genuine
# ---- "the spec is violated at this input" witness MUST fail against it; and
# ---- because its extracted program reduces, that failure is a real semantic
# ---- verdict rather than a stuck term.
_REF_DIRECT = _with_impl_and_proof(
    "    return selectNames selector excl candidates",
    "prove_correct selectModelFields by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl: return
    # `selectNames selector excl candidates` directly. Clause (C1) IS
    # `out = selectNames …` and `selectNames` is a total, grounded function of
    # the three inputs (no opaque oracle), so returning it is a correct,
    # fully-grounded implementation, not an echo. MUST verify; else the spec is
    # over-fit to the loop SHAPE => SPEC-TOO-STRONG. The obligation is byte-
    # identical; `loom_solve` alone closes the reshaped (straight-line) goal.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    return selectNames selector excl candidates",
            "prove_correct selectModelFields by\n  loom_solve"),
        "rationale": "clause (C1) `out = selectNames selector excl candidates` is "
                     "pinned to a total, grounded function of the three inputs, so "
                     "directly returning it is the honest cheapest CORRECT impl. A "
                     "correct reshape MUST verify, else the postcondition is over-fit "
                     "to the loop shape => SPEC-TOO-STRONG. Also shows the spec is "
                     "not echo-vulnerable (any WRONG value fails (C1)).",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — same backward loop, but each per-element
    # keep-decision is hoisted into a named local `k` before the prepend. The
    # loop direction and every invariant/`done_with` are UNCHANGED (a forward
    # loop would need an f(a++b)=f(a)++f(b) lemma against the front-recursive
    # `selectNames` fold), so the frozen proof script still closes. Only the
    # executable shape (a `let k :=` then a guarded prepend) differs. MUST verify;
    # else the postcondition is over-fit to the exact expression => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-localvar",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    let mut result : List Int := []\n"
            "    let mut i := candidates.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ candidates.length\n"
            "      invariant result = selectNames selector excl (candidates.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := candidates[i - 1]!\n"
            "      let k := keep selector excl c\n"
            "      result := (if k then [c] else []) ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "structurally-different but equivalent CORRECT impl: the "
                     "per-element keep-decision is hoisted into a named local before "
                     "the prepend. Same backward loop, same invariants/done_with "
                     "verbatim (so the front-recursive `selectNames` fold needs no "
                     "append lemma and the frozen proof still closes); only the "
                     "executable shape differs. Must verify (else SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling self-calls on the F2P-shaped input to
    # show the modeled behaviour is ADMITTED. This bundle has NO `require` clause
    # (nothing can be PRECOND-TOO-STRONG), so the probe is re-aimed at the
    # residual admissibility risk on a transparent carrier: that the post-image is
    # DEGENERATE, i.e. does not actually demand an empty result for the headline
    # present-empty-selector case. An in-region assert pins that the F2P headline
    # configuration (a supplied selector that lists nothing, over a non-empty
    # candidate set) selects NOTHING. The assert is LIVE (replacing `= []` with a
    # non-empty claim leaves an unsolved goal — RE-MEASURED during the
    # independent audit, not merely asserted: replacing `= []` with `= [1, 2]`
    # and giving the proof a deliberately TOLERANT script (the frozen rewrite
    # plus `all_goals try simp [selectNames, keep]; all_goals try decide`, so no
    # honest goal is left unclosed for a tactic-shape reason) still fails with
    #   error: unsolved goals
    #   case «admiss_1: (selectNames (some ([] : List Int)) [] [1, 2] = [1, 2])»
    #   ⊢ False
    # i.e. the assert is genuinely load-bearing: the false claim reduces to
    # `False`, so this assert cannot be satisfied by any tactic); the frozen
    # loop body follows it so the method's own `ensures` obligation still
    # discharges. The proof is retuned only to also close the added assert goal.
    # =====================================================================
    {
        "id": "admiss-f2p-empty-selector",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_TOP,
                  "    assert (with_name_prefix `admiss\n"
                  "      (selectNames (some ([] : List Int)) [] [1, 2] = []))\n"
                  + _IMPL_TOP),
            _PROOF,
            "prove_correct selectModelFields by\n"
            "  loom_solve\n"
            "  · rw [selectNames_drop_step selector excl candidates i (by omega) (by omega)]\n"
            "    rw [‹result = selectNames selector excl (candidates.drop i)›]"),
        "rationale": "the F2P headline configuration (a supplied selector that lists "
                     "nothing, over a non-empty candidate set) selects NOTHING — the "
                     "exact behaviour the failing test exercises when it supplies an "
                     "empty selector and expects an empty collected key set. The "
                     "in-region assert is live (a "
                     "non-empty claimed result leaves an unsolved goal) and the frozen "
                     "loop keeps the ensures obligation intact, so the module verifies; "
                     "this witnesses the spec ADMITS the modeled F2P behaviour rather "
                     "than being vacuous or over-strong there.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a
    # STRAIGHT-LINE wrong impl (so its extracted program reduces under `decide`,
    # letting the tester witness name the counterexample); it stays wrong for a
    # VALUE reason, not a shape reason.
    # =====================================================================
    {
        "id": "weak-truthiness",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: a present-but-empty selector is treated like an
        # absent one (keeps everything) instead of keeping nothing. Correct on
        # every input EXCEPT selector = some [].
        "module": _with_impl(
            "    let sel' := match selector with | some [] => none | s => s\n"
            "    return selectNames sel' excl candidates"),
        "refinement": "this IS the pre-patch skeleton: the selector filter uses "
                      "TRUTHINESS gating (a supplied-but-empty selector is treated "
                      "like an absent one), the exact truthiness-vs-presence defect "
                      "the issue reports. Its faithful real patch is the UNPATCHED "
                      "guard, which the added F2P assertion for the present-empty "
                      "selector FAILS (it collects every editable name instead of "
                      "none). A verifying rival here would be a true "
                      "verify-does-not-resolve break.",
        "rationale": "REJECT from (C1)/(C2): on a present-empty selector (some []) "
                     "`selectNames` keeps NOTHING, but the rival re-maps it to `none` "
                     "and keeps everything. Refuted at exactly the present-empty "
                     "sub-domain (selector = some []), where this rival diverges from "
                     "gold while agreeing on every other selector shape.",
        "witness_reference": _REF_DIRECT,
        "witness": _TESTER +
                   "example : selectModelFieldsTester [1] (some []) [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-restrict-none-drops",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the `selector = none => keep all` branch: an ABSENT selector is
        # treated as a membership filter that matches nothing. Correct only when
        # a selector is supplied; WRONG on the default (absent-selector) call.
        "module": _with_impl(
            "    let sel' := match selector with | none => some ([] : List Int) | s => s\n"
            "    return selectNames sel' excl candidates"),
        "refinement": "treats an ABSENT selector (the default, most common call) as "
                      "a supplied selector matching nothing. The faithful real patch "
                      "would drop the presence guard entirely and keep nothing for "
                      "the default call, breaking the baseline PASS-to-PASS keyset "
                      "assertion (the default call must collect every candidate "
                      "name, and this rival collects none), so it does NOT resolve.",
        "rationale": "REJECT from (C1): when the selector is absent (none) "
                     "`selectNames` keeps ALL candidates, but the rival re-maps it to "
                     "`some []` and keeps nothing. Refuted at the absent-selector "
                     "sub-domain (selector = none), which varies the selector binder "
                     "against the present-empty value the truthiness witness holds.",
        "witness_reference": _REF_DIRECT,
        "witness": _TESTER +
                   "example : selectModelFieldsTester [1] none [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-drop-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the `n ∉ excl` conjunct: an excluded candidate is no longer
        # dropped. Correct on every input with an empty (or non-matching) excl
        # list; WRONG whenever a candidate name appears in excl.
        "module": _with_impl(
            "    return candidates.filter (fun n =>\n"
            "      match selector with | none => true | some p => decide (n ∈ p))"),
        "refinement": "drops the exclusion conjunct (the second filter knob on the "
                      "candidate-collection loop, UNCHANGED by the gold hunk and "
                      "modeled faithfully in the spec). The faithful real patch would "
                      "emit excluded names into the result, breaking the added "
                      "assertion for a non-empty exclusion (which requires the "
                      "excluded names to be absent from the collected key set), so it "
                      "does NOT resolve.",
        "rationale": "REJECT from (C1)/(C3): when a candidate is in `excl`, "
                     "`keep` is false and `selectNames` drops it, but the rival keeps "
                     "it. Refuted at a non-empty exclusion (excl = [1] containing the "
                     "sole candidate), which varies the excl binder against the empty "
                     "value the other witnesses hold.",
        "witness_reference": _REF_DIRECT,
        "witness": _TESTER +
                   "example : selectModelFieldsTester [1] none [1] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-partial-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Never considers the first source element (drops candidates[0]). Correct
        # on every input whose first candidate would not survive; WRONG whenever
        # candidates[0] survives all filters. Attacks per-element source order /
        # multiplicity, which every value witness above holds at a singleton list.
        "module": _with_impl(
            "    return selectNames selector excl (candidates.drop 1)"),
        "refinement": "never keeps the first source candidate. The faithful real "
                      "patch would special-case the head of the candidate chain to "
                      "skip it (an off-by-one drop of the leading candidate) — the "
                      "baseline keyset assertion enumerates every candidate name "
                      "including the first, so it would lose one and FAIL; it does "
                      "NOT resolve.",
        "rationale": "REJECT from (C1): `selectNames` keeps every surviving "
                     "candidate in source order, but the rival never considers "
                     "candidates[0]. Refuted at a two-element list (candidates = "
                     "[1,2], both surviving) where gold returns [1,2] and the rival "
                     "returns [2] — a point that varies the candidates binder (length "
                     "2) against the singleton lists the other witnesses probe.",
        "witness_reference": _REF_DIRECT,
        "witness": _TESTER +
                   "example : selectModelFieldsTester [1, 2] none [] = false := by\n"
                   "  decide\n",
    },

    # =====================================================================
    # UNIQUENESS — added during the independent audit. Every rival above
    # attacks WHICH names survive; none attacks the ORDER they are emitted in,
    # even though (C1) pins `out` to `selectNames`, a list, and the F2P
    # observation is a SORTED comparison that would mask a permutation. So the
    # ordering content of (C1) was asserted by the prose ("in candidate order")
    # and demonstrated by nothing: a rival that returns the right SET in the
    # wrong ORDER was unattacked. This rival returns exactly the reversed kept
    # list — right set, right multiplicity, wrong order — and is refuted at
    # candidates=[1,2] (gold [1,2], rival [2,1]). Note it is refuted at the same
    # INPUT POINT as weak-partial-first but on a different clause content
    # (permutation vs. omission), so it is not a duplicate probe.
    # =====================================================================
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    return (selectNames selector excl candidates).reverse"),
        "refinement": "emits the surviving names in reverse candidate order. The "
                      "faithful real patch would build the collection by prepending "
                      "each survivor instead of appending it, which is a plausible "
                      "way to write this loop and passes any assertion that sorts "
                      "the observed key list — so nothing in the sorted F2P/P2P "
                      "comparisons distinguishes it. It is still WRONG against the "
                      "modeled behaviour, whose result is the kept names in "
                      "candidate order; a dict built in reverse iteration order "
                      "changes the mapping's own ordering, which is observable "
                      "elsewhere (dicts preserve insertion order). Shipping it "
                      "would be a silent behaviour change the spec must forbid.",
        "rationale": "REJECT from (C1): `out = selectNames selector excl candidates` "
                     "fixes the ORDER of the kept names, not merely the set. This is "
                     "the only rival attacking permutation: note (C3) does NOT catch "
                     "it (every returned name is still a member and still passes "
                     "`keep`, so (C3) holds of this rival) and (C2) does not either "
                     "(reversing [] is []), so the rejection is attributable to (C1) "
                     "alone. Refuted at candidates=[1,2], selector=none, excl=[] "
                     "where gold returns [1,2] and the rival returns [2,1].",
        "witness_reference": _REF_DIRECT,
        "witness": _TESTER +
                   "example : selectModelFieldsTester [1, 2] none [] = false := by\n"
                   "  decide\n",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — added during the independent audit as a
    # real SPEC-TOO-STRONG probe. Both shipped positives are cheap in the
    # direction that matters least: pos-direct returns the spec function itself
    # (so `loom_solve` alone closes it) and pos-localvar keeps the frozen loop
    # with its invariants VERBATIM (so the frozen script closes it unchanged).
    # Neither forces the spec to accept a genuinely different ALGORITHM. This
    # one does: a forward `List.filter` with the two `keep` conjuncts REORDERED
    # (exclusion tested first), which is the shape the nagini sibling's
    # pos-reorder attacks and which the port's accounting block claimed had "no
    # distinct executable shape to reorder" on this carrier. It does have one,
    # and the spec accepts it — but only with a retuned proof (a commutation
    # fact plus a filter/fold bridge, both proven inline in the tactic body, no
    # new top-level theorem). Verified to build during the audit.
    # =====================================================================
    {
        "id": "pos-filter-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    return candidates.filter (fun n => decide (n ∉ excl) &&\n"
            "      (match selector with | none => true | some p => decide (n ∈ p)))",
            "prove_correct selectModelFields by\n"
            "  have hcomm : ∀ (sel : Option (List Int)) (e : List Int) (n : Int),\n"
            "      (decide (n ∉ e) &&\n"
            "        (match sel with | none => true | some p => decide (n ∈ p)))\n"
            "        = keep sel e n := by\n"
            "    intro sel e n; unfold keep; exact Bool.and_comm _ _\n"
            "  have hbridge : ∀ (sel : Option (List Int)) (e : List Int) (xs : List Int),\n"
            "      xs.filter (fun n => decide (n ∉ e) &&\n"
            "        (match sel with | none => true | some p => decide (n ∈ p)))\n"
            "        = selectNames sel e xs := by\n"
            "    intro sel e xs\n"
            "    induction xs with\n"
            "    | nil => rfl\n"
            "    | cons a rest ih =>\n"
            "        rw [List.filter_cons, selectNames_cons, ← ih]\n"
            "        simp only [hcomm]\n"
            "        by_cases hk : keep sel e a = true\n"
            "        · rw [if_pos hk]; simp [hk]\n"
            "        · rw [if_neg hk]; simp [hk]\n"
            "  loom_solve <;>\n"
            "    simp [hbridge] <;>\n"
            "    (intro h; subst h; simp [selectNames_empty_selector])"),
        "rationale": "a genuinely different CORRECT ALGORITHM, not a re-spelling: a "
                     "forward `List.filter` (the frozen impl is a backward indexed "
                     "`while` loop accumulating by prepend) whose per-element guard "
                     "tests the two `keep` conjuncts in the OPPOSITE order — "
                     "exclusion before selector-membership. Boolean conjunction is "
                     "commutative so the decision is identical, and the traversal "
                     "direction differs from gold's, so the frozen proof script does "
                     "NOT close it: it needs a commutation fact and a filter/fold "
                     "bridge to the front-recursive `selectNames`. Both are proven "
                     "INLINE in the tactic body (`have`), adding no top-level "
                     "theorem and no assumption. This must verify, else the "
                     "postcondition is over-fit to gold's traversal direction and "
                     "conjunct order => SPEC-TOO-STRONG. It is the strongest "
                     "soundness control in the battery: the other two positives are "
                     "closed by `loom_solve` alone or by the frozen script verbatim.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives + 1 admissibility + 2 frame-mutation rivals + 4 value rivals) and an
# empty AXIOM_TESTS. This velvet bundle models the SAME single behaviour (the
# field-selection decision), narrowed to its purely-functional core over a
# `List Int` carrier, so the port drops the fractional-permission machinery and
# re-expresses the value rivals onto the three `ensures` clauses.
#
#   nagini case                 -> here
#   ------------------------------------------------------------------------
#   pos-reorder                 -> (folded into pos-direct)     OMITTED (see below)
#   pos-localvar                -> pos-localvar                 PORTED
#   admiss-fshaped              -> admiss-f2p-empty-selector    PORTED (re-aimed)
#   frame-mut-names             -> (none)                       VACUOUS class
#   frame-mut-edit              -> (none)                       VACUOUS class
#   weak-truthiness             -> weak-truthiness              PORTED
#   weak-restrict-none-drops    -> weak-restrict-none-drops     PORTED
#   weak-drop-editability       -> weak-drop-removal            RE-AIMED (see below)
#   weak-partial-first          -> weak-partial-first           PORTED
#   AXIOM_TESTS (empty)         -> (dropped)                    AXIOM LANE
#
# ADDED (pos-direct): the sibling has no bare-return positive because its nagini
#   carrier cannot materialize the deep-model `projection` result directly. Here
#   clause (C1) IS `out = selectNames …` over a total grounded function, so the
#   cheapest honest impl (return it) is a legitimate soundness positive and the
#   grounded-oracle control (any WRONG value fails (C1)).
# PORTED (pos-reorder -> pos-filter-reorder), CORRECTING THIS FILE'S EARLIER
#   ACCOUNTING. A previous revision recorded pos-reorder as OMITTED, claiming
#   pos-direct "subsumes" it because this carrier "folds the guard into `keep`,
#   leaving no distinct executable shape to reorder". That was wrong on both
#   halves, and the independent audit landed the case rather than agreeing with
#   it. (i) There IS a distinct executable shape: an impl may spell the guard
#   itself — `decide (n ∉ excl) && (match selector with …)` — with the conjuncts
#   in either order, without mentioning `keep` at all. (ii) pos-direct cannot
#   subsume it: pos-direct returns the spec function, so it exercises no guard
#   ordering and no traversal at all, and `loom_solve` alone closes it. The real
#   reason the case was hard is that a reordered forward `filter` needs a retuned
#   proof (a `Bool.and_comm` step plus a filter/`selectNames` bridge), which is a
#   PROOF cost, not an expressibility limit — and "the proof was hard" is not a
#   reason to omit. Both facts are proven inline in the tactic body; the case
#   verifies. It is now the battery's strongest SPEC-TOO-STRONG control.
# PORTED (pos-localvar): the sibling's hoist-into-locals positive ports directly —
#   same backward loop, invariants verbatim, keep-decision hoisted into a local.
#   Verified to build with the frozen proof.
# PORTED (admissibility, re-aimed): the sibling establishes the precondition
#   ADMITS the F2P input via a self-call. This bundle has NO `require` clause, so
#   there is no precondition to be too-strong; the argument is carried instead by
#   an in-region assertion that the F2P headline configuration (a supplied selector
#   that lists nothing) selects NOTHING. The assert is live and the frozen ensures
#   obligation still discharges. Verified to build.
# VACUOUS (frame-mut-names, frame-mut-edit): referentially-transparent backend, no
#   `mut` parameter, no heap, no fractional permission — no read-only input to
#   overwrite. Not fabricated and not replaced. The audit did not take this on the
#   porting map's word: it BUILT the rival (`candidates := candidates ++ [0]` in
#   the impl region) and the front end refused it — "`candidates` cannot be
#   mutated, only variables declared using `let mut` can be mutated". A variant
#   that cannot be elaborated at all cannot carry a witness (there is no impl for
#   the witness to hold of), so the class is inexpressible here, not merely hard.
# RE-AIMED (weak-drop-editability -> weak-drop-removal): the sibling attacks the
#   editability filter (`e != 0`). On this carrier the editability restriction is
#   PRE-APPLIED to the modeled input — `candidates` is already the ordered list of
#   EDITABLE field names (mapping.md §1), so editability is not a binder the spec
#   observes and there is no editability conjunct in `keep` to drop. Attacking it
#   would need a rival that mishandles an input the modeled behaviour does not
#   distinguish (there is no such input), so no discriminating witness exists —
#   that class is genuinely not expressible on this carrier. In its place the
#   exclusion conjunct (`n ∉ excl`, modeled faithfully and exercised by the added
#   F2P `exclude=` assertions) is attacked instead: weak-drop-removal drops it and
#   is refuted at a non-empty exclusion. This keeps a value rival on every modeled
#   filter clause of `keep` while honestly dropping the unmodeled one.
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
# PORTED (the four value rivals): each carries a machine-checked witness that
#   ELABORATES against the (straight-line) rival and is REFUTED against the
#   `witness_reference` `_REF_DIRECT` (not against gold — see the CARRIER NOTE:
#   gold's `Exec` does not reduce, so its build fails by STUCK REDUCTION and
#   attests to nothing). The four witnesses probe four distinct points that
#   together vary all three input binders — a present-empty selector (some []), an
#   absent selector (none), a non-empty exclusion (excl = [1]), and a two-element
#   candidate list.
# ADDED (weak-reverse-order): not a nagini port. The audit found the ORDER content
#   of (C1) unattacked — every ported rival changes WHICH names survive, and the
#   sibling's own rivals do too, because the nagini F2P/P2P observations sort the
#   key list and so cannot see a permutation. On this carrier (C1) equates `out` to
#   a LIST, so ordering is pinned and a permutation rival is expressible and must
#   be rejected. It is, and its rejection is attributable to (C1) alone: (C2) and
#   (C3) both HOLD of the reversed rival.
# ADDED (pos-filter-reorder): see the pos-reorder entry above — the sibling case
#   the port had recorded as omitted, landed.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the selection is modeled deeply by keep/selectNames; mapping.md §2/§3
# note there is no axiom_check.py), so there is nothing to probe.
AXIOM_TESTS = []

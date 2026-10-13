"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10673 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end``, or inside the ``prove_correct`` tactic body, is changed — both
of which the consumer spec view elides, so ``markers.same_spec`` holds by
construction and the ``prove_correct selectToctreeEntries`` obligation survives).
``expect="verify"`` passes iff (in scope AND verifies); ``expect="reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — see the CARRIER NOTE for what the second half is measured
against here, and why it cannot be the frozen solution).

DEFENDED SURFACE (one contracted method, three READ-ONLY list inputs, no
``require`` — the admitted domain is total over all three lists):

  selectToctreeEntries (requested sourceDocs autoTargets : List String)
    return (out : List String)
    ensures out = retainedEntries sourceDocs autoTargets requested       -- (C1)
    ensures ∀ e, e ∈ out → e ∈ requested
                         ∧ targetExists sourceDocs autoTargets e = true  -- (C2)
    ensures ∀ e, e ∈ requested → autoTargets.contains e = true → e ∈ out -- (C3)
    ensures ∀ e, e ∈ requested → targetExists sourceDocs autoTargets e
                                   = true → e ∈ out                      -- (C4)

The method decides which requested table-of-contents entry names are retained. A
requested name is retained when it names a target that EXISTS — one with a
backing source file (``sourceDocs``), OR one of the reference targets the project
provides automatically (``autoTargets``: the index, module-index and search
pages). A name that exists in neither collection is omitted (a diagnostic is
emitted for it; only the retained sequence is observed).

  * (C1) pins ``out`` to ``retainedEntries sourceDocs autoTargets requested`` —
    the fully-unfolded front-recursive filter over the method's OWN three
    arguments. The ``axioms`` region declares no ``axiom`` and no ``opaque``
    leaf, so the whole carrier is TRANSPARENT: there is no answer-key oracle for
    a wrong impl to echo, and pinning ``out`` to it is grounded rather than an
    echo. C1 pins the retained SET, the request ORDER, and (by omission) that
    nothing unrequested is invented.
  * (C2) is the no-invention direction, and it has TWO independent conjuncts:
    every emitted name was REQUESTED, and every emitted name EXISTS.
  * (C3) is the discriminating clause of this bundle: a requested name belonging
    to the automatically-provided family must be retained EVEN IF it has no
    backing source file. It is stated over ``autoTargets.contains`` alone, so it
    cannot be satisfied by an impl that only ever consults the source-file
    family.
  * (C4) is C3's generalisation over BOTH families (``targetExists``), which
    additionally forces the source-file family's own retention.

THREE INPUT BINDERS, all load-bearing and all read-only (none is ``mut``; the
loop-locals ``out``/``i`` are the only mutable state). ``requested`` supplies both
the candidate set and the ORDER; ``sourceDocs`` and ``autoTargets`` are the two
independent membership carriers whose UNION decides retention. The reject
witnesses move all three across SIX distinct input triples (pts = 6), including
points where ``sourceDocs`` is the sole retention channel and points where
``autoTargets`` is — so neither family can be silently masking the other. See the
COVERAGE ledger at the bottom.

CARRIER NOTE — the decidable boundary, and what the frozen-side failure is worth.
A witness reaches the post-image through Velvet's own tester machinery
(``selectToctreeEntriesTester requested sourceDocs autoTargets = false`` says the
extracted program's result violates the conjoined postcondition C1∧C2∧C3∧C4 at
that concrete input) and closes by ``decide``, checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Every reject rival is a LOOP-FREE expression, so its extracted tester
reduces by kernel computation. The FROZEN impl keeps a ``while`` loop under
``loom.semantics.choice "demonic"``, whose fixpoint elaborates through
``Classical.choice``; the kernel cannot unfold it, so ``decide`` against the
frozen tester is STUCK for every claim, true or false. Measured verbatim:

    error: Tactic `decide` failed for proposition
      selectToctreeEntriesTester ["t1"] [] ["t1"] = false
    because its `Decidable` instance ... did not reduce to `isTrue` or `isFalse`.

So the frozen-side exit code carries NO information on this bundle, and a
TAUTOLOGOUS witness would produce the very same failure. Every reject case
therefore names ``witness_reference``: ``_REFERENCE``, a loop-free impl of the
same frozen spec that VERIFIES (shipped in its own right as
``pos-control-direct-model``). Against it every witness is refuted SEMANTICALLY —
measured for all six:

    error: Tactic `decide` proved that the proposition
      selectToctreeEntriesTester ["t1"] [] ["t1"] = false
    is false

which is the discrimination the reduction-stuck frozen build cannot supply. An
impl the verifier ACCEPTS cannot violate its own spec, so a witness that fails
there fails on the spec's content, not on the kernel's inability to look. Every
witness states its refutation at concrete literals and binds no hypothesis, so no
consistency probe applies and none can be vacuous through an inconsistent binder.

PROOF-SHAPE CONTROL — why each rejection is attributable to the EXPRESSION rather
than to a tactic mismatch. Every reject rival is a loop-free ``return <expr>``
under the bare ``loom_solve`` body, and that exact shape and script carrying the
CORRECT expression VERIFIES (``pos-control-direct-model``, exit 0, measured).
Under it each rival still fails, and the residual goal names the rival's own
expression — e.g. ``⊢ retainedEntries sourceDocs [] requested = retainedEntries
sourceDocs autoTargets requested`` — which is the attribution. Shipping the
reference as a positive is also what records that LOOP-FREENESS is not what any
rival is being rejected for.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY, and are the real work on a
    tactic-proof backend. Three structurally different CORRECT impls must verify:
    the loop-free direct return of the grounded filter, the loop-preserving body
    reshape (hoist the membership decision into a local and name the prepended
    fragment), and a FORWARD ``List.filter`` bridged to the front-recursive model
    by an induction inside the tactic body. All three reprove honestly — no
    ``sorry``/``admit``/``native_decide``, no new ``axiom``, no new top-level
    ``theorem``/``lemma``.
  * ADMISSIBILITY — RE-AIMED. See the case comment: with no ``require`` at all,
    "a normal input satisfies the precondition" cannot fail, so the case is
    re-aimed at post-image NON-DEGENERACY via a live in-region ``assert``.
  * FRAME / PERMISSION MUTATION — VACUOUS on this carrier, and MEASURED rather
    than asserted. See the accounting note.
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
  * UNGROUNDED-ORACLE ECHO — N/A, same reading as the sibling's: C1 is pinned to
    a fully-unfolded ``def`` over the method's own three arguments, so there is no
    answer-key term to echo. The cheapest correct impl computes the filter
    honestly, which the positives cover.
  * CONTROL-FLOW-EFFECT (raise vs return) — the only control-flow difference in
    the modeled behaviour is the diagnostic emitted for a name that does not
    exist, and the frozen spec observes only the retained sequence (stated in the
    spec view). There is no raise/side-effect difference invisible to the value
    model, so no capability-token rival is needed.
  * PARTIAL-DOMAIN / VALUE — carries the whole reject lane: six rivals, each
    right on most of the domain and wrong on one sub-domain.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The bundle consumes no ``axiom`` (the
``axioms`` region is prose only; the one grounded R-binding is G-AX's job per
mapping.md §3), and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10673"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS. Each lies wholly inside the region it edits (the impl block, the loop
# body, the impl-start marker line, or the `prove_correct` tactic body) and is
# asserted UNIQUE at load, so the manifest breaks loudly if the frozen solution
# ever drifts.
# ---------------------------------------------------------------------------

# The whole impl block, markers included. Every loop-free variant swaps on this.
_IMPL = """    -- impl-start
    let mut out : List String := []
    let mut i := requested.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requested.length
      invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
      done_with i = 0
      decreasing i
    do
      let e := requested[i - 1]!
      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
      i := i - 1
    return out
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# The loop-body lines only. The loop-preserving positive reshapes just these,
# leaving the loop, its invariants and the frozen proof script intact.
_LOOP_BODY = """      let e := requested[i - 1]!
      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# The impl-start marker line. The admissibility case inserts an in-region
# `assert` immediately after it and keeps the whole frozen body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only — elided from the spec view). Any
# variant that removes the loop must retune it, since there is then no invariant
# to peel. The `prove_correct selectToctreeEntries` header always survives.
_PROOF_GOLD = """prove_correct selectToctreeEntries by
  loom_solve
  rw [retainedEntries_drop_step sourceDocs autoTargets requested i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# The loop-free proof body: with no loop there is no drop-step to rewrite, so
# `loom_solve` alone is the honest script. Not a weakening and not a confound —
# this exact body carrying the CORRECT expression VERIFIES
# (pos-control-direct-model, measured exit 0), so a rival failing under it fails
# for its EXPRESSION, and the residual goal names that expression.
_PROOF_FLAT = """prove_correct selectToctreeEntries by
  loom_solve"""


def _direct(expr, proof=_PROOF_FLAT):
    """A loop-free variant: `return <expr>`, reproved by `proof`."""
    return _swap(_swap(_BASE, _IMPL,
                       "    -- impl-start\n"
                       f"    return {expr}\n"
                       "    -- impl-end"),
                 _PROOF_GOLD, proof)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. The loop-free direct return of the grounded filter: a
# machine-checked-correct impl of the frozen spec whose extracted tester REDUCES.
# It is shipped as a positive control in its own right (pos-control-direct-model)
# AND named by every reject case as its `witness_reference`, because the FROZEN
# impl cannot serve as the witness's second subject on this bundle — its `while`
# loop elaborates through `Classical.choice`, so `decide` on the frozen tester is
# stuck for EVERY claim and its exit code discriminates nothing (CARRIER NOTE).
# ---------------------------------------------------------------------------
_REFERENCE = _direct("retainedEntries sourceDocs autoTargets requested")


# ---------------------------------------------------------------------------
# WITNESS MECHANICS. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the post-image through Velvet's own tester machinery. The
# directives are appended to BOTH builds, so `selectToctreeEntriesTester` exists
# on both sides by construction. Argument order follows the method signature:
# (requested, sourceDocs, autoTargets).
# ---------------------------------------------------------------------------
def _witness(requested, source_docs, auto_targets):
    return (
        "\n"
        "extract_program_for selectToctreeEntries\n"
        "prove_precondition_decidable_for selectToctreeEntries\n"
        "prove_postcondition_decidable_for selectToctreeEntries\n"
        "derive_tester_for selectToctreeEntries\n\n"
        f"example : selectToctreeEntriesTester {requested} {source_docs} "
        f"{auto_targets} = false := by\n"
        "  decide\n")


# Neutral literal names for the witness / assert inputs. `t*` stands for a name
# in the automatically-provided family, `s*` for one with a backing source file,
# `x*` for one that exists in neither.
_T1, _T2, _T3 = '"t1"', '"t2"', '"t3"'
_S1 = '"s1"'
_X9 = '"x9"'


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS / positive controls — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. On this backend each needs a proof that actually closes
    # for its own shape; all three do, with no assumption of any kind.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest correct impl: return the grounded model directly,
        # no loop at all — maximally structurally different from the frozen
        # backward scan. `out` IS the model, so C1 holds by reflexivity and
        # C2/C3/C4 fall out of the frozen `mem_retainedEntries` characterisation
        # `loom_solve`/`grind` already has. Also this battery's WITNESS REFERENCE
        # (see the CARRIER NOTE), which is why it must be a case in its own
        # right: the gate then records that a loop-free impl of this spec
        # VERIFIES, so no rival is being rejected merely for being loop-free.
        "module": _REFERENCE,
        "rationale": (
            "the grounded filter is returned directly (no loop), so C1 "
            "(`out = retainedEntries sourceDocs autoTargets requested`) holds by "
            "reflexivity and the three membership clauses C2/C3/C4 follow from the "
            "frozen `mem_retainedEntries` characterisation. Maximally different "
            "from the frozen backward scan, so if it failed to verify the spec "
            "would be over-fit to the loop code shape (SPEC-TOO-STRONG). It is "
            "also the honest no-ungrounded-echo control: the filter IS the real "
            "work over the method's own three arguments, so returning it is "
            "correct rather than a cheat — every WRONG expression fails C1, as the "
            "six rivals measure. Ports the sibling pos-control-local-reshape into "
            "the maximally-different correct shape, and doubles as the "
            "`witness_reference` every reject case names."),
    },
    {
        "id": "pos-control-loop-body-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the loop, its invariants and the frozen proof script byte for
        # byte; only reshapes the body — hoist the membership decision into a
        # boolean local and name the prepended fragment in a typed local, exactly
        # the sibling's `is_known` / `head` reshape. Observationally identical at
        # every input.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let e := requested[i - 1]!\n"
            "      let present : Bool := targetExists sourceDocs autoTargets e\n"
            "      let fragment : List String := if present then [e] else []\n"
            "      out := fragment ++ out\n"
            "      i := i - 1"),
        "rationale": (
            "the direct port of the sibling's positive control: hoist the "
            "membership decision into a boolean local and name the prepended "
            "fragment in a typed local, keeping the front-prepend shape. "
            "`targetExists` is a pure `def`, so the local is definitionally the "
            "same decision the model branches on and every clause C1..C4 still "
            "holds on the whole domain; the loop, its invariants and the frozen "
            "proof script are untouched. A correct reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG over the shape of the loop body."),
    },
    {
        "id": "pos-control-forward-filter",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely DIFFERENT algorithm shape: a FORWARD `List.filter` instead
        # of the frozen backward prepend-scan. The spec's model is
        # front-recursive, so this needs a real bridge — an induction proving
        # `List.filter <the decision> = retainedEntries ...`. That bridge is a
        # `have` INSIDE the tactic body, NOT a new top-level lemma, so the variant
        # adds no declaration and assumes nothing.
        "module": _direct(
            "requested.filter (fun e => targetExists sourceDocs autoTargets e)",
            "prove_correct selectToctreeEntries by\n"
            "  have hfil : ∀ (l : List String),\n"
            "      l.filter (fun e => targetExists sourceDocs autoTargets e)\n"
            "        = retainedEntries sourceDocs autoTargets l := by\n"
            "    intro l\n"
            "    induction l with\n"
            "    | nil => rfl\n"
            "    | cons a t ih =>\n"
            "      rw [List.filter_cons, retainedEntries_cons]\n"
            "      by_cases hp : targetExists sourceDocs autoTargets a = true\n"
            "      · simp [hp, ih]\n"
            "      · simp [hp] at *\n"
            "        simp [hp, ih]\n"
            "  loom_solve\n"
            "  all_goals (try rw [hfil requested])\n"
            "  all_goals simp_all"),
        "rationale": (
            "a FORWARD traversal (`List.filter` of the membership decision) "
            "instead of the frozen backward prepend-scan — the most different "
            "correct shape that still traverses, and the one whose proof does not "
            "come for free: the spec's model is front-recursive, so the variant "
            "reproves C1 through an induction bridging `List.filter` to it, "
            "carried as a `have` INSIDE the tactic body (no new top-level "
            "declaration, no assumption of any kind). Must verify: filtering the "
            "request list by the same decision retains exactly the same names in "
            "exactly the request order, so C1..C4 all hold. If a correct impl "
            "whose traversal direction differs from the frozen one could not "
            "verify, the spec would be SPEC-TOO-STRONG on traversal shape."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The sibling's probe re-establishes that its
    # fractional-permission precondition admits an F2P-shaped input. This method
    # has NO `require` at all, so nothing could exclude a normal input and that
    # probe cannot fail here — an admissibility case that cannot fail is
    # decoration. The residual risk on a total domain is instead a DEGENERATE
    # post-image (a spec no impl distinguishes reads exactly like one every impl
    # meets), so this case discharges a live in-region `assert` pinning that the
    # modeled filter genuinely DISCRIMINATES at F2P-shaped inputs: three
    # requested names that exist ONLY in the automatically-provided family are ALL
    # retained in request order (the discriminating sub-domain); a mixed request
    # retains one name from each family and DROPS the name that exists in neither;
    # and with both collections empty the retained sequence is genuinely empty.
    # The frozen impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the extra assert goal
    # (the tactic body is elided from the spec view).
    # The assert is LIVE, not decoration — measured: negating just the third
    # conjunct leaves ``Tactic `decide` proved that the proposition ... is false``
    # (exit 1).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  f"      retainedEntries [{_S1}] [{_T1},{_T2},{_T3}] "
                  f"[{_T1},{_T2},{_T3}] = [{_T1},{_T2},{_T3}] ∧\n"
                  f"      retainedEntries [{_S1}] [{_T1},{_T2},{_T3}] "
                  f"[{_S1},{_T1},{_X9}] = [{_S1},{_T1}] ∧\n"
                  f"      retainedEntries [] [] [{_T1}] = []))\n"),
            _PROOF_GOLD,
            "prove_correct selectToctreeEntries by\n"
            "  loom_solve\n"
            "  all_goals (try (rw [retainedEntries_drop_step sourceDocs "
            "autoTargets requested i (by omega) (by omega)]\n"
            "                  simp_all))\n"
            "  all_goals decide"),
        "rationale": (
            "the post-image is satisfiable AND NON-DEGENERATE at F2P-shaped "
            "inputs, discharged as a live in-region assert: three requested names "
            "that exist ONLY in the automatically-provided family are all retained "
            "IN REQUEST ORDER (the discriminating sub-domain of this bundle, and "
            "the point C3 exists to pin); a mixed request retains one name from "
            "each family and DROPS the one that exists in neither; and with both "
            "membership collections empty the retained sequence is genuinely "
            "empty. So the modeled filter is neither a constant nor a collapse, "
            "and the obligation is not degenerate. The frozen impl is kept "
            "verbatim so C1..C4 still discharge. RE-AIMED from the sibling "
            "admiss-gold-shape: that case witnesses that a fractional-permission "
            "precondition admits an F2P-shaped input, but this method has NO "
            "`require`, so the precondition-admissibility question is vacuous here "
            "and post-image non-degeneracy is the sharper residual risk."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input triple, and the refinement argument that its
    # faithful real counterpart would NOT resolve the failing test. Every rival
    # is loop-free under the bare `loom_solve` body — the SAME shape and script
    # that VERIFY for the correct expression (pos-control-direct-model) — so each
    # rejection is attributable to its expression rather than to a tactic gap.
    #
    # F2P scenario grounding the refinements: a document requests three entry
    # names that the project provides automatically (the index, module-index and
    # search reference pages) and that have NO backing source file. The test
    # asserts all three are retained, in request order, as that document's
    # table-of-contents entries.
    # =====================================================================
    {
        "id": "weak-source-family-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Classify against the backing-source-file family ALONE,
        # ignoring the automatically-provided family — the pre-change behaviour,
        # expressed here by handing the model an empty automatic family. Correct
        # on every input whose retained set is unaffected by that family; drops
        # exactly the names that exist ONLY there.
        "module": _direct("retainedEntries sourceDocs [] requested"),
        "refinement": (
            "this IS the pre-change behaviour: a requested name is accepted only "
            "when it has a backing source file, so the automatically-provided "
            "reference targets are treated as not existing. On the failing test "
            "the three requested names are precisely of that kind — provided "
            "automatically, with no backing source file — so this rival drops all "
            "three and emits the nonexisting-document diagnostic for each. The "
            "document's table-of-contents entries would be EMPTY instead of the "
            "asserted three-entry sequence, so it does NOT resolve. It is the "
            "behaviour the pre-patch skeleton implements (G-DIFF)."),
        "rationale": (
            "REJECT from C3 (`∀ e, e ∈ requested → autoTargets.contains e = true "
            "→ e ∈ out`) — the clause stated over the automatic family ALONE, "
            "which is unsatisfiable for an impl that never consults it — and also "
            "from C4 and C1. Refuted at `requested = [t1]`, `sourceDocs = []`, "
            "`autoTargets = [t1]`: the reference impl retains `[t1]` and the rival "
            "returns `[]`. This witness drives `sourceDocs` to EMPTY, so the "
            "automatic family is the sole retention channel at that point and the "
            "divergence cannot be masked by the source-file family. Verifying "
            "would be SPEC-TOO-WEAK (the spec would admit the pre-change "
            "behaviour). Ports the sibling partial-domain-found-only."),
        "witness": _witness(f"[{_T1}]", "[]", f"[{_T1}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-auto-family-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR of the bug, and the case that keeps the two membership
        # carriers from being tested as one: consult the automatically-provided
        # family ALONE and ignore the backing-source-file family. It gets the
        # bundle's headline sub-domain exactly RIGHT, so nothing about the change
        # itself would catch it — only the union's other half does.
        "module": _direct("retainedEntries [] autoTargets requested"),
        "refinement": (
            "corresponds to a patch that REPLACED the backing-source-file "
            "membership test with the automatically-provided one instead of "
            "UNIONING them. Every ordinary requested name — one with a real "
            "backing source file — would then be reported as nonexisting and "
            "dropped from its document's table of contents. The failing test's own "
            "document also requests an ordinary name with a backing source file "
            "alongside the three automatic ones, and the surrounding "
            "table-of-contents suite asserts those ordinary entries throughout, so "
            "this does NOT resolve. It is the near-miss that gets the change's own "
            "sub-domain right and breaks everything else."),
        "rationale": (
            "REJECT from C4 (`∀ e, e ∈ requested → targetExists sourceDocs "
            "autoTargets e = true → e ∈ out`) and C1: `targetExists` is the "
            "DISJUNCTION, so a requested name with a backing source file must be "
            "retained, and this rival drops it. Refuted at `requested = [s1]`, "
            "`sourceDocs = [s1]`, `autoTargets = [t1]`: the reference impl retains "
            "`[s1]` and the rival returns `[]`. Deliberately a DIFFERENT point "
            "from weak-source-family-only — here `sourceDocs` is non-empty and the "
            "requested name is absent from `autoTargets`, the exact dual — so the "
            "manifest demonstrates that BOTH membership binders are load-bearing "
            "and neither is masking the other. Without this case a spec pinned "
            "only to the automatic family would look fully defended."),
        "witness": _witness(f"[{_S1}]", f"[{_S1}]", f"[{_T1}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-first-requested",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the FIRST requested name unconditionally (classify only the tail).
        # Correct on every request whose leading name does not exist anyway, and
        # on the empty request; wrong whenever the leading name exists.
        "module": _direct(
            "retainedEntries sourceDocs autoTargets (requested.drop 1)"),
        "refinement": (
            "corresponds to a faithful patch whose parse loop never classifies the "
            "FIRST content line of the directive — a leading retained name would "
            "be dropped from its document's table of contents. On the failing test "
            "the first of the three requested automatic names must be retained; "
            "dropping it yields a two-entry sequence instead of the asserted "
            "three-entry one, so it does NOT resolve. Correct on every request "
            "whose leading name does not exist anyway, which is what makes it a "
            "partial-domain break rather than an obvious one."),
        "rationale": (
            "REJECT from C1 (`out = retainedEntries sourceDocs autoTargets "
            "requested`), which pins the filter over the WHOLE request sequence, "
            "and from C3/C4, which quantify over every requested name and so are "
            "violated at the leading one. Refuted at `requested = [t1,t2]`, "
            "`sourceDocs = []`, `autoTargets = [t1,t2]`: the reference impl "
            "retains both in order and the rival returns `[t2]`. This is a "
            "length-2 request, so `requested.length` is moved off 1, and it is the "
            "only witness whose divergence is POSITIONAL rather than "
            "membership-driven. Ports the sibling partial-domain-drop-first."),
        "witness": _witness(f"[{_T1},{_T2}]", "[]", f"[{_T1},{_T2}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER ALONE. Retain exactly the right SET of names — every membership
        # decision is correct — but emit them in the opposite order. This is the
        # only rival whose output is a permutation of the correct answer, so it
        # isolates C1's ORDER content: C2, C3 and C4 are all membership
        # statements and this rival satisfies every one of them.
        "module": _direct(
            "(retainedEntries sourceDocs autoTargets requested).reverse"),
        "refinement": (
            "corresponds to a patch that accumulates the retained entries by "
            "prepending while walking the request forward (or appending while "
            "walking it backward) — every membership decision right, the sequence "
            "reversed. The failing test asserts the retained entries as an ORDERED "
            "sequence matching the request order, and a reversed sequence also "
            "renders the document's table of contents in the wrong order, so it "
            "does NOT resolve. A pure ORDER break: no retention decision is "
            "wrong."),
        "rationale": (
            "REJECT from C1 ALONE (`out = retainedEntries sourceDocs autoTargets "
            "requested`), the only clause with ORDER content. C2, C3 and C4 are "
            "membership statements and this rival SATISFIES all three — measured: "
            "the residual goal is exactly `⊢ (retainedEntries sourceDocs "
            "autoTargets requested).reverse = retainedEntries sourceDocs "
            "autoTargets requested` and nothing else — which is what makes it an "
            "order probe rather than another membership probe, and the only rival "
            "that would survive a spec stating membership without sequence "
            "equality. Refuted at `requested = [t1,t2]`, `sourceDocs = [t1,t2]`, "
            "`autoTargets = []`: the reference impl returns `[t1,t2]` and the rival "
            "`[t2,t1]`. This is the only witness with `autoTargets = []`, so it "
            "also demonstrates that the source-file family alone drives retention "
            "at that point."),
        "witness": _witness(f"[{_T1},{_T2}]", f"[{_T1},{_T2}]", "[]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-retain-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the existence decision entirely: retain every requested name.
        # Correct exactly when every requested name exists; wrong as soon as one
        # does not. Attacks the no-invention direction (C2) from the "emits a
        # name that does not exist" side while satisfying both retention clauses.
        "module": _direct("requested"),
        "refinement": (
            "corresponds to a patch that widened the acceptance test until it "
            "accepts everything (e.g. dropping the membership check rather than "
            "unioning the second family into it). A requested name that names no "
            "target at all would then be silently accepted into the document's "
            "table of contents instead of being reported, and the surrounding "
            "table-of-contents suite asserts exactly which entries a document "
            "yields — including that a name with no target is excluded and "
            "diagnosed — so it does NOT resolve. Correct only on requests where "
            "every name already exists."),
        "rationale": (
            "REJECT from C2 (`∀ e, e ∈ out → e ∈ requested ∧ targetExists "
            "sourceDocs autoTargets e = true`) and C1: C2 is the no-invention "
            "direction, and this rival emits a name that exists in NEITHER "
            "family. It satisfies both retention clauses C3 and C4 (it retains "
            "everything, so a fortiori everything that exists), so it is the rival "
            "that isolates C2's `targetExists` conjunct — the half of the spec the "
            "retention-side rivals cannot reach. Refuted at `requested = [t1,x9]`, "
            "`sourceDocs = []`, `autoTargets = [t1]`: the reference impl returns "
            "`[t1]` and the rival `[t1,x9]`. This is the only witness whose "
            "`requested` contains a name absent from BOTH membership collections, "
            "so it is the only point at which the omission behaviour is probed at "
            "all."),
        "witness": _witness(f"[{_T1},{_X9}]", "[]", f"[{_T1}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-append-auto-family",
        "kind": "uniqueness",
        "expect": "reject",
        # Filter the request correctly, then ALSO append the whole automatic
        # family — names that were never requested. Correct exactly when the
        # automatic family is empty. Attacks C2's `e ∈ requested` conjunct, the
        # one clause weak-retain-everything leaves standing.
        "module": _direct(
            "retainedEntries sourceDocs autoTargets requested ++ autoTargets"),
        "refinement": (
            "corresponds to a patch that made the automatically-provided "
            "reference targets available by APPENDING them to every document's "
            "table-of-contents entries rather than by admitting them when they are "
            "REQUESTED. Every document would then gain those entries whether or "
            "not it asked for them. The failing test asserts the exact entry "
            "sequence of a specific directive, and the surrounding suite asserts "
            "the entry sequences of documents that request none of them, so the "
            "spurious entries break both and it does NOT resolve — a plausible "
            "over-fix that satisfies the reported symptom while corrupting every "
            "other document."),
        "rationale": (
            "REJECT from C2's `e ∈ requested` conjunct — the clause pinning that "
            "nothing UNREQUESTED is emitted — and from C1. This rival gets every "
            "retention decision right and satisfies C3 and C4, and unlike "
            "weak-retain-everything the names it invents genuinely EXIST, so C2's "
            "`targetExists` conjunct holds too: only `e ∈ requested` refutes it. "
            "Refuted at `requested = [s1]`, `sourceDocs = [s1]`, `autoTargets = "
            "[t1,t2]`: the reference impl returns `[s1]` and the rival "
            "`[s1,t1,t2]`. This is the only witness where `autoTargets` holds "
            "names absent from `requested`, so it is the only point that probes "
            "whether the automatic family may leak into the output unrequested."),
        "witness": _witness(f"[{_S1}]", f"[{_S1}]", f"[{_T1},{_T2}]"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling ships 5 SPEC cases (1 soundness, 1
# admissibility, 3 uniqueness — one of which is the MANDATORY frame-mutation
# rival) plus an AXIOM lane of 2 probes. It contracts
# `select_toctree_entries(entries, found, generated)` over three READ-ONLY
# half-permission `List[int]` columns, with the load-bearing postcondition
# pinning the result to the front-recursive `kept` fold whose head decision is
# membership in EITHER family. This backend models the SAME decision, at the same
# depth, over `List String` instead of `List[int]`, and adds three membership
# clauses (C2/C3/C4) that the sibling's single sequence equality subsumes.
#
#   sibling case                  kind          -> here                         disposition
#   ----------------------------------------------------------------------------------------
#   pos-control-local-reshape     soundness     -> pos-control-loop-body-reshape PORTED
#                                               +  pos-control-direct-model      ADDED
#                                               +  pos-control-forward-filter    ADDED
#   admiss-gold-shape             admissibility -> admiss-nondegenerate          RE-AIMED
#   partial-domain-found-only     uniqueness    -> weak-source-family-only       PORTED
#   partial-domain-drop-first     uniqueness    -> weak-drop-first-requested     PORTED
#   frame-mutation-write-entries  uniqueness    -> (none)                        VACUOUS (measured)
#   (no sibling)                  uniqueness    -> weak-auto-family-only         ADDED
#   (no sibling)                  uniqueness    -> weak-reversed-order           ADDED
#   (no sibling)                  uniqueness    -> weak-retain-everything        ADDED
#   (no sibling)                  uniqueness    -> weak-append-auto-family       ADDED
#   AXIOM_TESTS (2)               axiom         -> (none)                        DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 3 soundness, 1 admissibility, 6 uniqueness. NOTHING was
# omitted for being hard to prove; all three soundness positives close honestly,
# with no `sorry`/`admit`/`native_decide`, no new `axiom`, and no new top-level
# `theorem`/`lemma` (the forward-filter bridge is a `have` inside the tactic
# body).
#
# PORTED (partial-domain-found-only -> weak-source-family-only): the sibling's
#   pre-change rival branches on membership in the discovered-source family alone
#   instead of the union. Carries across exactly, expressed here by handing the
#   model an empty automatic family. Its refinement argument is unchanged — the
#   three requested names are provided automatically and have no backing source
#   file, so the rival drops all three and the asserted entry sequence never
#   appears — and it is now additionally backed by a machine-checked witness.
# PORTED (partial-domain-drop-first -> weak-drop-first-requested): the sibling
#   stops its backward scan one step early so the FIRST listed name is never
#   classified. Here the same behaviour is `requested.drop 1`, refuted against
#   C1's whole-sequence pin plus the two universally-quantified retention
#   clauses. Same refinement argument (a leading retained name is dropped).
# PORTED (pos-control-local-reshape -> pos-control-loop-body-reshape): the
#   sibling hoists the pure classification into a boolean local and builds the
#   prepend through a typed local, keeping the front-prepend shape. That reshape
#   transliterates line for line, and the frozen proof script still discharges.
#   Two further positives were ADDED because on a tactic-proof backend a
#   soundness positive is only as strong as the shape it exercises: the sibling's
#   single control keeps the loop, so it could not detect a spec over-fit to the
#   loop itself. pos-control-direct-model removes the loop entirely and
#   pos-control-forward-filter reverses the traversal direction (paying for a real
#   induction bridge to the front-recursive model). pos-control-direct-model is
#   additionally the battery's `witness_reference` — see the CARRIER NOTE.
# RE-AIMED (admiss-gold-shape -> admiss-nondegenerate): the sibling witnesses
#   that `Acc(list_pred(.),1/2)` on all three inputs admits a normal F2P-shaped
#   input and that every read in the loop frames. This method has NO `require`
#   and there is no permission surface, so the precondition cannot exclude
#   anything and that probe could not fail — an admissibility case that cannot
#   fail is decoration. Re-aimed to the sharper residual risk, a DEGENERATE
#   post-image, via a live in-region assert at F2P-shaped inputs. Live, not
#   decoration: negating one conjunct leaves ``Tactic `decide` proved that the
#   proposition ... is false`` (measured, exit 1).
# ADDED, and why each closes a hole the ported set leaves open. The three ported
#   rivals all attack the RETENTION side (a name that should be kept is dropped),
#   so as ported the battery would have said nothing about three independent
#   things:
#   (1) weak-auto-family-only — the DUAL of the bug. The bundle's whole subject is
#       one family, so a battery built only from the change's own sub-domain
#       leaves the OTHER membership binder untested: a rival that consults only
#       the automatic family gets the headline behaviour exactly right. Its
#       witness sits at the exact dual point (`sourceDocs` non-empty, the
#       requested name absent from `autoTargets`), which is what demonstrates that
#       neither family is masking the other. This is the failure mode the port
#       brief names — a binder every witness holds at one value is a binder no
#       rival was built to abuse.
#   (2) weak-reversed-order — ORDER. The other five rivals all diverge on WHICH
#       names are emitted, so C1's order content was attacked by nothing. This
#       rival retains exactly the right set and satisfies C2, C3 and C4 (measured:
#       the residual goal is C1's equality alone), so only the permutation
#       distinguishes it. It is also the only rival that would survive a spec
#       stating membership without sequence equality.
#   (3) weak-retain-everything and weak-append-auto-family — the NO-INVENTION
#       direction (C2), which no retention-side rival can reach, split across its
#       two independent conjuncts: the first emits a name that does not EXIST
#       (`targetExists`), the second emits names that were never REQUESTED
#       (`e ∈ requested`) while every name it emits does exist. Both are plausible
#       over-fixes that satisfy the reported symptom, which is what makes them
#       worth attacking rather than strawmen.
# VACUOUS (frame-mutation-write-entries) — MEASURED, not asserted. The sibling's
#   MANDATORY frame rival writes into a read-only half-permission input
#   (`entries[i-1] = x`) and is rejected for INSUFFICIENT PERMISSION. This backend
#   is referentially transparent: all three inputs are immutable values declared
#   read-only (none is `mut`; only the loop-locals `out`/`i` are), there is no
#   heap, no aliasing, no `Old`, and no permission system. There is no read-only
#   input to overwrite and no frame clause to violate. The nearest expressible
#   analogue — assigning to a read-only parameter, `requested := []` inside the
#   impl region — was actually BUILT, and the carrier refuses it at ELABORATION
#   rather than at the postcondition: "`requested` cannot be mutated, only
#   variables declared using `let mut` can be mutated" (exit 1). So a ported frame
#   rival would "reject" for a binder/parse reason with no spec content whatever,
#   and there would be nothing for a witness to state. NOT ported; fabricating a
#   substitute would test nothing.
# DROPPED (AXIOM_TESTS, 2): the sibling's axiom-soundness / containment probes for
#   its deep model `kept` belong to the G-AX lane (axiom_check.py — here there is
#   no consumed axiom at all; the one grounded R-binding is in mapping.md §3), and
#   the G-PBT gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
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
# CLAUSE / BINDER / POINT COVERAGE (the part the gate does not check).
# All FOUR independent `ensures` clauses are DEFENDED (every positive and the
# admissibility case discharges all four) and all four are ATTACKED:
#   C1 out = retainedEntries ...      : all six rivals; ALONE by weak-reversed-order
#   C2 no invention (two conjuncts)   : weak-retain-everything (`targetExists`
#                                       conjunct), weak-append-auto-family
#                                       (`e ∈ requested` conjunct)
#   C3 automatic family retained      : weak-source-family-only,
#                                       weak-drop-first-requested
#   C4 either family retained         : weak-source-family-only,
#                                       weak-auto-family-only,
#                                       weak-drop-first-requested
# The three binders are moved across SIX distinct input triples (pts = 6):
#   weak-source-family-only    requested [t1]     sourceDocs []       autoTargets [t1]
#   weak-auto-family-only      requested [s1]     sourceDocs [s1]     autoTargets [t1]
#   weak-drop-first-requested  requested [t1,t2]  sourceDocs []       autoTargets [t1,t2]
#   weak-reversed-order        requested [t1,t2]  sourceDocs [t1,t2]  autoTargets []
#   weak-retain-everything     requested [t1,x9]  sourceDocs []       autoTargets [t1]
#   weak-append-auto-family    requested [s1]     sourceDocs [s1]     autoTargets [t1,t2]
# So `requested` ranges over length 1 and 2 and over names drawn from each family
# and from NEITHER; `sourceDocs` ranges over empty and non-empty, and is the SOLE
# retention channel at weak-reversed-order's point; `autoTargets` ranges over
# empty, one and two names, and is the SOLE retention channel at
# weak-source-family-only's and weak-drop-first-requested's points. No binder is
# pinned at a single value across the reject set, and neither membership family is
# held constant while the other varies — which is exactly the masking failure the
# port brief warns about (a spec whose two toggles are only ever probed together).
# MEANINGFULNESS, not just distinctness: at each of the six points the reference
# impl's own output differs from the rival's, computed value for value —
# [t1] vs []; [s1] vs []; [t1,t2] vs [t2]; [t1,t2] vs [t2,t1]; [t1] vs [t1,x9];
# [s1] vs [s1,t1,t2]. No two points are two spellings of the same discrimination:
# they split by which family drives retention, by position, by ORDER alone, by
# emitting a name that does not exist, and by emitting one that was not requested.
#
# WITNESS MECHANICS, measured with scripts/lean_verify.sh. All six witnesses:
# ELABORATE against their rival (exit 0); are refuted SEMANTICALLY against
# `_REFERENCE` (exit 1, ``Tactic `decide` proved that the proposition ... is
# false``); and are STUCK against the frozen `while`-loop tester (exit 1, "did not
# reduce to `isTrue` or `isFalse`") — which is why every case names a
# `witness_reference` and the recorded `witness_subject` reads "the reference
# impl". No witness binds a hypothesis, so no consistency probe applies and none
# can be vacuous through an inconsistent binder.
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for pydata__xarray-4094 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct toComponents`` tactic body,
is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds by construction and the ``prove_correct
toComponents`` obligation survives with a byte-identical header) and swaps in a
candidate implementation. Each is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method):

  toComponents (selDim : String) (sampleCoords : List String)
               (vars : List String) return (out : List (String × List String))
    require selDim ∉ sampleCoords
    ensures out = expectedComponents sampleCoords vars      -- (C1) whole pin
    ensures out.map Prod.fst = vars                         -- (C2) key set/order
    ensures ∀ p ∈ out, selDim ∉ p.2                         -- (C3) no transient

The method reassembles a combined array into its labeled components. ``vars``
are the component labels to extract in order; ``sampleCoords`` are the
coordinate names every component shares; ``selDim`` is the transient selector
label used to address each component. Each component is abstracted to the SET OF
COORDINATE NAMES it carries (mapping.md §2), which is precisely the observable
this change moves. ``sliceCoords selDim sampleCoords keep`` is the coordinate-
name set one extracted component carries (``keep = false`` discards the
transient selector label, ``keep = true`` retains it as a residual scalar
coordinate); ``expectedComponents sampleCoords vars`` is the front-recursive
correct answer, each label paired with exactly the shared sample coordinates.

BOTH are TRANSPARENT ``def``s over the method's own inputs — the ``axioms``
region declares nothing (``sliceCoords`` is an A-reference deep model, validated
against the real extractor by axiom_check.py, NOT a consumed axiom). So the
carrier is fully computable, there is no opaque answer-key oracle in any clause,
and no witness here needs to CONDITION on the carrier: every refutation is
stated at concrete literal inputs and every witness binds nothing, so no
consistency probe applies.

WHICH CLAUSE CONSTRAINS WHAT. C1 is the strongest clause and subsumes C2 and C3
logically; the battery nevertheless separates them, because each states an
INDEPENDENT top-level fact a rival can break on its own and the coverage
invariant is per-clause:
  * C1 pins the whole result — the label of each component, its position, and
    the coordinate-name set it carries — at every index.
  * C2 pins the key sequence: the reassembly neither drops, duplicates, nor
    reorders a label. All three directions are demonstrated by their own rival:
    ``weak-drop-last-component`` (drops), ``weak-spurious-extra-component``
    (surplus), ``weak-reorder-components`` (reorders) and
    ``weak-duplicate-first-label`` (duplicates). The last two were added by the
    audit lane: the claim that C2 forbids reordering and duplication was made
    here before any case exhibited either, and a clause direction no rival
    probes is a claim the manifest does not demonstrate.
  * C3 is the decisive strengthening for THIS change: no component may carry the
    transient selector label. This is what makes the reassembled collection
    conflict-free — two components carrying that same coordinate name would
    carry conflicting values for it and could not be combined.

C3 is what the sibling battery's load-bearing capability token buys, obtained
here without a token. On the sibling carrier the per-component VALUES are
identical whether the transient label was discarded or not (the failure is
"raises vs returns", not "wrong value"), so no value-level clause could separate
the two and an abstract unforgeable predicate was needed. This bundle abstracts
each component to its coordinate-name SET instead, which makes the difference a
plain VALUE difference: retaining the label puts ``selDim`` into ``p.2``, which
C3 forbids outright and C1 pins away. So the token machinery has no counterpart
here and needs none — see the accounting footer.

ADVERSARIAL READ of the sibling classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling declares its two probes
    of this class MANDATORY because both of its inputs are held at a fractional
    heap permission that an impl cannot legally write, and the rejection comes
    from the permission system. Lean and Velvet are referentially transparent:
    ``selDim``, ``sampleCoords`` and ``vars`` are immutable values, this method
    declares NO ``mut`` parameter, and there is no heap, aliasing, or permission
    to subvert. There is no read-only input an impl could overwrite, so the
    class is genuinely vacuous and no substitute probe is fabricated.
  * CAPABILITY-TOKEN BYPASS / LAUNDERING — no counterpart; the distinction it
    existed to draw is a value difference here (see above). Not a dropped case:
    the attack it encodes — build the right per-component values but skip the
    step that makes them conflict-free — IS ported, as ``weak-keep-selector``,
    where it is refuted by C1/C3 directly rather than by an unforgeable token.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. Ported in full: the
    wrong-flag rival, a sub-domain rival right on some shapes and wrong on
    others, the wrong-argument rival, the dropped-component rival, and the empty
    rival.
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

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``toComponentsTester <selDim> <sampleCoords> <vars> = false`` says the extracted
program's returned value violates the method's postcondition at that concrete
input. It is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict. The precondition and all three
postcondition clauses are decidable over ``String`` / ``List String``, so the
tester ``decide``s at literal inputs. No ``sorry`` / ``admit`` /
``native_decide`` / ``axiom`` / ``opaque``.

Every rival is written LOOP-FREE (a ``vars.map``, or a ``.dropLast``/``++`` of
one) so its extracted ``toComponentsExec`` REDUCES fully under ``decide``.

GOLD CANNOT SERVE AS THE DISCRIMINATING SUBJECT HERE, and the record says so
(``meta.json`` stamps every reject case ``witness_subject: "a verifying positive
from this battery (gold cannot decide)"``). Gold's body is the backward ``while``
fold, whose ``…Exec`` elaborates through machinery the kernel does not reduce; a
``decide`` against it gets STUCK rather than deciding. Measured, for all nine
reject witnesses: the gold-side build fails with ``Tactic `decide` failed …
did not reduce to `isTrue` or `isFalse` … reduction got stuck at the `Decidable`
instance``. That is a REDUCIBILITY failure, not a refutation, and on its own it
would attribute nothing — it is exactly the ``_STUCK_REDUCTION`` trap the gate
screens for, and the gate does detect it here and falls back.

So what actually discriminates these witnesses is the battery's own CORRECT
loop-free positive, ``pos-map-direct`` (``return vars.map (fun k => (k,
sliceCoords selDim sampleCoords false))``), which verifies and whose extracted
program reduces. Against it each witness fails with ``decide`` PROVING the tester
``= true`` — a semantic refutation of the concrete claim: the postcondition
genuinely HOLDS at the probed input for a correct impl, and genuinely FAILS there
for the rival. That, not the gold-side stuck build, is the evidence each reject
case rests on. It also confirms the precondition is satisfiable at every probed
input (a failed ``require`` would make the tester ``true`` vacuously for the
rival too, and the rival build would not have elaborated).

THIS PLACES A LOAD-BEARING CONSTRAINT ON THE POSITIVE LANE that is easy to break
by accident: the gate tries only the first ``_MAX_FALLBACKS`` (3) ``expect=
"verify"`` sources in MANIFEST ORDER as substitute subjects, and both
``pos-index-local`` and ``pos-coords-local`` keep gold's ``while`` loop, so both
are ALSO stuck (verified: the ``weak-keep-selector`` witness against
``pos-index-local`` fails with the same ``did not reduce to `isTrue` or
`isFalse```). ``pos-map-direct`` is the third entry and the only subject in this
battery that can decide anything. Reordering the positives so that
``pos-map-direct`` falls past the third slot, or replacing it with another
looping impl, would silently turn EVERY reject case into ``witness-undecided``
and the battery into MALFORMED-TESTS. Keep ``pos-map-direct`` inside the first
three positives; do not reorder this lane casually.

Every case's three builds (rival: elaborates, exit 0; gold: fails by stuck
reduction, exit 1; correct-loop-free ``pos-map-direct``: fails by refutation with
the tester proved ``= true``, exit 1) were run with ``scripts/lean_verify.sh``,
originally out-of-band and re-run independently by the audit lane.

INPUT-BINDER COVERAGE (what the reject witnesses vary, so no binder is pinned):
  * ``selDim``:       "y", "sel", "z", "lvl", "dim0", and — in
                      ``weak-strip-wrong-label`` — a rival that ignores it
                      entirely in favour of the component's own label;
  * ``sampleCoords``: ``["x"]`` (the single-shared-coordinate shape the issue
                      reports), ``["x", "t"]``, ``["u", "v", "w"]``;
  * ``vars``:         one label ``["a"]``, two ``["a", "b"]`` / ``["p", "q"]``,
                      three ``["a", "b", "c"]``.
``weak-partial-single-sampledim`` is refuted at ``sampleCoords = ["x"]`` and
AGREES with the spec at ``sampleCoords = ["x", "t"]`` (checked: the tester
proves ``= true`` there), so it is a genuine sub-domain break and the
``sampleCoords`` binder is demonstrably load-bearing rather than incidentally
varied.

AXIOM lane: dropped. ``AXIOM_TESTS`` is not defined. The sibling carries
axiom-soundness / containment probes over the real unchanged callees; that is
G-AX's job (axiom_check.py / mapping.md §3) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no axiom at all.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4094"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen executable body (the backward
# ---- `while` fold that prepends one component per step), i.e. everything
# ---- strictly between the method's `-- impl-start` / `-- impl-end`. Every
# ---- variant replaces exactly this text, so each edit lies wholly inside the
# ---- single impl region and same_spec holds by construction (uniqueness and
# ---- presence both asserted at load by _swap).
_IMPL = (
    "    let mut result : List (String × List String) := []\n"
    "    let mut i := vars.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ vars.length\n"
    "      invariant result = expectedComponents sampleCoords (vars.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let k := vars[i - 1]!\n"
    "      -- extract this component discarding the transient selector label "
    "(keep = false)\n"
    "      result := (k, sliceCoords selDim sampleCoords false) :: result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "frozen impl region drifted; update _IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a variant whose impl no longer needs the
# ---- backward-fold step lemma (or which adds an in-region `assert`) may retune
# ---- THIS block without touching the spec statement or dropping the
# ---- obligation. The `prove_correct toComponents` header always survives.
_PROOF = (
    "prove_correct toComponents by\n"
    "  loom_solve\n"
    "  rw [expectedComponents_drop_step sampleCoords vars i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "frozen proof body drifted; update _PROOF"

# The residual goal of a loop-free body needs no fold step lemma.
_PROOF_BARE = "prove_correct toComponents by\n  loom_solve"

# ...unless the loop-free body is a `vars.map`, whose agreement with the
# front-recursive `expectedComponents` is a one-line list induction.
_PROOF_MAP = (
    "prove_correct toComponents by\n"
    "  loom_solve <;>\n"
    "    induction vars with\n"
    "    | nil => rfl\n"
    "    | cons k ks ih => simp_all [expectedComponents]"
)


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body, proof):
    """Impl body replaced AND the (elided) proof body retuned."""
    return _swap(_impl(body), _PROOF, proof)


def _loopfree(expr, proof=_PROOF_BARE):
    """A loop-free rival body: report `expr` directly.

    Loop-freeness is what makes the rival's extracted `toComponentsExec` reduce
    under `decide`, so its witness can be stated on the executable program. The
    corresponding proof needs no fold step lemma.
    """
    return _impl_reproved(f"    return ({expr})", proof)


# ---- witness preamble + builder. Reaches the method CONTRACT through Velvet's
# ---- tester machinery, in a file whose `prove_correct` block is stripped so no
# ---- tactic script can mask the verdict. The precondition and all three
# ---- ensures clauses are decidable over String / List String, so the tester
# ---- decides at literal inputs. Binds nothing => no consistency probe needed.
_TESTER = ("extract_program_for toComponents\n"
           "prove_precondition_decidable_for toComponents\n"
           "prove_postcondition_decidable_for toComponents\n"
           "derive_tester_for toComponents\n\n")


def _witness(sel_dim, sample_coords, vars_):
    return (_TESTER +
            f"example : toComponentsTester {sel_dim} {sample_coords} {vars_}"
            " = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the gold code form). Each keeps the
    # `prove_correct toComponents` obligation with its byte-identical header;
    # only the executable surface and the elided tactic body move.
    # =====================================================================
    {
        "id": "pos-index-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist the step's index arithmetic into an explicit local
        # `idx` instead of computing it inline at the read. Same backward build,
        # same direction, every invariant kept verbatim — so the frozen proof
        # (including the backward-fold step lemma) closes unchanged. Deliberately
        # avoids flipping the loop direction, which would need a whole new
        # induction rather than testing the spec.
        "module": _impl(
            "    let mut result : List (String × List String) := []\n"
            "    let mut i := vars.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ vars.length\n"
            "      invariant result = expectedComponents sampleCoords "
            "(vars.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let idx := i - 1\n"
            "      let k := vars[idx]!\n"
            "      result := (k, sliceCoords selDim sampleCoords false) :: result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "a behaviourally-identical reshape (hoist the step index "
                     "into a local) keeps the same backward build and every "
                     "invariant, so C1/C2/C3 discharge exactly as before and the "
                     "frozen tactic script closes the byte-identical obligation. "
                     "Ports the sibling's pos-local-reshape. MUST verify, else "
                     "SPEC-TOO-STRONG (over-fit to the inline-index code form).",
    },
    {
        "id": "pos-coords-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: materialise the per-component coordinate-name set in a local
        # before pairing it with the label, instead of inlining the extraction
        # into the pair. Identical value flow (`coords` is the same set), so C1
        # still discharges and the frozen loop proof closes as-is. Ports the
        # sibling's pos-singleton-local (materialise the step's value in a typed
        # local before building the accumulator entry).
        "module": _impl(
            "    let mut result : List (String × List String) := []\n"
            "    let mut i := vars.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ vars.length\n"
            "      invariant result = expectedComponents sampleCoords "
            "(vars.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let k := vars[i - 1]!\n"
            "      let coords : List String := sliceCoords selDim sampleCoords false\n"
            "      result := (k, coords) :: result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "materialising the per-component coordinate-name set in a "
                     "typed local before pairing it with the label is "
                     "behaviourally identical (the same set is paired), so all "
                     "three clauses still discharge and the frozen proof closes. "
                     "Ports the sibling's pos-singleton-local. MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-map-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and report the whole result as a single
        # traversal, pairing each label with the coordinate-name set its
        # component carries. The residual goal is the agreement between the
        # traversal and the front-recursive answer, a one-line list induction, so
        # the (elided) proof body is retuned; the obligation header is untouched.
        #
        # This case doubles as the CONTROL for every witness below: it is CORRECT
        # and loop-free, so its extracted program reduces under `decide` exactly
        # as each rival's does. Every witness was checked to FAIL against it with
        # `decide` proving the tester `= true` — which is what shows the witnesses
        # discriminate on semantics rather than on gold's loop being opaque to
        # reduction.
        "module": _loopfree(
            "vars.map (fun k => (k, sliceCoords selDim sampleCoords false))",
            _PROOF_MAP),
        "rationale": "a CORRECT impl with a completely different control shape "
                     "(one traversal, no loop) pairing each label with the "
                     "coordinate-name set its component carries once the "
                     "transient selector label is discarded. It agrees with the "
                     "front-recursive post-image pointwise, so C1 discharges by "
                     "list induction and C2/C3 follow. MUST verify, else "
                     "SPEC-TOO-STRONG (over-fit to the backward-fold shape). Also "
                     "the reducibility control for the reject witnesses: being "
                     "loop-free AND correct, it is the impl against which each "
                     "witness must FAIL for a SEMANTIC reason.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The sibling's admiss-precond-holds asserts, in
    # region, that the precondition (its cardinality facts, distinctness, and the
    # half-permission list predicates) is establishable for a normal F2P-shaped
    # input. Two of its three ingredients have no counterpart here: there are no
    # permissions, and no cardinality relation is required. The residual
    # `require selDim ∉ sampleCoords` is trivially satisfiable, so the classic
    # probe would say almost nothing on its own. Re-aimed at the residual
    # admissibility risk: that the three-clause post-image is jointly satisfiable
    # AND NON-DEGENERATE at the exact shape the issue reports (one shared sample
    # coordinate, two components) — i.e. the correct answer there really is each
    # label paired with just that coordinate, and the transient selector label
    # really is absent from an extracted component. The gold body is kept
    # verbatim below the assert so the method's own three ensures still
    # discharge; the elided proof body is retuned to also close the concrete
    # assert. Checked out-of-band that a FALSE claim about the same point leaves
    # an unsolved goal, so the assert has teeth.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-issue-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (expectedComponents [\"x\"] [\"a\", \"b\"]\n"
            "         = [(\"a\", [\"x\"]), (\"b\", [\"x\"])] ∧\n"
            "       sliceCoords \"y\" [\"x\"] false = [\"x\"] ∧\n"
            "       \"y\" ∉ sliceCoords \"y\" [\"x\"] false))\n" + _IMPL,
            "prove_correct toComponents by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (rw [expectedComponents_drop_step sampleCoords vars i "
            "(by omega) (by omega)]; simp_all)\n"
            "    | decide\n"
            "    | simp_all"),
        "rationale": "the three-clause post-image is jointly satisfiable AND "
                     "non-degenerate at the shape the report describes (a single "
                     "shared sample coordinate, two components): the correct "
                     "answer pairs each label with exactly that one coordinate, "
                     "and the transient selector label is genuinely absent from an "
                     "extracted component's coordinate-name set — so C3 is a real "
                     "constraint there rather than vacuously true. The in-region "
                     "assert must discharge (a false claim about the same point "
                     "leaves an unsolved goal) and the gold body is kept verbatim "
                     "so the method's own C1/C2/C3 still discharge too. Re-aimed "
                     "from the sibling's admiss-precond-holds, whose permission "
                     "and cardinality halves have no counterpart on this carrier. "
                     "Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input plus the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Every rival is loop-free so
    # its extracted program reduces; every witness was checked to fail against
    # the CORRECT loop-free `pos-map-direct` impl too, so no rejection rides on
    # reducibility. The witnesses vary all three binders (see the header's
    # binder-coverage note).
    # =====================================================================
    {
        "id": "weak-keep-selector",
        "kind": "uniqueness",
        "expect": "reject",
        # THE load-bearing rival and the pre-change behaviour: extract each
        # component WITHOUT discarding the transient selector label, so the label
        # rides along on every component as a residual coordinate. The label set
        # (C2) is perfectly correct and the cardinality is right — only the
        # coordinate-name sets are wrong, which is exactly the observable this
        # change moves.
        "module": _loopfree(
            "vars.map (fun k => (k, sliceCoords selDim sampleCoords true))"),
        "refinement": "this IS the pre-change behaviour. Extracting a component "
                      "by addressing it via the transient selector label, without "
                      "discarding that label, leaves it behind on the component as "
                      "a residual scalar coordinate; when the components share "
                      "only their sample coordinates, nothing downstream removes "
                      "that residual coordinate. Every component then carries the "
                      "same coordinate name with a DIFFERENT value, so combining "
                      "them into one collection is a conflict and raises rather "
                      "than returning — which is precisely the failure the test "
                      "reports (a roundtrip that must reassemble successfully and "
                      "compare identical to the original). It would NOT resolve; "
                      "it is the defect.",
        "rationale": "REJECT from C3 (`∀ p ∈ out, selDim ∉ p.2`) and from C1: "
                     "retaining the transient label puts `selDim` into every "
                     "component's coordinate-name set, which C3 forbids outright, "
                     "and C1 pins each set to exactly `sampleCoords`. C2 is kept "
                     "correct (the right labels in the right order), so the "
                     "rejection is attributable to the coordinate-set clauses "
                     "alone. Refuted at selDim = \"y\", sampleCoords = [\"x\"], "
                     "vars = [\"a\", \"b\"] — the shape the report describes. "
                     "Ports the sibling's atk-discard-false (its single-knob "
                     "wrong-flag rival) and, as the same value attack, the "
                     "substance of its token-bypass case: build the right "
                     "per-component values but skip what makes them "
                     "conflict-free. If it verified => SPEC-TOO-WEAK (the spec "
                     "admits the bug).",
        "witness": _witness('"y"', '["x"]', '["a", "b"]'),
    },
    {
        "id": "weak-partial-single-sampledim",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, the near-miss: discard the transient selector label
        # only when there are at least two shared sample coordinates, and retain
        # it when there is exactly one. Agrees with the correct answer on every
        # multi-coordinate shape — including the pre-existing multi-dimensional
        # case — and is wrong exactly on the single-shared-coordinate shape the
        # report is about. Given its own witness (NOT shared with
        # weak-keep-selector) at the sub-domain where it goes wrong, since it
        # agrees with the spec over strictly more of the domain.
        "module": _loopfree(
            "vars.map (fun k => (k, sliceCoords selDim sampleCoords "
            "(sampleCoords.length < 2)))"),
        "refinement": "a counterpart that only discards the transient selector "
                      "label when the components share two or more coordinates "
                      "reproduces the correct behaviour on the multi-coordinate "
                      "shapes that already worked, and reproduces the DEFECT on "
                      "the single-shared-coordinate shape. The failing test opens "
                      "with exactly that shape — components sharing one "
                      "coordinate, reassembled and compared identical to the "
                      "original — so the conflict still occurs there and it would "
                      "NOT resolve. A genuine sub-domain break: right everywhere "
                      "the code was already right, wrong exactly where the report "
                      "says it is wrong.",
        "rationale": "REJECT from C3/C1 on the single-shared-coordinate "
                     "sub-domain: with `sampleCoords = [\"x\"]` this body retains "
                     "the transient label, putting `selDim` into every "
                     "component's coordinate-name set. Refuted at selDim = "
                     "\"y\", sampleCoords = [\"x\"], vars = [\"a\"] — a DISTINCT "
                     "point from weak-keep-selector (one component rather than "
                     "two), and checked to AGREE with the spec at sampleCoords = "
                     "[\"x\", \"t\"] (the tester proves `= true` there), so the "
                     "sub-domain claim this rationale makes is demonstrated and "
                     "the `sampleCoords` binder is shown load-bearing. Ports the "
                     "sibling's partial-domain lane. If it verified => "
                     "SPEC-TOO-WEAK (domain-incomplete).",
        "witness": _witness('"y"', '["x"]', '["a"]'),
    },
    {
        "id": "weak-strip-wrong-label",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG ARGUMENT: retain a residual label, but the label retained is the
        # component's OWN label rather than the transient selector label. The
        # transient selector label is then genuinely absent from every component,
        # so C3 HOLDS — this rival is caught by C1 alone, which pins each
        # coordinate-name set to exactly `sampleCoords`. Ports the sibling's
        # atk-wrong-roundtrip-data (pass the wrong vector to the combining step).
        "module": _loopfree(
            "vars.map (fun k => (k, sliceCoords k sampleCoords true))"),
        "refinement": "a counterpart that discards the transient selector label "
                      "but leaves a different residual coordinate behind on each "
                      "component — one named after the component itself — gives "
                      "every component a coordinate the original did not have. "
                      "The failing test compares the reassembled collection "
                      "IDENTICAL to the original, which compares coordinates, so "
                      "the extra per-component coordinate makes them differ and "
                      "it would NOT resolve. (Distinct components carry distinct "
                      "extra names, so it does not even raise the conflict the "
                      "defect raises — it silently returns the wrong thing.)",
        "rationale": "REJECT from C1 (`out = expectedComponents sampleCoords "
                     "vars`), which pins every component's coordinate-name set to "
                     "exactly `sampleCoords`; appending any further name breaks "
                     "it. C3 HOLDS for this rival (the transient selector label "
                     "really is absent), and C2 holds too, so this case isolates "
                     "C1 as the clause doing the work — the wrong-argument attack "
                     "C3 alone cannot catch. Refuted at selDim = \"y\", "
                     "sampleCoords = [\"x\"], vars = [\"p\", \"q\"] — a distinct "
                     "label pair from every other witness. Ports the sibling's "
                     "atk-wrong-roundtrip-data. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness('"y"', '["x"]', '["p", "q"]'),
    },
    {
        "id": "weak-fabricate-empty-coords",
        "kind": "uniqueness",
        "expect": "reject",
        # FABRICATION: guarantee the transient label is absent by pairing every
        # label with NO coordinates at all. C2 is correct and C3 is trivially
        # satisfied — the cheapest way to satisfy C3 without doing the work —
        # so this is the case that shows C3 alone would be too weak and C1 is
        # load-bearing. Ports the sibling's
        # atk-fabricate-allequal-resid (satisfy the guard by feeding a
        # degenerate fabricated vector instead of the real one).
        "module": _loopfree(
            "vars.map (fun k => (k, ([] : List String)))"),
        "refinement": "a counterpart that returns each component stripped of all "
                      "its coordinates does satisfy the conflict-freeness the fix "
                      "is after — trivially, by discarding the shared sample "
                      "coordinates too. Reassembly would then succeed but produce "
                      "components that have lost the coordinates every one of "
                      "them is supposed to carry, so the identical-comparison in "
                      "the failing test fails and it would NOT resolve. No "
                      "faithful counterpart can invent this: the extraction "
                      "cannot drop the shared coordinates, only the transient "
                      "selector label.",
        "rationale": "REJECT from C1, which pins each component's coordinate-name "
                     "set to exactly `sampleCoords` — dropping them all breaks it. "
                     "C3 is trivially SATISFIED here (nothing is carried, so the "
                     "transient label certainly is not) and C2 is correct, which "
                     "is the point: this rival demonstrates that C3 alone would "
                     "be too weak and that C1 carries the positive content. "
                     "Refuted at selDim = \"sel\", sampleCoords = [\"x\", \"t\"] "
                     "(a TWO-coordinate shape, so the dropped content is "
                     "non-trivial), vars = [\"a\"]. Ports the sibling's "
                     "atk-fabricate-allequal-resid. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness('"sel"', '["x", "t"]', '["a"]'),
    },
    {
        "id": "weak-drop-last-component",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (missing element): extract every component but the last.
        # Each component that IS produced is perfectly correct — the coordinate
        # sets are right and C3 holds — so this rival isolates C2 (and the
        # cardinality half of C1). Ports the sibling's atk-drop-last-member.
        "module": _loopfree(
            "vars.dropLast.map (fun k => (k, sliceCoords selDim sampleCoords "
            "false))"),
        "refinement": "a counterpart that omits one component from the "
                      "reassembled collection yields a collection missing one of "
                      "its members. The failing test compares the reassembled "
                      "collection identical to the original, which has every "
                      "member, so a missing member makes them differ and it would "
                      "NOT resolve.",
        "rationale": "REJECT from C2 (`out.map Prod.fst = vars`): the produced "
                     "label sequence is `vars` minus its last entry. C1's "
                     "cardinality half fails for the same reason. C3 HOLDS and "
                     "every component that IS produced carries exactly the right "
                     "coordinate-name set, so this case isolates the key-sequence "
                     "clause — the clause no coordinate-set rival can exercise. "
                     "Refuted at selDim = \"z\", sampleCoords = [\"x\", \"t\"], "
                     "vars = [\"a\", \"b\"]. Ports the sibling's "
                     "atk-drop-last-member. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness('"z"', '["x", "t"]', '["a", "b"]'),
    },
    {
        "id": "weak-spurious-extra-component",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (extra element), the mirror of the dropped-component
        # rival: produce every correct component and then one more, keyed by the
        # transient selector label itself. C3 still HOLDS (the precondition
        # guarantees `selDim ∉ sampleCoords`, and the spurious entry carries only
        # `sampleCoords`), so again C2 and C1's cardinality do the work.
        "module": _loopfree(
            "vars.map (fun k => (k, sliceCoords selDim sampleCoords false)) "
            "++ [(selDim, sampleCoords)]"),
        "refinement": "a counterpart that adds a member the original never had — "
                      "one keyed by the transient selector label used to address "
                      "the components — produces a collection with an extra "
                      "member. The failing test compares the reassembled "
                      "collection identical to the original, which has exactly "
                      "the real members, so the extra one makes them differ and "
                      "it would NOT resolve. The transient label names the "
                      "addressing axis, not a member, so no faithful counterpart "
                      "produces it.",
        "rationale": "REJECT from C2 (`out.map Prod.fst = vars`): the produced "
                     "label sequence is `vars` with an extra `selDim` appended. "
                     "C1 fails for the same reason. C3 HOLDS — the precondition "
                     "gives `selDim ∉ sampleCoords` and the spurious entry "
                     "carries only `sampleCoords` — so, like the "
                     "dropped-component rival, this isolates the key-sequence "
                     "clause, from the OPPOSITE side (surplus rather than "
                     "deficit). Refuted at selDim = \"lvl\", sampleCoords = "
                     "[\"x\", \"t\"], vars = [\"a\", \"b\"]. Added (no direct "
                     "sibling counterpart) to attack C2 in both directions. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness('"lvl"', '["x", "t"]', '["a", "b"]'),
    },
    {
        "id": "weak-reorder-components",
        "kind": "uniqueness",
        "expect": "reject",
        # PERMUTATION: extract every component correctly, with exactly the right
        # coordinate-name set, but emit them in the opposite order. The label
        # MULTISET is right and the cardinality is right, so this is the C2
        # direction neither the dropped- nor the spurious-component rival
        # reaches: both of those change how MANY labels come back, and a spec
        # that only pinned the label multiset would admit this one. C3 HOLDS.
        # Added by the audit lane (attack D): the header claimed C2 forbids
        # reordering and no case demonstrated it.
        "module": _loopfree(
            "vars.reverse.map (fun k => (k, sliceCoords selDim sampleCoords "
            "false))"),
        "refinement": "a counterpart that recovers every component but keys "
                      "them in reverse order builds a collection whose members "
                      "are paired with the wrong labels: the component "
                      "extracted for one label is filed under another. The "
                      "failing test compares the reassembled collection "
                      "IDENTICAL to the original, which compares each member "
                      "against the label it belongs to, so a transposed "
                      "labelling makes them differ and it would NOT resolve.",
        "rationale": "REJECT from C2 (`out.map Prod.fst = vars`), which pins "
                     "the key SEQUENCE and not merely the key multiset: the "
                     "produced sequence is `vars` reversed. C1 fails for the "
                     "same reason. C3 HOLDS and every component carries "
                     "exactly the right coordinate-name set, so this case "
                     "isolates the ORDER half of C2 — the direction the "
                     "dropped- and spurious-component rivals cannot reach, "
                     "since both of those change the label count. Refuted at "
                     "selDim = \"y\", sampleCoords = [\"x\"], vars = "
                     "[\"a\", \"b\"]. If it verified => SPEC-TOO-WEAK (the "
                     "spec would pin only the multiset of labels).",
        "witness": _witness('"y"', '["x"]', '["a", "b"]'),
    },
    {
        "id": "weak-duplicate-first-label",
        "kind": "uniqueness",
        "expect": "reject",
        # DUPLICATION: return the right NUMBER of components, each with the
        # right coordinate-name set, but key every one of them with the FIRST
        # label — so one label is duplicated and the rest are dropped. The
        # cardinality is right, which is what separates this from
        # weak-drop-last-component, and C3 holds. Added by the audit lane
        # (attack D): the header claimed C2 forbids duplication and no case
        # demonstrated it.
        "module": _loopfree(
            "vars.map (fun _ => (vars.headD \"\", sliceCoords selDim "
            "sampleCoords false))"),
        "refinement": "a counterpart that files every extracted component "
                      "under the same label produces a collection that has one "
                      "member repeated and the others missing entirely. The "
                      "failing test compares the reassembled collection "
                      "identical to the original, which has one member per "
                      "label, so it would NOT resolve. (Nothing in the "
                      "extraction can key a component by another component's "
                      "label, so no faithful counterpart produces this.)",
        "rationale": "REJECT from C2 (`out.map Prod.fst = vars`): the produced "
                     "sequence repeats the first label `vars.length` times "
                     "instead of listing each label once. C1 fails for the "
                     "same reason. The CARDINALITY is correct here — which is "
                     "what distinguishes this from weak-drop-last-component "
                     "and weak-spurious-extra-component, both of which break "
                     "the count — and C3 HOLDS, so this case isolates C2's "
                     "no-duplication content specifically. Refuted at selDim = "
                     "\"y\", sampleCoords = [\"x\", \"t\"], vars = "
                     "[\"a\", \"b\"]. If it verified => SPEC-TOO-WEAK (the "
                     "spec would pin only the length and coordinate sets).",
        "witness": _witness('"y"', '["x", "t"]', '["a", "b"]'),
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The cheap floor: reassemble nothing. Ports the sibling's atk-empty.
        "module": _loopfree("([] : List (String × List String))"),
        "refinement": "a counterpart that returns an empty collection recovers "
                      "none of the components. The failing test compares the "
                      "reassembled collection identical to the original, which "
                      "has members, so an empty result fails it — and it never "
                      "performs the reassembly whose conflict is the reported "
                      "defect, so it would NOT resolve.",
        "rationale": "REJECT from C2 (`out.map Prod.fst = vars`, and `vars` is "
                     "non-empty at the probed input) and from C1. C3 is "
                     "vacuously satisfied, which again shows C3 alone cannot "
                     "carry the spec. Refuted at selDim = \"dim0\", sampleCoords "
                     "= [\"u\", \"v\", \"w\"], vars = [\"a\", \"b\", \"c\"] — a "
                     "THREE-coordinate, three-component point no other witness "
                     "probes, so this cheap near-miss also widens all three "
                     "binders. Ports the sibling's atk-empty. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness('"dim0"', '["u", "v", "w"]', '["a", "b", "c"]'),
    },
]


# ---------------------------------------------------------------------------
# Sibling -> velvet accounting (which cases ported, which did not, and why).
#
# The sibling battery ships 11 SPEC cases (2 soundness, 1 admissibility, 8
# uniqueness) plus a 2-case AXIOM lane, over ONE modeled function whose two
# inputs are heap collections held at half permission, with four @ContractOnly
# callees and an abstract capability predicate. This bundle models the same
# operation over a purely-functional, fully-transparent carrier and ships 13
# SPEC cases (3 soundness, 1 admissibility, 9 uniqueness).
#
# (The counts above were wrong as first written — the footer said "10 SPEC cases
# (3 soundness, 1 admissibility, 6 uniqueness)" while the battery shipped 11
# cases with 7 uniqueness. Corrected by the audit lane, which also added the two
# C2-direction rivals below, bringing the totals to 13/9.)
#
# PORTED (the argument carried over, mechanics rewritten for this carrier):
#   pos-local-reshape            -> pos-index-local
#   pos-singleton-local          -> pos-coords-local
#   (added)                      -> pos-map-direct    (also the reducibility
#                                   control every reject witness is checked
#                                   against; see the header)
#   admiss-precond-holds         -> admiss-nondegenerate-issue-shape (RE-AIMED:
#                                   the permission and cardinality halves have
#                                   no counterpart; the non-degeneracy half is
#                                   what remains testable)
#   atk-discard-false            -> weak-keep-selector
#   atk-bypass-assemble          -> weak-keep-selector (SAME attack on this
#                                   carrier: "produce the right per-component
#                                   values but skip what makes them
#                                   conflict-free" IS the wrong-flag body here,
#                                   because the coordinate-name abstraction turns
#                                   the sibling's value-invisible control-flow
#                                   difference into a plain value difference. Not
#                                   dropped — merged, and refuted by C1/C3
#                                   directly rather than by an unforgeable token.)
#   atk-wrong-roundtrip-data     -> weak-strip-wrong-label
#   atk-fabricate-allequal-resid -> weak-fabricate-empty-coords
#   atk-drop-last-member         -> weak-drop-last-component
#   atk-empty                    -> weak-empty
#   (added)                      -> weak-partial-single-sampledim  (the near-miss
#                                   the sibling's single-knob rival cannot
#                                   express: correct on every shape that already
#                                   worked, wrong only on the reported one)
#   (added)                      -> weak-spurious-extra-component  (attacks the
#                                   key-sequence clause from the surplus side)
#   (added, audit lane)          -> weak-reorder-components  (C2's ORDER half:
#                                   right labels, right multiset, right
#                                   coordinate sets, wrong order — the direction
#                                   no count-changing rival reaches)
#   (added, audit lane)          -> weak-duplicate-first-label  (C2's
#                                   no-duplication half at the CORRECT
#                                   cardinality, which the drop/surplus rivals
#                                   cannot isolate)
#
# NOT PORTED, with the reason:
#   frame-mutate-data, frame-mutate-resid — VACUOUS on this carrier, not dropped
#     for difficulty. Both are rejected on the sibling by the PERMISSION SYSTEM:
#     the inputs are held at a fractional permission an impl may not write
#     through. This method takes three immutable values and declares no `mut`
#     parameter; Lean and Velvet are referentially transparent, with no heap, no
#     aliasing and no permissions. There is no read-only input an impl could
#     overwrite, so there is no rival to write and no substitute is fabricated.
#   atk-launder-fresh-copy — no counterpart. It attacks the sibling's abstract
#     capability token by obtaining it and then returning a value-equal FRESH
#     copy, which the token does not travel to. This spec has no token: the
#     conflict-freeness requirement is stated as a VALUE property of the returned
#     coordinate-name sets (C3), and a value-equal copy satisfies a value
#     property. So the laundering rival is not wrong on this carrier — it IS a
#     correct impl here — and per the porting rules it is dropped rather than
#     shipped with a witness that cannot exist. The distinction the token drew
#     (did the result actually pass through the combining step?) is not modeled
#     here and does not need to be: the observable the change moves is which
#     coordinate names each component carries, and that is pinned by C1/C3.
#     DEMONSTRATED by the audit lane rather than argued: the laundering shape
#     transliterated to this carrier — build the correct answer, then
#     re-materialise it element-wise (`(vars.map (fun k => (k, sliceCoords
#     selDim sampleCoords false))).map (fun p => (p.1, p.2))`) — was built
#     against the frozen spec and VERIFIES (exit 0). So it is provably a CORRECT
#     impl here, no witness against it can exist, and dropping it is right. It
#     is not shipped as a positive only because it is definitionally the
#     `pos-map-direct` body composed with an identity map, so it would test
#     nothing that case does not.
#   The DIVERGENCE lane: the sibling carries no such case, so nothing to port, and
#     the class is CLOSED BY THE SEMANTICS rather than a hole or a vacuous class.
#     An earlier revision of this line recorded it in the header as a KNOWN SPEC
#     HOLE on the ground that the bundle runs under `partial` semantics, which
#     admits a non-terminating rival. It does not: line 4 sets `"total"` and line 7
#     opens `TotalCorrectness`, as in all 500 velvet bundles, and under `total` a
#     diverging rival is REJECTED. See the DIVERGENCE bullet in the header for the
#     builds, including the shape that supplies a constant measure and is refused
#     on the descent goal itself.
#   AXIOM_TESTS (ax-sound-callees, ax-cover-assemble) — dropped by the porting
#     rules: the axiom lane is G-AX's job and G-PBT ignores AXIOM_TESTS. This
#     bundle consumes no axiom at all (the extraction is modeled deeply as the
#     A-reference `sliceCoords`), so there is nothing for a containment probe to
#     bound.
#
# No soundness positive was dropped for a proof that would not close: all three
# positives verify with the frozen tactic script (pos-index-local,
# pos-coords-local) or a one-line list induction (pos-map-direct), and the
# admissibility case's in-region assert discharges by `decide` while the frozen
# body's three clauses still discharge as before.
# ---------------------------------------------------------------------------

"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14710 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct prepareScorerTargets`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over an integer-code carrier,
``List Int``):

  prepareScorerTargets (isClf : Bool) (labels : List Int) (y : List Int)
      return (out : List Int)
    require ∀ i, i ∈ y → 0 ≤ i ∧ i.toNat < labels.length
    ensures isClf = true  → out = gather labels y      -- (P_dec)  DISCRIMINATOR
    ensures isClf = false → out = y                    -- (P_id)   PASSTHROUGH

The method prepares the target sequence handed to the evaluation scorer. The
targets arrive as integer codes. For a CLASSIFICATION task the codes index a
table ``labels`` of the original class values, and each code must be mapped back
through that table, in order, before scoring (``gather`` is the total,
count- and order-preserving per-code lookup ``y.map (labels[·.toNat]!)``, fully
unfolded in the ``pure`` region — the ``axioms`` region is empty, so there is no
opaque answer key to echo; directive 8). For a NON-classification task the
targets are already in final form and are passed through unchanged.

Two independent top-level clauses:
  * (P_dec) classifier leg — the codes are decoded THROUGH ``labels``; this is
    the behavioural delta the fix introduces (the pre-fix code forwards the raw
    integer codes, which the scorer then compares against original-domain
    predictions — the exact type mismatch the issue reports);
  * (P_id) non-classifier leg — the read-only target sequence is passed through
    with nothing added, dropped, reordered, or transformed.

THREE input binders, all free; the guarantee must hold for every value of each:
  * ``isClf`` — selects the leg (both legs pinned);
  * ``labels`` — the label table the classifier leg looks codes up in;
  * ``y`` — the integer codes / passthrough sequence (length, contents, order).
The ``require`` clause pins that every code is a valid index into ``labels``
(guaranteed by the real encoder); a witness input respects it or the tester
short-circuits to ``true`` (precondition-false vacuously satisfies the test).

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — the nagini sibling makes this class MANDATORY
    (``labels``/``target`` held at half permission, a write to the read-only
    input rejected for insufficient permission). Lean/Velvet are referentially
    transparent: every input is an immutable value, the method declares no
    ``mut`` binder, there is no heap and no aliasing, so there is no read-only
    cell to overwrite. VACUOUS here; no substitute probe is fabricated (per the
    porting map, this class is legitimately dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The classifier
    post-image is pinned to ``gather labels y`` — a concrete ``def`` over the
    method's own arguments (empty ``axioms`` region; no opaque callee). The only
    satisfier is the grounded lookup itself; there is nothing to echo.
  * CONTROL-FLOW / RAISE / SIDE-EFFECT — N/A, as the sibling records: the method
    is total over its precondition domain, always returns a ``List Int``, never
    raises, has no side effect. The returned value fully captures the behaviour.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each rival gets the SHAPE right
    (a ``List Int`` on the right leg) and is correct on part of the domain, but
    diverges on one clause / one sub-domain above.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is LOOP-FREE (a branch over a
single ``.map``), so its extracted tester reduces under ``decide``. Each reject
rival is likewise a loop-free expression, so its tester also ``decide``s. Each
reject rival therefore carries a machine-checked refutation ``witness`` — a
Velvet tester statement ``prepareScorerTargetsTester isClf labels y = false`` at
ONE concrete input, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
its rival (the tester ``decide``s to ``false`` — the rival's output violates the
postcondition there) and FAILS against the frozen solution (gold's tester
``decide``s to ``true``, so ``= false`` is refuted). Every witness input
satisfies the ``require`` clause (codes in range), so it is not vacuously
excluded. No witness binds any hypothesis (all inputs are concrete literals that
``decide`` computes), so there is no consistency obligation to discharge.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the whole computation is concrete list arithmetic over the inputs (``gather`` is
an ordinary total NumPy-fancy-index model, an I-op under the R bijection — see
mapping.md §3). Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14710"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (both markers live inside the elided impl region). Every
# rival and reshape edits ONLY this block (and, for reshapes/admissibility, the
# elided `prove_correct` tactic body), so the spec view is untouched and
# same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    if isClf then\n"
    "      return gather labels y\n"
    "    else\n"
    "      return y\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as `loom_solve`, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct prepareScorerTargets by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `prepareScorerTargetsTester isClf labels y = false` says the extracted
# ---- program's result violates the postcondition at that concrete input (the
# ---- tester short-circuits to `true` when the `require` clause is false, so
# ---- every witness below uses in-range codes that satisfy the precondition).
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict; both the rival and the frozen impl are
# ---- loop-free, so both testers reduce under `decide`.
def _witness(call):
    return ("extract_program_for prepareScorerTargets\n"
            "prove_precondition_decidable_for prepareScorerTargets\n"
            "prove_postcondition_decidable_for prepareScorerTargets\n"
            "derive_tester_for prepareScorerTargets\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. The classifier leg binds the
    # decoded sequence to a local before returning it. Observationally identical;
    # the frozen `loom_solve` still closes the byte-identical obligation.
    # Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-let-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- impl-start\n"
            "    if isClf then\n"
            "      let dec := gather labels y\n"
            "      return dec\n"
            "    else\n"
            "      return y\n"
            "    -- impl-end"),
        "rationale": "structurally different CORRECT impl: the classifier leg "
                     "binds the decoded sequence to a typed local `dec` and "
                     "returns it, rather than returning the expression inline. "
                     "Observationally identical on every input, so both "
                     "`out = gather labels y` and `out = y` hold on the whole "
                     "domain. A faithful reshape MUST verify, else the "
                     "postcondition is SPEC-TOO-STRONG (it would reject its own "
                     "model's output).",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — inline the deep model. Instead of calling
    # `gather`, the classifier leg spells out the same per-code map
    # `y.map (fun i => labels[i.toNat]!)` (definitionally equal to `gather`).
    # Different surface syntax, identical value; the frozen proof still closes.
    # Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-inline-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- impl-start\n"
            "    if isClf then\n"
            "      return y.map (fun i => labels[i.toNat]!)\n"
            "    else\n"
            "      return y\n"
            "    -- impl-end"),
        "rationale": "structurally different CORRECT impl: the classifier leg "
                     "inlines the per-code lookup `y.map (fun i => "
                     "labels[i.toNat]!)`, which is definitionally `gather labels "
                     "y`. Same value, different spelling; `out = gather labels y` "
                     "holds on the whole domain. Must verify, else the spec is "
                     "over-fit to the `gather`-application spelling => "
                     "SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe re-establishes that the
    # precondition admits a normal F2P-shaped input. Here the residual risk is
    # that the `require` (every code a valid index into `labels`) could be
    # unsatisfiable for a real label-encoded target; an in-region assert pins
    # that it IS satisfiable at a concrete F2P-shaped input (a 2-class table with
    # codes 0,0,1,1 — the shape of the issue's 50-'x'/50-'y' fixture). The impl
    # is kept verbatim so the method's own obligation still discharges; the proof
    # is left as `loom_solve` (it discharges the assert directly), which is
    # elided from the spec view. The assert is live (a false claim leaves an
    # unsolved goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-precond-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss\n"
            "      (∀ i ∈ ([0,0,1,1] : List Int), 0 ≤ i ∧ i.toNat < ([10,20] : List Int).length))\n"
            "    if isClf then\n"
            "      return gather labels y\n"
            "    else\n"
            "      return y\n"
            "    -- impl-end"),
        "rationale": "the `require` clause (every code a valid index into the "
                     "label table) ADMITS the F2P-shaped input: a 2-entry table "
                     "with codes [0,0,1,1] (the shape of the issue's balanced "
                     "two-class fixture) satisfies 0 ≤ code < labels.length for "
                     "every code. So the obligation is not vacuously unsatisfiable "
                     "(else PRECOND-TOO-STRONG). The in-region assert must "
                     "discharge; the impl is kept verbatim so the method's own "
                     "`ensures` discharges too. (A non-degeneracy assert on the "
                     "post-image value was dropped: the concrete `gather` term "
                     "triggers a whnf heartbeat timeout in this workspace — the "
                     "positives already exercise the full non-degenerate lookup.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a loop-free
    # expression so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-prepatch-undecoded",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug: the classifier leg forwards the RAW integer codes instead
        # of decoding them through `labels`. Correct shape (a List Int of the same
        # length) and correct non-classifier leg, but the classifier values are
        # the codes, not the looked-up labels.
        "module": _impl(
            "    -- impl-start\n"
            "    if isClf then\n"
            "      return y\n"
            "    else\n"
            "      return y\n"
            "    -- impl-end"),
        "refinement": "this IS the pre-fix behaviour: the classifier leg hands the "
                      "raw integer codes to the scorer instead of the codes "
                      "decoded through the label table. Its faithful real "
                      "counterpart is the unpatched target preparation, which "
                      "scores integer-coded targets against original-domain "
                      "predictions — exactly the type mismatch the issue reports. "
                      "The failing test would then raise on that comparison, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from (P_dec) `isClf = true → out = gather labels y`: "
                     "the rival returns `y`, but `gather labels y` looks each code "
                     "up in `labels`, so they disagree whenever `labels[code] != "
                     "code` (a decoded label differs from its integer position). "
                     "Verifying would be SPEC-TOO-WEAK (the decode is unpinned). "
                     "Refuted at isClf=true, labels=[10,20], y=[1]: gold decodes to "
                     "[20], the rival returns [1]. Discrimination comes from the "
                     "`labels` lookup being applied to `y`.",
        "witness": _witness("prepareScorerTargetsTester true [10,20] [1]"),
    },
    {
        "id": "weak-first-undecoded",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: decodes every code EXCEPT the first, which is forwarded
        # raw. Correct shape and correct on the whole domain EXCEPT the first
        # element (whenever labels[y[0]] != y[0]). Pins the clause on EVERY
        # element, not most.
        "module": _impl(
            "    -- impl-start\n"
            "    if isClf then\n"
            "      let dec := match y with\n"
            "        | [] => []\n"
            "        | y0 :: rest => y0 :: rest.map (fun i => labels[i.toNat]!)\n"
            "      return dec\n"
            "    else\n"
            "      return y\n"
            "    -- impl-end"),
        "refinement": "a partial-domain counterpart that decoded all but the first "
                      "sample of the target would leave that one sample's integer "
                      "code un-mapped while its prediction is an original-domain "
                      "label, so the score comparison again crosses domains on that "
                      "sample and the failing test does NOT resolve. Tests that the "
                      "decode clause pins EVERY element, not most. (The issue's "
                      "fixture's first sample is a real class label, so a "
                      "first-element divergence is observable.)",
        "rationale": "REJECT from (P_dec) at index 0: `gather labels y` decodes the "
                     "first code like the rest, but the rival forwards it raw, so "
                     "the lists disagree whenever `labels[y[0]] != y[0]`. Refuted "
                     "at isClf=true, labels=[5,7], y=[1,0]: gold decodes to [7,5], "
                     "the rival returns [1,5]. Discrimination comes from the FIRST "
                     "`y` element (a near-miss the whole-domain prepatch rival does "
                     "not subsume; this point moves labels and y, distinct from the "
                     "other witnesses).",
        "witness": _witness("prepareScorerTargetsTester true [5,7] [1,0]"),
    },
    {
        "id": "weak-regressor-decode",
        "kind": "uniqueness",
        "expect": "reject",
        # PASSTHROUGH-CLAUSE attack: the NON-classifier leg DECODES through
        # `labels` instead of passing the target through unchanged. Correct shape;
        # equal to gold only when labels[y[j]] == y[j] for every j.
        "module": _impl(
            "    -- impl-start\n"
            "    if isClf then\n"
            "      return gather labels y\n"
            "    else\n"
            "      return gather labels y\n"
            "    -- impl-end"),
        "refinement": "a counterpart that decoded on the non-classification leg "
                      "too would apply the label-table lookup where the task has no "
                      "such table (a regressor keeps its targets in final form), "
                      "corrupting the scored targets and failing the regression "
                      "early-stopping behaviour, so it would NOT resolve. Confirms "
                      "the spec pins BOTH legs — the decode AND the passthrough.",
        "rationale": "REJECT from (P_id) `isClf = false → out = y`: on the "
                     "non-classifier leg the rival returns `gather labels y`, which "
                     "differs from `y` whenever `labels[y[j]] != y[j]`, so the "
                     "identity guarantee fails. Verifying would be SPEC-TOO-WEAK "
                     "(the passthrough leg unpinned). Refuted at isClf=false, "
                     "labels=[3,9], y=[1]: gold passes through [1], the rival "
                     "returns [9]. Discrimination comes from the `isClf=false` leg "
                     "(the only rival that abuses it).",
        "witness": _witness("prepareScorerTargetsTester false [3,9] [1]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness/frame rivals) plus a 2-case AXIOM
# lane. The sibling contracts TWO byte-identical modeled functions
# (primary/secondary) over a PSeq[int] carrier with half-permission read-only
# inputs and a grounded `decode_one` oracle. THIS bundle narrows the carrier to
# ONE contracted method `prepareScorerTargets` over `List Int` — the sibling's
# `secondary` differs only by an unmodeled `use_secondary` guard and collapses
# onto the same purely-functional core (single-site vs two-site is not a
# behavioural distinction the modeled value surface can carry). `decode_one`
# becomes the fully-unfolded pure `gather`; there is no permission surface on
# this backend.
#
#   sibling case                    -> here                       disposition
#   --------------------------------------------------------------------------
#   pos-grounded-oracle-decode-one  -> pos-inline-map             PORTED (re-aimed)
#   pos-localvar-reshape            -> pos-let-local              PORTED
#   admiss-primary-selfcall         -> admiss-precond-f2p         PORTED (re-aimed)
#   prepatch-undecoded-index        -> weak-prepatch-undecoded    PORTED
#   partial-domain-first-undecoded  -> weak-first-undecoded       PORTED
#   passthrough-regressor-decode    -> weak-regressor-decode      PORTED
#   frame-mutate-target             -> (none)                     VACUOUS
#   AXIOM_TESTS (2)                 -> (none)                     DROPPED (G-AX)
#
# All THREE behavioural sibling rivals PORTED; both positive controls PORTED; the
# admissibility case PORTED (re-aimed). The mandatory frame-mutation rival is
# VACUOUS on this backend; the axiom lane is dropped.
#
# PORTED (positives): pos-localvar-reshape bound the decoded value to a typed
#   local `dec` before the append — here the classifier leg binds `dec = gather
#   labels y` and returns it (`pos-let-local`). pos-grounded-oracle-decode-one
#   appended `decode_one(labels, target[i])`, which unfolds to `labels[target[i]]`
#   — here the grounded oracle IS `gather`, so the re-aimed positive inlines the
#   definitionally-equal `y.map (fun i => labels[i.toNat]!)` (`pos-inline-map`).
#   Both keep the whole computation, so the frozen `loom_solve` closes the
#   byte-identical obligation (both verified out-of-band with real builds).
# PORTED-RE-AIMED (admissibility): the sibling probes the precondition at a real
#   call site via a self-call. This backend has no callee-under-spec self-call for
#   a single method and no permission surface; the re-aimed probe asserts the sole
#   `require` (codes valid indices into the label table) is SATISFIABLE at the
#   F2P-shaped input (2-class table, codes [0,0,1,1]) — the residual
#   PRECOND-TOO-STRONG risk. (A post-image non-degeneracy conjunct was attempted
#   but the concrete `gather` literal triggers a whnf heartbeat timeout in this
#   workspace; the two positives already return the full non-degenerate lookup, so
#   non-degeneracy is covered. Reported here rather than silently dropped.)
# PORTED (rivals): prepatch-undecoded -> weak-prepatch-undecoded (attacks P_dec on
#   the whole classifier domain), partial-first -> weak-first-undecoded (attacks
#   P_dec at index 0 only, the near-miss), passthrough-regressor-decode ->
#   weak-regressor-decode (attacks P_id, the passthrough leg). Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   gold (two real builds per case).
# VACUOUS (frame-mutate-target): the sibling makes this MANDATORY (`target` held
#   at half permission; a write to the read-only input is rejected for
#   insufficient permission). This backend is referentially transparent and
#   declares no `mut` binder — every input is an immutable value with no heap
#   footprint — so there is no read-only cell to overwrite and no substitute
#   probe. Not fabricated (porting map: vacuous here).
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (`gather` is an I-op — concrete NumPy
#   fancy-index arithmetic over the inputs, see mapping.md §3), so there is
#   nothing to probe and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 3 distinct input points):
#     isClf  — true, true, false: BOTH legs of the top-level branch attacked.
#     labels — [10,20], [5,7], [3,9]: table contents varied (each rival's lookup
#              yields a value distinct from the raw code, so the decode is probed).
#     y      — [1], [1,0], [1]: length and contents varied; the [1,0] point probes
#              the FIRST-element sub-domain the whole-domain rival does not.
#   Every top-level clause of the postcondition is attacked: (P_dec) by
#   weak-prepatch-undecoded and weak-first-undecoded, (P_id) by
#   weak-regressor-decode. No two rivals share an input tuple.
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for django__django-11603 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte — region surgery touches only text inside a
``-- impl-start`` / ``-- impl-end`` region (which the consumer spec view elides)
and, for three positives, the equally-elided ``prove_correct`` tactic body, so
``markers.same_spec`` holds and both ``prove_correct`` headers survive
byte-identically. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted methods, one binder each, no ``require``):

  avgInit (distinct : Bool) return (out : Except InitErr AggState)
    ensures out = construct "AVG" true distinct                         [A1]

  sumInit (distinct : Bool) return (out : Except InitErr AggState)
    ensures out = construct "SUM" true distinct                         [S1]

Each method constructs one kind of aggregate over a source expression, with an
optional request to aggregate over the set of DISTINCT input values. ``construct
function acceptsDistinct distinct`` is the shared construction guard, spelled out
in the frozen ``pure`` region: it refuses the construction when the option is
requested of a kind that does not accept it, and otherwise builds the aggregate
recording the request unchanged.

WHICH CLAUSE IS LOAD-BEARING, AND HOW IT IS GROUNDED. A1/S1 each pin the WHOLE
outcome to a transparent total ``def`` applied to the method's own binder, with
the capability argument fixed at ``true``. Two things follow, and both are what
the battery attacks:

  * the refusal branch of ``construct "AVG" true _`` is DEAD, so the outcome must
    be a successful construction for EVERY value of ``distinct``, including a
    request to aggregate over distinct values. This is the analogue of the nagini
    sibling's load-bearing clause (there: the ABSENCE of an ``Exsures`` on the two
    build_* functions, which forces a normal return even when the option is
    requested). Rivals that route the construction through a kind that does not
    accept the option, or that refuse whenever the option is requested, violate it.
  * the built aggregate's recorded flag must EQUAL the request, and its function
    name must be the method's own. Merely accepting the request is not enough —
    a downstream aggregation over distinct values depends on the flag being
    recorded faithfully. Rivals that drop, force or flip the recorded flag, or
    that record another kind's function name, violate it.

The post-image is GROUNDED in the binder (``construct`` is a plain ``def`` over
the method's own input, and the ``axioms`` region is EMPTY — mapping.md §3), so
there is no opaque answer-key for a wrong impl to echo. Every uniqueness rival
therefore diverges from the post-image at a CONCRETE ``Bool`` input, and its
witness refutes it there directly.

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` contract, not a bare
predicate, so each witness reaches it through Velvet's own tester machinery:
``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for``, then
``<method>Tester <distinct> = false`` — the extracted program's result violates
the postcondition at that input. The outcome carrier is ``Except InitErr
AggState``, whose ``DecidableEq`` the postcondition-decidability derivation
needs, so each witness first writes ``deriving instance DecidableEq for Except``
(an instance derivation, not an assumption: no ``sorry`` / ``admit`` / ``axiom``
/ ``native_decide`` / ``opaque`` anywhere). Measured: WITHOUT that line
``decide`` reports "reduction got stuck at the `Decidable` instance" on BOTH the
rival and the frozen build, i.e. an inconclusive witness rather than a
discriminating one; with it, every witness below reduces. Every input is a
concrete ``Bool`` literal, so no witness binds a hypothesis and the gate's
consistency probe is a no-op. All nine were checked out-of-band with two real
``scripts/lean_verify.sh`` builds each: rival ELABORATES (exit 0), frozen
solution FAILS (exit 1, ``decide`` proving the tester equation false). The audit
independently rebuilt all nine pairs and additionally ran the FORGERY test on
each — the witness with its claim FLIPPED (``= true`` for ``= false``) — getting
the exact inversion on every case: flipped-on-gold elaborates (exit 0), flipped-
on-rival fails (exit 1) with ``decide`` proving the flipped equation false. So
each gold-side exit code tracks the CLAIM rather than being a constant property
of the file, which is what makes these plain-evaluation signatures admissible.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS, and the nagini sibling already records
    it so (its DEFENDED SURFACE note: three functions over plain booleans, no
    heap, no read-only fractional-permission input). Lean and Velvet are
    referentially transparent: every input is an immutable value, there is no
    ``mut`` binder, no heap, no aliasing and no permission system. Nothing to
    overwrite; no substitute probe fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the nagini sibling
    notes: the post-image is a transparent ``def`` of the method's own binder,
    not an axiomatized answer-key. Replaced there and here by honest
    cheapest-impl positive controls, plus value-pin rivals on the recorded flag.
  * DIVERGENCE — CLOSED BY THE CARRIER, and defended by a positive rather than
    attacked by a rival. This bundle runs under ``set_option
    loom.semantics.termination "total"`` (Solution.lean line 4), so the verifier
    DISCHARGES a termination obligation: a loop carrying no decreasing measure is
    refused outright with ``error: Decreasing annotations are required in total
    correctness semantics``. Measured by the audit on this bundle: a spin-loop
    rival spliced before gold's correct tail FAILS to build (exit 1) with exactly
    that diagnostic. So a diverging impl does NOT verify here and there is no
    spec hole to record — the disposition the battery previously carried
    (``partial`` semantics, non-terminating impl verifies vacuously, KNOWN SPEC
    HOLE) described a bundle this is not, and is corrected below.

    It is also not shippable as a REJECT case, for a mechanical reason the audit
    measured rather than assumed. The termination error is raised by the ``method``
    elaboration itself, so it fires in the WITNESS file too — where the
    obligations are stripped — and the extracted tester of a looping impl never
    reduces: ``decide`` reports ``reduction got stuck at the `Decidable`
    instance`` on the rival side, which is the ``witness-unproven`` half the gate
    requires to SUCCEED. Both measured (rival witness exit 1, stuck reduction),
    with a bounded loop and with a spin loop. A reject case therefore cannot be
    landed, and the honest way to exercise the lane on this carrier is from the
    OTHER side: ``pos-avg-terminating-loop`` below is a correct impl whose loop
    DOES carry a decreasing measure, and it must verify. That pins the
    termination obligation as discharged-and-satisfiable rather than merely
    unmentioned. See the footer.

AXIOM lane: dropped, and empty on both sides. The nagini sibling already ships
``AXIOM_TESTS = []`` (nothing axiomatized: the construction guard is modeled
deeply), and this bundle is likewise axiom-free (mapping.md §3, meta.json
``axioms: []``; G-AX auto-skips). The G-PBT gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11603"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly INSIDE one method's impl region
# ---- (strictly between its `-- impl-start` and `-- impl-end`) and is unique in
# ---- Solution.lean; both facts are asserted at load by `_swap`, so the manifest
# ---- breaks loudly if the frozen solution ever changes. Note that the bare
# ---- `let acceptsDistinct : Bool := true` line is NOT unique (both methods have
# ---- one), which is why each anchor carries its own distinguishing tail.

_AVG_IMPL = (
    "    -- `acceptsDistinct` is this kind's capability: an averaging aggregate\n"
    "    -- accepts the duplicate-elimination option.\n"
    "    let acceptsDistinct : Bool := true\n"
    "    if distinct && !acceptsDistinct then\n"
    "      return Except.error InitErr.distinctNotAccepted\n"
    "    else\n"
    '      return Except.ok { function := "AVG", distinct := distinct }'
)

_SUM_IMPL = (
    "    let acceptsDistinct : Bool := true\n"
    "    if distinct && !acceptsDistinct then\n"
    "      return Except.error InitErr.distinctNotAccepted\n"
    "    else\n"
    '      return Except.ok { function := "SUM", distinct := distinct }'
)

assert _BASE.count(_AVG_IMPL) == 1, "frozen avgInit impl drifted; update _AVG_IMPL"
assert _BASE.count(_SUM_IMPL) == 1, "frozen sumInit impl drifted; update _SUM_IMPL"

# ---- the frozen proof bodies, verbatim. Every REJECT rival keeps them unchanged:
# ---- its rejection is carried by the witness, not by whether the frozen tactic
# ---- happens to break on the reshape. Two positives retune ONLY the (elided)
# ---- tactic body, because their reshaped impl leaves the residual goal already
# ---- closed by `loom_solve` and the frozen `simp [construct]` tail then reports
# ---- "No goals to be solved". The `method`/`ensures` obligation headers and the
# ---- `prove_correct <name>` headers are untouched in every case.
_AVG_PROOF = "prove_correct avgInit by\n  loom_solve\n  simp [construct]"
_SUM_PROOF = "prove_correct sumInit by\n  loom_solve\n  simp [construct]"

assert _BASE.count(_AVG_PROOF) == 1, "frozen avgInit proof drifted"
assert _BASE.count(_SUM_PROOF) == 1, "frozen sumInit proof drifted"


def _avg(body, proof=None):
    src = _swap(_BASE, _AVG_IMPL, body)
    return _swap(src, _AVG_PROOF, proof) if proof else src


def _sum(body, proof=None):
    src = _swap(_BASE, _SUM_IMPL, body)
    return _swap(src, _SUM_PROOF, proof) if proof else src


# ---- witness builder. Checked in a file whose `prove_correct` blocks are
# ---- stripped, so no tactic script can mask the verdict. `deriving instance
# ---- DecidableEq for Except` is required for the postcondition-decidability
# ---- derivation to go through (see WITNESS MECHANICS above); it is an instance
# ---- derivation, not an assumption.
def _witness(method, distinct):
    return (
        "deriving instance DecidableEq for Except\n\n"
        f"extract_program_for {method}\n"
        f"prove_precondition_decidable_for {method}\n"
        f"prove_postcondition_decidable_for {method}\n"
        f"derive_tester_for {method}\n\n"
        f"example : {method}Tester {distinct} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the clause is SPEC-TOO-STRONG. Both obligations are
    # defended. Each was run out-of-band with a real build (exit 0).
    # =====================================================================
    {
        "id": "pos-avg-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-reorder: handle the honourable case FIRST and refuse last. Same
        # decision, mirrored control flow. The frozen proof body is kept verbatim.
        "module": _avg(
            "    -- Branch-reorder: build on the honourable case first, refuse last.\n"
            "    -- Same outcome for every input, opposite control-flow shape.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if (!distinct) || acceptsDistinct then\n"
            '      return Except.ok { function := "AVG", distinct := distinct }\n'
            "    else\n"
            "      return Except.error InitErr.distinctNotAccepted"),
        "rationale": (
            "ports the nagini pos-construct-reorder. The guard is expressed with the "
            "accept branch first and the refusal last — the negation of the same "
            "condition, so the outcome is identical for both values of `distinct` "
            "(build and record on the honourable case, refuse only otherwise). A1 "
            "(`out = construct \"AVG\" true distinct`) must still discharge, and the "
            "frozen tactic body closes it unchanged. If a faithful correct reshape "
            "could NOT verify, the clause is over-fit to the refuse-first spelling "
            "(SPEC-TOO-STRONG). Verified live: exit 0."
        ),
    },
    {
        "id": "pos-avg-delegate",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded post-image directly.
        # Maximally structurally different — no guard, no branch, no local. The
        # elided tactic body collapses to `loom_solve` (which now closes the goal
        # outright, so the frozen `simp [construct]` tail would report "No goals to
        # be solved"); the `prove_correct avgInit` header is byte-identical.
        "module": _avg(
            "    -- Cheapest honest shape: delegate wholesale to the shared\n"
            "    -- construction guard with this kind's capability.\n"
            '    return construct "AVG" true distinct',
            "prove_correct avgInit by\n  loom_solve"),
        "rationale": (
            "the cheapest honest correct impl delegates the whole construction to the "
            "shared guard with this kind's capability, so `out` IS the post-image and "
            "A1 holds outright. Not a cheat: the guard IS the modeled work (it is a "
            "transparent `def` of the method's own binder, not an opaque oracle), so a "
            "direct delegation is a genuine alternative shape rather than an echo. "
            "Note this is also the guard-FREE shape (the branch is dead once the "
            "capability is fixed at accepting), which is why the nagini "
            "weak-construct-never-refuse rival has no counterpart here — see the "
            "footer. Must verify, else SPEC-TOO-STRONG (over-fit to the explicit-guard "
            "code shape). Verified live: exit 0."
        ),
    },
    {
        "id": "pos-sum-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape on the SECOND obligation: name the value to be
        # recorded, then record the local. Frozen proof body kept verbatim.
        "module": _sum(
            "    -- Local-variable reshape: name the value to be recorded, then\n"
            "    -- record the local rather than the binder directly.\n"
            "    let recorded : Bool := distinct\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "SUM", distinct := recorded }'),
        "rationale": (
            "ports the nagini pos-mean-local to the second obligation: the value to be "
            "recorded is bound to a local and the local is recorded, which is the same "
            "honest impl shaped differently — construction succeeds for every input "
            "and the recorded flag still equals the request, so S1 (`out = construct "
            "\"SUM\" true distinct`) discharges under the frozen tactic body. Defends "
            "the sumInit obligation specifically, so neither obligation rests on the "
            "other's positive. Must verify, else SPEC-TOO-STRONG. Verified live: "
            "exit 0."
        ),
    },

    {
        "id": "pos-avg-terminating-loop",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack F′). The termination lane, defended from the
        # only side this carrier admits. Under `termination "total"` the verifier
        # discharges a termination obligation, so the risk in BOTH directions is
        # real: a measure-free loop is refused (audit-measured, exit 1,
        # "Decreasing annotations are required in total correctness semantics"),
        # and a correct impl whose loop DOES carry a measure must still verify.
        # This is the second: the capability is computed by a bounded loop with a
        # `decreasing` measure, then the construction is delegated. Same outcome
        # for every input; the only new content is the loop and its measure.
        "module": _avg(
            "    -- Terminating-loop reshape: the capability is computed by a bounded\n"
            "    -- loop carrying a decreasing measure, then the construction is\n"
            "    -- delegated. Same outcome for every input as the frozen impl.\n"
            "    let mut acceptsDistinct : Bool := false\n"
            "    let mut i : Nat := 1\n"
            "    while i > 0\n"
            "    invariant i <= 1\n"
            "    invariant acceptsDistinct = (i == 0)\n"
            "    decreasing i\n"
            "    do\n"
            "      acceptsDistinct := true\n"
            "      i := i - 1\n"
            '    return construct "AVG" acceptsDistinct distinct',
            "prove_correct avgInit by\n  loom_solve"),
        "rationale": (
            "the termination lane on a `total` bundle, defended. This is the only "
            "shippable case in that class here: the audit measured that a diverging "
            "rival IS rejected (so there is no spec hole to report) but that its "
            "witness cannot be built either — the `method` elaboration raises the "
            "termination error inside the stripped witness file too, and a looping "
            "impl's extracted tester does not reduce (`decide` gets stuck at the "
            "`Decidable` instance), so the rival half of the witness pair cannot "
            "succeed. What remains testable is the converse risk, and it is not "
            "hypothetical on a carrier that discharges a termination obligation: if "
            "the obligation were unsatisfiable for a looping-but-terminating impl, a "
            "faithful correct reshape would be REJECTED and the clause would be "
            "SPEC-TOO-STRONG in the termination direction. The loop here is bounded "
            "and carries `decreasing i`; the invariants tie the computed capability "
            "to the loop counter so the delegation is to `construct \"AVG\" true "
            "distinct` on exit. A1 must still discharge. Verified live by the audit: "
            "exit 0 (and exit 1 without the `decreasing` line, which is what makes "
            "the measure load-bearing rather than decorative)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-mean-distinct. That case
    # made an in-region self-call on the discriminating input to show the
    # precondition ADMITS it. Here the `pre-conditions` region is EMPTY (no
    # `require` on either method), so nothing could exclude any input and the
    # classic probe is vacuous. The residual risk on a total two-point domain is a
    # DEGENERATE post-image: a spec no impl can satisfy at the discriminating
    # input reads exactly like a spec every impl satisfies. This discharges an
    # in-region assert that the post-image is satisfiable AND that it genuinely
    # tracks both the request and the capability.
    # =====================================================================
    {
        "id": "admiss-avg-distinct",
        "kind": "admissibility",
        "expect": "verify",
        "module": _avg(
            "    -- Admissibility witness. The domain is total (no `require`), so the\n"
            "    -- risk is a degenerate post-image rather than a rejected input.\n"
            "    -- Assert that the post-image at the DISCRIMINATING input (the option\n"
            "    -- requested) is a successful construction recording the request; that\n"
            "    -- it is also a success recording the absence when the option is not\n"
            "    -- requested; and that it is NOT constant in the capability (a kind\n"
            "    -- that does not accept the option refuses the same request), so the\n"
            "    -- clause is not trivially met.\n"
            "    assert (with_name_prefix `admiss\n"
            '      (construct "AVG" true true =\n'
            '         Except.ok { function := "AVG", distinct := true } ∧\n'
            '       construct "AVG" true false =\n'
            '         Except.ok { function := "AVG", distinct := false } ∧\n'
            '       construct "AVG" false true = Except.error InitErr.distinctNotAccepted))\n'
            '    return construct "AVG" true distinct'),
        "rationale": (
            "re-aimed from the nagini admiss-mean-distinct. The failing test's shape is "
            "the option REQUESTED, which is exactly the input the nagini case probed; "
            "here no `require` clause exists, so instead of showing the precondition "
            "admits it, the assert shows the post-image at that input is a SATISFIABLE "
            "and NON-DEGENERATE demand: a successful construction recording the "
            "request (not a refusal, not a dropped flag), a successful construction "
            "recording its absence on the other input, and a REFUSAL once the "
            "capability is withheld — so the clause genuinely varies with both the "
            "request and the capability. The delegating body keeps A1 discharged. If "
            "this could not verify, the obligation would be unsatisfiable at the "
            "discriminating input (PRECOND/SPEC-UNSATISFIABLE). Verified live: the true "
            "assert builds (exit 0) and falsifying one conjunct leaves an unsolved "
            "`⊢ False` goal (exit 1), so the probe is not vacuous."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. The witnesses vary the sole
    # input binder of EACH obligation: avgInit is attacked at distinct=true
    # (prepatch, drop-request, over-refuse) AND at distinct=false (force-request,
    # wrong-function); sumInit at distinct=true (prepatch) AND distinct=false
    # (negate, wrong-function). So neither obligation's binder is held fixed across
    # the battery.
    # =====================================================================
    {
        "id": "weak-avg-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour for the averaging kind: route the construction
        # through the inherited capability that does NOT accept the option, so a
        # request to aggregate over distinct values is refused. Correct on the
        # not-requested input; wrong on the requested one.
        "module": _avg(
            "    -- WRONG (pre-change shape): route through the inherited capability,\n"
            "    -- which does NOT accept the duplicate-elimination option.\n"
            "    let acceptsDistinct : Bool := false\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "AVG", distinct := distinct }'),
        "refinement": (
            "this is the pre-change behaviour of the averaging kind: without its own "
            "capability it inherits the shared default that does not accept the "
            "duplicate-elimination option, so building the averaging aggregate with the "
            "option set is refused with an error instead of succeeding. The failing "
            "test builds each of the affected aggregates with the option set and "
            "asserts the resulting aggregated value; on the averaging sub-case the "
            "faithful real counterpart raises instead of producing a value, so it FAILS "
            "and does NOT resolve. It is precisely the behaviour the desired change "
            "corrects, and it is the pre-image the bundle already ships as "
            "Solution_prepatch.lean."
        ),
        "rationale": (
            "REJECT from A1 (`out = construct \"AVG\" true distinct`): with the "
            "capability fixed at accepting, the post-image's refusal branch is DEAD, so "
            "the outcome must be a successful construction for EVERY value of the "
            "binder — the analogue of the nagini sibling's load-bearing "
            "absence-of-Exsures on build_mean. This rival refuses at distinct=true, "
            "where the spec demands a success recording the request. Ports the nagini "
            "weak-mean-prepatch. Refuted at distinct=true. If it verified => "
            "SPEC-TOO-WEAK (the spec would admit the pre-change refusal)."
        ),
        "witness": _witness("avgInit", "true"),
    },
    {
        "id": "weak-sum-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The same pre-change behaviour on the SECOND, independently-fixed
        # obligation: the summing kind routed through the non-accepting capability.
        "module": _sum(
            "    -- WRONG (pre-change shape): route through the inherited capability,\n"
            "    -- which does NOT accept the duplicate-elimination option.\n"
            "    let acceptsDistinct : Bool := false\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "SUM", distinct := distinct }'),
        "refinement": (
            "the same pre-change behaviour for the summing kind, and an INDEPENDENT "
            "break: the failing test asserts a value for each affected aggregate "
            "separately, so a real counterpart that gives only the averaging kind the "
            "capability still refuses the summing sub-case, which FAILS and does NOT "
            "resolve. Shipped by the bundle as Solution_prepatch_2.lean for exactly "
            "that reason."
        ),
        "rationale": (
            "REJECT from S1 (`out = construct \"SUM\" true distinct`): the second "
            "obligation's refusal branch is dead too, so a success is required at "
            "distinct=true and this rival refuses. Ports the nagini "
            "weak-total-prepatch. Attacks the sumInit obligation specifically, so "
            "neither obligation is left unattacked. Refuted at distinct=true. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("sumInit", "true"),
    },
    {
        "id": "weak-avg-drop-request",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-pin: keep the guard, construct successfully, but record the option
        # as ABSENT — silently discarding the request that was granted.
        "module": _avg(
            "    -- WRONG: construct successfully but record the option as ABSENT,\n"
            "    -- silently discarding the request instead of carrying it through.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "AVG", distinct := false }'),
        "refinement": (
            "accepting the request and then recording it as absent is the "
            "accepted-but-ignored behaviour: the built aggregate carries no "
            "duplicate-elimination option, so the emitted aggregation runs over ALL "
            "input rows rather than over the distinct ones and returns a different "
            "number. The failing test asserts the exact aggregated value over the "
            "distinct inputs, so the faithful real counterpart FAILS and does NOT "
            "resolve — it builds without erroring, which is why merely accepting the "
            "request is not the fix."
        ),
        "rationale": (
            "REJECT from A1 (`out = construct \"AVG\" true distinct`): the post-image's "
            "success branch records the BINDER, so at distinct=true the recorded flag "
            "must be true and this rival records false. Ports the nagini "
            "weak-construct-const-false and its build-level twin weak-mean-const-false, "
            "which collapse into one case here because the guard is inlined into the "
            "method rather than being a separately contracted function. Refuted at "
            "distinct=true. If it verified => SPEC-TOO-WEAK (read-back of the request "
            "would be unpinned and accepting would suffice)."
        ),
        "witness": _witness("avgInit", "true"),
    },
    {
        "id": "weak-sum-negate",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-pin, off-by-flip, on the second obligation: record the NEGATION of
        # the request. Wrong on BOTH inputs; refuted at the not-requested one, which
        # varies sumInit's binder away from the prepatch witness.
        "module": _sum(
            "    -- WRONG: record the NEGATION of the request (off-by-flip), so the\n"
            "    -- built aggregate carries the opposite option to the one asked for.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "SUM", distinct := !distinct }'),
        "refinement": (
            "flipping the recorded option corrupts BOTH directions: a request to "
            "aggregate over distinct values is recorded as absent (so the aggregation "
            "runs over all rows and the failing test's asserted value is not produced), "
            "and an ordinary build with no request is recorded as having one (so every "
            "existing summing aggregation silently switches to distinct inputs and the "
            "passing aggregation suite's expected sums change). The faithful real "
            "counterpart fails on both counts and does NOT resolve."
        ),
        "rationale": (
            "REJECT from S1 (`out = construct \"SUM\" true distinct`): the success "
            "branch pins the recorded flag to the binder, and the negation differs from "
            "it at both values. Ports the nagini weak-construct-negate. Refuted at "
            "distinct=FALSE — deliberately the not-requested input, so sumInit's sole "
            "binder is moved off the value its other witness holds and a rival wrong "
            "only on the ordinary build cannot hide. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("sumInit", "false"),
    },
    {
        "id": "weak-avg-over-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow / spurious refusal: refuse whenever the option is requested,
        # ignoring the capability entirely. Correct on the not-requested input; it
        # honours the request only where there is nothing to honour.
        "module": _avg(
            "    -- WRONG: refuse whenever the option is requested, ignoring this\n"
            "    -- kind's capability entirely — so the request is honoured only when\n"
            "    -- there is nothing to honour.\n"
            "    if distinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "AVG", distinct := distinct }'),
        "refinement": (
            "refusing every request to aggregate over distinct values, whatever the "
            "kind's capability, keeps the pre-change observable behaviour while looking "
            "like a deliberate rule: the failing test builds the averaging aggregate "
            "with the option set and gets an error instead of a value, so the faithful "
            "real counterpart FAILS and does NOT resolve. The sub-domain it gets right "
            "(no option requested) is not the one the failing test exercises, and the "
            "spurious refusal would additionally break every kind that already accepted "
            "the option."
        ),
        "rationale": (
            "REJECT from A1 (`out = construct \"AVG\" true distinct`): the post-image "
            "with the capability at accepting NEVER refuses, so a refusal is outside "
            "the outcome the clause sanctions — the value-and-outcome carrier senses "
            "the refuse-vs-build difference through the `Except` variant. Ports BOTH "
            "nagini weak-construct-over-refuse (a refusal outside the declared Exsures "
            "domain) and weak-mean-honour-only-false (correct on the not-requested "
            "input, refusing on the requested one), which collapse into ONE impl here "
            "because the guard is inlined into the method. Refuted at distinct=true. If "
            "it verified => SPEC-TOO-WEAK (the refusal domain would be unpinned)."
        ),
        "witness": _witness("avgInit", "true"),
    },
    {
        "id": "weak-avg-force-request",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no nagini sibling). The mirror of drop-request: record the option
        # as PRESENT whatever was asked. Wrong precisely on the NOT-requested input,
        # which is the value every other avgInit witness holds fixed — without this
        # case a rival that mishandled only the ordinary build would verify unnoticed.
        "module": _avg(
            "    -- WRONG: record the option as PRESENT whatever was asked, so an\n"
            "    -- ordinary build silently acquires an option it never requested.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "AVG", distinct := true }'),
        "refinement": (
            "forcing the option on always makes every ordinary averaging aggregation "
            "run over the distinct input values instead of all of them, so it returns a "
            "different number wherever the source column repeats. The passing "
            "aggregation suite asserts exact averages for plain builds with no such "
            "request, and those assertions would now fail, so the faithful real "
            "counterpart does NOT resolve (it regresses the very behaviour the change "
            "must leave alone while extending it)."
        ),
        "rationale": (
            "REJECT from A1 (`out = construct \"AVG\" true distinct`): the success "
            "branch records the BINDER, so at distinct=false the recorded flag must be "
            "false and this rival records true. The exact mirror of "
            "weak-avg-drop-request, and refuted at the OPPOSITE input — this is the "
            "case that moves avgInit's sole binder to false, so the not-requested "
            "sub-domain is not left unpinned. No nagini sibling (its boolean carrier "
            "covers the flip in one negate case on the shared guard); added here so "
            "each obligation's binder is varied by the witnesses of its OWN attackers. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("avgInit", "false"),
    },
    {
        "id": "weak-avg-wrong-function",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no nagini sibling — nagini's carrier is a bare Bool and models no
        # aggregate identity). Build successfully, record the request faithfully, but
        # stamp the OTHER modeled kind's function name on the result.
        "module": _avg(
            "    -- WRONG: build and record the request faithfully, but stamp the\n"
            "    -- OTHER modeled kind's function name on the constructed aggregate.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "SUM", distinct := distinct }'),
        "refinement": (
            "an aggregate that carries the other kind's function name emits the wrong "
            "aggregation to the database: the averaging build would compute a running "
            "total. The failing test asserts a DIFFERENT expected value per kind, so "
            "the faithful real counterpart returns the other kind's number on the "
            "averaging sub-case and FAILS; every passing test that averages a column "
            "breaks too. It does NOT resolve. Note this rival grants the capability "
            "correctly and records the request faithfully — it would be invisible to a "
            "battery that only probed the recorded option."
        ),
        "rationale": (
            "REJECT from A1 (`out = construct \"AVG\" true distinct`): the post-image "
            "pins the CONSTRUCTED CONTENT, both components — the recorded option AND "
            "the aggregate's own function name — so substituting the other kind's name "
            "diverges at every input. No nagini sibling: nagini's three functions "
            "return a bare bool and model no aggregate identity at all, so this "
            "distinction exists only on this richer carrier and is attacked here rather "
            "than left to chance. Refuted at distinct=false (a second point holding "
            "avgInit's binder off true, and one where the recorded option is CORRECT so "
            "the refutation is attributable to the function-name component alone). If "
            "it verified => SPEC-TOO-WEAK (the aggregate's identity would be free)."
        ),
        "witness": _witness("avgInit", "false"),
    },
    {
        "id": "weak-sum-wrong-function",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (no nagini sibling). The mirror of weak-avg-wrong-function
        # on the SECOND obligation: sumInit's post-image pins two independent
        # components, and before this case only avgInit's function-name component was
        # ever attacked — sumInit's rivals (prepatch, negate) both leave the recorded
        # NAME untouched, so a rival that stamped the wrong kind on the summing build
        # was unprobed on the very obligation the footer claims is defended in both
        # components.
        "module": _sum(
            "    -- WRONG: build and record the request faithfully, but stamp the\n"
            "    -- OTHER modeled kind's function name on the constructed aggregate.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "AVG", distinct := distinct }'),
        "refinement": (
            "the summing kind's aggregate carrying the other kind's function name "
            "emits the wrong aggregation to the database: the summing build would "
            "compute an average instead of a running total. The failing test asserts a "
            "DIFFERENT expected value per kind, so the faithful real counterpart "
            "returns the other kind's number on the summing sub-case and FAILS; every "
            "passing test that totals a column breaks too. It does NOT resolve. Like "
            "its averaging mirror it grants the capability correctly and records the "
            "request faithfully, so a battery that only probed the recorded option "
            "would not see it."
        ),
        "rationale": (
            "REJECT from S1 (`out = construct \"SUM\" true distinct`): the post-image "
            "pins the CONSTRUCTED CONTENT, both components — the recorded option AND "
            "the aggregate's own function name — so substituting the other kind's name "
            "diverges at every input. Added by the audit because the "
            "function-name component was attacked on avgInit ONLY: sumInit carried "
            "two rivals and both varied only the recorded option, so this component of "
            "S1 rested on the avgInit case's argument rather than on any demonstration "
            "of its own. Refuted at distinct=false, where the recorded option is "
            "CORRECT, so the refutation is attributable to the function-name component "
            "alone. If it verified => SPEC-TOO-WEAK (the summing aggregate's identity "
            "would be free)."
        ),
        "witness": _witness("sumInit", "false"),
    },
    {
        "id": "weak-sum-drop-request",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The drop-request defect on the SECOND
        # obligation. sumInit's recorded-option rivals were prepatch (a refusal,
        # not a mis-record) and negate (wrong at BOTH inputs), so no sumInit rival
        # was wrong at distinct=true ONLY while building successfully — the exact
        # accepted-but-ignored shape, and the one avgInit probes with
        # weak-avg-drop-request. S1's recorded-option component was therefore
        # attacked only by a rival that is also wrong on the ordinary build, so a
        # summing impl that granted the capability and then silently discarded the
        # request was unprobed on its own obligation.
        "module": _sum(
            "    -- WRONG: construct successfully but record the option as ABSENT,\n"
            "    -- silently discarding the request instead of carrying it through.\n"
            "    let acceptsDistinct : Bool := true\n"
            "    if distinct && !acceptsDistinct then\n"
            "      return Except.error InitErr.distinctNotAccepted\n"
            "    else\n"
            '      return Except.ok { function := "SUM", distinct := false }'),
        "refinement": (
            "accepting the request on the summing kind and then recording it as "
            "absent is the accepted-but-ignored behaviour: the built aggregate "
            "carries no duplicate-elimination option, so the emitted aggregation "
            "totals ALL input rows rather than the distinct ones and returns a "
            "different number. The failing test asserts the exact aggregated value "
            "over the distinct inputs for each affected kind separately, so the "
            "faithful real counterpart FAILS on the summing sub-case and does NOT "
            "resolve — it builds without erroring, which is why merely accepting the "
            "request is not the fix. Unlike weak-sum-negate it is CORRECT on the "
            "ordinary build, so it is a strictly narrower near-miss: it breaks only "
            "the sub-domain the failing test exercises."
        ),
        "rationale": (
            "REJECT from S1 (`out = construct \"SUM\" true distinct`): the "
            "post-image's success branch records the BINDER, so at distinct=true the "
            "recorded flag must be true and this rival records false. The mirror of "
            "weak-avg-drop-request on the second obligation, added by the audit "
            "because S1's recorded-option component was previously attacked only by "
            "weak-sum-negate, which is wrong at BOTH inputs — so no sumInit rival "
            "isolated the accepted-but-ignored defect, and the narrower near-miss "
            "(right on the ordinary build, wrong exactly where the failing test "
            "looks) rested on the avgInit case's argument rather than on a "
            "demonstration of its own. Refuted at distinct=true. If it verified => "
            "SPEC-TOO-WEAK (read-back of the request would be unpinned on sumInit "
            "and accepting would suffice)."
        ),
        "witness": _witness("sumInit", "true"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling ships 12 SPEC cases (2 soundness, 1 admissibility, 9
# uniqueness — recounted by the audit; the battery previously said 11/8, which
# undercounted the uniqueness lane by one) and an EMPTY axiom lane, over THREE
# contracted functions:
# `construct_dedup(allow_dedup, dedup)` (the shared construction guard, with a
# normal-return-reachability Ensures, a read-back Ensures and an Exsures pinning
# the refusal domain) and `build_mean(dedup)` / `build_total(dedup)` (the two
# fixed kinds, each with a read-back Ensures and NO Exsures).
#
# This bundle contracts TWO methods, `avgInit` and `sumInit`, one binder each.
# The guard is NOT a contracted obligation here: it is the transparent
# `pure`-region `def construct`, INLINED into both post-images with the
# capability argument fixed at accepting. That is the whole carrier difference,
# and it drives every merge and the one omission below.
#
#   nagini case                     -> here
#   ------------------------------------------------------------------------
#   pos-construct-reorder           -> pos-avg-reorder              PORTED
#   pos-mean-local                  -> pos-sum-local                PORTED
#   (new shape, no sibling)         -> pos-avg-delegate             ADDED
#   admiss-mean-distinct            -> admiss-avg-distinct          RE-AIMED
#   weak-mean-prepatch              -> weak-avg-prepatch            PORTED
#   weak-total-prepatch             -> weak-sum-prepatch            PORTED
#   weak-construct-const-false  \
#   weak-mean-const-false        }  -> weak-avg-drop-request        MERGED
#   weak-construct-negate           -> weak-sum-negate              PORTED
#   weak-construct-over-refuse  \
#   weak-mean-honour-only-false  }  -> weak-avg-over-refuse         MERGED
#   weak-construct-never-refuse     -> (none)                       OMITTED
#   weak-mean-diverge               -> pos-avg-terminating-loop     RE-AIMED (audit)
#   (new, no sibling)               -> weak-avg-force-request       ADDED (binder)
#   (new, no sibling)               -> weak-avg-wrong-function      ADDED (clause)
#   (new, no sibling)               -> weak-sum-wrong-function      ADDED (audit)
#   (new, no sibling)               -> weak-sum-drop-request        ADDED (audit)
#   AXIOM_TESTS (already [])        -> AXIOM_TESTS = []             EMPTY BOTH SIDES
#
# 14 velvet SPEC cases: 4 soundness, 1 admissibility, 9 uniqueness.
#
# MERGED (2 pairs -> 2 cases). Nagini attacks the guard TWICE for each defect:
#   once on `construct_dedup` directly and once on `build_mean`, because they are
#   separately contracted functions. Here the guard is inlined into the method's
#   own post-image, so the two attacks become the same impl edit and the same
#   witness; shipping both would be one rival wearing two ids, and its rationale
#   would claim a sub-domain the second copy never demonstrates. The nagini
#   ARGUMENT of each pair is carried in the surviving case's rationale.
# OMITTED (weak-construct-never-refuse) — this rival is NOT WRONG on this
#   carrier. Nagini can drop the capability guard entirely because
#   `construct_dedup` takes the capability as an INPUT, so a guard-free body is
#   observably wrong at (dedup=True, allow_dedup=False). Here the capability is
#   not a binder of either method: both post-images fix it at accepting, so the
#   refusal branch is DEAD and a guard-free body is BEHAVIOURALLY IDENTICAL to
#   gold. It is shipped as the `pos-avg-delegate` POSITIVE, where it verifies —
#   which is the correct disposition, not a gap: there is no input at which the
#   spec refutes it, so no discriminating witness exists and a reject case would
#   have been a forgery. (What the nagini case defends — that a kind WITHOUT the
#   capability must still be refused — survives in this battery as the third
#   conjunct of admiss-avg-distinct, which asserts the refusal at a withheld
#   capability, and as weak-avg-over-refuse's mirror image.)
# RE-AIMED BY THE AUDIT (weak-mean-diverge -> pos-avg-terminating-loop). The
#   battery previously recorded this class as a KNOWN SPEC HOLE on the stated
#   ground that "this bundle runs under `set_option loom.semantics.termination
#   \"partial\"` (Solution.lean line 4), so a non-terminating implementation
#   satisfies A1 and S1 VACUOUSLY and VERIFIES". That was FALSE of this bundle:
#   line 4 reads `"total"`. The claim was inherited from an earlier corpus-wide
#   note that sized a `partial` majority against a `total` minority, and that
#   census is withdrawn as well (all 500 velvet bundles set `"total"`); it was
#   carried over without re-reading the frozen file, so the battery documented a
#   hole in a spec that does not have one. The audit re-measured all three legs:
#     * a spin-loop rival spliced before gold's correct tail is REJECTED, exit 1,
#       `error: Decreasing annotations are required in total correctness
#       semantics` — so nothing is admitted vacuously and there is no spec hole;
#     * that same error is raised by the `method` elaboration, so it also fires in
#       the WITNESS file (where the obligations are stripped), and the extracted
#       tester of a looping impl does not reduce: `decide` reports `reduction got
#       stuck at the Decidable instance` on the RIVAL side, which is the half the
#       gate requires to SUCCEED. Measured with a spin loop and with a bounded
#       loop. So the class is not shippable as a reject case either — not for
#       difficulty, but because no witness can pass the rival half;
#     * what IS shippable is the converse direction, and on a carrier that
#       discharges a termination obligation it is a real risk rather than a
#       formality: `pos-avg-terminating-loop` is a correct impl whose loop carries
#       `decreasing i`, and it must verify (measured exit 0; exit 1 with the
#       `decreasing` line removed, which is what makes the measure load-bearing).
#   Net: the class is CLOSED by the carrier, defended by a positive, and is not a
#   spec hole. Nothing here is escalated.
# RE-AIMED (admiss-mean-distinct -> admiss-avg-distinct): the nagini case
#   established that the precondition ADMITS the discriminating input. Neither
#   method here carries a `require` (the pre-conditions region is empty), so no
#   input can be excluded and that probe is vacuous; re-aimed at the residual
#   risk on a total two-point domain — a degenerate/unsatisfiable post-image —
#   witnessed by an in-region assert that was checked BOTH ways (true assert
#   builds, falsified conjunct fails).
# ADDED (3). pos-avg-delegate: the guard-free shape, which is the correct home for
#   the omitted nagini rival (see above) and the cheapest-honest-impl control the
#   nagini file describes in its DEFENDED SURFACE note. weak-avg-force-request:
#   moves avgInit's sole binder to FALSE, the value its other three witnesses hold
#   fixed — without it a rival wrong only on the ordinary build would verify and
#   the battery would never notice. weak-avg-wrong-function: attacks the
#   aggregate-identity component of the post-image, a distinction nagini's bare
#   `bool` carrier does not model at all; it is a REAL divergence with a
#   machine-checked witness, not fabricated wrongness. weak-sum-wrong-function
#   (added by the audit) is its mirror on the second obligation, for the same
#   reason: the component is real on this carrier and was otherwise unprobed there.
# FRAME / PERMISSION-MUTATION: VACUOUS, and the nagini sibling itself records the
#   class as inapplicable (three functions over plain booleans, no heap, no
#   read-only fractional-permission input). Referentially transparent backend: no
#   `mut` binder, no heap, no aliasing, no permission system. No substitute
#   fabricated.
# AXIOM lane: EMPTY ON BOTH SIDES. The nagini file already ships `AXIOM_TESTS =
#   []` (the guard is modeled deeply, nothing axiomatized), and this bundle is
#   axiom-free too (mapping.md §3; meta.json `axioms: []`; G-AX auto-skips). The
#   gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE. Each obligation has exactly ONE input binder,
#   `distinct : Bool`, and the domain is the whole of `Bool` (no `require`), so
#   the binder is fully covered iff BOTH values are probed — per obligation, not
#   just across the battery. They are: avgInit at true (weak-avg-prepatch,
#   weak-avg-drop-request, weak-avg-over-refuse) and at false
#   (weak-avg-force-request, weak-avg-wrong-function); sumInit at true
#   (weak-sum-prepatch, weak-sum-drop-request) and at false (weak-sum-negate,
#   weak-sum-wrong-function).
#   No obligation's binder is pinned. Both obligations are DEFENDED
#   (pos-avg-reorder + pos-avg-delegate + pos-avg-terminating-loop +
#   admiss-avg-distinct for avgInit; pos-sum-local for sumInit) and ATTACKED (five
#   rivals / four rivals respectively). Each obligation has a single top-level
#   `ensures`, and BOTH of its independent components are attacked ON THAT
#   OBLIGATION'S OWN RIVALS — never by inheriting the other obligation's argument:
#     OUTCOME (build vs refuse):      avgInit — prepatch, over-refuse
#                                     sumInit — prepatch
#     CONTENT / recorded option:      avgInit — drop-request, force-request
#                                     sumInit — negate, drop-request
#     CONTENT / function name:        avgInit — wrong-function
#                                     sumInit — wrong-function
#   The last row's sumInit entry was added by the audit: the battery previously
#   attacked the function-name component on avgInit only, so S1's second component
#   was claimed by this paragraph without any case demonstrating it. Both entries
#   are refuted at distinct=false, where the recorded option is correct, so the
#   refutation is attributable to the name component alone.
#   The recorded-option row's `sumInit — drop-request` entry was also added by the
#   audit, and for a subtler reason than a missing spelling: sumInit's only
#   recorded-option rival was `negate`, which is wrong at BOTH values of the
#   binder. A rival wrong everywhere is the EASY case; the accepted-but-ignored
#   defect (build successfully, grant the capability, then discard the request —
#   wrong at distinct=true ONLY, which is exactly where the failing test looks) is
#   the narrower near-miss, and on sumInit nothing exercised it. avgInit had it as
#   weak-avg-drop-request all along, so S1 was inheriting that argument.
#   TERMINATION is a third, carrier-level component, defended by
#   pos-avg-terminating-loop and unattackable by a rival for the witness reason in
#   the RE-AIMED note above.
#
# WITNESS MECHANICS: `deriving instance DecidableEq for Except` + the four Velvet
#   tester directives + `<method>Tester <literal> = false`, by `decide`. Measured:
#   without the `deriving instance` line `decide` gets stuck on the `Decidable`
#   instance for BOTH builds (inconclusive, not discriminating — re-measured by
#   the audit: both sides report `reduction got stuck at the Decidable instance`);
#   with it, all nine witnesses were confirmed with two real
#   `scripts/lean_verify.sh` builds each — rival exit 0, frozen solution exit 1
#   (`decide` proving the tester equation false). Every gold-side signature is a
#   PLAIN EVALUATION (`Tactic decide proved that the proposition <method>Tester
#   <literal> = false is false`), i.e. the kernel computed the tester and the
#   claim was refuted — not a missing identifier, type error, unfolding failure or
#   timeout. The audit confirmed that with the forgery test on all nine (see the
#   header): flipping the claim inverts both exit codes exactly, so the gold build
#   is discriminating the claim rather than failing for a fixed structural reason.
#   No witness binds a hypothesis (every input is a `Bool`
#   literal), so no carrier conditioning is used and the gate's consistency probe
#   is a no-op. No banned token anywhere.
AXIOM_TESTS = []

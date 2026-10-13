"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-12682 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (three contracted methods — the value is threaded through a
construction step, an encode step, and their end-to-end composition):

  recordIterationBudget (userBudget : Nat) return (cfg : CodingConfig)
    ensures cfg.iterationBudget = userBudget
  encodeWithConfig (cfg : CodingConfig) return (solverBudget : Nat)
    ensures solverBudget = cfg.iterationBudget
  configuredBudgetReachesSolver (userBudget : Nat) return (solverBudget : Nat)
    ensures solverBudget = userBudget

The modeled behaviour is a pure DATA-FLOW property: a user-configured iteration
budget for the underlying iterative solver is RECORDED on the configuration at
construction, READ BACK at the encode step, and FORWARDED UNCHANGED to the
solver — rather than being dropped so the solver falls back on a fixed built-in
default. Each ``ensures`` is an EXACT-VALUE identity (no opaque answer key to
echo; the ``axioms`` region is empty). The three clauses are independent
top-level obligations, one per modeled step; the end-to-end clause is the
composition and is the observable the F2P test pins (a user budget of 1 must
reach the solver and force non-convergence; a budget of 2000 must reach it and
allow convergence).

TWO INPUT BINDERS across the surface: ``userBudget : Nat`` (the requested budget,
binder of the construction and end-to-end clauses) and ``cfg.iterationBudget``
(the recorded budget, binder of the encode clause). Both are load-bearing — the
whole point is that the value the user configures is the value the solver runs
with — and both are VARIED by the reject witnesses (userBudget over {5, 8, 3, 9,
6}; cfg.iterationBudget over {7, 2, 12}), so no binder is pinned at one value
across the reject set (pts = 8 distinct input points).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``<method>Tester args = false`` says the extracted
program's result violates that method's postcondition at the concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` blocks have been
stripped so no tactic script can mask the verdict. This carrier is FULLY
TRANSPARENT: every impl is a finite ``Nat`` / structure computation, so the
extracted program reduces to ``isTrue``/``isFalse`` under the kernel for every
concrete literal — both against a rival (where the postcondition is violated, so
the tester is ``false`` and ``= false`` elaborates by ``decide``) and against the
frozen solution (where it holds, the tester is ``true``, and ``= false`` fails by
``decide``, the required FAIL-on-gold half). No opaque term appears, so no
conditioning is needed and the witnesses declare NO head binders. Both halves of
every witness were checked with ``scripts/lean_verify.sh`` during authoring —
each elaborates green against its rival and fails (``decide``) against the frozen
solution. (Nat subtraction truncates at 0, so the off-by-one witness is placed at
a nonzero budget where the truncation does not mask the divergence.)

ADVERSARIAL READ of the sibling's classes on this carrier (full accounting in the
footer):
  * SOUNDNESS / positive controls — APPLY. For each modeled step, a structurally
    different but behaviourally identical impl (return the field directly / bind
    a local before storing / thread an extra local through the composition) must
    verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the methods declare no ``require`` clause, so the sibling's
    "a normal input satisfies the fractional-permission Requires" probe is
    degenerate here. The residual admissibility risk on a total domain is a
    DEGENERATE post-image; ``admiss-nondegenerate`` discharges an in-region
    ``assert`` pinning the recorded budget at the two F2P-shaped probe values
    (the small budget that forces non-convergence and the large one that allows
    it) and that they are distinct, keeping the impl verbatim so the method's own
    obligation still discharges.
  * FRAME / PERMISSION-MUTATION — the MECHANISM is vacuous here, the ATTACK is
    not. The sibling's mandatory rival overwrites a read-only input held at a
    fractional heap permission. Lean/Velvet are referentially transparent, so
    there is no heap write to make and no permission to be insufficient — that
    much is a genuine carrier fact. But what the sibling's rival ATTACKS is
    directive 5: satisfy the pin on a value the impl substituted for the
    read-only input. That is expressible here by SHADOWING the binder, and
    ``weak-e2e-rebinds-request`` carries it. (AUDIT CORRECTION: the port recorded
    this whole class as VACUOUS / NOT PORTED. The mechanism reasoning was right
    and the disposition was wrong — the substitution attack lands on this carrier,
    was measured to be rejected for the right reason, and now ships.)
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, NOT a spec hole. This
    bundle sets ``loom.semantics.termination "total"``, and that option cannot drift
    from the file's ``open TotalCorrectness DemonicChoice``, because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Under ``total`` a
    postcondition is claimed of ALL runs, not only terminating ones, and the
    verifier demands a decreasing measure on every loop, so a diverging rival is
    REJECTED rather than vacuously admitted. Measured on this bundle with the proof
    reduced to a bare ``loom_solve``: an unmeasured spun loop is refused at
    elaboration (``Decreasing annotations are required in total correctness
    semantics``), and the sharper shape that CARRIES a measure which does not
    decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``,
    body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. That second shape is the one
    that matters: it cannot be dismissed as merely missing an annotation. So there is
    nothing here for a diverging rival to exploit and no reject case to ship. (The
    sibling carries no ``diverge-*`` case either.) An earlier version of this bullet
    said a non-terminating impl "cannot be written at all" and set this against a
    ``partial`` known-hole in an internal findings doc; the rival CAN be written, it
    is REJECTED when it is, and there is no ``partial`` cohort to contrast with,
    since all 500 velvet bundles now set ``"total"``.
  * UNGROUNDED-ORACLE ECHO — the sibling's two highest-value rivals echo @Pure
    answer-key constants (a solver's built-in default, and a coder's parameter
    default) that live in ITS contract. This backend has NO such answer key: each
    ``ensures`` is an EXACT identity to a method argument, not to an opaque
    constant. Those rivals port here as impls that return the literal default
    (the canonical wrong answers) instead of the threaded value; the spec refutes
    them not because they echo an oracle but because the returned constant is not
    the configured budget.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets part of the
    domain right yet diverges elsewhere (a construction step that stores a
    constant default, an encode step that ignores the configuration, an
    end-to-end path that returns a fixed default, an end-to-end off-by-one, an
    encode step hard-coding a single iteration, and an encode step correct at
    exactly the two tested budgets and defaulted everywhere else).
  * TEST-FITTING — AUDIT-ADDED, no sibling analogue. Every constant rival the port
    shipped is wrong AT the F2P probe values too, so none of them detects a spec
    that pins the behavior only where the failing test looks.
    ``weak-encode-f2p-echo`` is correct at exactly those two budgets and defaulted
    elsewhere; the spec refutes it on the rest of the domain.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12682"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- per-method impl-body anchors. Each lies WHOLLY inside its method's
# ---- `-- impl-start`/`-- impl-end` region and is unique in the file (asserted
# ---- at load), so a swap is confined to the impl region and same_spec holds.
# ---- The surrounding comments and the `prove_correct` headers are untouched.
_REC = "    let cfg : CodingConfig := { iterationBudget := userBudget }\n    return cfg"
assert _BASE.count(_REC) == 1, "record impl anchor drift — re-sync _REC"

_ENC = "    let solverBudget := cfg.iterationBudget\n    return solverBudget"
assert _BASE.count(_ENC) == 1, "encode impl anchor drift — re-sync _ENC"

_E2E = ("    let cfg ← recordIterationBudget userBudget\n"
        "    let solverBudget ← encodeWithConfig cfg\n"
        "    return solverBudget")
assert _BASE.count(_E2E) == 1, "end-to-end impl anchor drift — re-sync _E2E"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `<method>Tester args = false` says the extracted program's result violates
# ---- that method's postcondition at the concrete input. Checked in a file whose
# ---- `prove_correct` blocks have been stripped. Every argument is a concrete
# ---- literal so `decide` reduces the extracted program without getting stuck.
def _tester(method, call):
    return (
        "\n"
        f"extract_program_for {method}\n"
        f"prove_precondition_decidable_for {method}\n"
        f"prove_postcondition_decidable_for {method}\n"
        f"derive_tester_for {method}\n\n"
        f"example : {method}Tester {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. One per modeled step, so each obligation is defended by a
    # faithful reshape as well as attacked. If a correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG on the shape of the impl. (Every positive is a full
    # file, so it also re-verifies the two frozen obligations it does not reshape.)
    # =====================================================================
    {
        "id": "pos-control-encode-direct",
        "kind": "soundness",
        "expect": "verify",
        # Encode step reshaped to return the configured budget directly, with no
        # intermediate binding — observationally identical for every configuration.
        "module": _swap(_BASE, _ENC, "    return cfg.iterationBudget"),
        "rationale": (
            "the encode step returns the configured budget directly (no "
            "intermediate `let`), so `solverBudget = cfg.iterationBudget` holds on "
            "the whole domain; the reproof is `loom_solve`. If this fails to verify "
            "the encode obligation is over-fit to the frozen statement shape "
            "(SPEC-TOO-STRONG). (Sibling: pos-control-1, a structurally-different "
            "correct forwarder.)"),
    },
    {
        "id": "pos-control-record-named-local",
        "kind": "soundness",
        "expect": "verify",
        # Construction step reshaped to bind the requested budget to a local
        # before storing it — a statement-shape change that keeps the identity.
        "module": _swap(
            _BASE, _REC,
            "    let requested := userBudget\n"
            "    let cfg : CodingConfig := { iterationBudget := requested }\n"
            "    return cfg"),
        "rationale": (
            "the construction step binds the requested budget to a local before "
            "recording it, so `cfg.iterationBudget = userBudget` still holds; the "
            "read-only `userBudget` is consulted, not altered. A correct reshape "
            "must verify, else the record obligation is SPEC-TOO-STRONG (rejects a "
            "faithful impl over the shape of the assignment). (Sibling: "
            "pos-control-2, a local-variable reshape.)"),
    },
    {
        "id": "pos-control-e2e-extra-local",
        "kind": "soundness",
        "expect": "verify",
        # End-to-end composition reshaped to thread an extra local between the two
        # callee results — same data flow, different statement shape.
        "module": _swap(
            _BASE, _E2E,
            "    let cfg ← recordIterationBudget userBudget\n"
            "    let budget ← encodeWithConfig cfg\n"
            "    let solverBudget := budget\n"
            "    return solverBudget"),
        "rationale": (
            "the end-to-end path threads an extra local between recording the "
            "budget and encoding under it, so `solverBudget = userBudget` still "
            "holds via the callee obligations. A correct reshape must verify, else "
            "the composition obligation is SPEC-TOO-STRONG. (Sibling: pos-control-2 "
            "reshaped to the composition site.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the methods declare no `require`, so the sibling's
    # precondition-admissibility probe is degenerate here. The residual risk on a
    # total domain is a DEGENERATE post-image — a spec no impl distinguishes reads
    # exactly like one every impl meets. This case discharges an in-region
    # `assert` that the CALLEE CONTRACTS, applied at the two F2P-shaped probe
    # values, force distinct forwarded budgets. The assert is stated over the
    # results of two real forwarded calls (`recordIterationBudget` then
    # `encodeWithConfig`), so `loom_solve` can only close it by CONSUMING the two
    # `ensures` — which is what makes it a live probe of the modeled data flow
    # rather than a closed arithmetic fact. AUDIT NOTE: the case originally
    # asserted `({iterationBudget := 1} : CodingConfig).iterationBudget = 1 ∧ ...
    # ∧ (1 : Nat) ≠ 2000` — a closed tautology about the structure projection and
    # two literals, referring to no method result. Measured with the real
    # verifier: dropped verbatim into the `weak-record-drops-budget` wrong impl
    # that constant-stores 1000, that assert still CLOSED (the build's only
    # unsolved goal was the postcondition `1000 = userBudget`, with the assert
    # discharged to the residual hypothesis `admiss_1 : 1 ≠ 2000`), so its own
    # rationale's claim that "a constant-storing impl could not discharge this"
    # was false and the case probed nothing about the post-image. The self-call
    # form below was checked the same way: asserting a FALSE consequence of the
    # same two calls (`smallOut = 2000`) fails with the assert itself as the
    # unsolved goal, so the assert is load-bearing on the callee contracts.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _E2E,
            "    let probeSmall ← recordIterationBudget 1\n"
            "    let probeLarge ← recordIterationBudget 2000\n"
            "    let smallOut ← encodeWithConfig probeSmall\n"
            "    let largeOut ← encodeWithConfig probeLarge\n"
            "    assert (with_name_prefix `admiss (\n"
            "      smallOut = 1 ∧ largeOut = 2000 ∧ smallOut ≠ largeOut))\n"
            "    let cfg ← recordIterationBudget userBudget\n"
            "    let solverBudget ← encodeWithConfig cfg\n"
            "    return solverBudget"),
        "rationale": (
            "the modeled data flow is satisfiable AND non-degenerate at the two "
            "F2P-shaped probe values: recording a budget of 1 and encoding under "
            "that configuration forwards 1, recording 2000 forwards 2000, and the "
            "two forwarded budgets DIFFER — so the value the solver runs with "
            "genuinely tracks the request rather than being a constant every impl "
            "meets. The assert is over the results of two real forwarded calls, so "
            "it is closable only by consuming the record and encode `ensures`; the "
            "trailing impl is the frozen composition verbatim, so "
            "`solverBudget = userBudget` still verifies. (Sibling: admiss-1, "
            "re-aimed from precondition admissibility to post-image non-degeneracy "
            "since this backend declares no `require` and has no permission "
            "surface; kept as a SELF-CALL probe like the sibling's, which is what "
            "makes it read the contracts.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival keeps the frozen
    # `prove_correct` scripts (which, for the corrupted method, simply fail to
    # close — the rejection); the witness attributes that rejection to the spec.
    # =====================================================================
    {
        "id": "weak-record-drops-budget",
        "kind": "uniqueness",
        "expect": "reject",
        # The construction step ignores the requested budget and records the fixed
        # built-in default instead — the canonical wrong answer (the pre-change
        # construction path that stored no user budget). Correct for no input
        # except userBudget == 1000.
        "module": _swap(
            _BASE, _REC,
            "    let cfg : CodingConfig := { iterationBudget := 1000 }\n"
            "    return cfg"),
        "refinement": (
            "the faithful counterpart is the construction path that never stores "
            "the user-requested budget, so the recorded value is the fixed built-in "
            "default regardless of what the user asked for. With the default "
            "recorded, the small-budget F2P case (which must force non-convergence) "
            "would instead run with the large default and converge — no warning "
            "where one is required — so test_max_iter does NOT resolve. Correct only "
            "at the single request equal to the default."),
        "rationale": (
            "REJECT from `cfg.iterationBudget = userBudget`: the spec pins the "
            "recorded budget to the request, this rival records the constant 1000. "
            "Verifying would be SPEC-TOO-WEAK (the record obligation unpinned). "
            "Refuted at userBudget 5 (gold records 5, the rival 1000) — this is the "
            "only witness exercising the record obligation and varies userBudget "
            "away from the other reject points."),
        "witness": _tester("recordIterationBudget", "5"),
    },
    {
        "id": "weak-record-offby1",
        "kind": "uniqueness",
        "expect": "reject",
        # The construction step records one below the requested budget — a
        # partial-domain break on the record obligation, wrong at every nonzero
        # request yet structurally faithful (it does read `userBudget`). Probes the
        # record obligation at a userBudget distinct from weak-record-drops-budget.
        "module": _swap(
            _BASE, _REC,
            "    let cfg : CodingConfig := { iterationBudget := userBudget - 1 }\n"
            "    return cfg"),
        "refinement": (
            "a faithful counterpart that recorded a budget one below the user's "
            "request would under-configure the solver by one iteration for every "
            "value; the budget the F2P asserts is recorded is off by one throughout "
            "— it does NOT resolve. Reads the request (structurally close to gold) "
            "yet diverges on the whole nonzero domain."),
        "rationale": (
            "REJECT from `cfg.iterationBudget = userBudget`: the spec pins the "
            "recorded budget exactly, this rival records `userBudget - 1`. Verifying "
            "would be SPEC-TOO-WEAK (the record identity relaxed to off-by-one). "
            "Refuted at userBudget 8 (gold records 8, the rival 7) — a nonzero point "
            "so Nat truncation does not mask the gap, and a SECOND record-obligation "
            "input distinct from weak-record-drops-budget's userBudget 5, so the "
            "record obligation's dependence on `userBudget` is demonstrated."),
        "witness": _tester("recordIterationBudget", "8"),
    },
    {
        "id": "weak-encode-ignores-config",
        "kind": "uniqueness",
        "expect": "reject",
        # The encode step ignores the recorded configuration and forwards the fixed
        # built-in default to the solver — the canonical wrong answer (the
        # pre-change encode path that dropped the configured budget). Correct only
        # when the configured budget happens to equal the default.
        "module": _swap(
            _BASE, _ENC,
            "    let solverBudget := 1000\n"
            "    return solverBudget"),
        "refinement": (
            "the faithful counterpart is the encode path that does not read the "
            "recorded budget and lets the solver fall back on its fixed built-in "
            "default. The small-budget F2P case would then run with the default and "
            "converge instead of warning — so test_max_iter does NOT resolve. "
            "Correct only when the configured budget equals the default."),
        "rationale": (
            "REJECT from `solverBudget = cfg.iterationBudget`: the spec pins the "
            "forwarded value to the recorded budget, this rival forwards the "
            "constant 1000. Verifying would be SPEC-TOO-WEAK (the encode obligation "
            "unpinned). Refuted at a configuration recording 7 (gold forwards 7, the "
            "rival 1000) — varies cfg.iterationBudget away from the other encode "
            "witness."),
        "witness": _tester("encodeWithConfig", "{ iterationBudget := 7 }"),
    },
    {
        "id": "weak-e2e-builtin-default",
        "kind": "uniqueness",
        "expect": "reject",
        # The end-to-end path returns a fixed solver built-in default instead of
        # the threaded user budget — the value-echo rival for the second reported
        # default. Correct only when the user requests exactly that default.
        "module": _swap(
            _BASE, _E2E,
            "    let solverBudget := 500\n"
            "    return solverBudget"),
        "refinement": (
            "the faithful counterpart never threads the configured budget through "
            "to the solver, which runs at a fixed built-in default; the iteration "
            "limit is decoupled from the user's request for every value but that "
            "one default. The F2P (small budget must warn, large must not) reads the "
            "solver's convergence, which no longer tracks the configured value — so "
            "it does NOT resolve. Correct only at the single request equal to the "
            "default."),
        "rationale": (
            "REJECT from `solverBudget = userBudget`: the spec pins the "
            "end-to-end result to the request, this rival returns the constant 500. "
            "Verifying would be SPEC-TOO-WEAK (the composition obligation unpinned). "
            "Refuted at userBudget 3 (gold returns 3, the rival 500)."),
        "witness": _tester("configuredBudgetReachesSolver", "3"),
    },
    {
        "id": "weak-e2e-offby1",
        "kind": "uniqueness",
        "expect": "reject",
        # The end-to-end path threads the budget correctly but delivers one fewer
        # iteration than requested — a partial-domain break wrong at every nonzero
        # budget yet structurally faithful (it does read and forward the value).
        "module": _swap(
            _BASE, _E2E,
            "    let cfg ← recordIterationBudget userBudget\n"
            "    let budget ← encodeWithConfig cfg\n"
            "    return (budget - 1)"),
        "refinement": (
            "the faithful counterpart forwards a budget one below the user's "
            "request, so the solver is mis-budgeted by one iteration for every "
            "configured value; the budget the F2P asserts reaches the solver is off "
            "by one throughout — it does NOT resolve. Reads and forwards the value "
            "(so it is structurally close to gold) yet diverges on the whole "
            "positive domain."),
        "rationale": (
            "REJECT from `solverBudget = userBudget`: the spec pins the forwarded "
            "value exactly, this rival delivers `userBudget - 1`. Verifying would be "
            "SPEC-TOO-WEAK (the exact-value identity relaxed to off-by-one). Refuted "
            "at userBudget 9 (gold returns 9, the rival 8) — a nonzero point so Nat "
            "truncation does not mask the gap, and a distinct end-to-end input from "
            "the builtin-default witness. (Sibling: weak-partial-domain.)"),
        "witness": _tester("configuredBudgetReachesSolver", "9"),
    },
    {
        "id": "weak-encode-single-iteration",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss (sibling weak-const-coder): the encode step
        # hard-codes a single iteration, ignoring the configured budget. Correct
        # only when the configured budget is exactly 1.
        "module": _swap(
            _BASE, _ENC,
            "    let solverBudget := 1\n"
            "    return solverBudget"),
        "refinement": (
            "a faithful counterpart that forced a single solver iteration "
            "regardless of the configuration would leave the large-budget F2P case "
            "(which must converge without warning) running for one iteration and "
            "warning — so test_max_iter does NOT resolve. Correct only when the "
            "configured budget is 1."),
        "rationale": (
            "REJECT from `solverBudget = cfg.iterationBudget`: the spec pins the "
            "forwarded value to the recorded budget, this rival forwards the "
            "constant 1. Cheap corruption with a real refinement; supports the "
            "reasoned attacks above. Refuted at a configuration recording 2 (gold "
            "forwards 2, the rival 1) — a second encode-obligation point distinct "
            "from the ignores-config witness. (Sibling: weak-const-coder.)"),
        "witness": _tester("encodeWithConfig", "{ iterationBudget := 2 }"),
    },
    {
        "id": "weak-e2e-rebinds-request",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. The end-to-end path REBINDS the read-only requested budget
        # to a constant and then threads THAT through the two steps, so both callee
        # obligations are satisfied on the value it actually used while the request
        # never reaches the solver. This is the carrier's live analogue of the
        # sibling's mandatory frame-mutation rival: the port recorded that class as
        # VACUOUS because there is no heap to overwrite, but the ATTACK it encodes —
        # satisfy the end-to-end pin on a value the impl substituted for the
        # read-only input — is expressible here by shadowing, and directive 5 is
        # exactly the rule it violates. Correct only when the request is 42.
        "module": _swap(
            _BASE, _E2E,
            "    let userBudget := 42\n"
            "    let cfg ← recordIterationBudget userBudget\n"
            "    let solverBudget ← encodeWithConfig cfg\n"
            "    return solverBudget"),
        "refinement": (
            "the faithful counterpart substitutes a fixed budget of its own for the "
            "one the user asked for and then threads that substitute faithfully — "
            "every step downstream is internally consistent, but the solver's "
            "iteration limit is decoupled from the request. The F2P (a small budget "
            "must force non-convergence, a large one must allow it) reads the "
            "solver's convergence, which now tracks 42 and not the configured "
            "value, so it does NOT resolve. Correct only at the single request "
            "equal to the substituted constant."),
        "rationale": (
            "REJECT from `solverBudget = userBudget`: the spec pins the forwarded "
            "value to the REQUEST, and rebinding `userBudget` in the impl does not "
            "change what the obligation quantifies over. Verifying would be "
            "SPEC-TOO-WEAK in the directive-5 direction — a read-only input the "
            "impl may substitute for, which is the sibling's #1 weakness class "
            "reaching this carrier by shadowing rather than by mutation. Refuted at "
            "userBudget 6 (gold returns 6, the rival 42) — a sixth end-to-end input "
            "distinct from every other reject point. (Sibling: weak-frame-mutation, "
            "re-expressed as input substitution; the goal the verifier was left "
            "with is `x_1 = userBudget` under `x.iterationBudget = 42`, i.e. the "
            "rejection is the unprovable pin, not a tactic gap.)"),
        "witness": _tester("configuredBudgetReachesSolver", "6"),
    },
    {
        "id": "weak-encode-f2p-echo",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. The sharpest near-miss on this surface: the encode step
        # forwards the configured budget CORRECTLY at exactly the two values the
        # F2P exercises and falls back on the fixed built-in default everywhere
        # else. It therefore passes the literal failing test while leaving the
        # behavior unfixed for every other budget a user may configure — the
        # test-echo evasion the existing constant rivals cannot detect, since they
        # are wrong AT the F2P points too.
        "module": _swap(
            _BASE, _ENC,
            "    let solverBudget :=\n"
            "      if cfg.iterationBudget = 1 then 1\n"
            "      else if cfg.iterationBudget = 2000 then 2000\n"
            "      else 1000\n"
            "    return solverBudget"),
        "refinement": (
            "the faithful counterpart special-cases the two budgets the failing "
            "test happens to use and otherwise lets the solver fall back on its "
            "fixed built-in default. That resolves the F2P and NOTHING else: the "
            "reported behavior is that a user-chosen budget must govern the solver, "
            "and under this impl every budget outside the tested pair is silently "
            "replaced. A patch shaped like this is the canonical test-fitting "
            "non-fix — it would pass the suite while the estimator still ignores "
            "the configuration the issue asks it to honor."),
        "rationale": (
            "REJECT from `solverBudget = cfg.iterationBudget`: the spec pins the "
            "forwarded value to the recorded budget on the WHOLE domain, not at the "
            "two tested points. Verifying would be SPEC-TOO-WEAK in the most "
            "dangerous direction available here — the spec would certify an impl "
            "that only agrees with the request where the test looks. Refuted at a "
            "configuration recording 12 (gold forwards 12, the rival 1000) — a "
            "THIRD encode-obligation point, chosen off the two special-cased values "
            "so the divergence is in the fallback arm. (No sibling analogue: the "
            "sibling's per-arm split is on the algorithm selector, a binder this "
            "carrier does not have; this attacks the value domain instead.)"),
        "witness": _tester("encodeWithConfig", "{ iterationBudget := 12 }"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling ships 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals — one of which is a mandatory
# frame-mutation rival) plus an EMPTY AXIOM lane (AXIOM_TESTS = []). The sibling
# contracts THREE functions over a full-permission mutable estimator field held
# at Acc(.,1/2), with an algorithm selector splitting the encode step into
# lasso_lars / lasso_cd arms and two @Pure answer-key constants (500, 1000) in
# its contract. This backend models the SAME threading of one value DEEPLY and
# CONCRETELY over an exact `Nat` carrier across three methods (record / encode /
# end-to-end), but:
#   * there is NO algorithm selector binder — the value flows the same way for
#     every solver, so the per-arm split collapses (the two arms of the sibling's
#     encode both return the supplied budget; there is nothing to attack per-arm
#     that the value rivals below do not already attack on the whole domain);
#   * there is NO @Pure answer-key constant — each `ensures` is an exact identity
#     to a method argument, so the "echo the oracle" rivals port as "return the
#     literal default" rivals refuted by the identity itself.
#
#   sibling case                  kind          -> here                          disposition
#   ----------------------------------------------------------------------------------------
#   pos-control-branch-reorder    soundness     -> pos-control-encode-direct     RE-SHAPED
#   pos-control-local-reshape     soundness     -> pos-control-record-named-local PORTED
#                                                   (+ pos-control-e2e-extra-local ADDED)
#   admiss-self-call              admissibility -> admiss-nondegenerate          RE-AIMED
#   weak-echo-lars-default        uniqueness    -> weak-e2e-builtin-default      PORTED (value echo)
#   weak-echo-coder-default       uniqueness    -> weak-record-drops-budget +    SPLIT
#                                                   weak-encode-ignores-config
#   weak-partial-domain-lasso-lars uniqueness   -> weak-e2e-offby1 +             PORTED
#                                                   weak-record-offby1 ADDED
#   weak-frame-mutation           uniqueness    -> weak-e2e-rebinds-request      RE-EXPRESSED
#                                                   (AUDIT: port had this VACUOUS)
#   weak-const-coder-ignores-arg  uniqueness    -> weak-encode-single-iteration  PORTED
#   (no sibling analogue)         uniqueness    -> weak-encode-f2p-echo          AUDIT-ADDED
#   AXIOM_TESTS (none)            axiom         -> (none)                        N/A (G-AX)
#
# 5 uniqueness ported (one split into two, one re-expressed), 1 admissibility
# re-aimed, 1 soundness re-shaped + 1 ported + 1 added, 2 uniqueness added by the
# audit (the per-obligation off-by-one and the test-fitting near-miss); axiom lane
# empty (nothing to port). No sibling class is now dropped as vacuous except
# divergence, which the total lane makes unwritable.
#
# RE-SHAPED (pos-control-branch-reorder -> pos-control-encode-direct): the
#   sibling's positive is a two-arm branch on the algorithm selector, both arms
#   returning the budget. There is no selector binder here, so the maximally
#   different correct encode impl is a direct field return; the sibling's
#   local-reshape positive ports to pos-control-record-named-local, and a THIRD
#   positive (pos-control-e2e-extra-local) is ADDED so each of the three modeled
#   obligations is defended by a distinct faithful reshape (not just the two the
#   sibling reshaped).
# RE-AIMED (admiss-self-call -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped forwarded call meets its half-permission Requires. This backend has
#   no `require` and no permission surface, so that probe is degenerate; the
#   sharper residual risk is a DEGENERATE post-image, so the case is re-aimed to a
#   live in-region assert pinning the recorded budget at the two F2P probe values
#   (1 and 2000) and that they differ.
# SPLIT (weak-echo-coder-default -> weak-record-drops-budget +
#   weak-encode-ignores-config): the sibling's single "coder falls back to the
#   1000 default" rival corresponds here to TWO independent ways the value is
#   dropped — the construction step never storing it (weak-record-drops-budget,
#   attacking the record obligation) and the encode step never reading it
#   (weak-encode-ignores-config, attacking the encode obligation). Both are the
#   canonical wrong-answer default; splitting attacks two distinct obligations
#   that the sibling's single mutable-field model conflated.
# PORTED: weak-echo-lars-default (500) -> weak-e2e-builtin-default (the
#   end-to-end path returns the fixed default). weak-partial-domain-lasso-lars ->
#   weak-e2e-offby1 (there is no lasso_lars arm to isolate; the off-by-one is
#   attacked on the whole end-to-end domain at a nonzero budget). weak-const-coder
#   -> weak-encode-single-iteration (forward a hard-coded single iteration).
# RE-EXPRESSED (weak-frame-mutation -> weak-e2e-rebinds-request): the sibling's
#   MANDATORY frame rival overwrites the read-only estimator field (held at
#   Acc(.,1/2)) and is rejected for insufficient permission. That MECHANISM is
#   genuinely vacuous here — referential transparency means no heap write, no
#   aliasing, no permission to be insufficient. But the port concluded from this
#   that the whole CLASS has no carrier analogue and shipped nothing, and that was
#   wrong: the sibling's rival attacks directive 5 (satisfy the pin on a value the
#   impl substituted for the read-only input), and on this carrier the substitution
#   is a `let` that SHADOWS the binder. The rival threads its substitute through
#   both steps, so both callee `ensures` hold of the value it used, and the
#   end-to-end pin is still unprovable because the obligation quantifies over the
#   original `userBudget`. Measured: the verifier leaves exactly
#   `⊢ x_1 = userBudget` under `ensures_1 : x.iterationBudget = 42`, so the
#   rejection is the pin and not a tactic gap.
#
# DIVERGENCE / NON-TERMINATION: not present in the sibling, and closed by the
#   verifier rather than vacuous. This bundle is
#   `loom.semantics.termination "total"`, so a postcondition is claimed of ALL runs
#   and every loop owes a decreasing measure AND its descent. A diverging impl CAN
#   be written (a rival owns the whole impl region) and is REJECTED when it is:
#   measured on this cell, an unmeasured loop is refused at the `method`
#   declaration, and a loop carrying a non-decreasing measure is refused on
#   `case «decreasing_1: q»`, residual `q < q` (see the DIVERGENCE bullet in the
#   module docstring). There is no `partial` known-hole to contrast with: no velvet
#   bundle sets `partial`.
#
# BINDER / CLAUSE COVERAGE. Three independent `ensures` clauses, each an exact
#   identity, each DEFENDED (a positive verifies it) and ATTACKED (a reject rival
#   fails it):
#     * record   (`cfg.iterationBudget = userBudget`): defended by
#       pos-control-record-named-local; attacked by weak-record-drops-budget and
#       weak-record-offby1.
#     * encode   (`solverBudget = cfg.iterationBudget`): defended by
#       pos-control-encode-direct; attacked by weak-encode-ignores-config,
#       weak-encode-single-iteration and weak-encode-f2p-echo.
#     * e2e      (`solverBudget = userBudget`): defended by
#       pos-control-e2e-extra-local; attacked by weak-e2e-builtin-default,
#       weak-e2e-offby1 and weak-e2e-rebinds-request.
#   The two input binders are both varied by the reject witnesses (pts = 8):
#     * userBudget          over {5, 8, 3, 9, 6}  (record@5, record@8, e2e@3,
#                                                  e2e@9, e2e@6)
#     * cfg.iterationBudget over {7, 2, 12}       (encode@7, encode@2, encode@12)
#   No binder is pinned at one value across the reject set, and each obligation is
#   refuted at two or more DISTINCT points (record at 5 and 8; encode at 7, 2 and
#   12; e2e at 3, 9 and 6), so the record/encode/e2e clauses' dependence on their
#   binders is demonstrated and no near-miss shares a witness with a coarser rival.
#   The encode@12 point is deliberately OFF the two F2P-shaped values so the
#   test-fitting rival is refuted in its fallback arm.
#
# AUDIT PROBES THAT FOUND NO SPEC HOLE (recorded so the next reader does not
#   re-spend the builds). Six NEW wrong impls beyond the shipped rivals were built
#   against the frozen spec and ALL were rejected: encode forwarding
#   `cfg.iterationBudget + 1`; encode clamping to `max cfg.iterationBudget 1`
#   (wrong only at budget 0, the one point Nat truncation makes special); the
#   test-fitting echo; a record step flooring small requests at 10; and the
#   binder-shadowing substitution at both the record and the end-to-end site. The
#   last three were promoted to shipped cases. Four NEW correct reshapes were built
#   and ALL verified, so the spec is not too strong on impl shape: an end-to-end
#   path returning `userBudget` directly without consulting the configuration; a
#   record step storing `0 + userBudget`; one storing `(userBudget + 1) - 1`; and an
#   encode step routed through a redundant `if cfg.iterationBudget = 0` split.
#
# AXIOM_TESTS: empty. The bundle declares no axiom and no deep-model reference
#   (mapping.md §3: the changed steps are modeled deeply and concretely, validated
#   by G-CONF; the unchanged solver makes no consumed-property claim, so G-AX is
#   vacuous). The sibling's AXIOM_TESTS is likewise empty. This gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []

"""properties.py — G-PBT falsification battery for django__django-13343 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (three contracted methods over the field's storage
configuration, `total`-correctness + demonic choice):

  initField (arg : BackendArg) return (st : FieldState)
    ensures st = initState arg
  deconstructStorage (st : FieldState) return (e : BackendArg)
    ensures e = emit st
  roundTripStorage (arg : BackendArg) return (e : BackendArg)
    ensures e = emit (initState arg)

with ``initState`` and ``emit`` fully-unfolded ``def``s in the ``pure`` region
(no opaque callee, no consumed axiom). The three clauses together pin the
observable the issue is about — a supplied *producer* whose yielded backend is
not the ambient one must round-trip back AS that producer, not as the backend it
happened to yield:

  * CONSTRUCTION (initState) resolves the supplied argument to the retained
    configuration: an argument failing the presence test selects the ambient
    backend and retains nothing; a present concrete backend is kept as-is; a
    present producer is consulted once for its backend AND RETAINED
    (`origProducer := some p`). The RETENTION is the load-bearing sub-behavior:
    without it the later report has nothing to reconstruct the producer from.
  * DECONSTRUCTION (emit) reports how to re-supply the backend: the ambient
    backend as `omitted`; a producer-backed field AS ITS PRODUCER; any other as
    its concrete backend. The producer-report is the second load-bearing
    sub-behavior; the ambient-first guard (`st.backend = defaultBackend` checked
    BEFORE consulting `origProducer`) is a third — a producer that yields the
    ambient backend is reported as `omitted`, not as the producer.
  * LIFECYCLE (roundTripStorage) is `emit ∘ initState`, exercising both.

THE CARRIER IS FULLY TRANSPARENT and TOTAL. `Backend` / `Producer` /
`BackendArg` / `FieldState` all `deriving DecidableEq` over `Nat`/`Bool`, and
`initState` / `emit` compute on literals, so a witness reaches each method
through Velvet's own tester machinery (`extract_program_for M` gives `MExec`;
`derive_tester_for M` gives `MTester`, whose `= false` at a concrete input says
the extracted program's result violates that method's `ensures` there) and
closes by `decide`. Because the carrier computes, NO witness binds a hypothesis;
there is no opaque leaf, hence no carrier-conditioning and no
joint-satisfiability obligation. Each reject rival is a straight-line variant of
one method; the witness ELABORATES against the rival (its tester `decide`s to a
literal that provably differs from the model at the probed input) and FAILS
against the frozen solution (whose tester `decide`s the other way). Both halves
were checked out-of-band with ``scripts/lean_verify.sh`` (rival exit 0, gold
nonzero) for every reject case, and INDEPENDENTLY RE-DERIVED by a later audit
that also read gold's failure text: in every case it is `decide` proving
``<M>Tester <the concrete input> = false`` to BE FALSE — a semantic refutation of
the concrete claim, never a missing identifier, type error, unfolding failure, or
timeout.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame-mutation rivals (`frame-mutate-store`,
    `frame-mutate-producer-id`): its ``describe_store`` holds the field at
    ``Acc(field.*, 1/2)`` (read-only), so a rival that WRITES the field is
    rejected by the permission system before any postcondition reasoning. Lean
    and Velvet are referentially transparent: every input here is an immutable
    value, this bundle declares NO ``mut`` binder over any input, and there is no
    heap and no aliasing — so there is no read-only input to overwrite and the
    permission wall the sibling's rejection comes FROM does not exist. Not
    fabricated (per the porting map: this class is vacuous on Lean/Velvet).
    MEASURED rather than assumed by the independent audit: the two closest
    analogues were built and run — a deconstruction that shadows its input with a
    corrupted copy (``let st := { st with origProducer := none }``) and one that
    collapses the input's backend to the ambient value — and both ARE rejected
    (exit 1). They are rejected by the ordinary postcondition, however, at
    observables already covered by weak-decon-reports-backend-not-producer and
    weak-decon-drops-concrete-backend, so shipping them would add duplicate probe
    points under a misleading class name rather than cover anything new. Recorded
    as vacuous WITH that demonstration, not as "no probe is possible".
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``match`` / ``let`` / ``if``
    over immutable values, no loop and no recursion), so there is no control
    flow here to make diverge: a diverging rival cannot be obtained by mutating
    this body, it has to bring a loop of its own. When it does, the semantics
    refuse it. This bundle sets ``loom.semantics.termination "total"`` AND
    carries ``open TotalCorrectness``, and the ``open`` is the line that
    actually selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal
    (``case «decreasing_1: spin» ... ⊢ False``). Dropping the clause rather
    than faking it is refused even earlier, by the elaborator's own check
    (``Decreasing annotations are required in total correctness semantics``).
    So divergence neither applies to this impl nor discharges the ``ensures``
    clauses vacuously if a rival introduces it.
  * PARTIAL-DOMAIN / VALUE / UNIQUENESS — APPLIES; the heart of the port. Each
    nagini `describe_store`/`configure` rival re-expresses directly onto one
    clause of `initState`/`emit`, against the corresponding method here.
  * UNGROUNDED-ORACLE ECHO — N/A. `initState`/`emit` are total ``def``s over the
    methods' own inputs; there is no answer key to echo. Replaced by the honest
    positive controls (a cheapest direct impl + structurally-different reshapes).

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom`` and no
deep_model_references; `initState`/`emit` are deep models of the two CHANGED code
paths validated == the real `FileField` by conformance_check.py under G-CONF —
that is G-CONF/G-AX's job, and this gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-13343"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (a method's impl
# body between -- impl-start / -- impl-end, or a prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and every prove_correct STATEMENT
# byte-identical.
# ---------------------------------------------------------------------------

# initField's whole executable body (the construction dispatch).
_INIT_IMPL = """    match arg with
    | .omitted     => pure { backend := defaultBackend, origProducer := none }
    | .concrete b  =>
        if b.present then pure { backend := b, origProducer := none }
        else pure { backend := defaultBackend, origProducer := none }
    | .producer p  =>
        if p.present then pure { backend := p.yields, origProducer := some p }
        else pure { backend := defaultBackend, origProducer := none }"""

# deconstructStorage's whole executable body (the deconstruction dispatch).
_DECON_IMPL = """    if st.backend = defaultBackend then
      pure BackendArg.omitted
    else
      match st.origProducer with
      | some p => pure (BackendArg.producer p)
      | none   => pure (BackendArg.concrete st.backend)"""

# roundTripStorage's whole executable body (the lifecycle composite).
_RT_IMPL = """    let st ← initField arg
    let e ← deconstructStorage st
    return e"""

# The frozen proof scripts (each unique, elided from the spec view). The reshaped
# positive controls keep these AS-IS — loom_solve's `simp_all [initState]` /
# `simp_all [emit]` closes the residual regardless of the branch ordering. Reject
# rivals also keep them (they fail to close the wrong impl, which is exactly the
# intended rejection — but the WITNESS, not the tactic failure, is what the gate
# scores). Only the admissibility control retunes a proof (it adds an in-region
# `assert`, whose extra goal `decide` clears).
_RT_PROOF = "prove_correct roundTripStorage by\n  loom_solve"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `<M>Tester <args…> = false` says the extracted program's result violates
# ---- method M's `ensures` at that concrete input. Checked in a file whose
# ---- `prove_correct` blocks have been stripped, so no tactic script can mask the
# ---- verdict. Every argument is a concrete literal over a DecidableEq carrier so
# ---- `decide` reduces the (straight-line) extracted rival program; the frozen
# ---- dispatch `decide`s the other way, so the same witness fails on gold — the
# ---- required discrimination. No opaque leaf ⇒ no bound hypothesis ⇒ no
# ---- joint-satisfiability obligation.
def _tester(method, body):
    return ("extract_program_for %s\n"
            "prove_precondition_decidable_for %s\n"
            "prove_postcondition_decidable_for %s\n"
            "derive_tester_for %s\n\n" % (method, method, method, method)) + body


def _witness(method, arg):
    return _tester(
        method,
        "example : %sTester %s = false := by\n  decide\n" % (method, arg))


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen branch/statement FORM).
    # =====================================================================

    # ---- initField reshaped: pull the presence `if` inside `pure` (a single
    # ---- `pure (if … then … else …)` per arm) instead of two `pure` tails.
    # ---- Same construction on every input; `st = initState arg` still discharges
    # ---- under the frozen `loom_solve <;> simp_all [initState]`.
    {
        "id": "pos-control-init-reshaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INIT_IMPL,
            "    match arg with\n"
            "    | .omitted     => pure { backend := defaultBackend, origProducer := none }\n"
            "    | .concrete b  =>\n"
            "        pure (if b.present then { backend := b, origProducer := none }\n"
            "              else { backend := defaultBackend, origProducer := none })\n"
            "    | .producer p  =>\n"
            "        pure (if p.present then { backend := p.yields, origProducer := some p }\n"
            "              else { backend := defaultBackend, origProducer := none })"),
        "rationale": (
            "structurally different CORRECT reshape of the construction dispatch: "
            "each arm's presence `if` is pulled inside a single `pure`, keeping the "
            "retained configuration identical on every input, so `st = initState "
            "arg` still discharges under the frozen proof. A faithful reshape MUST "
            "verify, else the clause is over-fit to the branch FORM => "
            "SPEC-TOO-STRONG. (Sibling: pos-control-configure-reshaped.)"),
    },

    # ---- deconstructStorage reshaped: match on origProducer FIRST, testing the
    # ---- ambient-backend guard inside each arm. Observationally identical (the
    # ---- ambient case still reports `omitted` in both arms); `e = emit st`
    # ---- discharges under the frozen `loom_solve <;> simp_all [emit]`.
    {
        "id": "pos-control-decon-reshaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _DECON_IMPL,
            "    match st.origProducer with\n"
            "    | some p =>\n"
            "        if st.backend = defaultBackend then pure BackendArg.omitted\n"
            "        else pure (BackendArg.producer p)\n"
            "    | none   =>\n"
            "        if st.backend = defaultBackend then pure BackendArg.omitted\n"
            "        else pure (BackendArg.concrete st.backend)"),
        "rationale": (
            "structurally different CORRECT reshape of the deconstruction dispatch: "
            "the retained-producer match is lifted outside the ambient-backend "
            "guard, but the ambient case still reports `omitted` in BOTH arms, so "
            "the reported argument is identical on every field and `e = emit st` "
            "still discharges under the frozen proof. A faithful reshape MUST "
            "verify, else the clause is over-fit to the branch FORM => "
            "SPEC-TOO-STRONG. (Sibling: pos-control-describe-reordered.)"),
    },

    # ---- roundTripStorage direct: return the grounded model `emit (initState
    # ---- arg)` with no method calls — maximally structurally different from the
    # ---- gold two-step lifecycle. Also the honest no-ungrounded-echo control:
    # ---- `emit ∘ initState` IS the real work, so a direct return is correct, not
    # ---- a cheat; any wrong constant/echo fails `e = emit (initState arg)`.
    {
        "id": "pos-control-roundtrip-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RT_IMPL,
            "    return emit (initState arg)"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded composite "
            "`emit (initState arg)` directly (no method calls). `e` IS that model, "
            "so `e = emit (initState arg)` holds on the whole domain and the frozen "
            "`loom_solve` closes it. If this failed to verify the lifecycle clause "
            "would be over-fit to the call-sequence shape (SPEC-TOO-STRONG). Also "
            "the no-echo control: the model is the real work, so a direct return is "
            "correct, not an ungrounded answer-key echo."),
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling self-calls `configure` on an F2P-shaped
    # producer input to prove its `Requires` admit it. This backend declares NO
    # precondition (pre-conditions region empty), so there is no precondition to
    # admit; and the post-images are total functions, so each `ensures` is
    # satisfiable everywhere by construction. The residual admissibility risk is
    # that the post-image is DEGENERATE at the interesting point — a spec no impl
    # distinguishes reads exactly like one every impl meets. This case discharges
    # an in-region `assert`, at three fully-concrete F2P-shaped inputs, that the
    # lifecycle post-image is NON-DEGENERATE: a present producer round-trips AS
    # that producer (the new behaviour), a present concrete backend as itself, an
    # omitted argument as omitted — three genuinely distinct outcomes. The impl is
    # otherwise the gold lifecycle, so `e = emit (initState arg)` still verifies;
    # the proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-roundtrip-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _RT_IMPL,
                "    -- Non-degeneracy: the lifecycle distinguishes the three supply\n"
                "    -- shapes at representative inputs — a present producer round-trips\n"
                "    -- AS that producer (not the backend it yields), a present concrete\n"
                "    -- backend as itself, an omitted argument as omitted.\n"
                "    assert (with_name_prefix `admiss (\n"
                "      emit (initState (BackendArg.producer ⟨2, ⟨1, true⟩, true⟩))\n"
                "        = BackendArg.producer ⟨2, ⟨1, true⟩, true⟩ ∧\n"
                "      emit (initState (BackendArg.concrete ⟨1, true⟩))\n"
                "        = BackendArg.concrete ⟨1, true⟩ ∧\n"
                "      emit (initState BackendArg.omitted) = BackendArg.omitted))\n"
                "    let st ← initField arg\n"
                "    let e ← deconstructStorage st\n"
                "    return e"),
            _RT_PROOF,
            "prove_correct roundTripStorage by\n  loom_solve <;> decide"),
        "rationale": (
            "the lifecycle post-image is satisfiable AND non-degenerate at the "
            "F2P-shaped inputs: a present producer must round-trip AS that producer "
            "(the behaviour the fix adds — NOT the backend it yields), a present "
            "concrete backend as itself, an omitted argument as omitted — three "
            "distinct outcomes. The in-region assert must discharge (else the "
            "obligation is degenerate); the lifecycle is kept so `e = emit (initState "
            "arg)` still verifies. (Sibling: admiss-configure-producer-input, "
            "re-aimed from precondition admissibility to post-image non-degeneracy "
            "since this backend has no `require` clause and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a straight-line variant of ONE method with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================

    # ---- CONSTRUCTION / retention: a present producer is consulted for its
    # ---- backend but NOT retained (origProducer stays none). This is the literal
    # ---- gold pre-image at the construction site: the field forgets it was
    # ---- supplied a producer, so a later deconstruction has nothing to report the
    # ---- producer from and emits the evaluated backend instead.
    {
        "id": "weak-init-drops-producer-retention",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _INIT_IMPL,
            "    match arg with\n"
            "    | .omitted     => pure { backend := defaultBackend, origProducer := none }\n"
            "    | .concrete b  =>\n"
            "        if b.present then pure { backend := b, origProducer := none }\n"
            "        else pure { backend := defaultBackend, origProducer := none }\n"
            "    | .producer p  =>\n"
            "        if p.present then pure { backend := p.yields, origProducer := none }\n"
            "        else pure { backend := defaultBackend, origProducer := none }"),
        "refinement": (
            "this is the pre-change construction behaviour: a supplied producer is "
            "consulted for its backend but no reference to the producer itself is "
            "retained. A faithful counterpart that dropped the producer-retention "
            "step would leave the field with nothing to reconstruct the producer "
            "from, so deconstruction inlines the evaluated backend instead of "
            "returning the original callable — exactly the bug the change fixes. "
            "The failing scenario that asserts the deconstructed value IS the "
            "original callable would get the evaluated backend, so it would NOT "
            "resolve. Correct on omitted and concrete inputs (a "
            "producer-sub-domain break)."),
        "rationale": (
            "REJECT from `st = initState arg` (CONSTRUCTION/retention): on a present "
            "producer `initState` sets `origProducer := some p`, but the rival "
            "leaves it `none`. Verifying would be SPEC-TOO-WEAK (producer retention "
            "unpinned at the construction site). Refuted at a present producer "
            "`BackendArg.producer ⟨2, ⟨1, true⟩, true⟩` — varies `arg` to the "
            "producer shape at present=true. (Sibling: "
            "uniqueness-configure-records-evaluated-as-producer, aimed at the "
            "construction site.)"),
        "witness": _witness("initField",
                            "(BackendArg.producer ⟨2, ⟨1, true⟩, true⟩)"),
    },

    # ---- CONSTRUCTION / spurious retention on the concrete arm: a present
    # ---- CONCRETE backend (no producer supplied) is recorded WITH a fabricated
    # ---- producer. Mirror of the nagini `configure-scribbles-producer-id` rival
    # ---- (writing a spurious producer record when no callable was supplied).
    {
        "id": "weak-init-scribbles-producer-on-concrete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _INIT_IMPL,
            "    match arg with\n"
            "    | .omitted     => pure { backend := defaultBackend, origProducer := none }\n"
            "    | .concrete b  =>\n"
            "        if b.present then pure { backend := b, origProducer := some ⟨b.handle, b, true⟩ }\n"
            "        else pure { backend := defaultBackend, origProducer := none }\n"
            "    | .producer p  =>\n"
            "        if p.present then pure { backend := p.yields, origProducer := some p }\n"
            "        else pure { backend := defaultBackend, origProducer := none }"),
        "refinement": (
            "a faithful counterpart that recorded a producer reference even when a "
            "CONCRETE backend was supplied would make deconstruction report a "
            "spurious producer instead of the supplied backend for every "
            "concrete-storage field: reconstructing such a field would consult a "
            "value that was never a producer. NOT TEST-VISIBLE, and the manifest "
            "does not claim otherwise: the shipped scenarios construct a field "
            "from a producer (whose arm this rival leaves intact) or read the "
            "resolved backend without deconstructing, so this defect alone would "
            "still resolve. It is nonetheless a genuine violation of the frozen "
            "obligation — the modeled construction pins `origProducer := none` on "
            "the concrete arm because that is what the real configuration path "
            "leaves behind — and the spec is deliberately stronger than the "
            "scenario set here, which preserves `verify ⟹ resolved` (a spec that "
            "pins MORE than the tests observe never admits a non-resolving impl). "
            "Correct on omitted and on genuine producers (a concrete-sub-domain "
            "break)."),
        "rationale": (
            "REJECT from `st = initState arg` (CONSTRUCTION): on a present concrete "
            "backend `initState` retains `origProducer := none`, but the rival "
            "records `some ⟨…⟩`. Verifying would be SPEC-TOO-WEAK (the no-producer "
            "invariant on the concrete arm unpinned). Refuted at a present concrete "
            "backend `BackendArg.concrete ⟨1, true⟩` — varies `arg` to the concrete "
            "shape, the input the retention rival above agrees with gold on. "
            "(Sibling: uniqueness-configure-scribbles-producer-id-nonproducer.)"),
        "witness": _witness("initField", "(BackendArg.concrete ⟨1, true⟩)"),
    },

    # ---- CONSTRUCTION / presence test ignored on the producer arm: a producer
    # ---- that FAILS the presence test is nonetheless consulted and retained.
    # ---- This varies the `present` binder — the falsy-storage corner (mapping.md)
    # ---- that every other rival holds at present=true.
    {
        "id": "weak-init-ignores-presence-on-producer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _INIT_IMPL,
            "    match arg with\n"
            "    | .omitted     => pure { backend := defaultBackend, origProducer := none }\n"
            "    | .concrete b  =>\n"
            "        if b.present then pure { backend := b, origProducer := none }\n"
            "        else pure { backend := defaultBackend, origProducer := none }\n"
            "    | .producer p  =>\n"
            "        pure { backend := p.yields, origProducer := some p }"),
        "refinement": (
            "a faithful counterpart that skipped the pre-existing presence test on "
            "a supplied callable would consult and retain a callable that should "
            "have been discarded (a value that does not count as supplied selects "
            "the ambient backend and records nothing). The construction would then "
            "keep a store the field must treat as absent, and deconstruction would "
            "emit a producer where the modeled behaviour requires the ambient "
            "default. NOT TEST-VISIBLE (no shipped scenario supplies a value that "
            "fails the presence test), and the manifest does not claim otherwise; "
            "the presence arm is nonetheless part of the frozen obligation, and "
            "conformance of this corner against the real configuration path is "
            "G-CONF's lane (mapping.md records it as a fuzzed corner). A spec that "
            "pins this arm is stronger than the scenario set, which preserves "
            "`verify ⟹ resolved`. Correct on every present input (a "
            "presence-sub-domain break)."),
        "rationale": (
            "REJECT from `st = initState arg` (CONSTRUCTION/presence): on a "
            "NOT-present producer `initState` selects `{ defaultBackend, none }`, "
            "but the rival consults and retains it. Verifying would be "
            "SPEC-TOO-WEAK (the presence test unpinned on the producer arm). Refuted "
            "at a not-present producer `BackendArg.producer ⟨2, ⟨1, true⟩, false⟩` — "
            "the ONLY witness that drives the `present` binder to false, the "
            "falsy-storage corner no other rival probes. (No direct nagini sibling; "
            "the sibling folds presence into the field's pre-existing behaviour — "
            "ADDED to vary the presence binder.)"),
        "witness": _witness("initField",
                            "(BackendArg.producer ⟨2, ⟨1, true⟩, false⟩)"),
    },

    # ---- DECONSTRUCTION / the literal reported bug: a producer-backed field
    # ---- reports its concrete backend instead of the retained producer. This is
    # ---- the exact issue — deconstruct inlines the evaluated store, not the
    # ---- callable — introduced at the deconstruction site.
    {
        "id": "weak-decon-reports-backend-not-producer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECON_IMPL,
            "    if st.backend = defaultBackend then\n"
            "      pure BackendArg.omitted\n"
            "    else\n"
            "      pure (BackendArg.concrete st.backend)"),
        "refinement": (
            "this is the gold pre-image at the deconstruction site: a producer-"
            "backed field reports the concrete backend the producer yielded rather "
            "than the producer itself. The failing scenario that asserts the "
            "deconstructed value IS the original callable would get the evaluated "
            "backend (a different object), so `assertIs` fails — the exact verify-"
            "does-not-imply-resolve break the spec exists to block. Correct on "
            "ambient and on concrete-backed fields (a producer-sub-domain break)."),
        "rationale": (
            "REJECT from `e = emit st` (DECONSTRUCTION/producer report): when a "
            "producer is retained on a non-ambient backend `emit` reports "
            "`BackendArg.producer p`, but the rival reports `BackendArg.concrete "
            "st.backend`. Verifying would be SPEC-TOO-WEAK (the producer report "
            "unpinned) — the very bug the spec must sense. Refuted at "
            "`{ backend := ⟨1, true⟩, origProducer := some ⟨2, ⟨1, true⟩, true⟩ }` "
            "— varies `st` to a producer-backed non-ambient field. (Sibling: "
            "uniqueness-producer-returns-evaluated-store.)"),
        "witness": _witness(
            "deconstructStorage",
            "{ backend := ⟨1, true⟩, origProducer := some ⟨2, ⟨1, true⟩, true⟩ }"),
    },

    # ---- DECONSTRUCTION / concrete-backed field wrongly reported as omitted:
    # ---- a non-ambient backend with NO producer reports `omitted` instead of the
    # ---- concrete backend. Attacks the concrete arm of `emit`.
    {
        "id": "weak-decon-drops-concrete-backend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECON_IMPL,
            "    if st.backend = defaultBackend then\n"
            "      pure BackendArg.omitted\n"
            "    else\n"
            "      match st.origProducer with\n"
            "      | some p => pure (BackendArg.producer p)\n"
            "      | none   => pure BackendArg.omitted"),
        "refinement": (
            "a faithful counterpart that reported nothing for a concrete-backed "
            "field would omit the storage argument for a field configured with an "
            "explicit non-default backend, so reconstructing it would silently fall "
            "back to the ambient default and lose the configured location. NOT "
            "TEST-VISIBLE on its own (the shipped scenarios that deconstruct do so "
            "for a producer-backed field, whose arm this rival leaves intact), and "
            "the manifest does not claim otherwise; it is still a genuine violation "
            "of the frozen obligation, which pins the concrete report because that "
            "is the real deconstruction behaviour for an explicitly-configured "
            "field. The spec pinning MORE than the scenario set observes preserves "
            "`verify ⟹ resolved`. Correct on ambient and on producer-backed fields "
            "(a concrete-sub-domain break)."),
        "rationale": (
            "REJECT from `e = emit st` (DECONSTRUCTION/concrete report): a non-"
            "ambient backend with no producer must be reported `BackendArg.concrete "
            "st.backend`, but the rival reports `BackendArg.omitted`. Verifying "
            "would be SPEC-TOO-WEAK (the concrete report unpinned). Refuted at "
            "`{ backend := ⟨1, true⟩, origProducer := none }` — varies `st` to a "
            "concrete-backed field (origProducer none), the sub-domain the "
            "producer-report rival agrees with gold on, so the two do NOT share a "
            "witness. (Sibling: partial-domain-nonproducer-returns-producer-id.)"),
        "witness": _witness(
            "deconstructStorage",
            "{ backend := ⟨1, true⟩, origProducer := none }"),
    },

    # ---- DECONSTRUCTION / ambient-first guard dropped: a producer that yields
    # ---- the AMBIENT backend is reported as that producer instead of `omitted`.
    # ---- Attacks the producer-yields-default corner (mapping.md §2): the report
    # ---- must key off the resolved backend's identity, not the mere presence of
    # ---- a retained producer.
    {
        "id": "weak-decon-ignores-ambient-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECON_IMPL,
            "    match st.origProducer with\n"
            "    | some p => pure (BackendArg.producer p)\n"
            "    | none   =>\n"
            "      if st.backend = defaultBackend then pure BackendArg.omitted\n"
            "      else pure (BackendArg.concrete st.backend)"),
        "refinement": (
            "a faithful counterpart that consulted the retained producer BEFORE "
            "checking whether the resolved backend is the ambient one would report "
            "a producer for a field whose backend is the ambient default (a "
            "callable that evaluates to the default). The real guard keys off the "
            "backend's identity-vs-default, not the presence of a callable, and "
            "emits NO storage argument in that case; reporting the producer instead "
            "would round-trip a field that must deconstruct with no storage "
            "argument at all. NOT TEST-VISIBLE (no shipped scenario supplies a "
            "producer that yields the ambient backend), and the manifest does not "
            "claim otherwise — mapping.md §2 records this as the "
            "producer-yields-default corner that G-CONF fuzzes against the real "
            "path. Pinning it makes the spec stronger than the scenario set, which "
            "preserves `verify ⟹ resolved`. Correct on every non-ambient field (an "
            "ambient-corner break)."),
        "rationale": (
            "REJECT from `e = emit st` (DECONSTRUCTION/ambient-first guard): `emit` "
            "checks `st.backend = defaultBackend` BEFORE consulting `origProducer`, "
            "so a producer-backed field whose backend IS ambient reports `omitted`; "
            "the rival reports `BackendArg.producer p`. Verifying would be "
            "SPEC-TOO-WEAK (the ambient-first guard unpinned). Refuted at "
            "`{ backend := defaultBackend, origProducer := some ⟨2, defaultBackend, "
            "true⟩ }` — the ONLY witness driving `st.backend` to the ambient value "
            "WITH a retained producer, a corner no other rival reaches. (No direct "
            "nagini sibling — this corner is specific to the identity-vs-default "
            "guard modeled here; ADDED to cover the ambient-first clause.)"),
        "witness": _witness(
            "deconstructStorage",
            "{ backend := defaultBackend, origProducer := some ⟨2, defaultBackend, true⟩ }"),
    },

    # ---- LIFECYCLE / composite break: the round-trip returns the resolved
    # ---- concrete backend directly, bypassing the producer report entirely. The
    # ---- end-to-end analogue of the reported bug, attacking the composite clause.
    {
        "id": "weak-roundtrip-inlines-backend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RT_IMPL,
            "    return BackendArg.concrete (initState arg).backend"),
        "refinement": (
            "this is the observable bug end-to-end: construct from a supplied "
            "producer, then report the resolved backend inline instead of the "
            "original producer. The F2P scenario that constructs with a callable "
            "and asserts the deconstructed value IS that callable would get the "
            "evaluated backend (a different object), so `assertIs` fails — the exact "
            "verify-does-not-imply-resolve break. Wrong on the producer sub-domain "
            "(reports the yielded backend, not the producer) — the sub-domain the "
            "witness probes."),
        "rationale": (
            "REJECT from `e = emit (initState arg)` (LIFECYCLE): on a present "
            "producer the composite must report `BackendArg.producer p`, but the "
            "rival reports `BackendArg.concrete p.yields`. Verifying would be "
            "SPEC-TOO-WEAK (the end-to-end producer round-trip unpinned). Refuted at "
            "a present producer `BackendArg.producer ⟨2, ⟨1, true⟩, true⟩` — varies "
            "`arg` at the composite obligation, distinct from the per-method rivals "
            "above. (Sibling: the composite the issue's F2P test exercises.)"),
        "witness": _witness("roundTripStorage",
                            "(BackendArg.producer ⟨2, ⟨1, true⟩, true⟩)"),
    },

    # ---- LIFECYCLE / concrete arm dropped: the round-trip always reports
    # ---- `omitted`, so a field configured with an explicit concrete backend
    # ---- round-trips to the ambient default. Varies the composite's `arg` binder
    # ---- to the CONCRETE shape (distinct from the producer input above), so the
    # ---- roundTrip obligation's dependence on `arg` is genuinely probed.
    {
        "id": "weak-roundtrip-always-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RT_IMPL,
            "    return BackendArg.omitted"),
        "refinement": (
            "a faithful counterpart that always reported nothing would round-trip a "
            "field configured with an explicit concrete backend to the ambient "
            "default, dropping the supplied storage entirely — and, because it "
            "reports `omitted` on EVERY input, it also loses the producer the "
            "failing scenario asserts is returned, so it would NOT resolve. (The "
            "concrete leg the witness probes is not itself scenario-visible: no "
            "shipped scenario deconstructs a concrete-backed field. The rival is "
            "refuted at the concrete input to give it a point DISTINCT from "
            "weak-roundtrip-inlines-backend's, and the non-resolution above is "
            "carried by its producer-input behaviour.) Correct only on the "
            "genuinely-ambient input (a break on every supplied backend)."),
        "rationale": (
            "REJECT from `e = emit (initState arg)` (LIFECYCLE): on a present "
            "concrete backend the composite must report `BackendArg.concrete b`, but "
            "the rival reports `BackendArg.omitted`. Verifying would be "
            "SPEC-TOO-WEAK (the composite unpinned on the concrete sub-domain). "
            "Refuted at a present concrete backend `BackendArg.concrete ⟨1, true⟩` — "
            "varies the roundTrip `arg` binder to the concrete shape, a DISTINCT "
            "point from the producer input of weak-roundtrip-inlines-backend, so the "
            "battery demonstrates the composite's dependence on `arg`. (Sibling: the "
            "composite the issue's F2P test exercises, concrete-storage leg.)"),
        "witness": _witness("roundTripStorage",
                            "(BackendArg.concrete ⟨1, true⟩)"),
    },

    # ---- CONSTRUCTION / presence test ignored on the CONCRETE arm. Added by the
    # ---- independent audit: the battery drove the `present` binder to false on
    # ---- the PRODUCER arm only, leaving the concrete arm's presence guard
    # ---- unattacked, so a rival that keeps a not-present concrete backend was
    # ---- unprobed. Refuted at `concrete ⟨1, false⟩`, an input no other case
    # ---- reaches.
    {
        "id": "weak-init-ignores-presence-on-concrete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _INIT_IMPL,
            "    match arg with\n"
            "    | .omitted     => pure { backend := defaultBackend, origProducer := none }\n"
            "    | .concrete b  =>\n"
            "        pure { backend := b, origProducer := none }\n"
            "    | .producer p  =>\n"
            "        if p.present then pure { backend := p.yields, origProducer := some p }\n"
            "        else pure { backend := defaultBackend, origProducer := none }"),
        "refinement": (
            "a faithful counterpart that skipped the pre-existing presence test on "
            "a supplied concrete backend would retain a value the field must treat "
            "as absent, so the field would report that value back instead of "
            "reporting nothing. NOT TEST-VISIBLE (no shipped scenario supplies a "
            "concrete backend that fails the presence test); mapping.md records "
            "the corner as one G-CONF fuzzes against the real configuration path. "
            "Pinning it makes the spec stronger than the scenario set, which "
            "preserves `verify ⟹ resolved`. Correct on every present input and on "
            "both other arms (a presence-sub-domain break on the concrete arm)."),
        "rationale": (
            "REJECT from `st = initState arg` (CONSTRUCTION/presence, concrete "
            "arm): on a NOT-present concrete backend `initState` selects "
            "`{ defaultBackend, none }`, but the rival keeps the backend. "
            "Verifying would be SPEC-TOO-WEAK (the presence test unpinned on the "
            "concrete arm — the sibling of "
            "weak-init-ignores-presence-on-producer, which pins only the producer "
            "arm). Refuted at `BackendArg.concrete ⟨1, false⟩`, the only case "
            "driving `present` to false on a CONCRETE argument. (ADDED by the "
            "independent audit: the concrete arm's presence guard was the "
            "unattacked half of the falsy-storage corner.)"),
        "witness": _witness("initField", "(BackendArg.concrete ⟨1, false⟩)"),
    },

    # ---- CONSTRUCTION / spurious retention on the OMITTED arm. Added by the
    # ---- independent audit: the omitted arm was defended but never attacked, so
    # ---- nothing pinned that an omitted argument retains NOTHING. Refuted at
    # ---- `BackendArg.omitted`, an input no other case reaches.
    {
        "id": "weak-init-scribbles-producer-on-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _INIT_IMPL,
            "    match arg with\n"
            "    | .omitted     =>\n"
            "        pure { backend := defaultBackend, origProducer := some ⟨0, defaultBackend, true⟩ }\n"
            "    | .concrete b  =>\n"
            "        if b.present then pure { backend := b, origProducer := none }\n"
            "        else pure { backend := defaultBackend, origProducer := none }\n"
            "    | .producer p  =>\n"
            "        if p.present then pure { backend := p.yields, origProducer := some p }\n"
            "        else pure { backend := defaultBackend, origProducer := none }"),
        "refinement": (
            "a faithful counterpart that fabricated a producer record when NOTHING "
            "was supplied would leave every default-configured field carrying a "
            "reference that was never given to it. Here the ambient-first report "
            "guard masks it end-to-end (the deconstruction still reports "
            "`omitted`), so it is NOT scenario-visible on its own — but it is a "
            "genuine violation of the construction obligation, which pins "
            "`origProducer := none` on the omitted arm, and it would become "
            "observable in composition with any relaxation of that guard. Pinning "
            "it is strictly stronger than the scenario set, preserving "
            "`verify ⟹ resolved`. Correct on both other arms (an omitted-arm "
            "break)."),
        "rationale": (
            "REJECT from `st = initState arg` (CONSTRUCTION/omitted arm): on "
            "`BackendArg.omitted` `initState` retains `origProducer := none`, but "
            "the rival records `some ⟨…⟩`. Verifying would be SPEC-TOO-WEAK (the "
            "retain-nothing invariant on the omitted arm unpinned). Refuted at "
            "`BackendArg.omitted` — the ONLY case whose witness probes the omitted "
            "argument, which every other rival agrees with gold on. (ADDED by the "
            "independent audit: the omitted arm was defended by the positive "
            "controls but attacked by nothing.)"),
        "witness": _witness("initField", "BackendArg.omitted"),
    },

    # ---- DECONSTRUCTION / the ambient field reported as a concrete backend.
    # ---- Added by the independent audit: every emit rival probed a non-ambient
    # ---- field or an ambient field WITH a retained producer, so the plain
    # ---- ambient-and-nothing-retained field — the default-configured field, the
    # ---- most common one in practice — was unattacked.
    {
        "id": "weak-decon-reports-ambient-as-concrete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECON_IMPL,
            "    match st.origProducer with\n"
            "    | some p =>\n"
            "        if st.backend = defaultBackend then pure BackendArg.omitted\n"
            "        else pure (BackendArg.producer p)\n"
            "    | none   => pure (BackendArg.concrete st.backend)"),
        "refinement": (
            "a faithful counterpart that applied the ambient-vs-configured guard "
            "only to producer-backed fields would report the ambient backend as an "
            "explicitly-supplied one for every default-configured field, so every "
            "such field would round-trip carrying a storage argument it was never "
            "given. That is a broad, real regression on the most common field "
            "shape — a field with no storage configured — and it breaks the "
            "modeled deconstruction's first clause, which reports the ambient "
            "backend as `omitted`. Correct on producer-backed fields and on "
            "non-ambient concrete fields (an ambient-arm break)."),
        "rationale": (
            "REJECT from `e = emit st` (DECONSTRUCTION/ambient report): `emit` "
            "reports `BackendArg.omitted` whenever `st.backend = defaultBackend`, "
            "including with nothing retained; the rival reports "
            "`BackendArg.concrete defaultBackend`. Verifying would be "
            "SPEC-TOO-WEAK (the ambient report unpinned on the "
            "nothing-retained arm). Refuted at "
            "`{ backend := defaultBackend, origProducer := none }` — the ONLY case "
            "probing an ambient field with nothing retained; "
            "weak-decon-ignores-ambient-guard probes the ambient field WITH a "
            "retained producer, so the two do NOT share a witness. (ADDED by the "
            "independent audit.)"),
        "witness": _witness(
            "deconstructStorage",
            "{ backend := defaultBackend, origProducer := none }"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 mandatory frame-mutation rivals, 4 uniqueness
# rivals) plus an EMPTY AXIOM lane (AXIOM_TESTS = []). The sibling contracts TWO
# functions — `configure` (full-permission field write) and `describe_store`
# (read-only, Acc(field.*, 1/2)) — over an integer-id field carrier. This backend
# models the SAME two code paths DEEPLY (`initState` = construction, `emit` =
# deconstruction) plus their composite (`roundTripStorage`) over structure /
# inductive carriers with object-identity handles, under total correctness.
#
#   sibling case                                       kind   -> here                                    disposition
#   ----------------------------------------------------------------------------------------------------------------------------
#   pos-control-describe-reordered                     sound  -> pos-control-decon-reshaped               PORTED (reshaped)
#   pos-control-configure-reshaped                     sound  -> pos-control-init-reshaped                PORTED (reshaped)
#   (no sibling; + roundTrip composite is new here)    sound  -> pos-control-roundtrip-direct             ADDED
#   admiss-configure-producer-input                    admiss -> admiss-roundtrip-nondegenerate           PORTED (re-aimed)
#   frame-mutate-store                                 uniq   -> (none)                                   VACUOUS
#   frame-mutate-producer-id                           uniq   -> (none)                                   VACUOUS
#   uniqueness-configure-records-evaluated-as-producer uniq   -> weak-init-drops-producer-retention       PORTED (re-expressed)
#   uniqueness-configure-scribbles-producer-id-nonprod uniq   -> weak-init-scribbles-producer-on-concrete PORTED
#   uniqueness-configure-flag-always-true              uniq   -> weak-init-ignores-presence-on-producer   PORTED (re-expressed)
#   uniqueness-producer-returns-evaluated-store        uniq   -> weak-decon-reports-backend-not-producer  PORTED (the reported bug)
#   partial-domain-nonproducer-returns-producer-id     uniq   -> weak-decon-drops-concrete-backend        PORTED (re-expressed)
#   (no sibling; identity-vs-default guard is new)     uniq   -> weak-decon-ignores-ambient-guard         ADDED
#   (no sibling; roundTrip composite is new here)      uniq   -> weak-roundtrip-inlines-backend           ADDED
#   (no sibling; roundTrip composite is new here)      uniq   -> weak-roundtrip-always-omitted            ADDED
#   (no sibling; audit-found gap)                      uniq   -> weak-init-ignores-presence-on-concrete   ADDED (audit)
#   (no sibling; audit-found gap)                      uniq   -> weak-init-scribbles-producer-on-omitted  ADDED (audit)
#   (no sibling; audit-found gap)                      uniq   -> weak-decon-reports-ambient-as-concrete   ADDED (audit)
#   AXIOM_TESTS (0)                                    -      -> (none)                                   DROPPED (G-AX)
#
# 6 ported, 7 added, 2 vacuous = 3 soundness + 1 admissibility + 11 uniqueness = 15 SPEC cases.
#
# AUDIT ADDITIONS (independent adversarial re-derivation of this battery). Three
#   arm/corner combinations were DEFENDED by a positive control but ATTACKED by
#   nothing, so the original 8 reject cases left them unpinned. Each was landed
#   as a real rival with a machine-checked witness (rival exit 0, gold exit 1,
#   gold's failure a semantic `decide` refutation naming the concrete input):
#     - weak-init-ignores-presence-on-concrete — the presence guard was pinned on
#       the producer arm only; the concrete arm's guard was unattacked. Witness at
#       `concrete ⟨1, false⟩`.
#     - weak-init-scribbles-producer-on-omitted — nothing pinned that an OMITTED
#       argument retains nothing. Witness at `BackendArg.omitted`.
#     - weak-decon-reports-ambient-as-concrete — every emit rival probed a
#       non-ambient field or an ambient field WITH a retained producer, leaving
#       the plain ambient/nothing-retained field (the default-configured field)
#       unattacked. Witness at `{ defaultBackend, none }`.
#   The audit also re-derived every original case: all 12 statements are
#   byte-identical to the frozen file (surgery confined to impl regions and
#   proof bodies), all 8 original witnesses rebuilt with rival exit 0 / gold
#   exit 1 and semantic gold failures, and the admissibility `assert` was shown
#   load-bearing by re-running it with a FALSE claim (build fails, exit 1). Six
#   new correct reshapes were checked against the spec and ALL verified (no
#   SPEC-TOO-STRONG hole); no wrong impl was found that the spec accepts (no
#   SPEC-TOO-WEAK hole). Four refinement paragraphs OVERCLAIMED scenario
#   visibility — they asserted a shipped scenario would fail for a defect no
#   shipped scenario exercises — and were corrected to say so explicitly while
#   keeping the (still valid) obligation-violation argument.
#
# PORTED (positives): the sibling's branch-reorder of `describe_store` (test the
#   producer flag first) ports as pos-control-decon-reshaped (match origProducer
#   first, ambient-guard inside each arm — observationally identical). The
#   sibling's flat-branch reshape of `configure` ports as pos-control-init-reshaped
#   (pull the presence `if` inside `pure`). Both keep the frozen proof (loom_solve
#   <;> simp_all [initState] / [emit]) with no retune — VERIFIED to build (exit 0).
# ADDED (pos-control-roundtrip-direct): this backend models the F2P composite
#   `deconstruct ∘ construct` as its own method, which the sibling has no
#   counterpart for (nagini contracts the two halves separately). The cheapest
#   honest impl returns `emit (initState arg)` directly — VERIFIED to build.
# PORTED (admissibility, re-aimed): the sibling proves its `Requires` admit an
#   F2P-shaped producer input via a self-call. This backend has NO `require`
#   clause and no permission surface, so precondition-admissibility is degenerate;
#   the case is re-aimed to post-image NON-DEGENERACY — an in-region assert that
#   the lifecycle yields three distinct outcomes (producer / concrete / omitted) at
#   representative inputs. VERIFIED to build (loom_solve <;> decide).
# PORTED (uniqueness): the four sibling rivals re-express DIRECTLY onto the
#   corresponding clause. `configure-records-evaluated-as-producer` and
#   `configure-flag-always-true` (both configuration-site defects) become
#   weak-init-drops-producer-retention (the literal pre-image: retain nothing) and
#   weak-init-ignores-presence-on-producer (the presence test dropped on the
#   producer arm). `configure-scribbles-producer-id-nonproducer` becomes
#   weak-init-scribbles-producer-on-concrete (a spurious producer recorded for a
#   concrete backend). `producer-returns-evaluated-store` (the reported bug) becomes
#   weak-decon-reports-backend-not-producer, and
#   partial-domain-nonproducer-returns-producer-id becomes
#   weak-decon-drops-concrete-backend. Each refinement carries over: a faithful
#   counterpart with that defect still mis-reports a field the fix requires to
#   round-trip correctly, so it would NOT resolve.
# ADDED (uniqueness): weak-decon-ignores-ambient-guard attacks the identity-vs-
#   default guard `emit` checks BEFORE consulting the producer (the
#   producer-yields-default corner, mapping.md §2) — no sibling counterpart because
#   nagini's `describe_store` keys off has_producer, not a resolved-backend-identity
#   guard. weak-roundtrip-inlines-backend attacks the composite clause directly.
# VACUOUS (frame-mutate-store, frame-mutate-producer-id): the sibling carries
#   these MANDATORY because `describe_store` holds the field at Acc(field.*, 1/2)
#   and a rival can illegally WRITE it. This backend is referentially transparent
#   and declares NO `mut` binder — every input is an immutable value with no heap
#   footprint — so there is no read-only input to overwrite and no substitute
#   probe. Not fabricated (porting map: vacuous on Lean/Velvet).
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``match`` / ``let`` / ``if`` over immutable
#   values, no loop and no recursion), so there is no control flow here to make
#   diverge: a diverging rival cannot be obtained by mutating this body, it has
#   to bring a loop of its own. When it does, the semantics refuse it. This
#   bundle sets ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal
#   (``case «decreasing_1: spin» ... ⊢ False``). Dropping the clause rather
#   than faking it is refused even earlier, by the elaborator's own check
#   (``Decreasing annotations are required in total correctness semantics``).
#   So divergence neither applies to this impl nor discharges the ``ensures``
#   clauses vacuously if a rival introduces it.
# AXIOM_TESTS: empty in the sibling; empty here. The bundle consumes no axiom
#   `ensures` (`initState`/`emit` are deep A-references validated == the real
#   FileField by conformance_check.py under G-CONF); the gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. Three obligations, each with one input binder:
#   initField/`arg : BackendArg`, deconstructStorage/`st : FieldState`,
#   roundTripStorage/`arg : BackendArg`. Every top-level clause is DEFENDED (a
#   positive per method) and ATTACKED (a rival per clause):
#     - initState CONSTRUCTION: defended by pos-control-init-reshaped; EVERY arm is
#       now attacked — producer retention (weak-init-drops-producer-retention),
#       producer presence (weak-init-ignores-presence-on-producer), concrete-arm
#       no-producer invariant (weak-init-scribbles-producer-on-concrete), concrete
#       presence (weak-init-ignores-presence-on-concrete), and the omitted arm's
#       retain-nothing invariant (weak-init-scribbles-producer-on-omitted).
#     - emit DECONSTRUCTION: defended by pos-control-decon-reshaped; EVERY arm is
#       now attacked — producer report (weak-decon-reports-backend-not-producer),
#       concrete report (weak-decon-drops-concrete-backend), ambient-first guard
#       with a retained producer (weak-decon-ignores-ambient-guard), and the
#       ambient report with nothing retained
#       (weak-decon-reports-ambient-as-concrete).
#     - roundTrip LIFECYCLE: defended by pos-control-roundtrip-direct and
#       admiss-roundtrip-nondegenerate; attacked by weak-roundtrip-inlines-backend
#       (producer arg) and weak-roundtrip-always-omitted (concrete arg).
#   Both INPUT BINDERS are varied by the reject witnesses:
#     * `arg : BackendArg` ranges over ALL THREE constructors — producer(true),
#       producer(false), concrete(true), concrete(false), and omitted — so the
#       `present` sub-field is driven to both values on BOTH value-carrying arms
#       (the falsy-storage corner of mapping.md), not just on the producer arm.
#     * `st : FieldState` ranges over all four (backend x origProducer) quadrants:
#       producer-backed non-ambient, concrete-backed non-ambient, producer-backed
#       AMBIENT, and ambient with nothing retained — so `origProducer` (some/none)
#       and `backend` (ambient/non-ambient) are varied INDEPENDENTLY.
#   The 11 reject witnesses probe 11 DISTINCT input points; no two rivals are
#   refuted at the same input (near-misses given their own discriminating point:
#   the producer-report and concrete-report rivals agree with gold on each other's
#   sub-domain and are separated accordingly; the two ambient rivals are separated
#   by whether a producer is retained; the two roundTrip rivals are probed at
#   producer vs concrete `arg`). pts = 11.
# WITNESS DISCRIMINATION (re-derived by the independent audit with two real builds
#   per reject case, not merely asserted): each witness ELABORATES against its
#   rival (exit 0) and FAILS against the frozen solution (exit 1). Gold's failure
#   is in every case the SEMANTIC form `Tactic 'decide' proved that the
#   proposition <M>Tester <the concrete input> = false is false` — i.e. gold's
#   tester is `true` at exactly the probed point while the rival's is `false`.
#   No unknown identifier, type error, unfolding failure, or timeout appears on
#   the gold side, so no rejection rests on a syntactic accident. No witness binds
#   a hypothesis (the carrier is fully transparent and total), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
# SPEC PROBES run by the audit and NOT shipped as cases (they found no hole, so
#   there is nothing to ship): six wrong impls beyond the shipped rivals were
#   checked against the frozen spec and ALL were rejected, including a
#   retained-but-not-consulted producer, an end-to-end presence bypass, and a
#   diverging `while true` loop (rejected with `Decreasing annotations are
#   required in total correctness semantics`, confirming the `total` setting is
#   load-bearing). Six correct reshapes were checked and ALL verified: the
#   grounded-model direct returns for initField and deconstructStorage, a
#   negated-presence-guard construction, a pair-match deconstruction, and two
#   alternative lifecycle call shapes. So the spec is neither too weak nor too
#   strong on the probed surface.
AXIOM_TESTS = []

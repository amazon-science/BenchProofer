"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26291 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed — the consumer spec view elides that region,
so ``markers.same_spec`` holds and the ``prove_correct computePlacement``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over two read-only inputs):

  computePlacement (ctx : Option Ctx) (host : Host)
      return (out : Except PlaceErr Region)
    ensures ∃ reg, out = Except.ok reg                                    (E1)
    ensures ctx = none → out = Except.ok (placeWith (hostContext host) host)  (E2)
    ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)        (E3)

An anchored child's placement region is computed by running a downstream
measure-and-position pipeline with a CONCRETE drawing context. ``ctx`` is the
supplied context, or absent when the caller has none; ``host`` is the container
the child is placed against and always carries a retrievable context of its own.
The three clauses are grounded in the two opaque, unchanged callees
``hostContext`` (the host's own context) and ``placeWith`` (the downstream region
computation given a concrete context) — directive 8: there is no single spec
answer-key an implementation could echo, since each clause pins a DIFFERENT
composition of the inputs with the callees. There is no ``require`` clause, so
the admitted domain is total — which does NOT retire the admissibility lane: on a
total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
unsatisfiable at an F2P-shaped input, and ``admiss-absent-context-satisfiable``
discharges the joint post-image at ``ctx = none`` by evaluation to rule that out.

Three INDEPENDENT top-level clauses, each load-bearing and each attacked below:
  (E1) the placement always yields a region (``Except.ok``) — the never-abandon
       frame. A body that reports the undefined-measurement error on any input
       fails here. This is the core of the fix: the absent-context path used to
       raise, and must now produce a region.
  (E2) an absent context runs the downstream with the HOST's own context, not
       an abandonment and not an arbitrary substitute.
  (E3) a present context is threaded to the downstream UNCHANGED — the supplied
       context, not the host's.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how a witness reaches the post-image.
``Ctx``, ``Host``, ``Region`` and the two callees ``hostContext`` / ``placeWith``
are ``axiom``-declared opaque with NO ``ensures``: they are A-consumed
UNCHANGED callees validated == the real callees by axiom_check.py (G-AX), NOT
contracts to attack. Two consequences shape every witness:

  * A ``decide`` on a literal cannot COMPUTE the result — it flows through the
    opaque ``placeWith``. And ``extract_program_for`` is unavailable: the method
    is ``noncomputable`` over opaque callees, so the extractor's generated ``def``
    fails the IR-compile check. So each witness states the refutation directly
    over the method's Hoare triple (``¬ triple True (computePlacement …) (fun out
    => …)``) — a ``Prop`` that is never IR-compiled and reduces cleanly for a
    straight-line rival under ``simp [triple, wp_pure]``.
  * Where the divergence is a WRONG REGION rather than a wrong outcome
    constructor, the witness CONDITIONS on the opaque carrier: it hypothesises
    that the two ``placeWith`` applications differ (``placeWith (hostContext host)
    host ≠ placeWith c host``) and concludes the triple fails. Against the FROZEN
    impl the same goal cannot close (gold threads the supplied context, so its
    triple HOLDS and ``¬ triple`` leaves ``⊢ False``), which is precisely why the
    witness FAILS on gold — a genuine discriminator, not a tautology. Each
    conditioning witness carries at most ONE hypothesis about a single opaque
    composition and is jointly satisfiable (``placeWith`` is opaque, so no
    ``False`` is derivable from it) — the gate's consistency probe cannot refute
    it. No ``sorry``/``admit``/``native_decide``/new ``axiom``.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS here, exactly as the nagini sibling
    itself reasoned (it noted there is NO read-only ``Acc(x,1/2)`` input to
    overwrite). This backend is referentially transparent: ``ctx`` and ``host``
    are immutable values, the method declares NO ``mut`` binder, there is no heap
    and no aliasing and no permission system. No read-only input to overwrite and
    no substitute probe to fabricate. Reported vacuous, not faked.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. The clauses pin distinct
    compositions of the two inputs with the opaque callees; no single answer-key
    exists for an impl to echo without threading the right context down the right
    branch. Honest positive controls stand in.
  * MEASUREMENT-COUNT / WRONG-HANDLE / PASS-AXES — see the accounting footer: the
    measurement-count observable is not modeled on this carrier (carrier
    narrowing), the wrong-handle attack folds into E3 (weak-ignore-supplied-
    context), and the pass-the-host-as-a-context attack is ILL-TYPED here
    (``Ctx`` and ``Host`` are distinct opaque types), so the Lean type discipline
    forbids the rival outright.
  * PARTIAL-DOMAIN / CONTROL-FLOW — APPLIES and carries the reject lane: rivals
    right on part of the domain but abandoning the absent-context path, echoing
    the host context on the present path, or reporting a refusal on the present
    path.

WITNESS PLACEMENT / BINDER COVERAGE. The ``ctx`` binder is moved across the
battery — ``none`` (weak-none-abandons) and ``some c`` (weak-ignore-supplied-
context, weak-present-refuses) — so the present/absent decision is probed on
both sides (pts across {ctx=none, ctx=some c}). The ``host`` binder is opaque and
cannot be moved to a second closed value (there is no closed ``Host`` term other
than a fresh universally-quantified one; a second would need a banned new
``axiom``), so every witness quantifies over an abstract ``host`` — the
documented opaque-carrier situation, and ``host`` participates in every witness's
refuted composition. All three clauses are attacked: E1 by weak-none-abandons
(none side) and weak-present-refuses (present side); E2 by weak-none-abandons; E3
by weak-ignore-supplied-context and weak-present-refuses.

AXIOM lane: DROPPED (the axiom lane is G-AX's job; this gate ignores
``AXIOM_TESTS``). ``hostContext`` / ``placeWith`` are A-consumed opaque callees
validated by axiom_check.py, not contracts this spec-lane manifest probes.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26291"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Spans the gold impl's leading comment and its code,
# ---- lies wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). A variant
# ---- replaces the ENTIRE behaviour (comment included) so no stale narration
# ---- survives. The spec (signature, `ensures`, docstring) and the
# ---- `prove_correct computePlacement` header are untouched, so same_spec holds
# ---- and the obligation survives with a byte-identical statement.
_GOLD_IMPL = (
    "    -- Obtain a concrete context before measuring: when one is supplied use it,\n"
    "    -- otherwise substitute the host's own context. Then run the unchanged\n"
    "    -- downstream pipeline with that concrete context. The substitution guards\n"
    "    -- the measurement against an absent context, so the placement always\n"
    "    -- produces a region instead of attempting an undefined measurement.\n"
    "    let chosen : Ctx :=\n"
    "      match ctx with\n"
    "      | some c => c\n"
    "      | none   => hostContext host\n"
    "    return Except.ok (placeWith chosen host)"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"
assert _BASE.count(_GOLD_IMPL) == 1, "impl anchor not unique; update _GOLD_IMPL"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl-region body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_asserted(assertion):
    """Frozen impl kept VERBATIM with `assertion` prepended inside the region.

    Used by the admissibility case: the method's own behaviour (and the frozen
    `prove_correct` tactic body) is untouched, so the three `ensures` still
    discharge exactly as they do for the frozen file, and the ONLY added goal is
    the assertion itself. That goal is live — a FALSE assertion of the same shape
    leaves `unsolved goals ... ⊢ ∃ out, ...` under the same frozen `loom_solve`
    (checked with a real build), so the case cannot pass by the assert being
    ignored.
    """
    return _swap(_BASE, _GOLD_IMPL, assertion + _GOLD_IMPL)


# ---- witness preamble. A witness reaches the post-image through the method's
# ---- Hoare triple `triple True (computePlacement …) (fun out => …)` (a Prop,
# ---- never IR-compiled — `extract_program_for` is unavailable because the
# ---- method is noncomputable over opaque callees). Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can
# ---- interfere. `simp [triple, wp_pure]` reduces the triple over a straight-line
# ---- rival; against gold the reduced goal cannot close (its triple HOLDS, so
# ---- `¬ triple` leaves `⊢ False`). No `axiom`/`sorry`/`native_decide`.
def _witness(head, ctx_arg, post, hyp=False):
    # `ctx_arg` is the `ctx` argument at the probed input ("none" / "(some c)").
    # `hyp=True` adds the conditioning hypothesis `h` to the simp set (used only
    # by the near-miss rival, whose refutation depends on the opaque inequality);
    # the unconditional witnesses close from the outcome constructor alone.
    simp = "[triple, wp_pure, h]" if hyp else "[triple, wp_pure]"
    return (
        f"example {head} :\n"
        f"    ¬ triple True (computePlacement {ctx_arg} host)\n"
        f"      (fun out => out = Except.ok ({post})) := by\n"
        "  unfold computePlacement\n"
        f"  simp {simp}\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — the direct nagini port of
    # pos-control-branch-reorder. A structurally-different but CORRECT impl:
    # instead of the gold "default-then-thread" shape, branch explicitly on the
    # supplied context and return one region per arm. Observationally identical
    # on every input; the frozen `loom_solve` still discharges all three clauses
    # (verified with a real build during authoring). MUST verify, else the spec
    # would be SPEC-TOO-STRONG on impl shape.
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Branch explicitly on whether a context is supplied and run the\n"
            "    -- downstream once per arm: the supplied context on the present arm,\n"
            "    -- the host's own context on the absent arm.\n"
            "    match ctx with\n"
            "    | some c => return Except.ok (placeWith c host)\n"
            "    | none   => return Except.ok (placeWith (hostContext host) host)"),
        "rationale": (
            "a structurally-different correct impl (an explicit two-arm branch, one "
            "downstream call per arm) yields the identical outcome on every input: "
            "on `some c` it returns `placeWith c host` (E3), on `none` it returns "
            "`placeWith (hostContext host) host` (E2), and both arms return "
            "`Except.ok` (E1). It adds no new proof obligation, so the frozen "
            "`loom_solve` still discharges all three clauses. Must verify (else "
            "SPEC-TOO-STRONG on impl shape)."),
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a second structurally-different CORRECT
    # impl: collapse the branch into a single downstream call whose context is
    # obtained by `Option.getD` (supplied context, else the host's). Same net
    # region on every input, different executable shape; the frozen `loom_solve`
    # still discharges it (verified with a real build). MUST verify.
    # =====================================================================
    {
        "id": "pos-control-getd-context",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Obtain the concrete context with a single defaulting operation\n"
            "    -- (the supplied context, else the host's own) and run the\n"
            "    -- downstream once with it.\n"
            "    return Except.ok (placeWith (ctx.getD (hostContext host)) host)"),
        "rationale": (
            "a correct reshape that obtains the concrete context with one "
            "defaulting operation `ctx.getD (hostContext host)` — definitionally "
            "`c` on `some c` and `hostContext host` on `none` — computes the "
            "identical region on every input, satisfying E1/E2/E3 with no new "
            "proof obligation, so the frozen `loom_solve` still discharges it. Must "
            "verify (else SPEC-TOO-STRONG on impl shape)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the direction PRECOND-TOO-STRONG lives in. The admitted
    # domain here is total (no `require`), so the nagini sibling's "a normal
    # input satisfies the precondition chain" reading has no analogue. The
    # analogue on a TOTAL carrier is the one that still bites: the obligation
    # being UNSATISFIABLE at exactly the shape of input the failing scenario
    # drives. A post-image no outcome can satisfy would make every `ensures`
    # dischargeable only vacuously — the frozen impl would verify while pinning
    # nothing — and nothing else in this battery tests it: the two positives
    # show a faithful impl verifies, and the rivals show wrong impls do not, but
    # neither asks whether the three clauses can be JOINTLY satisfied at the
    # absent-context input.
    #
    # So this case discharges the obligation at that concrete input, by
    # evaluation, as an in-region `assert` BEFORE the frozen obligation closes
    # verbatim: at `ctx = none` there EXISTS an outcome satisfying all three
    # clauses at once (E1's `∃ reg`, E2's host-context region, and E3 — which is
    # non-trivially discharged at `none`, since `none = some c` is impossible).
    # The impl and the frozen `prove_correct` body are kept byte-for-byte, so the
    # three clauses still discharge exactly as for the frozen file and the only
    # added goal is the assertion.
    # =====================================================================
    {
        "id": "admiss-absent-context-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_asserted(
            "    -- The post-image is JOINTLY satisfiable at the absent-context\n"
            "    -- input: some outcome meets all three clauses there at once, so\n"
            "    -- the obligation is not vacuous at the shape of input the\n"
            "    -- failing scenario drives.\n"
            "    assert (with_name_prefix `admiss\n"
            "      (∃ out : Except PlaceErr Region,\n"
            "         (∃ reg, out = Except.ok reg) ∧\n"
            "         ((none : Option Ctx) = none →\n"
            "            out = Except.ok (placeWith (hostContext host) host)) ∧\n"
            "         (∀ c, (none : Option Ctx) = some c →\n"
            "            out = Except.ok (placeWith c host))))\n"),
        "rationale": (
            "ADMISSIBILITY on a total carrier. There is no `require` clause, so "
            "no input can be excluded and the nagini precondition-admits-the-"
            "input reading is vacuous; the residual risk that reading exists to "
            "catch is the obligation being UNSATISFIABLE at an F2P-shaped input, "
            "which would make the three clauses dischargeable only vacuously. "
            "The in-region assert discharges the whole post-image at the "
            "absent-context input — E1 (`∃ reg`), E2 (the host-context region) "
            "and E3 (vacuous at `none`, since `none = some c` is impossible) are "
            "met JOINTLY by one outcome — so the obligation is live rather than "
            "unsatisfiable there. The impl and the frozen `loom_solve` are kept "
            "verbatim, so the three `ensures` discharge as for the frozen file "
            "and the assert is the only added goal; it is load-bearing (a FALSE "
            "assertion of the same shape, additionally demanding the satisfying "
            "outcome be an `Except.error`, leaves an unsolved goal under the same "
            "frozen proof). Must verify (else PRECOND-TOO-STRONG / a vacuous "
            "obligation at the input that matters)."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- E1 + E2: the absent-context path must not abandon the placement ----
    {
        "id": "weak-none-abandons",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change defect: on a present context run the downstream, but on
        # an ABSENT context report the undefined-measurement error instead of
        # substituting the host's own context. Correct on every present-context
        # input; wrong on the absent-context sub-domain the issue reports.
        "module": _impl(
            "    -- Present context: run the downstream. Absent context: report the\n"
            "    -- undefined-measurement error (no substitute is obtained).\n"
            "    match ctx with\n"
            "    | some c => return Except.ok (placeWith c host)\n"
            "    | none   => return Except.error PlaceErr.noContext"),
        "refinement": (
            "this is the pre-patch behaviour: with no context supplied the "
            "placement attempts the downstream measurement with nothing to measure "
            "against and raises rather than substituting the host's own context. "
            "The failing test drives exactly that absent-context path (the "
            "tight-bbox save calls the placement with no live context) and still "
            "observes the raise, so it stays RED. It would NOT resolve."),
        "rationale": (
            "REJECT from E1 (`∃ reg, out = Except.ok reg`) and E2 "
            "(`ctx = none → out = Except.ok (placeWith (hostContext host) host)`): "
            "on `none` the body returns `Except.error`, which is neither an "
            "`Except.ok` region nor the host-context region E2 demands. Refuted at "
            "`ctx = none` (any host); the witness is unconditional — the outcome "
            "constructor alone contradicts the post-image, so no opaque hypothesis "
            "is needed. Against gold the triple HOLDS (it returns the host-context "
            "region), so the witness fails on gold."),
        "witness": _witness("(host : Host)", "none",
                            "placeWith (hostContext host) host"),
    },

    # ---- E3: a supplied context must be threaded through UNCHANGED ----
    {
        "id": "weak-ignore-supplied-context",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS. Always run the downstream with the HOST's own context, even
        # when a context was supplied — the "ignore the supplied renderer" rival.
        # Correct on the absent-context path (E1/E2 hold) and correct on any
        # present input where the host context happens to yield the same region;
        # wrong wherever the supplied context yields a different region. Its
        # witness therefore CONDITIONS on the opaque carrier.
        "module": _impl(
            "    -- Always run the downstream with the host's own context, ignoring\n"
            "    -- any supplied context.\n"
            "    return Except.ok (placeWith (hostContext host) host)"),
        "refinement": (
            "a faithful counterpart that always measures against the host's own "
            "context — even when a live one was threaded in — measures the "
            "child's geometry against a different context than the caller supplied "
            "on the normal draw/save paths (and the present-context position "
            "tests), so the computed placement diverges from gold. The image / "
            "position tests that thread a live context observe the wrong geometry, "
            "so they stay RED. It would NOT resolve."),
        "rationale": (
            "REJECT from E3 (`∀ c, ctx = some c → out = Except.ok (placeWith c "
            "host)`): on `some c` the body returns `placeWith (hostContext host) "
            "host`, and `hostContext host` need not equal the supplied `c` (both "
            "opaque). This rival keeps E1 and E2 (it always returns an `ok` region, "
            "and the `none` arm coincides with gold), so it agrees with gold over "
            "more of the domain than weak-present-refuses; its witness therefore "
            "CONDITIONS on the opaque carrier with the single satisfiable "
            "hypothesis `placeWith (hostContext host) host ≠ placeWith c host` — "
            "exactly the sub-domain where the rival is wrong. Against gold the "
            "triple HOLDS (it threads `c`), so the witness fails on gold."),
        "witness": _witness(
            "(c : Ctx) (host : Host)\n"
            "    (h : placeWith (hostContext host) host ≠ placeWith c host)",
            "(some c)", "placeWith c host", hyp=True),
    },

    # ---- E1 + E3 on the PRESENT side: a supplied context must yield a region --
    {
        "id": "weak-present-refuses",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of weak-none-abandons: substitute the host context on the ABSENT
        # path (E2 correct) but REPORT A REFUSAL on the PRESENT path. Isolates the
        # never-abandon frame on the present-context sub-domain — the side
        # weak-none-abandons leaves correct. Unconditional witness (the outcome
        # constructor alone contradicts the post-image at any `some c`).
        "module": _impl(
            "    -- Absent context: substitute the host's own context. Present\n"
            "    -- context: report the undefined-measurement error.\n"
            "    match ctx with\n"
            "    | some c => return Except.error PlaceErr.noContext\n"
            "    | none   => return Except.ok (placeWith (hostContext host) host)"),
        "refinement": (
            "a faithful counterpart that abandons the placement whenever a context "
            "IS supplied never completes the measurement on the normal "
            "draw/save/position paths (which all thread a live context), so the "
            "child is never positioned and those tests stay RED. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from E1 (`∃ reg, out = Except.ok reg`) and E3 "
            "(`∀ c, ctx = some c → out = Except.ok (placeWith c host)`): on "
            "`some c` the body returns `Except.error`, neither an `ok` region nor "
            "the `placeWith c host` region E3 demands. It keeps E2 correct (the "
            "`none` arm coincides with gold), and it fails on EVERY present input "
            "(unlike weak-ignore-supplied-context, which fails only where the "
            "regions differ), so the witness is unconditional. Refuted at "
            "`ctx = some c` (any host); against gold the triple HOLDS, so the "
            "witness fails on gold."),
        "witness": _witness("(c : Ctx) (host : Host)", "(some c)",
                            "placeWith c host"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals) plus a 2-case AXIOM lane. It
# contracts TWO functions over a value-int carrier — `call` (the placement entry,
# which resolves the context and delegates) and `measure` (which records a count
# and a handle) — with a postcondition folding: exactly-one measurement
# (`measurements == 1`), a present context (`measured_with > 0`), passthrough of a
# supplied renderer (`Implies(renderer is not None, measured_with == renderer)`),
# and the resolved-source pin on the absent path (`Implies(renderer is None,
# measured_with == axes_context(ax))`), plus `measure`'s `Requires(context > 0)`.
#
# This bundle models only the PURELY-FUNCTIONAL CORE the fix touches:
# `computePlacement (ctx) (host)` returning the placement region, over the opaque
# carrier `Ctx`/`Host`/`Region` with the two UNCHANGED callees `hostContext`
# (the host's own context; nagini `axes_context`) and `placeWith` (the downstream
# region pipeline). The nagini `measure`/`measurements`/`measured_with` counter is
# NOT a modeled observable here — the region result carries no measurement-count
# footprint — so every nagini case attached to that counter re-aims onto the
# region clauses (E1/E2/E3) or is dropped as unmodeled (carrier narrowing, which
# the porting map explicitly blesses: parity with nagini is NOT the target).
#
#   nagini case                          -> here                            status
#   ---------------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-control-branch-reorder      PORTED
#   admiss-no-renderer-path               -> admiss-absent-context-satisfiable RE-EXPRESSED
#   reject-substitute-present-context     -> weak-none-abandons              RE-EXPRESSED
#   reject-ignore-supplied-renderer       -> weak-ignore-supplied-context    PORTED
#   reject-partial-domain-pass-axes       -> (none)                          VACUOUS (ill-typed)
#   reject-measure-twice                  -> (none)                          OMITTED (count unmodeled)
#   reject-skip-measurement-no-renderer   -> weak-none-abandons (folded)     FOLDED
#   reject-measure-wrong-handle           -> weak-ignore-supplied-context    FOLDED
#   (no sibling counterpart)              -> weak-present-refuses             ADDED
#
# 2 ported (1 positive + 1 rival), 2 re-expressed (1 rival + the admissibility
# lane), 1 added rival, 2 folded, 2 omitted/vacuous. No case was dropped because
# its proof or witness was hard; each omission is a modeling or typing fact
# stated below. The admissibility lane was recorded as omitted by an earlier
# revision and is restored (audit repair) — see its entry below.
#
# RE-EXPRESSED (weak-none-abandons): the nagini reject-substitute-present-context
#   measures the absent path against an ARBITRARY present context (a positive
#   literal `1`) instead of the resolved host context. On THIS carrier there is no
#   closed `Ctx` term other than `hostContext host` itself — the only context the
#   absent branch can name is the gold one — so "substitute a different present
#   context" has no term. What IS expressible, and is the same defect the F2P
#   reports (the absent path abandoning the placement), is the pre-patch: on
#   `none` report the undefined-measurement error. It attacks E1+E2 and is refuted
#   unconditionally at `ctx = none`.
# PORTED (weak-ignore-supplied-context): the nagini reject-ignore-supplied-renderer
#   measures against the resolved context on BOTH branches, ignoring a supplied
#   renderer. Re-expressed verbatim on this carrier: run the downstream with
#   `hostContext host` even on `some c`. Attacks E3; refuted by conditioning on
#   `placeWith (hostContext host) host ≠ placeWith c host` (the sub-domain where a
#   supplied context yields a different region). It is a genuine near-miss (E1/E2
#   both hold), so it carries its own conditioning witness per the near-miss rule.
# ADDED (weak-present-refuses): the never-abandon frame E1 must be attacked on the
#   PRESENT side too, not only the absent side. weak-none-abandons leaves the
#   present path correct, so without this rival a body that completes the absent
#   path but refuses the present one would go unattacked. It attacks E1+E3 at
#   `ctx = some c`, unconditionally (the outcome constructor alone contradicts the
#   post-image), so it is NOT the same failure as the conditioning near-miss even
#   though both sit at a `some c` input.
#
# OMITTED / VACUOUS (3), plus the admissibility lane now RE-EXPRESSED:
#  * admiss-no-renderer-path -> admiss-absent-context-satisfiable. RE-EXPRESSED,
#    NOT omitted (audit repair). The nagini case Asserts the precondition chain
#    admits the F2P-shaped no-renderer input and that the resolved context is
#    establishable (`axes_context(ax) > 0`). This bundle has NO `require` clause
#    (the admitted domain is total) and the opaque carrier has no `> 0` notion,
#    so THAT reading is indeed vacuous — but the total-carrier analogue is not,
#    and an earlier revision wrongly recorded the whole lane as inexpressible on
#    the strength of "E1/E2/E3 are satisfiable by construction". That is an
#    argument, not a machine-checked claim, and it is exactly what an
#    admissibility case is supposed to check rather than assume: the residual
#    risk is the obligation being UNSATISFIABLE at an F2P-shaped input, which
#    would leave every clause dischargeable only vacuously. It IS expressible
#    here — an in-region `assert` discharges the joint post-image at `ctx = none`
#    by evaluation and closes under the frozen `loom_solve` — so the lane is now
#    carried by admiss-absent-context-satisfiable. Neither positive control
#    covers it: they show a faithful impl verifies, not that the clauses can be
#    jointly met at the input the failing scenario drives.
#  * reject-partial-domain-pass-axes. The nagini rival passes the axes HANDLE
#    itself (`ax`, an unconstrained int) as the context on the absent path,
#    violating `measure`'s `Requires(context > 0)`. On this carrier `Ctx` and
#    `Host` are DISTINCT opaque types, so `placeWith host host` is ILL-TYPED —
#    the Lean type discipline forbids passing the host as a context outright.
#    VACUOUS on this carrier (the distinction nagini's untyped-int carrier
#    collapses is kept by the type system here); no substitute fabricated.
#  * reject-measure-twice. The nagini rival performs the measurement TWICE,
#    caught by `Ensures(self.measurements == 1)`. The measurement-count is not a
#    modeled observable here: `computePlacement` returns a region, and running the
#    downstream twice returns the same region, leaving no value footprint the spec
#    can force (directive 9 shape). Unmodeled behaviour, dropped (carrier
#    narrowing) — not a substitute counter fabricated.
#  * reject-skip-measurement-no-renderer / reject-measure-wrong-handle. FOLDED:
#    "skip the measurement on the absent path" (returning no region) is exactly
#    weak-none-abandons on this carrier; "record the wrong handle" (measure the
#    geometry against the wrong context) is exactly weak-ignore-supplied-context
#    (E3). Both nagini cases attack, on their two-function carrier, the same two
#    behaviours these velvet rivals attack; no separate case is needed.
#
# CLAUSE / BINDER COVERAGE. Three independent clauses, each DEFENDED by the two
#   positive controls and each ATTACKED: E1 by weak-none-abandons (absent side)
#   and weak-present-refuses (present side); E2 by weak-none-abandons; E3 by
#   weak-ignore-supplied-context and weak-present-refuses. The `ctx` binder is
#   moved across the reject witnesses — `ctx = none` (weak-none-abandons) and
#   `ctx = some c` (weak-ignore-supplied-context, weak-present-refuses) — so the
#   present/absent decision is probed on BOTH sides (pts spans {none, some c}).
#   The `host` binder is opaque and cannot be moved to a second closed value
#   (there is no closed `Host` term; a second would need a banned new `axiom`), so
#   every witness quantifies over an abstract `host`, which participates in each
#   witness's refuted composition — the documented opaque-carrier situation, not
#   an unattacked binder. The two `some c` rivals fail at overlapping inputs but
#   for DIFFERENT reasons (a wrong region vs a refusal), and the near-miss
#   (weak-ignore-supplied-context) carries the discriminating conditioning
#   hypothesis per the manifest's near-miss rule.
#
# WITNESS DISCRIMINATION (verified during authoring with real builds, re-checked
#   by the gate's two builds per reject case): each witness ELABORATES against its
#   straight-line rival (its `triple` reduces under `simp [triple, wp_pure]` to a
#   goal the rival's outcome — or the conditioning hypothesis — closes) and FAILS
#   against the frozen solution (whose triple HOLDS, leaving `¬ triple` with a
#   residual `⊢ False` the hypothesis cannot close). Each conditioning witness
#   carries at most ONE hypothesis about a single opaque `placeWith` composition,
#   jointly satisfiable (no `False` derivable from an opaque callee). No
#   `sorry`/`admit`/`native_decide`/new `axiom` appears.
#
# AXIOM_TESTS: dropped. The nagini 2-case axiom lane (soundness + containment for
#   `axes_context`) is G-AX's job; this gate ignores `AXIOM_TESTS`. The opaque
#   `hostContext`/`placeWith` are A-consumed callees validated by axiom_check.py,
#   not contracts this spec-lane manifest probes.
AXIOM_TESTS = []

# properties.py — PBT falsification battery for matplotlib__matplotlib-26291.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT.
#
# Spec cases are full model.py variants built by region-surgery: every variant
# is produced by _swap()-ing text that lies ENTIRELY inside an `# impl-start /
# # impl-end` region (either `measure`'s impl or `call`'s impl). The frozen
# spec (axioms / pure / pre-conditions / post-conditions / signatures /
# docstring) is never touched, so `markers.same_spec` holds for every case by
# construction.
#
# Defended surface (the postcondition of `call`):
#     Ensures(self.measurements == 1)                                   # exactly one measurement
#     Ensures(self.measured_with > 0)                                   # against a PRESENT context
#     Ensures(Implies(renderer is not None, self.measured_with == renderer))  # supplied one when supplied
#     Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
#         # when absent: pinned to the context the host axes resolves via the
#         # unchanged drawing-context source (NOT an arbitrary substitute)
# plus `measure`'s Requires(context > 0) — the measurement is unreachable
# without a present context (the real AttributeError on the no-renderer path).
#
# There is NO read-only Acc(x, 1/2) input: `self` is full-write (both fields are
# assigned by `measure`), and `ax`/`renderer` are value-typed ints. So the
# classic frame-mutation probe (overwrite a half-permission input) does not
# apply here; see `assessment` in the structured return. Instead the battery
# attacks the value/control-flow surface and the presence-only relaxation.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26291"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_GOLD_PATCH = str(Path(__file__).parent / "patch.diff")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- the unique impl-region bodies we are allowed to edit --------------------
# call's impl region body (gold):
_CALL_GOLD = (
    "    eff = renderer  # type: Optional[int]\n"
    "    if eff is None:\n"
    "        eff = axes_context(ax)\n"
    "    measure(self, eff)"
)
# measure's impl region body (gold):
_MEASURE_GOLD = (
    "    self.measurements = self.measurements + 1\n"
    "    self.measured_with = context"
)


def _call_variant(body):
    return _swap(_BASE, _CALL_GOLD, body)


def _measure_variant(body):
    return _swap(_BASE, _MEASURE_GOLD, body)


# =========================================================================
# SPEC LANE
# =========================================================================
SPEC_TESTS = [

    # ---------------------------------------------------------------------
    # POSITIVE CONTROL (soundness). A structurally-DIFFERENT but CORRECT impl
    # of `call`: instead of the gold "default-then-overwrite-if-None" shape,
    # branch explicitly on `renderer is None` and call `measure` once inside
    # each arm (the no-renderer arm resolves the present context from the
    # axiom). This keeps every gold proof obligation (one measure call per
    # path; `measure`'s Requires(context > 0) is discharged by renderer>0 on
    # the present arm and by axes_context(ax)>0 on the absent arm). MUST
    # verify; if it cannot => SPEC-TOO-STRONG.
    # ---------------------------------------------------------------------
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _call_variant(
            "    if renderer is None:\n"
            "        measure(self, axes_context(ax))\n"
            "    else:\n"
            "        measure(self, renderer)"
        ),
        "rationale": (
            "structurally-different correct impl (explicit two-arm branch, one "
            "measure per arm) that keeps every gold obligation: on renderer is "
            "not None, measure(self, renderer) gives measured_with == renderer "
            "(precond renderer>0 discharges Requires); on renderer is None, "
            "measure(self, axes_context(ax)) gives measured_with > 0 via the "
            "axiom's Ensures(Result()>0). Must verify (else SPEC-TOO-STRONG)."
        ),
    },

    # ---------------------------------------------------------------------
    # ADMISSIBILITY. Confirm the precondition admits a normal F2P-shaped input
    # (the no-renderer save path: measurements==0, renderer is None). The
    # gold body is kept verbatim and an in-impl Assert pins that, for the
    # representative entry state, the resolved present context is established
    # (axes_context(ax) > 0) before the single measurement — i.e. the
    # precondition chain produces a verifying run for the F2P input. If this
    # cannot verify, the precondition is contradictory for a legitimate input
    # => PRECOND-TOO-STRONG.
    # ---------------------------------------------------------------------
    {
        "id": "admiss-no-renderer-path",
        "kind": "admissibility",
        "expect": "verify",
        "module": _call_variant(
            "    Assert(self.measurements == 0)\n"
            "    eff = renderer  # type: Optional[int]\n"
            "    if eff is None:\n"
            "        Assert(axes_context(ax) > 0)\n"
            "        eff = axes_context(ax)\n"
            "    measure(self, eff)"
        ),
        "rationale": (
            "precondition (measurements==0, renderer present=>renderer>0) admits "
            "the F2P-shaped no-renderer input; the in-impl Asserts confirm the "
            "entry state and the resolved present context are establishable. "
            "Must verify (else PRECOND-TOO-STRONG)."
        ),
    },

    # ---------------------------------------------------------------------
    # SUBSTITUTE-CONTEXT rival (the G-PANEL-1 attack shape). On the
    # no-renderer path it measures against an ARBITRARY present context (a
    # positive literal) instead of the one the host axes resolves. This is the
    # model twin of the audit attack atk_1_const_present.py, whose faithful
    # patch constructs a fresh `RendererAgg(100, 100, 72)` instead of calling
    # `ax.figure._get_renderer()`. Under the previous presence-only
    # postcondition (measured_with > 0) this VERIFIED — the recorded
    # G-PANEL-1 spec-too-weak failure. The spec now pins the no-renderer
    # measurement to the resolved host-axes context
    # (Ensures(Implies(renderer is None, measured_with == axes_context(ax)))),
    # so a substitute constant is no longer provable: axes_context(ax) is
    # opaque (only known > 0) and cannot be shown equal to 1. MUST reject.
    #
    # NOTE (repair 2026-08-05): this case was previously relabeled to a
    # soundness positive control on the theory that "any present source is a
    # correct resolve". The G-PANEL-1 audit refuted that theory concretely:
    # a fresh fixed-size 100x100@72dpi substitute renderer measures the
    # window-extent/offset geometry against a context whose dpi/size need not
    # match the figure's actual renderer, so the computed inset placement in
    # the tight-bbox save diverges from the gold whenever the figure's
    # dpi != 72 — behaviourally unequal to the gold patch even though the
    # thin F2P test (which only checks the save does not raise) cannot
    # observe it. The spec, not the test, must pin the resolved source.
    # ---------------------------------------------------------------------
    {
        "id": "reject-substitute-present-context",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _call_variant(
            "    eff = renderer  # type: Optional[int]\n"
            "    if eff is None:\n"
            "        eff = 1\n"
            "    measure(self, eff)"
        ),
        "refinement": (
            "Its faithful patch resolves the no-renderer path from a substitute "
            "source (e.g. a fresh RendererAgg(100, 100, 72) — the recorded "
            "G-PANEL-1 attack) instead of ax.figure._get_renderer(). The "
            "window-extent/offset geometry is then measured against a context "
            "whose dpi/size need not match the figure's actual renderer, so the "
            "inset placement computed during the tight-bbox save diverges from "
            "the gold patch for any figure whose dpi differs from the "
            "substitute's — behaviourally unequal to gold; the divergence is "
            "invisible to the thin F2P (no-raise) test, which is exactly why "
            "the spec must pin the source."
        ),
        "rationale": (
            "Rejected by Ensures(Implies(renderer is None, measured_with == "
            "axes_context(ax))): the substitute constant 1 cannot be proven "
            "equal to the opaque axes_context(ax) (only known > 0). Rejection "
            "comes from the pinned no-renderer postcondition clause."
        ),
    },

    # ---------------------------------------------------------------------
    # UNGROUNDED-ORACLE / wrong-branch echo. A rival that measures against the
    # resolved axes context on BOTH branches (ignores the supplied renderer).
    # It satisfies the no-renderer clauses but VIOLATES
    # Implies(renderer is not None, measured_with == renderer): axes_context(ax)
    # is opaque (only known > 0), so the verifier cannot prove it equals the
    # supplied renderer. MUST reject.
    # REFINEMENT: its faithful patch always uses ax.figure._get_renderer()
    # even when a real renderer was passed in. On the supplied-renderer paths
    # exercised by the P2P bbox/offset tests (e.g. test_anchored_locator_base_call,
    # test_inset_locator) the measurement would be taken against a different
    # renderer than the one the caller threaded in (the active draw renderer),
    # changing the measured geometry => the image-comparison / position P2P
    # tests would NOT pass. So a verifying rival would be a real break.
    # ---------------------------------------------------------------------
    {
        "id": "reject-ignore-supplied-renderer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _call_variant(
            "    eff = axes_context(ax)  # type: int\n"
            "    measure(self, eff)"
        ),
        "refinement": (
            "Its faithful patch ignores the supplied renderer and always "
            "measures against ax.figure._get_renderer(). On the supplied-renderer "
            "paths (the normal draw/savefig path and the P2P position/image tests "
            "test_inset_locator, test_anchored_locator_base_call) it would measure "
            "against a different renderer than the one passed in, perturbing the "
            "computed window-extent/offset geometry => those P2P tests would NOT "
            "pass. Not a faithful resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Implies(renderer is not None, "
            "measured_with == renderer)): axes_context(ax) is opaque (only known "
            ">0), so measured_with == renderer is unprovable when a renderer was "
            "supplied. Rejection comes from that postcondition clause."
        ),
    },

    # ---------------------------------------------------------------------
    # PARTIAL-DOMAIN. A rival correct on the supplied-renderer sub-domain but
    # diverging on the no-renderer sub-domain: on renderer is None it measures
    # against `ax` directly (the host-axes handle), which is an UNCONSTRAINED
    # int (could be <= 0). MUST reject for INSUFFICIENT proof of the
    # measurement precondition.
    # REFINEMENT: its faithful patch passes the axes object itself as the
    # renderer (`renderer = ax`) on the no-renderer path. An Axes has no
    # points_to_pixels => get_offset raises AttributeError, so the tight-bbox
    # save (test_inset_axes_tight) STILL fails => F2P not resolved.
    # ---------------------------------------------------------------------
    {
        "id": "reject-partial-domain-pass-axes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _call_variant(
            "    eff = renderer  # type: Optional[int]\n"
            "    if eff is None:\n"
            "        measure(self, ax)\n"
            "        return\n"
            "    measure(self, eff)"
        ),
        "refinement": (
            "Its faithful patch sets renderer = ax (the axes) on the no-renderer "
            "path. An Axes object has no points_to_pixels, so get_offset raises "
            "AttributeError and test_inset_axes_tight STILL fails => the F2P does "
            "NOT resolve. A faithful resolve must source a real renderer."
        ),
        "rationale": (
            "Rejected by measure's Requires(context > 0): on the no-renderer arm "
            "`ax` is an unconstrained int (the host-axes handle), not provably "
            ">0, so measure(self, ax) cannot establish its precondition (and the "
            "no-renderer postcondition measured_with > 0 is unprovable). "
            "Rejection comes from measure's precondition."
        ),
    },

    # ---------------------------------------------------------------------
    # CONTROL-FLOW-EFFECT (measurement count). A rival that performs the
    # measurement TWICE (resolve, measure, then measure once more with the same
    # present context). The value abstraction exposes the count as
    # self.measurements; the second measure makes measurements == 2. MUST
    # reject by Ensures(self.measurements == 1).
    # REFINEMENT: its faithful patch calls get_window_extent/get_offset twice.
    # measure's spec asserts measurements==Old+1 each call; the second call also
    # requires measurements unchanged-modulo-self... the real double measurement
    # is redundant work and would not match the gold's exactly-once contract;
    # more importantly the model's measurements==1 obligation pins single
    # execution. A double-measure rival cannot be the gold and is rejected.
    # ---------------------------------------------------------------------
    {
        "id": "reject-measure-twice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _call_variant(
            "    eff = renderer  # type: Optional[int]\n"
            "    if eff is None:\n"
            "        eff = axes_context(ax)\n"
            "    measure(self, eff)\n"
            "    measure(self, eff)"
        ),
        "refinement": (
            "Its faithful patch performs the window-extent/offset measurement "
            "twice. The exactly-once contract (measurements == 1) is the modeled "
            "observable of 'the measurement is performed exactly once'; a rival "
            "that measures twice diverges from the gold single-measurement "
            "behaviour the F2P/P2P paths exercise and is not a faithful resolve."
        ),
        "rationale": (
            "Rejected by Ensures(self.measurements == 1): two measure() calls "
            "make measurements == 2 (each call adds 1), contradicting the "
            "exactly-once postcondition. Rejection comes from that clause."
        ),
    },

    # ---------------------------------------------------------------------
    # SUPPORTING near-miss: drop the measurement entirely on the no-renderer
    # path (never measure). measurements stays 0 != 1. Cheap supporting case;
    # still carries a refinement (a patch that skips the measurement when no
    # renderer is supplied returns no bbox => the inset is never positioned and
    # the save path crashes / mis-positions => F2P not resolved).
    # ---------------------------------------------------------------------
    {
        "id": "reject-skip-measurement-no-renderer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _call_variant(
            "    eff = renderer  # type: Optional[int]\n"
            "    if eff is None:\n"
            "        return\n"
            "    measure(self, eff)"
        ),
        "refinement": (
            "A patch that skips the window-extent/offset measurement entirely on "
            "the no-renderer path computes no bbox/offset for the inset; "
            "test_inset_axes_tight's save would still fail (no position computed) "
            "=> F2P not resolved."
        ),
        "rationale": (
            "Rejected by Ensures(self.measurements == 1) and "
            "Implies(renderer is None, measured_with > 0): on renderer is None "
            "the early return leaves measurements == 0 and measured_with == 0, "
            "violating both. Rejection comes from those postcondition clauses."
        ),
    },

    # ---------------------------------------------------------------------
    # SUPPORTING near-miss on `measure`'s own impl: record the WRONG handle
    # (measured_with = context + 1 instead of context). Violates measure's own
    # Ensures(measured_with == context). Confirms the measurement abstraction
    # is tightly pinned (a faithful measurement records the context it was
    # handed). Cheap supporting case.
    # ---------------------------------------------------------------------
    {
        "id": "reject-measure-wrong-handle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _measure_variant(
            "    self.measurements = self.measurements + 1\n"
            "    self.measured_with = context + 1"
        ),
        "refinement": (
            "A measurement that records a handle different from the one it was "
            "handed misrepresents which context the geometry was measured "
            "against; in the present-renderer P2P paths this breaks the "
            "measured_with == renderer correspondence the caller relies on => not "
            "a faithful resolve."
        ),
        "rationale": (
            "Rejected by measure's Ensures(self.measured_with == context): "
            "recording context+1 violates it. Rejection comes from measure's "
            "own postcondition."
        ),
    },
]


# =========================================================================
# AXIOM LANE
# =========================================================================
# One @ContractOnly axiom: axes_context(ax) Ensures Result() > 0 (A-consumed).
# It stands in for the UNCHANGED callee ax.figure._get_renderer(). The gold
# patch touches only inset_locator.py __call__, not figure.py, so the callee is
# identical at base_commit and post-gold; apply_gold=True is harmless (the patch
# applies cleanly) and matches the runner default.
#
# Containment: axes_context has NO Requires (its domain is all of int); the
# model calls it only as axes_context(ax) on the renderer-is-None branch, where
# `ax` is an arbitrary host-axes handle. Every reachable input is therefore in
# the (total) axiom domain by construction — containment is vacuously satisfied.
# The containment probe documents this by confirming the real callee is total
# (defined + present-yielding) over the representative reachable axes shapes
# (a caller-reachable axes that the callee could NOT handle would be the only
# defect; none exists).

_AX_SOUNDNESS_PROBE = r'''
import sys

def _is_present_context(renderer):
    # model's Result() > 0 (present, non-absent handle) <-> the real renderer
    # being a usable object: not None, and carrying the point-to-pixel scale the
    # downstream offset measurement (get_offset) requires (points_to_pixels).
    return renderer is not None and hasattr(renderer, "points_to_pixels")

def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    checks = 0

    # 1. a single plain axes
    fig, ax = plt.subplots()
    r = ax.figure._get_renderer()          # the REAL callee axes_context models
    assert _is_present_context(r), (
        "axes_context UNSOUND: plain axes figure produced no usable renderer "
        "(got %r) -> axiom Ensures(Result()>0) violated" % (r,))
    checks += 1
    plt.close(fig)

    # 2. the exact reproduction from the bug report: two subplots, an inset
    #    axes built by axes_grid1.inset_locator on the first. Every axes' figure
    #    must yield a present renderer (this is the regression scenario).
    fig, (a0, a1) = plt.subplots(1, 2, figsize=[5.5, 2.8])
    axins = inset_axes(a0, width=1.3, height=0.9)
    for a in (a0, a1, axins):
        r = a.figure._get_renderer()
        assert _is_present_context(r), (
            "axes_context UNSOUND: inset-regression axes produced no usable "
            "renderer (got %r)" % (r,))
        checks += 1
    plt.close(fig)

    # 3. fuzz figure shapes / dpis (boundaries + sentinels): tiny, default, and
    #    large figures at varied dpi. The renderer must always be present.
    for figsize, dpi in [((0.5, 0.5), 1), ((1, 1), 50), ((3, 2), 100),
                         ((6.4, 4.8), 72), ((10, 8), 200), ((2.5, 2.5), 150),
                         ((20, 0.3), 300)]:
        fig = plt.figure(figsize=figsize, dpi=dpi)
        a = fig.add_subplot(111)
        r = a.figure._get_renderer()
        assert _is_present_context(r), (
            "axes_context UNSOUND: figure %r@%rdpi produced no usable renderer "
            "(got %r)" % (figsize, dpi, r))
        checks += 1
        plt.close(fig)

    # 4. multiple stacked inset axes on one host (deeper nesting) — every
    #    figure must still yield a present renderer.
    fig, ax = plt.subplots()
    ins1 = inset_axes(ax, width="40%", height="30%")
    ins2 = inset_axes(ins1, width=0.5, height=0.5)
    for a in (ax, ins1, ins2):
        r = a.figure._get_renderer()
        assert _is_present_context(r), (
            "axes_context UNSOUND: nested-inset axes produced no usable "
            "renderer (got %r)" % (r,))
        checks += 1
    plt.close(fig)

    print("AX-SOUND OK: axes_context (ax.figure._get_renderer()) yields a "
          "present (non-absent) usable renderer on %d witnesses incl. the bug "
          "reproduction and nested insets" % checks)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

_AX_CONTAINMENT_PROBE = r'''
import sys

def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    # The axiom axes_context(ax) has NO Requires -> its domain is all of int
    # (every host-axes handle). The model calls it only on the renderer-is-None
    # branch as axes_context(ax), where `ax` is the host axes the caller was
    # invoked with. Containment asks: does every axes the caller can actually
    # reach lie in the axiom's (total) domain? Since there is no Requires to
    # violate, containment is vacuous; we positively confirm it by checking the
    # real callee is TOTAL (defined and present-yielding, never raising) over
    # the representative reachable host-axes shapes the no-renderer save path
    # passes in. A reachable axes the callee could not handle would be the only
    # AXIOM-TOO-WEAK-FOR-CALLER defect; we show none exists.
    reachable = []

    fig, ax = plt.subplots()
    reachable.append(("plain", ax))
    fig2, (a0, a1) = plt.subplots(1, 2, figsize=[5.5, 2.8])
    axins = inset_axes(a0, width=1.3, height=0.9)   # the regression's host axes
    reachable += [("subplot-left", a0), ("subplot-right", a1),
                  ("inset", axins)]

    covered = 0
    for label, a in reachable:
        # _get_renderer is the unchanged callee; it must be defined on the axes'
        # figure and return a present handle for every reachable axes (in-domain).
        assert hasattr(a, "figure") and a.figure is not None, (
            "containment: reachable axes %s has no figure" % label)
        r = a.figure._get_renderer()
        assert r is not None and hasattr(r, "points_to_pixels"), (
            "AXIOM-TOO-WEAK-FOR-CALLER: reachable axes %s produced a "
            "non-present/unusable context %r outside the axiom's covered "
            "domain" % (label, r))
        covered += 1

    plt.close(fig)
    plt.close(fig2)
    print("AX-CONTAIN OK: axiom domain is total (no Requires); every "
          "caller-reachable host-axes (%d shapes incl. the regression host) is "
          "in-domain and yields a present context" % covered)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-axes_context",
        "axiom": "axes_context",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": (
            "Runs the REAL callee ax.figure._get_renderer() (what axes_context "
            "models) over plain, the exact bug-reproduction inset, fuzzed "
            "figure shapes/dpis, and nested insets; asserts each yields a "
            "present usable renderer (Ensures(Result()>0) analog: not None + has "
            "points_to_pixels). Any violation => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-contain-axes_context",
        "axiom": "axes_context",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": (
            "axes_context has no Requires (domain = all int), and the model only "
            "passes the host-axes handle on the renderer-is-None branch. Confirms "
            "every caller-reachable axes is in-domain and yields a present "
            "context; a reachable axes the callee couldn't handle would be the "
            "only AXIOM-TOO-WEAK-FOR-CALLER defect, and none exists."
        ),
    },
]

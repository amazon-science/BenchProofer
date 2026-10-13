# properties.py — PBT falsification battery for pydata__xarray-3993.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   select_coordinate(coord: Optional[int], dim: Optional[int]) -> Routed
#   is the selector-routing PROLOGUE of DataArray.integrate (gold patch). The two
#   selectors are abstract coordinate identifiers (Hashable -> Optional[int]);
#   `None` means "not supplied". Five load-bearing postcondition clauses pin a
#   three-way decision:
#     (C1) Ensures(not (dim is not None and coord is not None))
#          -> a NORMAL return is reachable only when NOT both supplied.
#     (C2) Ensures(Acc(Result().coord) and Acc(Result().deprecated))   [framing]
#     (C3) Implies(dim is not None and coord is None, Result().coord is dim)
#          -> legacy-selector-only routes ALONG dim.
#     (C4) Implies(not (dim is not None and coord is None), Result().coord is coord)
#          -> every other honoured case routes ALONG coord.
#     (C5) Result().deprecated == (dim is not None and coord is None)
#          -> the DEPRECATION SIGNAL fires EXACTLY on the legacy-selector-only call
#             (this is the discriminating clause the change introduces; what
#             pytest.warns(FutureWarning) asserts in F2P).
#     (C6) Exsures(ConflictingSelection, dim is not None and coord is not None)
#          -> supplying BOTH is refused (raise), and ONLY then.
#
# F2P: xarray/tests/test_dataset.py::test_integrate[True/False] — adds
#      `with pytest.warns(FutureWarning): da.integrate(dim="x")` and keeps
#      `with pytest.raises(ValueError): da.integrate("x2d")` (the conflict path is
#      exercised elsewhere in the same test family; the NEW behaviour is the warning).
#
# This spec is FULLY GROUNDED: every output clause is a direct function of the two
# inputs `coord`/`dim`. There is NO @Pure answer-key oracle in the postcondition to
# echo (ungrounded-oracle-echo is N/A — see 'assessment'), and NO read-only heap
# input held at Acc(.,1/2) (selectors are plain Optional[int] VALUE parameters —
# frame-mutation is N/A; see 'assessment'). The bundle has NO @ContractOnly axioms
# and NO A-reference deep models (axioms region empty; meta.json axioms == []), so
# AXIOM_TESTS = []. The applicable attack classes are therefore PARTIAL-DOMAIN
# (sub-case divergences of routing/deprecation) and CONTROL-FLOW-EFFECT (the
# refusal raise / the deprecation signal are observable effects), plus the two
# mandatory positive lanes (structural positive control + admissibility).

from pathlib import Path

INSTANCE = "pydata__xarray-3993"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region body (model.py lines 107-115). Every rival edits ONLY
# text strictly between # impl-start and # impl-end, so spec_view (and thus
# same_spec) is preserved.
# ---------------------------------------------------------------------------
_IMPL = """    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True

    return Routed(coord, deprecated)"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT impl: an early-return cascade with NO mutable
# `deprecated` local and NO `coord = dim` reassignment. After the both-supplied
# refusal, `dim is not None` implies coord is None, so we route dim with the
# signal; otherwise we route coord with no signal. This is a branch/return reshape
# (directive-3 safe: no loop, no fold, no induction lemma needed) — the verifier
# discharges each return against C3/C4/C5 directly. If this CANNOT verify, the
# postcondition rejects a faithful correct impl => SPEC-TOO-STRONG.
_POS = """    if dim is not None and coord is not None:
        raise ConflictingSelection()
    if dim is not None:
        # both-supplied already refused above, so here coord is None: this is the
        # legacy-selector-only case -> route dim AND emit the deprecation signal.
        return Routed(dim, True)
    # dim is None: route the primary selector (or None), no deprecation signal.
    return Routed(coord, False)"""

POS_REORDER = _swap(_BASE, _IMPL, _POS)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (spec_view elides ONLY the
# impl region; anything at module level enters the spec signature). So the
# admissibility witness lives INSIDE the impl region, inserted right after
# `# impl-start`, before any gold obligation, so every following obligation is
# preserved verbatim. It constructs the F2P-shaped legacy-only outcome
# (Routed(5, True), i.e. da.integrate(dim="x")) and asserts — through the Routed
# constructor's own Ensures — that its fields are exactly the routed coordinate
# and the deprecation flag. If this block cannot verify, a normal F2P-shaped
# value cannot even be constructed under the contract => PRECOND-TOO-STRONG.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P-shaped honoured outcome — the
    # legacy-selector-only call da.integrate(dim="x") (coord omitted) — must be
    # constructible and pin coord=the routed selector with the deprecation signal
    # set. Bind the selector to a local so the Routed Ensures' identity chains.
    sel = dim  # type: Optional[int]
    witness = Routed(sel, True)
    Assert(witness.coord is sel)
    Assert(witness.deprecated)"""

ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- W1 (partial-domain, THE discriminator): never emit the deprecation signal.
# This is exactly the PRE-PATCH behaviour (model_prepatch.py): route dim straight
# through as the coordinate but NEVER set deprecated. Correct on routing (C3/C4)
# and refusal (C6); diverges ONLY on the deprecation signal for the
# legacy-selector-only sub-domain.
# refinement: the faithful real patch is the pre-patch DataArray.integrate
# (`ds = self._to_temp_dataset().integrate(dim, datetime_unit)` with no
# warnings.warn). The F2P `with pytest.warns(FutureWarning): da.integrate(dim="x")`
# asserts a FutureWarning is emitted; the no-warn patch emits none and pytest.warns
# FAILS — so it does NOT resolve.
# rejection source: C5 `Result().deprecated == (dim is not None and coord is None)`
# — on the legacy-only input (dim!=None, coord==None) the RHS is True but the impl
# returns deprecated=False.
_W1_NEVER_DEPRECATE = """    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        # PRE-PATCH RIVAL: route dim through but NEVER emit the deprecation signal.

    return Routed(coord, deprecated)"""

W1_NEVER_DEPRECATE = _swap(_BASE, _IMPL, _W1_NEVER_DEPRECATE)


# --- W2 (partial-domain): always emit the deprecation signal.
# Routes correctly and refuses correctly, but sets deprecated=True even on the
# primary-selector-only call da.integrate("x") (and the neither-supplied call).
# refinement: a real patch that emits warnings.warn(FutureWarning) UNCONDITIONALLY
# (e.g. moved the warning above the `if dim is not None` guard) would warn on the
# primary-only / Dataset-style call da.integrate(coord="x") too. The P2P suite and
# the units test (now `method("integrate", coord="x")`) call integrate via the
# primary selector with NO FutureWarning expected; an unconditional warn turns the
# benign path noisy (and under the project's warning-filter config can error), so
# it does NOT resolve.
# rejection source: C5 — on the primary-only input (dim==None, coord!=None) the RHS
# is False but the impl returns deprecated=True.
_W2_ALWAYS_DEPRECATE = """    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = True
    if dim is not None and coord is None:
        coord = dim

    return Routed(coord, deprecated)"""

W2_ALWAYS_DEPRECATE = _swap(_BASE, _IMPL, _W2_ALWAYS_DEPRECATE)


# --- W3 (partial-domain): route the WRONG selector on the legacy-only call.
# Emits the deprecation signal correctly (C5 holds) and refuses correctly, but on
# the legacy-selector-only call it forgets `coord = dim` and routes the (None)
# primary selector instead of `dim`.
# refinement: a real patch that emits the warning but drops the `coord = dim`
# reassignment passes `coord` (still None) into
# `self._to_temp_dataset().integrate(coord, datetime_unit)` — integrating along
# the WRONG/absent coordinate. da.integrate(dim="x") would integrate along None
# (TypeError / wrong axis) rather than "x"; the F2P call (which must SUCCEED and
# return the dim-x integral, only warning) would error — so it does NOT resolve.
# rejection source: C3 `Implies(dim is not None and coord is None, Result().coord
# is dim)` — routing coord (None) instead of dim violates it.
_W3_WRONG_COORD = """    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        # WRONG-ROUTE RIVAL: emit the signal but FORGET coord = dim, leaving coord
        # (None) to be routed instead of the supplied legacy selector dim.
        deprecated = True

    return Routed(coord, deprecated)"""

W3_WRONG_COORD = _swap(_BASE, _IMPL, _W3_WRONG_COORD)


# --- W4 (control-flow-effect): RETURN normally on the both-supplied input instead
# of raising. Routes/deprecates the honoured cases correctly, but on the
# contradictory (both selectors) input it returns Routed(coord, False) rather than
# raising the conflicting-selection failure.
# refinement: a real patch that drops the `if dim is not None and coord is not
# None: raise ValueError(...)` guard would SILENTLY proceed (integrating along
# coord) when a caller passes both `dim=` and `coord=`. The repo conflict semantics
# (the test family asserts `pytest.raises(ValueError)` on a contradictory call) and
# the documented refusal require a raise; the silent-proceed patch would not raise
# and would NOT resolve.
# rejection source: C1 `Ensures(not (dim is not None and coord is not None))` — a
# normal return on the both-supplied input cannot prove this (the verifier requires
# the both-supplied path to NOT return normally, i.e. to raise per C6).
_W4_NO_RAISE = """    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True

    # CONTROL-FLOW RIVAL: never raise the refusal — return normally even when BOTH
    # selectors are supplied (routes coord, the both-supplied default here).
    return Routed(coord, deprecated)"""

W4_NO_RAISE = _swap(_BASE, _IMPL, _W4_NO_RAISE)


# --- W5 (control-flow-effect, supporting): raise UNCONDITIONALLY (refuse every
# call). Trivially "honours" nothing; the refusal is over-broad.
# refinement: a real patch whose guard is `if dim is not None or coord is not None:
# raise ValueError(...)` (or an unconditional raise) refuses the ordinary
# da.integrate("x") / da.integrate(dim="x") calls outright. The F2P call
# da.integrate(dim="x") must SUCCEED (only warning); an unconditional refusal
# raises instead of returning, so it does NOT resolve.
# rejection source: C3/C4 + C5 cannot be discharged on a path that never returns
# normally for the honoured inputs, and the raise on a single-selector input is
# unsanctioned by C6 (which permits the refusal ONLY when BOTH are supplied).
_W5_ALWAYS_RAISE = """    raise ConflictingSelection()"""

W5_ALWAYS_RAISE = _swap(_BASE, _IMPL, _W5_ALWAYS_RAISE)


# --- W6 (control-flow-effect, vacuity): DIVERGE instead of answering on the
# primary-selector path. Handles the refusal and the legacy-only call correctly,
# but on the primary-only / neither-supplied path it spins forever instead of
# returning — every Ensures then holds vacuously (no normal exit on that path).
# refinement: a real patch that hangs on da.integrate("x") / da.integrate(coord="x")
# (e.g. an accidental infinite retry loop before the downstream call) never
# returns; the P2P integrate tests time out — it does NOT resolve. (This is the
# audit P1 witness atk_6: same-spec, verified under the pre-fix contract, and its
# SWE-bench eval timed out after 300s.)
# rejection source: the MustTerminate(2) termination obligation in the
# pre-conditions — the loop takes no termination measure, so Nagini reports an
# obligation leak ("Loop might not take all unsatisfied obligations from the
# context"); without MustTerminate this rival VERIFIED (the pre-fix hole).
_W6_DIVERGE = """    if dim is not None and coord is not None:
        raise ConflictingSelection()

    if dim is not None and coord is None:
        return Routed(dim, True)

    x = 0
    while x == 0:
        x = 0

    return Routed(coord, False)"""

W6_DIVERGE = _swap(_BASE, _IMPL, _W6_DIVERGE)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl: early-return cascade with "
        "no mutable `deprecated` local and no `coord = dim` reassignment; each return "
        "discharges directly against C3/C4/C5/C6. Must verify, else SPEC-TOO-STRONG. "
        "Branch/return reshape only (directive-3 safe: no loop/fold/induction).",
    },
    {
        "id": "admiss-legacy-only",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "constructs the F2P-shaped legacy-only outcome Routed(5, True) "
        "(da.integrate(dim=\"x\")) inside the impl and asserts coord=dim with the "
        "deprecation signal via the Routed constructor's Ensures. The contract must "
        "admit a normal F2P-shaped value, else PRECOND-TOO-STRONG. (No Requires on the "
        "selectors, so the lane confirms the result machinery is satisfiable.)",
    },
    {
        "id": "w1-never-deprecate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_NEVER_DEPRECATE,
        "refinement": "this is the PRE-PATCH DataArray.integrate (route dim through, "
        "never warn). F2P `with pytest.warns(FutureWarning): da.integrate(dim=\"x\")` "
        "asserts a FutureWarning fires; the no-warn patch emits none and pytest.warns "
        "FAILS — it does NOT resolve. (model_prepatch.py reproduces exactly this and "
        "fails C5 — G-DIFF.)",
        "rationale": "rejected by C5 `Result().deprecated == (dim is not None and "
        "coord is None)`: on the legacy-only input the RHS is True but deprecated=False. "
        "THE discriminating clause; partial-domain (legacy-only sub-domain).",
    },
    {
        "id": "w2-always-deprecate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_ALWAYS_DEPRECATE,
        "refinement": "a real patch emitting warnings.warn(FutureWarning) "
        "UNCONDITIONALLY (warning hoisted above the `if dim is not None` guard) warns "
        "on the primary-only call da.integrate(coord=\"x\") too. P2P / the units test "
        "(method(\"integrate\", coord=\"x\")) call via the primary selector expecting "
        "NO FutureWarning; an unconditional warn makes the benign path noisy (and under "
        "a warnings-as-errors filter, fail) — it does NOT resolve.",
        "rationale": "rejected by C5: on the primary-only input (dim==None, coord!=None) "
        "the RHS is False but deprecated=True. Partial-domain (primary-only / "
        "neither-supplied sub-domain).",
    },
    {
        "id": "w3-wrong-coord",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_WRONG_COORD,
        "refinement": "a real patch that emits the warning but DROPS the `coord = dim` "
        "reassignment passes coord (still None) into "
        "self._to_temp_dataset().integrate(coord, datetime_unit) — integrating along "
        "the wrong/absent coordinate. da.integrate(dim=\"x\") would error / integrate "
        "along None instead of \"x\"; the F2P call must succeed returning the dim-x "
        "integral (only warning), so it does NOT resolve.",
        "rationale": "rejected by C3 `Implies(dim is not None and coord is None, "
        "Result().coord is dim)`: routing coord (None) instead of dim violates it. "
        "Partial-domain (legacy-only sub-domain, routing axis).",
    },
    {
        "id": "w4-no-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_NO_RAISE,
        "refinement": "a real patch dropping the `if dim is not None and coord is not "
        "None: raise ValueError(...)` guard SILENTLY proceeds (integrating along coord) "
        "when a caller passes BOTH dim= and coord=. The repo conflict semantics require "
        "a raise (the test family asserts pytest.raises(ValueError) on a contradictory "
        "call); a silent-proceed patch never raises and does NOT resolve.",
        "rationale": "rejected by C1 `Ensures(not (dim is not None and coord is not "
        "None))`: a normal return on the both-supplied input cannot prove it (C6 "
        "requires that path to raise instead). Control-flow-effect (raise vs return).",
    },
    {
        "id": "w5-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_ALWAYS_RAISE,
        "refinement": "a real patch whose guard is `if dim is not None or coord is not "
        "None: raise` (or an unconditional raise) refuses ordinary da.integrate(\"x\") "
        "and da.integrate(dim=\"x\") calls outright. The F2P call da.integrate(dim=\"x\") "
        "must SUCCEED (only warning); an unconditional refusal raises instead of "
        "returning — it does NOT resolve.",
        "rationale": "rejected by C3/C4/C5 (cannot be discharged on a path that never "
        "returns normally for honoured inputs) and by C6, which sanctions the refusal "
        "ONLY when BOTH selectors are supplied — a raise on a single-selector input is "
        "unsanctioned. Supporting control-flow-effect / over-broad-refusal case.",
    },
    {
        "id": "w6-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W6_DIVERGE,
        "refinement": "a real patch that spins forever on the primary-selector path "
        "(da.integrate(\"x\") / da.integrate(coord=\"x\")) never returns; the P2P "
        "integrate tests hang and the harness times out — it does NOT resolve. This "
        "is the audit P1 witness (atk_6): its SWE-bench eval timed out after 300s.",
        "rationale": "rejected by the MustTerminate(2) termination obligation: the "
        "loop carries no termination measure, so Nagini reports an obligation leak. "
        "Under the pre-fix contract (no MustTerminate) this rival VERIFIED — every "
        "Ensures holds vacuously on a path with no normal exit. Vacuity / "
        "control-flow-effect case.",
    },
]


# No @ContractOnly axioms and no A-reference deep models (axioms region empty;
# meta.json axioms == []; refinement.md C: every step is R or I, the routing is
# modeled DEEPLY over its two args, and everything downstream is unchanged /
# independent / unobserved). Nothing for the axiom lane to run.
AXIOM_TESTS = []

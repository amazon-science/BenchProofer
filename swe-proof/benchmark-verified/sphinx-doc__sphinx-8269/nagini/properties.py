# properties.py — PBT falsification battery for sphinx-doc__sphinx-8269.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec verbatim
# (built by region-surgery that edits ONLY the text BETWEEN # impl-start /
# # impl-end, so markers.same_spec is guaranteed) with a swapped impl; the runner
# checks it with the Nagini verifier + markers.same_spec. AXIOM_TESTS are
# real-callee probes run in the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (model.py):
#   classify_fragment_link(status: int, fragment_present: bool) -> Tuple[int, int]
#
#   BOTH inputs are pass-by-VALUE primitives (int, bool). There is NO read-only
#   reference input (no Acc(x, 1/2) on a list/object), so the FRAME-MUTATION
#   class does NOT apply here — there is nothing to overwrite to satisfy the
#   postcondition vacuously. (Stated in 'assessment'; has_readonly_input=False.)
#
#   The precondition carries ONLY the total-correctness obligation
#   Requires(MustTerminate(2)) — no value constraint — so every
#   (status, fragment_present) pair is admissible.
#
#   The postcondition is a TOTAL, fully-GROUNDED dispatch table — six Ensures
#   clauses that together pin Result() for every (status, fragment_present):
#     (1) status == 401                          -> (WORKING,  DATUM_NONE)
#     (2) status == 503                          -> (IGNORED,  DATUM_TRANSPORT)
#     (3) is_error_status & !=401 & !=503         -> (FAILED,   DATUM_TRANSPORT)
#     (4) !is_error_status & fragment_present     -> (WORKING,  DATUM_NONE)
#     (5) !is_error_status & !fragment_present    -> (FAILED,   DATUM_FRAGMENT_ABSENT)
#     (6) is_error_status & Result()[0]==FAILED   -> Result()[1]==DATUM_TRANSPORT
#   The helpers WORKING/FAILED/IGNORED/DATUM_* are constant @Pure codes and
#   is_error_status is a fully-unfolded predicate on `status`. There is NO opaque
#   answer-key / marker oracle to echo — the postcondition IS the dispatch table,
#   grounded entirely in the two inputs. So the UNGROUNDED-ORACLE-ECHO class does
#   NOT apply; the cheapest-impl "echo the F2P answer" attack is covered instead
#   by the constant-return rival (atk-const), which a tight spec must reject.
#
#   The LOAD-BEARING change clauses are (3) and (5)+(6): on an error status the
#   datum is the TRANSPORT error, never the FRAGMENT-ABSENT datum. This is the
#   exact F2P discriminator (a 500 must be reported with the HTTP transport error,
#   not 'Anchor not found'). The pre-patch skeleton (model_prepatch.py) is a
#   PARTIAL-DOMAIN rival on precisely this clause.
#
#   CONTROL-FLOW-EFFECT class: N/A. The function's entire observable is its
#   return tuple (status-class, datum-kind); there is no externally-visible raise
#   or side effect distinct from the value abstraction (the internal
#   TransportError/FragmentAbsent are caught and collapsed into the returned
#   pair). Nothing to discriminate with a capability token.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8269"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region body, VERBATIM (the text between # impl-start and
# # impl-end). Every variant replaces exactly this block, so the spec view (and
# thus same_spec) is byte-identical to model.py.
_IMPL = """    try:
        # Read the whole document and obtain the fragment verdict.
        found = fragment_present
        # The transport-status gate is consulted BEFORE acting on the verdict.
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


def _with_impl(new_impl):
    """Build a full model variant whose impl-region body is `new_impl` (the spec
    view is byte-identical to model.py, so same_spec holds)."""
    return _swap(_BASE, _IMPL, new_impl)


# ===========================================================================
# 1) POSITIVE CONTROL (soundness) — structurally DIFFERENT, but CORRECT.
#    Direct branch-on-status dispatch with NO try/except and NO call to the
#    raise_on_error_status axiom at all (it inspects is_error_status(status)
#    directly). This is a genuinely different executable shape (the gold impl is
#    exception-driven; this is a flat if-ladder) yet pins exactly the same total
#    table. No loop / no induction, so there is no auto-discharge proof gap. MUST
#    verify; else SPEC-TOO-STRONG. (Also demonstrates the spec does not FORCE the
#    gate-call structure — only the resulting classification.)
# ===========================================================================
_POS = """    if is_error_status(status):
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    if not fragment_present:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


# ===========================================================================
# 2) ADMISSIBILITY — the precondition carries only the termination obligation
#    MustTerminate(2) (no value constraint), so every input is admissible. A
#    contract-free module-level caller (injected into the elided impl span so
#    the spec view is untouched) calls classify_fragment_link on the exact
#    F2P-shaped input (status=500 server error, fragment absent); the callee's
#    result is pinned by clause (3) to (FAILED, DATUM_TRANSPORT), asserted
#    inline. The caller holds no obligation of its own, so the callee's
#    MustTerminate poses no obstacle. If this cannot verify =>
#    PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = _IMPL + """


def _admiss_caller() -> None:
    # The F2P scenario: a 500 with the fragment absent is FAILED-with-TRANSPORT,
    # NOT FAILED-with-FRAGMENT-ABSENT. The value-unconstrained precondition
    # admits it (MustTerminate is an obligation, not a value restriction).
    probe = classify_fragment_link(500, False)  # type: Tuple[int, int]
    Assert(probe == (FAILED(), DATUM_TRANSPORT()))"""


# ===========================================================================
# 3) PARTIAL-DOMAIN (the literal pre-patch bug) — gate NEVER consulted.
#    Search the document for the fragment first; if absent, report
#    FRAGMENT_ABSENT without ever testing the transport status. This is
#    model_prepatch.py exactly: correct on the no-fragment-error-free domain
#    (and on present-fragment success), but on an error status with the fragment
#    absent it returns (FAILED, DATUM_FRAGMENT_ABSENT) instead of
#    (FAILED, DATUM_TRANSPORT). MUST be REJECTED by clause (5)/(6) (and (1)/(2)
#    for 401/503 — Nagini reports the first).
# ===========================================================================
_PARTIAL_PREPATCH = """    try:
        found = fragment_present
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


# ===========================================================================
# 4) UNIQUENESS — WRONG ERROR DATUM (the atk9 the audit panel used). The gate is
#    consulted correctly, 401/503 dispatched correctly, but the GENERAL-error
#    branch emits the FRAGMENT-ABSENT datum instead of the TRANSPORT datum. The
#    status-class is still FAILED (matches the repo 'broken'), so this is the
#    subtle hole the load-bearing clause must close: same status-class, WRONG
#    accompanying datum. MUST be REJECTED by clause (3) (and clause (6): an
#    error-status FAILED result must carry DATUM_TRANSPORT).
# ===========================================================================
_WRONG_DATUM = """    try:
        found = fragment_present
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_FRAGMENT_ABSENT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


# ===========================================================================
# 5) PARTIAL-DOMAIN — 401 special-case dropped. 401 falls into the general-error
#    branch -> (FAILED, DATUM_TRANSPORT). Correct on the F2P (500) and every
#    other error, but WRONG on the 'authorization required' status. MUST be
#    REJECTED by clause (1) (status==401 must be (WORKING, DATUM_NONE)).
# ===========================================================================
_DROP_401 = """    try:
        found = fragment_present
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


# ===========================================================================
# 6) PARTIAL-DOMAIN — 503 special-case dropped. 503 falls into the general-error
#    branch -> (FAILED, DATUM_TRANSPORT). Correct on 401, the F2P 500, and every
#    other error, but WRONG on the 'service unavailable' status (must be
#    IGNORED). MUST be REJECTED by clause (2).
# ===========================================================================
_DROP_503 = """    try:
        found = fragment_present
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


# ===========================================================================
# 7) UNIQUENESS — CONSTANT-RETURN "echo the F2P answer" (atk6). Always return
#    (FAILED, DATUM_TRANSPORT): the exact answer the F2P test (500) expects. This
#    is the cheapest impl that satisfies the load-bearing error-status clauses
#    (3)/(6) without doing any work. A tight spec must still reject it because it
#    is WRONG everywhere else: clause (1) (401 must be WORKING) and clause (4)
#    (non-error + fragment present must be WORKING). MUST be REJECTED.
# ===========================================================================
_CONST = """    return (FAILED(), DATUM_TRANSPORT())"""


# ===========================================================================
# 8) VACUOUS NON-TERMINATION (uniqueness) — an impl that never returns. It
#    spins forever before the dispatch, so every value postcondition is
#    satisfiable only vacuously: no execution reaches a return. This is the
#    exact spec-too-weak class the G-PANEL-1 auditor exploited (atk_4: an
#    infinite `while spin` loop verified against the value-only spec; its
#    faithful real patch inserts `while True: pass` into check_uri's fragment
#    branch, hanging the checker thread so the F2P test times out — it does
#    NOT resolve). Under Requires(MustTerminate(2)) the loop takes no
#    termination obligation and has no decreasing measure, so Nagini's
#    obligation system MUST reject it ("Obligation leak check failed"). The
#    loop invariant is exactly what the spinning loop maintains — the reject
#    must come from the obligation system, not a broken proof.
# ===========================================================================
_NONTERM = """    spin = True
    while spin:
        # invariants-start
        Invariant(spin)
        # invariants-end
        spin = True
    try:
        found = fragment_present
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())"""


# ===========================================================================
# 9) PARTIAL-DOMAIN (non-error sub-domain) — fragment-present success path
#    mis-classified. On a non-error status with the fragment PRESENT this returns
#    (FAILED, DATUM_FRAGMENT_ABSENT) instead of (WORKING, DATUM_NONE) (it ignores
#    `found` and always reports fragment-absent on the non-error path). Correct on
#    every error status and on non-error+absent, but WRONG on non-error+present.
#    MUST be REJECTED by clause (4). Supporting partial-domain on the unchanged
#    half of the table (guards the spec didn't only pin the error path).
#
#    NO trailing fall-through return, unlike every other variant here. Because
#    the `raise FragmentAbsent()` is unconditional, this try body cannot complete
#    normally: it either raises the transport error from the gate or raises
#    FragmentAbsent, and both handlers return on every path. A statement after
#    the try is therefore unreachable, and Nagini's mypy front-end refuses the
#    module for it ("Type error: dead.code") BEFORE Viper ever sees a
#    postcondition. Nagini exits 1 for that -- its rejection code -- so with the
#    unreachable return present this case recorded "rejected" in 7.4s (every real
#    verdict in this battery takes 19-25s) on the strength of a front-end crash,
#    proving nothing about the spec: nagini is in the complement of
#    pbt.WITNESS_REQUIRED, so "did not verify" is the WHOLE argument for its
#    rejections and a rival that never translated has not been turned down by
#    anything. Omitting a statement that cannot execute changes no behaviour on
#    any input: the divergence claimed above (non-error + fragment present ->
#    FAILED/FRAGMENT-ABSENT) is exactly as before, and it is now Viper that turns
#    it down, on clause (4) by name.
#
#    NON-VACUITY (measured, SBN_PARALLEL_VERIFIERS=1): the targeted handler is
#    genuinely entered, not skipped by an infeasible guard.
#      * `Assert(False)` as the first statement of the `except FragmentAbsent`
#        arm is REJECTED -- "Assert might fail. Assertion False might not hold"
#        (23.9s) -- so the arm is reachable.
#      * `Assert(not fragment_present)` there is ALSO rejected (26.1s): a state
#        with the fragment PRESENT reaches the arm and returns the
#        fragment-absent datum from it, which is the divergence this case claims.
#      * `Assert(not is_error_status(status))` there HOLDS (the only error is the
#        clause (4) postcondition), so the arm is entered on exactly the
#        non-error sub-domain clause (4) governs -- the rejection is not
#        collateral from some error-status path.
# ===========================================================================
_NONERR_PRESENT = """    try:
        found = fragment_present
        raise_on_error_status(status)
        raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())"""


SPEC_TESTS = [
    {
        "id": "pos-control-flat-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS),
        "rationale": (
            "A structurally-different but CORRECT impl: a flat if-ladder that "
            "branches on is_error_status(status) directly, with NO try/except and "
            "NO call to the raise_on_error_status axiom. It pins exactly the same "
            "total dispatch table (clauses 1-6 all hold) but in a different "
            "executable shape than the exception-driven gold impl. No loop / no "
            "induction => no auto-discharge proof gap. If it cannot verify => "
            "SPEC-TOO-STRONG (the spec would be over-constraining the impl shape "
            "rather than the classification)."),
    },
    {
        "id": "admiss-f2p-shaped-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": (
            "The precondition carries no value constraint (only the termination "
            "obligation MustTerminate(2)), so the F2P-shaped input (status=500, "
            "fragment_present=False) is admissible with no Requires obstacle. A "
            "contract-free module-level caller (injected into the elided impl span "
            "so spec_signature is untouched) calls it and its result is pinned by "
            "clause (3) to (FAILED, DATUM_TRANSPORT) — asserted inline. If this "
            "cannot verify => PRECOND-TOO-STRONG."),
    },
    {
        "id": "partial-prepatch-no-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_PREPATCH),
        "refinement": (
            "This is model_prepatch.py exactly — the pre-patch skeleton with "
            "response.raise_for_status() REMOVED from the fragment branch. On the "
            "F2P scenario (a localhost server answering 500, fragment absent) it "
            "returns (FAILED, DATUM_FRAGMENT_ABSENT), i.e. the repo emits "
            "'[broken] ...: Anchor \\'anchor\\' not found' instead of the required "
            "'[broken] ...: 500 Server Error: Internal Server Error for url: ...'. "
            "The F2P test test_raises_for_invalid_status asserts the exact "
            "transport-error line, so this real patch does NOT resolve."),
        "rationale": (
            "Rejected by the postcondition: for status=503 it returns "
            "(FAILED, DATUM_FRAGMENT_ABSENT) violating clause (2); for a general "
            "error status with fragment absent it returns "
            "(FAILED, DATUM_FRAGMENT_ABSENT) violating clauses (3) and (6); for 401 "
            "absent it violates clause (1). Nagini reports the first. If it "
            "verified => SPEC-TOO-WEAK (the spec would not sense the change)."),
    },
    {
        "id": "wrong-error-datum",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WRONG_DATUM),
        "refinement": (
            "The gate IS consulted and 401/503 dispatched correctly, but the "
            "general-error branch attaches the FRAGMENT-ABSENT datum to a FAILED "
            "result. The repo analogue returns ('broken', \"Anchor 'anchor' not "
            "found\", 0) for a 500 instead of ('broken', '500 Server Error: ... for "
            "url: ...', 0). The status-class 'broken' matches, but the F2P asserts "
            "the EXACT info string is the HTTP transport error, so the printed line "
            "still reads 'Anchor not found' and the F2P test FAILS => does NOT "
            "resolve. This is the subtle hole: right class, wrong datum."),
        "rationale": (
            "Rejected by clause (3) (is_error_status & !=401 & !=503 => "
            "(FAILED, DATUM_TRANSPORT)) and clause (6) (an error-status FAILED "
            "result must carry DATUM_TRANSPORT, never DATUM_FRAGMENT_ABSENT). This "
            "is the discriminating clause the change establishes; if this rival "
            "verified => SPEC-TOO-WEAK on the load-bearing datum."),
    },
    {
        "id": "partial-drop-401",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DROP_401),
        "refinement": (
            "Dropping the 401 special-case sends 'authorization required' into the "
            "general-error branch -> (FAILED, DATUM_TRANSPORT). The repo analogue "
            "would report a 401-anchor link as 'broken' instead of 'working' (the "
            "'- unauthorized' working path). A real patch shaped this way diverges "
            "from the established behaviour the shared HTTPError dispatch encodes "
            "for 401 (which test_auth and the no-fragment path exercise as "
            "working/redirected), so it does not preserve the P2P-tested "
            "classification."),
        "rationale": (
            "Rejected by clause (1): status==401 must be (WORKING, DATUM_NONE) but "
            "this returns (FAILED, DATUM_TRANSPORT). Correct on the F2P (500) and "
            "every other error, so a byte-fuzzer's near-miss would not target it; "
            "the spec pins the 401 sub-domain. If it verified => SPEC-TOO-WEAK on "
            "the 401 special case."),
    },
    {
        "id": "partial-drop-503",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DROP_503),
        "refinement": (
            "Dropping the 503 special-case sends 'service unavailable' into the "
            "general-error branch -> (FAILED, DATUM_TRANSPORT). The repo analogue "
            "would report a 503-anchor link as 'broken' instead of 'ignored' (the "
            "503-is-ignored path the shared HTTPError dispatch encodes). A real "
            "patch shaped this way changes the 503 classification the unchanged "
            "dispatch already establishes, so it does not preserve the tested "
            "behaviour for the service-unavailable status."),
        "rationale": (
            "Rejected by clause (2): status==503 must be (IGNORED, DATUM_TRANSPORT) "
            "but this returns (FAILED, DATUM_TRANSPORT) (wrong status-class). "
            "Correct on the F2P 500 and every other error, so it is a true "
            "sub-domain divergence the spec pins. If it verified => SPEC-TOO-WEAK "
            "on the 503 special case."),
    },
    {
        "id": "const-echo-failed-transport",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_CONST),
        "refinement": (
            "Unconditionally returning (FAILED, DATUM_TRANSPORT) is the cheapest "
            "impl that satisfies the F2P answer (a 500 -> '[broken] ...: 500 Server "
            "Error ...') without doing any classification work. But the repo "
            "analogue would mark EVERY link 'broken' with a transport error — a "
            "working link (200, fragment present) and a 401 link would both be "
            "reported broken, so test_defaults / test_auth / the success P2P cases "
            "FAIL and it does NOT resolve."),
        "rationale": (
            "The grounded total dispatch table has no ungrounded oracle to echo; "
            "the cheapest 'echo the F2P answer' impl is this constant. It is "
            "rejected by clause (1) (401 must be WORKING) and clause (4) (non-error "
            "+ fragment present must be (WORKING, DATUM_NONE)). If it verified => "
            "SPEC-TOO-WEAK (a constant would satisfy the spec)."),
    },
    {
        "id": "vacuous-nonterminating-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NONTERM),
        "refinement": (
            "the rival never returns: it spins in an unbounded loop before the "
            "dispatch, so every value postcondition holds only vacuously and no "
            "classification is ever delivered. Its faithful real patch inserts a "
            "`while True: pass` into check_uri's fragment branch (the exact "
            "G-PANEL-1 atk_4 attack patch): the checker thread hangs, the linkcheck "
            "build never completes, and the F2P test test_raises_for_invalid_status "
            "times out — it does NOT resolve."),
        "rationale": (
            "MUST reject via the OBLIGATION system: the "
            "Requires(MustTerminate(2)) forces every loop on the path to the "
            "return to carry a decreasing termination measure; the spinning loop "
            "has none, so Nagini reports 'Obligation leak check failed'. Rejection "
            "source: the termination obligation, not a value clause — "
            "demonstrating the spec no longer admits vacuous divergence."),
    },
    {
        "id": "partial-nonerror-present-misclassified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NONERR_PRESENT),
        "refinement": (
            "On a non-error status this always raises FragmentAbsent regardless of "
            "`found`, so a working link whose fragment IS present is reported "
            "'broken'/'Anchor not found' instead of 'working'. The repo analogue "
            "breaks the existing success path: test_defaults / test_anchors_ignored "
            "(P2P) expect a present anchor on a 2xx page to be working, so this "
            "real patch FAILS those P2P tests and does NOT resolve."),
        "rationale": (
            "Supporting partial-domain on the UNCHANGED half of the table (guards "
            "that the spec pins more than just the error path). Rejected by clause "
            "(4): not is_error_status & fragment_present must be "
            "(WORKING, DATUM_NONE) but this returns (FAILED, DATUM_FRAGMENT_ABSENT). "
            "If it verified => SPEC-TOO-WEAK on the non-error success sub-domain."),
    },
]


# ===========================================================================
# AXIOM lane. One @ContractOnly A-consumed axiom:
#   raise_on_error_status(status) -> None
#     Ensures(status < 400 or status >= 600)                  # normal => non-error
#     Exsures(TransportError, 400 <= status and status < 600) # raise  => error
# models the UNCHANGED requests.models.Response.raise_for_status() — the callee
# the one added gold line calls. flag_dependency: NONE (raise_for_status takes no
# flag; behaviour is fixed by the 4xx/5xx range checks), so there is no caller
# runtime config to vary.
#
# axiom-soundness: re-run the bundle's own G-AX oracle (axiom_check.py) IN the
# instance image. It constructs a REAL requests.models.Response, sets status_code,
# and runs the REAL raise_for_status() on 33 boundary statuses + the dispatch
# specials (401/503/500/200) + 20000 fuzz over [-50,1200], asserting the callee
# raises HTTPError EXACTLY on [400,600) and returns normally otherwise (and emits
# NO other out-of-band signal). It CALLS the real callee (it does not scrape
# source) and imports only the standard `requests` package (present in the eval
# image). The runner mounts ONLY the probe at /work, so axiom_check.py is read on
# the HOST now and inlined; it runs as __main__ so its sys.exit(main()) fires.
#
# axiom-containment: the model's classify_fragment_link passes `status` (an
# arbitrary int — no value precondition; its only Requires is the MustTerminate
# obligation) straight to raise_on_error_status, and the axiom's VALUE domain is
# unrestricted (its only Requires is likewise the MustTerminate(1) obligation;
# the axiom is total over all int: every status is either in [400,600) -> raise,
# or not -> normal). So every caller-reachable
# callee-input is trivially inside the axiom domain. The containment probe
# witnesses this by driving the REAL raise_for_status over the full reachable
# integer range and asserting it classifies cleanly (raise iff [400,600)) on
# every one — no reachable status is left uncovered. (apply_gold=True so the
# post-patch call-site is what is being justified, though the unchanged callee's
# behaviour is independent of the patch.)
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AXIOM_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "# axiom-soundness for sphinx-doc__sphinx-8269: run the bundle's REAL-callee\n"
    "# G-AX oracle in-container. It executes the real requests.Response.\n"
    "# raise_for_status() on boundary + dispatch-special + 20000 fuzz statuses and\n"
    "# asserts it raises HTTPError EXACTLY on [400,600), returns normally otherwise,\n"
    "# and emits no other out-of-band signal. Exit 0 iff the axiom is sound.\n"
    + _AXIOM_CHECK_SRC
)


# Containment probe: independent of axiom_check.py. The axiom is TOTAL over int
# (no VALUE Requires; its only precondition is the MustTerminate(1) termination
# obligation), and the caller passes an arbitrary `status: int` (no value
# precondition of its own) verbatim. So the full reachable callee-input set is
# all of int, every member of which the axiom partitions cleanly. We witness this
# by driving the REAL raise_for_status across the reachable range and confirming
# the raise/no-raise boundary matches the axiom's [400,600) for every status — no
# reachable input falls outside the axiom's (total) domain.
_AXIOM_CONTAIN_PROBE = r'''# -*- coding: utf-8 -*-
"""axiom-containment for sphinx-doc__sphinx-8269.

raise_on_error_status has no VALUE Requires (its only precondition is the
MustTerminate(1) termination obligation; it is total over every int status:
status in [400,600) => raise TransportError; else => return normally). The
modeled classify_fragment_link passes `status` (an arbitrary int — its own
Requires carries no value constraint) straight to the gate, so the set of
callee-inputs the
caller can REACH is exactly all of int, and every one lies inside the axiom's
(total) domain by construction. This probe witnesses containment by driving the
REAL callee (requests.models.Response.raise_for_status) over the full reachable
integer range — the F2P/dispatch specials plus dense fuzz across negatives,
sub-400, [400,600), and >=600 — and asserting each classifies cleanly on the
axiom boundary. A reachable status the callee handled OUTSIDE the axiom's
raise<=>[400,600) partition would be AXIOM-TOO-WEAK-FOR-CALLER; none exists.
"""
import random
import sys

try:
    import requests
    from requests.exceptions import HTTPError
except Exception as exc:  # pragma: no cover - container guard
    print("containment SKIP: requests unavailable (%r)" % (exc,))
    sys.exit(0)


def in_axiom_domain(status):
    """The axiom is total over int -> every status is in the (raise|normal)
    partition; there is no excluded sub-domain."""
    return True


def observe(status):
    resp = requests.models.Response()
    resp.status_code = status
    resp.url = "http://localhost:7777/"
    resp.reason = "Internal Server Error"
    try:
        resp.raise_for_status()
    except HTTPError:
        return "raise"
    except Exception as other:  # any non-HTTPError out-of-band signal
        return ("other", other)
    return "normal"


# Exactly the callee-inputs classify_fragment_link can reach: an arbitrary int
# status. Enumerate the boundary + dispatch specials, then dense fuzz across the
# whole reachable range so no sub-domain (negative, sub-400, error, >=600) is
# left unwitnessed.
specials = [
    -2 ** 31, -1, 0, 1, 200, 301, 399,
    400, 401, 403, 404, 499,
    500, 503, 504, 599,
    600, 601, 999, 2 ** 31,
]
checked = 0
for s in specials:
    assert in_axiom_domain(s), "reachable status %r outside axiom domain" % (s,)
    out = observe(s)
    assert out in ("raise", "normal"), (
        "callee produced a non-HTTPError out-of-band signal on reachable status "
        "%r: %r — outside the axiom's raise/normal partition" % (s, out))
    err = 400 <= s < 600
    assert (out == "raise") == err, (
        "axiom mis-scoped for caller: reachable status %r -> %r but axiom "
        "partitions raise<=>[400,600)" % (s, out))
    checked += 1

rng = random.Random(8269)
for _ in range(4000):
    s = rng.randint(-2000, 3000)
    assert in_axiom_domain(s), "reachable status %r outside axiom domain" % (s,)
    out = observe(s)
    assert out in ("raise", "normal"), (
        "callee produced a non-HTTPError out-of-band signal on reachable status "
        "%r: %r" % (s, out))
    err = 400 <= s < 600
    assert (out == "raise") == err, (
        "axiom mis-scoped for caller: reachable status %r -> %r but axiom "
        "partitions raise<=>[400,600)" % (s, out))
    checked += 1

print("containment OK: %d caller-reachable callee-inputs (arbitrary int status) "
      "all inside the axiom's total domain; real raise_for_status partitions "
      "raise<=>[400,600) on every one" % checked)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-raise-on-error-status",
        "axiom": "raise_on_error_status",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_SOUND_PROBE,
        "rationale": (
            "Runs the bundle's own G-AX oracle (axiom_check.py) in the eval "
            "container: it EXECUTES the real requests.models.Response."
            "raise_for_status() on 33 boundary statuses + the dispatch specials "
            "(401/503/500/200) + 20000 fuzz over [-50,1200] and asserts it raises "
            "HTTPError EXACTLY on [400,600), returns normally otherwise, and emits "
            "no other out-of-band signal — exactly the axiom's "
            "Ensures(status<400 or status>=600) / "
            "Exsures(TransportError, 400<=status<600). flag_dependency is none, so "
            "there is no caller runtime config to vary. If the real callee violates "
            "the partition on any input => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-contain-raise-on-error-status",
        "axiom": "raise_on_error_status",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AXIOM_CONTAIN_PROBE,
        "rationale": (
            "The axiom has no VALUE Requires (total over every int status; its "
            "only precondition is the MustTerminate(1) obligation), and "
            "classify_fragment_link passes its arbitrary `status` (no caller "
            "value precondition) straight to the gate, so every caller-reachable "
            "callee-input is inside the axiom domain by construction. The probe "
            "witnesses this by driving the REAL raise_for_status across the full "
            "reachable integer range (boundary + dispatch specials + 4000 fuzz over "
            "[-2000,3000]) and asserting each classifies cleanly on the "
            "raise<=>[400,600) partition. A reachable status the callee handled "
            "outside that partition => AXIOM-TOO-WEAK-FOR-CALLER; none exists."),
    },
]

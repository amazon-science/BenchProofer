# properties.py — PBT manifest for sympy__sympy-13372. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# parses. Spec cases are full model.py variants that share the FROZEN spec
# (only the # impl-start/# impl-end region is edited via _swap) and are checked
# by Nagini verify + markers.same_spec; axiom cases (none here) would be real-
# callee probes run in Docker.
#
# Defended surface (reasoned, not mechanical):
#   assemble_evalf_result(re_kind:int, im_kind:int, prec:int) -> EvalfResult
#   classifies each of the real / imaginary part into one of three integer case
#   tags (0 exact-zero, 1 numeric, 2 OTHER) and assembles a result pairing each
#   part with a precision component, OR defers (raises EvalfDeferred) when some
#   part is OTHER. This models the gold fix to sympy/core/evalf.py: adding
#   `else: raise NotImplementedError` to the two classification chains so an
#   unrepresentable part defers instead of falling through to read an unset
#   `reprec`/`imprec` local (the UnboundLocalError of issue 13076 / 13372).
#
#   Load-bearing postconditions (the whole defended surface):
#     P1  Ensures(re_kind != 2 and im_kind != 2)               # normal return ONLY when both representable (THE FIX)
#     P2  Ensures(Acc(Result().reprec) and Acc(Result().imprec))
#     P3  Ensures(Result().reprec is part_precision(re_kind, prec))   # exact precision component (real)
#     P4  Ensures(Result().imprec is part_precision(im_kind, prec))   # exact precision component (imag)
#     X1  Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)  # defer EXACTLY on an OTHER part
#
# Coverage decisions (justified in 'assessment'):
#   * FRAME-MUTATION: N/A. There is NO read-only `Acc(x,1/2)` input — all three
#     params are integer VALUE types and there is no mutable carrier to overwrite
#     to vacuously satisfy a postcondition. (has_readonly_input = False.)
#   * UNGROUNDED-ORACLE: the postcondition oracle `part_precision` is GROUNDED —
#     it is a @Pure function purely of (kind, prec), fully unfoldable by the
#     verifier (None for kind 0, prec for kind 1). There is no opaque answer-key
#     to echo, so an "echo" cannot be wrong-yet-verifying. We instead exercise
#     this clause through the wrong-precision / numeric-as-none rivals below
#     (which DO fail P3/P4) and the cheapest honest positive control.
#   * AXIOM lane: empty — the bundle consumes no @ContractOnly axiom and has no
#     A-reference deep model (pure control-flow / definedness fix).

from pathlib import Path

INSTANCE = "sympy__sympy-13372"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl region body (verbatim, between # impl-start / # impl-end). Every
# rival is produced by _swap on exactly this block, so the frozen spec
# (axioms/pure/pre/post-conditions + signatures) is NEVER touched => same_spec.
_GOLD_IMPL = '''    # Classify the real part. The precision component is set only in the
    # exact-zero and numeric cases; the OTHER case defers before any result is
    # assembled (so no result is ever built around a missing component).
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    else:
        raise EvalfDeferred()
    # Classify the imaginary part identically.
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    else:
        raise EvalfDeferred()
    Assert(reprec is part_precision(re_kind, prec))
    Assert(imprec is part_precision(im_kind, prec))
    return EvalfResult(reprec, imprec)'''

# sanity: the gold body must be present and unique in the frozen model.
assert _GOLD_IMPL in _BASE and _BASE.count(_GOLD_IMPL) == 1, "gold impl drift"


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness, expect=verify) — structurally different but
#    correct. Reorders the per-part branch chain to handle the OTHER case FIRST
#    (early-defer), then a flat if/else for the two representable cases. Keeps
#    the gold framing asserts so the precision pins (P3/P4) still discharge.
#    A correct-but-reshaped impl MUST verify, else SPEC-TOO-STRONG.
_POS = _swap(_BASE, _GOLD_IMPL, '''    # Reordered, still correct: defer FIRST on the OTHER case, then a flat
    # two-way assignment for the exact-zero / numeric cases. Same observable
    # behaviour as gold; only the executable shape differs.
    if re_kind == 2:
        raise EvalfDeferred()
    if im_kind == 2:
        raise EvalfDeferred()
    reprec = prec  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    imprec = prec  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    Assert(reprec is part_precision(re_kind, prec))
    Assert(imprec is part_precision(im_kind, prec))
    return EvalfResult(reprec, imprec)''')


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY (expect=verify) — a self-call caller proves the precondition
#    admits a normal F2P/P2P-shaped input. The F2P witness Mul(Max(0,y), x) has a
#    NUMERIC real part / exact-zero imag part for the representable arm, and the
#    bug-trigger has an OTHER real part. We assert both a representable call
#    (re_kind=1, im_kind=0) returns a result with the right components, and the
#    OTHER call (re_kind=2) defers — proving Requires accepts the real domain.
#    If the call site cannot establish Requires => PRECOND-TOO-STRONG.
_ADM = _swap(_BASE, _GOLD_IMPL, '''    # ADMISSIBILITY probe: drive the function on representative in-domain
    # inputs and confirm both the assemble path and the defer path are admitted
    # for a normal F2P/P2P-shaped call. (Still satisfies every postcondition.)
    Assert(0 <= 1 and 1 <= 2)
    Assert(0 <= 0 and 0 <= 2)
    deferred = False
    if re_kind != 2:
        # The self-call is GUARDED so the recursion is bounded: the callee is
        # entered at re_kind == 2, where this guard is false, so it does not
        # self-call again. The level `6 - re_kind` therefore strictly decreases
        # from this frame (re_kind < 2) to the callee's (re_kind == 2), which is
        # what discharges MustTerminate. Unguarded, this probe recursed on
        # (2, 0, prec) forever. The guard is NOT vacuous: an `Assert(False)`
        # placed inside it is reported unprovable, so the probe still fires.
        try:
            assemble_evalf_result(2, 0, prec)       # OTHER re -> must defer
            Assert(False)
        except EvalfDeferred:
            deferred = True
        Assert(deferred)
    # now produce the contracted result for THIS call exactly as gold does.
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    else:
        raise EvalfDeferred()
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    else:
        raise EvalfDeferred()
    Assert(reprec is part_precision(re_kind, prec))
    Assert(imprec is part_precision(im_kind, prec))
    return EvalfResult(reprec, imprec)''')


# ---------------------------------------------------------------------------
# 3. PREPATCH FALL-THROUGH (uniqueness, expect=reject) — the actual buggy
#    pre-patch shape: the classification chains have NO `else`, so an OTHER part
#    keeps the placeholder None and the function assembles a result instead of
#    deferring. Fails P1 (re_kind != 2 / im_kind != 2 unprovable on an OTHER
#    part) — this is the formal face of `r = re, im, reprec, imprec` reading the
#    unbound local. Mirrors model_prepatch.py.
#    REFINEMENT: the faithful real patch (dropping both `else: raise`) is exactly
#    the pre-patch source — Mul(Max(0,y), x).evalf() raises UnboundLocalError
#    rather than deferring to return 'x*Max(0, y)', so it FAILS the F2P test
#    (test_evalf_bugs). A verifying rival here would be a true verify⇏resolve.
_PREPATCH = _swap(_BASE, _GOLD_IMPL, '''    # PREPATCH (buggy): no else branch; an OTHER part falls through with the
    # placeholder precision local and the result is assembled around it.
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec
    return EvalfResult(reprec, imprec)''')


# ---------------------------------------------------------------------------
# 4. WRONG PRECISION (uniqueness / partial-domain, expect=reject) — correct on
#    the exact-zero and OTHER cases, but on the NUMERIC case assigns the wrong
#    precision component (prec + 1 instead of prec). Diverges ONLY on the numeric
#    sub-domain. Fails P3/P4 (`Result().reprec is part_precision(re_kind, prec)`
#    requires `prec`, not `prec + 1`).
#    REFINEMENT: a real patch that wrote `reprec = prec + 1` for a number would
#    attach the wrong working precision to every numeric part, corrupting the
#    mpmath evaluation of every concrete number — the numeric P2P tests
#    (test_evalf_basic, test_evalf_powers, ...) would fail; it would not resolve.
_WRONG_PREC = _swap(_BASE, _GOLD_IMPL, '''    # WRONG precision on the numeric branch (prec + 1 instead of prec).
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = prec + 1
    else:
        raise EvalfDeferred()
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = prec + 1
    else:
        raise EvalfDeferred()
    return EvalfResult(reprec, imprec)''')


# ---------------------------------------------------------------------------
# 5. NUMERIC-AS-ABSENT (uniqueness / value-level, expect=reject) — treats a
#    NUMERIC part like an exact-zero part: returns None as the precision
#    component for kind 1. Defers correctly on OTHER (so X1 holds and P1 holds)
#    and is correct on the exact-zero case, but fails P3/P4 on the numeric case
#    (`None is part_precision(1, prec)` is `None is prec`, unprovable).
#    REFINEMENT: a real patch that left `reprec = None` for a number would mark
#    every concrete number as an exact zero (prec=None means exact zero per the
#    module), so `_to_mpmath`/the downstream result would treat real numbers as
#    exact 0 — every numeric evalf P2P test would fail; it would not resolve.
_NUM_AS_NONE = _swap(_BASE, _GOLD_IMPL, '''    # NUMERIC mislabelled as exact-zero: no precision component for a number.
    reprec = None  # type: Optional[int]
    if re_kind == 0:
        reprec = None
    elif re_kind == 1:
        reprec = None
    else:
        raise EvalfDeferred()
    imprec = None  # type: Optional[int]
    if im_kind == 0:
        imprec = None
    elif im_kind == 1:
        imprec = None
    else:
        raise EvalfDeferred()
    return EvalfResult(reprec, imprec)''')


# ---------------------------------------------------------------------------
# 6. OVER-DEFER (control-flow-effect, expect=reject) — always defers (raises
#    EvalfDeferred) even when both parts are representable. The deferral is a
#    control-flow effect invisible to a pure value abstraction; the spec
#    discriminates it via X1, which licenses EvalfDeferred ONLY when some part
#    is OTHER. Raising on a representable call (re_kind != 2 and im_kind != 2)
#    violates X1 (and leaves P1..P4 unestablished on the normal path).
#    REFINEMENT: a real patch that raised NotImplementedError unconditionally
#    would make evalf defer on EVERY expression — no number would ever be
#    evaluated; essentially every evalf test (F2P and all numeric P2P) would
#    fail; it would not resolve.
_OVER_DEFER = _swap(_BASE, _GOLD_IMPL, '''    # OVER-DEFER: bail out for every input, even representable parts.
    raise EvalfDeferred()''')


# ---------------------------------------------------------------------------
# 7. SWAPPED COMPONENTS (uniqueness / partial-domain, expect=reject) — assigns
#    the real precision from im_kind and the imaginary precision from re_kind.
#    Identical when re_kind == im_kind, but diverges whenever the two parts'
#    cases differ (e.g. numeric re / exact-zero im, the F2P-adjacent shape).
#    Fails P3 (`Result().reprec is part_precision(re_kind, prec)` but reprec was
#    computed from im_kind) on any asymmetric input.
#    REFINEMENT: a real patch that crossed the reprec/imprec assignments would
#    attach the imaginary part's precision to the real component (and vice
#    versa) in `r = re, im, reprec, imprec` — wrong on every expression with a
#    differently-classified real vs imaginary part (test_evalf_complex,
#    test_evalf_complex_powers, ...); it would not resolve.
_SWAP = _swap(_BASE, _GOLD_IMPL, '''    # SWAPPED: real precision taken from im_kind, imag precision from re_kind.
    if re_kind == 2:
        raise EvalfDeferred()
    if im_kind == 2:
        raise EvalfDeferred()
    reprec = prec  # type: Optional[int]
    if im_kind == 0:
        reprec = None
    imprec = prec  # type: Optional[int]
    if re_kind == 0:
        imprec = None
    return EvalfResult(reprec, imprec)''')


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "a structurally-different but correct impl (early-defer on "
                     "the OTHER case, flat two-way assignment, gold framing "
                     "asserts kept) must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": "self-calls on representative in-domain inputs (numeric/"
                     "exact-zero assemble path AND OTHER defer path) verify, "
                     "proving Requires (0<=kind<=2) admits the normal F2P/P2P "
                     "domain; else PRECOND-TOO-STRONG.",
    },
    {
        "id": "prepatch-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PREPATCH,
        "refinement": "this IS the pre-patch source (no `else: raise`); "
                      "Mul(Max(0,y),x).evalf() raises UnboundLocalError instead "
                      "of deferring to 'x*Max(0, y)', failing the F2P test "
                      "test_evalf_bugs (issue 13076). A verifying rival would be "
                      "a true verify⇏resolve break.",
        "rationale": "rejected by P1 (Ensures(re_kind != 2 and im_kind != 2)): "
                     "on an OTHER part the placeholder-None fall-through cannot "
                     "establish the non-2 guard — the formal face of reading the "
                     "unbound reprec/imprec local.",
    },
    {
        "id": "wrong-precision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_PREC,
        "refinement": "a real patch writing `reprec = prec + 1` for a number "
                      "attaches the wrong working precision to every numeric "
                      "part, corrupting the mpmath evaluation; the numeric P2P "
                      "tests (test_evalf_basic/powers/trig/...) would fail — it "
                      "would not resolve.",
        "rationale": "rejected by P3/P4 (Result().reprec is "
                     "part_precision(re_kind, prec) requires exactly `prec`, but "
                     "the numeric branch yields `prec + 1`).",
    },
    {
        "id": "numeric-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NUM_AS_NONE,
        "refinement": "a real patch leaving `reprec = None` for a number marks "
                      "every concrete number as an exact zero (prec=None means "
                      "exact zero in the module), so downstream evalf treats real "
                      "numbers as 0 — every numeric evalf P2P test would fail; it "
                      "would not resolve.",
        "rationale": "rejected by P3/P4 (Result().reprec is "
                     "part_precision(1, prec) requires `prec`, not None; "
                     "`None is prec` is unprovable for the symbolic prec).",
    },
    {
        "id": "over-defer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _OVER_DEFER,
        "refinement": "a real patch raising NotImplementedError unconditionally "
                      "makes evalf defer on EVERY expression — no number is ever "
                      "evaluated; essentially every evalf test (F2P and all "
                      "numeric P2P) would fail; it would not resolve.",
        "rationale": "rejected by X1 (Exsures(EvalfDeferred, re_kind == 2 or "
                     "im_kind == 2)): EvalfDeferred is licensed ONLY when some "
                     "part is OTHER; raising on a representable call is an "
                     "illegal control-flow effect (and leaves P1..P4 unmet on "
                     "the normal path).",
    },
    {
        "id": "swapped-components",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SWAP,
        "refinement": "a real patch crossing the reprec/imprec assignments in "
                      "`r = re, im, reprec, imprec` attaches the imaginary "
                      "part's precision to the real component (and vice versa) — "
                      "wrong on every expression whose real vs imaginary part is "
                      "classified differently (test_evalf_complex/...); it would "
                      "not resolve.",
        "rationale": "rejected by P3 (Result().reprec is "
                     "part_precision(re_kind, prec)) on any asymmetric input: "
                     "reprec was computed from im_kind, so the pin fails whenever "
                     "re_kind != im_kind.",
    },
]


# No @ContractOnly axiom is consumed and no A-reference deep model is checked
# (pure control-flow / definedness fix; meta.axioms == []). The classification
# <-> precision/defer mapping is validated against real SymPy by axiom_check.py
# / G-AX, not by an axiom obligation. Hence the axiom lane is empty.
AXIOM_TESTS = []

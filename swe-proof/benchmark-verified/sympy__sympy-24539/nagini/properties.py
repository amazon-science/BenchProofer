# properties.py — PBT falsification battery for sympy__sympy-24539.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# byte-for-byte (region-surgery: only the text strictly INSIDE the single
# # impl-start / # impl-end region — which includes the nested invariants — is
# swapped) and is checked by Nagini verify + markers.same_spec. AXIOM_TESTS is
# empty: this bundle has NO @ContractOnly axioms and NO A-reference deep models
# (axioms and pure regions intentionally empty). The only callee downstream of
# the modeled selection is the UNCHANGED, deterministic expr_from_dict, modeled
# directly via the returned selected sequence — there is no axiom obligation a
# Docker probe could falsify (refinement.md / mapping.md "Callee provenance").
#
# Defended surface (model.py `select_render_symbols`):
#   select_render_symbols(symbols, default_symbols, ngens) -> List[int]
#     READ-ONLY inputs  symbols, default_symbols  (both Acc(list_pred(.),1/2))
#     Requires: ngens == len(default_symbols)
#     Ensures:
#       (E0) Acc(list_pred(symbols),1/2) and Acc(list_pred(default_symbols),1/2)
#            -- inputs preserved (read-only round-trips)
#       (E1) len(symbols) == 0 or len(symbols) == ngens
#            -- a VALUE is produced only on the non-rejected domain (so a
#               returned value on the wrong-count case is forbidden)
#       (E2) Implies(len(symbols)==ngens and len(symbols)>0,
#                    ToSeq(Result()) == ToSeq(symbols))
#            -- THE FIX: a correctly-sized SUPPLIED sequence is the selected one,
#               element-for-element, never the default
#       (E3) Implies(len(symbols)==0, ToSeq(Result()) == ToSeq(default_symbols))
#            -- no symbols supplied => the ring's own defaults are selected
#     Exsures(SymbolCountError, ... len(symbols)>0 and len(symbols)!=ngens)
#       -- the error is admissible ONLY on the non-empty wrong-count case
#
# The postcondition is GROUNDED entirely in the input carriers (ToSeq equality to
# `symbols` / `default_symbols`); there is NO @Pure answer-key / opaque oracle to
# echo, so the ungrounded-oracle-echo class is N/A (see 'assessment'). The strong,
# applicable classes are FRAME-MUTATION (both inputs are read-only — MANDATORY),
# PARTIAL-DOMAIN (the pre-patch bug, plus a drop-last off-by-one), and
# CONTROL-FLOW-EFFECT (return-instead-of-raise on the wrong-count case), plus a
# structurally-different positive control and an admissibility self-call.
from pathlib import Path

INSTANCE = "sympy__sympy-24539"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The verbatim gold impl body (the text strictly INSIDE # impl-start/# impl-end,
# nested invariants included). Every variant is _BASE with this block replaced
# by an alternative body that touches ONLY the impl region -> markers.same_spec
# holds by construction (the frozen pre/post-conditions are never edited).
# ---------------------------------------------------------------------------
_GOLD = """    if len(symbols) == 0:
        src = default_symbols  # type: List[int]
    elif len(symbols) != ngens:
        raise SymbolCountError()
    else:
        src = symbols
    # Materialise the selected sequence (a fresh carrier element-for-element
    # equal to `src`); the downstream builder reads this sequence.
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(Implies(len(symbols) == 0, src is default_symbols))
        Invariant(Implies(len(symbols) > 0, src is symbols))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result"""


# ===========================================================================
# (1) FRAME-MUTATION — MANDATORY: `symbols` is read-only (Acc(list_pred,1/2)).
# A rival that WRITES to `symbols` to "build" the selection must be rejected for
# INSUFFICIENT PERMISSION. The write (symbols[0] = symbols[0]) is a value no-op,
# so a fold over the value abstraction would still look correct; the spec must
# reject it on PERMISSION grounds, not value grounds. Everything else is the gold
# body verbatim so the rejection is attributable SOLELY to the write.
# ===========================================================================
_frame_mut_symbols = _swap(
    _BASE,
    _GOLD,
    """    if len(symbols) == 0:
        src = default_symbols  # type: List[int]
    elif len(symbols) != ngens:
        raise SymbolCountError()
    else:
        src = symbols
    if len(symbols) > 0:
        symbols[0] = symbols[0]  # WRITE to read-only input -> insufficient permission
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(Implies(len(symbols) == 0, src is default_symbols))
        Invariant(Implies(len(symbols) > 0, src is symbols))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result""",
)


# ===========================================================================
# (1b) FRAME-MUTATION on the OTHER read-only input `default_symbols`. Same
# class, different operand: write to default_symbols[0] needs full permission
# the caller does not hold. Kept gold-verbatim otherwise.
# ===========================================================================
_frame_mut_default = _swap(
    _BASE,
    _GOLD,
    """    if len(symbols) == 0:
        src = default_symbols  # type: List[int]
    elif len(symbols) != ngens:
        raise SymbolCountError()
    else:
        src = symbols
    if len(default_symbols) > 0:
        default_symbols[0] = default_symbols[0]  # WRITE to read-only input -> insufficient permission
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(Implies(len(symbols) == 0, src is default_symbols))
        Invariant(Implies(len(symbols) > 0, src is symbols))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result""",
)


# ===========================================================================
# (2) PARTIAL-DOMAIN — the PRE-PATCH bug (model_prepatch.py): ALWAYS select the
# default symbols, discarding a correctly-sized supplied sequence. Correct on the
# empty-supplied sub-domain (E3) but WRONG on the discriminating sub-domain
# len(symbols)==ngens>0 (E2): renders over the defaults, not the supplied symbols.
# Refinement: this is exactly the reported bug — pre-patch the `else` arm fired on
# every non-rejected path so f.as_expr(U,V,W) rendered over x,y,z and equalled f
# (3*x**2*y - ...), not g. The F2P assert f.as_expr(U,V,W) == g FAILS, so the
# faithful real patch does NOT resolve.
# ===========================================================================
_prepatch_always_default = _swap(
    _BASE,
    _GOLD,
    """    if len(symbols) != 0 and len(symbols) != ngens:
        raise SymbolCountError()
    # PRE-PATCH BUG: the `else` arm fires on every non-rejected path, so a
    # correctly-sized supplied sequence is silently discarded and the ring's own
    # default symbols are used instead.
    src = default_symbols  # type: List[int]
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(src is default_symbols)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result""",
)


# ===========================================================================
# (3) PARTIAL-DOMAIN — drop-last (off-by-one). Correct on the FRONT of the
# selected sequence but stops the materialisation loop one element early, so the
# returned sequence is src[:-1] (missing the final generator). Violates E2 (and
# E3) whenever the selected sequence is non-empty: ToSeq(Result()) ==
# ToSeq(src).take(n-1) != ToSeq(src).
# Refinement: a faithful patch that hands expr_from_dict the supplied symbols
# with the last one dropped (gens[:-1]) renders a polynomial over too few
# generators -> for f.as_expr(U,V,W) the term -U*V*W loses its W factor (and the
# zip in expr_from_dict drops the last monomial exponent), so the result != g.
# F2P f.as_expr(U,V,W) == g FAILS -> does NOT resolve.
# ===========================================================================
_drop_last = _swap(
    _BASE,
    _GOLD,
    """    if len(symbols) == 0:
        src = default_symbols  # type: List[int]
    elif len(symbols) != ngens:
        raise SymbolCountError()
    else:
        src = symbols
    result = []  # type: List[int]
    i = 0
    n = len(src)
    # DROP-LAST: stop one element short, so result == src[:-1].
    if n > 0:
        n = n - 1
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n <= len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(Implies(len(symbols) == 0, src is default_symbols))
        Invariant(Implies(len(symbols) > 0, src is symbols))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    return result  # ToSeq(result) == ToSeq(src).take(len(src)-1): last element dropped""",
)


# ===========================================================================
# (4) CONTROL-FLOW-EFFECT — return-instead-of-raise on the wrong-count case.
# Instead of raising on a non-empty wrong-length supply, this rival RETURNS the
# default symbols. It produces a VALUE on an input where len(symbols)>0 and
# len(symbols)!=ngens, which violates E1 (len(symbols)==0 or len(symbols)==ngens
# must hold whenever a value is returned).
# Refinement: a faithful patch that silently falls back to the ring defaults on a
# wrong-count supply renders an expression instead of erroring, so the F2P arm
# raises(ValueError, lambda: f.as_expr(X)) FAILS (no ValueError) -> does NOT
# resolve. The raise difference is a control-flow effect the value abstraction
# would otherwise miss; here E1 forbids the value altogether.
# ===========================================================================
_no_raise = _swap(
    _BASE,
    _GOLD,
    """    if len(symbols) == ngens and len(symbols) > 0:
        src = symbols  # type: List[int]
    else:
        # WRONG: never raise -- fall back to the defaults even on a non-empty
        # wrong-count supply (returns a value where the contract forbids one).
        src = default_symbols
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result""",
)


# ===========================================================================
# (5) POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT: the
# three-way selection is REORDERED (raise-guard checked first, then the empty
# case, then the matching case) while the materialisation loop and ALL gold
# invariants/framing Asserts are kept VERBATIM (pilot warnings #2/#3: no dropped
# framing assert, no loop-direction flip against the front-prefix ToSeq.take
# invariant). Behaviourally identical to the gold. MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================
_pos_ctrl_reorder = _swap(
    _BASE,
    _GOLD,
    """    if len(symbols) != 0 and len(symbols) != ngens:
        raise SymbolCountError()
    elif len(symbols) == 0:
        src = default_symbols  # type: List[int]
    else:
        src = symbols
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(Implies(len(symbols) == 0, src is default_symbols))
        Invariant(Implies(len(symbols) > 0, src is symbols))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result""",
)


# ===========================================================================
# (6) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input. A
# self-call on the discriminating witness (3 supplied symbols == ngens==3, plus 3
# distinct defaults) forces Requires(ngens == len(default_symbols)) and both
# Acc(list_pred,1/2) halves to be discharged at the call site for freshly-built
# in-domain lists; the returned 1/2 permissions round-trip. We then assert the
# postcondition's fix clause (E2) on the probe result before running the real
# gold body on the actual inputs. If the precondition rejected this normal input,
# PRECOND-TOO-STRONG.
# ===========================================================================
_admiss_selfcall = _swap(
    _BASE,
    _GOLD,
    """    # Admissibility: a representative F2P-shaped self-call (3 supplied symbols
    # matching ngens==3, 3 distinct defaults). The Requires must be establishable.
    probe_syms = [7, 8, 9]  # type: List[int]
    probe_def = [1, 2, 3]  # type: List[int]
    probe = select_render_symbols(probe_syms, probe_def, 3)  # type: List[int]
    # The fix clause (E2): a correctly-sized supplied sequence is the selected one.
    Assert(ToSeq(probe) == ToSeq(probe_syms))
    # Real gold logic on the actual inputs (unchanged behaviour).
    if len(symbols) == 0:
        src = default_symbols  # type: List[int]
    elif len(symbols) != ngens:
        raise SymbolCountError()
    else:
        src = symbols
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(symbols), 1 / 2))
        Invariant(Acc(list_pred(default_symbols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(src))
        Invariant(len(symbols) == 0 or len(symbols) == ngens)
        Invariant(Implies(len(symbols) == 0, src is default_symbols))
        Invariant(Implies(len(symbols) > 0, src is symbols))
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        c = src[i]
        Assert(ToSeq(src).take(i + 1) == ToSeq(src).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(src).take(n) == ToSeq(src))
    return result""",
)


SPEC_TESTS = [
    {
        "id": "frame-mut-symbols",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_symbols,
        "refinement": (
            "symbols[0] = symbols[0] is a VALUE no-op, so a 'faithful' patch that "
            "mutates the supplied symbol sequence in place would still hand the "
            "same gens to expr_from_dict and could look correct on the F2P value "
            "checks -- the value abstraction is blind to the write. The spec must "
            "reject it on PERMISSION grounds: the contract grants only "
            "Acc(list_pred(symbols),1/2), a read-only view, mirroring the real "
            "as_expr which only READS the *symbols var-args (a tuple, in fact "
            "immutable) into expr_from_dict. A patch that mutates the caller's "
            "supplied symbols is not what the gold does and would corrupt caller "
            "state, so it is unfaithful."
        ),
        "rationale": (
            "Rejection comes from the permission system: symbols[0]=symbols[0] "
            "needs full write permission to list_pred(symbols) but the "
            "precondition/invariant grant only 1/2. INSUFFICIENT PERMISSION, not a "
            "postcondition failure."
        ),
    },
    {
        "id": "frame-mut-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_default,
        "refinement": (
            "Same frame-mutation class on the OTHER read-only input. "
            "default_symbols[0]=default_symbols[0] is a value no-op; a patch that "
            "mutates self.ring.symbols would still select the same gens and could "
            "pass the F2P value checks, but it would corrupt the SHARED ring's "
            "generator tuple (cached on the PolyRing) -- the real as_expr never "
            "mutates self.ring.symbols. Unfaithful; the spec must reject on "
            "permission grounds."
        ),
        "rationale": (
            "Rejection from the permission system: assigning default_symbols[0] "
            "needs full list_pred(default_symbols) permission; the caller holds "
            "only 1/2."
        ),
    },
    {
        "id": "uniq-prepatch-always-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _prepatch_always_default,
        "refinement": (
            "This is exactly model_prepatch.py / the reported bug: the old `else` "
            "arm fired on every non-rejected path, so a correctly-sized supplied "
            "sequence was discarded and self.ring.symbols used instead. With f "
            "built over x,y,z, f.as_expr(U,V,W) rendered over x,y,z and equalled f "
            "(3*x**2*y - x*y*z + 7*z**3 + 1), NOT g (the same polynomial in u,v,w). "
            "The F2P assert f.as_expr(U,V,W) == g FAILS, so this faithful patch "
            "does NOT resolve."
        ),
        "rationale": (
            "Violates Ensures (E2) Implies(len(symbols)==ngens and len(symbols)>0, "
            "ToSeq(Result())==ToSeq(symbols)): it returns ToSeq(default_symbols), "
            "which differs from ToSeq(symbols) whenever the supplied sequence "
            "differs from the defaults. The rejection is the discriminating fix "
            "clause."
        ),
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop_last,
        "refinement": (
            "Stopping the materialisation one element short hands expr_from_dict a "
            "gens sequence missing its final generator (gens[:-1]). For "
            "f.as_expr(U,V,W) the term -U*V*W loses its W factor and expr_from_dict's "
            "zip(gens, monom) drops the last exponent on every monomial, so the "
            "rendered expression != g. The F2P assert f.as_expr(U,V,W) == g FAILS "
            "(and a length-1 supply that should equal a single symbol renders the "
            "bare coefficient) -> does NOT resolve."
        ),
        "rationale": (
            "Violates Ensures (E2)/(E3): ToSeq(Result()) == ToSeq(src).take(n-1) "
            "!= ToSeq(src) for every non-empty selected sequence. Targets the "
            "tail-of-sequence sub-domain that a head-only check would miss."
        ),
    },
    {
        "id": "uniq-no-raise-wrong-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_raise,
        "refinement": (
            "A faithful patch that silently falls back to the ring defaults on a "
            "wrong-count supply (instead of raising) renders an expression rather "
            "than erroring. The F2P arm raises(ValueError, lambda: f.as_expr(X)) -- "
            "where X is a single symbol and ngens==3 -- then FAILS (no ValueError "
            "is raised), so this patch does NOT resolve."
        ),
        "rationale": (
            "Violates Ensures (E1) len(symbols)==0 or len(symbols)==ngens: on an "
            "input with len(symbols)>0 and len(symbols)!=ngens it RETURNS a value, "
            "which E1 forbids (only the Exsures raise path is admissible there). "
            "A control-flow / raise difference the value-only abstraction would "
            "miss is caught by the value-production guard E1."
        ),
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl_reorder,
        "rationale": (
            "A structurally-different but behaviourally-identical impl: the "
            "three-way selection is reordered (raise-guard first, then empty, then "
            "matching) while the materialisation loop and ALL gold invariants and "
            "framing Asserts are kept verbatim. The branch reorder is logically "
            "equivalent (Implies(len(symbols)>0, src is symbols) still holds: a "
            "non-empty supply that survives the guard has len==ngens and falls to "
            "the else). It must verify; if it cannot, SPEC-TOO-STRONG. Pilot-safe: "
            "no loop-direction flip, no dropped framing assert."
        ),
    },
    {
        "id": "admiss-f2p-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_selfcall,
        "rationale": (
            "Self-call on the discriminating F2P-shaped input "
            "select_render_symbols([7,8,9], [1,2,3], 3) forces "
            "Requires(ngens == len(default_symbols)) and both Acc(list_pred,1/2) "
            "halves to be discharged at the call site for freshly-built in-domain "
            "lists; the probe then asserts the fix clause E2 (the supplied [7,8,9] "
            "is selected). If the precondition rejected this normal input, "
            "PRECOND-TOO-STRONG. Uses only permissions the gold proof already holds."
        ),
    },
]


# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.axioms == []; meta.deep_model_references == []; the axioms and pure
# regions of model.py are empty). The only callee downstream of the modeled
# selection is the UNCHANGED, deterministic expr_from_dict, captured directly via
# the returned selected sequence (refinement.md, all rows R/I; mapping.md "Callee
# provenance"). There is no axiom-soundness / axiom-containment obligation a
# Docker probe could falsify here, so the axiom lane is empty.
AXIOM_TESTS = []

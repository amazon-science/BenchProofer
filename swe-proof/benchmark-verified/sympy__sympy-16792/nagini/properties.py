# properties.py — PBT falsification battery for sympy__sympy-16792.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions) byte-for-byte and edits ONLY the impl region
# (lines 120-166, between # impl-start / # impl-end, which the spec_view elides —
# so same_spec is guaranteed by construction). Each is checked by Nagini verify
# + markers.same_spec on the host.
#
# Defended surface (read from model.py / refinement.md / axiom_check.py):
#   pointer_flags(kinds: List[int], present: List[bool]) -> List[bool]
#   * BOTH inputs are READ-ONLY: Requires/Ensures carry Acc(list_pred(kinds),1/2)
#     and Acc(list_pred(present),1/2). => FRAME-MUTATION is mandatory.
#   * Load-bearing postcondition (the only thing pinning the output values):
#       Forall i in [0,len): Result()[i] == want_pointer(kinds[i], present[i])
#     plus  len(Result()) == len(kinds).
#   * want_pointer is a @Pure helper fully GROUNDED in the args (it unfolds to
#       array_resolved(k,present) = (k==1) or (k==2 and present)) — there is NO
#     opaque answer-key oracle to echo, so "ungrounded-oracle echo" is N/A; a
#     literal echo of want_pointer is the honest cheapest correct impl, used as
#     the positive control instead (see 'assessment').
#   * The F2P scenario (test_ccode_unused_array_arg) is exactly kind=1 (matrix),
#     present=False -> MUST be a pointer (True). The prepatch bug renders it as a
#     scalar (False). The two adversarial partial-domain rivals attack precisely
#     this matrix/indexed sub-domain split.
#   * No @ContractOnly axioms (axioms region empty); the array-ness + prototype
#     rendering are deep A-reference models validated out-of-band by axiom_check.py
#     (G-AX). The PBT axiom lane therefore re-runs that same real-callee check as
#     an axiom-soundness probe (the deep model must equal the real sympy callee on
#     the F2P scenario + boundary + fuzz). No axiom-containment case: there is no
#     consumed axiom whose Requires domain could be under-scoped.

from pathlib import Path

INSTANCE = "sympy__sympy-16792"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# The gold decision block inside the impl region (lines 146-154). Every variant
# edits text INSIDE the impl region only — never the frozen spec above it.
_GOLD_DECISION = """        if shape_is_intrinsic(k):
            has_dims = True
        elif k == 2:
            if is_present:
                has_dims = True
            else:
                has_dims = False
        else:
            has_dims = False"""


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — structurally different but CORRECT.
# Branch-reorder: test scalar first, matrix second, collapse the nested
# indexed `if is_present` into `has_dims = is_present`. Produces the IDENTICAL
# has_dims for every (k, present), so flag == want_pointer holds and every gold
# framing assert / loop invariant still discharges. Must VERIFY (else
# SPEC-TOO-STRONG). Keeps all asserts (pilot bug #2 avoided).
# ---------------------------------------------------------------------------
_POS = _swap(
    _BASE,
    _GOLD_DECISION,
    """        if k == 0:
            has_dims = False
        elif k == 1:
            has_dims = True
        else:
            has_dims = is_present""",
)


# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — a fresh module-level caller that constructs an F2P-shaped
# input (single absent matrix argument: kinds=[1], present=[False]), establishes
# the Requires, calls pointer_flags, and asserts the result matches want_pointer
# (the absent matrix is a pointer — the discriminating F2P clause). Must VERIFY
# (else PRECOND-TOO-STRONG). The caller is injected BETWEEN `return result` and
# the terminal `# impl-end`, so it lands INSIDE the elided impl span (same_spec
# preserved) yet is a genuine module-level function Nagini independently checks.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE,
    "    return result\n    # impl-end",
    "    return result\n"
    "\n"
    "\n"
    "def _admiss_caller() -> None:\n"
    "    # F2P-shaped input: a single matrix argument absent from the expression.\n"
    "    kinds = [1]  # type: List[int]\n"
    "    present = [False]  # type: List[bool]\n"
    "    Assert(len(kinds) == len(present))\n"
    "    Assert(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),\n"
    "                                          0 <= kinds[i] and kinds[i] <= 2),\n"
    "                                   [[kinds[i]]])))\n"
    "    out = pointer_flags(kinds, present)\n"
    "    # the absent matrix MUST be a pointer (the discriminating F2P clause)\n"
    "    Assert(len(out) == 1)\n"
    "    Assert(out[0] == want_pointer(1, False))\n"
    "    # impl-end",
)


# ---------------------------------------------------------------------------
# 3a. PARTIAL-DOMAIN (uniqueness) — the EXACT prepatch bug. Correct on scalars
# and indexed arrays and PRESENT matrices, but an ABSENT matrix (kind=1,
# present=False — the F2P scenario) is given no dimensions (scalar) instead of a
# pointer. Diverges only on that one sub-domain. Must REJECT: the loop-body
# Assert(flag == want_pointer(k,is_present)) / the loop invariant / the
# postcondition Forall all pin Result()[i] == want_pointer(kinds[i],present[i]),
# and want_pointer(1, False) == True while this impl yields False.
# ---------------------------------------------------------------------------
_PARTIAL_ABSENT_MATRIX = _swap(
    _BASE,
    """        if shape_is_intrinsic(k):
            has_dims = True
        elif k == 2:""",
    """        if shape_is_intrinsic(k):
            has_dims = is_present
        elif k == 2:""",
)


# ---------------------------------------------------------------------------
# 3b. PARTIAL-DOMAIN (uniqueness) — the OTHER sub-domain. Correct on matrices
# and scalars and PRESENT indexed arrays, but an ABSENT indexed array (kind=2,
# present=False) is wrongly promoted to a pointer. Diverges only on that
# sub-domain (want_pointer(2, False) == False; this impl yields True). Must
# REJECT for the same postcondition clause.
# ---------------------------------------------------------------------------
_PARTIAL_ABSENT_INDEXED = _swap(
    _BASE,
    """        elif k == 2:
            if is_present:
                has_dims = True
            else:
                has_dims = False
        else:""",
    """        elif k == 2:
            has_dims = True
        else:""",
)


# ---------------------------------------------------------------------------
# 4. FRAME-MUTATION (uniqueness, MANDATORY — both inputs are Acc(...,1/2)).
# A rival that WRITES to the read-only `kinds` input to force every argument to
# the matrix kind (k=1), then computes the now-trivially-correct flags. Under
# Acc(list_pred(kinds), 1/2) a store kinds[j] = 1 has INSUFFICIENT permission, so
# Nagini MUST reject. Gold invariants/asserts kept verbatim so the rejection is
# attributable to the write, not a proof gap.
# ---------------------------------------------------------------------------
_FRAME_KINDS = _swap(
    _BASE,
    """        k = kinds[j]
        is_present = present[j]""",
    """        kinds[j] = 1  # frame violation: write a 1/2-permission read-only input
        k = kinds[j]
        is_present = present[j]""",
)

# 4b. FRAME-MUTATION on the OTHER read-only input (present). Writes present[j]=True
# so an absent matrix/indexed array looks present. Same insufficient-permission
# rejection.
_FRAME_PRESENT = _swap(
    _BASE,
    """        k = kinds[j]
        is_present = present[j]""",
    """        present[j] = True  # frame violation: write a 1/2-permission read-only input
        k = kinds[j]
        is_present = present[j]""",
)


# ---------------------------------------------------------------------------
# 5. LENGTH-CLASS partial-domain (uniqueness, supporting). A rival whose loop
# stops one element early, so the LAST requested argument carries no flag. Correct
# values for every emitted flag, but len(Result()) == len(kinds) - 1. Must REJECT
# on the postcondition len(Result()) == len(kinds). Refinement: dropping the last
# argument's flag drops the final function parameter from the generated C
# prototype, so the prototype is wrong and the F2P/P2P assertions fail.
# ---------------------------------------------------------------------------
_LEN_SHORT = _swap(
    _BASE,
    """    j = 0
    while j < len(kinds):""",
    """    j = 0
    while j < len(kinds) - 1:""",
)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "structurally-different CORRECT impl (scalar-first branch order, "
            "indexed branch collapsed to `has_dims = is_present`) produces the "
            "identical has_dims for every (k,present); flag == want_pointer holds "
            "and every gold framing assert/loop invariant discharges. Must verify "
            "(else SPEC-TOO-STRONG). All gold asserts kept (avoids pilot bug #2)."
        ),
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "a contract-free caller (_admiss_caller, appended OUTSIDE all regions "
            "so spec_signature is untouched) constructs the F2P-shaped input "
            "kinds=[1], present=[False], establishes the Requires, calls "
            "pointer_flags, and asserts out[0] == want_pointer(1,False) (== True, "
            "the absent-matrix-is-a-pointer clause). If the call site cannot "
            "establish the precondition for this legitimate input => "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "partial-absent-matrix-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_ABSENT_MATRIX,
        "refinement": (
            "this is the prepatch behaviour: a matrix absent from the expression "
            "gets has_dims = is_present (i.e. False), so it is rendered `double x` "
            "(scalar) instead of `double *x` (pointer). Its faithful real patch is "
            "exactly `InputArgument(symbol)` with no dimensions in the KeyError "
            "branch — which FAILS test_ccode_unused_array_arg (the F2P), so the "
            "real patch does NOT resolve. A verifying rival here would be a true "
            "verify-without-resolve break."
        ),
        "rationale": (
            "rejected by the loop-body Assert(flag == want_pointer(k,is_present)) "
            "and the postcondition Forall: want_pointer(1,False)==True but this "
            "impl yields False on the absent-matrix sub-domain. Rejection source: "
            "the load-bearing postcondition clause Result()[i]==want_pointer(...)."
        ),
    },
    {
        "id": "partial-absent-indexed-overpromote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_ABSENT_INDEXED,
        "refinement": (
            "an absent indexed array (kind=2, present=False) is wrongly promoted "
            "to a pointer. The real sympy code normalises an IndexedBase in "
            "argument_sequence to its scalar .label BEFORE the KeyError branch, so "
            "isinstance(label,(IndexedBase,MatrixSymbol)) is False and an absent "
            "indexed array is NOT promoted — it renders as a scalar. A faithful "
            "patch that promoted it (e.g. dropping the label-normalisation or "
            "matching IndexedBase) would render `double *A` where gold renders "
            "`double A`, diverging from gold on that sub-domain; the P2P codegen "
            "assertions over indexed args would no longer match gold output."
        ),
        "rationale": (
            "rejected by the postcondition Forall: want_pointer(2,False)==False "
            "but this impl yields True on the absent-indexed sub-domain. Rejection "
            "source: Result()[i]==want_pointer(...)."
        ),
    },
    {
        "id": "frame-mutation-kinds",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_KINDS,
        "refinement": (
            "writes the read-only `kinds` input (kinds[j]=1) to force every "
            "argument to the matrix kind, making the postcondition trivially "
            "satisfiable for the mutated input. A faithful real patch cannot "
            "rewrite the caller's argument_sequence types — it would reclassify "
            "scalars/indexed args as matrices and render them as pointers, "
            "producing wrong C prototypes for every non-matrix argument, so it "
            "does NOT resolve the P2P scalar/indexed scenarios."
        ),
        "rationale": (
            "MUST reject for INSUFFICIENT PERMISSION: Requires/Ensures hold only "
            "Acc(list_pred(kinds), 1/2) (read-only), so the store kinds[j]=1 is not "
            "permitted. Rejection source: the fractional-permission system, not the "
            "value postcondition. A byte-fuzzer never constructs this. (MANDATORY "
            "frame-mutation case — read-only input present.)"
        ),
    },
    {
        "id": "frame-mutation-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_PRESENT,
        "refinement": (
            "writes the read-only `present` input (present[j]=True) so an absent "
            "argument looks present, vacuously satisfying the postcondition for the "
            "mutated input. A faithful real patch cannot rewrite which symbols "
            "occur in the wrapped expression; pretending an absent indexed array is "
            "present would render it `double *A` instead of `double A`, diverging "
            "from gold, so it does NOT resolve."
        ),
        "rationale": (
            "MUST reject for INSUFFICIENT PERMISSION: only Acc(list_pred(present), "
            "1/2) is held (read-only), so present[j]=True is not permitted. "
            "Rejection source: the fractional-permission system. Second read-only "
            "input attacked."
        ),
    },
    {
        "id": "length-short-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _LEN_SHORT,
        "refinement": (
            "the loop stops one element early (j < len(kinds)-1), so the LAST "
            "requested argument carries no flag. Every emitted flag is correct but "
            "the output has one fewer entry. A faithful real patch that omitted the "
            "last argument from new_args would drop the final parameter from the "
            "generated C prototype, breaking the F2P (single-arg) scenario and the "
            "P2P multi-arg prototypes, so it does NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition len(Result()) == len(kinds): this impl "
            "yields len == len(kinds)-1. Supporting length-class partial-domain "
            "case; rejection source: the cardinality postcondition clause."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE.
# meta.axioms == [] (no @ContractOnly axioms). The array-ness decision and the
# C-prototype pointer rendering are DEEP A-reference models (want_pointer /
# array_resolved / arg_is_pointer), validated == the real sympy callees by
# axiom_check.py (G-AX). We re-run that real-callee soundness obligation here as
# a single axiom-soundness probe: the deep model must equal the real
# CCodeGen.routine + get_prototype on the F2P scenario + boundary + fuzz. There
# is NO axiom-containment case — there is no consumed axiom whose Requires domain
# could be under-scoped for the caller (the A-reference covers all three kinds x
# present/absent, which is exactly what the model can reach).
#
# axiom_check.py imports only sympy (the module under change) and runs entirely
# in-container against the patched sympy. The probe below embeds the HOST copy of
# axiom_check.py's source (read at manifest-load time per pilot bug #6 — the
# runner mounts ONLY the probe at /work) and executes its main(), exiting 0 iff
# every real-callee obligation holds.
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

_AX_PROBE = (
    "import sys\n"
    "AXIOM_CHECK_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__axiom_check__'}\n"
    "exec(compile(AXIOM_CHECK_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom-soundness probe rc =', rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-deep-model-vs-real-prototype",
        "axiom": "want_pointer/array_resolved/arg_is_pointer (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "the deep model (matrix => pointer always; indexed => pointer iff "
            "present; scalar => never) must equal the real sympy CCodeGen.routine "
            "+ get_prototype on the F2P scenario + 13 boundary + 400 fuzz argument "
            "sequences, read two independent ways (prototype string '*name' and "
            "arg.dimensions). If the real callee disagrees on any in-domain input "
            "(esp. the absent-matrix F2P boundary) => AXIOM-UNSOUND. Runs against "
            "patched sympy (apply_gold). Probe CALLS the real callee (avoids pilot "
            "bug #4) and opens nothing on disk (no codec issue, pilot bug #5)."
        ),
    },
]

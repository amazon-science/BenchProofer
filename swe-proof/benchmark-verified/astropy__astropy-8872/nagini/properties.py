# properties.py — PBT manifest for astropy__astropy-8872. NOT a Nagini module; a
# record of adversarial spec-falsification cases. The runner (swebench_nagini.pbt)
# writes each `module` to a temp file, runs Nagini verify on the host, and checks
# same_spec against the frozen model.py. Spec cases edit ONLY inside the
# # impl-start / # impl-end regions (region surgery => same_spec guaranteed).
#
# DEFENDED SURFACE (read model.py + refinement.md + mapping.md):
#   Two pure boolean predicates over a numpy-dtype abstraction (kind:int code
#   point, fits_ref_real32:bool, is_composite:bool). NO heap permission, NO
#   Acc(x,1/2) read-only inputs (all params are plain value-type int/bool), NO
#   @ContractOnly axioms (axioms region empty => AXIOM_TESTS = []).
#
#   Load-bearing postconditions (exact equalities, fully grounded in the input):
#     coerce_homogeneous_input:  Result() == is_int_like(kind)
#     coerce_generic_input:      Result() == (is_int_like(kind) or kind == KIND_OBJECT())
#   where is_int_like(kind) := kind==KIND_INT() or kind==KIND_UINT().
#
#   THE DISCRIMINATOR the fix establishes: the decision is a function of `kind`
#   ALONE, never of `fits_ref_real32` (the storage-width observable). The gold
#   patch replaced the pre-patch width test `not (np.can_cast(np.float32, dtype)
#   or dtype.fields)` with `dtype.kind in 'iu'` / `'iuO'`. The realizable()
#   precondition pins float16 as kind==KIND_REAL with fits_ref_real32==False, so
#   the spec ranges over the very input that the width-based bug got wrong.
#
# WHY NO FRAME-MUTATION CASE: there is no read-only Acc(...,1/2) input to mutate
#   (all three params are plain ints/bools passed by value; the functions touch
#   no heap). A "write to an input to satisfy the post vacuously" attack has no
#   target here. See `assessment`.
# WHY NO UNGROUNDED-ORACLE ECHO: the postcondition's "oracle" is is_int_like(kind)
#   — a @Pure predicate FULLY UNFOLDED over the input `kind` (it IS the work, not
#   an opaque answer key). There is no wrong value an echo could return that still
#   matches the equality. The honest cheapest impl is therefore a positive control,
#   included below.
# WHY NO CONTROL-FLOW-EFFECT CASE: both functions are total, side-effect-free,
#   raise nothing; the value abstraction is the whole behaviour. N/A.

from pathlib import Path

INSTANCE = "astropy__astropy-8872"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused; pure int/bool logic)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The two impl regions, uniquely identifiable for region surgery.
_HOMOG_IMPL = "    return is_int_like(kind)\n    # impl-end"
_GENERIC_IMPL = "    return is_int_like(kind) or kind == KIND_OBJECT()\n    # impl-end"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % old)
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % old)
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness): structurally-different but CORRECT impls must
# verify. Both functions are pure boolean logic over `kind`; a branch-reorder /
# spelled-out variant keeps the gold proof valid (no loop, no induction lemma).
# ---------------------------------------------------------------------------

# pos-control-homog: spell the predicate out as an explicit if/else over the two
# integer kinds (semantically identical to is_int_like(kind), structurally
# different). Must verify (else SPEC-TOO-STRONG).
_POS_HOMOG = _swap(
    _BASE, _HOMOG_IMPL,
    "    if kind == KIND_INT() or kind == KIND_UINT():\n"
    "        return True\n"
    "    return False\n"
    "    # impl-end",
)

# pos-control-generic: branch-reorder — test the object kind FIRST, then the
# integer kinds, all returns explicit. Semantically identical, structurally
# different. Must verify.
_POS_GENERIC = _swap(
    _BASE, _GENERIC_IMPL,
    "    if kind == KIND_OBJECT():\n"
    "        return True\n"
    "    if kind == KIND_UINT() or kind == KIND_INT():\n"
    "        return True\n"
    "    return False\n"
    "    # impl-end",
)

# pos-control-both: a CORRECT variant of BOTH sites simultaneously, each a
# different structural shape, exercising that the frozen spec admits a faithful
# rewrite of the whole module at once.
_POS_BOTH = _swap(
    _swap(_BASE, _HOMOG_IMPL,
          "    coerce = is_int_like(kind)\n"
          "    return coerce\n"
          "    # impl-end"),
    _GENERIC_IMPL,
    "    coerce = is_int_like(kind) or (kind == KIND_OBJECT())\n"
    "    return coerce\n"
    "    # impl-end",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN (reject): same-spec WRONG impls. Each diverges from
# the gold predicate on a sub-domain of the realisable inputs; the exact-equality
# postcondition must reject it. Each carries the refinement argument that its
# faithful real patch would NOT resolve the F2P (test_preserve_dtype).
# ---------------------------------------------------------------------------

# weak-width-homog: THE headline bug, reborn as a same-spec rival. Key the
# homogeneous decision on the storage-width observable `fits_ref_real32` instead
# of on `kind` (this is exactly the pre-patch predicate). Diverges precisely on
# float16 (kind==KIND_REAL, fits_ref_real32==False, is_composite==False): gold
# preserves (Result False) but this coerces (Result True). Must REJECT on the
# Ensures equality.
_WEAK_WIDTH_HOMOG = _swap(
    _BASE, _HOMOG_IMPL,
    "    return not (fits_ref_real32 or is_composite)\n"
    "    # impl-end",
)

# weak-width-generic: the same width-based bug on the generic path (pre-patch
# predicate ORed with the object kind). Diverges on float16. Must REJECT.
_WEAK_WIDTH_GENERIC = _swap(
    _BASE, _GENERIC_IMPL,
    "    return (not (fits_ref_real32 or is_composite)) or kind == KIND_OBJECT()\n"
    "    # impl-end",
)

# weak-coerce-bool-homog: a rival that ALSO coerces the boolean kind (treats
# bool like an integer). Correct on every kind except KIND_BOOL, where gold
# preserves (Result False) but this coerces (Result True). Must REJECT.
_WEAK_BOOL_HOMOG = _swap(
    _BASE, _HOMOG_IMPL,
    "    return is_int_like(kind) or kind == KIND_BOOL()\n"
    "    # impl-end",
)

# weak-coerce-complex-generic: a rival that ALSO coerces the complex kind.
# Correct except on KIND_COMPLEX, where gold preserves but this coerces. REJECT.
_WEAK_COMPLEX_GENERIC = _swap(
    _BASE, _GENERIC_IMPL,
    "    return is_int_like(kind) or kind == KIND_OBJECT() or kind == KIND_COMPLEX()\n"
    "    # impl-end",
)

# weak-drop-object-generic: the generic rival that uses the HOMOGENEOUS predicate
# (drops the object kind). Correct on every kind except KIND_OBJECT, where gold
# coerces (Result True) but this preserves (Result False). Must REJECT.
_WEAK_DROP_OBJECT = _swap(
    _BASE, _GENERIC_IMPL,
    "    return is_int_like(kind)\n"
    "    # impl-end",
)

# weak-drop-uint-homog: a rival that coerces only signed int, missing unsigned
# int. Correct except on KIND_UINT, where gold coerces (True) but this preserves
# (False). A single-value partial-domain miss. Must REJECT.
_WEAK_DROP_UINT = _swap(
    _BASE, _HOMOG_IMPL,
    "    return kind == KIND_INT()\n"
    "    # impl-end",
)

# weak-const-false-homog: a cheap supporting near-miss — always preserve (never
# coerce). Correct on every preserved kind but wrong on every integer kind.
# Must REJECT. (Supporting case; still carries a refinement.)
_WEAK_CONST_FALSE = _swap(
    _BASE, _HOMOG_IMPL,
    "    return False\n"
    "    # impl-end",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (verify): a caller asserts the Requires (realizable) is
# establishable for the F2P-shaped witness inputs (the float16 regression input,
# plus an integer input). If the precondition cannot be met for a normal input =>
# PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------

# admiss-float16: assert realizable() holds for the float16 witness (kind=REAL,
# fits=False, comp=False) and for the int witness, then call both modeled
# functions on them inside an admissibility driver appended in the homogeneous
# impl region. Keeps the gold return; only adds a self-call exercising Requires.
_ADMISS = _swap(
    _BASE, _HOMOG_IMPL,
    "    # admissibility driver: the F2P witnesses must satisfy realizable()\n"
    "    Assert(realizable(KIND_REAL(), False, False))   # float16\n"
    "    Assert(realizable(KIND_INT(), False, False))    # int64\n"
    "    Assert(realizable(KIND_OBJECT(), True, False))  # object\n"
    "    Assert(realizable(KIND_COMPOSITE(), False, True))  # structured\n"
    "    return is_int_like(kind)\n"
    "    # impl-end",
)


SPEC_TESTS = [
    {
        "id": "pos-control-homog",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HOMOG,
        "rationale": "structurally-different (explicit if/else over the two integer "
                     "kinds) but semantically identical to is_int_like(kind); pure "
                     "boolean, no loop/induction. Must verify against "
                     "Result()==is_int_like(kind) else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-generic",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GENERIC,
        "rationale": "branch-reorder positive control (object kind tested first, "
                     "then integer kinds, all returns explicit); semantically equal "
                     "to is_int_like(kind) or kind==KIND_OBJECT(). Must verify.",
    },
    {
        "id": "pos-control-both",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BOTH,
        "rationale": "both sites rewritten at once with a typed local-variable "
                     "reshape (bind the decision to a local, then return it); "
                     "frozen spec must admit a faithful full-module rewrite.",
    },
    {
        "id": "weak-width-homog",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_WIDTH_HOMOG,
        "refinement": "this is the literal pre-patch predicate "
                      "`not (np.can_cast(np.float32, value.dtype) or value.dtype.fields)`. "
                      "Its faithful real patch coerces float16 to float64 (kind 'f', "
                      "cannot absorb float32) => q3_16.dtype != a3_16.dtype, so "
                      "test_preserve_dtype FAILS. It does NOT resolve.",
        "rationale": "rejection from Ensures Result()==is_int_like(kind): on the "
                     "realisable witness kind=KIND_REAL, fits_ref_real32=False, "
                     "is_composite=False (float16) the rival returns True (coerce) "
                     "while is_int_like(kind)==False. Keys on width, not kind => "
                     "SPEC-TOO-WEAK if it verified.",
    },
    {
        "id": "weak-width-generic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_WIDTH_GENERIC,
        "refinement": "the pre-patch generic predicate "
                      "`(not (can_cast(float32, dtype) or dtype.fields)) or dtype.kind=='O'`. "
                      "Coerces float16 => the float16 assertion in test_preserve_dtype "
                      "FAILS. Does NOT resolve.",
        "rationale": "rejection from Ensures Result()==(is_int_like(kind) or "
                     "kind==KIND_OBJECT()): diverges on the float16 witness (rival "
                     "True, gold False). width-based => SPEC-TOO-WEAK if verified.",
    },
    {
        "id": "weak-coerce-bool-homog",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_BOOL_HOMOG,
        "refinement": "a patch that also coerced kind 'b' (`dtype.kind in 'iub'`) "
                      "would convert boolean arrays to float, violating the documented "
                      "preserve-bool contract and the broader Quantity dtype tests "
                      "(P2P); not the gold behaviour, would not resolve faithfully.",
        "rationale": "rejection from the equality on the KIND_BOOL witness "
                     "(realizable(KIND_BOOL,False,False)): rival True, "
                     "is_int_like(KIND_BOOL)==False. Single-kind partial-domain miss.",
    },
    {
        "id": "weak-coerce-complex-generic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_COMPLEX_GENERIC,
        "refinement": "a patch `dtype.kind in 'iuOc'` would coerce complex arrays to "
                      "float (lossy, drops the imaginary part) — never the gold "
                      "behaviour; complex must be preserved, so it would not resolve.",
        "rationale": "rejection from Ensures on the KIND_COMPLEX witness "
                     "(realizable(KIND_COMPLEX,True,False)): rival True, gold "
                     "(is_int_like or object)==False. partial-domain on complex.",
    },
    {
        "id": "weak-drop-object-generic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DROP_OBJECT,
        "refinement": "this is the homogeneous predicate used on the generic path "
                      "(`dtype.kind in 'iu'`, dropping 'O'). Its faithful patch would "
                      "NOT coerce a Decimal/object input to float, so q4 "
                      "(Decimal('10.25')) keeps dtype object => the q4 float "
                      "assertion in test_preserve_dtype FAILS. Does NOT resolve.",
        "rationale": "rejection from Ensures Result()==(is_int_like(kind) or "
                     "kind==KIND_OBJECT()): on the KIND_OBJECT witness "
                     "(realizable(KIND_OBJECT,True,False)) rival False, gold True. "
                     "partial-domain on the object kind.",
    },
    {
        "id": "weak-drop-uint-homog",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DROP_UINT,
        "refinement": "a patch `dtype.kind == 'i'` (signed only) would leave unsigned "
                      "integer arrays uncoerced, contradicting the documented "
                      "'integer inputs are converted to float' contract; unsigned "
                      "ints would keep their integer dtype, not gold behaviour.",
        "rationale": "rejection from the equality on the KIND_UINT witness "
                     "(realizable(KIND_UINT,False,False)): rival False, "
                     "is_int_like(KIND_UINT)==True. single-value partial-domain miss.",
    },
    {
        "id": "weak-const-false-homog",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_CONST_FALSE,
        "refinement": "always-preserve never coerces integers, so int Quantity inputs "
                      "keep their integer dtype — directly contradicts the F2P/P2P "
                      "expectation that integer inputs become float; would not resolve. "
                      "(cheap supporting near-miss; still carries a refinement.)",
        "rationale": "rejection from the equality on every integer witness "
                     "(KIND_INT/KIND_UINT): rival False, is_int_like==True. "
                     "supporting constant-output near-miss.",
    },
    {
        "id": "admiss-witnesses",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the precondition realizable() must admit the F2P-shaped "
                     "witnesses: float16 (REAL,False,False), int (INT,False,False), "
                     "object (OBJECT,True,False), structured (COMPOSITE,False,True). "
                     "The Assert()s discharge inside the impl; if any fails the "
                     "precondition is PRECOND-TOO-STRONG (excludes a normal input).",
    },
]

# No @ContractOnly axioms / A-consumed callees in this bundle (axioms region is
# empty; the changed predicate is modeled DEEPLY and validated by axiom_check.py
# / G-AX out-of-band, not via a consumed Nagini axiom). Hence no axiom lane.
AXIOM_TESTS = []

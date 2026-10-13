# properties.py — PBT falsification battery for django__django-13794. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + mapping.md + the gold patch):
#   TWO modeled functions, one per added proxy method:
#     forward_combine(realized: List[int], other: List[int]) -> List[int]   (__add__)
#     reverse_combine(realized: List[int], other: List[int]) -> List[int]   (__radd__)
#   `realized` is the FORCED lazy value (self.__cast(), an R-refined read-only input);
#   `other` is the other operand. The model carries str/bytes/list (and the int F2P
#   case) as List[int] of code points; the spec is over PSeq[int] via ToSeq; `+` is
#   sequence concatenation modeled DEEPLY by a two-phase forward-append loop.
#
#   Precondition (BOTH inputs READ-ONLY):
#     (P1) Requires(Acc(list_pred(realized), 1 / 2))   # HALF perm => no write
#     (P2) Requires(Acc(list_pred(other),    1 / 2))   # HALF perm => no write
#   Postcondition — forward_combine (four clauses; first two are framing/permission):
#     (Qf1) Ensures(Acc(list_pred(realized), 1 / 2))   # returns the read perm
#     (Qf2) Ensures(Acc(list_pred(other),    1 / 2))   # returns the read perm
#     (Qf3) Ensures(Acc(list_pred(Result())))          # FULL perm on a fresh result
#     (Qf4) Ensures(ToSeq(Result()) == ToSeq(realized) + ToSeq(other))  # LOAD-BEARING
#   Postcondition — reverse_combine:
#     (Qr1..3) the same framing/permission clauses
#     (Qr4) Ensures(ToSeq(Result()) == ToSeq(other) + ToSeq(realized))  # LOAD-BEARING
#
# THE DISCRIMINATING CONTENT IS OPERAND ORDER. forward pins `realized ++ other`;
# reverse pins `other ++ realized`. The whole point of the gold patch (two distinct
# methods, __add__ vs reflected __radd__) is that order. The sharpest uniqueness
# attack is therefore the ORDER-SWAP rival (return the OTHER direction's concat),
# which a value abstraction that only checked "the multiset of elements" would miss.
#
# FRAME-MUTATION lane is MANDATORY: BOTH realized and other are Acc(...,1/2)
#   (read-only). A rival that WRITES to either input must be rejected for
#   INSUFFICIENT PERMISSION. We include a write-to-realized rival (forward) and a
#   write-to-other rival (reverse), so each half-permission input is independently
#   exercised. A byte-fuzzer never thinks to mutate the input; this is the project's
#   #1 weakness class.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Qf4/Qr4 pin Result to a
#   concatenation of the two INPUT arguments (ToSeq(realized)/ToSeq(other)), fully
#   grounded — there is NO opaque @Pure answer-key and NO exact-marker oracle (the
#   pure region in model.py is empty; the axioms region is empty). There is no value
#   an echo could carry that satisfies the postcondition yet is wrong: the unique
#   satisfier IS the correct ordered concatenation. The honest grounded-oracle
#   positive control is therefore "produce the concatenation" (the pos controls
#   below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. Both functions are pure value-returning
#   concatenations with no raise/return-vs-fallthrough difference invisible to the
#   value abstraction. The real bug — the proxy's `+` RAISING (TypeError) pre-patch,
#   so the `add` filter's `except Exception: return ''` collapses to empty — is
#   captured at the VALUE level: the prepatch image returns `[]` (the empty
#   sequence), and that empty result is rejected by Qf4/Qr4. There is no separately
#   observable side effect to discriminate with a capability token; the empty-result
#   rival below covers the prepatch control-flow outcome at the value level.
#
# AXIOM lane: meta.axioms == []. There is ONE deep_model_reference (the PSeq
#   concatenation A-reference for the changed `+`) but it is consumed by NO
#   @ContractOnly axiom and is modeled DIRECTLY in model.py's impl regions (the
#   two-phase append loop), pinned by Qf4/Qr4. axiom_check.py validates that deep
#   model == the real patched __add__/__radd__ on a live lazy() proxy under G-AX
#   already (text boundary+fuzz, int, lazy+lazy). Nothing in this bundle's model.py
#   proof rests on a @ContractOnly axiom or an A-reference deep model the proof
#   QUOTES, so AXIOM_TESTS = []. (The G-AX check is not re-run here; it is its own
#   gate and would only duplicate the same-callee soundness already certified.)
from pathlib import Path

INSTANCE = "django__django-13794"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two frozen FUNCTION impl blocks, verbatim (everything from each function's
# `# impl-start` through its `# impl-end`, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY one of these blocks, so the edit never touches
# the spec (axioms/pure/pre-/post-conditions regions + the function signatures).
# same_spec is computed over the spec_view, which elides every impl region (and the
# nested invariants), so swapping inside here is guaranteed same_spec. Each block is
# unique in model.py (forward iterates `realized` then `other`; reverse iterates
# `other` then `realized`).
# ---------------------------------------------------------------------------

_FWD_IMPL = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        result.append(other[j])
        j = j + 1
    return result
    # impl-end"""

_REV_IMPL = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(other))
        Invariant(ToSeq(result) == ToSeq(other).take(i))
        Invariant(MustTerminate(len(other) - i + 1))
        # invariants-end
        result.append(other[i])
        i = i + 1
    j = 0
    while j < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(realized))
        Invariant(ToSeq(result) == ToSeq(other) + ToSeq(realized).take(j))
        Invariant(MustTerminate(len(realized) - j + 1))
        # invariants-end
        result.append(realized[j])
        j = j + 1
    return result
    # impl-end"""

assert _BASE.count(_FWD_IMPL) == 1, "forward_combine impl region drifted"
assert _BASE.count(_REV_IMPL) == 1, "reverse_combine impl region drifted"


def _fwd(new_block):
    """Full model.py variant with ONLY forward_combine's impl block replaced."""
    return _swap(_BASE, _FWD_IMPL, new_block)


def _rev(new_block):
    """Full model.py variant with ONLY reverse_combine's impl block replaced."""
    return _swap(_BASE, _REV_IMPL, new_block)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ===========================================================================

# pos-cached-bound: structurally-different but behaviourally-identical. The loop
# bounds are cached in locals (nr = len(realized), no = len(other)) rather than
# re-evaluating len(...) each iteration, and a trivially-preserved framing invariant
# Invariant(nr == len(realized)) / Invariant(no == len(other)) is added (both inputs
# are read-only, so their lengths are constant). It KEEPS the gold forward-append
# shape and every gold proof obligation (the take(i) prefix invariants for both
# phases). No loop-direction flip (which would need an f(a+b) concat lemma against
# the front take()-fold). If it fails => SPEC-TOO-STRONG (a faithful correct impl
# rejected). Applied to BOTH functions so each direction's spec is exercised.
_FWD_POS = """\
# impl-start
    result = []  # type: List[int]
    nr = len(realized)
    no = len(other)
    i = 0
    while i < nr:
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nr == len(realized))
        Invariant(no == len(other))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < no:
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nr == len(realized))
        Invariant(no == len(other))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        result.append(other[j])
        j = j + 1
    return result
    # impl-end"""

_REV_POS = """\
# impl-start
    result = []  # type: List[int]
    no = len(other)
    nr = len(realized)
    i = 0
    while i < no:
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(no == len(other))
        Invariant(nr == len(realized))
        Invariant(0 <= i and i <= len(other))
        Invariant(ToSeq(result) == ToSeq(other).take(i))
        Invariant(MustTerminate(len(other) - i + 1))
        # invariants-end
        result.append(other[i])
        i = i + 1
    j = 0
    while j < nr:
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(no == len(other))
        Invariant(nr == len(realized))
        Invariant(0 <= j and j <= len(realized))
        Invariant(ToSeq(result) == ToSeq(other) + ToSeq(realized).take(j))
        Invariant(MustTerminate(len(realized) - j + 1))
        # invariants-end
        result.append(realized[j])
        j = j + 1
    return result
    # impl-end"""

# admiss-reads (forward): an admissibility positive control. The precondition is the
# non-trivial heap permission Acc(list_pred(realized), 1/2) AND Acc(list_pred(other),
# 1/2); this control confirms it ADMITS the reads a normal F2P-shaped input needs —
# it reads len(realized), len(other) and (per element) each code point under the
# half-permission, asserting those reads succeed, before running the gold body. If
# the half-permission did not admit a legitimate read of a normal operand pair, this
# would fail => PRECOND-TOO-STRONG. All asserts are over values readable under
# Acc(...,1/2); no write, so no proof gap and no permission demand beyond the spec.
_FWD_ADMISS = """\
# impl-start
    # Admissibility: a normal (possibly empty) operand pair is in-domain; the
    # half-permission admits reading the lengths and the elements of both inputs.
    Assert(len(realized) >= 0)
    Assert(len(other) >= 0)
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        c = realized[i]
        Assert(c == realized[i])  # the read is admitted under the half-permission
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        d = other[j]
        Assert(d == other[j])  # the read is admitted under the half-permission
        result.append(other[j])
        j = j + 1
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION RIVALS (MANDATORY — both realized and other are Acc(...,1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ===========================================================================

# frame-mut-realized (forward): keeps the gold forward body VERBATIM (so the
# rejection is attributable solely to the added write, not to a value mismatch),
# then WRITES BACK into the read-only `realized` input: realized[0] = realized[0].
# A no-op store, but a STORE — it demands FULL write permission on `realized`, which
# the caller only granted at 1/2 (P1). The verifier must reject for insufficient
# permission. (`realized` models self.__cast(): the gold patch reads it and NEVER
# writes back into the forced value.)
_FWD_FRAME_REALIZED = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        result.append(other[j])
        j = j + 1
    if len(realized) > 0:
        # Frame violation: write back into the read-only (Acc(...,1/2)) `realized`.
        realized[0] = realized[0]
    return result
    # impl-end"""

# frame-mut-other (reverse): keeps the gold reverse body VERBATIM, then WRITES BACK
# into the read-only `other` input: other[0] = other[0]. Demands FULL write
# permission on `other`, granted only at 1/2 (P2). Must be rejected for insufficient
# permission. Exercises the SECOND half-permission input independently of the first.
_REV_FRAME_OTHER = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(other))
        Invariant(ToSeq(result) == ToSeq(other).take(i))
        Invariant(MustTerminate(len(other) - i + 1))
        # invariants-end
        result.append(other[i])
        i = i + 1
    j = 0
    while j < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(realized))
        Invariant(ToSeq(result) == ToSeq(other) + ToSeq(realized).take(j))
        Invariant(MustTerminate(len(realized) - j + 1))
        # invariants-end
        result.append(realized[j])
        j = j + 1
    if len(other) > 0:
        # Frame violation: write back into the read-only (Acc(...,1/2)) `other`.
        other[0] = other[0]
    return result
    # impl-end"""


# ===========================================================================
# UNIQUENESS / ORDER RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# The discriminating content of this patch is OPERAND ORDER.
# ===========================================================================

# weak-swap-order-fwd: forward_combine returns the WRONG direction — `other ++
# realized` instead of `realized ++ other` (it runs reverse_combine's body). The
# elements are identical as a multiset; only the ORDER differs. Must be rejected by
# Qf4 (ToSeq(Result()) == ToSeq(realized) + ToSeq(other)): the take(other) prefix
# invariant cannot establish ToSeq(realized) as the prefix when `other` is non-empty
# and differs from a prefix of `realized`. This is THE attack the gold patch's two
# distinct methods exist to defend (left-operand __add__ vs reflected __radd__).
_FWD_SWAP = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(other))
        Invariant(ToSeq(result) == ToSeq(other).take(i))
        Invariant(MustTerminate(len(other) - i + 1))
        # invariants-end
        result.append(other[i])
        i = i + 1
    j = 0
    while j < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(realized))
        Invariant(ToSeq(result) == ToSeq(other) + ToSeq(realized).take(j))
        Invariant(MustTerminate(len(realized) - j + 1))
        # invariants-end
        result.append(realized[j])
        j = j + 1
    return result
    # impl-end"""

# weak-swap-order-rev: reverse_combine returns the WRONG direction — `realized ++
# other` instead of `other ++ realized` (it runs forward_combine's body). Rejected
# by Qr4 (ToSeq(Result()) == ToSeq(other) + ToSeq(realized)). Same order attack,
# reflected method.
_REV_SWAP = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        result.append(other[j])
        j = j + 1
    return result
    # impl-end"""


# ===========================================================================
# PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# ===========================================================================

# weak-drop-last-other-fwd: PARTIAL-DOMAIN / off-by-one. forward copies `realized`
# in full, then appends `other` EXCEPT its last element (the second loop stops at
# len(other) - 1). Correct ONLY when `other` is empty (and degenerate when
# len(other)==0 the bound is -1, so the loop simply does not run — still the
# realized-only prefix). Wrong for every non-empty `other`: the result is missing
# other's final code point. Rejected by Qf4 (the final result is one element short,
# so ToSeq(Result()) != ToSeq(realized) + ToSeq(other)). The second loop's
# postcondition ToSeq(result) == ToSeq(realized) + ToSeq(other) cannot be discharged
# from take(len(other)-1). Targets the input that fails LAST (other's trailing char,
# e.g. the final char of 'lazy' in test_add08's 'string' + 'lazy').
_FWD_DROP_LAST = """\
# impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(realized):
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(realized))
        Invariant(ToSeq(result) == ToSeq(realized).take(i))
        Invariant(MustTerminate(len(realized) - i + 1))
        # invariants-end
        result.append(realized[i])
        i = i + 1
    j = 0
    while j < len(other) - 1:
        # invariants-start
        Invariant(Acc(list_pred(realized), 1 / 2))
        Invariant(Acc(list_pred(other), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(other))
        Invariant(ToSeq(result) == ToSeq(realized) + ToSeq(other).take(j))
        Invariant(MustTerminate(len(other) - j + 1))
        # invariants-end
        result.append(other[j])
        j = j + 1
    return result
    # impl-end"""

# weak-empty-fwd: the prepatch baseline reborn at the VALUE level. The proxy pre-patch
# has no __add__; the `+` RAISES and the `add` template filter's `except Exception:
# return ''` collapses the outcome to the empty string => the modeled empty sequence
# []. This is model_prepatch.py's exact value for forward_combine. Correct ONLY when
# BOTH operands are empty; wrong for every non-empty case (e.g. test_add09's lazy +
# lazy, test_lazy_add's 4 + 5). Rejected by Qf4 (empty != non-empty concat). Cheap
# supporting near-miss that still carries the real prepatch refinement. The
# `empty = []  # type: List[int]` local is bound BEFORE return to keep the Nagini
# type comment valid (no bare `return []`).
_FWD_EMPTY = """\
# impl-start
    # Prepatch outcome at the value level: the `+` raises and the caller's
    # `except Exception: return ''` collapses to the empty sequence.
    empty = []  # type: List[int]
    return empty
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-cached-bound-fwd",
        "kind": "soundness",
        "expect": "verify",
        "module": _fwd(_FWD_POS),
        "rationale": (
            "structurally-different forward impl (loop bounds cached in locals nr/no, "
            "extra trivially-preserved Invariant(nr == len(realized)) / "
            "Invariant(no == len(other)) — both inputs read-only so lengths are "
            "constant) that keeps the gold forward-append shape and every gold proof "
            "obligation (both take(i) prefix invariants). Verifies Qf4 unchanged. If "
            "it fails => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-cached-bound-rev",
        "kind": "soundness",
        "expect": "verify",
        "module": _rev(_REV_POS),
        "rationale": (
            "the reverse-direction analogue of pos-cached-bound-fwd: cached bounds + "
            "trivially-preserved length invariants, gold forward-append shape and "
            "both take(i) invariants kept. Verifies Qr4 (other ++ realized) unchanged. "
            "If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-reads-fwd",
        "kind": "admissibility",
        "expect": "verify",
        "module": _fwd(_FWD_ADMISS),
        "rationale": (
            "the non-trivial precondition Acc(list_pred(realized),1/2) AND "
            "Acc(list_pred(other),1/2) must admit the reads a normal operand pair "
            "needs (both lengths and each element). The control reads len(realized), "
            "len(other) and each element under the half-permission and asserts the "
            "reads succeed before the gold body. If it fails => PRECOND-TOO-STRONG "
            "(the half-permission would reject a legitimate F2P-shaped input)."
        ),
    },
    {
        "id": "frame-mut-realized-fwd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fwd(_FWD_FRAME_REALIZED),
        "refinement": (
            "`realized` models self.__cast() — the forced lazy value. The gold patch "
            "`return self.__cast() + other` READS that value and NEVER writes back "
            "into it. A faithful real patch that mutated the forced value in place "
            "(e.g. rewrote the proxy's cached/realized object while combining) would "
            "corrupt the shared lazy object and diverge from the gold's read-only "
            "use — it would not be the gold patch and would not faithfully resolve "
            "the F2P. The store here is a no-op only by coincidence; the spec must "
            "forbid ANY write to the read-only forced value."
        ),
        "rationale": (
            "REJECTED by the permission system: `realized` is granted at "
            "Acc(...,1/2) (P1); the store realized[0]=realized[0] demands FULL write "
            "permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold forward body is kept verbatim so the "
            "rejection is attributable solely to the write. If it verifies => the "
            "read-only frame on the forced value is not enforced (frame-mutation, the "
            "#1 weakness class)."
        ),
    },
    {
        "id": "frame-mut-other-rev",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rev(_REV_FRAME_OTHER),
        "refinement": (
            "`other` models the other operand of the reflected `+` "
            "(`return other + self.__cast()`). The gold patch READS `other` and "
            "never writes back into the caller's operand object. A faithful real "
            "patch that mutated `other` in place would corrupt the caller's value "
            "(e.g. a shared list/str-like buffer) and diverge from the gold's "
            "read-only use — it would not faithfully resolve. Exercises the SECOND "
            "half-permission input independently of the first."
        ),
        "rationale": (
            "REJECTED by the permission system: `other` is granted at Acc(...,1/2) "
            "(P2); the store other[0]=other[0] demands FULL write permission, not "
            "available, so the verifier rejects for INSUFFICIENT PERMISSION. The gold "
            "reverse body is kept verbatim so the rejection is attributable solely to "
            "the write. If it verifies => the read-only frame on `other` is not "
            "enforced (frame-mutation)."
        ),
    },
    {
        "id": "weak-swap-order-fwd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fwd(_FWD_SWAP),
        "refinement": (
            "forward_combine returns `other ++ realized` (the REFLECTED direction) "
            "instead of `realized ++ other`. Its faithful real patch is a __add__ "
            "that returns `other + self.__cast()` (operands swapped). That produces "
            "'lazystring' for test_add08-shaped 'string' + lazy('lazy') (the lazy "
            "value is the LEFT operand of `+` here) — the WRONG order — and for the "
            "int F2P would still total correctly only by commutativity of int + but "
            "would be the wrong method semantics; on the string carriers the F2P "
            "asserts the realized value FIRST, so a swapped __add__ fails test_add09 "
            "/ test_lazy_add string-shaped concatenation. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Qf4 (ToSeq(Result()) == ToSeq(realized) + ToSeq(other)): the "
            "body proves ToSeq(result) == ToSeq(other) + ToSeq(realized), which "
            "differs from the required prefix order whenever realized and other are "
            "not equal as ordered prefixes (any non-empty distinct operands). The "
            "elements match as a multiset but the ORDER does not — the precise "
            "content this two-method patch defends. If it verifies => SPEC-TOO-WEAK "
            "(operand order unpinned)."
        ),
    },
    {
        "id": "weak-swap-order-rev",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rev(_REV_SWAP),
        "refinement": (
            "reverse_combine returns `realized ++ other` instead of "
            "`other ++ realized`. Its faithful real patch is a __radd__ that returns "
            "`self.__cast() + other` (operands swapped). For test_add08 "
            "('string' + lazy('lazy'), dispatched to the proxy's __radd__ because "
            "str.__add__ returns NotImplemented) it would yield 'lazystring' instead "
            "of the asserted 'stringlazy' — the WRONG order. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Qr4 (ToSeq(Result()) == ToSeq(other) + ToSeq(realized)): the "
            "body proves the opposite order, which differs for any non-empty distinct "
            "operands. If it verifies => SPEC-TOO-WEAK (operand order unpinned on the "
            "reflected method)."
        ),
    },
    {
        "id": "weak-drop-last-other-fwd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fwd(_FWD_DROP_LAST),
        "refinement": (
            "an off-by-one real patch that built `self.__cast() + other[:-1]` (or a "
            "loop bound `len(other) - 1`) would drop the trailing character of the "
            "other operand: 'string' + lazy('lazy') worth of test_add08 would lose "
            "the final 'y' (yielding 'stringlaz'), failing the F2P which asserts the "
            "full 'stringlazy'. Correct only when other is empty. PARTIAL-DOMAIN "
            "break on the trailing element. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Qf4: the second loop stops at len(other)-1, so the final "
            "ToSeq(result) == ToSeq(realized) + ToSeq(other).take(len(other)-1), which "
            "is one element short of ToSeq(realized) + ToSeq(other) for every "
            "non-empty other. The postcondition cannot be discharged. If it verifies "
            "=> SPEC-TOO-WEAK on the trailing-element sub-domain."
        ),
    },
    {
        "id": "weak-empty-fwd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fwd(_FWD_EMPTY),
        "refinement": (
            "this is the PRE-PATCH behaviour (model_prepatch.py) at the value level: "
            "without __add__ the proxy's `+` raises TypeError and the `add` template "
            "filter's `except Exception: return ''` collapses to the empty string. "
            "Its faithful real patch is the unpatched repo, which yields '' for "
            "test_add09 (lazy + lazy) and breaks test_lazy_add — exactly the bug the "
            "gold fixes. Does NOT resolve. Cheap supporting near-miss with a genuine "
            "refinement (the actual prepatch failure)."
        ),
        "rationale": (
            "REJECTED by Qf4 (ToSeq(Result()) == ToSeq(realized) + ToSeq(other)): the "
            "empty result equals the concatenation only when both operands are empty; "
            "for any non-empty operand it fails. This is exactly the clause G-DIFF "
            "shows the prepatch variant failing. The `empty = []  # type: List[int]` "
            "local is bound before return to keep the Nagini type comment valid (no "
            "bare `return []`). If it verifies => SPEC-TOO-WEAK."
        ),
    },
]

# No @ContractOnly axioms (meta.axioms == []) and no A-reference deep model that the
# model.py PROOF quotes: the changed `+` is modeled DIRECTLY as PSeq concatenation in
# the two impl regions, pinned by Qf4/Qr4. The single deep_model_reference is the
# executable A-reference check that the deep concat model == the real patched
# __add__/__radd__ on a live lazy() proxy — that is axiom_check.py's job under G-AX
# (already pass: text boundary+fuzz, int, lazy+lazy), not a @ContractOnly the proof
# consumes. Nothing in this bundle's proof rests on an axiom or A-reference the proof
# uses, so there is nothing for the axiom lane to execute.
AXIOM_TESTS = []

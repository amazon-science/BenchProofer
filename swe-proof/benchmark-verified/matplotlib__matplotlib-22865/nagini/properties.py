# properties.py — PBT manifest for matplotlib__matplotlib-22865. NOT a Nagini
# module; a record of adversarial cases. The runner (swebench_nagini.pbt) writes
# each SPEC_TESTS["module"] to a temp file, runs Nagini verify + markers.same_spec
# against the frozen model.py, and stamps RESULT. Spec cases are full model.py
# variants built by region-surgery (edits ONLY inside # impl-start/# impl-end, so
# the frozen spec — axioms/pure/pre/post — is byte-identical: same_spec holds).
#
# Defended surface (read from model.py):
#   drawn_separators(segments: List[int], lower_open: bool, upper_open: bool)
#     Requires Acc(list_pred(segments), 1/2)         <- READ-ONLY input
#     Requires len(segments) >= 2
#     Ensures  Acc(list_pred(segments), 1/2)         <- returns the half perm
#     Ensures  Acc(list_pred(Result()))
#     Ensures  len(Result()) == end_index(upper_open, n) - start_index(lower_open)   (LENGTH PIN)
#     Ensures  Forall k. 0<=k<len(Result()) ==> Result()[k] == segments[start_index(lower_open)+k]  (ELEMENT PIN)
#   where start_index(lo) = 0 if lo else 1; end_index(uo,n) = n if uo else n-1.
#
# The postcondition oracle is GROUNDED: start_index/end_index are fully-unfolded
# @Pure functions OF THE ARGS, and the element pin references segments[...] (the
# input) — not an opaque answer key. So there is no "wrong echo to verify"
# (UNGROUNDED-ORACLE class N/A — see assessment); we supply a positive control
# instead. The applicable attacks are FRAME-MUTATION (read-only segments) and
# several PARTIAL-DOMAIN rivals (each diverges on a real F2P sub-case).
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22865"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer slice bounds only)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact frozen impl region (between # impl-start / # impl-end) we edit. We
# anchor on sub-strings of it so each _swap is unique and stays in-region.
# ---------------------------------------------------------------------------
_GOLD_LOOP_BODY = """        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result"""


# === 1. POSITIVE CONTROL (soundness) =======================================
# Structurally-different but CORRECT: instead of an absolute-index loop
# (i from start to end appending segments[i]), iterate an OFFSET j from 0 and
# append segments[start + j]. Same forward direction (so no fold/append lemma is
# needed — directive 3), but a genuinely different loop shape. We re-express
# EVERY gold invariant in terms of j (keeping the prefix-preservation pin and
# the framing of segments/result — directive 2) so the proof obligations the
# spec needs are all still discharged. Must verify (else SPEC-TOO-STRONG).
_POS_IMPL = """    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    count = end - start
    result = []  # type: List[int]
    j = 0
    while j < count:
        # invariants-start
        Invariant(Acc(list_pred(segments), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(start == start_index(lower_open))
        Invariant(end == end_index(upper_open, len(segments)))
        Invariant(0 <= start and start <= 1)
        Invariant(end == len(segments) or end == len(segments) - 1)
        Invariant(start <= end)
        Invariant(count == end - start)
        Invariant(0 <= j and j <= count)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        # TERMINATION MEASURE, derived from THIS loop's own shape. The gold counts
        # an absolute index i up to `end`, so its measure is `end - i + 1`; this
        # control counts an OFFSET j up to `count`, and `i` does not even exist
        # here. The bound on the remaining iterations is therefore
        # `count - j + 1`: `count` is fixed before the loop (pinned by the
        # `count == end - start` invariant above, so the verifier knows it is not
        # reassigned), j rises by exactly 1 per step, and the `j <= count`
        # invariant keeps the expression >= 1 while the loop runs. The `+ 1` is
        # what makes the LAST iteration (j == count - 1, zero iterations left)
        # satisfiable: MustTerminate(0) is unsatisfiable.
        Invariant(MustTerminate(count - j + 1))
        # invariants-end
        result.append(segments[start + j])
        j = j + 1
    return result"""
pos_control = _swap(
    _BASE,
    """    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start
    while i < end:
        # invariants-start
        Invariant(Acc(list_pred(segments), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(start == start_index(lower_open))
        Invariant(end == end_index(upper_open, len(segments)))
        Invariant(0 <= start and start <= 1)
        Invariant(end == len(segments) or end == len(segments) - 1)
        Invariant(start <= end)
        Invariant(start <= i and i <= end)
        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        Invariant(MustTerminate(end - i + 1))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result""",
    _POS_IMPL,
)


# === 2. ADMISSIBILITY ======================================================
# Confirm the precondition admits a normal F2P-shaped input and yields a
# well-formed (non-negative-length) slice: assert the facts the precondition
# must give before the loop. len(segments)>=2 is a Requires; for n>=2 the slice
# bounds satisfy start_index<=end_index (worst case start=1,end=n-1 needs
# n>=2). If these can't be established the precondition is contradictory /
# PRECOND-TOO-STRONG. Stays in-region (asserts before the gold loop).
_ADMISS_IMPL = """    Assert(len(segments) >= 2)
    Assert(start_index(lower_open) <= end_index(upper_open, len(segments)))
    Assert(0 <= start_index(lower_open))
    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start
    while i < end:
        # invariants-start
        Invariant(Acc(list_pred(segments), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(start == start_index(lower_open))
        Invariant(end == end_index(upper_open, len(segments)))
        Invariant(0 <= start and start <= 1)
        Invariant(end == len(segments) or end == len(segments) - 1)
        Invariant(start <= end)
        Invariant(start <= i and i <= end)
        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        Invariant(MustTerminate(end - i + 1))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result"""
admiss = _swap(
    _BASE,
    """    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start""",
    _ADMISS_IMPL.split("\n    result = []")[0] + "\n    result = []  # type: List[int]\n    i = start",
)


# === 3. FRAME-MUTATION (read-only segments) — MANDATORY ====================
# segments is Acc(list_pred(segments), 1/2): half (read-only) permission. This
# rival WRITES to the input (segments[i] = segments[i], a value-preserving write)
# inside the loop. To execute a store Nagini needs FULL permission on segments,
# which the precondition does not grant — so it must be REJECTED for INSUFFICIENT
# PERMISSION. Every gold invariant is kept verbatim, so the rejection is
# attributable to the write, not a proof gap. A byte-fuzzer never tries this.
_FRAME_BODY = """        # invariants-end
        segments[i] = segments[i]
        result.append(segments[i])
        i = i + 1
    return result"""
frame_mut = _swap(_BASE, _GOLD_LOOP_BODY, _FRAME_BODY)


# === 4. PARTIAL-DOMAIN: prepatch bug (unconditional [1:-1]) ================
# Ignore BOTH booleans: always start=1, end=n-1 (the literal pre-patch slice
# np.dstack([X,Y])[1:-1]). This is exactly model_prepatch. It violates the
# LENGTH PIN: for extend='both' (lower_open=upper_open=True) the spec demands
# len == n - 0 = n, but this yields n-2. Must REJECT.
_PREPATCH_IMPL = """    start = 1
    end = len(segments) - 1
    result = []  # type: List[int]
    i = start"""
prepatch = _swap(
    _BASE,
    """    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start""",
    _PREPATCH_IMPL,
)


# === 5. PARTIAL-DOMAIN: ignore lower_open (start always 0) =================
# Compute end correctly, but always start=0 (ignore lower_open). Correct on the
# F2P cases where lower_open is True (extend in {both,min}) but WRONG when
# lower_open is False (extend in {max,neither}): start should be 1. Violates the
# LENGTH PIN (off by one) and the ELEMENT PIN (result[0] would be segments[0]
# but the spec pins it to segments[start_index(False)=1]). Must REJECT.
_IGNORE_LOWER_IMPL = """    start = 0
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start"""
ignore_lower = _swap(
    _BASE,
    """    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start""",
    _IGNORE_LOWER_IMPL,
)


# === 6. PARTIAL-DOMAIN: ignore upper_open (end always n) ===================
# Compute start correctly, but always end=n (ignore upper_open). Correct when
# upper_open is True (extend in {both,max}) but WRONG when upper_open is False
# (extend in {min,neither}): end should be n-1, keeping the end-most upper
# separator that belongs to the cap. Violates the LENGTH PIN. Must REJECT.
_IGNORE_UPPER_IMPL = """    start = 0 if lower_open else 1
    end = len(segments)
    result = []  # type: List[int]
    i = start"""
ignore_upper = _swap(
    _BASE,
    """    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start""",
    _IGNORE_UPPER_IMPL,
)


# === 7. PARTIAL-DOMAIN: drop the last kept element (off-by-one short) ======
# Bounds are correct but the loop stops one short (while i < end - 1), emitting
# one fewer separator than the slice has. Violates the LENGTH PIN: for
# extend='both' the F2P expects 3 separators, this yields 2. Must REJECT.
_SHORT_BODY = """        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result"""
_SHORT_BODY_NEW = """        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result"""
# (re-express via loop bound change rather than body change to keep invariants valid)
short_run = _swap(
    _BASE,
    "    i = start\n    while i < end:",
    "    i = start\n    while i < end - 1:",
)


SPEC_TESTS = [
    {
        "id": "pos-control-offset-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": pos_control,
        "rationale": (
            "structurally-different CORRECT impl: offset-indexed forward loop "
            "(j from 0, append segments[start+j]) instead of absolute-index "
            "loop. All gold invariants re-expressed in j (prefix pin + framing "
            "kept). Must verify against the frozen Ensures, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": admiss,
        "rationale": (
            "asserts len(segments)>=2 (a Requires) and that the precondition "
            "yields a well-formed slice (start_index<=end_index, start_index>=0) "
            "for any in-domain input before running the gold loop. Verifies iff "
            "the precondition is consistent/non-vacuous; else PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutation-write-segments",
        "kind": "uniqueness",
        "expect": "reject",
        "module": frame_mut,
        "refinement": (
            "A faithful real patch that mutates the candidate-segments array "
            "np.dstack([X,Y]) in place would corrupt the array that "
            "set_segments stores; the F2P reads it back via "
            "cbar.dividers.get_segments() and compares element values, so an "
            "in-place-mutating impl does not match the gold's read-only slice "
            "and need not produce the F2P-expected segment arrays. It is not "
            "behaviourally the gold patch."
        ),
        "rationale": (
            "REJECTION SOURCE = permission system. segments is granted only "
            "Acc(list_pred(segments), 1/2); the store `segments[i] = ...` "
            "requires FULL permission, which the precondition never grants — "
            "Nagini fails it for insufficient permission. Gold invariants kept "
            "verbatim so the failure is attributable to the write. If it "
            "verified, the read-only frame condition would be hollow "
            "(SPEC-TOO-WEAK / frame-mutation)."
        ),
    },
    {
        "id": "partial-domain-prepatch-unconditional-1-to-n1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": prepatch,
        "refinement": (
            "This is exactly the pre-patch behaviour (np.dstack([X,Y])[1:-1] "
            "unconditionally). model_prepatch reproduces it and FAILS — it is "
            "the documented prepatch witness. For extend='both' it produces n-2 "
            "separators where the F2P (test_colorbar_extend_drawedges[both-...]) "
            "expects all n=3; it does NOT resolve."
        ),
        "rationale": (
            "REJECTION SOURCE = LENGTH PIN postcondition "
            "len(Result()) == end_index(upper_open,n) - start_index(lower_open). "
            "When lower_open and upper_open are both True the spec demands "
            "len==n-0==n, but start=1,end=n-1 yields n-2. Verifier rejects."
        ),
    },
    {
        "id": "partial-domain-ignore-lower-open",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ignore_lower,
        "refinement": (
            "Always start=0 (ignores _extend_lower). Faithful real patch would "
            "set start_idx=0 even when the lower limit is NOT open ended, "
            "keeping the lower cap's end-most separator. For extend='max' "
            "(lower_open False) the F2P (test_colorbar_extend_drawedges[max-...]) "
            "expects positions [1,2] but this keeps [0,1,2]; does NOT resolve."
        ),
        "rationale": (
            "REJECTION SOURCE = LENGTH PIN (off by one when lower_open False: "
            "demands n - start_index(False)=n-1 but produces end-0) AND ELEMENT "
            "PIN (Result()[0] is segments[0] but spec pins it to "
            "segments[start_index(False)=1]). Verifier rejects."
        ),
    },
    {
        "id": "partial-domain-ignore-upper-open",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ignore_upper,
        "refinement": (
            "Always end=n (ignores _extend_upper). Faithful real patch would set "
            "end_idx=len(X) even when the upper limit is NOT open ended, keeping "
            "the upper cap's end-most separator. For extend='min' (upper_open "
            "False) the F2P (test_colorbar_extend_drawedges[min-...]) expects "
            "positions [0,1] but this keeps [0,1,2]; does NOT resolve."
        ),
        "rationale": (
            "REJECTION SOURCE = LENGTH PIN: when upper_open is False the spec "
            "demands len == (n-1) - start_index(lower_open), but end=n yields "
            "n - start_index. Verifier rejects."
        ),
    },
    {
        "id": "partial-domain-short-run-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": short_run,
        "refinement": (
            "Bounds correct but the loop stops one short (i < end-1), emitting "
            "one fewer separator than the slice. A faithful real patch dropping "
            "the last kept divider would, for extend='both', emit 2 dividers "
            "where the F2P expects 3 (res has three segment arrays); does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTION SOURCE = LENGTH PIN: len(Result()) is end-1-start but the "
            "spec demands end_index(upper_open,n)-start_index(lower_open) = "
            "end-start. Verifier rejects (and the loop also cannot reach i=end-1 "
            "so the per-element coverage of the last index is dropped)."
        ),
    },
]

# No @ContractOnly axioms and no consumed axiom in this bundle (meta.axioms == [],
# refinement.md §B). The single changed operation (the slice-bound selection) is
# modeled DEEPLY (start_index/end_index + verified copy loop) and validated as an
# A-reference by axiom_check.py (G-AX) on the HOST over 4 canonical F2P + 56
# small-exhaustive + 20000 fuzz configs. There is no in-container axiom obligation
# to probe here, so the axiom lane is vacuous.
AXIOM_TESTS = []

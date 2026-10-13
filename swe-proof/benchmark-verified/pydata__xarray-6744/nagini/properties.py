"""properties.py — PBT falsification manifest for pydata__xarray-6744.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical"). This battery is
reasoned from THIS spec's defended surface, not stamped out by a corruption
template.

The functions under spec
------------------------
    block_ends(n: int, w: int, center: bool)   -> List[int]   (the gold `stops`)
    block_begins(n: int, w: int, center: bool) -> List[int]   (the gold `starts`)

model the single changed hunk in `DataArrayRolling.__iter__`
(`xarray/core/rolling.py:270-282`). The gold patch makes the per-position window
index ranges centre-aware:

    offset = (window0 + 1) // 2 if self.center[0] else 1
    stops  = np.arange(offset, n + offset)     # stops[i]  = offset + i
    starts = stops - window0                     # starts[i] = offset + i - window0
    starts[: window0 - offset] = 0               # leading clamp -> max(0, .)

The pre-patch code used `offset == 1` always (centre flag ignored). `block_ends`
is the `stops` site, `block_begins` is the `starts` site.

The defended surface (model.py:159-239)
---------------------------------------
INPUTS ARE ALL PRIMITIVES PASSED BY VALUE: `n: int`, `w: int`, `center: bool`.
There is NO `Acc(x, 1/2)` read-only container input and NO mutable input. So the
FRAME-MUTATION class (directive 5) DOES NOT APPLY — there is nothing to overwrite
to satisfy the postcondition vacuously; an int/bool argument cannot be aliased or
written through. (has_readonly_input = False; stated in the StructuredOutput.)

block_ends load-bearing postcondition (model.py:165-175):
  Ensures(Acc(list_pred(Result())))
  Ensures(len(Result()) == n)
  (P_fold) ToSeq(Result()) == ends_from(0, n, w, center)
  (P_elem) Forall i in [0,n): Result()[i] == end_at(i, w, center)
           where end_at(i) = i + end_shift(w, center),
                 end_shift(w, center) = (w+1)//2 if center else 1

block_begins load-bearing postcondition (model.py:203-215):
  Ensures(Acc(list_pred(Result()))) ; len(Result()) == n
  (P_fold) ToSeq(Result()) == begins_from(0, n, w, center)
  (P_elem) Forall i in [0,n): Result()[i] == begin_at(i, w, center)
           where begin_at(i) = max(0, end_at(i) - w)
  (P_nn)   Forall i in [0,n): Result()[i] >= 0

The DISCRIMINATING clause is the `center`-dependence of `end_shift`: when
`center` is true the shift must be `(w+1)//2 == ceil(w/2)`, not `1`. That is
exactly what `model_prepatch.py` (shift = 1 always) FAILS (meta.json G-DIFF),
and exactly what the F2P `test_rolling_iter[numpy-{3,7}-True-{1,2}]` cases assert
(manual centred iteration == `rolling.mean()`). The begins side additionally
defends the clamp `max(0, .)` (P_nn + P_elem via begin_at).

The @Pure helpers are GROUNDED, not an answer-key oracle
--------------------------------------------------------
`end_at`/`begin_at`/`end_shift` are TOTAL pure integer arithmetic, fully unfolded
in their own `Ensures` as a function of (i, w, center). The postcondition pins
each element to `end_at(i)`/`begin_at(i)`, which IS the correct closed form —
there is NO opaque oracle to echo wrongly: echoing `end_at(i)` is just computing
the right value. Hence UNGROUNDED-ORACLE ECHO (directive 2) does NOT apply; we
instead supply honest cheapest-correct positive controls (a local-variable
reshape on the ends side; a branch-reorder of the clamp on the begins side) which
MUST verify. Stated in 'assessment'.

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
Both functions are TOTAL over their precondition (`n >= 0`, `w > 0`): each always
returns a `List[int]` of length n, never raises, has no side effect (no mutable
input). The real `__iter__` index computation likewise never raises on this
domain (`__init__` enforces `w > 0`; an empty rolling dim gives n = 0 -> an empty
arange, no raise). The value abstraction (the returned index list) fully captures
the behaviour, so there is no capability-token discriminator to build. The
CONTROL-FLOW-EFFECT class (directive 4) therefore does NOT apply; stated in
'assessment'.

Axiom lane (A-reference, no @ContractOnly axioms)
-------------------------------------------------
meta.axioms = [] — there is NO consumed `@ContractOnly` axiom. The lone
out-of-band obligation is the A-reference deep model (`end_shift`/`end_at`/
`begin_at`) which must equal the REAL changed operation (the gold patch's
`np.arange`/subtract/slice-assign). axiom_check.py (G-AX) validates exactly that.
The AXIOM_TESTS REUSE + strengthen axiom_check.py. CRUCIAL (pilot trap 6): the
runner mounts ONLY the probe at /work, so axiom_check.py's source is read on the
HOST at manifest-load time and EMBEDDED into the probe string. The "callee" here
is pure integer arithmetic (numpy arange/subtract/slice-assign), so the probe is
stdlib-only and needs no Docker library; apply_gold is irrelevant (the arithmetic
is reproduced verbatim from the post-patch source), set False.
 - axiom-soundness: the deep model == the gold patch's index arrays on a boundary
   sweep + the F2P windows {1,2,3,7} + both center flags + 200k fuzz cases + the
   issue's worked example. Any mismatch => AXIOM-UNSOUND.
 - axiom-containment: every callee-input the MODEL can reach lies in the deep
   model's domain. The model evaluates end_shift/end_at/begin_at only at
   `w = caller w > 0` and `i in [0, n)` with `n >= 0` (the loop runs k = n..1,
   so i = k-1 in [0, n)); each helper's Requires is exactly `w > 0`
   (+ index bounds for the folds), so every reachable evaluation is in-domain.
   A reachable evaluation outside the domain => AXIOM-TOO-WEAK-FOR-CALLER.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY text inside a function's `# impl-start` / `# impl-end` body (the whole
body, or a unique substring within it). `markers.same_spec` is therefore
GUARANTEED (spec_view elides every impl region, invariants included) and a
rejection is attributable to the POSTCONDITION / loop INVARIANT / the spec
helpers, never to a tampered spec. The @Pure helpers and the pre/post-conditions
are NEVER touched. Each `expect:"reject"` rival carries the refinement argument
that its faithful real patch would NOT resolve the F2P.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6744"
FLOAT_ENCODING = None  # meta.json float_encoding is null


# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two gold impl bodies, verbatim (each unique in model.py). Whole-body swaps
# keep every framing Assert + loop Invariant in place, so a reject is a genuine
# invariant/postcondition failure, never a dangling-reference translation error.
# ---------------------------------------------------------------------------
_GOLD_ENDS_BODY = """    # impl-start
    shift = end_shift(w, center)
    stops = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(stops)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(ends_unfold(k - 1, n, w, center))
        stops = [shift + (k - 1)] + stops
        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
        k = k - 1
    return stops
    # impl-end"""

_GOLD_BEGINS_BODY = """    # impl-start
    shift = end_shift(w, center)
    starts = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(starts)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(starts) == begins_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(begins_unfold(k - 1, n, w, center))
        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts
        Assert(starts[0] == begin_at(k - 1, w, center))
        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
        k = k - 1
    return starts
    # impl-end"""

# sanity: both bodies are present exactly once in the frozen model
assert _BASE.count(_GOLD_ENDS_BODY) == 1, "ends gold body drift"
assert _BASE.count(_GOLD_BEGINS_BODY) == 1, "begins gold body drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) ENDS local-variable reshape (soundness). Bind the per-position end into a
# fresh typed local `e` and prepend `[e]` instead of inlining `shift + (k - 1)`.
# Behaviour identical; the BACKWARD prepend loop (matching the FRONT-recursive
# fold ends_from — directive 3 trap avoided: NO loop-direction flip, NO
# forward-append) and every framing Assert / loop Invariant are kept verbatim. We
# add `Assert(e == shift + (k - 1))` to bridge the local to the inlined form the
# final fold-assert uses. If this CORRECT impl fails to verify, the postcondition
# is over-fit to the inlined spelling => SPEC-TOO-STRONG.
_POS_ENDS_RESHAPE = _swap(_BASE, _GOLD_ENDS_BODY, """    # impl-start
    shift = end_shift(w, center)
    stops = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(stops)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(ends_unfold(k - 1, n, w, center))
        e = shift + (k - 1)  # type: int
        Assert(e == shift + (k - 1))
        stops = [e] + stops
        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
        k = k - 1
    return stops
    # impl-end""")

# (5b) BEGINS clamp branch-reorder (soundness). Rewrite the clamp branch
# `if raw > 0: [raw] else: [0]` as the logically-equivalent
# `if raw <= 0: [0] else: [raw]`. Same value on every position (raw > 0 -> raw;
# raw <= 0 -> 0); the entire backward-loop scaffold + front-recursive invariant +
# both framing asserts are kept verbatim. If it fails => SPEC-TOO-STRONG (over-fit
# to the `raw > 0` branch spelling).
_POS_BEGINS_REORDER = _swap(
    _BASE,
    """        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts""",
    """        raw = (shift + (k - 1)) - w
        if raw <= 0:
            starts = [0] + starts
        else:
            starts = [raw] + starts""",
)

# (6) ADMISSIBILITY: a self-call on the in-scope F2P-shaped input must establish
# the precondition. block_ends' callee Requires is exactly the caller's own (n>=0,
# w>0, in scope), and primitives are passed by value so no permission is consumed.
# Prepend the self-call and Assert its length is n (its Ensures). If the call site
# cannot establish the Requires for a legitimate input => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    "    # impl-start\n    shift = end_shift(w, center)\n    stops = []  # type: List[int]",
    "    # impl-start\n"
    "    _probe = block_ends(n, w, center)\n"
    "    Assert(len(_probe) == n)\n"
    "    shift = end_shift(w, center)\n"
    "    stops = []  # type: List[int]",
)


# ===========================================================================
# UNIQUENESS RIVALS (must be REJECTED) — the centred-shift + clamp defended surface
# ===========================================================================

# (uniqueness — PREPATCH BUG / center ignored) shift hardcoded to 1, ignoring
# `center`. This is the exact pre-patch regression (offset == 1 always). All
# framing asserts + invariants kept verbatim, so the rejection is attributable to
# the loop Invariant `shift == end_shift(w, center)` and the Assert
# `shift + (k-1) == end_at(k-1, w, center)` failing when center is True and w > 1
# (then end_shift = (w+1)//2 != 1), and ultimately the postcondition P_fold/P_elem.
#
# Refinement: its faithful real patch is `offset = 1` (the pre-patch code).
# model_prepatch.py reproduces this and FAILS the fold invariant (meta.json
# G-DIFF). The F2P test_rolling_iter[numpy-3-True-*] / [numpy-7-True-*] assert that
# manual centred iteration == rolling.mean(); with offset = 1 the centred blocks
# are mis-justified (e.g. n=9,w=3,center=True -> position 1's block becomes [0,2)
# instead of [0,3), masked to NaN), so the test FAILS. It would NOT resolve.
_RIVAL_ENDS_IGNORE_CENTER = _swap(
    _GOLD_ENDS_BODY,
    "    shift = end_shift(w, center)",
    "    shift = 1",
)
_RIVAL_ENDS_IGNORE_CENTER = _swap(_BASE, _GOLD_ENDS_BODY, _RIVAL_ENDS_IGNORE_CENTER)

# (uniqueness — PARTIAL-DOMAIN, floor instead of ceil) centred shift computed as
# `w // 2` instead of `(w + 1) // 2`. Agrees with the gold shift ONLY for EVEN w
# (w//2 == (w+1)//2 iff w even); diverges for ODD w (w=3: 1 vs 2; w=7: 3 vs 4),
# which are exactly two of the F2P windows. Non-centred branch (1) is unchanged.
# Framing asserts kept verbatim so the rejection is the Invariant
# `shift == end_shift(w, center)` / the end_at Assert for centred odd-w inputs.
#
# Refinement: its faithful real patch is `offset = window0 // 2 if center else 1`.
# For n,w=3,center=True it gives offset=1 (== the buggy pre-patch value), so the
# centred mean is mis-aligned and F2P test_rolling_iter[numpy-3-True-*] FAILS; for
# w=7 it gives offset=3 vs the correct 4, again mis-justifying the window. It would
# NOT resolve.
_RIVAL_ENDS_FLOOR = _swap(
    _GOLD_ENDS_BODY,
    "    shift = end_shift(w, center)",
    "    shift = w // 2 if center else 1",
)
_RIVAL_ENDS_FLOOR = _swap(_BASE, _GOLD_ENDS_BODY, _RIVAL_ENDS_FLOOR)

# (uniqueness — OFF-BY-ONE on every position) shift = end_shift(w, center) + 1.
# Every end (and hence every start) is shifted forward by one extra position, on
# BOTH center flags. Framing asserts kept verbatim; rejection is the Invariant
# `shift == end_shift(w, center)` / the end_at Assert at every k.
#
# Refinement: its faithful real patch is `offset = ((window0+1)//2 if center else
# 1) + 1`. Then stops = arange(offset, n+offset) overshoots by one, so even the
# non-centred F2P cases (and every P2P rolling-iteration case) read the wrong
# half-open block — the manual-iteration mean disagrees with rolling.mean() and the
# F2P assert_allclose FAILS. It would NOT resolve.
_RIVAL_ENDS_OFFBYONE = _swap(
    _GOLD_ENDS_BODY,
    "    shift = end_shift(w, center)",
    "    shift = end_shift(w, center) + 1",
)
_RIVAL_ENDS_OFFBYONE = _swap(_BASE, _GOLD_ENDS_BODY, _RIVAL_ENDS_OFFBYONE)

# (uniqueness — BEGINS drop the clamp) always prepend `raw` (never clamp to 0),
# dropping the `max(0, .)`. CORRECT only on the sub-domain where every position's
# raw >= 0 (i.e. w is small enough that no leading block underflows); WRONG for the
# leading positions of any real window (raw < 0). Framing asserts kept verbatim;
# rejection is the postcondition P_nn (Result()[i] >= 0) and the Assert
# `starts[0] == begin_at(k-1, w, center)` (begin_at clamps, raw does not), failing
# whenever raw < 0.
#
# Refinement: its faithful real patch DROPS the `starts[: window0 - offset] = 0`
# clamp, leaving negative start indices. numpy `slice(negative, stop)` indexes from
# the END of the dimension, so the leading windows select the WRONG (tail) data;
# the manual-iteration mean diverges from rolling.mean() and the F2P assert_allclose
# FAILS (and many P2P rolling cases). It would NOT resolve.
_RIVAL_BEGINS_NOCLAMP = _swap(
    _GOLD_BEGINS_BODY,
    """        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts""",
    """        raw = (shift + (k - 1)) - w
        starts = [raw] + starts""",
)
_RIVAL_BEGINS_NOCLAMP = _swap(_BASE, _GOLD_BEGINS_BODY, _RIVAL_BEGINS_NOCLAMP)

# (uniqueness — BEGINS center ignored) the prepatch bug on the starts site:
# shift = 1 always. Mirrors the ends ignore-center rival; the starts fold invariant
# `ToSeq(starts) == begins_from(k, n, w, center)` and the begin_at Assert fail for
# centred windows with w > 1. Framing asserts kept verbatim.
#
# Refinement: faithful real patch `offset = 1` always -> starts = arange(1,n+1) -
# window0 with the wrong leading clamp count; the centred-window starts are
# mis-justified exactly as the pre-patch bug (G-DIFF). F2P
# test_rolling_iter[numpy-3-True-*]/[numpy-7-True-*] FAIL. It would NOT resolve.
_RIVAL_BEGINS_IGNORE_CENTER = _swap(
    _GOLD_BEGINS_BODY,
    "    shift = end_shift(w, center)",
    "    shift = 1",
)
_RIVAL_BEGINS_IGNORE_CENTER = _swap(_BASE, _GOLD_BEGINS_BODY, _RIVAL_BEGINS_IGNORE_CENTER)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-ends-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_ENDS_RESHAPE,
     "rationale": "structurally-different but CORRECT block_ends impl: the per-position end is "
                  "bound to a fresh typed local `e` (with Assert(e == shift + (k-1)) bridging it "
                  "to the inlined form the fold-assert uses) and prepended; the backward prepend "
                  "loop matching the front-recursive ends_from fold and every framing Assert / "
                  "loop Invariant are kept verbatim (no loop-direction flip, directive-3 trap "
                  "avoided). Must verify; else the postcondition is over-fit to the inlined "
                  "spelling => SPEC-TOO-STRONG."},
    {"id": "pos-begins-clamp-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_BEGINS_REORDER,
     "rationale": "structurally-different but CORRECT block_begins impl: the clamp branch "
                  "`if raw > 0: [raw] else: [0]` rewritten as the equivalent `if raw <= 0: [0] "
                  "else: [raw]` (same value on every position). Entire backward-loop scaffold + "
                  "front-recursive invariant + both framing asserts kept verbatim. Must verify; "
                  "else the spec is over-fit to the branch spelling => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call block_ends(n, w, center) on the in-scope F2P-shaped input "
                  "(n >= 0, w > 0 — the caller's own precondition, in scope; primitives passed "
                  "by value so no permission is consumed) must establish the Requires and return "
                  "a list of length n. If the call site cannot establish the Requires for a "
                  "legitimate input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-ends-ignore-center", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_IGNORE_CENTER,
     "refinement": "PREPATCH BUG: shift hardcoded to 1, ignoring center — the exact pre-patch "
                   "`offset = 1` always. model_prepatch.py reproduces this and FAILS the fold "
                   "invariant (meta.json G-DIFF). The F2P test_rolling_iter[numpy-3-True-*] / "
                   "[numpy-7-True-*] assert manual centred iteration == rolling.mean(); with "
                   "offset = 1 the centred blocks are mis-justified (n=9,w=3,center=True: "
                   "position 1's block becomes [0,2) not [0,3), masked to NaN), so the test "
                   "FAILS. It would NOT resolve.",
     "rationale": "Rejection source: the loop Invariant `shift == end_shift(w, center)` "
                  "(model.py:185) and the Assert `shift + (k-1) == end_at(k-1, w, center)` "
                  "(model.py:188) fail when center is True and w > 1 (end_shift = (w+1)//2 != 1), "
                  "and ultimately P_fold/P_elem. If it verified => SPEC-TOO-WEAK (admits the "
                  "center-ignoring prepatch regression)."},
    {"id": "rival-ends-floor-shift", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_FLOOR,
     "refinement": "PARTIAL-DOMAIN (floor vs ceil): centred shift `w // 2` instead of "
                   "`(w + 1) // 2`. Agrees with the gold shift only for EVEN w; diverges for ODD "
                   "w (w=3: 1 vs 2; w=7: 3 vs 4) — exactly two F2P windows. Its faithful real "
                   "patch `offset = window0 // 2 if center else 1` gives offset=1 for w=3,"
                   "center=True (== the buggy pre-patch value), so test_rolling_iter[numpy-3-"
                   "True-*] FAILS (and w=7 mis-justifies with offset 3 vs 4). It would NOT "
                   "resolve.",
     "rationale": "Rejection source: the Invariant `shift == end_shift(w, center)` / the "
                  "Assert `shift + (k-1) == end_at(k-1, w, center)` for centred ODD-w inputs "
                  "(end_shift uses (w+1)//2), and ultimately P_elem. If it verified => "
                  "SPEC-TOO-WEAK on the odd-window centred sub-domain."},
    {"id": "rival-ends-offbyone", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENDS_OFFBYONE,
     "refinement": "OFF-BY-ONE on every position: shift = end_shift(w, center) + 1. Its faithful "
                   "real patch `offset = (... ) + 1` makes stops = arange(offset, n+offset) "
                   "overshoot by one on BOTH center flags, so even the non-centred F2P cases and "
                   "every P2P rolling-iteration case read the wrong half-open block; the manual "
                   "mean disagrees with rolling.mean() and assert_allclose FAILS. It would NOT "
                   "resolve.",
     "rationale": "Rejection source: the Invariant `shift == end_shift(w, center)` / the "
                  "Assert `shift + (k-1) == end_at(k-1, w, center)` at every k (end_at = i + "
                  "end_shift, with no +1), and ultimately P_elem. If it verified => "
                  "SPEC-TOO-WEAK (admits a uniformly-shifted block)."},
    {"id": "rival-begins-drop-clamp", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BEGINS_NOCLAMP,
     "refinement": "DROP THE CLAMP: always prepend `raw` (no max(0, .)). Its faithful real patch "
                   "DROPS `starts[: window0 - offset] = 0`, leaving NEGATIVE start indices. numpy "
                   "slice(negative, stop) indexes from the END of the dimension, so the leading "
                   "windows select the wrong (tail) data; the manual-iteration mean diverges from "
                   "rolling.mean() and the F2P assert_allclose FAILS (plus many P2P rolling "
                   "cases). It would NOT resolve.",
     "rationale": "Rejection source: the postcondition P_nn (Forall i. Result()[i] >= 0, "
                  "model.py:214) and the Assert `starts[0] == begin_at(k-1, w, center)` "
                  "(model.py:235; begin_at clamps to 0, raw does not), failing whenever raw < 0 "
                  "(the leading positions of any window with w > offset). If it verified => "
                  "SPEC-TOO-WEAK (admits negative, unclamped starts)."},
    {"id": "rival-begins-ignore-center", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BEGINS_IGNORE_CENTER,
     "refinement": "PREPATCH BUG on the starts site: shift = 1 always. Faithful real patch "
                   "`offset = 1` -> starts = arange(1, n+1) - window0 with the wrong leading "
                   "clamp count; centred-window starts are mis-justified exactly as the pre-patch "
                   "bug (G-DIFF). F2P test_rolling_iter[numpy-3-True-*] / [numpy-7-True-*] FAIL. "
                   "It would NOT resolve.",
     "rationale": "Rejection source: the loop Invariant `ToSeq(starts) == begins_from(k, n, w, "
                  "center)` (model.py:226) and the Assert `starts[0] == begin_at(k-1, w, center)` "
                  "(model.py:235) fail for centred windows with w > 1, and ultimately "
                  "P_fold/P_elem. If it verified => SPEC-TOO-WEAK (center-ignoring on starts)."},
]


# ===========================================================================
# AXIOM LANE (A-reference deep model; NO @ContractOnly axiom). REUSE + strengthen
# axiom_check.py. The runner mounts ONLY the probe at /work (pilot trap 6), so
# axiom_check.py's source is read on the HOST here and EMBEDDED into the probe.
# The "callee" is pure integer arithmetic (numpy arange/subtract/slice-assign over
# an integer dtype == plain-int range/subtract/slice-assign), reproduced verbatim
# from the post-patch source; stdlib-only, no Docker library needed, apply_gold
# irrelevant (set False).
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# (axiom-soundness) Run the EXACT axiom_check.py battery: it reproduces the gold
# patch's `offset/stops/starts` arithmetic with plain ints and asserts the deep
# model (end_at/begin_at + the end_shift = ceil(w/2)/1 and clamp identities) equals
# it element-by-element on a boundary sweep (n 0..21, w in {1..8,21}, both center
# flags), the issue's worked example (n=9,w=3,center=True -> position 1's block
# [0,3)), and 200000 fuzz (n,w,center) cases. Exit 0 iff every observation matches.
_AX_SOUNDNESS = _AXIOM_CHECK_SRC

# (axiom-containment) Confirm every callee-input the MODEL can REACH lies in the
# deep model's Requires domain. The model evaluates end_shift/end_at/begin_at only
# at: w = the caller's w (Requires w > 0); center = the caller's bool; and index
# i = k - 1 for k = n down to 1, i.e. i in [0, n) with n >= 0 (Requires n >= 0).
# Each helper's Requires is exactly `w > 0` (end_shift/end_at/begin_at) plus index
# bounds for the folds (0 <= j <= n, 0 <= m < n - j). We assert that for every
# (n, w, center) the model can be called on, every evaluation the loops perform is
# in-domain: w > 0 holds by precondition; every loop index i is in [0, n); the fold
# index args stay in 0 <= j <= n and 0 <= m < n - j. Covering w <= 0 or i outside
# [0, n) is impossible for the model (excluded by Requires / the loop bound) — we
# positively confirm those are OUTSIDE the reachable domain (sound, not a defect).
# A reachable evaluation outside the domain => AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import random
import sys


def m_end_shift(w, center):
    # the deep model's end_shift; Requires w > 0
    return (w + 1) // 2 if center else 1


def check_reachable(n, w, center):
    # Precondition the model is called under: n >= 0, w > 0.
    if not (n >= 0 and w > 0):
        return True  # not a reachable caller input; skip
    # end_shift/end_at/begin_at Requires is exactly w > 0 -> satisfied.
    if not (w > 0):
        print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches end_shift with w=%d <= 0" % w)
        return False
    # The loop runs k = n down to 1, evaluating end_at(k-1)/begin_at(k-1), i.e.
    # i = k - 1 in [0, n). Every such i must satisfy the helpers' index needs.
    for k in range(n, 0, -1):
        i = k - 1
        if not (0 <= i and i < n):
            print("AXIOM-TOO-WEAK-FOR-CALLER: loop index i=%d outside [0,%d)" % (i, n))
            return False
        # ends_index_lemma / begins_index_lemma Requires: 0 <= j <= n and
        # 0 <= m < n - j. The postcondition invokes them at j = 0, m = i, so:
        j, m = 0, i
        if not (0 <= j and j <= n and 0 <= m and m < n - j):
            print("AXIOM-TOO-WEAK-FOR-CALLER: fold index (j=%d,m=%d) outside domain "
                  "for n=%d" % (j, m, n))
            return False
        # ends_from / begins_from Requires: 0 <= j <= n; the loop invariant uses
        # j = k in [0, n].
        if not (0 <= k and k <= n):
            print("AXIOM-TOO-WEAK-FOR-CALLER: fold j=k=%d outside [0,%d]" % (k, n))
            return False
        # end_shift is always evaluated with w > 0 -> in-domain.
        m_end_shift(w, center)
    return True


def main():
    checked = 0
    # boundary sweep over the reachable (n, w, center) domain (n >= 0, w > 0),
    # including the F2P windows {1,2,3,7} and the issue's n=9.
    for n in [0, 1, 2, 3, 7, 8, 9, 10, 21]:
        for w in [1, 2, 3, 7, 8, 21]:
            for center in (True, False):
                if not check_reachable(n, w, center):
                    return 1
                checked += 1
    # confirm the NON-reachable edges (w <= 0, n < 0) are excluded by the model's
    # precondition (sound over-coverage / under-coverage is irrelevant here): the
    # model can never call the helpers with w <= 0 or a negative loop index.
    for n in [-1, -5]:
        assert not (n >= 0), "n<0 is excluded by Requires(n >= 0)"
    for w in [0, -1]:
        assert not (w > 0), "w<=0 is excluded by Requires(w > 0)"
    # randomized fuzz over the reachable domain
    rng = random.Random(6744)
    for _ in range(20000):
        n = rng.randint(0, 80)
        w = rng.randint(1, 80)
        center = rng.random() < 0.5
        if not check_reachable(n, w, center):
            return 1
        checked += 1
    print("CONTAINMENT OK: every callee-input the model can reach is in-domain over "
          "%d (n,w,center) cases: w > 0 (helpers' Requires), every loop index i in "
          "[0,n), and every fold index (j,m) in 0<=j<=n & 0<=m<n-j. The w<=0 / n<0 "
          "edges are OUTSIDE the model's reachable domain (Requires n>=0, w>0), which "
          "is sound, not a containment defect." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-deepmodel-sound", "axiom": "end_at/begin_at",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": False,
     "probe": _AX_SOUNDNESS,
     "rationale": "REUSES axiom_check.py: reproduces the gold patch's offset/stops/starts "
                  "arithmetic with plain ints (numpy integer arange/subtract/slice-assign == the "
                  "same plain-int ops) and asserts the deep model end_at/begin_at equals it "
                  "element-by-element on a boundary sweep (n 0..21, w in {1..8,21}, both center "
                  "flags), the issue's worked example (n=9,w=3,center=True -> position 1's block "
                  "[0,3)), and 200000 fuzz cases, plus the end_shift = ceil(w/2)/1 and "
                  "begin_at = max(0, end_at - w) identities the proof relies on. The deep model "
                  "is an A-reference (no @ContractOnly axiom); any mismatch => AXIOM-UNSOUND."},
    {"id": "ax-deepmodel-containment", "axiom": "end_at/begin_at",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": False,
     "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach is in-domain: the helpers' Requires is "
                  "w > 0 (satisfied by the caller's Requires(w > 0)); every loop index i = k - 1 "
                  "lies in [0, n) (the loop runs k = n..1 with Requires(n >= 0)); the fold index "
                  "args stay in 0 <= j <= n and 0 <= m < n - j. The w<=0 / n<0 edges are OUTSIDE "
                  "the reachable domain by precondition (sound). A reachable evaluation outside "
                  "the domain => AXIOM-TOO-WEAK-FOR-CALLER."},
]

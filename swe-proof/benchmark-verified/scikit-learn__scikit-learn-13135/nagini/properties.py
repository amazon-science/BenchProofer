# properties.py — PBT falsification battery for scikit-learn__scikit-learn-13135.
#
# NOT a Nagini module; a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS, writes each
# `module` to a temp file, runs Nagini verify + markers.same_spec against the
# frozen model.py, and stamps RESULT. Region-surgery (we replace ONLY the text
# strictly inside # impl-start / # impl-end via _swap on the gold body) mechanically
# GUARANTEES same_spec stays True — the spec regions (axioms / pure / pre / post)
# are never touched.
#
# DEFENDED SURFACE (reasoned from the spec, not corruption-stamped)
# -----------------------------------------------------------------
#   make_bin_edges(a, b, c, d, col_min, col_max : float) -> List[float]
#   Models the kmeans-branch bin-edge construction of KBinsDiscretizer.fit. The
#   gold patch inserts `centers.sort()` BEFORE forming the pairwise midpoints, so
#   the bin-boundary list is non-decreasing (the property np.digitize requires).
#
#   PRECONDITION (Requires): col_min <= col_max, and col_min <= each of a,b,c,d
#   <= col_max. All six inputs are PLAIN `float` SCALARS passed BY VALUE. There is
#   NO Acc(x, 1/2) read-only mutable input (no array/list/object permission in the
#   Requires), so the FRAME-MUTATION weakness class is N/A for this spec: there is
#   no half-permission input to overwrite to satisfy a postcondition vacuously, and
#   a "write to a 1/2 input" rival would have nothing to write to. has_readonly_input
#   == False. (The only produced permission, Acc(list_pred(Result())), is a fresh
#   OUTPUT obligation, not an input frame.) See 'assessment'.
#
#   POSTCONDITION (load-bearing clauses):
#     (P0) Acc(list_pred(Result()))                       fresh list produced
#     (P1) len(Result()) == 5                             exactly five boundaries
#     (P2) Result()[0] == col_min                         left-closed by col_min
#     (P3) Result()[4] == col_max                         right-closed by col_max
#     (P4) Result()[1] == (order4(a,b,c,d,col_min,col_max)[0]
#                        + order4(a,b,c,d,col_min,col_max)[1]) / 2   <-- discriminator
#     (P5) Result()[2] == (order4(...)[1] + order4(...)[2]) / 2      <-- discriminator
#     (P6) Result()[3] == (order4(...)[2] + order4(...)[3]) / 2      <-- discriminator
#     (P7) non_decreasing(ToSeq(Result()))                monotone boundary list
#
#   P4/P5/P6 pin each interior boundary to the EXACT midpoint of a consecutive pair
#   of the centres TAKEN IN NON-DECREASING ORDER (order4 is the @ContractOnly
#   A-consumed sort). order4 is GROUNDED in the actual arguments a,b,c,d,col_min,
#   col_max (it is not an opaque answer-key keyed off the desired output): the only
#   way to satisfy P4/P5/P6 is to actually compute order4 and the ordered midpoints.
#   So the "ungrounded-oracle echo" class has no WRONG echo — echoing order4's result
#   IS doing the sort. We therefore (directive-2 fallback) ship honest cheapest /
#   structurally-different positive controls instead of a wrong-echo reject, and
#   instead probe whether the value clauses P4/P5/P6 are genuinely load-bearing
#   beyond the weaker P7 (a rival that satisfies P7 trivially but breaks a value
#   clause must still be rejected — see reject-flat-monotone).
#
#   THE REAL BUG (prepatch / model_prepatch.py): the midpoints were formed from the
#   centres in the order k-means emitted them, with NO sort. That breaks P4/P5/P6
#   (the interior boundary is no longer the ordered-centre midpoint) and P7 (an
#   out-of-order boundary list), and downstream np.digitize raises
#   `ValueError: bins must be monotonically increasing or decreasing`.
#
# AXIOM lane: order4 is the single @ContractOnly A-consumed axiom modeling the
# in-place ascending sort numpy.ndarray.sort that the patch adds (`centers.sort()`).
# We reuse the bundle's audited axiom_check.py verbatim for soundness, and add a
# caller-domain containment probe.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13135"
FLOAT_ENCODING = "real"  # meta.json float_encoding == "real" (real-valued ordering)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The EXACT frozen impl-region BODY (strictly between # impl-start and # impl-end,
# marker comment lines EXCLUDED). We only ever replace this body, so the spec view
# is untouched and markers.same_spec stays True for every spec case.
_GOLD = (
    "    # Arrange the centres into non-decreasing order BEFORE forming the midpoints.\n"
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    m2 = (s[2] + s[3]) / 2\n"
    "    result = [col_min, m0, m1, m2, col_max]  # type: List[float]\n"
    "    # Each midpoint lies between its two ordered centres, so the midpoints are\n"
    "    # non-decreasing and bracketed by the column bounds; the whole boundary list\n"
    "    # is therefore non-decreasing.\n"
    "    Assert(s[0] <= m0 and m0 <= s[1])\n"
    "    Assert(s[1] <= m1 and m1 <= s[2])\n"
    "    Assert(s[2] <= m2 and m2 <= s[3])\n"
    "    Assert(col_min <= m0)\n"
    "    Assert(m0 <= m1)\n"
    "    Assert(m1 <= m2)\n"
    "    Assert(m2 <= col_max)\n"
    "    return result\n"
)


def _impl(body: str) -> str:
    """Full model.py variant with ONLY the impl-region body replaced."""
    return _swap(_BASE, _GOLD, body)


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# Compute the three midpoints in REVERSE variable order (m2, then m1, then m0)
# and reorder the monotonicity proof-hint asserts to match. Same computed result
# (the same ordered-midpoint list literal), only the executable shape / assert
# order changed. No induction lemma (order4 is consumed by its Ensures; the
# asserts are bracketing hints the gold proof already uses). MUST verify — else
# SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_REORDER = (
    "    # Order the centres first, then form the midpoints last-to-first.\n"
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m2 = (s[2] + s[3]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    result = [col_min, m0, m1, m2, col_max]  # type: List[float]\n"
    "    # Same bracketing obligations, asserted in a different order.\n"
    "    Assert(s[2] <= m2 and m2 <= s[3])\n"
    "    Assert(s[1] <= m1 and m1 <= s[2])\n"
    "    Assert(s[0] <= m0 and m0 <= s[1])\n"
    "    Assert(col_min <= m0)\n"
    "    Assert(m0 <= m1)\n"
    "    Assert(m1 <= m2)\n"
    "    Assert(m2 <= col_max)\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# 5'. POSITIVE CONTROL #2 (soundness) — build the list element-by-element via
# append into a fresh typed local instead of a single list literal, re-asserting
# each appended element's value so the per-index framing the postcondition needs
# (P2/P3/P4/P5/P6) is re-established around each append. Keeps the gold bracketing
# asserts (directive-2: a positive control must KEEP the framing it still needs).
# A genuinely different executable shape that must verify — else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_APPEND = (
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    m2 = (s[2] + s[3]) / 2\n"
    "    Assert(s[0] <= m0 and m0 <= s[1])\n"
    "    Assert(s[1] <= m1 and m1 <= s[2])\n"
    "    Assert(s[2] <= m2 and m2 <= s[3])\n"
    "    result = []  # type: List[float]\n"
    "    result.append(col_min)\n"
    "    result.append(m0)\n"
    "    result.append(m1)\n"
    "    result.append(m2)\n"
    "    result.append(col_max)\n"
    "    # re-establish the per-index values the postcondition pins\n"
    "    Assert(result[0] == col_min)\n"
    "    Assert(result[1] == m0)\n"
    "    Assert(result[2] == m1)\n"
    "    Assert(result[3] == m2)\n"
    "    Assert(result[4] == col_max)\n"
    "    Assert(col_min <= m0)\n"
    "    Assert(m0 <= m1)\n"
    "    Assert(m1 <= m2)\n"
    "    Assert(m2 <= col_max)\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input
# and is non-vacuous. The F2P column is [0, 0.5, 2, 3, 9, 10] (col_min=0,
# col_max=10) and the centres k-means emits are UNSORTED reals inside [0,10]. We
# keep the gold impl and add entry asserts that the Requires actually holds for
# such an input (each centre in [col_min, col_max]) and that order4 is callable on
# it (its Requires lo<=a<=hi is established from make_bin_edges's own Requires).
# If a legitimate F2P-shaped input could not establish the Requires / call order4
# this would fail => PRECOND-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS = (
    "    # admissibility witnesses: the Requires holds for a normal F2P-shaped\n"
    "    # input (unsorted centres in the column range), and order4 is callable.\n"
    "    Assert(col_min <= a and a <= col_max)\n"
    "    Assert(col_min <= b and b <= col_max)\n"
    "    Assert(col_min <= c and c <= col_max)\n"
    "    Assert(col_min <= d and d <= col_max)\n"
    "    Assert(col_min <= col_max)\n"
    + _GOLD
)


# ---------------------------------------------------------------------------
# 1. THE REAL BUG — prepatch rival: form the midpoints from the centres in the
# order k-means produced them, with NO order4 sort (this IS model_prepatch.py).
# expect=reject. Fails P4/P5/P6 (interior boundary no longer the ordered-centre
# midpoint) and P7 (out-of-order boundary list).
# ---------------------------------------------------------------------------
_W_PREPATCH = (
    "    # PREPATCH BUG: midpoints from the centres in given (unsorted) order.\n"
    "    m0 = (a + b) / 2\n"
    "    m1 = (b + c) / 2\n"
    "    m2 = (c + d) / 2\n"
    "    result = [col_min, m0, m1, m2, col_max]  # type: List[float]\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN — order the centres for two of the three midpoints but form
# the LAST midpoint from the RAW (unsorted) last two arguments c, d instead of the
# ordered pair s[2], s[3]. Correct on most inputs (whenever c,d happen to be the
# two largest in order) but diverges when they are not. expect=reject — fails P6
# (Result()[3] == (s[2]+s[3])/2) on the sub-domain where (c+d)/2 != (s[2]+s[3])/2.
# ---------------------------------------------------------------------------
_W_PARTIAL_LAST = (
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    # WRONG on a sub-domain: last midpoint from the RAW c,d, not s[2],s[3].\n"
    "    m2 = (c + d) / 2\n"
    "    result = [col_min, m0, m1, m2, col_max]  # type: List[float]\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# 3'. MIS-PAIRED INTERIOR — order the centres correctly but pair the WRONG ordered
# neighbours for the middle boundary: m1 = (s[0]+s[2])/2 (skipping s[1]) instead of
# (s[1]+s[2])/2. expect=reject — fails P5 (Result()[2] == (s[1]+s[2])/2) whenever
# s[0] != s[1].
# ---------------------------------------------------------------------------
_W_MISPAIR = (
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    # WRONG pairing: average s[0] and s[2], skipping the true neighbour s[1].\n"
    "    m1 = (s[0] + s[2]) / 2\n"
    "    m2 = (s[2] + s[3]) / 2\n"
    "    result = [col_min, m0, m1, m2, col_max]  # type: List[float]\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# UNGROUNDED-ORACLE fallback probe: a FLAT but MONOTONE boundary list. Returns
# [col_min, col_min, col_min, col_min, col_max] — trivially non-decreasing (P7
# holds) with P1/P2/P3 holding too, but the interior boundaries are col_min, NOT
# the ordered-midpoint values P4/P5/P6 demand. expect=reject. This proves the value
# clauses P4/P5/P6 are LOAD-BEARING beyond the weaker monotonicity clause P7 (a spec
# pinned only on P7 would WRONGLY admit this). A real patch returning a degenerate
# constant boundary list bins every value into the last bin and fails the F2P.
# ---------------------------------------------------------------------------
_W_FLAT_MONOTONE = (
    "    # Trivially monotone but the interior boundaries are NOT the ordered\n"
    "    # midpoints: satisfies P7 (and P1/P2/P3) yet must fail P4/P5/P6.\n"
    "    result = [col_min, col_min, col_min, col_min, col_max]  # type: List[float]\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# DESCENDING — sort the centres but report them in DESCENDING order, so the
# boundary list is reverse-monotone: [col_max, hi-mid, mid, lo-mid, col_min].
# expect=reject — fails P2 (Result()[0]==col_min), P3 (Result()[4]==col_max), and
# P7 (non-decreasing). A faithful descending-sort patch yields bins
# monotonically DECREASING; np.digitize on the ascending-expecting transform
# misassigns every value and the F2P [0,0,1,2,3,4] expectation FAILS.
# ---------------------------------------------------------------------------
_W_DESCENDING = (
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    m2 = (s[2] + s[3]) / 2\n"
    "    # WRONG: reverse the boundary list (descending bins).\n"
    "    result = [col_max, m2, m1, m0, col_min]  # type: List[float]\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# LENGTH BREAK (cheap supporting near-miss with a real refinement) — drop the last
# interior midpoint, returning four boundaries. expect=reject — fails P1 (len==5)
# and P3 (Result()[4]==col_max becomes Result()[3]). A real patch that emits one
# fewer bin edge produces the wrong number of bins, so fit_transform yields a bin
# vector that does not match the F2P expected [0,0,1,2,3,4].
# ---------------------------------------------------------------------------
_W_SHORT = (
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    # WRONG LENGTH: only four boundaries (dropped one interior midpoint).\n"
    "    result = [col_min, m0, m1, col_max]  # type: List[float]\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# ENDPOINT SWAP (cheap supporting near-miss) — order the centres and form the
# midpoints correctly, but swap the closing endpoints: col_max first, col_min last.
# expect=reject — fails P2 (Result()[0]==col_min) and P3 (Result()[4]==col_max) and
# P7. A real patch that brackets with [max, ..., min] hands np.digitize an
# out-of-order edge list and the transform raises / misassigns; F2P FAILS.
# ---------------------------------------------------------------------------
_W_ENDPOINT_SWAP = (
    "    s = order4(a, b, c, d, col_min, col_max)\n"
    "    m0 = (s[0] + s[1]) / 2\n"
    "    m1 = (s[1] + s[2]) / 2\n"
    "    m2 = (s[2] + s[3]) / 2\n"
    "    # WRONG: closing endpoints swapped (col_max prepended, col_min appended).\n"
    "    result = [col_max, m0, m1, m2, col_min]  # type: List[float]\n"
    "    return result\n"
)


SPEC_TESTS = [
    {
        "id": "pos-reverse-midpoint-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "structurally-different CORRECT impl: order the centres, then "
        "compute the three midpoints last-to-first and reorder the bracketing "
        "asserts to match. Same ordered-midpoint result; only the executable shape "
        "and assert order changed (no induction lemma — order4 consumed by its "
        "Ensures). Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-append-build",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_APPEND),
        "rationale": "correct reshape: build the boundary list element-by-element "
        "via append into a fresh typed local (gold uses one list literal), "
        "re-asserting each appended value so the per-index framing P2..P6 the "
        "postcondition needs is re-established. Keeps the gold bracketing asserts. "
        "Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "the precondition admits a normal F2P-shaped input (unsorted "
        "centres inside the column range [0,10]) and is non-vacuous: each centre "
        "lies in [col_min, col_max] and order4 is callable (its Requires established "
        "from make_bin_edges's Requires). If the call cannot verify, PRECOND-TOO-STRONG.",
    },
    {
        "id": "reject-prepatch-no-sort",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_PREPATCH),
        "refinement": "this IS the pre-patch op verbatim (bin_edges = (centers[1:] + "
        "centers[:-1]) * 0.5 with NO centers.sort()). For the F2P column "
        "[0,0.5,2,3,9,10] with n_bins=5 the k-means centres come out unsorted, so the "
        "midpoints are out of order and np.digitize raises `ValueError: bins must be "
        "monotonically increasing or decreasing`; fit_transform never reaches the "
        "expected [0,0,1,2,3,4]. model_prepatch.py is this skeleton and fails (G-DIFF). "
        "Does NOT resolve.",
        "rationale": "rejected by P4/P5/P6 (interior boundaries are (a+b)/2,(b+c)/2,"
        "(c+d)/2, not the ordered-centre midpoints (s[0]+s[1])/2 etc.) and P7 "
        "(non_decreasing fails on unsorted centres). A verify here is SPEC-TOO-WEAK.",
    },
    {
        "id": "reject-partial-last-midpoint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_PARTIAL_LAST),
        "refinement": "partial-domain: its faithful patch sorts the centres for the "
        "first two midpoints but forms the LAST interior edge from the raw last two "
        "centres (centers[-2:] before the in-place sort settles, e.g. a stale slice). "
        "On the F2P column the last raw pair differs from the two largest ordered "
        "centres, so that interior edge is wrong and can sit out of order -> "
        "np.digitize misassigns / raises and the F2P [0,0,1,2,3,4] FAILS. Does NOT "
        "resolve on the sub-domain where (c+d)/2 != (s[2]+s[3])/2.",
        "rationale": "rejected by P6: Result()[3] == (order4(...)[2]+order4(...)[3])/2 "
        "is violated whenever the raw (c+d)/2 differs from the ordered (s[2]+s[3])/2. "
        "A verify here would mean P6 does not pin the last interior boundary to the "
        "ordered pair (SPEC-TOO-WEAK).",
    },
    {
        "id": "reject-mispaired-interior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_MISPAIR),
        "refinement": "its faithful patch averages non-adjacent ordered centres for "
        "the middle edge (e.g. (centers[0]+centers[2])*0.5 by an off-by-one slice "
        "centers[2:]+centers[:-2]) instead of the adjacent pair. The middle bin edge "
        "lands at the wrong value, so the bin assignment for the F2P column diverges "
        "from [0,0,1,2,3,4] (a point near the true midpoint falls in the wrong bin). "
        "Does NOT resolve when centers[0] != centers[1].",
        "rationale": "rejected by P5: Result()[2] == (order4(...)[1]+order4(...)[2])/2 "
        "is violated because the impl produces (s[0]+s[2])/2. A verify here would mean "
        "P5 does not pin the middle boundary to the adjacent ordered pair "
        "(SPEC-TOO-WEAK).",
    },
    {
        "id": "reject-flat-monotone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_FLAT_MONOTONE),
        "refinement": "its faithful patch returns a degenerate boundary list whose "
        "interior edges all equal col_min (e.g. bin_edges = np.r_[col_min, "
        "np.full(k-1, col_min), col_max]). It is trivially monotone, so np.digitize "
        "does not raise, but every value of the F2P column [0,0.5,2,3,9,10] falls into "
        "the last bin -> the bin vector is [4,4,4,4,4,4] (or all-0), NOT the expected "
        "[0,0,1,2,3,4]. Does NOT resolve. (Targets the ungrounded-oracle/value-double-"
        "mask risk: a monotone-only spec would wrongly admit this.)",
        "rationale": "rejected by P4/P5/P6: the interior boundaries are col_min, not "
        "the ordered-midpoint values. This is the key witness that the value clauses "
        "are load-bearing BEYOND the weaker P7 (non_decreasing) — a spec pinned only "
        "on monotonicity would VERIFY this wrong impl (SPEC-TOO-WEAK).",
    },
    {
        "id": "reject-descending-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_DESCENDING),
        "refinement": "its faithful patch sorts the centres DESCENDING (e.g. "
        "centers.sort(); centers = centers[::-1]) and brackets with [col_max, ..., "
        "col_min]. The bin edges are monotonically DECREASING; KBinsDiscretizer.transform "
        "feeds bin_edges[jj][1:] (ascending-expected) to np.digitize, which misassigns "
        "every value -> the F2P bin vector is the reverse/garbage, never [0,0,1,2,3,4]. "
        "Does NOT resolve.",
        "rationale": "rejected by P2 (Result()[0]==col_min — here col_max), P3 "
        "(Result()[4]==col_max — here col_min), and P7 (the list is reverse-monotone). "
        "A verify here would mean the spec does not pin orientation (SPEC-TOO-WEAK).",
    },
    {
        "id": "reject-short-length-four",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_SHORT),
        "refinement": "its faithful patch drops one interior midpoint (an off-by-one "
        "slice yielding centers[1:-1] midpoints, one short). The boundary array has "
        "the wrong number of edges, so for n_bins=5 fit_transform produces a bin "
        "vector of the wrong width / wrong assignment and the F2P assert_array_equal "
        "against [0,0,1,2,3,4] FAILS. Does NOT resolve. (Cheap supporting near-miss "
        "with a real refinement.)",
        "rationale": "rejected by P1 (len(Result())==5 — here 4) and P3 "
        "(Result()[4]==col_max — index 4 does not exist). A verify here would mean "
        "the boundary count is unconstrained (SPEC-TOO-WEAK).",
    },
    {
        "id": "reject-endpoint-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_ENDPOINT_SWAP),
        "refinement": "its faithful patch brackets the (correctly ordered) interior "
        "midpoints with the endpoints SWAPPED — np.r_[col_max, mids, col_min]. The "
        "boundary list starts above and ends below the interior values, so it is not "
        "monotone and np.digitize raises / misassigns; the F2P [0,0,1,2,3,4] FAILS. "
        "Does NOT resolve. (Cheap supporting near-miss with a real refinement.)",
        "rationale": "rejected by P2 (Result()[0]==col_min — here col_max), P3 "
        "(Result()[4]==col_max — here col_min), and P7 (non-monotone). A verify here "
        "would mean the endpoints are not pinned (SPEC-TOO-WEAK).",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — order4 (@ContractOnly, A-consumed) models numpy.ndarray.sort, the
# in-place ascending sort the gold patch adds (`centers.sort()`).
#
# The runner mounts ONLY the probe at /work (directive 6), so we read the bundle's
# audited axiom_check.py on the HOST at load time and embed its source verbatim for
# the soundness probe — the strongest available witness (it CALLS the real
# numpy.ndarray.sort, never scrapes source — directive 4). axiom_check.py imports
# only numpy + random and opens no files, so no utf-8/locale concern (directive 5).
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


AXIOM_TESTS = [
    {
        "id": "ax-sound-order4",
        "axiom": "order4",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the A-consumed axiom order4 (length 4, every element in [lo,hi], "
        "non-decreasing) must hold on the REAL numpy.ndarray.sort for every input in "
        "its Requires domain. axiom_check.py executes the real sort on 10 boundary + "
        "200000 fuzz 4-tuples (each in [lo,hi]) and asserts all three Ensures clauses; "
        "it also reproduces the discriminator (unsorted centres -> non-monotone "
        "boundary list; sorted-first -> monotone over 50000 fuzz cases). A single "
        "violation is AXIOM-UNSOUND. apply_gold=True (the discriminator's post-fix "
        "branch reflects the sorted, post-patch behaviour). Exit 0 iff sound.",
    },
    {
        "id": "ax-contain-order4-domain",
        "axiom": "order4",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "try:\n"
            "    import numpy as np\n"
            "except Exception as e:\n"
            "    print('cannot import numpy:', e); sys.exit(1)\n"
            "\n"
            "# CONTAINMENT (not whole-domain coverage). make_bin_edges's Requires forces\n"
            "# col_min <= col_max and col_min <= each centre <= col_max, and it calls\n"
            "# order4(a,b,c,d, col_min, col_max) -- i.e. the ONLY inputs the model can\n"
            "# reach are four reals each in [lo,hi] with lo<=hi (lo=col_min, hi=col_max).\n"
            "# The order4 axiom's Requires domain is EXACTLY lo<=a<=hi, ..., lo<=d<=hi.\n"
            "# So every caller-reachable input lies in the axiom domain BY CONSTRUCTION.\n"
            "# We enumerate caller-reachable 4-tuples (boundary + fuzz), assert each is\n"
            "# in the axiom Requires domain (each elem in [lo,hi]), and confirm the real\n"
            "# numpy sort ACCEPTS each (so no reachable input is rejected by the callee)\n"
            "# and keeps every element in [lo,hi] (the bound the postcondition consumes).\n"
            "# numpy.ndarray.sort accepts ANY finite float array (broader than reached),\n"
            "# which is SOUND (float-vs-int rule); a reachable input outside the axiom\n"
            "# domain would be AXIOM-TOO-WEAK-FOR-CALLER -- none can exist.\n"
            "boundary = [\n"
            "    ((0.0, 0.0, 0.0, 0.0), 0.0, 0.0),          # degenerate lo==hi\n"
            "    ((0.0, 10.0, 0.0, 10.0), 0.0, 10.0),       # bounds duplicated\n"
            "    ((1.0, 2.0, 3.0, 4.0), 0.0, 10.0),         # already sorted\n"
            "    ((4.0, 3.0, 2.0, 1.0), 0.0, 10.0),         # reverse sorted\n"
            "    ((0.25, 9.5, 2.5, 6.0), 0.0, 10.0),        # F2P-flavoured unsorted\n"
            "    ((0.0, 0.5, 9.0, 10.0), 0.0, 10.0),        # F2P column extremes\n"
            "]\n"
            "rng = random.Random(13135)\n"
            "reached = list(boundary)\n"
            "for _ in range(20000):\n"
            "    lo = rng.uniform(-1e6, 1e6)\n"
            "    hi = lo + rng.uniform(0.0, 1e6)\n"
            "    vals = tuple(rng.uniform(lo, hi) for _ in range(4))\n"
            "    reached.append((vals, lo, hi))\n"
            "ok = True\n"
            "for vals, lo, hi in reached:\n"
            "    # (a) caller-reachable input must be IN the axiom Requires domain\n"
            "    if not (lo <= hi and all(lo <= v <= hi for v in vals)):\n"
            "        print('FAIL: caller-reachable input %r outside axiom domain '\n"
            "              '[%r,%r]' % (vals, lo, hi))\n"
            "        ok = False\n"
            "        continue\n"
            "    # (b) the REAL callee accepts it and keeps every element in [lo,hi]\n"
            "    arr = np.array(vals, dtype=np.float64)\n"
            "    try:\n"
            "        arr.sort()\n"
            "    except Exception as e:\n"
            "        print('FAIL: real numpy sort rejected reachable input %r: %s'\n"
            "              % (vals, e))\n"
            "        ok = False\n"
            "        continue\n"
            "    if arr.shape[0] != 4:\n"
            "        print('FAIL: sort changed length for %r' % (vals,)); ok = False; continue\n"
            "    if not all(lo <= v <= hi for v in arr):\n"
            "        print('FAIL: sorted element left [%r,%r] for %r -> %r'\n"
            "              % (lo, hi, vals, arr.tolist())); ok = False; continue\n"
            "if not ok:\n"
            "    sys.exit(1)\n"
            "print('AX-CONTAIN OK: every caller-reachable 4-tuple (6 boundary + 20000 '\n"
            "      'fuzz, each in [lo,hi] by make_bin_edges Requires) lies in the order4 '\n"
            "      'Requires domain and is accepted by the real numpy.ndarray.sort with '\n"
            "      'every element kept in [lo,hi]; callee coverage is broader-than-reached '\n"
            "      '(accepts any float array) - SOUND.')\n"
            "sys.exit(0)\n"
        ),
        "rationale": "containment, not whole-domain coverage: make_bin_edges's Requires "
        "forces each centre into [col_min,col_max] and passes lo=col_min, hi=col_max, so "
        "every caller-reachable order4 input is in the axiom's Requires domain BY "
        "CONSTRUCTION. The probe enumerates caller-reachable 4-tuples, asserts each is in "
        "the axiom domain, and confirms the real numpy sort accepts it and keeps every "
        "element in [lo,hi]. A reachable input outside the domain would be "
        "AXIOM-TOO-WEAK-FOR-CALLER; none can exist. Broader callee coverage is sound.",
    },
]
